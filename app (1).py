"""PartLink: BOM-to-spend cost intelligence (demo on synthetic data; industry is a configuration pack).

Run:  streamlit run app.py
"""
import json
import os

import altair as alt
import pandas as pd
import streamlit as st

import uuid

from core import analytics as A
from core import evaluate, foresight, matcher, store
from core.pack import list_packs, load_pack

st.set_page_config(page_title="PartLink", page_icon="🔗", layout="wide")

INK, MUTED, ACCENT, WARN, GOOD = "#14121A", "#3F3B4A", "#7823DC", "#C2410C", "#047857"
PURPLE_DK, PURPLE_LT = "#4B1A8F", "#F5F0FC"
st.markdown(f"""
<style>
.block-container {{padding-top: 1.4rem; max-width: 1250px;}}
h1, h2, h3, h4, h5 {{color: {INK}; letter-spacing: -0.01em;}}
h1 {{font-weight: 800;}}
[data-testid="stSidebar"] {{background: {PURPLE_LT}; border-right: 1px solid #E2D5F5;}}
button[role="tab"] p {{font-weight: 600; color: {INK};}}
button[role="tab"][aria-selected="true"] p {{color: {ACCENT};}}
.pl-banner {{background:{PURPLE_LT}; border-left:5px solid {ACCENT}; padding:.8rem 1.1rem; border-radius:6px; font-size:.95rem; color:{INK};}}
.pl-warn {{background:#FFF4E5; border-left:5px solid {WARN}; padding:.8rem 1.1rem; border-radius:6px; font-size:.95rem; color:{INK};}}
.pl-big {{font-size:2.05rem; font-weight:800; color:{ACCENT}; line-height:1.1; margin:.1rem 0; white-space:nowrap;}}
.pl-lab {{font-size:.8rem; font-weight:700; color:{INK}; text-transform:uppercase; letter-spacing:.06em;}}
.pl-sub {{font-size:.88rem; color:{MUTED};}}
.pl-card {{background:#FFFFFF; border:1px solid #E2D5F5; border-top:5px solid {ACCENT}; border-radius:8px; padding:.9rem 1rem; height:100%;}}
.pl-card b {{color:{ACCENT};}}
.pl-step {{font-size:.78rem; font-weight:800; color:{ACCENT}; letter-spacing:.08em;}}
.pl-hero {{font-size:1.15rem; font-weight:600; color:{INK}; margin:.2rem 0 .8rem 0;}}
</style>""", unsafe_allow_html=True)

PACKS = list_packs()
_by_name = {p.name: p for p in PACKS}
_qp = st.query_params.get("pack")
_default = next((i for i, p in enumerate(PACKS) if p.id == _qp), 0)
pick = st.sidebar.selectbox("Industry pack", [p.name for p in PACKS], index=_default,
                            help="The engine is identical for every industry. A pack supplies the data, vocabulary and rule labels.")
PACK = _by_name[pick]
st.sidebar.caption(PACK.cfg["text"]["company_blurb"])
DATA_DIR, KEY_PATH = PACK.data_dir, PACK.key_path
BASES, BASIS_LABEL = PACK.bases, PACK.basis_label
T, X = PACK.term, PACK.text

if "sid" not in st.session_state:
    st.session_state.sid = st.query_params.get("s") or uuid.uuid4().hex[:12]
SID = st.session_state.sid


@st.cache_data(show_spinner="Matching purchase lines to parts…")
def get_matches(pack_id):
    p = load_pack(pack_id)
    return matcher.run_matching(p.data_dir, lex=p.lexicon, uom=p.uom, spares_plant_prefix=p.spares_plant_prefix)


@st.cache_data
def get_data(pack_id):
    return A.load_data(load_pack(pack_id).data_dir)


def usd(x, d=0):
    return f"${x:,.{d}f}"


def kpi(col, label, value, sub=""):
    col.markdown(f'<div class="pl-lab">{label}</div><div class="pl-big">{value}</div><div class="pl-sub">{sub}</div>',
                 unsafe_allow_html=True)


raw = get_matches(PACK.id)
d = get_data(PACK.id)
# decisions and ledger live in SQLite (per session and pack); session_state mirrors them for the current run
if st.session_state.get("_loaded") != (SID, PACK.id):
    st.session_state.approvals = store.load_decisions(SID, PACK.id)
    st.session_state.ledger_status = store.load_ledger(SID, PACK.id)
    st.session_state._loaded = (SID, PACK.id)


