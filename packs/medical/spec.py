"""Pack spec: fictional medical-device maker (bedside and portable devices). Company, parts, prices and volumes are invented.

Rule bases cite real regimes (FDA QMSR, FD&C s524B) as screening inputs. See rules/medical.json for sources and dates.
"""

PARTS = {
    "SPO2-MOD": ("Pulse oximetry SpO2 sensor module", "Sensing"),
    "ECG-AFE": ("ECG analog front-end module 5-lead", "Sensing"),
    "NIBP-PMP": ("NIBP cuff inflation pump assembly", "Sensing"),
    "TRD-US": ("Ultrasound transducer array 3.5MHz", "Sensing"),
    "MCU-V1": ("Main control board monitor V1", "Electronics"),
    "MCU-I2": ("Main control board pump I2", "Electronics"),
    "MCU-U3": ("Main control board ultrasound U3", "Electronics"),
    "WIFI-MOD": ("WiFi module 2.4GHz dual-band", "Electronics"),
    "BLE-MOD": ("Bluetooth LE module 2.4GHz", "Electronics"),
    "LCD-7": ("Touch display 7in", "Display"),
    "LCD-4": ("Touch display 4in", "Display"),
    "BAT-2S": ("Li-ion battery pack 2S 3.4Ah", "Power"),
    "PSU-24": ("Medical power supply 24V 60W", "Power"),
    "PMP-PER": ("Peristaltic pump mechanism", "Fluidics"),
    "OCC-SEN": ("Occlusion sensor assembly", "Fluidics"),
    "ENC-V1": ("Enclosure housing monitor V1", "Housing"),
    "ENC-I2": ("Enclosure housing pump I2", "Housing"),
    "ENC-U3": ("Enclosure housing ultrasound U3", "Housing"),
    "GSK-BLK": ("Silicone gasket seal black", "Housing"),
    "GSK-CLR": ("Silicone gasket seal clear", "Housing"),
    "FAS-M2": ("Screw M2x6 pan head", "Hardware"),
    "FAS-M3": ("Screw M3x8 pan head", "Hardware"),
}

# parts the clinical variants must source from qualified suppliers only
GOV_REQ = {
    "SPO2-MOD", "ECG-AFE", "NIBP-PMP", "TRD-US", "PMP-PER", "OCC-SEN", "MCU-V1", "MCU-I2", "MCU-U3",
    "PSU-24", "BAT-2S", "WIFI-MOD", "BLE-MOD",
}
REQ_BASIS = {
    "SPO2-MOD": "regulatory", "ECG-AFE": "regulatory", "NIBP-PMP": "regulatory", "TRD-US": "regulatory",
    "PMP-PER": "regulatory", "OCC-SEN": "regulatory", "MCU-V1": "regulatory", "MCU-I2": "regulatory",
    "MCU-U3": "regulatory", "PSU-24": "standard", "BAT-2S": "standard",
    "WIFI-MOD": "buyer_imposed", "BLE-MOD": "buyer_imposed",
}
BASIS_NOTE = {
    "regulatory": "Safety-critical component: supplier controls apply under 21 CFR Part 820 (FDA QMSR, effective 2 Feb 2026, which incorporates ISO 13485 clause 7.4 purchasing controls). Screening input, not a legal determination; confirm with regulatory affairs.",
    "standard": "Battery or power component expected to carry safety certification under the device's applicable standards. Screening input; confirm the standards list with regulatory affairs.",
    "buyer_imposed": "Wireless module: the device is likely a 'cyber device' under FD&C Act s524B (SBOM, vulnerability plan), and hospital customers often add attestations. Check the governing contract.",
}
CHECKED_ON = "2026-11-14"

