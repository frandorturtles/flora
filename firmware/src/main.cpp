// FLORA - Smart Plant Companion - firmware v0.1 (ESP32-C3, Arduino framework)
// ESTADO: escrito para el hardware FLORA v0.1; NO compilado ni probado en placa (ver README.md).
//
// GPIO (ver hardware/pinout.csv):
//   GPIO0  SOIL_ADC   (ADC1_CH0)   salida de la sonda capacitiva, tras R 1k + C 100nF
//   GPIO4  SOIL_PWR_N              ACTIVO EN BAJO: P-MOSFET que alimenta la sonda
//   GPIO6/7 SDA/SCL                I2C: SHT40 (0x44), TSL25911 (0x29), OLED SSD1306 (0x3C)
//   GPIO9  BTN_USER                activo en bajo (pin BOOT/strapping: no pulsar durante el reset)
//   GPIO3  LED_RED, GPIO5 LED_GRN, GPIO10 LED_AMB   ACTIVOS EN BAJO (ánodo a 3V3)
//   GPIO1  BUZZER (PWM) -> 2N7002 -> zumbador piezo
#include <Arduino.h>
#include <Wire.h>
#include <Preferences.h>
#include <U8g2lib.h>
#include "flora_logic.h"

using namespace flora;

constexpr int PIN_SOIL_ADC = 0, PIN_SOIL_PWR_N = 4, PIN_SDA = 6, PIN_SCL = 7, PIN_BTN = 9;
constexpr int PIN_LED_RED = 3, PIN_LED_GRN = 5, PIN_LED_AMB = 10, PIN_BUZ = 1;
constexpr uint8_t ADDR_SHT = 0x44, ADDR_TSL = 0x29;

U8G2_SSD1306_128X64_NONAME_F_HW_I2C oled(U8G2_R0, U8X8_PIN_NONE);
Preferences prefs;

// ------------------------------------------------------------------ estado
struct Readings {
  float tempC = NAN, rh = NAN, lux = NAN, soilMv = NAN, soilPct = NAN;
  bool shtOk = false, tslOk = false, soilOk = false, oledOk = false;
} R;
SoilCal cal; Thresholds thr; AlertPolicy alert; SoilState soilState = SoilState::Unknown;
Button button;
enum Screen : uint8_t { SCR_MAIN, SCR_SOIL, SCR_THRESH, SCR_CAL, SCR_SOUND, SCR_COUNT };
uint8_t screen = SCR_MAIN; bool dirty = true;
String toast; uint32_t toastUntil = 0;

// ------------------------------------------------------------------ I2C helpers
bool i2cPresent(uint8_t a) { Wire.beginTransmission(a); return Wire.endTransmission() == 0; }

// SHT40: comando 0xFD = medida alta precisión (~8.3 ms); lectura 6 bytes con CRC
bool readSHT(float &t, float &h) {
  Wire.beginTransmission(ADDR_SHT); Wire.write(0xFD);
  if (Wire.endTransmission() != 0) return false;
  delay(10);   // única espera corta bloqueante (10 ms) por lectura cada varios segundos
  if (Wire.requestFrom((int)ADDR_SHT, 6) != 6) return false;
  uint8_t b[6]; for (auto &x : b) x = Wire.read();
  if (sensirionCrc8(b, 2) != b[2] || sensirionCrc8(b + 3, 2) != b[5]) return false;
  t = sht4xTemp((b[0] << 8) | b[1]); h = sht4xRh((b[3] << 8) | b[4]);
  return true;
}

// TSL25911 (registros compatibles con TSL2591). Ganancia media (25x), integración 200 ms.
constexpr uint8_t TSL_CMD = 0xA0;
bool tslWrite(uint8_t reg, uint8_t v) { Wire.beginTransmission(ADDR_TSL); Wire.write(TSL_CMD | reg); Wire.write(v); return Wire.endTransmission() == 0; }
bool tslRead(uint8_t reg, uint8_t *buf, uint8_t n) {
  Wire.beginTransmission(ADDR_TSL); Wire.write(TSL_CMD | reg);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom((int)ADDR_TSL, (int)n) != n) return false;
  for (uint8_t i = 0; i < n; i++) buf[i] = Wire.read();
  return true;
}
bool tslInit() {
  uint8_t id; if (!tslRead(0x12, &id, 1) || id != 0x50) return false;   // ID esperado 0x50 (verificar en hoja de datos)
  return tslWrite(0x01, 0x11) && tslWrite(0x00, 0x03);                   // gain medio + atime 200 ms; PON|AEN
}
bool readTSL(float &lux) {
  uint8_t d[4]; if (!tslRead(0x14, d, 4)) return false;
  uint16_t c0 = d[0] | (d[1] << 8), c1 = d[2] | (d[3] << 8);
  lux = tslLux(c0, c1, 200.0f, 25.0f);
  return true;   // lux = NAN si saturado
}