def set_approvals(new):
    st.session_state.approvals = new
    store.save_decisions(SID, PACK.id, new)

m = A.effective(raw, st.session_state.approvals)
cov = A.coverage(m)

# ------------------------------------------------------------------------ header
st.title("PartLink")
st.caption("Connect every purchase to the approved part it belongs to, and see what each product costs, spares included (estimate).")
st.markdown(f'<div class="pl-banner"><b>Demo on synthetic data.</b> {X("company_blurb")} ({len(d["products"].family.unique())} product families, {len(d["parts_master"])} parts, {len(d["suppliers"])} suppliers, '
            f'{len(raw):,} purchase lines). Savings shown are <b>potential</b>, not realized, and nothing here is a legal '
            'compliance determination.</div>', unsafe_allow_html=True)
st.write("")

MAIN_TABS = ["Overview", "Review queue", "Savings simulator", "Regulatory outlook", "Pilot & limits", "More"]
MORE_TABS = ["Cost per unit (est.)", "Savings ledger", "Negotiation brief", "Match quality"]
tabs = dict(zip(MAIN_TABS, st.tabs(MAIN_TABS)))
with tabs["More"]:
    st.caption("Supporting views: cost per unit, the savings ledger, negotiation briefs and match quality.")
    tabs.update(dict(zip(MORE_TABS, st.tabs(MORE_TABS))))

