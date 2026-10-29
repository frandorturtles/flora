#!/usr/bin/env python3
"""Genera bom.csv, pinout.csv y la tabla de componentes de ensamblaje desde flora_data.py."""
import csv, os, sys
from collections import OrderedDict
sys.path.insert(0, os.path.dirname(__file__)); import flora_data as D
HW = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ALT = {
 "ESP32-C3-WROOM-02-N4": "ESP32-C3-WROOM-02U-N4 (conector u.FL, otra huella de antena); ESP32-C3-MINI-1 (otra huella, no incluida en KiCad 7)",
 "SHT40-AD1B": "SHT41/SHT45 (misma huella DFN-4, mayor precision); SHT31-DIS (otra huella)",
 "TSL25911FN": "TSL2591 (mismo mapa de registros, otra huella); BH1750FVI (otra huella WSOF6I, direccion 0x23)",
 "AP2112K-3.3": "ME6211C33 / XC6220B331 / MIC5504-3.3 (SOT-23-5; verificar patillaje)",
 "USBLC6-2SC6": "PRTR5V0U2X (otra huella SOT-143B)", "AO3401A (P-MOSFET)": "Si2301 / DMG3415U (SOT-23, G-S-D igual: verificar)",
 "2N7002 (N-MOSFET)": "BSS138 / Si2302 (SOT-23)", "PKMCS0909E4000-R1 (piezo)": "Zumbador piezo SMD 9x9 mm de resonancia ~4 kHz equivalente; o no montar (BOM opcional)",
}
rows = OrderedDict()
for ref, lib, val, fp, mpn, nets in D.PARTS:
    key = (val, fp, mpn)
    rows.setdefault(key, []).append(ref)
def natkey(r): 
    import re; m = re.match(r"([A-Z]+)(\d+)", r); return (m.group(1), int(m.group(2)))
with open(os.path.join(HW, "bom.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["Referencias", "Cantidad", "Valor / descripcion", "Huella KiCad", "Fabricante / MPN (SIN verificar stock)", "Alternativas compatibles (a verificar)"])
    for (val, fp, mpn), refs in rows.items():
        refs = sorted(refs, key=natkey)
        w.writerow([" ".join(refs), len(refs), val, fp, mpn, ALT.get(val, "")])
    w.writerow([]); w.writerow(["NO EN PCB (comprar aparte)", 1, "Modulo OLED SSD1306 0.96in I2C 128x64, orden de pines GND-VCC-SCL-SDA", "Cabezal macho 4 pines", "Generico (verificar orden de pines VCC/GND: varia segun fabricante)", ""])
    w.writerow(["NO EN PCB (comprar aparte)", 1, "Sonda de humedad de suelo capacitiva (tipo v1.2) con cable JST-PH 3 pines GND-VCC-AOUT", "-", "Generico (calidad muy variable; ver testing_plan.md)", ""])
print("bom.csv:", sum(len(r) for r in rows.values()), "refs,", len(rows), "lineas")
# pinout
GPIO = {"1":"3V3","2":"EN","3":"GPIO4","4":"GPIO5","5":"GPIO6","6":"GPIO7","7":"GPIO8","8":"GPIO9","9":"GND","10":"GPIO10","11":"GPIO20 (RXD)","12":"GPIO21 (TXD)",
        "13":"GPIO18","14":"GPIO19","15":"GPIO3","16":"GPIO2","17":"GPIO1","18":"GPIO0","19":"GND (EPAD)"}
NOTE = {"SOIL_ADC":"ADC1_CH0; RC 1k+100nF; pull-down 470k (deteccion de sonda desconectada)","SOIL_PWR_N":"ACTIVO BAJO; gate del P-MOSFET Q1; pull-up 10k","LED_GRN":"ACTIVO BAJO (anodo a 3V3)",
        "LED_RED":"ACTIVO BAJO (anodo a 3V3)","LED_AMB":"ACTIVO BAJO (anodo a 3V3)","I2C_SDA":"I2C; pull-up 4.7k; SHT40 0x44, TSL25911 0x29, OLED 0x3C","I2C_SCL":"I2C; pull-up 4.7k",
        "BTN_USER":"Boton a GND; pull-up 10k; pin de strapping BOOT (GPIO9)","GPIO8_STRAP":"Strapping: pull-up 10k (necesario para modo descarga); sin uso","GPIO2_STRAP":"Strapping: pull-up 10k; sin uso",
        "BUZZER_PWM":"PWM ~4 kHz hacia gate de Q2 (2N7002)","USB_DN":"USB D- nativo (GPIO18)","USB_DP":"USB D+ nativo (GPIO19)","UART_TX":"UART0 TXD en pad de prueba TP8","UART_RX":"UART0 RXD en pad de prueba TP9","EN":"RC 10k+1uF + pulsador RESET (SW2)"}
u1 = [p for p in D.PARTS if p[0]=="U1"][0][5]
with open(os.path.join(HW, "pinout.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["Pin modulo (U1)", "Funcion GPIO", "Red", "Notas"])
    for n in sorted(u1, key=int): w.writerow([n, GPIO[n], u1[n], NOTE.get(u1[n], "")])
print("pinout.csv ok")