// ------------------------------------------------------------------ sonda de suelo (máquina de estados no bloqueante)
enum class SoilPhase : uint8_t { Idle, Settling };
SoilPhase soilPhase = SoilPhase::Idle; uint32_t soilT0 = 0, lastSoilCycle = 0;
constexpr uint32_t SOIL_PERIOD_MS = 3000, SOIL_SETTLE_MS = 200;

float readSoilMv() {
  analogSetPinAttenuation(PIN_SOIL_ADC, ADC_11db);
  uint32_t acc = 0; for (int i = 0; i < 16; i++) acc += analogReadMilliVolts(PIN_SOIL_ADC);
  return acc / 16.0f;
}
void soilTick(uint32_t now) {
  if (soilPhase == SoilPhase::Idle && now - lastSoilCycle >= SOIL_PERIOD_MS) {
    digitalWrite(PIN_SOIL_PWR_N, LOW); soilPhase = SoilPhase::Settling; soilT0 = now;     // enciende la sonda
  } else if (soilPhase == SoilPhase::Settling && now - soilT0 >= SOIL_SETTLE_MS) {
    R.soilMv = readSoilMv();
    digitalWrite(PIN_SOIL_PWR_N, HIGH); soilPhase = SoilPhase::Idle; lastSoilCycle = now;
    R.soilOk = soilMvPlausible(R.soilMv);
    R.soilPct = R.soilOk ? soilPercent(R.soilMv, cal) : NAN;
    SoilState ns = classify(R.soilPct, R.soilOk, thr, soilState);
    if (ns != soilState) { soilState = ns; }
    dirty = true;
  }
}

// ------------------------------------------------------------------ salidas
void setLeds(SoilState s, uint32_t now) {
  bool r = false, g = false, a = false;
  switch (s) {
    case SoilState::Dry: r = true; break;
    case SoilState::Ok: g = true; break;
    case SoilState::Wet: a = true; break;
    case SoilState::SensorError: r = a = ((now / 400) % 2); break;   // parpadeo rojo+ámbar
    default: g = ((now / 1000) % 2); break;                         // sin calibrar: verde lento
  }
  digitalWrite(PIN_LED_RED, r ? LOW : HIGH); digitalWrite(PIN_LED_GRN, g ? LOW : HIGH); digitalWrite(PIN_LED_AMB, a ? LOW : HIGH);
}
uint32_t beepUntil = 0;
void buzzerTone(bool on) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  if (on) ledcWriteTone(PIN_BUZ, 4000); else ledcWriteTone(PIN_BUZ, 0);
#else
  if (on) ledcWriteTone(0, 4000); else ledcWriteTone(0, 0);
#endif
}
void buzzerInit() {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcAttach(PIN_BUZ, 4000, 8);
#else
  ledcSetup(0, 4000, 8); ledcAttachPin(PIN_BUZ, 0);
#endif
  buzzerTone(false);
}
void showToast(const String &s) { toast = s; toastUntil = millis() + 1500; dirty = true; }

// ------------------------------------------------------------------ persistencia
void loadPrefs() {
  prefs.begin("flora", true);
  cal.dry_mv = prefs.getFloat("dry", NAN); cal.wet_mv = prefs.getFloat("wet", NAN);
  thr.low = prefs.getFloat("lo", thr.low); thr.high = prefs.getFloat("hi", thr.high);
  alert.enabled = prefs.getBool("snd", true);
  prefs.end();
  if (!thresholdsValid(thr)) thr = Thresholds();
}
void savePrefs() {
  prefs.begin("flora", false);
  if (!isnan(cal.dry_mv)) prefs.putFloat("dry", cal.dry_mv);
  if (!isnan(cal.wet_mv)) prefs.putFloat("wet", cal.wet_mv);
  prefs.putFloat("lo", thr.low); prefs.putFloat("hi", thr.high); prefs.putBool("snd", alert.enabled);
  prefs.end();
}

