# Notas de ensamblaje — FLORA v0.1

- Archivo de posiciones: `hardware/assembly/FLORA_pos.csv` (coordenadas en mm, origen absoluto de KiCad; rotaciones de KiCad, **pueden requerir ajuste según el ensamblador**).
- Lista de materiales: `hardware/bom.csv` (sin verificar stock).
- Componentes sensibles: SHT40 y TSL25911FN (DFN) y módulo ESP32 (pad térmico central).
- Polaridades: LEDs D2–D4 (cátodo hacia la resistencia), TVS D1, PTC F1 (sin polaridad), pin 1 de ICs y módulo.
- No montar BZ1/Q2/R13/R14 si no quieres alerta sonora.
- Piezas fuera de la PCB: módulo OLED 0,96" (cabezal macho de 4 pines) y sonda capacitiva con cable JST-PH.
- **Vía en pad** en GND de C6.
- Vista de referencia: `renders/assembly_top_fab.png` (capa Fab de KiCad).
