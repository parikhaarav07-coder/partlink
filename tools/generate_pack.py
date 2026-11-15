#!/usr/bin/env python3
"""Synthetic BOM + spend cube generator for any PartLink pack. All companies and numbers are fictional.

Usage: python3 tools/generate_pack.py packs/<pack_id>
Reads packs/<pack_id>/spec.py, writes packs/<pack_id>/data/ and packs/<pack_id>/_answer_key/.
"""
import csv
import importlib.util
import json
import os
import random
import sys
from collections import defaultdict
from datetime import date, timedelta

PACK_DIR = sys.argv[1] if len(sys.argv) > 1 else "packs/drones"
spec_path = os.path.join(PACK_DIR, "spec.py")
_s = importlib.util.spec_from_file_location("pack_spec", spec_path)
S = importlib.util.module_from_spec(_s)
_s.loader.exec_module(S)

random.seed(42)
DATA = os.path.join(PACK_DIR, "data")
KEY = os.path.join(PACK_DIR, "_answer_key")
os.makedirs(DATA, exist_ok=True)
os.makedirs(KEY, exist_ok=True)


def write_csv(path, header, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


PARTS, GOV_REQ, REQ_BASIS, BASIS_NOTE = S.PARTS, S.GOV_REQ, S.REQ_BASIS, S.BASIS_NOTE
SUPPLIERS, PRICES, SPARE_RATE, DESC = S.SUPPLIERS, S.PRICES, S.SPARE_RATE, S.DESC
FAMILIES, UNITS, SEGMENT, VARIANT, BOM = S.FAMILIES, S.UNITS, S.SEGMENT, S.VARIANT, S.BOM
CHECKED_ON = S.CHECKED_ON
assert set(REQ_BASIS) == GOV_REQ

product_rows, bom_rows = [], []
prod_need = defaultdict(int)
gov_need = defaultdict(int)
line_no = 0
for fam, (name, note) in FAMILIES.items():
    for v in S.VARIANT:
        pid = f"{fam}-{v}"
        units = UNITS[(fam, v)]
        product_rows.append([pid, fam, name, VARIANT[v], SEGMENT[v], units, note])
        for part, q in BOM[fam].items():
            line_no += 1
            req = "Y" if (v == S.REG_VARIANT_CODE and part in GOV_REQ) else "N"
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
          [[s, v[0], v[1], v[2], v[3], S.SUPPLIER_EVIDENCE, CHECKED_ON] for s, v in SUPPLIERS.items()])
write_csv(os.path.join(DATA, "sourcing_rules.csv"),
          ["part_id", "description", "requirement_basis", "basis_note", "checked_on"],
          [[p, PARTS[p][0], REQ_BASIS[p], BASIS_NOTE[REQ_BASIS[p]], CHECKED_ON] for p in sorted(GOV_REQ)])

spare_demand = {p: int(round(prod_need[p] * SPARE_RATE[p])) for p in PARTS}
write_csv(os.path.join(DATA, "service_bom.csv"),
          ["part_id", "description", "annual_spare_demand_units", "driver"],
          [[p, PARTS[p][0], spare_demand[p], S.SPARES_DRIVER(p)] for p in PARTS])

# ------------------------------------------------------------------- spend cube
START = date(*S.START_DATE)
sku_cache = {}


def sku(sup, part):
    k = (sup, part)
    if k not in sku_cache:
        pre = SUPPLIERS[sup][4]
        if sup in S.DISTRIBUTOR_SUPS:
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
    for pred, f, u, prob in S.UOM_RULES:
        if pred(part, sup, channel) and random.random() < prob:
            factor, uom = f, u
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
            add_line(part, sup, price, q, "production", random.choice(S.PLANTS_PROD))
    n = random.randint(14, 28)
    for q in split_qty(spare_demand[part] * random.uniform(.95, 1.05), n):
        add_line(part, sp_sup, sp_price, q, "spares", S.PLANT_SPARES)

for _ in range(90):
    sup = random.choice(S.MISC_SUPS)
    price = round(random.uniform(*S.MISC_PRICE), 2)
    qty = random.randint(1, 60)
    lines.append({
        "date": START + timedelta(days=random.randint(0, 364)),
        "plant": random.choice(S.PLANTS_PROD + [S.PLANT_SPARES]), "sup": sup,
        "sku": f"{SUPPLIERS[sup][4]}-{random.randint(1000, 9999)}",
        "desc": messy(random.choice(S.MISC_ITEMS)), "qty": qty, "uom": "EA", "unit_price": price,
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
summary = {
    "spend_lines": len(lines),
    "production_spend": round(tot["prod_spend"], 2),
    "spares_spend": round(tot["spares_spend"], 2),
    "naive_savings_move_everything_to_cheapest": round(tot["naive"], 2),
    "compliant_aware_savings": round(tot["aware"], 2),
    "overstatement_of_naive_view": round(tot["naive"] - tot["aware"], 2),
    "compliance_premium_gov_volume": round(tot["comp_prem"], 2),
    "spares_premium_vs_production_price": round(tot["spares_prem"], 2),
    "compliance_premium_by_requirement_basis": {k: round(v, 2) for k, v in by_basis.items() if k != "none"},
    "framing": "Compliance premium is a SCENARIO: cost of restricting regulated-variant volume to eligible suppliers.",
}
if S.NEAR_DUP:
    hi, lo = S.NEAR_DUP
    summary["near_duplicate_standardization_saving"] = round(agg[hi]["pq"] * (avg_price[hi] - avg_price[lo]), 2)
with open(os.path.join(KEY, "expected_findings_summary.json"), "w") as f:
    json.dump(summary, f, indent=2)

with open(os.path.join(DATA, "README.md"), "w") as f:
    f.write(f"""# {S.PACK_TITLE}

All companies, parts and prices are invented. Period: from {START.isoformat()} for 12 months.

- products.csv: product families x variants
- bom_lines.csv: engineering BOM. requires_compliant_supplier=Y means that line must come from a supplier
  with compliant_for_gov=Y (regulated variant only)
- parts_master.csv: engineering part master
- suppliers.csv: suppliers with an eligibility flag and evidence type
- sourcing_rules.csv: why each restricted part is restricted, and on what basis
- spend_lines.csv: the spend cube. Descriptions are messy on purpose. uom: EA = each, PR = pair, BX100 = box of 100.
  Some lines are not parts at all.
- service_bom.csv: annual spare/warranty demand by part (spares are bought at plant {S.PLANT_SPARES})

The _answer_key folder is for grading the matcher and savings math. Do not feed it to the tool.
""")

print(json.dumps(summary, indent=2))
for row in cost_rows:
    print(row)
