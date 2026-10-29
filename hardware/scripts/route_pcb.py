#!/usr/bin/env python3
"""Rutea con router.cpp (rejilla 0.05 mm), añade planos GND, guarda FLORA.kicad_pcb."""
import os, subprocess, sys
import numpy as np, shapely
import pcbnew
sys.path.insert(0, os.path.dirname(__file__))
import build_pcb as B
from pcbnew import FromMM as mm, ToMM as tomm
HW = B.HW; PITCH = 0.05; TW = 0.2; CLR = 0.2; VD = 0.6; VDR = 0.3; EDGE = 0.4

def kc(x, y): return (B.CX - x, B.CY + y)

def export(board, shape, path):
    pts = [kc(*p) for p in shape.exterior.coords]
    poly = shapely.Polygon(pts)
    gx, gy = B.CX - 31.0, B.CY - 31.0
    W = H = int(62.0 / PITCH)
    xs = gx + np.arange(W) * PITCH; ys = gy + np.arange(H) * PITCH
    X, Y = np.meshgrid(xs, ys)
    # zona de exclusión de antena (regla del propio footprint del módulo)
    keeps = []
    for fp in board.GetFootprints():
        for z in fp.Zones():
            if z.GetIsRuleArea():
                bb = z.GetBoundingBox(); keeps.append((tomm(bb.GetX()), tomm(bb.GetY()), tomm(bb.GetRight()), tomm(bb.GetBottom())))
    def raster(margin, kmargin):
        a = shapely.contains_xy(poly.buffer(-margin), X, Y)
        for keep in keeps:
            k = (X > keep[0] - kmargin) & (X < keep[2] + kmargin) & (Y > keep[1] - kmargin) & (Y < keep[3] + kmargin)
            a &= ~k
        return a.astype(np.uint8)
    aT = raster(EDGE + TW / 2 + 0.03, TW / 2); aV = raster(EDGE + VDR + 0.03, VDR)
    with open("/tmp/rT.bin", "wb") as f: f.write(aT.tobytes() * 2)
    with open("/tmp/rV.bin", "wb") as f: f.write(aV.tobytes() * 2)
    lines = [f"GRID {gx} {gy} {PITCH} {W} {H}", f"PARAMS {TW/2} {CLR} {VDR} 500 3", "RASTER /tmp/rT.bin /tmp/rV.bin"]
    padlist = []; netpads = {}
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if not (p.IsOnLayer(pcbnew.F_Cu) or p.IsOnLayer(pcbnew.B_Cu)): continue
            bb = p.GetBoundingBox()
            lm = (1 if p.IsOnLayer(pcbnew.F_Cu) else 0) | (2 if p.IsOnLayer(pcbnew.B_Cu) else 0)
            net = p.GetNetCode() if p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH else 0
            tht = p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH)
            pid = len(padlist); padlist.append((fp.GetReference(), p.GetNumber(), net))
            lines.append(f"PAD {pid} {net if net > 0 else -1} {lm} {tomm(bb.GetX())} {tomm(bb.GetY())} {tomm(bb.GetRight())} {tomm(bb.GetBottom())} {int(tht)}")
            if net > 0: netpads.setdefault(net, []).append(pid)
    for net, ids in netpads.items():
        name = board.FindNet(net).GetNetname().replace(" ", "_")
        lines.append(f"NET {net} {name} {1 if name == 'GND' else 0} {len(ids)} " + " ".join(map(str, ids)))
    open(path, "w").write("\n".join(lines) + "\n")
    return padlist

