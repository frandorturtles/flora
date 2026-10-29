# Scripts generadores (hardware)

Todo el hardware se genera de forma reproducible a partir de `flora_data.py` (única fuente de verdad del esquemático).

Requisitos: KiCad 7.0.x (con `kicad-cli` y el módulo Python `pcbnew`), Python 3.12, `pip install kiutils shapely numpy cairosvg gerbonara`, g++.

Orden:
1. `python3 build_schematic.py` — genera `FLORA.kicad_sch` y `FLORA.kicad_sym`.
2. `python3 check_netlist.py` — comprueba que el netlist exportado coincide con el modelo.
3. `g++ -O2 -std=c++17 -o /tmp/flora_router router.cpp` — router propio de rejilla (0,05 mm).
4. `python3 route_pcb.py` — coloca (`build_pcb.py`), rutea, añade planos GND y vías de costura, guarda `FLORA.kicad_pcb`, escribe `/tmp/drc.rpt`.
5. `python3 finish_pcb.py` — serigrafía (logotipo, etiquetas, flores y hojas) y DRC final.
6. Exportación: ver `manufacturing/gerber_checklist.md` (comandos `kicad-cli`).
7. `python3 render_gerbers.py` — imágenes desde los Gerbers.

Aviso: el router es propio y simple (no es Freerouting). Tras abrir el proyecto en KiCad, revisa el rutado a mano.
