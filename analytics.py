"""PartLink analytics: all dollar math in plain pandas (no AI in the math).

Inputs: the matches table from matcher.run_matching + the data/ CSVs. Only lines that are
auto-accepted or human-approved count toward the numbers; everything else is reported as unresolved.
"""
import os
import re

import pandas as pd

BASES = ["statutory", "blue_framework", "buyer_imposed"]
BASIS_LABEL = {"statutory": "Statutory (named in FY2020 NDAA s848)",
               "blue_framework": "Blue UAS Framework category",
               "buyer_imposed": "Buyer / contract imposed"}


def load_data(data_dir="data"):
    d = {n: pd.read_csv(os.path.join(data_dir, f"{n}.csv")) for n in
         ["products", "bom_lines", "parts_master", "suppliers", "spend_lines", "service_bom", "sourcing_rules"]}
    return d


def effective(matches: pd.DataFrame, approvals: dict | None = None) -> pd.DataFrame:
    """Add effective_part: auto-accepted, or human-approved (approvals: spend_id -> part or 'NONE')."""
    m = matches.copy()
    approvals = approvals or {}
    m["effective_part"] = "UNRESOLVED"
    m.loc[m.status == "auto", "effective_part"] = m.pred_part
    m.loc[m.status == "unmatched", "effective_part"] = "NONE"
    for sid, part in approvals.items():
        m.loc[m.spend_id == sid, "effective_part"] = part
    return m


def coverage(m: pd.DataFrame) -> dict:
    tot = m.extended_spend.sum()
    mapped = m[~m.effective_part.isin(["UNRESOLVED", "NONE"])].extended_spend.sum()
    unresolved = m[m.effective_part == "UNRESOLVED"].extended_spend.sum()
    none = m[m.effective_part == "NONE"].extended_spend.sum()
    return {"total_spend": tot, "mapped_spend": mapped, "unresolved_spend": unresolved, "non_part_spend": none,
            "mapped_pct": mapped / tot, "unresolved_lines": int((m.effective_part == "UNRESOLVED").sum())}


def _mapped(m, channel):
    x = m[(~m.effective_part.isin(["UNRESOLVED", "NONE"])) & (m.channel_guess == channel)]
    return x


def part_prices(m: pd.DataFrame) -> pd.DataFrame:
    """Per part and channel: quantity (each), spend, average paid price each."""
    x = m[~m.effective_part.isin(["UNRESOLVED", "NONE"])]
    g = x.groupby(["effective_part", "channel_guess"]).agg(qty=("qty_each", "sum"), spend=("extended_spend", "sum")).reset_index()
    g["avg_price"] = g.spend / g.qty
    return g


def supplier_prices(m: pd.DataFrame, suppliers: pd.DataFrame) -> pd.DataFrame:
    x = _mapped(m, "production")
    g = x.groupby(["effective_part", "supplier_id"]).agg(qty=("qty_each", "sum"), spend=("extended_spend", "sum")).reset_index()
    g["avg_price"] = g.spend / g.qty
    return g.merge(suppliers[["supplier_id", "supplier_name", "country", "compliant_for_gov"]], on="supplier_id")


def true_cost(m: pd.DataFrame, d: dict) -> pd.DataFrame:
    """Material cost per unit at average paid price, plus spares allocated per unit sold."""
    pp = part_prices(m)
    prod = pp[pp.channel_guess == "production"].set_index("effective_part").avg_price
    spares_spend = pp[pp.channel_guess == "spares"].set_index("effective_part").spend
    prods = d["products"].set_index("product_id")
    bom = d["bom_lines"].merge(d["products"][["product_id", "annual_units", "family"]], on="product_id")
    bom["consumption"] = bom.qty_per_unit * bom.annual_units
    share = bom.consumption / bom.groupby("part_id").consumption.transform("sum")
    bom["spares_alloc"] = bom.part_id.map(spares_spend).fillna(0) * share
    bom["line_cost"] = bom.qty_per_unit * bom.part_id.map(prod)
    out = bom.groupby("product_id").agg(material_cost=("line_cost", "sum"), spares_total=("spares_alloc", "sum")).reset_index()
    out = out.merge(d["products"][["product_id", "product_name", "variant", "annual_units"]], on="product_id")
    out["spares_per_unit"] = out.spares_total / out.annual_units
    out["true_cost_per_unit"] = out.material_cost + out.spares_per_unit
    out["spares_pct_of_cost"] = out.spares_per_unit / out.true_cost_per_unit
    return out