def _segd(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return ((px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2) ** 0.5

def best_via_spot(board, pad):
    bb = pad.GetBoundingBox(); c = pad.GetPosition(); hx = max(0, tomm(bb.GetWidth()) / 2 - 0.3); hy = max(0, tomm(bb.GetHeight()) / 2 - 0.3)
    best, bd = c, -1
    for fx in (-1, -0.5, 0, 0.5, 1):
        for fy in (-1, -0.5, 0, 0.5, 1):
            x, y = tomm(c.x) + fx * hx, tomm(c.y) + fy * hy; d = 9
            for t in board.GetTracks():
                if t.GetNetCode() == pad.GetNetCode(): continue
                if t.GetClass() == "PCB_VIA": d = min(d, ((x - tomm(t.GetPosition().x)) ** 2 + (y - tomm(t.GetPosition().y)) ** 2) ** 0.5 - 0.3 - 0.3)
                else: d = min(d, _segd(x, y, tomm(t.GetStart().x), tomm(t.GetStart().y), tomm(t.GetEnd().x), tomm(t.GetEnd().y)) - 0.3 - tomm(t.GetWidth()) / 2)
            for fp in board.GetFootprints():
                for q in fp.Pads():
                    if q.GetNetCode() == pad.GetNetCode() or not (q.IsOnLayer(pcbnew.F_Cu) or q.IsOnLayer(pcbnew.B_Cu)): continue
                    qb = q.GetBoundingBox(); qx0, qy0, qx1, qy1 = tomm(qb.GetX()), tomm(qb.GetY()), tomm(qb.GetRight()), tomm(qb.GetBottom())
                    ddx = max(qx0 - x, 0, x - qx1); ddy = max(qy0 - y, 0, y - qy1); d = min(d, (ddx * ddx + ddy * ddy) ** 0.5 - 0.3)
            if d > bd: bd, best = d, pcbnew.VECTOR2I(mm(x), mm(y))
    return best

def apply(board, shape, netinfo, out, padlist):
    byid = {board.FindNet(n).GetNetCode(): board.FindNet(n) for n in netinfo}
    placed = []
    for l in out.splitlines():
        p = l.split()
        if p[0] == "SEG":
            t = pcbnew.PCB_TRACK(board); t.SetStart(pcbnew.VECTOR2I(mm(float(p[2])), mm(float(p[3])))); t.SetEnd(pcbnew.VECTOR2I(mm(float(p[4])), mm(float(p[5]))))
            t.SetWidth(mm(TW)); t.SetLayer(pcbnew.F_Cu if p[1] == "0" else pcbnew.B_Cu); t.SetNet(byid[int(p[6])]); board.Add(t)
        elif p[0] == "VIA":
            vx, vy = float(p[1]), float(p[2])
            if any(abs(vx - a) < 0.6 and abs(vy - b) < 0.6 for a, b in placed): continue
            placed.append((vx, vy))
            v = pcbnew.PCB_VIA(board); v.SetPosition(pcbnew.VECTOR2I(mm(float(p[1])), mm(float(p[2])))); v.SetViaType(pcbnew.VIATYPE_THROUGH)
            v.SetWidth(mm(VD)); v.SetDrill(mm(VDR)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(byid[int(p[3])]); board.Add(v)
    # pads GND que el router no pudo enlazar: vía en el propio pad (documentado como compromiso de la v0.1)
    for l in out.splitlines():
        if l.startswith("FAIL GND"):
            ref, num, _ = padlist[int(l.split()[-1])]
            for fp in board.GetFootprints():
                if fp.GetReference() == ref:
                    for p in fp.Pads():
                        if p.GetNumber() == num and p.GetNetname() == "GND":
                            pos = best_via_spot(board, p)
                            v = pcbnew.PCB_VIA(board); v.SetPosition(pos); v.SetViaType(pcbnew.VIATYPE_THROUGH)
                            v.SetWidth(mm(VD)); v.SetDrill(mm(VDR)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(p.GetNet()); board.Add(v)
                            print("via en pad:", ref, num)
    # prolongar extremos de pista hasta el centro del pad (dentro del cobre del propio pad)
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetNetCode() <= 0 or not (p.IsOnLayer(pcbnew.F_Cu) or p.IsOnLayer(pcbnew.B_Cu)): continue
            bb = p.GetBoundingBox(); bb.Inflate(mm(0.08)); c = p.GetPosition()
            for t in list(board.GetTracks()):
                if t.GetClass() != "PCB_TRACK" or t.GetNetCode() != p.GetNetCode() or not p.IsOnLayer(t.GetLayer()): continue
                for getp, setp in ((t.GetStart, t.SetStart), (t.GetEnd, t.SetEnd)):
                    q = getp()
                    if bb.Contains(q) and (q.x != c.x or q.y != c.y):
                        n = pcbnew.PCB_TRACK(board); n.SetStart(q); n.SetEnd(c); n.SetWidth(t.GetWidth()); n.SetLayer(t.GetLayer()); n.SetNet(t.GetNet()); board.Add(n)
    # planos GND en ambas caras
    gnd = board.FindNet("GND")
    inner = shape.buffer(-0.5)
    from shapely import affinity as _af
    shape_kc = shapely.Polygon([(B.CX - x - B.CX, B.CY + y - B.CY) for x, y in shape.exterior.coords])
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board); z.SetLayer(layer); z.SetNet(gnd); z.SetMinThickness(mm(0.2)); z.SetLocalClearance(mm(0.2))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL); z.SetThermalReliefGap(mm(0.3)); z.SetThermalReliefSpokeWidth(mm(0.3))
        ol = z.Outline(); ol.NewOutline()
        for x, y in list(inner.exterior.coords)[:-1]:
            kx, ky = kc(x, y); ol.Append(mm(kx), mm(ky))
        board.Add(z)
    out_path = os.path.join(HW, "FLORA.kicad_pcb")
    pcbnew.SaveBoard(out_path, board)
    board = pcbnew.LoadBoard(out_path)
    bds = board.GetDesignSettings(); bds.m_HoleClearance = mm(0.15); bds.m_MinResolvedSpokes = 1; bds.m_HoleToHoleMin = mm(0.25)
    board.BuildConnectivity()
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    # vías de costura GND (malla de 4 mm) solo donde ambos planos tienen cobre libre alrededor
    zf = [z for z in board.Zones() if z.GetLayer() == pcbnew.F_Cu][0]; zb = [z for z in board.Zones() if z.GetLayer() == pcbnew.B_Cu][0]
    gnd = board.FindNet("GND"); n = 0
    vias = [(tomm(t.GetPosition().x), tomm(t.GetPosition().y)) for t in board.GetTracks() if t.GetClass() == 'PCB_VIA']
    def far(x, y): return all((x - a) ** 2 + (y - b) ** 2 > 0.8 ** 2 for a, b in vias)
    import math as _m
    for iy in range(-14, 14):
        for ix in range(-14, 14):
            x, y = B.CX + ix * 4.0 + 0.7, B.CY + iy * 4.0 + 0.7
            ok = True
            for dx, dy in [(0, 0)] + [(0.7 * _m.cos(a * _m.pi / 4), 0.7 * _m.sin(a * _m.pi / 4)) for a in range(8)]:
                pt = pcbnew.VECTOR2I(mm(x + dx), mm(y + dy))
                if not (zf.HitTestFilledArea(pcbnew.F_Cu, pt) and zb.HitTestFilledArea(pcbnew.B_Cu, pt)): ok = False; break
            if ok and far(x, y) and shapely.Point(x - B.CX, y - B.CY).within(shape_kc.buffer(-1.2)):
                vias.append((x, y))
                v = pcbnew.PCB_VIA(board); v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y))); v.SetViaType(pcbnew.VIATYPE_THROUGH)
                v.SetWidth(mm(VD)); v.SetDrill(mm(VDR)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(gnd); board.Add(v); n += 1
    # una vía por cada isla de cobre superior (evita regiones de GND sin conexión al plano inferior)
    fpl = zf.GetFilledPolysList(pcbnew.F_Cu)
    for i in range(fpl.OutlineCount()):
        bb = fpl.Outline(i).BBox(); x0, y0 = tomm(bb.GetX()), tomm(bb.GetY()); w, h = tomm(bb.GetWidth()), tomm(bb.GetHeight())
        done = False
        for jy in range(int(h / 0.25) + 1):
            for jx in range(int(w / 0.25) + 1):
                x, y = x0 + jx * 0.25, y0 + jy * 0.25
                if far(x, y) and all(zf.HitTestFilledArea(pcbnew.F_Cu, pcbnew.VECTOR2I(mm(x + dx), mm(y + dy))) and zb.HitTestFilledArea(pcbnew.B_Cu, pcbnew.VECTOR2I(mm(x + dx), mm(y + dy)))
                       for dx, dy in [(0, 0)] + [(0.34 * _m.cos(a * _m.pi / 3), 0.34 * _m.sin(a * _m.pi / 3)) for a in range(6)]):
                    v = pcbnew.PCB_VIA(board); v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y))); v.SetViaType(pcbnew.VIATYPE_THROUGH)
                    v.SetWidth(mm(VD)); v.SetDrill(mm(VDR)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(gnd); board.Add(v); vias.append((x, y)); n += 1; done = True; break
            if done: break
    print("vias de costura GND:", n)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    # fragmentos diminutos de cobre superior sin vía (no caben vías): se impiden con un área de exclusión de relleno
    vpos = [t.GetPosition() for t in board.GetTracks() if t.GetClass() == "PCB_VIA"]
    fpl = zf.GetFilledPolysList(pcbnew.F_Cu); small = []
    for i in range(fpl.OutlineCount()):
        o = fpl.Outline(i); bb = o.BBox()
        if not any(o.PointInside(v) for v in vpos) and tomm(bb.GetWidth()) * tomm(bb.GetHeight()) < 3.0:
            small.append((tomm(bb.GetX()), tomm(bb.GetY()), tomm(bb.GetRight()), tomm(bb.GetBottom())))
    for (x0, y0, x1, y1) in small:
        ra = pcbnew.ZONE(board); ra.SetIsRuleArea(True); ra.SetDoNotAllowCopperPour(True); ra.SetDoNotAllowTracks(False); ra.SetDoNotAllowVias(False)
        ra.SetDoNotAllowPads(False); ra.SetDoNotAllowFootprints(False); ra.SetLayer(pcbnew.F_Cu)
        ol = ra.Outline(); ol.NewOutline()
        for px, py in ((x0 - 0.15, y0 - 0.15), (x1 + 0.15, y0 - 0.15), (x1 + 0.15, y1 + 0.15), (x0 - 0.15, y1 + 0.15)): ol.Append(mm(px), mm(py))
        board.Add(ra)
    print("fragmentos pequeños excluidos:", len(small))
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(out_path, board)
    pcbnew.WriteDRCReport(board, "/tmp/drc.rpt", pcbnew.EDA_UNITS_MILLIMETRES, True)
    print("guardado", out_path)

if __name__ == "__main__":
    board, shape, netinfo = B.build()
    padlist = export(board, shape, "/tmp/route_in.txt")
    r = subprocess.run(["/tmp/flora_router", "/tmp/route_in.txt"], capture_output=True, text=True, timeout=280)
    open("/tmp/route_out.txt", "w").write(r.stdout)
    apply(board, shape, netinfo, r.stdout, padlist)
    print(r.stdout.count("SEG"), "segmentos;", r.stdout.count("VIA"), "vias;", [l for l in r.stdout.splitlines() if l.startswith(("FAIL", "DONE"))][:20], r.stderr[-300:])
