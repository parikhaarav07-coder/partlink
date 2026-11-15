"""Pack spec: fictional drone maker (defense & public safety). Every figure is an invented assumption."""

# ---------------------------------------------------------------- parts master
PARTS = {
    "MOT-2808": ("Brushless motor 2808 1350KV", "Propulsion"),
    "MOT-4012": ("Brushless motor 4012 400KV", "Propulsion"),
    "ESC-35A": ("Electronic speed controller 35A", "Propulsion"),
    "ESC-60A": ("Electronic speed controller 60A", "Propulsion"),
    "PRP-10": ("Carbon fiber propeller 10in", "Propulsion"),
    "PRP-13": ("Carbon fiber propeller 13in", "Propulsion"),
    "BAT-6S-10": ("Li-ion battery pack 6S 10Ah", "Power"),
    "PDB-1": ("Power distribution board", "Power"),
    "WIR-HARN": ("Main wiring harness", "Power"),
    "FC-7": ("Flight controller FC-7", "Avionics"),
    "GPS-M9": ("GNSS GPS module M9", "Avionics"),
    "RAD-L1": ("Radio link module 900MHz SMA", "Avionics"),
    "RAD-L1B": ("Radio link module 900MHz U.FL", "Avionics"),
    "CAM-EO": ("4K visible camera module", "Payload"),
    "CAM-THM": ("Thermal camera module 640", "Payload"),
    "GMB-3": ("3-axis gimbal frame (no motors)", "Payload"),
    "FRM-S1": ("Carbon frame Scout S1", "Airframe"),
    "FRM-P2": ("Carbon frame Patrol P2", "Airframe"),
    "FRM-H3": ("Carbon frame Hauler H3", "Airframe"),
    "LG-1": ("Landing gear set", "Airframe"),
    "FAS-M3": ("Screw M3x8 socket head", "Hardware"),
    "FAS-M4": ("Screw M4x12 socket head", "Hardware"),
    "ENC-IP65": ("Dock enclosure IP65", "Dock"),
    "PSU-1200": ("Power supply 1200W", "Dock"),
    "CHG-CON": ("Charging contact spring pair", "Dock"),
    "DCK-CTL": ("Dock controller board", "Dock"),
    "WX-SENS": ("Weather sensor module", "Dock"),
}

# parts that government variants must source from compliant suppliers only
GOV_REQ = {
    "MOT-2808", "MOT-4012", "ESC-35A", "ESC-60A", "BAT-6S-10", "PDB-1", "FC-7",
    "GPS-M9", "RAD-L1", "RAD-L1B", "CAM-EO", "CAM-THM", "PSU-1200", "DCK-CTL",
}

# Why each government-required part is restricted. Statutory = named in FY2020 NDAA s848 (as amended);
# blue_framework = listed component category in the Blue UAS Framework (managed by DCMA; a vetting program, not a statute);
# buyer_imposed = customer contract / program requirement (not named in s848).
REQ_BASIS = {
    "FC-7": "statutory", "RAD-L1": "statutory", "RAD-L1B": "statutory",
    "CAM-EO": "statutory", "CAM-THM": "statutory",
    "GPS-M9": "buyer_imposed", "ESC-35A": "blue_framework", "ESC-60A": "blue_framework",
    "MOT-2808": "buyer_imposed", "MOT-4012": "buyer_imposed", "BAT-6S-10": "buyer_imposed",
    "PDB-1": "buyer_imposed", "PSU-1200": "buyer_imposed", "DCK-CTL": "buyer_imposed",
}
assert set(REQ_BASIS) == GOV_REQ
BASIS_NOTE = {
    "statutory": "Named component category in FY2020 NDAA s848. Screening input, not a legal determination.",
    "blue_framework": "Component category in the Blue UAS Framework (DCMA-managed vetting program, not a statute). Check the current listing; FCC exemption for Blue UAS items runs to 1 Jan 2027 unless extended.",
    "buyer_imposed": "Customer contract or program requirement. Not named in s848. Check the governing contract.",
}
CHECKED_ON = "2026-11-01"

