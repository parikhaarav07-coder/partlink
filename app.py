"""PartLink: BOM-to-spend cost intelligence (demo on synthetic drone-maker data).

Run:  streamlit run app.py
"""
import json
import os

import altair as alt
import pandas as pd
import streamlit as st

import analytics as A
import matcher

st.set_page_config(page_title="PartLink", page_icon="🔗", layout="wide")

INK, MUTED, ACCENT, WARN, GOOD = "#1f2937", "#6b7280", "#2563eb", "#d97706", "#059669"
st.markdown(f"""
<style>
.block-container {{padding-top: 1.6rem; max-width: 1250px;}}
h1, h2, h3 {{color: {INK}; letter-spacing: -0.01em;}}
.pl-banner {{background:#f1f5f9; border-left:4px solid {ACCENT}; padding:.7rem 1rem; border-radius:6px; font-size:.92rem; color:{INK};}}
.pl-warn {{background:#fffbeb; border-left:4px solid {WARN}; padding:.7rem 1rem; border-radius:6px; font-size:.92rem; color:{INK};}}
.pl-big {{font-size:2.0rem; font-weight:700; color:{INK}; line-height:1.1;}}
.pl-lab {{font-size:.82rem; color:{MUTED}; text-transform:uppercase; letter-spacing:.04em;}}
.pl-sub {{font-size:.85rem; color:{MUTED};}}
</style>""", unsafe_allow_html=True)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
KEY_PATH = os.path.join(os.path.dirname(__file__), "_answer_key", "answer_key.csv")


@st.cache_data(show_spinner="Matching purchase lines to parts…")
def get_matches():
    return matcher.run_matching(DATA_DIR)


@st.cache_data
def get_data():
    return A.load_data(DATA_DIR)


def usd(x, d=0):
    return f"${x:,.{d}f}"


def kpi(col, label, value, sub=""):
    col.markdown(f'<div class="pl-lab">{label}</div><div class="pl-big">{value}</div><div class="pl-sub">{sub}</div>',
                 unsafe_allow_html=True)


raw = get_matches()
d = get_data()
if "approvals" not in st.session_state:
    st.session_state.approvals = {}
if "ledger_status" not in st.session_state:
    st.session_state.ledger_status = {}

m = A.effective(raw, st.session_state.approvals)
cov = A.coverage(m)

# ------------------------------------------------------------------------ header
st.title("PartLink")
st.caption("Connect every purchase to the approved part it belongs to, and see what each product costs, spares included (estimate).")
st.markdown('<div class="pl-banner"><b>Demo on synthetic data.</b> A fictional drone maker (4 products, 27 parts, 16 suppliers, '
            f'{len(raw):,} purchase lines). Savings shown are <b>potential</b>, not realized, and nothing here is a legal '
            'compliance determination.</div>', unsafe_allow_html=True)
st.write("")

tabs = st.tabs(["Overview", "Cost per unit (est.)", "Review queue", "Savings simulator", "Savings ledger",
                "Negotiation brief", "Match quality", "Pilot & limits"])

