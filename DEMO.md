# PartLink demo script (about 4 minutes)

Setup: `pip install -r requirements.txt && streamlit run app.py`. Start on the Drones pack (default); mention the sidebar switches to Medical devices with the same engine. Open on the Overview tab. Don't click Accept-all before the demo.

1. **Problem (30s).** A company's BOM says what it builds. Its spend data says what it bought. Nothing connects them, and spares and warranty parts never appear in the BOM. So nobody knows what a product really costs.
2. **Overview.** 99.1% of spend is mapped to an approved part. 26 lines need a human. Naive savings: $4.09M. After sourcing limits: $1.83M.
3. **Cost per unit (est.) tab.** Pick a product: production material plus allocated spares (allocated by usage, an assumption; approved BOM, not as-built). Point out the spares share the BOM never shows.
4. **Review queue.** Show that doubtful lines are never auto-accepted, and that the best guess is often wrong: a shipping carton looks like a propeller. Click "Demo: simulate expert reviewer". All 26 lines clear, 25 are marked "not a part", and the savings number stays right. Then "Clear decisions". Message: the human step protects the number.
5. **Savings simulator.** Untick the buyer-imposed and Blue UAS rules and watch net savings move. Drag the share-movable slider to 50%. Mention rules are screening inputs, not legal determinations.
6. **Savings ledger.** Identified is not realized. Realized only counts once later invoices show the lower price.
7. **Negotiation brief.** Choose a supplier and show the auto-generated brief.
8. **Match quality, then Pilot & limits.** Show dollar-weighted accuracy, then the pilot proposal and what we don't claim. State the caveats yourself: synthetic data, small samples, real-world accuracy will be lower. This builds trust.

Closing line: "Not a dashboard. An auditable join from approved BOM revision to actual paid price, including spares."

Likely judge questions: why drones (beachhead, then any BOM-heavy manufacturer); how this differs from Dassault/GEP (revision-aware matching to paid prices, including spares, with an audit trail); what is real vs synthetic (all data synthetic, rules checked 2026-11-01).
