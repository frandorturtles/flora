# Revisión de diseño — FLORA v0.1

## Verificaciones automáticas realizadas
| Comprobación | Herramienta | Resultado |
|---|---|---|
| Netlist esquemático vs modelo de diseño | `check_netlist.py` (kicad-cli) | ✅ idéntico (53 componentes, 34 redes) |
| DRC PCB | KiCad 7.0.11 (API pcbnew `WriteDRCReport`) | ✅ 0 errores, 0 pads sin conectar. 1 aviso de serigrafía recortada por máscara. 53 avisos "librería no configurada" (ejecución sin tabla de librerías; no aparecen con las librerías estándar) |
| Contorno, cobre al borde | DRC (borde 0,4 mm) | ✅ sin infracciones |
| Zona de antena | DRC (área de exclusión del módulo) | ✅ sin pistas/vías/relleno |
| Gerbers | gerbonara (lector independiente) | ✅ 9 capas leídas, contorno 56,5 × 53,0 mm |
| Revisión visual | Render desde Gerbers | ✅ |
| Lógica del firmware | g++ en PC | ✅ pruebas pasan |

## NO realizado
- **ERC de KiCad** (la CLI de KiCad 7 no lo tiene): ejecutarlo en el editor o con KiCad 8 (el CI lo intenta).
- **Compilación del firmware para ESP32-C3.**
- **Contraste con las hojas de datos** de SHT40, AP2112K, USBLC6-2SC6, AO3401A, 2N7002, USB-C, zumbador.
- **Verificación de stock y números de parte.**
- **Simulación** de cualquier tipo.
- **Render 3D** (KiCad 7 no lo ofrece por CLI; se entrega el STEP de la placa desnuda).
- **Fabricación y todas las pruebas físicas.**

## Limitaciones y riesgos conocidos
1. **Router propio**, no revisado por un humano: 574 segmentos, 118 vías, 893 mm de pista, todo a 0,2 mm. Revisar visualmente en KiCad; pistas de alimentación finas (0,2 mm) para ≤ 500 mA.
2. **Vía en pad** en el GND de C6 (el router no encontró otra salida).
3. **OLED sobre el módulo ESP32** y a ~0,8 mm de la zona de antena: posible degradación de RF; la altura del módulo OLED debe permitir el espacio.
4. **Orden de pines del OLED** variable según fabricante: riesgo de invertir alimentación.
5. **Sonda desconectada:** detección heurística (pull-down 470 kΩ y rango de tensión); depende de la sonda real.
6. **TSL25911FN:** el firmware usa registros y fórmula de lux del TSL2591; falta validar.
7. **TVS D1:** polaridad/tipo por confirmar.
8. **LDO/PTC al límite** si se activa Wi-Fi.
9. **Reglas de fabricación supuestas** (0,2/0,2, vía 0,6/0,3): confirmar con tu laboratorio.
10. **Sin agujeros de montaje** en v0.1.
11. **SHT40 en DFN:** requiere aire caliente/reflujo. Se eliminó del footprint un área de exclusión interna del SHT4x (ocupaba sus propios pads).
12. **Serigrafía decorativa** colocada automáticamente en zonas libres; revisar contra el Gerber de serigrafía.
13. Los colores de las imágenes **no** son capas de fabricación.
