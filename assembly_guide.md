# Guía de montaje — FLORA v0.1 (no probada)

**Herramientas:** soldador de punta fina, pasta de soldar + aire caliente (o horno de reflujo), pinzas, flux, lupa/microscopio, multímetro.

1. **Inspección de la PCB:** contorno, cortocircuitos 3V3–GND y VBUS–GND con el multímetro (antes de montar).
2. **Cara superior, pasta de soldar** (stencil `F_Paste` o aplicación manual): resistencias/condensadores 0603 y 0805, LEDs (polaridad: cátodo hacia la resistencia), SOT-23 (Q1, Q2, U4, U5), diodo D1 (polaridad), PTC F1.
3. **ICs delicados:** U2 SHT40 (DFN 1,5 × 1,5 mm) y U3 TSL25911FN (DFN-6 2 × 2 mm) con aire caliente; cuida la orientación (marca de pin 1 en serigrafía/`assembly_top_fab.png`). Mantén U2 limpio de flux.
4. **Módulo U1 (ESP32-C3-WROOM-02):** alinear pin 1 con la marca; soldar los 18 pines del borde y el pad térmico central (vías térmicas de 0,3 mm).
5. **USB-C J1** y **pulsadores SW1/SW2**.
6. **THT:** J2 (JST-PH 3 pines) y J3 (zócalo hembra 1×4).
7. **Zumbador BZ1** (opcional).
8. **C6 tiene una vía en el pad de GND** (compromiso de la v0.1): usa poca pasta o suelda con cuidado.
9. **Limpieza** con alcohol isopropílico.
10. **Antes de energizar:** repetir pruebas de cortocircuito. Alimentar desde una fuente limitada a 100 mA la primera vez.
11. **OLED:** comprueba el orden de pines de **tu** módulo (esta placa espera GND-VCC-SCL-SDA, de izquierda a derecha con los pines hacia arriba). Si es VCC-GND-SCL-SDA, **no lo conectes**: invertiría la alimentación.
12. Conecta la sonda al JST (GND-VCC-AOUT) y programa el firmware (ver `firmware/README.md`).

Alturas: el OLED va montado sobre el zócalo cubriendo el centro y parte del módulo ESP32; deja ≥ 5 mm entre la placa y el módulo OLED (zócalo estándar).