# ------------------------------------------------------------------------ overview
with tabs["Overview"]:
    st.markdown('<div class="pl-hero">A company\'s bill of materials says what it builds. Its spend data says what it bought. Nobody joins them, so nobody knows what a product really costs or which savings are real.</div>', unsafe_allow_html=True)
    s1, s2, s3 = st.columns(3)
    s1.markdown('<div class="pl-card"><div class="pl-step">1 · CONNECT</div><b>Every purchase line to its approved part</b><br>Messy descriptions, units and supplier codes are normalized and matched.</div>', unsafe_allow_html=True)
    s2.markdown('<div class="pl-card"><div class="pl-step">2 · CHECK</div><b>A human reviews every doubtful match</b><br>A wrong guess never silently changes a cost number.</div>', unsafe_allow_html=True)
    s3.markdown('<div class="pl-card"><div class="pl-step">3 · DECIDE</div><b>Cost per unit and savings net of rules</b><br>Including spares, with sourcing rules as dated, cited evidence.</div>', unsafe_allow_html=True)
    st.write("")
    sc_all = A.savings_scenario(m, d)
    sp = A.spares_premium(m)
    tc = A.true_cost(m, d)
    c = st.columns(4)
    kpi(c[0], "Spend mapped to a part", f"{cov['mapped_pct']:.1%}", f"{usd(cov['unresolved_spend'])} awaiting review")
    kpi(c[1], "Lines needing a human", f"{cov['unresolved_lines']}", "of {:,} purchase lines".format(len(raw)))
    kpi(c[2], "Potential savings (net)", usd(sc_all.scenario_savings.sum()), "after sourcing limits, if all volume moves")
    kpi(c[3], "Spares paid above production price", usd(sp.premium_usd.sum()), "illustrative, same part, same year")
    st.write("")
    st.subheader("What PartLink found")
    nd = A.near_duplicates(d["parts_master"], m, PACK.lexicon)
    naive, net = sc_all.naive_savings.sum(), sc_all.scenario_savings.sum()
    top = sc_all.iloc[0]
    st.markdown(f"""
- **A naive "buy everything from the cheapest supplier" view promises {usd(naive)}. Respecting sourcing limits cuts it to {usd(net)}.**
  The {usd(naive - net)} gap is the cost of {T('restricted_note')}. Largest single opportunity: **{top.part_id}** ({usd(top.scenario_savings)} net).
- **Spares are bought at a premium.** Fleet spares cost {usd(sp.premium_usd.sum())} more than the same parts at production prices; batteries and thermal cameras lead.
  Spares add **{tc.spares_pct_of_cost.min():.0%}–{tc.spares_pct_of_cost.max():.0%}** to each product's estimated cost per unit, a cost the production BOM never shows (allocated by part usage, an assumption).
- **Near-duplicate parts are flagged, not assumed swappable.** {len(nd)} pair(s) found (e.g. {nd.part_a.iloc[0]} vs {nd.part_b.iloc[0]}, differing only on {nd.differs_on.iloc[0]}). Standardizing is worth {usd(nd.potential_if_standardized.sum())} only if engineering approves.
""" if len(nd) else f"- Naive view: {usd(naive)}; net of sourcing limits: {usd(net)}.")
    st.markdown('<div class="pl-warn"><b>How to read these numbers.</b> They are computed from average paid prices in this '
                'synthetic data. Real savings need engineering approval, supplier qualification, a negotiated change, and '
                'later invoices that show it (see Savings ledger).</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------ true cost
with tabs["Cost per unit (est.)"]:
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
with tabs["Review queue"]:
    st.subheader("Review queue")
    st.caption(f"PartLink never auto-accepts a doubtful match, and the best guess is often wrong ({X("review_example")}). A human decides: pick a part, or 'NONE' if it is not a tracked part. Decisions update every number in the app. The demo button simulates an expert reviewer using the hidden answer key.")
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
        set_approvals({**st.session_state.approvals, **{r.spend_id: _k[r.spend_id] for r in rq.itertuples()}})
        st.rerun()
    if c2.button("Clear decisions"):
        set_approvals({})
        st.rerun()
    edited = st.data_editor(view, hide_index=True, width='stretch', key="rq_editor",
                            disabled=[c for c in view.columns if c != "Decision"],
                            column_config={"Decision": st.column_config.SelectboxColumn(options=options, required=True),
                                           "Spend $": st.column_config.NumberColumn(format="$%.0f"),
                                           "Confidence": st.column_config.ProgressColumn(min_value=0, max_value=1, format="%.2f")})
    new = {r.Line: ("NONE" if r.Decision.startswith("NONE") else r.Decision) for r in edited.itertuples() if r.Decision != "Pending"}
    if new != st.session_state.approvals:
        set_approvals(new)
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
with tabs["Savings simulator"]:
    st.subheader("What-if savings simulator")
    st.caption("Choose which sourcing requirements bind, and how much volume you can realistically move.")
    left, right = st.columns([1, 2])
    with left:
        enforce = st.multiselect(T("binding_label"), BASES,
                                 default=BASES, format_func=lambda b: BASIS_LABEL[b])
        share = st.slider("Share of volume you can move", 0, 100, 100, 5, format="%d%%") / 100
        st.markdown(f'<div class="pl-sub">{X("rules_note")}</div>', unsafe_allow_html=True)
    sc = A.savings_scenario(m, d, enforce=enforce, share_movable=share)
    with right:
        k = st.columns(3)
        kpi(k[0], "Naive view", usd(sc.naive_savings.sum()), "all volume to cheapest supplier")
        kpi(k[1], T("rule_cost"), usd(sc.compliance_cost.sum()), T("rule_cost_sub"))
        kpi(k[2], "Net potential savings", usd(sc.scenario_savings.sum()), f"at {share:.0%} of volume movable")
    bar = sc.head(10).melt(id_vars="part_id", value_vars=["naive_savings", "scenario_savings"], var_name="view", value_name="usd")
    bar["view"] = bar.view.map({"naive_savings": "Naive", "scenario_savings": "Net of sourcing limits"})
    st.altair_chart(alt.Chart(bar).mark_bar().encode(
        y=alt.Y("part_id:N", sort="-x", title=None),
        x=alt.X("usd:Q", title="Potential annual savings (USD)"),
        yOffset="view:N", color=alt.Color("view:N", scale=alt.Scale(range=["#C9B8E8", ACCENT]), legend=alt.Legend(title=None, orient="top")),
        tooltip=["part_id", "view", alt.Tooltip("usd:Q", format="$,.0f")]).properties(height=360), width='stretch')
    st.dataframe(sc[["part_id", "requirement_basis", "avg_paid", "best_any_supplier", "best_compliant", "naive_savings",
                     "compliance_cost", "scenario_savings"]].rename(columns={
        "part_id": "Part", "requirement_basis": "Basis", "avg_paid": "Avg paid", "best_any_supplier": "Best price (any)",
        "best_compliant": "Best qualified", "naive_savings": "Naive $", "compliance_cost": T("rule_cost") + " $",
        "scenario_savings": "Net $"}).style.format({"Avg paid": "${:,.2f}", "Best price (any)": "${:,.2f}", "Best compliant": "${:,.2f}",
                                                    "Naive $": "${:,.0f}", T("rule_cost") + " $": "${:,.0f}", "Net $": "${:,.0f}"}),
        hide_index=True, width='stretch')
    st.markdown("##### Near-duplicate parts: needs engineering review")
    nd = A.near_duplicates(d["parts_master"], m, PACK.lexicon)
    st.dataframe(nd.style.format({"price_gap_each": "${:,.2f}", "qty_at_higher_price": "{:,.0f}", "potential_if_standardized": "${:,.0f}"}),
                 hide_index=True, width='stretch')
    st.markdown("##### Spares priced above production (illustrative)")
    spx = A.spares_premium(m).head(8)
    st.dataframe(spx[["effective_part", "qty", "avg_price", "production_price", "premium_pct", "premium_usd"]].rename(columns={
        "effective_part": "Part", "qty": "Spares qty", "avg_price": "Spares price", "production_price": "Production price",
        "premium_pct": "Premium", "premium_usd": "Premium $"}).style.format({
        "Spares qty": "{:,.0f}", "Spares price": "${:,.2f}", "Production price": "${:,.2f}", "Premium": "{:.0%}", "Premium $": "${:,.0f}"}),
        hide_index=True, width='stretch')
    st.caption(X("spares_note"))

# ------------------------------------------------------------------------ ledger
with tabs["Savings ledger"]:
    st.subheader("Savings ledger: from identified to realized")
    st.caption("A price spread is not cash saved. Each opportunity must pass engineering, procurement and finance. "
               "'Realized' should only be set when later invoices show the lower price.")
    sc0 = A.savings_scenario(m, d)
    nd = A.near_duplicates(d["parts_master"], m, PACK.lexicon)
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
    _new_led = dict(zip(ed.Opportunity, ed.Status))
    if _new_led != st.session_state.ledger_status:
        st.session_state.ledger_status = _new_led
        store.save_ledger(SID, PACK.id, _new_led)
    tot = ed.groupby("Status")["Identified $"].sum().reindex(stages).fillna(0)
    cc = st.columns(4)
    for col, s in zip(cc, stages):
        kpi(col, s, usd(tot[s]), f"{int((ed.Status == s).sum())} item(s)")

# ------------------------------------------------------------------------ negotiation brief
with tabs["Negotiation brief"]:
    st.subheader("Negotiation brief")
    sup = d["suppliers"]
    sid = st.selectbox("Supplier", sup.supplier_id.tolist(),
                       format_func=lambda s: f"{s} · " + sup.set_index("supplier_id").loc[s, "supplier_name"])
    brief = A.negotiation_brief(m, d, sid)
    if os.environ.get("ANTHROPIC_API_KEY") and st.checkbox("Polish wording with Claude (numbers stay as computed)"):
        brief = A.llm_polish(brief)
    st.text_area("Brief (copy into an email or deck)", brief, height=380)

# ------------------------------------------------------------------------ match quality
with tabs["Match quality"]:
    st.subheader("How good is the matching?")
    st.caption("Graded against a hidden answer key that exists only because this data is synthetic. Real data would need a labeled sample.")
    if os.path.exists(KEY_PATH):
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
        notes = "\n".join("- " + n.replace("{auto_share}", f"{res['auto_accept_share_of_part_lines']:.1%}") for n in X("match_notes") if True) if isinstance(X("match_notes"), list) else ""
        st.markdown(f"""
**Reading these honestly**
{notes}
- **Not-a-part lines** (cartons, gloves, tape): {res['non_part_wrongly_auto_accepted']} wrongly auto-accepted; {res['non_part_correctly_unmatched']:.0%} left cleanly unmatched, the rest in review.
- This data is cleaner than real ERP exports and the abbreviations list was written by the same team that wrote the data, so **real-world accuracy will be lower**. That is why the review queue and a labeled pilot sample exist.
- Auto-accept never means engineering-approved: **identity is not interchangeability**.
""")
        with st.expander("All metrics"):
            st.json(res)
    else:
        st.info("Answer key not found. Place it in _answer_key/ to see grading.")


# ------------------------------------------------------------------------ regulatory outlook
with tabs["Regulatory outlook"]:
    LIBS = foresight.load_libraries()
    lib = LIBS.get(PACK.id, {"industry": PACK.name, "rules": []})
    rules = lib["rules"]
    st.subheader("Regulatory outlook")
    st.caption("Dated rule changes for this industry, joined to your BOM and spend. Rules are entered by hand with a source and review date; PartLink does not scrape regulators or decide what is legal. Not legal advice.")
    st.markdown('<div class="pl-warn">Dollar figures are <b>exposure</b>: spend that a rule would touch today, not a forecast of what it will cost. Tariff costs use one assumed rate for all affected spend, because this demo holds no HTS codes.</div>', unsafe_allow_html=True)
    st.write("")
    mm = A.effective(raw, st.session_state.approvals)
    rows = []
    for r in rules:
        ex = foresight.exposure(r, mm, d)
        dd = foresight.days_until(r)
        rows.append({"Rule": r["title"], "Status": foresight.STATUS_LABEL[r["status"]], "Date": r["date_label"],
                     "Days": (dd if (dd is not None and r["status"] == "scheduled") else None),
                     "Parts touched": len(ex), "Exposed spend": float(ex.exposed_spend.sum()) if len(ex) else 0.0, "_id": r["id"], "_ex": ex})
    sched = sorted([x for x in rows if x["Days"] is not None and x["Days"] >= 0], key=lambda x: x["Days"])
    k = st.columns(3)
    kpi(k[0], "Rules tracked", str(len(rules)), f"{sum(1 for r in rules if r['status']=='in_force')} in force, {sum(1 for r in rules if r['status']=='scheduled')} scheduled, {sum(1 for r in rules if r['status']=='pending')} pending")
    if sched:
        kpi(k[1], "Next dated change", f"{sched[0]['Days']} days", sched[0]["Rule"][:70])
        kpi(k[2], "Spend it would touch", usd(sched[0]["Exposed spend"]), "production spend with affected suppliers")
    st.write("")
    dated = [{"Rule": (r["title"][:46] + ("…" if len(r["title"]) > 46 else "")), "Date": r["date"], "Status": foresight.STATUS_LABEL[r["status"]]}
             for r in rules if r.get("date")]
    if dated:
        tdf = pd.DataFrame(dated)
        tdf["Date"] = pd.to_datetime(tdf["Date"])
        today = pd.Timestamp.today().normalize()
        base = alt.Chart(tdf).encode(y=alt.Y("Rule:N", sort=alt.EncodingSortField("Date"), title=None, axis=alt.Axis(labelLimit=330, labelColor=INK)))
        pts = base.mark_circle(size=260).encode(x=alt.X("Date:T", title=None),
            color=alt.Color("Status:N", scale=alt.Scale(domain=["In force", "Scheduled", "Pending"], range=[ACCENT, WARN, "#6B7280"]), legend=alt.Legend(title=None, orient="top")),
            tooltip=["Rule", alt.Tooltip("Date:T", format="%d %b %Y"), "Status"])
        line = alt.Chart(pd.DataFrame({"Date": [today]})).mark_rule(color=INK, strokeDash=[4, 4]).encode(x="Date:T")
        lab = alt.Chart(pd.DataFrame({"Date": [today], "t": ["today"]})).mark_text(dy=-6, align="left", dx=4, color=INK, fontWeight="bold").encode(x="Date:T", text="t:N", y=alt.value(8))
        st.altair_chart((pts + line + lab).properties(height=max(150, 46 * len(tdf))), width="stretch")
        st.caption("Dated rules only. Undated rules are in the table below.")
    tbl = pd.DataFrame([{k_: v for k_, v in x.items() if not k_.startswith("_")} for x in rows])
    st.dataframe(tbl.style.format({"Exposed spend": "${:,.0f}", "Days": "{:,.0f}"}, na_rep="-"), hide_index=True, width='stretch')
    if rules:
        pick_r = st.selectbox("Open a rule", [r["id"] for r in rules], format_func=lambda i: next(r["title"] for r in rules if r["id"] == i))
        r = next(r for r in rules if r["id"] == pick_r)
        ex = next(x["_ex"] for x in rows if x["_id"] == pick_r)
        st.markdown(f"**{r['title']}**  \n{foresight.STATUS_LABEL[r['status']]} · {r['date_label']} · {r['authority']}")
        st.markdown(f"{r['summary']}")
        st.markdown(f"**Why it matters for the BOM.** {r['why_it_matters']}")
        st.markdown(f"**Workaround to explore.** {r['workaround']}")
        src = f"[{r['source']}]({r['source_url']})" if r.get("source_url") else r["source"]
        st.caption(f"Source: {src} · reviewed {r['checked_on']} · confidence: {r['confidence']}")
        if r["impact"] == "none" or ex.empty:
            st.info("No parts in this pack are touched by this rule, or it is watch-only." if r["impact"] != "none" else "Watch-only: no BOM exposure is calculated for this rule.")
        elif r["impact"] == "tariff":
            rate = st.slider("Assumed duty rate (scenario, not a forecast)", 0, 100, 25, 5, format="%d%%") / 100
            ex = ex.assign(added_duty=ex.exposed_spend * rate)
            c = st.columns(2)
            kpi(c[0], "Spend with affected suppliers", usd(ex.exposed_spend.sum()), "production spend, non-U.S. suppliers")
            kpi(c[1], "Added duty at this rate", usd(ex.added_duty.sum()), "if all of it stayed put")
            st.dataframe(ex[["part_id", "exposed_suppliers", "exposed_spend", "added_duty", "alt_supplier", "alt_price", "avg_paid"]].rename(columns={
                "part_id": "Part", "exposed_suppliers": "Affected suppliers", "exposed_spend": "Spend $", "added_duty": "Added duty $",
                "alt_supplier": "Unaffected alternative on file", "alt_price": "Alt price", "avg_paid": "Avg paid"}).style.format({
                "Spend $": "${:,.0f}", "Added duty $": "${:,.0f}", "Alt price": "${:,.2f}", "Avg paid": "${:,.2f}"}, na_rep="-"), hide_index=True, width='stretch')
        else:
            c = st.columns(2)
            kpi(c[0], "Spend with affected suppliers", usd(ex.exposed_spend.sum()), f"{len(ex)} part(s)")
            if r["impact"] == "switch":
                kpi(c[1], "Est. cost to switch to alternates on file", usd(ex.switch_cost.sum(skipna=True)), "alternate avg price vs today's, same volume")
            st.dataframe(ex[["part_id", "exposed_suppliers", "exposed_spend", "avg_paid", "alt_supplier", "alt_price", "switch_cost"]].rename(columns={
                "part_id": "Part", "exposed_suppliers": "Affected suppliers", "exposed_spend": "Spend $", "avg_paid": "Avg paid",
                "alt_supplier": "Alternative on file", "alt_price": "Alt price", "switch_cost": "Switch cost $"}).style.format({
                "Spend $": "${:,.0f}", "Avg paid": "${:,.2f}", "Alt price": "${:,.2f}", "Switch cost $": "${:,.0f}"}, na_rep="-"), hide_index=True, width='stretch')
            if r["impact"] == "documentation":
                st.caption("This rule adds documentation duties rather than a purchase ban, so the table shows who supplies the affected parts, not a dollar cost.")
    with st.expander("Rule library for every industry"):
        st.caption("Industries with a full data pack run end to end. The others show the rules only; bring a BOM and spend export in the same CSV format to get exposure.")
        lib_pick = st.selectbox("Industry", list(LIBS), index=list(LIBS).index(PACK.id) if PACK.id in LIBS else 0,
                                format_func=lambda k_: LIBS[k_]["industry"] + ("" if LIBS[k_].get("pack") else "  (rules only)"))
        for r in LIBS[lib_pick]["rules"]:
            link = f" · [source]({r['source_url']})" if r.get("source_url") else f" · {r['source']}"
            st.markdown(f"- **{r['title']}** ({foresight.STATUS_LABEL[r['status']]}, {r['date_label']}). {r['summary']}{link}")

# ------------------------------------------------------------------------ pilot & limits
with tabs["Pilot & limits"]:
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
        st.markdown(f"""
- **Not actual unit cost.** It uses the approved BOM, not as-built records, and allocates spares by part usage (an assumption).
- **Not a legal compliance determination.** {X('rules_change_example')}
- **Not proven on real data.** The demo data is synthetic and cleaner than real ERP exports.
- **Not a replacement for engineering approval.** A matched part is not an approved substitute.
- **Not unique at BOM-to-spend.** Platforms like Sievo, GEP, JAGGAER and Coupa document BOM and spend capabilities; the test is the last, auditable mile, with less buyer effort.
""")
    with r:
        st.markdown("##### Proposed pilot (8 weeks, read-only)")
        st.markdown(f"""
**Scope:** {X('pilot_scope')}. Buyer: procurement or supply-chain lead. Engineering and finance sign off jointly.

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
