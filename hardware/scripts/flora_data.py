"""FLORA - modelo de diseño (única fuente de verdad del esquemático).

Cada componente: ref, lib_id (símbolo KiCad), valor, huella, MPN/fabricante, {pin_número: red}.
Pines con red None se marcan No-Connect. El PCB se genera desde el netlist exportado del
esquemático (no desde este archivo), de modo que esquemático y PCB no pueden divergir.

Pines del módulo ESP32-C3-WROOM-02: datasheet v1.7, Table 3-1 (consultado el 2026-10-25).
Pines de SHT4x, TSL25911FN, AP2112K, USBLC6-2SC6, AO3401A, 2N7002, USB-C: símbolos oficiales de
KiCad 7.0.11 (pendiente de contraste con la hoja de datos de cada fabricante: ver design_review.md).
"""
GND, V33, VBUS, VSW = "GND", "+3V3", "VBUS", "SENS_VCC"

# (n, nombre, tipo) - datasheet ESP32-C3-WROOM-02 v1.7, Table 3-1
ESP32_PINS = [
    ("1", "3V3", "power_in"), ("2", "EN", "input"), ("3", "IO4", "bidirectional"),
    ("4", "IO5", "bidirectional"), ("5", "IO6", "bidirectional"), ("6", "IO7", "bidirectional"),
    ("7", "IO8", "bidirectional"), ("8", "IO9", "bidirectional"), ("9", "GND", "power_in"),
    ("10", "IO10", "bidirectional"), ("11", "RXD", "bidirectional"), ("12", "TXD", "bidirectional"),
    ("13", "IO18", "bidirectional"), ("14", "IO19", "bidirectional"), ("15", "IO3", "bidirectional"),
    ("16", "IO2", "bidirectional"), ("17", "IO1", "bidirectional"), ("18", "IO0", "bidirectional"),
    ("19", "GND", "power_in")]

R = "Resistor_SMD:R_0603_1608Metric"
C = "Capacitor_SMD:C_0603_1608Metric"
C8 = "Capacitor_SMD:C_0805_2012Metric"
L = "LED_SMD:LED_0603_1608Metric"
TP = "TestPoint:TestPoint_Pad_D1.5mm"