// ------------------------------------------------------------------ interfaz
// Navegación: pulsación corta = siguiente pantalla. Pulsación larga = acción de la pantalla actual:
//   PRINCIPAL: silenciar alerta 10 min | SUELO: -- | UMBRALES: +5 en "seco" (cicla 10..45) |
//   CALIBRAR: 1ª larga = captura SECO, 2ª larga = captura HÚMEDO | SONIDO: activar/desactivar
bool calWaitingWet = false;
void onLong() {
  switch (screen) {
    case SCR_MAIN: alert.silenceUntil = millis() + 600000UL; buzzerTone(false); showToast("Alerta silenciada"); break;
    case SCR_THRESH: {
      float v = thr.low + 5; if (v > 45) v = 10; Thresholds t = thr; t.low = v;
      if (thresholdsValid(t)) { thr = t; savePrefs(); showToast("Seco < " + String((int)thr.low) + "%"); } break; }
    case SCR_CAL:
      if (!soilMvPlausible(R.soilMv)) { showToast("Sonda no valida"); break; }
      if (!calWaitingWet) { cal.dry_mv = R.soilMv; calWaitingWet = true; showToast("SECO guardado"); }
      else { cal.wet_mv = R.soilMv; calWaitingWet = false;
             if (cal.valid()) { savePrefs(); showToast("Calibrado"); } else { cal.wet_mv = NAN; showToast("Error: poca diferencia"); } }
      break;
    case SCR_SOUND: alert.enabled = !alert.enabled; savePrefs(); showToast(alert.enabled ? "Sonido ON" : "Sonido OFF"); break;
    default: break;
  }
  dirty = true;
}

const char *stateText(SoilState s) {
  switch (s) { case SoilState::Dry: return "SECO - regar"; case SoilState::Ok: return "Humedad OK"; case SoilState::Wet: return "EXCESO humedad";
    case SoilState::SensorError: return "SONDA?"; default: return "Sin calibrar"; }
}
void fmt(char *b, size_t n, float v, const char *f, const char *na = "--") { if (isnan(v)) snprintf(b, n, "%s", na); else snprintf(b, n, f, v); }

void draw() {
  if (!R.oledOk) return;
  char a[24], b[24], c[24];
  oled.clearBuffer(); oled.setFont(u8g2_font_6x12_tf);
  if (millis() < toastUntil) { oled.drawStr(4, 36, toast.c_str()); oled.sendBuffer(); return; }
  switch (screen) {
    case SCR_MAIN:
      fmt(a, sizeof a, R.soilPct, "Suelo %.0f%%"); oled.drawStr(0, 11, a);
      if (isnan(R.soilPct) && R.soilOk) { snprintf(a, sizeof a, "(%.0f mV)", R.soilMv); oled.drawStr(78, 11, a); }
      if (R.shtOk) { fmt(a, sizeof a, R.tempC, "Temp %.1f C"); oled.drawStr(0, 24, a); } else oled.drawStr(0, 24, "Temp: SHT40 ?");
      if (R.shtOk) { fmt(b, sizeof b, R.rh, "HR   %.0f %%"); oled.drawStr(0, 36, b); } else oled.drawStr(0, 36, "HR: SHT40 ?");
      if (R.tslOk) { if (isnan(R.lux)) snprintf(c, sizeof c, "Luz: saturada"); else snprintf(c, sizeof c, "Luz  %.0f lx", R.lux); oled.drawStr(0, 48, c); }
      else oled.drawStr(0, 48, "Luz: TSL ?");
      oled.drawStr(0, 62, stateText(soilState)); break;
    case SCR_SOIL:
      oled.drawStr(0, 11, "SUELO (detalle)");
      fmt(a, sizeof a, R.soilMv, "ADC: %.0f mV"); oled.drawStr(0, 26, a);
      snprintf(a, sizeof a, "Seco:%s", isnan(cal.dry_mv) ? "--" : String((int)cal.dry_mv).c_str()); oled.drawStr(0, 40, a);
      snprintf(a, sizeof a, "Humedo:%s", isnan(cal.wet_mv) ? "--" : String((int)cal.wet_mv).c_str()); oled.drawStr(0, 52, a);
      oled.drawStr(0, 63, R.soilOk ? "Sonda: OK" : "Sonda: desconectada?"); break;
    case SCR_THRESH:
      oled.drawStr(0, 11, "UMBRALES"); snprintf(a, sizeof a, "Seco < %d %%", (int)thr.low); oled.drawStr(0, 28, a);
      snprintf(a, sizeof a, "Exceso > %d %%", (int)thr.high); oled.drawStr(0, 41, a); oled.drawStr(0, 62, "Larga: +5 seco"); break;
    case SCR_CAL:
      oled.drawStr(0, 11, "CALIBRAR SUELO");
      oled.drawStr(0, 26, calWaitingWet ? "2) Sonda en agua" : "1) Sonda al aire/seca"); oled.drawStr(0, 38, "   y pulsa LARGO");
      fmt(a, sizeof a, R.soilMv, "ADC ahora: %.0f mV"); oled.drawStr(0, 56, a); break;
    case SCR_SOUND:
      oled.drawStr(0, 11, "ALERTA SONORA"); oled.drawStr(0, 32, alert.enabled ? "Estado: ACTIVADA" : "Estado: DESACTIVADA"); oled.drawStr(0, 62, "Larga: cambiar"); break;
  }
  oled.sendBuffer();
}

