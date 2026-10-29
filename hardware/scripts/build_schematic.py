#!/usr/bin/env python3
"""Genera hardware/FLORA.kicad_sch (y FLORA.kicad_sym) desde flora_data.py. KiCad 7."""
import copy, os, sys, uuid
from kiutils.schematic import Schematic
from kiutils.symbol import SymbolLib
from kiutils.items.schitems import (SchematicSymbol, LocalLabel, Connection, NoConnect,
                                    SymbolProjectInstance, SymbolProjectPath)
from kiutils.items.common import Position, Property, Effects, Font, Justify, Stroke, TitleBlock
sys.path.insert(0, os.path.dirname(__file__))
import flora_data as D

HW = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SYM = "/usr/share/kicad/symbols/"
NEWID = lambda: str(uuid.uuid4())

# ---------------------------------------------------------------- símbolo ESP32 (datasheet v1.7)
def esp32_symbol_text():
    byname = {p[0]: p for p in D.ESP32_PINS}
    left = ["2", "18", "17", "16", "15", "3", "4", "5", "6"]          # EN, IO0..IO7
    right = ["7", "8", "10", "13", "14", "11", "12"]                  # IO8, IO9, IO10, IO18, IO19, RXD, TXD
    out = ['(kicad_symbol_lib (version 20220914) (generator flora)',
           ' (symbol "ESP32-C3-WROOM-02" (in_bom yes) (on_board yes)',
           '  (property "Reference" "U" (at -10.16 17.78 0) (effects (font (size 1.27 1.27)) (justify left)))',
           '  (property "Value" "ESP32-C3-WROOM-02" (at 10.16 17.78 0) (effects (font (size 1.27 1.27)) (justify right)))',
           '  (property "Footprint" "RF_Module:ESP32-C3-WROOM-02" (at 0 -22 0) (effects (font (size 1.27 1.27)) hide))',
           '  (property "Datasheet" "https://www.espressif.com/sites/default/files/documentation/esp32-c3-wroom-02_datasheet_en.pdf" (at 0 -24 0) (effects (font (size 1.27 1.27)) hide))',
           '  (symbol "ESP32-C3-WROOM-02_0_1" (rectangle (start -10.16 15.24) (end 10.16 -15.24) (stroke (width 0.254) (type default)) (fill (type background))))',
           '  (symbol "ESP32-C3-WROOM-02_1_1"']
    def pin(n, x, y, ang, side):
        _, name, typ = byname[n]
        disp = {"IO0": "IO0/ADC1_0", "IO1": "IO1/ADC1_1", "IO2": "IO2/ADC1_2/STRAP", "IO3": "IO3/ADC1_3",
                "IO4": "IO4/ADC1_4", "IO5": "IO5/ADC2_0", "IO6": "IO6", "IO7": "IO7", "IO8": "IO8/STRAP",
                "IO9": "IO9/STRAP", "IO10": "IO10", "IO18": "IO18/USB_D-", "IO19": "IO19/USB_D+",
                "RXD": "RXD/GPIO20", "TXD": "TXD/GPIO21"}.get(name, name)
        return (f'   (pin {typ} line (at {x} {y} {ang}) (length 2.54) (name "{disp}" (effects (font (size 1.27 1.27)))) '
                f'(number "{n}" (effects (font (size 1.27 1.27)))))')
    out.append(pin("1", 0, 17.78, 270, "top"))
    for i, n in enumerate(left):  out.append(pin(n, -12.7, 10.16 - 2.54 * i, 0, "l"))
    for i, n in enumerate(right): out.append(pin(n, 12.7, 10.16 - 2.54 * i, 180, "r"))
    out.append(pin("9", 0, -17.78, 90, "b"))
    out.append(pin("19", 2.54, -17.78, 90, "b"))
    out += ['  ))', ')']
    return "\n".join(out)

open(os.path.join(HW, "FLORA.kicad_sym"), "w").write(esp32_symbol_text() + "\n")

# ---------------------------------------------------------------- carga de símbolos
_libs = {}
def get_lib(name):
    if name not in _libs:
        path = os.path.join(HW, "FLORA.kicad_sym") if name == "FLORA" else SYM + name + ".kicad_sym"
        _libs[name] = {s.entryName: s for s in SymbolLib.from_file(path).symbols}
    return _libs[name]

def flat_symbol(lib_id):
    lib, name = lib_id.split(":")
    s = get_lib(lib)[name]
    if s.extends:
        parent = get_lib(lib)[s.extends]
        c = copy.deepcopy(s); c.extends = None
        c.units = copy.deepcopy(parent.units)
        for u in c.units:
            u.entryName = u.entryName.replace(parent.entryName, name, 1)
        # propiedades que el hijo no define
        have = {p.key for p in c.properties}
        for p in parent.properties:
            if p.key not in have: c.properties.append(copy.deepcopy(p))
        s = c
    else:
        s = copy.deepcopy(s)
    s.libraryNickname = lib
    return s