# --------------------------------------------------------------------- suppliers
SUPPLIERS = {
    "SUP01": ("Apex Motion Systems", "US", "Y", "Manufacturer", "AM"),
    "SUP02": ("Meridian Drive Co", "Taiwan", "Y", "Manufacturer", "MD"),
    "SUP03": ("Hualong Motor Works", "China", "N", "Manufacturer", "HL"),
    "SUP04": ("Northfield Electronics", "US", "Y", "Manufacturer", "NF"),
    "SUP05": ("Zhenrui Avionics", "China", "N", "Manufacturer", "ZR"),
    "SUP06": ("Cobalt Power Cells", "US", "Y", "Manufacturer", "CP"),
    "SUP07": ("Lumen Cell Tech", "South Korea", "Y", "Manufacturer", "LC"),
    "SUP08": ("Baolin Battery", "China", "N", "Manufacturer", "BB"),
    "SUP09": ("SkyLink Radios", "US", "Y", "Manufacturer", "SL"),
    "SUP10": ("Orion Optics", "Japan", "Y", "Manufacturer", "OO"),
    "SUP11": ("Tianyu Imaging", "China", "N", "Manufacturer", "TY"),
    "SUP12": ("CarbonWorks Aero", "US", "Y", "Manufacturer", "CW"),
    "SUP13": ("BoltPoint Supply", "US", "Y", "Distributor", "BP"),
    "SUP14": ("DroneParts Direct", "US", "Y", "Distributor", "DPD"),
    "SUP15": ("Pacific Enclosures", "Mexico", "Y", "Manufacturer", "PE"),
    "SUP16": ("Everbright Power", "China", "N", "Manufacturer", "EB"),
}

# part -> (production suppliers [(sup, price_each, volume_share)], spares (sup, price_each))
PRICES = {
    "MOT-2808": ([("SUP01", 21.50, .35), ("SUP02", 19.80, .30), ("SUP03", 16.90, .35)], ("SUP14", 29.00)),
    "MOT-4012": ([("SUP01", 84.00, .25), ("SUP02", 79.00, .35), ("SUP03", 64.00, .40)], ("SUP14", 108.00)),
    "ESC-35A": ([("SUP04", 22.00, .60), ("SUP05", 17.50, .40)], ("SUP14", 31.00)),
    "ESC-60A": ([("SUP04", 118.00, .55), ("SUP05", 96.00, .45)], ("SUP14", 158.00)),
    "PRP-10": ([("SUP12", 6.00, 1.0)], ("SUP14", 11.00)),
    "PRP-13": ([("SUP12", 13.00, 1.0)], ("SUP14", 19.50)),
    "BAT-6S-10": ([("SUP06", 95.00, .40), ("SUP07", 89.00, .35), ("SUP08", 71.00, .25)], ("SUP14", 140.00)),
    "PDB-1": ([("SUP04", 9.80, .70), ("SUP05", 7.40, .30)], ("SUP14", 15.00)),
    "WIR-HARN": ([("SUP15", 14.00, 1.0)], ("SUP14", 21.00)),
    "FC-7": ([("SUP04", 149.00, .60), ("SUP05", 118.00, .40)], ("SUP14", 210.00)),
    "GPS-M9": ([("SUP04", 52.00, .50), ("SUP05", 41.00, .50)], ("SUP14", 74.00)),
    "RAD-L1": ([("SUP09", 84.00, 1.0)], ("SUP14", 112.00)),
    "RAD-L1B": ([("SUP09", 89.00, 1.0)], ("SUP14", 118.00)),
    "CAM-EO": ([("SUP10", 74.00, .60), ("SUP11", 55.00, .40)], ("SUP14", 109.00)),
    "CAM-THM": ([("SUP10", 1450.00, .70), ("SUP11", 850.00, .30)], ("SUP14", 2000.00)),
    "GMB-3": ([("SUP10", 96.00, .60), ("SUP11", 70.00, .40)], ("SUP14", 140.00)),
    "FRM-S1": ([("SUP12", 48.00, 1.0)], ("SUP14", 72.00)),
    "FRM-P2": ([("SUP12", 88.00, 1.0)], ("SUP14", 130.00)),
    "FRM-H3": ([("SUP12", 210.00, 1.0)], ("SUP14", 310.00)),
    "LG-1": ([("SUP12", 7.20, 1.0)], ("SUP14", 12.00)),
    "FAS-M3": ([("SUP13", 0.018, 1.0)], ("SUP13", 0.030)),
    "FAS-M4": ([("SUP13", 0.026, 1.0)], ("SUP13", 0.042)),
    "ENC-IP65": ([("SUP15", 64.00, 1.0)], ("SUP14", 92.00)),
    "PSU-1200": ([("SUP15", 128.00, .50), ("SUP16", 104.00, .50)], ("SUP14", 172.00)),
    "CHG-CON": ([("SUP15", 12.50, 1.0)], ("SUP14", 19.00)),
    "DCK-CTL": ([("SUP04", 85.00, 1.0)], ("SUP14", 125.00)),
    "WX-SENS": ([("SUP04", 18.00, 1.0)], ("SUP14", 27.00)),
}

