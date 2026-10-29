#!/usr/bin/env python3
"""Renders de presentación a partir de los Gerbers (gerbonara, independiente de KiCad). Colores = solo presentación."""
import re, sys, os, warnings
warnings.filterwarnings("ignore")
import cairosvg
from gerbonara import LayerStack
sys.path.insert(0, os.path.dirname(__file__)); import build_pcb as B
HW = B.HW
st = LayerStack.open(os.path.join(HW, "gerbers"))
(x0, y0), (x1, y1) = st.outline.bounding_box(); m = 3
bounds = ((x0 - m, y0 - m), (x1 + m, y1 + m))
poly = [(B.CX - x, B.CY + y) for x, y in B.flower_polygon().exterior.coords]       # coords KiCad
pts = " ".join(f"{x:.4f},{-y:.4f}" for x, y in poly)                                # a coords Gerber (y invertida)
def parts(layer, fg):
    s = str(layer.to_svg(force_bounds=bounds, fg=fg, bg="none"))
    head = re.search(r"<svg[^>]*>", s).group(0); body = s[s.index(head) + len(head): s.rindex("</svg>")]
    return head, body
def compose(side, base, under, expo, silk, out, mirror=False):
    chunks = []; head = None
    for kind, fg in (("copper", under), ("mask", expo), ("silk", silk)):
        h, b = parts(st[(side, kind)], fg); head = head or h; chunks.append(b)
    tr = re.search(r'<g transform="([^"]*)"', chunks[0]).group(1)
    base_poly = f'<g transform="{tr}"><polygon points="{pts}" fill="{base}"/></g>'
    svg = head + '<rect x="-1000" y="-1000" width="3000" height="3000" fill="#fdf6ff"/>' + base_poly + "".join(chunks) + "</svg>"
    cairosvg.svg2png(bytestring=svg.encode(), write_to=out, output_width=1800)
    if side == "bottom":   # vista desde atrás: voltear horizontalmente
        from PIL import Image, ImageOps; ImageOps.mirror(Image.open(out)).save(out)
os.makedirs(os.path.join(HW, "..", "renders"), exist_ok=True)
compose("top", "#6b3fa3", "#8a64c4", "#e6c27a", "#fff6fb", os.path.join(HW, "..", "renders", "top_view.png"))
compose("bottom", "#7a4fb5", "#9570cf", "#e6c27a", "#fff6fb", os.path.join(HW, "..", "renders", "bottom_view.png"))
print("renders ok")
