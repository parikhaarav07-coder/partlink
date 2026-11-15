"""Regulatory outlook: dated rule records (rules/<industry>.json) joined to a pack's BOM and spend.

A rule record is data, written by hand with a source and a review date. PartLink does not scrape regulators or
decide what is legal; it shows which parts and how many dollars a rule would touch, and what the alternatives cost.
"""
import json
import os
from datetime import date

import pandas as pd

from core.analytics import supplier_prices

RULES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "rules")
STATUS_LABEL = {"in_force": "In force", "scheduled": "Scheduled", "pending": "Pending"}


def load_libraries() -> dict:
    out = {}
    for fn in sorted(os.listdir(RULES_DIR)):
        if fn.endswith(".json"):
            with open(os.path.join(RULES_DIR, fn)) as f:
                out[fn[:-5]] = json.load(f)
    return out


def days_until(rule, today=None):
    if not rule.get("date"):
        return None
    return (date.fromisoformat(rule["date"]) - (today or date.today())).days


def affected_parts(rule, d) -> list:
    sc, parts = rule.get("scope", {}), set(rule.get("scope", {}).get("parts", []))
    if "basis" in sc:
        sr = d["sourcing_rules"]
        parts |= set(sr[sr.requirement_basis.isin(sc["basis"])].part_id)
    if sc.get("all_production"):
        parts |= set(d["parts_master"].part_id)
    return sorted(parts)


def _is_exposed(sp, sup):
    if not sup:
        return pd.Series(True, index=sp.index)
    if "flag" in sup:
        return sp.compliant_for_gov == sup["flag"]
    if "countries" in sup:
        return sp.country.isin(sup["countries"])
    if "not_countries" in sup:
        return ~sp.country.isin(sup["not_countries"])
    return pd.Series(True, index=sp.index)


def exposure(rule, m, d) -> pd.DataFrame:
    """Per affected part: production spend with suppliers the rule would touch, and the best alternative on file."""
    parts = affected_parts(rule, d)
    if not parts or rule.get("impact") == "none":
        return pd.DataFrame()
    sp = supplier_prices(m, d["suppliers"])
    sp = sp[sp.effective_part.isin(parts)].copy()
    sp["exposed"] = _is_exposed(sp, rule["scope"].get("supplier"))
    rows = []
    for part, g in sp.groupby("effective_part"):
        ex, ok = g[g.exposed], g[~g.exposed]
        if ex.empty:
            continue
        qty, spend = ex.qty.sum(), ex.spend.sum()
        avg = spend / qty
        alt = ok.sort_values("avg_price").iloc[0] if len(ok) else None
        rows.append({"part_id": part, "exposed_spend": spend, "exposed_qty": qty,
                     "exposed_suppliers": ", ".join(ex.supplier_name.tolist()), "avg_paid": avg,
                     "alt_supplier": alt.supplier_name if alt is not None else "none on file",
                     "alt_price": alt.avg_price if alt is not None else float("nan"),
                     "switch_cost": qty * (alt.avg_price - avg) if alt is not None else float("nan")})
    return pd.DataFrame(rows).sort_values("exposed_spend", ascending=False) if rows else pd.DataFrame()