def pins_of(sym):
    return [(p.number, p.name, p.position.X, p.position.Y, p.position.angle) for u in sym.units for p in u.pins]

# ---------------------------------------------------------------- colocación (mm, múltiplos de 1.27)
POS = {
 # alimentación
 "J1": (50.8, 76.2), "U5": (114.3, 50.8), "F1": (101.6, 109.22), "D1": (116.84, 109.22), "C1": (132.08, 109.22),
 "U4": (172.72, 76.2), "C2": (210.82, 109.22), "C3": (226.06, 109.22), "R1": (66.04, 109.22), "R2": (81.28, 109.22),
 # MCU
 "U1": (310.0, 76.2), "R5": (254.0, 139.7), "C6": (269.24, 139.7), "R6": (284.48, 139.7), "C7": (299.72, 139.7),
 "R7": (314.96, 139.7), "R8": (330.2, 139.7), "C4": (345.44, 139.7), "SW1": (370.0, 60.96), "SW2": (370.0, 91.44),
 # sensores y periféricos
 "U2": (45.72, 190.5), "C5": (86.36, 215.9), "U3": (127.0, 190.5), "R3": (167.64, 215.9), "R4": (182.88, 215.9),
 "J3": (215.9, 190.5), "J2": (254.0, 190.5), "Q1": (302.26, 190.5), "R9": (322.58, 215.9), "C9": (337.82, 215.9),
 "R15": (353.06, 215.9), "C8": (368.3, 215.9), "R16": (383.54, 215.9),
 "Q2": (302.26, 241.3), "R13": (279.4, 261.62), "R14": (294.64, 261.62), "BZ1": (330.2, 241.3),
 "D2": (45.72, 261.62), "R10": (66.04, 261.62), "D3": (96.52, 261.62), "R11": (116.84, 261.62),
 "D4": (147.32, 261.62), "R12": (167.64, 261.62),
}
for i in range(10): POS[f"TP{i+1}"] = (30.48 + i * 15.24, 30.48) if False else (205.74 + i * 15.24, 30.48)
FLAGS = {("U4", "1"), ("J1", "A12"), ("J1", "A4")}   # PWR_FLAG

# ---------------------------------------------------------------- construcción
sch = Schematic.create_new()
sch.version = 20230121; sch.generator = "flora"
sch.paper.paperSize = "A3"
sch.uuid = NEWID()
sch.titleBlock = TitleBlock()
sch.titleBlock.title = "FLORA - Smart Plant Companion"
sch.titleBlock.date = "2026-10-25"; sch.titleBlock.revision = "v0.1 (prototipo, sin fabricar)"
sch.titleBlock.company = "Proyecto academico - Ing. Electronica"
sch.titleBlock.comments = {1: "Autora: Francesca Martinez", 2: "ESP32-C3-WROOM-02 + SHT40 + TSL25911 + OLED SSD1306", 3: "Alimentacion USB-C 5 V, sin bateria (v1)"}

libsyms = {}
def need(lib_id):
    if lib_id not in libsyms:
        libsyms[lib_id] = flat_symbol(lib_id)
    return libsyms[lib_id]

def eff(h=1.27, hide=False, justify=None):
    return Effects(font=Font(height=h, width=h), hide=hide, justify=Justify(horizontally=justify) if justify else Justify())

def add_wire(a, b):
    sch.graphicalItems.append(Connection(type="wire", points=[Position(*a), Position(*b)], stroke=Stroke(width=0), uuid=NEWID()))

def place(lib_id, ref, value, fp, mpn, xy, nets, power_sym=False):
    s = need(lib_id)
    lib, name = lib_id.split(":")
    x, y = xy
    props = [Property("Reference", ref, 0, Position(x + 2.54, y - 5.08, 0), eff(hide=power_sym)),
             Property("Value", value, 1, Position(x + 2.54, y - 2.54, 0), eff()),
             Property("Footprint", fp, 2, Position(x, y, 0), eff(hide=True)),
             Property("Datasheet", "~", 3, Position(x, y, 0), eff(hide=True))]
    if mpn: props.append(Property("MPN", mpn, 4, Position(x, y, 0), eff(hide=True)))
    inst = SchematicSymbol(libraryNickname=lib, entryName=name, position=Position(x, y, 0), unit=1,
                           inBom=not power_sym, onBoard=True, uuid=NEWID(), properties=props,
                           pins={}, instances=[SymbolProjectInstance(name="FLORA", paths=[SymbolProjectPath(
                               sheetInstancePath="/" + sch.uuid, reference=ref, unit=1)])])
    for num, pname, px, py, ang in pins_of(s):
        inst.pins[num] = NEWID()
    sch.schematicSymbols.append(inst)
    return s