# annual spare demand as a fraction of production consumption
SPARE_RATE = {
    "PRP-10": .75, "PRP-13": .62, "BAT-6S-10": .30, "MOT-2808": .07, "MOT-4012": .075,
    "ESC-35A": .05, "ESC-60A": .05, "FC-7": .02, "GPS-M9": .03, "RAD-L1": .03,
    "RAD-L1B": .04, "CAM-EO": .04, "CAM-THM": .03, "GMB-3": .02, "FRM-S1": .03,
    "FRM-P2": .03, "FRM-H3": .04, "LG-1": .06, "PDB-1": .015, "FAS-M3": .01,
    "FAS-M4": .01, "ENC-IP65": .02, "PSU-1200": .03, "CHG-CON": .08, "DCK-CTL": .02,
    "WX-SENS": .03, "WIR-HARN": .02,
}

# messy description variants ({dir} filled with CW/CCW)
DESC = {
    "MOT-2808": ["Brushless motor 2808 1350KV", "BLDC MTR 2808-1350 3-6S", "2808 outrunner motor 1350kv", "MOTOR,BRUSHLESS,2808,1350KV"],
    "MOT-4012": ["Brushless motor 4012 400KV", "BLDC MTR 4012 400KV HI-TORQUE", "4012 400kv outrunner motor drone", "MOTOR,BRUSHLESS,4012,400KV"],
    "ESC-35A": ["ESC 35A 6S BLHeli32", "Electronic speed controller 35 amp", "SPEED CTRL 35A 4-6S", "ESC,35A,6S,DSHOT"],
    "ESC-60A": ["ESC 60A 12S", "Electronic speed controller 60 amp 12S", "SPEED CTRL 60A HV", "ESC,60A,12S,DSHOT"],
    "PRP-10": ["Carbon fiber propeller 10x4.5 {dir}", "PROP 10X4.5 CF {dir}", "10in CF prop {dir}", "PROPELLER,CF,10IN,{dir}"],
    "PRP-13": ["Carbon fiber propeller 13x5.5 {dir}", "PROP 13X5.5 CF {dir}", "13in CF prop {dir}", "PROPELLER,CF,13IN,{dir}"],
    "BAT-6S-10": ["Li-ion battery pack 6S 10Ah", "BATT PACK 6S 10000MAH LIION", "6S 10Ah smart battery XT90", "BATTERY,LI-ION,6S,10AH"],
    "PDB-1": ["Power distribution board 6-12S", "PDB 12S 200A W/ BEC", "PWR DIST BRD 200A", "BOARD,POWER DIST,12S"],
    "WIR-HARN": ["Main wiring harness", "Wire harness main drone", "HARNESS ASSY MAIN", "CABLE HARNESS,MAIN,XT90"],
    "FC-7": ["Flight controller FC-7", "FC7 autopilot board", "FLT CTRL FC-7 H7", "CONTROLLER,FLIGHT,FC7"],
    "GPS-M9": ["GNSS module M9 w/ compass", "GPS M9N + MAG", "GPS/GNSS RECEIVER M9", "MODULE,GNSS,M9"],
    "RAD-L1": ["Radio link module 900MHz SMA", "RF LINK MOD 900 SMA", "Telemetry radio 900MHz (SMA)", "MODULE,RADIO,900MHZ,SMA"],
    "RAD-L1B": ["Radio link module 900MHz U.FL", "RF LINK MOD 900 UFL", "Telemetry radio 900MHz (u.fl)", "MODULE,RADIO,900MHZ,UFL"],
    "CAM-EO": ["4K camera module 1/2in sensor", "CAM MOD 4K VISIBLE", "4k EO camera module", "CAMERA,4K,VISIBLE"],
    "CAM-THM": ["Thermal camera 640x512", "THERMAL CAM 640", "IR imager 640x512 radiometric", "CAMERA,THERMAL,640"],
    "GMB-3": ["3-axis gimbal frame", "GIMBAL 3AX FRAME ASSY", "gimbal assembly 3 axis no motors", "FRAME,GIMBAL,3AXIS"],
    "FRM-S1": ["Carbon frame Scout S1", "FRAME CF S1", "S1 airframe carbon fiber", "FRAME,AIRFRAME,S1"],
    "FRM-P2": ["Carbon frame Patrol P2", "FRAME CF P2", "P2 airframe carbon fiber", "FRAME,AIRFRAME,P2"],
    "FRM-H3": ["Carbon frame Hauler H3", "FRAME CF H3 HEAVY", "H3 airframe carbon fiber", "FRAME,AIRFRAME,H3"],
    "LG-1": ["Landing gear set", "LANDING SKID SET", "Landing gear kit carbon", "GEAR,LANDING,SET"],
    "FAS-M3": ["Screw M3x8 socket head SS", "SHCS M3-0.5X8 A2", "M3 x 8mm cap screw stainless", "SCREW,SOCKET,M3X8"],
    "FAS-M4": ["Screw M4x12 socket head SS", "SHCS M4-0.7X12 A2", "M4 x 12mm cap screw stainless", "SCREW,SOCKET,M4X12"],
    "ENC-IP65": ["Enclosure IP65 dock housing", "ENCLOSURE IP65 HSG", "Weatherproof dock housing IP65", "HOUSING,DOCK,IP65"],
    "PSU-1200": ["Power supply 1200W 48V", "PSU 1200W 48VDC OUTDOOR", "AC-DC supply 1.2kW 48V", "SUPPLY,POWER,1200W"],
    "CHG-CON": ["Charging contact spring pair", "SPRING CONTACT PAIR CHG", "Pogo charge contacts (pair)", "CONTACT,CHARGE,SPRING"],
    "DCK-CTL": ["Dock controller board", "DOCK CTRL BRD REV C", "dock control PCB", "BOARD,CONTROL,DOCK"],
    "WX-SENS": ["Weather sensor module wind/rain", "WX SENSOR MOD", "wind rain temp sensor module", "SENSOR,WEATHER,MODULE"],
}

