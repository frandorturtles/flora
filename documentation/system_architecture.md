# Arquitectura del sistema — FLORA v0.1

```
USB-C 5 V ─ PTC 500 mA ─ TVS ─┬─ LDO 3V3 (AP2112K) ─┬─ ESP32-C3-WROOM-02-N4
CC1/CC2: 5k1 a GND            │                      ├─ I2C (GPIO6 SDA / GPIO7 SCL, pull-up 4k7)
D+/D− ─ ESD (USBLC6) ─ GPIO19/18                     │     SHT40 (0x44) · TSL25911 (0x29) · OLED SSD1306 (0x3C)
                                                     ├─ Sonda suelo: P-MOSFET (GPIO4) → J2 → ADC1_CH0 (GPIO0)
                                                     ├─ LEDs ×3 (GPIO3/5/10, activos en bajo)
                                                     ├─ Zumbador piezo ← 2N7002 ← GPIO1 (PWM)
                                                     └─ Botón usuario (GPIO9) · Reset (EN)
```

## Decisiones y supuestos
| Tema | Decisión | Motivo / límite |
|---|---|---|
| MCU | ESP32-C3-WROOM-02-N4 (antena PCB) | Es el módulo con huella en las librerías oficiales de KiCad 7; el ESP32-C3-MINI-1 no la trae |
| Humedad aire/T | SHT40 (DFN-4) | Requiere aire caliente o reflujo para soldar |
| Luz | TSL25911FN (I2C 0x29) | BH1750 no tiene símbolo/huella oficial; el TSL25911 cumple la función. El firmware usa el mapa de registros del TSL2591: **validar con la hoja de datos y en hardware** |
| Pantalla | Módulo OLED 0,96" sobre zócalo 1×4 | Más fácil de reparar que soldar el panel; **el orden de pines del módulo varía** (esta placa espera GND-VCC-SCL-SDA) |
| Suelo | Sonda capacitiva analógica externa (JST-PH 3 pines GND-VCC-AOUT) | Calidad muy variable; ver calibración |
| Energía | Sonda alimentada por P-MOSFET solo durante la lectura | Reduce consumo y corrosión; consumo real **no medido** |
| Batería | No incluida | Revisión 2 (requiere carga, protección y power-path verificados) |
| Orientación de uso | USB-C arriba, para leer el OLED derecho | El OLED queda sobre el centro de la placa |
| Fabricación | Pista/sep. 0,2 mm, vía 0,6/0,3 mm, borde 0,4 mm | **Supuestos conservadores**, no son datos de tu laboratorio |

## Mapa de pines
Ver `hardware/pinout.csv` y `documentation/electrical_design.md`.
