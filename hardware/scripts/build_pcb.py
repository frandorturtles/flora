#!/usr/bin/env python3
"""Genera hardware/FLORA.kicad_pcb (sin rutar) a partir del netlist del esquemático.
Coordenadas de diseño en mm con Y hacia arriba y origen en el centro de la flor; se convierten a KiCad.
Uso: python3 build_pcb.py            -> escribe FLORA_unrouted.kicad_pcb
"""
import math, os, subprocess, sys, xml.etree.ElementTree as ET
import pcbnew
from pcbnew import VECTOR2I, FromMM as mm
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union
from shapely import affinity

HW = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FPDIR = "/usr/share/kicad/footprints/"
CX, CY = 100.0, 100.0                       # centro de la flor en coordenadas KiCad (mm)
# Diseño girado 180 grados: USB-C arriba, OLED legible con el USB-C arriba (orientación de uso)
K = lambda x, y: VECTOR2I(mm(CX - x), mm(CY + y))
GROT = 180.0

# ------------------------------------------------------------------ geometría de la flor
D_PETAL, R_PETAL, N_PETAL = 16.0, 13.0, 5
ANG0 = 270.0                                 # un pétalo apunta hacia abajo (USB-C)
USB_FLAT_Y = -27.0                           # recorte plano para el conector USB-C

def flower_polygon():
    petals = [Point(D_PETAL * math.cos(math.radians(ANG0 + i * 360 / N_PETAL)),
                    D_PETAL * math.sin(math.radians(ANG0 + i * 360 / N_PETAL))).buffer(R_PETAL, 64)
              for i in range(N_PETAL)]
    core = Point(0, 0).buffer(D_PETAL, 64)
    shape = unary_union(petals + [core])
    shape = shape.buffer(2.0, 32).buffer(-2.0, 32)           # redondea los valles entre pétalos
    shape = shape.intersection(box(-60, USB_FLAT_Y, 60, 60))   # plano para el USB-C
    return shape

# ------------------------------------------------------------------ netlist
def load_netlist():
    subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", "/tmp/flora.xml",
                    f"{HW}/FLORA.kicad_sch"], check=True, capture_output=True)
    root = ET.parse("/tmp/flora.xml").getroot()
    comps = {}
    for c in root.find("components"):
        fields = {f.get("name"): f.text for f in c.iter("field")}
        ts = c.find("tstamps")
        comps[c.get("ref")] = dict(value=c.find("value").text, fp=c.find("footprint").text, fields=fields,
                                   uuid=ts[0].text if ts is not None and len(ts) else None)
    nets = {}
    for n in root.find("nets"):
        nets[n.get("name")] = [(x.get("ref"), x.get("pin")) for x in n]
    return comps, nets

# ------------------------------------------------------------------ colocación (x, y, rot, lado)
PL = {
 "U1": (0, 5, 0), "J1": (0, -22.8, 0),
 # columna izquierda (pines 1-9 del módulo)
 "C3": (-11.8, 10.4, 0), "R5": (-11.8, 8.5, 0), "C6": (-11.8, 6.6, 0), "R9": (-11.8, 4.7, 0), "R8": (-11.8, 2.8, 0),
 "R6": (-11.8, 0.9, 0), "C7": (-11.8, -1.0, 0), "R3": (-11.8, -2.9, 0), "R4": (-11.8, -4.8, 0),
 # columna derecha (pines 10-18)
 "R15": (11.8, 10.4, 0), "C8": (11.8, 8.5, 0), "R16": (11.8, 6.6, 0), "R7": (11.8, 4.7, 0),
 # alimentación bajo el módulo
 "U4": (0.0, -6.0, 0), "C1": (-4.6, -6.6, 90), "C2": (4.4, -4.6, 0),
 "F1": (-6.0, -10.5, 0), "D1": (-0.5, -10.5, 0), "U5": (6.5, -11.0, 0),
 "R1": (-8.4, -16.4, 0), "R2": (8.4, -16.4, 0),
 "J3": (3.81, -14.5, 270),
 # pétalo derecho-inferior: sensores / sonda
 "U2": (25.0, -3.0, 0), "C5": (25.0, 0.6, 90), "U3": (18.5, 5.0, 180), "C4": (18.5, 7.8, 0),
 "J2": (13.2, -12.4, 0), "SW1": (18.6, -6.6, 0), "Q1": (23.8, -7.0, 0), "C9": (21.6, -10.2, 0),
 # pétalo izquierdo-inferior: zumbador
 "BZ1": (-21.0, -4.9, 0), "Q2": (-19.0, 3.2, 0), "R13": (-18.0, 6.6, 0), "R14": (-18.0, 8.6, 0),
 "SW2": (-19.0, 11.8, 0),
 # pétalo derecho-superior: LEDs
 "D2": (15.6, 20.0, 90), "D3": (15.6, 16.8, 90), "D4": (15.6, 13.6, 90),
 "R10": (18.0, 20.0, 90), "R11": (18.0, 16.8, 90), "R12": (18.0, 13.6, 90),
}
# puntos de prueba en la cara inferior (2 filas)
for i in range(10):
    PL[f"TP{i+1}"] = (-8.0 + (i % 5) * 4.0, -3.0 if i < 5 else -7.0, 0, "B")
