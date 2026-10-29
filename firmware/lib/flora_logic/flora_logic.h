// FLORA - lógica pura (sin dependencias de Arduino) para poder probarla en el PC.
#pragma once
#include <stdint.h>
#include <math.h>

namespace flora {

// ---------------------------------------------------------------- humedad de suelo
struct SoilCal {
  float dry_mv = NAN;   // lectura con la sonda al aire / suelo seco (mV en el ADC)
  float wet_mv = NAN;   // lectura con la sonda en agua / suelo saturado (mV)
  bool valid() const {
    return !isnan(dry_mv) && !isnan(wet_mv) && (dry_mv - wet_mv) >= 150.0f;  // separación mínima
  }
};

// Plausibilidad eléctrica de la lectura del ADC (heurística de sonda desconectada).
// El pull-down de 470k del PCB lleva la entrada a ~0 V si no hay sonda; una sonda capacitiva conectada
// entrega una tensión claramente mayor. El umbral exacto debe confirmarse con medidas reales.
inline bool soilMvPlausible(float mv, float minMv = 80.0f, float maxMv = 3150.0f) {
  return !isnan(mv) && mv >= minMv && mv <= maxMv;
}

// Porcentaje calibrado 0..100 (100 = húmedo). Devuelve NAN si no hay calibración válida.
inline float soilPercent(float mv, const SoilCal &c) {
  if (!c.valid() || isnan(mv)) return NAN;
  float p = (c.dry_mv - mv) / (c.dry_mv - c.wet_mv) * 100.0f;
  if (p < 0) p = 0;
  if (p > 100) p = 100;
  return p;
}

enum class SoilState : uint8_t { Unknown, Dry, Ok, Wet, SensorError };

struct Thresholds { float low = 30.0f; float high = 70.0f; float hyst = 3.0f; };

// Clasificación con histéresis para evitar parpadeo en el límite.
inline SoilState classify(float pct, bool sensorOk, const Thresholds &t, SoilState prev) {
  if (!sensorOk) return SoilState::SensorError;
  if (isnan(pct)) return SoilState::Unknown;
  switch (prev) {
    case SoilState::Dry:  if (pct < t.low + t.hyst) return SoilState::Dry; break;
    case SoilState::Wet:  if (pct > t.high - t.hyst) return SoilState::Wet; break;
    default: break;
  }
  if (pct < t.low) return SoilState::Dry;
  if (pct > t.high) return SoilState::Wet;
  return SoilState::Ok;
}

inline bool thresholdsValid(const Thresholds &t) {
  return t.low >= 0 && t.high <= 100 && (t.high - t.low) >= 10.0f && t.hyst >= 0 && t.hyst < (t.high - t.low) / 2;
}

// ---------------------------------------------------------------- botón (antirrebote + corta/larga)
enum class BtnEvent : uint8_t { None, Short, Long };

class Button {
 public:
  Button(uint16_t debounceMs = 30, uint16_t longMs = 1200) : db_(debounceMs), lg_(longMs) {}
  // pressed: true = pulsado. now: millis()
  BtnEvent update(bool pressed, uint32_t now) {
    if (pressed != raw_) { raw_ = pressed; tChange_ = now; }
    if ((now - tChange_) >= db_ && stable_ != raw_) {
      stable_ = raw_;
      if (stable_) { tDown_ = now; longSent_ = false; }
      else if (!longSent_) return BtnEvent::Short;   // soltó sin llegar a larga
    }
    if (stable_ && !longSent_ && (now - tDown_) >= lg_) { longSent_ = true; return BtnEvent::Long; }
    return BtnEvent::None;
  }
 private:
  uint16_t db_, lg_; bool raw_ = false, stable_ = false, longSent_ = false; uint32_t tChange_ = 0, tDown_ = 0;
};

// ---------------------------------------------------------------- alerta sonora
struct AlertPolicy {
  bool enabled = true;
  uint32_t silenceUntil = 0;          // millis() hasta el que está silenciada
  uint32_t repeatMs = 60000;          // repetición mientras persista el estado
  uint32_t lastBeep = 0;
  bool haveBeeped = false;
  bool shouldBeep(SoilState s, uint32_t now) {
    if (!enabled || (int32_t)(silenceUntil - now) > 0) return false;
    if (s != SoilState::Dry && s != SoilState::Wet) { haveBeeped = false; return false; }
    if (!haveBeeped || (now - lastBeep) >= repeatMs) { haveBeeped = true; lastBeep = now; return true; }
    return false;
  }
};

// ---------------------------------------------------------------- SHT4x
inline uint8_t sensirionCrc8(const uint8_t *d, int n) {   // poly 0x31, init 0xFF
  uint8_t crc = 0xFF;
  for (int i = 0; i < n; i++) { crc ^= d[i]; for (int b = 0; b < 8; b++) crc = (crc & 0x80) ? (crc << 1) ^ 0x31 : (crc << 1); }
  return crc;
}
// T = -45 + 175*S/65535 ; RH = -6 + 125*S/65535 (recortada a 0..100)
inline float sht4xTemp(uint16_t s) { return -45.0f + 175.0f * (float)s / 65535.0f; }
inline float sht4xRh(uint16_t s) { float r = -6.0f + 125.0f * (float)s / 65535.0f; return r < 0 ? 0 : (r > 100 ? 100 : r); }

// ---------------------------------------------------------------- TSL2591 / TSL25911 (mismo mapa de registros)
// Fórmula del driver de referencia de Adafruit (DF=408). A validar contra la hoja de datos del TSL25911FN.
inline float tslLux(uint16_t ch0, uint16_t ch1, float atimeMs, float gain) {
  if (ch0 == 0xFFFF || ch1 == 0xFFFF) return NAN;   // saturado
  if (ch0 == 0) return 0.0f;
  float cpl = (atimeMs * gain) / 408.0f;
  float lux = ((float)ch0 - (float)ch1) * (1.0f - (float)ch1 / (float)ch0) / cpl;
  return lux < 0 ? 0 : lux;
}

}  // namespace flora