MISC_ITEMS = [
    "Shipping carton 24x18x10", "Foam insert kit", "Thread locker 242 blue 50ml",
    "ESD bags 100pk", "Soldering flux paste", "Freight surcharge", "Packing tape 2in",
    "Calibration weights set", "Nitrile gloves L box", "Isopropyl alcohol 1gal",
    "Heat shrink assortment", "Zip ties 8in 100pk",
]

# ---------------------------------------------------------------------- products
FAMILIES = {
    "S1": ("Scout S1", "Small recon quadcopter"),
    "P2": ("Patrol P2", "Mid-size thermal patrol drone"),
    "H3": ("Hauler H3", "Heavy-lift resupply octocopter"),
    "D1": ("Harbor D1", "Drone charging dock"),
}
UNITS = {("S1", "G"): 2800, ("S1", "C"): 5200, ("P2", "G"): 2000, ("P2", "C"): 3000,
         ("H3", "G"): 500, ("H3", "C"): 1000, ("D1", "G"): 400, ("D1", "C"): 800}
SEGMENT = {"G": "Public Safety & Defense", "C": "Infrastructure, Agriculture & Commercial"}
VARIANT = {"G": "Government", "C": "Commercial"}

BOM = {
    "S1": {"MOT-2808": 4, "ESC-35A": 4, "PRP-10": 4, "BAT-6S-10": 1, "PDB-1": 1, "WIR-HARN": 1,
           "FC-7": 1, "GPS-M9": 1, "RAD-L1": 1, "CAM-EO": 1, "FRM-S1": 1, "LG-1": 1,
           "FAS-M3": 40, "FAS-M4": 12},
    "P2": {"MOT-4012": 4, "MOT-2808": 2, "ESC-60A": 4, "PRP-13": 4, "BAT-6S-10": 2, "PDB-1": 1,
           "WIR-HARN": 1, "FC-7": 1, "GPS-M9": 1, "RAD-L1": 1, "CAM-EO": 1, "CAM-THM": 1,
           "GMB-3": 1, "FRM-P2": 1, "LG-1": 1, "FAS-M3": 60, "FAS-M4": 16},
    "H3": {"MOT-4012": 8, "ESC-60A": 8, "PRP-13": 8, "BAT-6S-10": 4, "PDB-1": 1, "WIR-HARN": 1,
           "FC-7": 1, "GPS-M9": 1, "RAD-L1B": 1, "CAM-EO": 1, "FRM-H3": 1, "FAS-M3": 90,
           "FAS-M4": 32},
    "D1": {"BAT-6S-10": 2, "WIR-HARN": 1, "GPS-M9": 1, "RAD-L1": 1, "ENC-IP65": 1, "PSU-1200": 1,
           "CHG-CON": 2, "DCK-CTL": 1, "WX-SENS": 1, "FAS-M3": 30, "FAS-M4": 24},
}

# ------------------------------------------------------------ generator settings (not data)
PACK_TITLE = "Drone BOM + spend cube (synthetic, fictional)"
REG_VARIANT_CODE = "G"            # variant whose volume carries the sourcing requirements
SUPPLIER_EVIDENCE = "self-attested origin (demo)"
DISTRIBUTOR_SUPS = {"SUP14"}      # distributor SKUs look different (no suffix)
MISC_SUPS = ["SUP13", "SUP14", "SUP15"]
MISC_PRICE = (4, 180)
PLANTS_PROD = ["DAY-01", "TUC-02"]
PLANT_SPARES = "MEM-SVC"
START_DATE = (2025, 11, 1)
NEAR_DUP = ("RAD-L1B", "RAD-L1")   # (pricier variant, base) for the expected-findings check
UOM_RULES = [   # (predicate(part, sup, channel), uom_factor, uom, probability)
    (lambda p, s, c: p in ("PRP-10", "PRP-13") and s == "SUP12" and c == "production", 2, "PR", .5),
    (lambda p, s, c: p.startswith("FAS"), 100, "BX100", .65),
]
SPARES_DRIVER = lambda p: "crash and wear replacement" if p.startswith(("PRP", "BAT", "MOT", "LG")) else "field repair"