// ------------------------------------------------------------------ setup / loop
uint32_t lastEnv = 0, lastDraw = 0, lastI2cRetry = 0;
void setup() {
  Serial.begin(115200);
  pinMode(PIN_SOIL_PWR_N, OUTPUT); digitalWrite(PIN_SOIL_PWR_N, HIGH);        // sonda apagada
  pinMode(PIN_LED_RED, OUTPUT); pinMode(PIN_LED_GRN, OUTPUT); pinMode(PIN_LED_AMB, OUTPUT);
  digitalWrite(PIN_LED_RED, HIGH); digitalWrite(PIN_LED_GRN, HIGH); digitalWrite(PIN_LED_AMB, HIGH);
  pinMode(PIN_BTN, INPUT);                                                    // pull-up externo de 10k en el PCB
  buzzerInit();
  Wire.begin(PIN_SDA, PIN_SCL, 100000); Wire.setTimeOut(50);
  loadPrefs();
  R.oledOk = i2cPresent(0x3C);
  if (R.oledOk) { oled.setI2CAddress(0x3C << 1); oled.begin(); oled.setContrast(120); }
  R.tslOk = i2cPresent(ADDR_TSL) && tslInit();
  Serial.printf("FLORA v0.1 | OLED:%d SHT:%d TSL:%d cal:%d\n", R.oledOk, i2cPresent(ADDR_SHT), R.tslOk, cal.valid());
}

void loop() {
  uint32_t now = millis();
  // botón (activo en bajo)
  BtnEvent e = button.update(digitalRead(PIN_BTN) == LOW, now);
  if (e == BtnEvent::Short) { screen = (screen + 1) % SCR_COUNT; calWaitingWet = false; buzzerTone(false); dirty = true; }
  else if (e == BtnEvent::Long) onLong();

  soilTick(now);

  if (now - lastEnv >= 2000) {            // entorno cada 2 s
    lastEnv = now;
    float t, h; R.shtOk = readSHT(t, h); if (R.shtOk) { R.tempC = t; R.rh = h; } else { R.tempC = R.rh = NAN; }
    if (!R.tslOk && now - lastI2cRetry > 10000) { lastI2cRetry = now; R.tslOk = i2cPresent(ADDR_TSL) && tslInit(); }
    if (R.tslOk) { float l; if (readTSL(l)) R.lux = l; else { R.tslOk = false; R.lux = NAN; } }
    if (!R.oledOk && now - lastI2cRetry > 10000) { lastI2cRetry = now; if (i2cPresent(0x3C)) { oled.begin(); R.oledOk = true; } }
    dirty = true;
  }

  setLeds(soilState, now);
  if (alert.shouldBeep(soilState, now)) beepUntil = now + 300;
  buzzerTone(now < beepUntil);

  if (dirty && now - lastDraw >= 100) { lastDraw = now; dirty = false; draw(); }
  if (toastUntil && now >= toastUntil) { toastUntil = 0; dirty = true; }
}
