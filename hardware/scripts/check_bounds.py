import sys, pcbnew
from shapely.geometry import box
sys.path.insert(0,'.'); import build_pcb as B
def check(board, shape, margin=0.5):
    inner = shape.buffer(-margin); bad=[]
    for fp in board.GetFootprints():
        bb = fp.GetBoundingBox(False, False)
        x0,y0,x1,y1 = [pcbnew.ToMM(v) for v in (bb.GetX(), bb.GetY(), bb.GetRight(), bb.GetBottom())]
        poly = box(x0-B.CX, -(y1-B.CY), x1-B.CX, -(y0-B.CY))   # a coordenadas de diseño (sin giro)
        # el diseño está girado 180°: convertir
        poly = box(-(x1-B.CX), (y0-B.CY), -(x0-B.CX), (y1-B.CY))
        if not inner.contains(poly):
            bad.append((fp.GetReference(), round(poly.difference(inner).area,2)))
    return bad
if __name__ == "__main__":
    board, shape, _ = B.build()
    print(check(board, shape))