OUT = {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}   # dirección saliente en pantalla (x,y_pantalla) según ángulo del pin
LBL_ANG = {(-1, 0): 180, (1, 0): 0, (0, -1): 90, (0, 1): 270}
seen_pin_pos = set()
PWR = {"GND": "power:GND", "+3V3": "power:+3V3", "VBUS": "power:VBUS"}
pwr_count = [0]

def power_instance(net, at, outward):
    pwr_count[0] += 1
    lib_id = PWR[net]; s = need(lib_id)
    default_dir = (0, 1) if net == "GND" else (0, -1)
    rot = {(0, 1): 0, (-1, 0): 90, (0, -1): 180, (1, 0): 270}     # GND: gráfico hacia abajo por defecto
    if net != "GND":
        rot = {(0, -1): 0, (-1, 0): 270, (0, 1): 180, (1, 0): 90}
    ang = rot[outward]
    lib, name = lib_id.split(":")
    x, y = at
    props = [Property("Reference", f"#PWR{pwr_count[0]:03d}", 0, Position(x, y, 0), eff(hide=True)),
             Property("Value", net, 1, Position(x, y, 0), eff(hide=True)),
             Property("Footprint", "", 2, Position(x, y, 0), eff(hide=True)),
             Property("Datasheet", "", 3, Position(x, y, 0), eff(hide=True))]
    inst = SchematicSymbol(libraryNickname=lib, entryName=name, position=Position(x, y, ang), unit=1, inBom=False,
                           onBoard=False, uuid=NEWID(), properties=props, pins={"1": NEWID()},
                           instances=[SymbolProjectInstance(name="FLORA", paths=[SymbolProjectPath(
                               sheetInstancePath="/" + sch.uuid, reference=f"#PWR{pwr_count[0]:03d}", unit=1)])])
    sch.schematicSymbols.append(inst)

def flag_instance(at, outward, net):
    pwr_count[0] += 1
    lib_id = "power:PWR_FLAG"; need(lib_id)
    x, y = at
    ref = f"#FLG{pwr_count[0]:03d}"
    ang = {(0, -1): 0, (-1, 0): 270, (0, 1): 180, (1, 0): 90}[outward]
    props = [Property("Reference", ref, 0, Position(x, y, 0), eff(hide=True)), Property("Value", "PWR_FLAG", 1, Position(x, y, 0), eff(hide=True)),
             Property("Footprint", "", 2, Position(x, y, 0), eff(hide=True)), Property("Datasheet", "", 3, Position(x, y, 0), eff(hide=True))]
    sch.schematicSymbols.append(SchematicSymbol(libraryNickname="power", entryName="PWR_FLAG", position=Position(x, y, ang), unit=1,
        inBom=False, onBoard=False, uuid=NEWID(), properties=props, pins={"1": NEWID()},
        instances=[SymbolProjectInstance(name="FLORA", paths=[SymbolProjectPath(sheetInstancePath="/" + sch.uuid, reference=ref, unit=1)])]))

for ref, lib_id, value, fp, mpn, nets in D.PARTS:
    s = place(lib_id, ref, value, fp, mpn, POS[ref], nets)
    x, y = POS[ref]
    pin_list = pins_of(s)
    # pines no listados en 'nets' => error de diseño
    nums = {p[0] for p in pin_list}
    assert set(nets) <= nums, (ref, set(nets) - nums)
    done = set()
    for num, pname, px, py, ang in pin_list:
        if num not in nets: raise SystemExit(f"{ref} pin {num} ({pname}) sin red definida")
        net = nets[num]
        ax, ay = x + px, y - py                        # coordenada absoluta del extremo del pin
        key = (round(ax, 2), round(ay, 2), net)
        if key in done: continue                       # pines apilados (GND del USB-C)
        done.add(key)
        ox, oy = OUT[int(ang) % 360]
        if net is None:
            sch.noConnects.append(NoConnect(position=Position(ax, ay), uuid=NEWID())); continue
        # el USB-C tiene pines apilados con redes distintas en el mismo punto: separar con stub inclinado
        L = 2.54
        end = (ax + ox * L, ay + oy * L)
        add_wire((ax, ay), end)
        if net in PWR:
            power_instance(net, end, (ox, oy))
        else:
            sch.labels.append(LocalLabel(text=net, position=Position(end[0], end[1], LBL_ANG[(ox, oy)]),
                                          effects=Effects(font=Font(height=1.27, width=1.27),
                                          justify=Justify(horizontally="left" if LBL_ANG[(ox, oy)] in (0, 90) else "right")), uuid=NEWID()))
        if (ref, num) in FLAGS:
            flag_instance(end, (ox, oy), net)

# embebe símbolos
for lib_id, s in libsyms.items():
    sch.libSymbols.append(s)
sch.to_file(os.path.join(HW, "FLORA.kicad_sch"))
print("OK esquemático:", len(sch.schematicSymbols), "símbolos,", len(sch.labels), "etiquetas")
