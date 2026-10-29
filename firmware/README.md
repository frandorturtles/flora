# Firmware FLORA v0.1 (ESP32-C3, Arduino)

**Estado:** escrito para el hardware FLORA v0.1. **No compilado para ESP32-C3 ni probado en placa.** La lógica pura (`lib/flora_logic`) sí se prueba en PC.

## Compilar y cargar
```
pip install platformio
cd firmware
pio run -e flora            # compilar
pio run -e flora -t upload  # cargar por USB-C (si no entra, mantén el botón USUARIO (BOOT) y pulsa RESET)
pio device monitor
```
El CI de GitHub intenta `pio run`. Si falla, corrige antes de usarlo.

## Pruebas en PC (sin hardware)
```
g++ -std=gnu++17 -Wall -Wextra -Ilib/flora_logic test/test_logic.cpp -o /tmp/t && /tmp/t
```
Resultado en el desarrollo: "todas las pruebas OK".

## GPIO
| GPIO | Función |
|---|---|
| 0 | SOIL_ADC (ADC1_CH0) |
| 1 | Zumbador (PWM) |
| 3 / 5 / 10 | LED rojo / verde / ámbar (**activos en bajo**) |
| 4 | Alimentación de la sonda (**activo en bajo**) |
| 6 / 7 | SDA / SCL |
| 9 | Botón USUARIO (pin BOOT) |
| 18 / 19 | USB |
| 20 / 21 | UART0 (pads de prueba) |

## Uso
- **Pulsación corta:** siguiente pantalla (Principal → Suelo → Umbrales → Calibrar → Sonido).
- **Pulsación larga:** Principal: silenciar alerta 10 min · Umbrales: sube el umbral "seco" de 5 en 5 (10–45 %) · Calibrar: 1ª larga guarda SECO, 2ª guarda HÚMEDO · Sonido: activar/desactivar.
- Mientras no haya calibración válida se muestran los mV del ADC y el estado "Sin calibrar" (no hay valores universales).
- Sensor no disponible o lectura inválida → mensajes "SHT40 ?", "TSL ?", "SONDA?"; el firmware reintenta cada 10 s sin bloquearse.

## Limitaciones
- Driver del TSL25911 basado en el mapa de registros del TSL2591 (ID 0x50, gain 25×, 200 ms): **validar**.
- Ganancia/tiempo fijos: sin autorango (saturación → "Luz: saturada").
- El umbral "exceso" (70 %) no se edita en la interfaz (solo el de seco).
- El porcentaje de humedad es una **estimación calibrada**, no una medida profesional.
- Una única espera bloqueante de 10 ms por lectura del SHT40.
