# Checklist de Gerbers

Antes de enviar:
- [ ] Contorno cerrado y único (`Edge_Cuts`), sin cobre fuera.
- [ ] 9 capas + taladros presentes (tabla en `fabrication_notes.md`).
- [ ] Abrir los Gerbers en un visor externo (gerbv, KiCad Gerber Viewer o el visor del fabricante) y comprobar contorno, taladros y serigrafía.
- [ ] Taladro mínimo 0,3 mm y pista/separación 0,2 mm aceptados por el fabricante.
- [ ] Revisar USB-C a ras del borde y recorte plano.
- [ ] Revisar que el fabricante no cambie el color de máscara sin avisar.
- [ ] Confirmar espesor 1,6 mm y acabado.

Verificación hecha en el desarrollo: lectura de las 9 capas con gerbonara y revisión visual del render (`renders/top_view.png`, `bottom_view.png`). **No** se ha comprobado con el CAM de ningún fabricante.

Regenerar (KiCad 7):
```
cd hardware
kicad-cli pcb export gerbers --layers "F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts,F.Paste,B.Paste" --subtract-soldermask -o gerbers/ FLORA.kicad_pcb
kicad-cli pcb export drill --format excellon --drill-origin absolute --excellon-units mm --generate-map --map-format gerberx2 -o drill/ FLORA.kicad_pcb
kicad-cli pcb export pos --format csv --units mm --side both -o assembly/FLORA_pos.csv FLORA.kicad_pcb
```