# ------------------------------------------------------------------------ overview
with tabs[0]:
    sc_all = A.savings_scenario(m, d)
    sp = A.spares_premium(m)
    tc = A.true_cost(m, d)
    c = st.columns(4)
    kpi(c[0], "Spend mapped to a part", f"{cov['mapped_pct']:.1%}", f"{usd(cov['unresolved_spend'])} awaiting review")
    kpi(c[1], "Lines needing a human", f"{cov['unresolved_lines']}", "of {:,} purchase lines".format(len(raw)))
    kpi(c[2], "Potential savings (net)", usd(sc_all.scenario_savings.sum()), "after compliance limits, if all volume moves")
    kpi(c[3], "Spares paid above production price", usd(sp.premium_usd.sum()), "illustrative, same part, same year")
    st.write("")
    st.subheader("What PartLink found")
    nd = A.near_duplicates(d["parts_master"], m)
    naive, net = sc_all.naive_savings.sum(), sc_all.scenario_savings.sum()
    top = sc_all.iloc[0]
    st.markdown(f"""
- **A naive "buy everything from the cheapest supplier" view promises {usd(naive)}. Respecting sourcing limits cuts it to {usd(net)}.**
  The {usd(naive - net)} gap is the cost of keeping restricted parts with compliant suppliers. Largest single opportunity: **{top.part_id}** ({usd(top.scenario_savings)} net).
- **Spares are bought at a premium.** Fleet spares cost {usd(sp.premium_usd.sum())} more than the same parts at production prices; batteries and thermal cameras lead.
  Spares add **{tc.spares_pct_of_cost.min():.0%}–{tc.spares_pct_of_cost.max():.0%}** to each product's estimated cost per unit, a cost the production BOM never shows (allocated by part usage, an assumption).
- **Near-duplicate parts are flagged, not assumed swappable.** {len(nd)} pair(s) found (e.g. {nd.part_a.iloc[0]} vs {nd.part_b.iloc[0]}, differing only on {nd.differs_on.iloc[0]}). Standardizing is worth {usd(nd.potential_if_standardized.sum())} only if engineering approves.
""" if len(nd) else f"- Naive view: {usd(naive)}; net of sourcing limits: {usd(net)}.")
    st.markdown('<div class="pl-warn"><b>How to read these numbers.</b> They are computed from average paid prices in this '
                'synthetic data. Real savings need engineering approval, supplier qualification, a negotiated change, and '
                'later invoices that show it (see Savings ledger).</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------ true cost
with tabs[1]:
    st.subheader("Procurement-attributable cost per unit (estimate)")
    st.caption("Material cost = BOM quantity × average price actually paid. Spares = spares spend allocated by part usage, per unit sold.")
    fam = A.family_cost(m, d).drop_duplicates("family")
    fam["Product"] = fam.product_name
    long = fam.melt(id_vars="Product", value_vars=["material_cost", "spares_per_unit"], var_name="part", value_name="usd")
    long["part"] = long.part.map({"material_cost": "Production material", "spares_per_unit": "Spares (allocated)"})
    chart = alt.Chart(long).mark_bar().encode(
        x=alt.X("Product:N", sort=None, axis=alt.Axis(labelAngle=0, title=None)),
        y=alt.Y("usd:Q", title="USD per unit"),
        color=alt.Color("part:N", scale=alt.Scale(range=[ACCENT, WARN]), legend=alt.Legend(title=None, orient="top")),
        tooltip=["Product", "part", alt.Tooltip("usd:Q", format="$,.0f")]).properties(height=320)
    st.altair_chart(chart, width='stretch')
    show = fam[["Product", "material_cost", "spares_per_unit", "true_cost_per_unit", "spares_pct_of_cost"]].rename(columns={
        "material_cost": "Material $/unit", "spares_per_unit": "Spares $/unit", "true_cost_per_unit": "Est. cost $/unit",
        "spares_pct_of_cost": "Spares share"})
    st.dataframe(show.style.format({"Material $/unit": "${:,.0f}", "Spares $/unit": "${:,.0f}",
                                    "Est. cost $/unit": "${:,.0f}", "Spares share": "{:.0%}"}), hide_index=True, width='stretch')
    st.markdown("##### Drill into one product's BOM")
    pid = st.selectbox("Product variant", d["products"].product_id.tolist(),
                       format_func=lambda p: f"{p}  ·  " + d["products"].set_index("product_id").loc[p, "product_name"] +
                       " (" + d["products"].set_index("product_id").loc[p, "variant"] + ")")
    bb = A.bom_breakdown(m, d, pid).sort_values("line_cost", ascending=False)
    bb["sourcing_requirement"] = bb.requirement_basis.fillna("").replace("", "none")
    st.dataframe(bb.drop(columns=["requirement_basis"]).rename(columns={
        "part_id": "Part", "part_description": "Description", "qty_per_unit": "Qty", "avg_paid_price": "Avg paid $",
        "line_cost": "Line cost $", "requires_compliant_supplier": "Restricted?", "sourcing_requirement": "Basis"}).style.format(
        {"Avg paid $": "${:,.2f}", "Line cost $": "${:,.2f}"}), hide_index=True, width='stretch')

# ------------------------------------------------------------------------ review queue
with tabs[2]:
    st.subheader("Review queue")
    st.caption("PartLink never auto-accepts a doubtful match, and the best guess is often wrong (cartons look like propellers). A human decides: pick a part, or 'NONE' if it is not a tracked part. Decisions update every number in the app. The demo button simulates an expert reviewer using the hidden answer key.")
    rq = raw[raw.status == "review"].sort_values("extended_spend", ascending=False).copy()
    options = ["Pending"] + sorted(d["parts_master"].part_id.tolist()) + ["NONE (not a tracked part)"]
    rq["Decision"] = rq.spend_id.map(lambda s: st.session_state.approvals.get(s, "Pending"))
    rq["Decision"] = rq.Decision.replace({"NONE": "NONE (not a tracked part)"})
    view = rq[["spend_id", "line_description", "supplier_name", "extended_spend", "pred_part", "confidence", "reason", "Decision"]].rename(
        columns={"spend_id": "Line", "line_description": "Description", "supplier_name": "Supplier", "extended_spend": "Spend $",
                 "pred_part": "Best guess", "confidence": "Confidence", "reason": "Why it needs review"})
    c1, c2, c3 = st.columns([1, 1, 3])
    if c1.button("Demo: simulate expert reviewer") and os.path.exists(KEY_PATH):
        _k = pd.read_csv(KEY_PATH).set_index("spend_id").true_part_id
        for r in rq.itertuples():
            st.session_state.approvals[r.spend_id] = _k[r.spend_id]
        st.rerun()
    if c2.button("Clear decisions"):
        st.session_state.approvals = {}
        st.rerun()
    edited = st.data_editor(view, hide_index=True, width='stretch', key="rq_editor",
                            disabled=[c for c in view.columns if c != "Decision"],
                            column_config={"Decision": st.column_config.SelectboxColumn(options=options, required=True),
                                           "Spend $": st.column_config.NumberColumn(format="$%.0f"),
                                           "Confidence": st.column_config.ProgressColumn(min_value=0, max_value=1, format="%.2f")})
    new = {r.Line: ("NONE" if r.Decision.startswith("NONE") else r.Decision) for r in edited.itertuples() if r.Decision != "Pending"}
    if new != st.session_state.approvals:
        st.session_state.approvals = new
        st.rerun()
    st.info(f"{len(st.session_state.approvals)} of {len(rq)} decided · mapped spend now {cov['mapped_pct']:.1%}")

    st.markdown("---")
    st.markdown("##### Lineage: trace any purchase line back to its part, BOM and sourcing evidence")
    _eff = m.set_index("spend_id")
    _opts = raw.sort_values("extended_spend", ascending=False).spend_id.head(300).tolist()
    sid_pick = st.selectbox("Purchase line (largest 300 by spend)", _opts, format_func=lambda s_: f"{s_}  ·  " + raw.set_index("spend_id").loc[s_, "line_description"] + "  ·  " + usd(raw.set_index("spend_id").loc[s_, "extended_spend"]))
    ln = raw.set_index("spend_id").loc[sid_pick]
    eff_part = _eff.loc[sid_pick, "effective_part"]
    c1_, c2_, c3_ = st.columns(3)
    c1_.markdown(f"**1. What was bought**  \n{ln.line_description}  \nSupplier: {ln.supplier_name} ({ln.supplier_id})  \nSKU: {ln.supplier_sku}  \nPO {ln.po_number} on {ln.date}  \nPlant: {ln.plant} ({ln.channel_guess})")
    c2_.markdown(f"**2. Normalized**  \nQty {ln.qty:g} {ln.uom} to {ln.qty_each:g} each (x{ln.uom_factor:g})  \nPrice {ln.unit_price:,.2f} per {ln.uom} to {ln.price_each:,.2f} each  \nvs part median price: {ln.price_vs_median:.2f}x")
    c3_.markdown(f"**3. Matched to**  \nBest guess: {ln.pred_part} (confidence {ln.confidence:.2f}, {ln.method})  \nStatus: {ln.status}  \nReason: {ln.reason}  \nEffective part now: **{eff_part}**")
    if eff_part not in ("NONE", "UNRESOLVED"):
        bl = d["bom_lines"][d["bom_lines"].part_id == eff_part].merge(d["products"][["product_id", "product_name", "variant"]], on="product_id")
        st.markdown(f"**4. Where {eff_part} is used in the approved BOM**")
        st.dataframe(bl[["product_id", "product_name", "variant", "assembly", "qty_per_unit", "requirement_basis"]].rename(columns={"requirement_basis": "sourcing basis"}), hide_index=True, width='stretch')
        sr = d["sourcing_rules"][d["sourcing_rules"].part_id == eff_part]
        sup = d["suppliers"].set_index("supplier_id").loc[ln.supplier_id]
        if len(sr):
            st.markdown(f"**5. Sourcing evidence:** {sr.iloc[0].requirement_basis}. {sr.iloc[0].basis_note} (checked {sr.iloc[0].checked_on}). This supplier: {sup.supplier_name}, {sup.country}, compliant-for-gov flag {sup.compliant_for_gov}, evidence: {sup.evidence}.")
        else:
            st.markdown(f"**5. Sourcing evidence:** no government sourcing requirement recorded for {eff_part}. Supplier: {sup.supplier_name}, {sup.country}.")
    else:
        st.info("This line is not currently linked to a tracked part, so it adds nothing to any product cost.")

# ------------------------------------------------------------------------ simulator
with tabs[3]:
    st.subheader("What-if savings simulator")
    st.caption("Choose which sourcing requirements bind, and how much volume you can realistically move.")
    left, right = st.columns([1, 2])
    with left:
        enforce = st.multiselect("Requirements treated as binding for government-variant volume", A.BASES,
                                 default=A.BASES, format_func=lambda b: A.BASIS_LABEL[b])
        share = st.slider("Share of volume you can move", 0, 100, 100, 5, format="%d%%") / 100
        st.markdown('<div class="pl-sub">Statutory means a named component category in the FY2020 NDAA §848. Blue UAS Framework (managed by DCMA) is a vetting '
                    'program, not a statute; the FCC exemption for Blue UAS items runs to 1 Jan 2027 unless extended. Rules also reach any federally funded buyer (American Security Drone Act), not only DoD. Buyer-imposed comes from the customer contract. All are screening inputs, '
                    'not legal conclusions. Rules last checked 2026-11-01 (demo).</div>', unsafe_allow_html=True)
    sc = A.savings_scenario(m, d, enforce=enforce, share_movable=share)
    with right:
        k = st.columns(3)
        kpi(k[0], "Naive view", usd(sc.naive_savings.sum()), "all volume to cheapest supplier")
        kpi(k[1], "Compliance cost", usd(sc.compliance_cost.sum()), "forced moves for restricted parts")
        kpi(k[2], "Net potential savings", usd(sc.scenario_savings.sum()), f"at {share:.0%} of volume movable")
    bar = sc.head(10).melt(id_vars="part_id", value_vars=["naive_savings", "scenario_savings"], var_name="view", value_name="usd")
    bar["view"] = bar.view.map({"naive_savings": "Naive", "scenario_savings": "Net of sourcing limits"})
    st.altair_chart(alt.Chart(bar).mark_bar().encode(
        y=alt.Y("part_id:N", sort="-x", title=None),
        x=alt.X("usd:Q", title="Potential annual savings (USD)"),
        yOffset="view:N", color=alt.Color("view:N", scale=alt.Scale(range=["#cbd5e1", ACCENT]), legend=alt.Legend(title=None, orient="top")),
        tooltip=["part_id", "view", alt.Tooltip("usd:Q", format="$,.0f")]).properties(height=360), width='stretch')
    st.dataframe(sc[["part_id", "requirement_basis", "avg_paid", "best_any_supplier", "best_compliant", "naive_savings",
                     "compliance_cost", "scenario_savings"]].rename(columns={
        "part_id": "Part", "requirement_basis": "Basis", "avg_paid": "Avg paid", "best_any_supplier": "Best price (any)",
        "best_compliant": "Best compliant", "naive_savings": "Naive $", "compliance_cost": "Compliance cost $",
        "scenario_savings": "Net $"}).style.format({"Avg paid": "${:,.2f}", "Best price (any)": "${:,.2f}", "Best compliant": "${:,.2f}",
                                                    "Naive $": "${:,.0f}", "Compliance cost $": "${:,.0f}", "Net $": "${:,.0f}"}),
        hide_index=True, width='stretch')
    st.markdown("##### Near-duplicate parts: needs engineering review")
    nd = A.near_duplicates(d["parts_master"], m)
    st.dataframe(nd.style.format({"price_gap_each": "${:,.2f}", "qty_at_higher_price": "{:,.0f}", "potential_if_standardized": "${:,.0f}"}),
                 hide_index=True, width='stretch')
    st.markdown("##### Spares priced above production (illustrative)")
    spx = A.spares_premium(m).head(8)
    st.dataframe(spx[["effective_part", "qty", "avg_price", "production_price", "premium_pct", "premium_usd"]].rename(columns={
        "effective_part": "Part", "qty": "Spares qty", "avg_price": "Spares price", "production_price": "Production price",
        "premium_pct": "Premium", "premium_usd": "Premium $"}).style.format({
        "Spares qty": "{:,.0f}", "Spares price": "${:,.2f}", "Production price": "${:,.2f}", "Premium": "{:.0%}", "Premium $": "${:,.0f}"}),
        hide_index=True, width='stretch')
    st.caption("Spares often cost more for good reasons (small lots, fast delivery). No typical drone-spares markup is published, so treat this as a prompt to ask, not a verdict.")

# ------------------------------------------------------------------------ ledger
with tabs[4]:
    st.subheader("Savings ledger: from identified to realized")
    st.caption("A price spread is not cash saved. Each opportunity must pass engineering, procurement and finance. "
               "'Realized' should only be set when later invoices show the lower price.")
    sc0 = A.savings_scenario(m, d)
    nd = A.near_duplicates(d["parts_master"], m)
    sp0 = A.spares_premium(m)
    items = [{"Opportunity": f"Move {r.part_id} volume to lower-priced eligible supplier", "Type": "Price spread",
              "Identified $": r.scenario_savings, "Needs": "Supplier qualification + sourcing-rule check + negotiation"}
             for r in sc0.head(6).itertuples()]
    items += [{"Opportunity": f"Standardize {r.part_b} onto {r.part_a}", "Type": "Near-duplicate",
               "Identified $": r.potential_if_standardized, "Needs": "Engineering confirms interchangeability"} for r in nd.itertuples()]
    items += [{"Opportunity": f"Renegotiate spares price for {r.effective_part}", "Type": "Spares", "Identified $": r.premium_usd * 0.3,
               "Needs": "Compare like-for-like terms (assumes 30% of premium is addressable: illustrative)"} for r in sp0.head(3).itertuples()]
    led = pd.DataFrame(items)
    led["Status"] = [st.session_state.ledger_status.get(o, "Identified") for o in led.Opportunity]
    stages = ["Identified", "Engineering approved", "Negotiated", "Realized (invoices confirm)"]
    ed = st.data_editor(led, hide_index=True, width='stretch', key="ledger",
                        disabled=["Opportunity", "Type", "Identified $", "Needs"],
                        column_config={"Status": st.column_config.SelectboxColumn(options=stages, required=True),
                                       "Identified $": st.column_config.NumberColumn(format="$%.0f")})
    st.session_state.ledger_status = dict(zip(ed.Opportunity, ed.Status))
    tot = ed.groupby("Status")["Identified $"].sum().reindex(stages).fillna(0)
    cc = st.columns(4)
    for col, s in zip(cc, stages):
        kpi(col, s, usd(tot[s]), f"{int((ed.Status == s).sum())} item(s)")

# ------------------------------------------------------------------------ negotiation brief
with tabs[5]:
    st.subheader("Negotiation brief")
    sup = d["suppliers"]
    sid = st.selectbox("Supplier", sup.supplier_id.tolist(),
                       format_func=lambda s: f"{s} · " + sup.set_index("supplier_id").loc[s, "supplier_name"])
    brief = A.negotiation_brief(m, d, sid)
    if os.environ.get("ANTHROPIC_API_KEY") and st.checkbox("Polish wording with Claude (numbers stay as computed)"):
        brief = A.llm_polish(brief)
    st.text_area("Brief (copy into an email or deck)", brief, height=380)

# ------------------------------------------------------------------------ match quality
with tabs[6]:
    st.subheader("How good is the matching?")
    st.caption("Graded against a hidden answer key that exists only because this data is synthetic. Real data would need a labeled sample.")
    if os.path.exists(KEY_PATH):
        import evaluate
        res = evaluate.grade(raw, pd.read_csv(KEY_PATH))
        k = st.columns(4)
        kpi(k[0], "Auto-accept precision", f"{res['auto_accept_precision']:.1%}", f"{res['auto_accepted_wrong_lines']} wrong auto-accepts")
        kpi(k[1], "Part lines auto-accepted", f"{res['auto_accept_share_of_part_lines']:.1%}", "the rest go to review")
        kpi(k[2], "Candidate recall (top 3)", f"{res['candidate_recall_top3']:.1%}", "true part appears among top 3 guesses")
        kpi(k[3], "Unit conversion exact", f"{res['uom_qty_each_exact']:.0%}", "pairs and boxes normalized to each")
        st.write("")
        k2 = st.columns(4)
        kpi(k2[0], "Part spend auto-accepted", f"{res['auto_accept_share_of_part_spend']:.1%}", "dollar-weighted, not just line count")
        kpi(k2[1], "Wrong auto-accepted $", usd(res['auto_accepted_wrong_spend']), "dollars at risk from silent errors")
        kpi(k2[2], "Unresolved exposure $", usd(res['review_spend']), f"{res['review_lines']} lines awaiting a human")
        kpi(k2[3], "Review share of lines", f"{res['review_share_of_all_lines']:.1%}", "analyst workload")
        st.write("")
        st.markdown(f"""
**Reading these honestly**
- **Text alone** auto-accepts about 77% of part lines with zero wrong; **supplier-SKU history** (a SKU confirmed once vouches for its other lines) lifts that to {res['auto_accept_share_of_part_lines']:.1%}.
- On **54 fresh descriptions written after tuning** (text only), 42 were auto-accepted with none wrong, and the other 12 went to review with the right guess on top. Small sample.
- **Not-a-part lines** (cartons, gloves, tape): {res['non_part_wrongly_auto_accepted']} wrongly auto-accepted; {res['non_part_correctly_unmatched']:.0%} left cleanly unmatched, the rest in review.
- This data is cleaner than real ERP exports and the abbreviations list was written by the same team that wrote the data, so **real-world accuracy will be lower**. That is why the review queue and a labeled pilot sample exist.
- Auto-accept never means engineering-approved: **identity is not interchangeability**.
""")
        with st.expander("All metrics"):
            st.json(res)
    else:
        st.info("Answer key not found. Place it in _answer_key/ to see grading.")


# ------------------------------------------------------------------------ pilot & limits
with tabs[7]:
    st.subheader("What we claim, what we don't, and how a real pilot would prove it")
    l, r = st.columns(2)
    with l:
        st.markdown("##### What PartLink claims")
        st.markdown("""
- An **auditable join** from an approved BOM revision to the prices actually paid, including spares.
- A **review queue** so a doubtful match never silently changes a cost number.
- Savings split into **identified, approved, realized**, with realized counted only after later invoices.
- Sourcing rules kept as **evidence with a source and date**, not a "compliant" badge.
""")
        st.markdown("##### What PartLink does not claim")
        st.markdown("""
- **Not actual unit cost.** It uses the approved BOM, not as-built records, and allocates spares by part usage (an assumption).
- **Not a legal compliance determination.** Rules change (e.g. the FCC Blue UAS exemption runs to 1 Jan 2027 unless extended).
- **Not proven on real data.** The demo data is synthetic and cleaner than real ERP exports.
- **Not a replacement for engineering approval.** A matched part is not an approved substitute.
- **Not unique at BOM-to-spend.** Platforms like Sievo, GEP, JAGGAER and Coupa document BOM and spend capabilities; the test is the last, auditable mile, with less buyer effort.
""")
    with r:
        st.markdown("##### Proposed pilot (8 weeks, read-only)")
        st.markdown("""
**Scope:** one consenting U.S. drone maker, one product family, 2 to 3 BOM revisions, purchased assemblies and recurring spares. Buyer: procurement or supply-chain lead. Engineering and finance sign off jointly.

**Data (read-only, fields needed only):** effective-dated approved BOMs, supplier and manufacturer part crosswalks, approved alternates, PO and invoice lines with paid prices, units and currency, credits and returns, supplier master, spares identifiers, agreed savings baseline.

**Timeline:** weeks 1 to 2 agree definitions, security boundary and a hand-labeled answer set. Weeks 3 to 5 ingest, reconcile and review exceptions. Weeks 6 to 8 test savings cases against actual transactions and recommend scale, revise or stop.

**Proposed pass/fail gates (agreed before loading data; proposals, not industry benchmarks):**
1. At least 90% of in-scope purchased dollars linked to an effective BOM or spares record, or explicitly classified as an exception.
2. At least 95% dollar-weighted precision on auto-accepted links in an independently reviewed sample. Report coverage and precision together.
3. 100% of ambiguous or non-approved substitutions held for review, never auto-approved.
4. An evidence trail for 100% of approved savings cases.
5. Success: finance verifies at least one realized saving from later paid transactions, and reviewer minutes per exception beat the current process.

**Stop condition:** if records cannot establish the approved configuration or the paid price reliably, fix master data before selling any savings claim.
""")
        st.markdown('<div class="pl-warn"><b>Pitch line.</b> Not a dashboard. An auditable join from approved BOM revision to actual paid price, including spares.</div>', unsafe_allow_html=True)
