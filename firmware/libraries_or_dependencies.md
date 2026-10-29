# Dependencias

| Dependencia | Versión | Uso | Estado |
|---|---|---|---|
| PlatformIO `espressif32` | ^6.9.0 | Plataforma ESP32-C3 + Arduino core | No resuelta en el entorno de desarrollo (sin acceso al registro) |
| U8g2 (olikraus) | ^2.35.19 | OLED SSD1306 | Idem |
| Wire, Preferences, Arduino.h | del core | I2C, NVS, GPIO | Idem |
| `flora_logic.h` | propia | Calibración, estados, botón, alertas, CRC SHT4x, lux | Probada en PC |

Los drivers del SHT40 y del TSL25911 están escritos a mano (sin librerías externas). Revisa que la versión de U8g2 exista antes de compilar.