SUPPLIERS = {
    "SUP01": ("Northbridge Sensors", "US", "Y", "Manufacturer", "NS"),
    "SUP02": ("Kestrel Sensing GmbH", "Germany", "Y", "Manufacturer", "KS"),
    "SUP03": ("Shenhua Sensor Co", "China", "N", "Manufacturer", "SH"),
    "SUP04": ("Lakeshore Medical Electronics", "US", "Y", "Manufacturer", "LM"),
    "SUP05": ("Dongyang Boards", "China", "N", "Manufacturer", "DY"),
    "SUP06": ("Fjord Display Tech", "Denmark", "Y", "Manufacturer", "FD"),
    "SUP07": ("Brightview Panels", "China", "N", "Manufacturer", "BV"),
    "SUP08": ("Cellvance Power", "US", "Y", "Manufacturer", "CV"),
    "SUP09": ("Hanbit Energy", "South Korea", "Y", "Manufacturer", "HE"),
    "SUP10": ("Greenlight Cells", "China", "N", "Manufacturer", "GL"),
    "SUP11": ("Precision Flow Systems", "US", "Y", "Manufacturer", "PF"),
    "SUP12": ("Polyform Housings", "Mexico", "Y", "Manufacturer", "PH"),
    "SUP13": ("FastenRight Supply", "US", "Y", "Distributor", "FR"),
    "SUP14": ("MedParts Direct", "US", "Y", "Distributor", "MPD"),
    "SUP15": ("Altus Power Systems", "Taiwan", "Y", "Manufacturer", "AP"),
    "SUP16": ("Brightline Power", "China", "N", "Manufacturer", "BL"),
}

PRICES = {
    "SPO2-MOD": ([("SUP01", 18.50, .55), ("SUP03", 11.00, .45)], ("SUP14", 27.00)),
    "ECG-AFE": ([("SUP01", 34.00, .50), ("SUP03", 22.00, .50)], ("SUP14", 49.00)),
    "NIBP-PMP": ([("SUP02", 21.00, .60), ("SUP03", 14.50, .40)], ("SUP14", 31.00)),
    "TRD-US": ([("SUP02", 410.00, .65), ("SUP03", 260.00, .35)], ("SUP14", 590.00)),
    "MCU-V1": ([("SUP04", 62.00, .60), ("SUP05", 41.00, .40)], ("SUP14", 90.00)),
    "MCU-I2": ([("SUP04", 55.00, .60), ("SUP05", 36.00, .40)], ("SUP14", 80.00)),
    "MCU-U3": ([("SUP04", 88.00, .60), ("SUP05", 58.00, .40)], ("SUP14", 125.00)),
    "WIFI-MOD": ([("SUP04", 6.80, .50), ("SUP05", 4.60, .50)], ("SUP14", 10.50)),
    "BLE-MOD": ([("SUP04", 4.90, .50), ("SUP05", 3.40, .50)], ("SUP14", 7.50)),
    "LCD-7": ([("SUP06", 38.00, .55), ("SUP07", 26.00, .45)], ("SUP14", 56.00)),
    "LCD-4": ([("SUP06", 17.50, .55), ("SUP07", 11.50, .45)], ("SUP14", 26.00)),
    "BAT-2S": ([("SUP08", 14.00, .40), ("SUP09", 13.20, .35), ("SUP10", 9.40, .25)], ("SUP14", 21.00)),
    "PSU-24": ([("SUP15", 19.00, .50), ("SUP16", 12.50, .50)], ("SUP14", 29.00)),
    "PMP-PER": ([("SUP11", 42.00, 1.0)], ("SUP14", 64.00)),
    "OCC-SEN": ([("SUP11", 9.50, 1.0)], ("SUP14", 15.00)),
    "ENC-V1": ([("SUP12", 14.00, 1.0)], ("SUP14", 21.00)),
    "ENC-I2": ([("SUP12", 12.50, 1.0)], ("SUP14", 19.00)),
    "ENC-U3": ([("SUP12", 16.50, 1.0)], ("SUP14", 25.00)),
    "GSK-BLK": ([("SUP12", 0.85, 1.0)], ("SUP14", 1.40)),
    "GSK-CLR": ([("SUP12", 0.95, 1.0)], ("SUP14", 1.55)),
    "FAS-M2": ([("SUP13", 0.011, 1.0)], ("SUP13", 0.019)),
    "FAS-M3": ([("SUP13", 0.017, 1.0)], ("SUP13", 0.028)),
}