def family_cost(m, d):
    tc = true_cost(m, d)
    tc["family"] = tc.product_id.str.split("-").str[0]
    return tc


def bom_breakdown(m, d, product_id):
    pp = part_prices(m)
    prod = pp[pp.channel_guess == "production"].set_index("effective_part").avg_price
    b = d["bom_lines"][d["bom_lines"].product_id == product_id].copy()
    b["avg_paid_price"] = b.part_id.map(prod)
    b["line_cost"] = b.qty_per_unit * b.avg_paid_price
    return b[["part_id", "part_description", "qty_per_unit", "avg_paid_price", "line_cost", "requires_compliant_supplier", "requirement_basis"]]


def spares_premium(m: pd.DataFrame) -> pd.DataFrame:
    """Spares spend minus spares quantity at the same part's production price. ILLUSTRATIVE, not a benchmark."""
    pp = part_prices(m)
    prod = pp[pp.channel_guess == "production"].set_index("effective_part").avg_price
    sp = pp[pp.channel_guess == "spares"].copy()
    sp["production_price"] = sp.effective_part.map(prod)
    sp["premium_pct"] = sp.avg_price / sp.production_price - 1
    sp["premium_usd"] = sp.spend - sp.qty * sp.production_price
    return sp.sort_values("premium_usd", ascending=False)


def gov_volume(d: dict) -> pd.Series:
    """Annual government-variant volume (each) per part that carries a sourcing requirement, and total volume."""
    bom = d["bom_lines"].merge(d["products"][["product_id", "annual_units"]], on="product_id")
    bom["vol"] = bom.qty_per_unit * bom.annual_units
    gov = bom[bom.requires_compliant_supplier == "Y"].groupby("part_id").vol.sum()
    return gov


def savings_scenario(m: pd.DataFrame, d: dict, enforce=BASES, share_movable=1.0) -> pd.DataFrame:
    """Per part: potential savings from moving production volume to the cheapest ELIGIBLE supplier.

    - Government-variant volume of a part with a sourcing requirement may only go to compliant suppliers
      if that requirement's basis is in `enforce`; otherwise any supplier is eligible. That forced move can
      cost MORE than today's average price, so scenario savings are NET of that compliance cost.
    - Everything else may go to any supplier.
    share_movable: share of volume a buyer can realistically move (0-1). This is a scenario, not a forecast.
    """
    sp = supplier_prices(m, d["suppliers"])
    pp = part_prices(m)
    prod = pp[pp.channel_guess == "production"].set_index("effective_part")
    gov = gov_volume(d)
    basis = d["sourcing_rules"].set_index("part_id").requirement_basis
    rows = []
    for part, g in sp.groupby("effective_part"):
        qty, avg = prod.loc[part, "qty"], prod.loc[part, "avg_price"]
        best_any = g.avg_price.min()
        best_comp = g[g.compliant_for_gov == "Y"].avg_price.min()
        gv = min(gov.get(part, 0), qty)
        b = basis.get(part, "")
        restricted = gv > 0 and b in enforce
        gv_price = best_comp if restricted else best_any
        free_vol = qty - gv
        naive = qty * (avg - best_any)                       # everything to the cheapest supplier
        scenario = gv * (avg - gv_price) + free_vol * (avg - best_any)   # net of forced compliant moves
        rows.append({"part_id": part, "production_qty": qty, "avg_paid": avg, "best_any_supplier": best_any,
                     "best_compliant": best_comp, "gov_volume": gv, "requirement_basis": b,
                     "gov_volume_restricted": restricted,
                     "naive_savings": naive * share_movable, "scenario_savings": scenario * share_movable,
                     "compliance_cost": (naive - scenario) * share_movable})
    return pd.DataFrame(rows).sort_values("scenario_savings", ascending=False)


