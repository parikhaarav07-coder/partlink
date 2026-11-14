#!/usr/bin/env python3
"""Synthetic drone BOM + spend cube generator. All companies and numbers are fictional.

Usage: python3 gen_drone_dataset.py [output_dir]
"""
import csv
import json
import os
import random
import sys
from collections import defaultdict
from datetime import date, timedelta

random.seed(42)
ROOT = sys.argv[1] if len(sys.argv) > 1 else "drone_dataset"
DATA = os.path.join(ROOT, "data")
KEY = os.path.join(ROOT, "_answer_key")
os.makedirs(DATA, exist_ok=True)
os.makedirs(KEY, exist_ok=True)


def write_csv(path, header, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


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
# blue_framework = listed component category in the DIU Blue UAS Framework (a vetting program, not a statute);
# buyer_imposed = customer contract / program requirement (not named in s848).
REQ_BASIS = {
    "FC-7": "statutory", "RAD-L1": "statutory", "RAD-L1B": "statutory",
    "CAM-EO": "statutory", "CAM-THM": "statutory",
    "GPS-M9": "blue_framework", "ESC-35A": "blue_framework", "ESC-60A": "blue_framework",
    "MOT-2808": "buyer_imposed", "MOT-4012": "buyer_imposed", "BAT-6S-10": "buyer_imposed",
    "PDB-1": "buyer_imposed", "PSU-1200": "buyer_imposed", "DCK-CTL": "buyer_imposed",
}
assert set(REQ_BASIS) == GOV_REQ
BASIS_NOTE = {
    "statutory": "Named component category in FY2020 NDAA s848 (as amended Dec 2022). Screening input, not a legal determination.",
    "blue_framework": "Component category in DIU Blue UAS Framework (vetting program, not a statute). Check current listing.",
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
    "MOT-4012": ([("SUP01", 52.00, .25), ("SUP02", 44.00, .35), ("SUP03", 38.00, .40)], ("SUP14", 68.00)),
    "ESC-35A": ([("SUP04", 18.40, .60), ("SUP05", 14.10, .40)], ("SUP14", 26.00)),
    "ESC-60A": ([("SUP04", 31.50, .55), ("SUP05", 24.80, .45)], ("SUP14", 44.00)),
    "PRP-10": ([("SUP12", 6.00, 1.0)], ("SUP14", 11.00)),
    "PRP-13": ([("SUP12", 8.50, 1.0)], ("SUP14", 15.50)),
    "BAT-6S-10": ([("SUP06", 95.00, .40), ("SUP07", 89.00, .35), ("SUP08", 71.00, .25)], ("SUP14", 140.00)),
    "PDB-1": ([("SUP04", 9.80, .70), ("SUP05", 7.40, .30)], ("SUP14", 15.00)),
    "WIR-HARN": ([("SUP15", 14.00, 1.0)], ("SUP14", 21.00)),
    "FC-7": ([("SUP04", 112.00, .60), ("SUP05", 84.00, .40)], ("SUP14", 165.00)),
    "GPS-M9": ([("SUP04", 22.50, .50), ("SUP05", 17.90, .50)], ("SUP14", 34.00)),
    "RAD-L1": ([("SUP09", 61.00, 1.0)], ("SUP14", 88.00)),
    "RAD-L1B": ([("SUP09", 66.00, 1.0)], ("SUP14", 92.00)),
    "CAM-EO": ([("SUP10", 74.00, .60), ("SUP11", 55.00, .40)], ("SUP14", 109.00)),
    "CAM-THM": ([("SUP10", 310.00, .70), ("SUP11", 225.00, .30)], ("SUP14", 430.00)),
    "GMB-3": ([("SUP10", 96.00, .60), ("SUP11", 70.00, .40)], ("SUP14", 140.00)),
    "FRM-S1": ([("SUP12", 48.00, 1.0)], ("SUP14", 72.00)),
    "FRM-P2": ([("SUP12", 88.00, 1.0)], ("SUP14", 130.00)),
    "FRM-H3": ([("SUP12", 210.00, 1.0)], ("SUP14", 310.00)),
    "LG-1": ([("SUP12", 7.20, 1.0)], ("SUP14", 12.00)),
    "FAS-M3": ([("SUP13", 0.018, 1.0)], ("SUP13", 0.030)),
    "FAS-M4": ([("SUP13", 0.026, 1.0)], ("SUP13", 0.042)),
    "ENC-IP65": ([("SUP15", 64.00, 1.0)], ("SUP14", 92.00)),
    "PSU-1200": ([("SUP15", 58.00, .50), ("SUP16", 41.00, .50)], ("SUP14", 84.00)),
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

product_rows, bom_rows = [], []
prod_need = defaultdict(int)
gov_need = defaultdict(int)
line_no = 0
for fam, (name, note) in FAMILIES.items():
    for v in ("G", "C"):
        pid = f"{fam}-{v}"
        units = UNITS[(fam, v)]
        product_rows.append([pid, fam, name, VARIANT[v], SEGMENT[v], units, note])
        for part, q in BOM[fam].items():
            line_no += 1
            req = "Y" if (v == "G" and part in GOV_REQ) else "N"
            bom_rows.append([f"BL-{line_no:04d}", pid, PARTS[part][1], part, PARTS[part][0], q, "EA", req,
                             REQ_BASIS.get(part, "") if req == "Y" else ""])
            prod_need[part] += units * q
            if req == "Y":
                gov_need[part] += units * q

write_csv(os.path.join(DATA, "products.csv"),
          ["product_id", "family", "product_name", "variant", "target_segment", "annual_units", "description"],
          product_rows)
write_csv(os.path.join(DATA, "bom_lines.csv"),
          ["bom_line_id", "product_id", "assembly", "part_id", "part_description", "qty_per_unit", "uom",
           "requires_compliant_supplier", "requirement_basis"], bom_rows)
write_csv(os.path.join(DATA, "parts_master.csv"),
          ["part_id", "description", "category"], [[p, d, c] for p, (d, c) in PARTS.items()])
write_csv(os.path.join(DATA, "suppliers.csv"),
          ["supplier_id", "supplier_name", "country", "compliant_for_gov", "supplier_type",
           "evidence", "checked_on"],
          [[s, v[0], v[1], v[2], v[3], "self-attested origin (demo)", CHECKED_ON] for s, v in SUPPLIERS.items()])
write_csv(os.path.join(DATA, "sourcing_rules.csv"),
          ["part_id", "description", "requirement_basis", "basis_note", "checked_on"],
          [[p, PARTS[p][0], REQ_BASIS[p], BASIS_NOTE[REQ_BASIS[p]], CHECKED_ON] for p in sorted(GOV_REQ)])

spare_demand = {p: int(round(prod_need[p] * SPARE_RATE[p])) for p in PARTS}
write_csv(os.path.join(DATA, "service_bom.csv"),
          ["part_id", "description", "annual_spare_demand_units", "driver"],
          [[p, PARTS[p][0], spare_demand[p],
            "crash and wear replacement" if p.startswith(("PRP", "BAT", "MOT", "LG")) else "field repair"]
           for p in PARTS])

# ------------------------------------------------------------------- spend cube
START = date(2025, 11, 1)
sku_cache = {}


def sku(sup, part):
    k = (sup, part)
    if k not in sku_cache:
        pre = SUPPLIERS[sup][4]
        if sup == "SUP14":
            sku_cache[k] = f"{pre}-{random.randint(10000, 99999)}"
        else:
            sku_cache[k] = f"{pre}-{random.randint(1000, 9999)}-{random.choice(['A', 'B', 'C', 'R2'])}"
    return sku_cache[k]


def messy(text):
    r = random.random()
    if r < .25:
        text = text.upper()
    elif r < .35:
        text = text.lower()
    if random.random() < .12:
        text += random.choice([" RoHS", " - BULK", " (LOT)", " REV B"])
    if random.random() < .08 and len(text) > 8:
        i = random.randrange(1, len(text) - 2)
        text = text[:i] + text[i + 1] + text[i] + text[i + 2:]
    return text


def split_qty(total, n):
    w = [random.random() + .4 for _ in range(n)]
    s = sum(w)
    return [max(1, int(round(total * x / s))) for x in w]


lines = []


def add_line(part, sup, price_each, qty_each, channel, plant):
    factor, uom = 1, "EA"
    if part in ("PRP-10", "PRP-13") and sup == "SUP12" and channel == "production" and random.random() < .5:
        factor, uom = 2, "PR"
    if part.startswith("FAS") and random.random() < .65:
        factor, uom = 100, "BX100"
    qty_each = max(factor, (qty_each // factor) * factor)
    qty_uom = qty_each // factor
    unit_price = round(price_each * (1 + random.uniform(-.015, .015)) * factor, 4)
    desc = random.choice(DESC[part]).format(dir=random.choice(["CW", "CCW"]))
    lines.append({
        "date": START + timedelta(days=random.randint(0, 364)),
        "plant": plant, "sup": sup, "sku": sku(sup, part), "desc": messy(desc),
        "qty": qty_uom, "uom": uom, "unit_price": unit_price,
        "ext": round(qty_uom * unit_price, 2),
        "part": part, "channel": channel, "factor": factor, "qty_each": qty_each,
        "price_each": unit_price / factor,
    })


for part, (prod_sups, (sp_sup, sp_price)) in PRICES.items():
    total = prod_need[part] * random.uniform(.96, 1.04)
    for sup, price, share in prod_sups:
        n = random.randint(14, 26)
        for q in split_qty(total * share, n):
            add_line(part, sup, price, q, "production", random.choice(["DAY-01", "TUC-02"]))
    n = random.randint(14, 28)
    for q in split_qty(spare_demand[part] * random.uniform(.95, 1.05), n):
        add_line(part, sp_sup, sp_price, q, "spares", "MEM-SVC")

for _ in range(90):
    sup = random.choice(["SUP13", "SUP14", "SUP15"])
    price = round(random.uniform(4, 180), 2)
    qty = random.randint(1, 60)
    lines.append({
        "date": START + timedelta(days=random.randint(0, 364)),
        "plant": random.choice(["DAY-01", "TUC-02", "MEM-SVC"]), "sup": sup,
        "sku": f"{SUPPLIERS[sup][4]}-{random.randint(1000, 9999)}",
        "desc": messy(random.choice(MISC_ITEMS)), "qty": qty, "uom": "EA", "unit_price": price,
        "ext": round(qty * price, 2), "part": "NONE", "channel": "other", "factor": 1,
        "qty_each": qty, "price_each": price,
    })

lines.sort(key=lambda r: r["date"])
spend_rows, key_rows = [], []
for i, r in enumerate(lines, 1):
    r["id"] = f"SP-{i:05d}"
    spend_rows.append([r["id"], f"PO-{random.randint(100000, 999999)}", r["date"].isoformat(), r["plant"],
                       r["sup"], SUPPLIERS[r["sup"]][0], r["sku"], r["desc"], r["qty"], r["uom"],
                       r["unit_price"], r["ext"], "USD"])
    key_rows.append([r["id"], r["part"], r["channel"], r["factor"], r["qty_each"], round(r["price_each"], 5)])

write_csv(os.path.join(DATA, "spend_lines.csv"),
          ["spend_id", "po_number", "date", "plant", "supplier_id", "supplier_name", "supplier_sku",
           "line_description", "qty", "uom", "unit_price", "extended_spend", "currency"], spend_rows)
write_csv(os.path.join(KEY, "answer_key.csv"),
          ["spend_id", "true_part_id", "channel", "uom_factor", "qty_each", "unit_price_each"], key_rows)

# -------------------------------------------------------------- expected findings
agg = defaultdict(lambda: {"pq": 0, "ps": 0.0, "sq": 0, "ss": 0.0})
for r in lines:
    if r["part"] == "NONE":
        continue
    a = agg[r["part"]]
    if r["channel"] == "production":
        a["pq"] += r["qty_each"]
        a["ps"] += r["ext"]
    else:
        a["sq"] += r["qty_each"]
        a["ss"] += r["ext"]

find_rows = []
tot = defaultdict(float)
avg_price = {}
for part, (prod_sups, _) in PRICES.items():
    a = agg[part]
    avg = a["ps"] / a["pq"]
    avg_price[part] = avg
    best_all = min(p for _, p, _ in prod_sups)
    best_comp = min(p for s, p, _ in prod_sups if SUPPLIERS[s][2] == "Y")
    gov = min(gov_need[part], a["pq"])
    naive = a["ps"] - a["pq"] * best_all
    aware = a["ps"] - (gov * best_comp + (a["pq"] - gov) * best_all)
    comp_prem = gov * (best_comp - best_all)
    sp_prem = a["ss"] - a["sq"] * avg
    find_rows.append([part, a["pq"], round(a["ps"], 2), round(avg, 4), best_all, best_comp, gov,
                      round(naive, 2), round(aware, 2), round(comp_prem, 2), a["sq"], round(a["ss"], 2),
                      round(sp_prem, 2)])
    tot["prod_spend"] += a["ps"]
    tot["spares_spend"] += a["ss"]
    tot["naive"] += naive
    tot["aware"] += aware
    tot["comp_prem"] += comp_prem
    tot["spares_prem"] += sp_prem

write_csv(os.path.join(KEY, "expected_findings_by_part.csv"),
          ["part_id", "prod_qty", "prod_spend", "avg_price", "best_price_any", "best_price_compliant",
           "gov_required_qty", "naive_savings_if_cheapest", "compliant_aware_savings",
           "compliance_premium", "spares_qty", "spares_spend", "spares_premium_vs_production"], find_rows)

cost_rows = []
for fam in FAMILIES:
    cost = sum(q * avg_price[p] for p, q in BOM[fam].items())
    cost_rows.append([fam, round(cost, 2)])
write_csv(os.path.join(KEY, "expected_material_cost_per_unit.csv"),
          ["family", "material_cost_per_unit_at_avg_price"], cost_rows)

by_basis = defaultdict(float)
for row in find_rows:
    by_basis[REQ_BASIS.get(row[0], "none")] += row[9]
dup_saving = agg["RAD-L1B"]["pq"] * (avg_price["RAD-L1B"] - avg_price["RAD-L1"])
summary = {
    "spend_lines": len(lines),
    "production_spend": round(tot["prod_spend"], 2),
    "spares_spend": round(tot["spares_spend"], 2),
    "naive_savings_move_everything_to_cheapest": round(tot["naive"], 2),
    "compliant_aware_savings": round(tot["aware"], 2),
    "overstatement_of_naive_view": round(tot["naive"] - tot["aware"], 2),
    "compliance_premium_gov_volume": round(tot["comp_prem"], 2),
    "spares_premium_vs_production_price": round(tot["spares_prem"], 2),
    "near_duplicate_radio_standardization_saving": round(dup_saving, 2),
    "compliance_premium_by_requirement_basis": {k: round(v, 2) for k, v in by_basis.items() if k != "none"},
    "framing": "Compliance premium is a SCENARIO: cost of restricting government-variant volume to compliant suppliers. "
               "Only the 'statutory' share reflects a named statutory component category.",
}
with open(os.path.join(KEY, "expected_findings_summary.json"), "w") as f:
    json.dump(summary, f, indent=2)

with open(os.path.join(DATA, "README.md"), "w") as f:
    f.write("""# Drone BOM + spend cube (synthetic, fictional)

All companies, parts and prices are invented. Period: Nov 2025 - Oct 2026.

- products.csv: 4 product families x 2 variants (Government / Commercial)
- bom_lines.csv: engineering BOM, one level of assemblies. requires_compliant_supplier=Y means that line
  must come from a supplier with compliant_for_gov=Y (government variants only)
- parts_master.csv: engineering part master
- suppliers.csv: suppliers with compliance flag, evidence type and checked_on date (stand-in for sourcing evidence)
- sourcing_rules.csv: why each government-required part is restricted: statutory / blue_framework / buyer_imposed
- spend_lines.csv: the spend cube. Descriptions are messy on purpose. Watch the uom column:
  EA = each, PR = pair (price per pair), BX100 = box of 100 (price per box). Some lines are not parts at all.
- service_bom.csv: annual spare/warranty demand by part (spares are bought at the MEM-SVC plant)

The _answer_key folder is for grading your matcher and savings math. Do not feed it to the tool.
""")

print(json.dumps(summary, indent=2))
for row in cost_rows:
    print(row)