SILK_REF = {"U3", "U4", "U5", "J1", "J2", "J3", "SW1", "SW2", "BZ1", "D2", "D3", "D4", "Q1", "Q2", "F1", "D1"}

def build():
    comps, nets = load_netlist()
    board = pcbnew.BOARD()
    bds = board.GetDesignSettings()
    bds.SetCopperLayerCount(2)
    bds.m_TrackMinWidth = mm(0.2); bds.m_MinClearance = mm(0.2); bds.m_ViasMinSize = mm(0.6)
    bds.m_MinThroughDrill = mm(0.3); bds.m_ViasMinAnnularWidth = mm(0.15)
    bds.m_MinSilkTextHeight = mm(0.8); bds.m_MinSilkTextThickness = mm(0.12)
    bds.m_CopperEdgeClearance = mm(0.4)
    nc = bds.m_NetSettings.m_DefaultNetClass
    nc.SetClearance(mm(0.2)); nc.SetTrackWidth(mm(0.25)); nc.SetViaDiameter(mm(0.6)); nc.SetViaDrill(mm(0.3))

    # redes
    netinfo = {}
    for name in nets:
        ni = pcbnew.NETINFO_ITEM(board, name); board.Add(ni); netinfo[name] = ni
    pin2net = {(r, p): n for n, nodes in nets.items() for r, p in nodes}

    # contorno (Edge.Cuts) como polilínea cerrada de segmentos finos
    shape = flower_polygon()
    pts = list(shape.exterior.coords)
    for a, b in zip(pts[:-1], pts[1:]):
        s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
        s.SetStart(K(*a)); s.SetEnd(K(*b)); s.SetWidth(mm(0.1)); board.Add(s)

    # footprints
    for ref, c in comps.items():
        lib, name = c["fp"].split(":")
        fp = pcbnew.FootprintLoad(FPDIR + lib + ".pretty", name)
        assert fp, (ref, c["fp"])
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(ref); fp.SetValue(c["value"])
        x, y, rot = PL[ref][:3]
        bottom = len(PL[ref]) > 3 and PL[ref][3] == "B"
        board.Add(fp)
        fp.SetPosition(K(x, y))
        if bottom: fp.Flip(K(x, y), False)
        fp.SetOrientationDegrees(rot + GROT if not bottom else rot + GROT)
        for pad in fp.Pads():
            key = (ref, pad.GetName())
            if key in pin2net: pad.SetNet(netinfo[pin2net[key]])
        if ref == "U1":   # vías térmicas del módulo: 0.3 mm de taladro (mínimo conservador)
            for pad in fp.Pads():
                if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                    pad.SetDrillSize(pcbnew.VECTOR2I(mm(0.3), mm(0.3))); pad.SetSize(pcbnew.VECTOR2I(mm(0.6), mm(0.6)))
        if ref == "U2":   # elimina el área de exclusión interna del SHT4x (ocupa sus propios pads); se documenta
            for z in list(fp.Zones()): fp.Remove(z)
        fp.Value().SetVisible(False)
        r = fp.Reference(); r.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8))); r.SetTextThickness(mm(0.13))
        if ref in SILK_REF and not bottom:
            r.SetLayer(pcbnew.F_SilkS)
        elif bottom:
            r.SetLayer(pcbnew.B_SilkS)
        else:
            r.SetLayer(pcbnew.F_Fab)
        # propiedades para BOM
        try:
            fp.SetProperty("MPN", c["fields"].get("MPN", ""))
        except Exception:
            pass
    return board, shape, netinfo

if __name__ == "__main__":
    board, shape, netinfo = build()
    out = os.path.join(HW, "FLORA_unrouted.kicad_pcb")
    pcbnew.SaveBoard(out, board)
    print("guardado", out, "huella flor: bounds", [round(v, 2) for v in shape.bounds], "área", round(shape.area, 1))
