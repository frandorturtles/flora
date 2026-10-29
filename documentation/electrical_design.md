# Diseño eléctrico — FLORA v0.1

## Alimentación
- USB-C receptáculo de 16 pines (GCT USB4105-GF-A en el diseño). CC1 y CC2 con **5,1 kΩ a GND** (dispositivo sumidero sin negociación PD: pide 5 V).
- VBUS → PTC 500 mA (F1, 1206) → nodo `VIN_PROT` con TVS (D1) y 10 µF (C1) → LDO AP2112K-3.3 (U4, 600 mA) → +3V3 con 10 µF + 100 nF por bloque.
- No hay diodo de polaridad: el cable USB-C fija la polaridad de VBUS. No se conecta 5 V a ningún pin de 3,3 V.
- **TVS:** el símbolo es bidireccional; si usas SMF5.0A (unidireccional) verifica la polaridad o usa SMF5.0CA. **Pendiente de revisar con la hoja de datos.**
- Corriente: el módulo puede dar picos de transmisión del orden de varios cientos de mA (consultar datasheet); el LDO de 600 mA y el PTC de 500 mA están al límite si se usa Wi-Fi intensivo. El firmware v0.1 no usa Wi-Fi.

## Asignación de GPIO (módulo ESP32-C3-WROOM-02, pines según datasheet v1.7)
| Pin módulo | GPIO | Red | Función |
|---|---|---|---|
| 18 | GPIO0 | SOIL_ADC | ADC1_CH0, tras R 1 kΩ + C 100 nF; pull-down 470 kΩ (detección de sonda desconectada) |
| 17 | GPIO1 | BUZZER_PWM | PWM ~4 kHz → R 100 Ω → gate 2N7002 |
| 16 | GPIO2 | GPIO2_STRAP | Strapping: pull-up 10 k, sin uso |
| 15 | GPIO3 | LED_RED | LED rojo (activo en bajo) |
| 3 | GPIO4 | SOIL_PWR_N | Gate del P-MOSFET de la sonda (activo en bajo), pull-up 10 k |
| 4 | GPIO5 | LED_GRN | LED verde (activo en bajo) |
| 5 / 6 | GPIO6 / 7 | I2C_SDA / SCL | Bus I2C |
| 7 | GPIO8 | GPIO8_STRAP | Strapping: pull-up 10 k, sin uso |
| 8 | GPIO9 | BTN_USER | Botón a GND, pull-up 10 k + 100 nF (pin BOOT: no pulsar durante el reset) |
| 10 | GPIO10 | LED_AMB | LED ámbar (activo en bajo) |
| 13 / 14 | GPIO18 / 19 | USB_DN / USB_DP | USB nativo (programación y consola) |
| 11 / 12 | GPIO20 / 21 | UART_RX / TX | Pads de prueba TP9 / TP8 |
| 2 | EN | EN | RC 10 k + 1 µF, pulsador RESET |

Ningún GPIO está asignado a dos funciones. Los 3 pines de strapping (2, 8, 9) tienen pull-up para permitir el arranque normal y el modo descarga por USB.

## Sonda de suelo
J2: pin 1 GND, pin 2 VCC conmutado (`SENS_VCC`), pin 3 salida analógica. El firmware enciende la sonda (GPIO4 en bajo), espera 200 ms, promedia 16 lecturas y la apaga. Una lectura < 80 mV o > 3150 mV se interpreta como "sonda desconectada o inválida" (**heurística; confirmar umbrales con medidas reales**).
El porcentaje de humedad es una **estimación calibrada para tu sonda y tu sustrato**, no una medida profesional.

## LEDs
Ánodo a 3V3, cátodo a GPIO vía 330 Ω → encienden con el GPIO en **bajo**. La corriente es de pocos mA con las tensiones directas típicas (rojo/verde/ámbar ≈ 2 V; **no medido**). Un LED azul (Vf ≈ 3 V) no sería adecuado con 330 Ω.

## Zumbador
Piezo SMD pasivo entre 3V3 y el drenador de un 2N7002; se excita con PWM de ~4 kHz. Si no lo quieres, no montes BZ1/Q2/R13/R14 (el firmware lo tolera).

## Antena
La huella del módulo incluye su zona de exclusión (sin cobre, vías ni componentes). El DRC no reporta infracciones. La antena queda orientada hacia el borde inferior (vista KiCad), a ≈ 0,8 mm del borde del OLED montado: **el OLED con respaldo metálico puede degradar el RF; v0.1 no usa Wi-Fi/BLE y no se ha medido nada.**

## Contraste con hojas de datos
| Componente | Estado |
|---|---|
| ESP32-C3-WROOM-02 (pines, strapping, alimentación) | ✅ contrastado con datasheet v1.7 |
| TSL25911FN (pin 1 SCL, 2 INT, 3 GND, 4 NC, 5 VDD, 6 SDA) | ✅ contrastado con datasheet de ams |
| SHT40, AP2112K, USBLC6-2SC6, AO3401A, 2N7002, USB-C, resto | ⚠️ solo símbolos oficiales de KiCad |