SPARE_RATE = {
    "SPO2-MOD": .06, "ECG-AFE": .04, "NIBP-PMP": .07, "TRD-US": .05, "MCU-V1": .02, "MCU-I2": .02,
    "MCU-U3": .03, "WIFI-MOD": .02, "BLE-MOD": .02, "LCD-7": .05, "LCD-4": .05, "BAT-2S": .25,
    "PSU-24": .06, "PMP-PER": .08, "OCC-SEN": .06, "ENC-V1": .02, "ENC-I2": .02, "ENC-U3": .03,
    "GSK-BLK": .10, "GSK-CLR": .10, "FAS-M2": .01, "FAS-M3": .01,
}

DESC = {
    "SPO2-MOD": ["Pulse oximetry SpO2 sensor module", "SPO2 SENSOR MOD PULSE OX", "pulse ox SpO2 module", "MODULE,SENSOR,SPO2,OXIMETRY"],
    "ECG-AFE": ["ECG analog front-end module 5-lead", "ECG AFE MOD 5-LEAD", "5-lead ECG front end module", "MODULE,ECG,FRONT-END,5-LEAD"],
    "NIBP-PMP": ["NIBP cuff inflation pump assembly", "NIBP PUMP ASSY", "BP cuff pump assembly NIBP", "ASSEMBLY,PUMP,NIBP,CUFF"],
    "TRD-US": ["Ultrasound transducer array 3.5MHz", "US TRANSDUCER ARRAY 3.5 MHZ", "ultrasound probe array 3.5MHz", "TRANSDUCER,ULTRASOUND,3.5MHZ"],
    "MCU-V1": ["Main control board monitor V1", "MAIN CTRL BRD V1 MONITOR", "monitor V1 main control PCB", "BOARD,CONTROL,MAIN,V1"],
    "MCU-I2": ["Main control board pump I2", "MAIN CTRL BRD I2 PUMP", "pump I2 main control PCB", "BOARD,CONTROL,MAIN,I2"],
    "MCU-U3": ["Main control board ultrasound U3", "MAIN CTRL BRD U3 ULTRASOUND", "ultrasound U3 main control PCB", "BOARD,CONTROL,MAIN,U3"],
    "WIFI-MOD": ["WiFi module 2.4GHz dual-band", "WI-FI MOD 2.4GHZ DUAL BAND", "wifi radio module 2.4GHz", "MODULE,WIFI,2.4GHZ"],
    "BLE-MOD": ["Bluetooth LE module 2.4GHz", "BT LE MOD 2.4GHZ", "bluetooth low energy module 2.4GHz", "MODULE,BLUETOOTH,LE,2.4GHZ"],
    "LCD-7": ["Touch display 7in", "LCD TOUCH DISP 7IN", "7 inch touchscreen display", "DISPLAY,TOUCH,7IN"],
    "LCD-4": ["Touch display 4in", "LCD TOUCH DISP 4IN", "4 inch touchscreen display", "DISPLAY,TOUCH,4IN"],
    "BAT-2S": ["Li-ion battery pack 2S 3.4Ah", "BATT PACK 2S 3400MAH LIION", "2S 3.4Ah Li-ion battery", "BATTERY,LI-ION,2S,3.4AH"],
    "PSU-24": ["Medical power supply 24V 60W", "PSU 24V 60W MEDICAL", "AC-DC medical supply 24V 60W", "SUPPLY,POWER,MEDICAL,24V"],
    "PMP-PER": ["Peristaltic pump mechanism", "PERISTALTIC PUMP MECH", "peristaltic pump head assembly", "MECHANISM,PUMP,PERISTALTIC"],
    "OCC-SEN": ["Occlusion sensor assembly", "OCCLUSION SENSOR ASSY", "occlusion detect sensor assy", "SENSOR,OCCLUSION,ASSEMBLY"],
    "ENC-V1": ["Enclosure housing monitor V1", "ENCLOSURE HSG MONITOR V1", "V1 monitor housing ABS", "HOUSING,ENCLOSURE,V1"],
    "ENC-I2": ["Enclosure housing pump I2", "ENCLOSURE HSG PUMP I2", "I2 pump housing ABS", "HOUSING,ENCLOSURE,I2"],
    "ENC-U3": ["Enclosure housing ultrasound U3", "ENCLOSURE HSG ULTRASOUND U3", "U3 ultrasound housing ABS", "HOUSING,ENCLOSURE,U3"],
    "GSK-BLK": ["Silicone gasket seal black", "GASKET SIL BLK", "silicone seal gasket, black", "GASKET,SILICONE,BLACK"],
    "GSK-CLR": ["Silicone gasket seal clear", "GASKET SIL CLR", "silicone seal gasket, clear", "GASKET,SILICONE,CLEAR"],
    "FAS-M2": ["Screw M2x6 pan head SS", "PHMS M2-0.4X6 A2", "M2 x 6mm pan head screw", "SCREW,PAN,M2X6"],
    "FAS-M3": ["Screw M3x8 pan head SS", "PHMS M3-0.5X8 A2", "M3 x 8mm pan head screw", "SCREW,PAN,M3X8"],
}

