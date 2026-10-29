// Pruebas en el PC:  g++ -std=gnu++17 -Ilib/flora_logic test/test_logic.cpp -o /tmp/t && /tmp/t
#include <cstdio>
#include <cstdlib>
#include "flora_logic.h"
using namespace flora;
static int fails = 0;
#define CHECK(c) do { if (!(c)) { printf("FALLO linea %d: %s\n", __LINE__, #c); fails++; } } while (0)
int main() {
  SoilCal c; CHECK(!c.valid()); CHECK(isnan(soilPercent(1500, c)));
  c.dry_mv = 2600; c.wet_mv = 1200; CHECK(c.valid());
  CHECK(fabsf(soilPercent(2600, c) - 0) < 1e-3); CHECK(fabsf(soilPercent(1200, c) - 100) < 1e-3);
  CHECK(fabsf(soilPercent(1900, c) - 50) < 1e-3); CHECK(soilPercent(3000, c) == 0); CHECK(soilPercent(500, c) == 100);
  SoilCal bad; bad.dry_mv = 1500; bad.wet_mv = 1450; CHECK(!bad.valid());
  CHECK(soilMvPlausible(1500)); CHECK(!soilMvPlausible(10)); CHECK(!soilMvPlausible(3300)); CHECK(!soilMvPlausible(NAN));
  Thresholds t; CHECK(thresholdsValid(t));
  SoilState s = SoilState::Unknown;
  s = classify(20, true, t, s); CHECK(s == SoilState::Dry);
  s = classify(32, true, t, s); CHECK(s == SoilState::Dry);            // histéresis
  s = classify(34, true, t, s); CHECK(s == SoilState::Ok);
  s = classify(75, true, t, s); CHECK(s == SoilState::Wet);
  s = classify(68, true, t, s); CHECK(s == SoilState::Wet);            // histéresis
  s = classify(60, true, t, s); CHECK(s == SoilState::Ok);
  CHECK(classify(50, false, t, s) == SoilState::SensorError); CHECK(classify(NAN, true, t, s) == SoilState::Unknown);
  Thresholds tb; tb.low = 50; tb.high = 55; CHECK(!thresholdsValid(tb));
  Button b; uint32_t now = 0; int shortN = 0, longN = 0;
  auto step = [&](bool p, uint32_t dt) { for (uint32_t i = 0; i < dt; i++) { now++; auto e = b.update(p, now); shortN += e == BtnEvent::Short; longN += e == BtnEvent::Long; } };
  step(false, 100); step(true, 5); step(false, 5); step(true, 100); step(false, 100);   // rebote + pulsación corta
  CHECK(shortN == 1 && longN == 0);
  step(true, 1500); step(false, 100);                                                    // larga: no genera corta al soltar
  CHECK(shortN == 1 && longN == 1);
  AlertPolicy a; CHECK(!a.shouldBeep(SoilState::Ok, 0)); CHECK(a.shouldBeep(SoilState::Dry, 1000)); CHECK(!a.shouldBeep(SoilState::Dry, 2000));
  CHECK(a.shouldBeep(SoilState::Dry, 62000)); a.silenceUntil = 200000; CHECK(!a.shouldBeep(SoilState::Dry, 130000));
  a.silenceUntil = 0; a.enabled = false; CHECK(!a.shouldBeep(SoilState::Dry, 400000));
  uint8_t v[2] = {0xBE, 0xEF}; CHECK(sensirionCrc8(v, 2) == 0x92);   // vector de la hoja de datos Sensirion
  CHECK(fabsf(sht4xTemp(0) + 45) < 1e-3); CHECK(fabsf(sht4xTemp(65535) - 130) < 1e-3);
  CHECK(sht4xRh(0) == 0); CHECK(sht4xRh(65535) == 100);
  CHECK(isnan(tslLux(0xFFFF, 10, 100, 1))); CHECK(tslLux(0, 0, 100, 1) == 0);
  printf(fails ? "%d FALLOS\n" : "todas las pruebas OK\n", fails);
  return fails ? 1 : 0;
}
