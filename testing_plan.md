# Plan de pruebas — todo PENDIENTE (nada se ha probado en hardware)

| # | Prueba | Cómo | Criterio |
|---|---|---|---|
| 1 | Cortocircuitos | Multímetro 3V3–GND, VBUS–GND, 5V–3V3 | Sin cortos |
| 2 | Alimentación | USB-C, fuente limitada a 100 mA; medir TP3 (VBUS), TP1 (3V3) | 3V3 dentro de la tolerancia del LDO |
| 3 | CC / enumeración USB | Conectar a un PC; ver puerto serie del ESP32-C3 | Aparece el dispositivo |
| 4 | Carga de firmware | `pio run -t upload` | Subida correcta |
| 5 | I2C | Escáner I2C en TP4/TP5 | Se ven 0x3C, 0x44, 0x29 |
| 6 | SHT40 | Comparar con termómetro/higrómetro de referencia | Registrar error |
| 7 | TSL25911 | Comparar con luxómetro de referencia; **validar la fórmula de lux** | Registrar error |
| 8 | OLED | Pantallas principal, suelo, umbrales, calibración, sonido | Se muestran y navegan |
| 9 | Sonda de suelo | Medir TP6 (SOIL_ADC) con la sonda al aire, seca y en agua | Obtener `dry_mv` y `wet_mv` |
| 10 | Sonda desconectada | Quitar sonda | La pantalla muestra "SONDA?" |
| 11 | Calibración | Pantalla CALIBRAR: sonda seca (pulsación larga), sonda en agua (larga) | Porcentaje coherente; se conserva al reiniciar |
| 12 | LEDs y zumbador | Forzar estados SECO / OK / EXCESO | LED correcto; alerta sonora; se puede silenciar y desactivar |
| 13 | Botón | Pulsación corta y larga, sin falsos eventos | Correcto |
| 14 | Consumo | Amperímetro en serie en reposo y con pantalla | **Registrar** (no hay cifra previa) |
| 15 | Térmica | Comparar T del SHT40 con referencia tras 1 h | Registrar sesgo por calor del LDO/ESP32 |
| 16 | Ensamblaje | Acceso a conectores, encaje del OLED | Correcto |

Cómo obtener la calibración: sonda al aire (o suelo completamente seco) → "SECO"; sonda sumergida hasta la línea de máximo en agua (o suelo saturado) → "HÚMEDO". Los valores dependen de la sonda y del sustrato; no hay valores universales.
