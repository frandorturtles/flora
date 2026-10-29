#!/usr/bin/env python3
"""Serigrafía decorativa/identificativa sobre FLORA.kicad_pcb ya rutada. Coordenadas de diseño (Y arriba) -> KiCad."""
import math, os, sys
import pcbnew, shapely
from pcbnew import FromMM as mm, ToMM as tomm
from shapely.geometry import Point, box
sys.path.insert(0, os.path.dirname(__file__))
import build_pcb as B
HW = B.HW
board = pcbnew.LoadBoard(os.path.join(HW, "FLORA.kicad_pcb"))
shape = B.flower_polygon()
for f in board.GetFootprints():   # las etiquetas funcionales sustituyen a estos designadores en serigrafía (siguen en Fab)
    if f.GetReference() in ("SW1", "SW2", "J1", "J2", "U3") or f.GetReference().startswith("TP"):
        f.Reference().SetLayer(pcbnew.B_Fab if f.IsFlipped() else pcbnew.F_Fab)
V = lambda x, y: pcbnew.VECTOR2I(mm(float(B.CX - x)), mm(float(B.CY + y)))

def text(s, x, y, h=0.9, th=0.15, layer=pcbnew.F_SilkS, bottom=False, bold=False):
    t = pcbnew.PCB_TEXT(board); t.SetText(s); t.SetPosition(V(x, y)); t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(mm(h), mm(h))); t.SetTextThickness(mm(th))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); t.SetMirrored(bottom); board.Add(t)

def line(pts, layer=pcbnew.F_SilkS, w=0.15, closed=False):
    seq = list(pts) + ([pts[0]] if closed else [])
    for a, b in zip(seq[:-1], seq[1:]):
        s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(layer); s.SetWidth(mm(w))
        s.SetStart(V(*a)); s.SetEnd(V(*b)); board.Add(s)

def circle(cx, cy, r, w=0.15, layer=pcbnew.F_SilkS):
    s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_CIRCLE); s.SetLayer(layer); s.SetWidth(mm(w))
    s.SetCenter(V(cx, cy)); s.SetEnd(V(cx + r, cy)); board.Add(s)

def flower(cx, cy, r=1.5):
    for k in range(5):
        a = math.radians(90 + k * 72); circle(cx + 0.55 * r * math.cos(a), cy + 0.55 * r * math.sin(a), 0.42 * r)
    circle(cx, cy, 0.2 * r)

def leaf(cx, cy, ang, L=2.4, W=0.8):
    pts = []
    for t in [i / 8 for i in range(9)]:
        pts.append((t * L, W * math.sin(math.pi * t)))
    pts += [(t * L, -W * math.sin(math.pi * t)) for t in [i / 8 for i in range(7, 0, -1)]]
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    P = [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts]
    line(P, closed=True); line([(cx, cy), (cx + L * ca, cy + L * sa)], w=0.12)

def star(cx, cy, r=1.0):
    pts = []
    for k in range(8):
        rr = r if k % 2 == 0 else r * 0.28; a = math.radians(90 + k * 45); pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    line(pts, closed=True)

# ---- etiquetas funcionales (coordenadas de diseño)
text("FLORA", -15.0, 18.0, h=2.0, th=0.3)
text("USB-C 5V", 0.0, -17.7, h=0.9)
text("SOIL", 15.2, -16.9, h=0.9); text("GND VCC AO", 15.2, -8.9, h=0.8)
text("DRY", 12.2, 20.0, h=0.8); text("OK", 12.2, 16.8, h=0.8); text("WET", 12.2, 13.6, h=0.8)
text("USER", 18.6, -3.7, h=0.8); text("RESET", -19.0, 14.7, h=0.8)
text("BUZZER", -21.0, -10.6, h=0.8)
text("SHT40", 25.0, -7.0, h=0.8); text("LUX", 18.5, 2.6, h=0.8)
# ---- cara inferior
text("FLORA", 0.0, 12.0, h=3.4, th=0.5, layer=pcbnew.B_SilkS, bottom=True)
text("Smart Plant Companion", 0.0, 8.2, h=1.1, th=0.2, layer=pcbnew.B_SilkS, bottom=True)
text("v0.1  2026", 0.0, 5.4, h=0.9, th=0.15, layer=pcbnew.B_SilkS, bottom=True)
for i in range(10):
    name = ["3V3", "GND", "VBUS", "SDA", "SCL", "SOIL", "EN", "TX", "RX", "BOOT"][i]
    x = -8.0 + (i % 5) * 4.0; y = -3.0 if i < 5 else -7.0
    text(name, x, y - 1.5 if i < 5 else y - 1.5, h=0.8, layer=pcbnew.B_SilkS, bottom=True)

# ---- motivos decorativos en zonas libres
occupied = shapely.unary_union([box(tomm(f.GetBoundingBox(False, False).GetX()) - 0, 0, 0, 0) for f in []] or [Point(0, 0).buffer(0)])
boxes = []
for f in board.GetFootprints():
    bb = f.GetBoundingBox(False, False)
    x0, x1 = B.CX - tomm(bb.GetRight()), B.CX - tomm(bb.GetX()); y0, y1 = tomm(bb.GetY()) - B.CY, tomm(bb.GetBottom()) - B.CY
    if f.GetReference() == "U1": y1 = y1  # el módulo: solo su cuerpo
    boxes.append(box(x0 - 0.8, y0 - 0.8, x1 + 0.8, y1 + 0.8))
import numpy as np
for t in board.GetDrawings():
    if t.GetClass() == "PCB_TEXT":
        bb = t.GetBoundingBox(); x0, x1 = B.CX - tomm(bb.GetRight()), B.CX - tomm(bb.GetX()); y0, y1 = tomm(bb.GetY()) - B.CY, tomm(bb.GetBottom()) - B.CY
        boxes.append(box(x0 - 0.6, y0 - 0.6, x1 + 0.6, y1 + 0.6))
occ = shapely.unary_union(boxes); inner = shape.buffer(-1.6)
placed = []
def free(x, y, r): 
    c = Point(x, y).buffer(r)
    return inner.contains(c) and not occ.intersects(c) and all((x - a) ** 2 + (y - b) ** 2 > (r + rr + 0.4) ** 2 for a, b, rr in placed)
motifs = [("flower", 1.6)] * 5 + [("leaf", 1.5)] * 6 + [("star", 1.0)] * 6
cands = [(x, y) for y in np.arange(-24, 24, 0.8) for x in np.arange(-26, 26, 0.8)]
count = {"flower": 0, "leaf": 0, "star": 0}
for kind, r in motifs:
    for (x, y) in sorted(cands, key=lambda p: -(p[0] ** 2 + p[1] ** 2)):   # preferir los bordes de los pétalos
        if free(x, y, r):
            if kind == "flower": flower(x, y, r)
            elif kind == "leaf": leaf(x - 1.2, y, (x * 7 + y * 13) % 360, L=2.4)
            else: star(x, y, r)
            placed.append((x, y, r)); count[kind] += 1; break
print("motivos:", count)
pcbnew.SaveBoard(os.path.join(HW, "FLORA.kicad_pcb"), board)
pcbnew.WriteDRCReport(board, "/tmp/drc_final.rpt", pcbnew.EDA_UNITS_MILLIMETRES, True)
