# Notas de fabricación — FLORA v0.1

**Entregar al fabricante:** `FLORA_gerbers_for_fab.zip` (Gerbers + taladros). Pide siempre que revisen el contorno y te envíen la vista previa de sus CAM antes de producir.

## Especificación de la PCB
| Parámetro | Valor |
|---|---|
| Capas | 2 (cobre superior e inferior) |
| Tamaño | 56,53 × 53,04 mm (contorno irregular en forma de flor, recorte plano en el lado del USB-C) |
| Espesor | 1,6 mm (estándar; **el conector USB-C se diseñó para 1,6 mm**) |
| Cobre | 1 oz (35 µm) |
| Pista / separación mínimas usadas | 0,2 mm / 0,2 mm |
| Vía | 0,6 mm pad / 0,3 mm taladro (118 vías) |
| Taladro mínimo | 0,30 mm |
| Cobre al borde | ≥ 0,4 mm (el USB-C queda a ras del borde por diseño) |
| Acabado superficial | ENIG recomendado (DFN y pads finos); HASL sin plomo posible |
| Máscara de soldadura | Ver opciones abajo |
| Serigrafía | Blanca, líneas ≥ 0,15 mm, texto ≥ 0,8 mm |
| Panelizado | Ninguno (pieza única); pide al fabricante si necesita rieles |
| Sin V-cut ni mouse-bites | |

**Estas reglas son supuestos conservadores, no datos de tu laboratorio.** Si tu laboratorio no puede hacer 0,2/0,2 mm o taladros de 0,3 mm, la placa debe rediseñarse (ver `design_review.md`).

## Estética: qué es fabricación y qué es dibujo
- La **forma de flor** es el contorno real (`Edge_Cuts`).
- Los **colores** (lavanda/violeta, rosa pastel, crema) de `renders/` son **solo de presentación**. En fabricación solo existen: color de máscara, color de serigrafía y acabado de cobre. Los colores disponibles dependen del fabricante (habitual: verde, negro, blanco, rojo, azul; violeta/rosa no siempre). Confirma antes de pedir.
- Paleta sugerida: máscara violeta (si hay) o negra/blanca; serigrafía blanca; ENIG dorado. Los motivos botánicos (flores, hojas, estrellas) son serigrafía.

## Archivos incluidos en el ZIP
| Archivo | Función |
|---|---|
| `FLORA-F_Cu.gtl` | Cobre superior |
| `FLORA-B_Cu.gbl` | Cobre inferior |
| `FLORA-F_Mask.gts` | Máscara de soldadura superior (aperturas) |
| `FLORA-B_Mask.gbs` | Máscara de soldadura inferior |
| `FLORA-F_Silkscreen.gto` | Serigrafía superior |
| `FLORA-B_Silkscreen.gbo` | Serigrafía inferior |
| `FLORA-F_Paste.gtp` | Pasta de soldar superior (stencil) |
| `FLORA-B_Paste.gbp` | Pasta de soldar inferior |
| `FLORA-Edge_Cuts.gm1` | Contorno de la placa |
| `FLORA.drl` | Taladros (Excellon, mm) |
| `FLORA-drl_map.gbr` | Mapa de taladros |
| `FLORA-job.gbrjob` | Descriptor del trabajo |

Taladros (`FLORA.drl`): 0,30 mm × 130 (118 vías + 12 vías térmicas del módulo), 0,60 mm × 4, 0,65 mm × 2, 0,75 mm × 3, 1,00 mm × 4. (Cantidades según el archivo exportado.)