# ref, lib_id, valor, huella, MPN, {pin: red}
PARTS = [
    ("U1", "FLORA:ESP32-C3-WROOM-02", "ESP32-C3-WROOM-02-N4", "RF_Module:ESP32-C3-WROOM-02",
     "Espressif ESP32-C3-WROOM-02-N4",
     {"1": V33, "2": "EN", "3": "SOIL_PWR_N", "4": "LED_GRN", "5": "I2C_SDA", "6": "I2C_SCL",
      "7": "GPIO8_STRAP", "8": "BTN_USER", "9": GND, "10": "LED_AMB", "11": "UART_RX",
      "12": "UART_TX", "13": "USB_DN", "14": "USB_DP", "15": "LED_RED", "16": "GPIO2_STRAP",
      "17": "BUZZER_PWM", "18": "SOIL_ADC", "19": GND}),
    ("U2", "Sensor_Humidity:SHT4x", "SHT40-AD1B", "Sensor_Humidity:Sensirion_DFN-4_1.5x1.5mm_P0.8mm_SHT4x_NoCentralPad",
     "Sensirion SHT40-AD1B-R2", {"1": "I2C_SDA", "2": "I2C_SCL", "3": V33, "4": GND}),
    ("U3", "Sensor_Optical:TSL25911FN", "TSL25911FN", "OptoDevice:AMS_TSL25911FN",
     "ams-OSRAM TSL25911FN", {"1": "I2C_SCL", "2": None, "3": GND, "4": None, "5": V33, "6": "I2C_SDA"}),
    ("U4", "Regulator_Linear:AP2112K-3.3", "AP2112K-3.3", "Package_TO_SOT_SMD:SOT-23-5",
     "Diodes Inc. AP2112K-3.3TRG1", {"1": "VIN_PROT", "2": GND, "3": "VIN_PROT", "4": None, "5": V33}),
    ("U5", "Power_Protection:USBLC6-2SC6", "USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6",
     "STMicroelectronics USBLC6-2SC6", {"1": "USB_DP", "2": GND, "3": "USB_DN", "4": "USB_DN", "5": VBUS, "6": "USB_DP"}),
    ("J1", "Connector:USB_C_Receptacle_USB2.0_16P", "USB-C (5V + USB 2.0)",
     "Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal", "GCT USB4105-GF-A",
     {"A1": GND, "A12": GND, "B1": GND, "B12": GND, "S1": GND, "A4": VBUS, "A9": VBUS, "B4": VBUS,
      "B9": VBUS, "A5": "CC1", "B5": "CC2", "A6": "USB_DP", "B6": "USB_DP", "A7": "USB_DN",
      "B7": "USB_DN", "A8": None, "B8": None}),
    ("F1", "Device:Polyfuse", "PTC 500mA hold", "Fuse:Fuse_1206_3216Metric",
     "Bourns MF-MSMF050-2 (o equivalente)", {"1": VBUS, "2": "VIN_PROT"}),
    ("D1", "Device:D_TVS", "TVS 5V", "Diode_SMD:D_SOD-123F",
     "Littelfuse SMF5.0A (verificar polaridad/tension)", {"1": "VIN_PROT", "2": GND}),
    ("Q1", "Transistor_FET:AO3401A", "AO3401A (P-MOSFET)", "Package_TO_SOT_SMD:SOT-23",
     "Alpha&Omega AO3401A", {"1": "SOIL_PWR_N", "2": V33, "3": VSW}),
    ("Q2", "Transistor_FET:2N7002", "2N7002 (N-MOSFET)", "Package_TO_SOT_SMD:SOT-23",
     "2N7002 (onsemi/Nexperia)", {"1": "BUZ_GATE", "2": GND, "3": "BUZ_DRAIN"}),
    ("BZ1", "Device:Buzzer", "PKMCS0909E4000-R1 (piezo)", "Buzzer_Beeper:Buzzer_Murata_PKMCS0909E",
     "Murata PKMCS0909E4000-R1", {"1": V33, "2": "BUZ_DRAIN"}),
    ("J2", "Connector_Generic:Conn_01x03", "Sonda suelo (JST PH 3p: GND VCC AOUT)",
     "Connector_JST:JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical", "JST B3B-PH-K-S",
     {"1": GND, "2": VSW, "3": "SOIL_SIG"}),
    ("J3", "Connector_Generic:Conn_01x04", "OLED I2C (GND VCC SCL SDA)",
     "Connector_PinSocket_2.54mm:PinSocket_1x04_P2.54mm_Vertical", "Socket hembra 1x4 2.54mm",
     {"1": GND, "2": V33, "3": "I2C_SCL", "4": "I2C_SDA"}),
    ("SW1", "Switch:SW_Push", "USUARIO", "Button_Switch_SMD:SW_Push_1P1T_NO_CK_KMR2",
     "C&K KMR2 (o equivalente)", {"1": "BTN_USER", "2": GND}),
    ("SW2", "Switch:SW_Push", "RESET", "Button_Switch_SMD:SW_Push_1P1T_NO_CK_KMR2",
     "C&K KMR2 (o equivalente)", {"1": "EN", "2": GND}),
    ("D2", "Device:LED", "ROJO", L, "LED 0603 rojo", {"1": "LED_RED_K", "2": V33}),
    ("D3", "Device:LED", "VERDE", L, "LED 0603 verde", {"1": "LED_GRN_K", "2": V33}),
    ("D4", "Device:LED", "AMBAR", L, "LED 0603 ambar", {"1": "LED_AMB_K", "2": V33}),
    # Resistencias
    ("R1", "Device:R", "5.1k", R, "Yageo RC0603FR-075K1L", {"1": "CC1", "2": GND}),
    ("R2", "Device:R", "5.1k", R, "Yageo RC0603FR-075K1L", {"1": "CC2", "2": GND}),
    ("R3", "Device:R", "4.7k", R, "Yageo RC0603FR-074K7L", {"1": V33, "2": "I2C_SDA"}),
    ("R4", "Device:R", "4.7k", R, "Yageo RC0603FR-074K7L", {"1": V33, "2": "I2C_SCL"}),
    ("R5", "Device:R", "10k", R, "Yageo RC0603FR-0710KL", {"1": V33, "2": "EN"}),
    ("R6", "Device:R", "10k", R, "Yageo RC0603FR-0710KL", {"1": V33, "2": "BTN_USER"}),
    ("R7", "Device:R", "10k", R, "Yageo RC0603FR-0710KL", {"1": V33, "2": "GPIO2_STRAP"}),
    ("R8", "Device:R", "10k", R, "Yageo RC0603FR-0710KL", {"1": V33, "2": "GPIO8_STRAP"}),
    ("R9", "Device:R", "10k", R, "Yageo RC0603FR-0710KL", {"1": V33, "2": "SOIL_PWR_N"}),
    ("R10", "Device:R", "330", R, "Yageo RC0603FR-07330RL", {"1": "LED_RED", "2": "LED_RED_K"}),
    ("R11", "Device:R", "330", R, "Yageo RC0603FR-07330RL", {"1": "LED_GRN", "2": "LED_GRN_K"}),
    ("R12", "Device:R", "330", R, "Yageo RC0603FR-07330RL", {"1": "LED_AMB", "2": "LED_AMB_K"}),
    ("R13", "Device:R", "100", R, "Yageo RC0603FR-07100RL", {"1": "BUZZER_PWM", "2": "BUZ_GATE"}),
    ("R14", "Device:R", "100k", R, "Yageo RC0603FR-07100KL", {"1": "BUZ_GATE", "2": GND}),
    ("R15", "Device:R", "1k", R, "Yageo RC0603FR-071KL", {"1": "SOIL_SIG", "2": "SOIL_ADC"}),
    ("R16", "Device:R", "470k", R, "Yageo RC0603FR-07470KL", {"1": "SOIL_ADC", "2": GND}),
    # Condensadores
    ("C1", "Device:C", "10uF/10V", C8, "Samsung CL21A106KPFNNNE", {"1": "VIN_PROT", "2": GND}),
    ("C2", "Device:C", "10uF/10V", C8, "Samsung CL21A106KPFNNNE", {"1": V33, "2": GND}),
    ("C3", "Device:C", "100nF", C, "Samsung CL10B104KB8NNNC", {"1": V33, "2": GND}),
    ("C4", "Device:C", "100nF", C, "Samsung CL10B104KB8NNNC", {"1": V33, "2": GND}),
    ("C5", "Device:C", "100nF", C, "Samsung CL10B104KB8NNNC", {"1": V33, "2": GND}),
    ("C6", "Device:C", "1uF", C, "Samsung CL10A105KB8NNNC", {"1": "EN", "2": GND}),
    ("C7", "Device:C", "100nF", C, "Samsung CL10B104KB8NNNC", {"1": "BTN_USER", "2": GND}),
    ("C8", "Device:C", "100nF", C, "Samsung CL10B104KB8NNNC", {"1": "SOIL_ADC", "2": GND}),
    ("C9", "Device:C", "100nF", C, "Samsung CL10B104KB8NNNC", {"1": VSW, "2": GND}),
    # Puntos de prueba
    ("TP1", "Connector:TestPoint", "3V3", TP, "Pad de prueba", {"1": V33}),
    ("TP2", "Connector:TestPoint", "GND", TP, "Pad de prueba", {"1": GND}),
    ("TP3", "Connector:TestPoint", "VBUS", TP, "Pad de prueba", {"1": VBUS}),
    ("TP4", "Connector:TestPoint", "SDA", TP, "Pad de prueba", {"1": "I2C_SDA"}),
    ("TP5", "Connector:TestPoint", "SCL", TP, "Pad de prueba", {"1": "I2C_SCL"}),
    ("TP6", "Connector:TestPoint", "SOIL", TP, "Pad de prueba", {"1": "SOIL_ADC"}),
    ("TP7", "Connector:TestPoint", "EN", TP, "Pad de prueba", {"1": "EN"}),
    ("TP8", "Connector:TestPoint", "TX", TP, "Pad de prueba", {"1": "UART_TX"}),
    ("TP9", "Connector:TestPoint", "RX", TP, "Pad de prueba", {"1": "UART_RX"}),
    ("TP10", "Connector:TestPoint", "BOOT", TP, "Pad de prueba", {"1": "BTN_USER"}),
]