MISC_ITEMS = [
    "Shipping carton 18x14x8", "Foam insert kit", "Isopropyl wipes 100ct", "ESD bags 100pk",
    "Packing tape 2in", "Freight surcharge", "Calibration service fee", "Nitrile gloves L box",
    "Thermal labels 4x6", "Cleanroom wipes", "Zip ties 8in 100pk", "Sterile pouch 100pk",
]

FAMILIES = {
    "V1": ("Vitals monitor V1", "Bedside patient vital-signs monitor"),
    "I2": ("Infusion pump I2", "Large-volume infusion pump"),
    "U3": ("Handheld ultrasound U3", "Portable point-of-care ultrasound"),
}
UNITS = {("V1", "C"): 6000, ("V1", "V"): 3500, ("I2", "C"): 4000, ("I2", "V"): 1200,
         ("U3", "C"): 2500, ("U3", "V"): 1800}
SEGMENT = {"C": "Hospitals and clinics", "V": "Veterinary"}
VARIANT = {"C": "Clinical", "V": "Veterinary"}

BOM = {
    "V1": {"SPO2-MOD": 1, "ECG-AFE": 1, "NIBP-PMP": 1, "MCU-V1": 1, "WIFI-MOD": 1, "BLE-MOD": 1, "LCD-7": 1,
           "BAT-2S": 1, "PSU-24": 1, "ENC-V1": 1, "GSK-BLK": 2, "FAS-M2": 24, "FAS-M3": 8},
    "I2": {"MCU-I2": 1, "PMP-PER": 1, "OCC-SEN": 2, "WIFI-MOD": 1, "LCD-4": 1, "BAT-2S": 1, "PSU-24": 1,
           "ENC-I2": 1, "GSK-BLK": 1, "GSK-CLR": 1, "FAS-M2": 30, "FAS-M3": 12},
    "U3": {"TRD-US": 1, "MCU-U3": 1, "BLE-MOD": 1, "WIFI-MOD": 1, "LCD-7": 1, "BAT-2S": 2, "ENC-U3": 1,
           "GSK-CLR": 2, "FAS-M2": 20, "FAS-M3": 10},
}

# ------------------------------------------------------------ generator settings (not data)
PACK_TITLE = "Medical-device BOM + spend cube (synthetic, fictional)"
REG_VARIANT_CODE = "C"
SUPPLIER_EVIDENCE = "ISO 13485 certificate on file (demo data)"
DISTRIBUTOR_SUPS = {"SUP14"}
MISC_SUPS = ["SUP13", "SUP14", "SUP12"]
MISC_PRICE = (4, 150)
PLANTS_PROD = ["BOS-01", "AUS-02"]
PLANT_SPARES = "SVC-01"
START_DATE = (2025, 11, 1)
NEAR_DUP = ("GSK-CLR", "GSK-BLK")
UOM_RULES = [
    (lambda p, s, c: p.startswith("FAS"), 100, "BX100", .65),
]
SPARES_DRIVER = lambda p: "wear and field replacement" if p.startswith(("BAT", "PMP", "OCC", "GSK")) else "field repair"
