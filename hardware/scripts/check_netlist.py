#!/usr/bin/env python3
"""Compara el netlist exportado del esquemático con el modelo de diseño (flora_data.py)."""
import sys, os, subprocess, xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(__file__)); import flora_data as D
HW = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
subprocess.run(["kicad-cli","sch","export","netlist","--format","kicadxml","-o","/tmp/flora.xml",f"{HW}/FLORA.kicad_sch"],check=True,capture_output=True)
root = ET.parse("/tmp/flora.xml").getroot()
got = {}
for n in root.find("nets"):
    name = n.get("name").lstrip("/")
    for node in n: got[(node.get("ref"), node.get("pin"))] = name if not name.startswith("unconnected") else None
bad = 0
for ref, lib, val, fp, mpn, nets in D.PARTS:
    for pin, net in nets.items():
        g = got.get((ref, pin), "MISSING")
        if g != net: print("DIFF", ref, pin, "esperado", net, "netlist", g); bad += 1
exp = {(r, p) for r, *_, nets in D.PARTS for p in nets}
for k in got:
    if k not in exp: print("EXTRA", k); bad += 1
print("netlist == modelo" if not bad else f"{bad} diferencias")
sys.exit(1 if bad else 0)