def near_duplicates(parts: pd.DataFrame, m: pd.DataFrame) -> pd.DataFrame:
    """Master parts whose descriptions differ only by non-numeric tokens -> 'needs engineering review'."""
    from matcher import normalize
    toks = {p: set(normalize(t)) for p, t in zip(parts.part_id, parts.description)}
    pp = part_prices(m)
    prod = pp[pp.channel_guess == "production"].set_index("effective_part")
    out = []
    ids = list(toks)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            diff = toks[a] ^ toks[b]
            if 0 < len(diff) <= 2 and not any(re.search(r"\d", t) for t in diff):
                if a in prod.index and b in prod.index:
                    hi, lo = (a, b) if prod.avg_price[a] > prod.avg_price[b] else (b, a)
                    out.append({"part_a": a, "part_b": b, "differs_on": ", ".join(sorted(diff)),
                                "higher_priced": hi, "price_gap_each": prod.avg_price[hi] - prod.avg_price[lo],
                                "qty_at_higher_price": prod.qty[hi],
                                "potential_if_standardized": prod.qty[hi] * (prod.avg_price[hi] - prod.avg_price[lo]),
                                "status": "Needs engineering review: not assumed interchangeable"})
    return pd.DataFrame(out)


def negotiation_brief(m: pd.DataFrame, d: dict, supplier_id: str, enforce=BASES) -> str:
    """Deterministic, evidence-backed brief for a supplier conversation."""
    sp = supplier_prices(m, d["suppliers"])
    me = sp[sp.supplier_id == supplier_id]
    if me.empty:
        return "No production spend mapped to this supplier."
    name = me.supplier_name.iloc[0]
    sc = savings_scenario(m, d, enforce=enforce).set_index("part_id")
    lines = [f"NEGOTIATION BRIEF: {name} ({supplier_id})", "",
             f"Mapped production spend with {name}: ${me.spend.sum():,.0f} across {len(me)} part(s).", "",
             "Where we pay more than the best alternative we already buy from:"]
    n = 0
    for r in me.sort_values("spend", ascending=False).itertuples():
        alt = sp[(sp.effective_part == r.effective_part) & (sp.supplier_id != supplier_id)]
        if alt.empty:
            continue
        comp_only = d["sourcing_rules"].set_index("part_id").requirement_basis.get(r.effective_part, "") in enforce
        pool = alt[alt.compliant_for_gov == "Y"] if comp_only else alt
        if pool.empty:
            continue
        best = pool.sort_values("avg_price").iloc[0]
        gap = r.avg_price - best.avg_price
        if gap > 0.005:
            n += 1
            lines.append(f"  - {r.effective_part}: we pay ${r.avg_price:,.2f} each; {best.supplier_name} charges "
                         f"${best.avg_price:,.2f} ({gap / r.avg_price:.0%} lower) on similar volume. "
                         f"Volume with {name}: {r.qty:,.0f} units (${r.spend:,.0f}).")
    if n == 0:
        lines.append("  - No lower-priced alternative in our history for this supplier's parts.")
    lines += ["", "Suggested asks:",
              "  1. Match the lower paid price on the parts above, or offer volume tiers.",
              "  2. Quote spares pricing separately from production and justify any spares premium.",
              "", "Before we use any of this:",
              "  - Prices are averages of our own paid history, not quotes.",
              "  - Any alternative supplier must pass engineering qualification and the program's sourcing rules.",
              "  - Savings here are potential, not realized, until later invoices show them."]
    return "\n".join(lines)


def llm_polish(text: str) -> str:
    """OPTIONAL: tighten the brief with Claude if ANTHROPIC_API_KEY is set. Numbers come from the text, not the model."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return text
    try:
        import anthropic
        c = anthropic.Anthropic(api_key=key)
        r = c.messages.create(model="claude-sonnet-5-5", max_tokens=900, messages=[{
            "role": "user", "content": "Rewrite this supplier negotiation brief to be concise and professional. "
            "Keep every number and caveat exactly as given; do not add facts.\n\n" + text}])
        return r.content[0].text
    except Exception as e:  # never break the demo
        return text + f"\n\n[AI polish unavailable: {type(e).__name__}]"
