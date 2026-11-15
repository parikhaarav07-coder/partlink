# PartLink (demo)
BOM-to-spend cost linkage on synthetic data. Hackathon: UIUC x Kearney PERLab, Track 3.

Run: `pip install -r requirements.txt && streamlit run app.py` (pick an industry in the sidebar, or open `?pack=medical`).

## Layout
- `.streamlit/config.toml` light purple theme (Kearney-style accent; brand colors approximated, no logo used).
- `core/` industry-agnostic engine: `matcher.py` (normalize, match, unit conversion), `analytics.py` (cost per unit, savings, near-duplicates, briefs), `evaluate.py` (grading), `store.py` (SQLite for review decisions and the savings ledger, per session), `pack.py` (loads packs).
- `packs/<industry>/` everything industry-specific: `pack.json` (labels, rule bases, wording, vocabulary, unit factors), `data/` (same CSV schema for every pack), `_answer_key/` (demo-only grading), `spec.py` (synthetic data generator spec).
- `rules/<industry>.json` dated rule records (title, authority, status, date, source, review date, which parts and suppliers it touches). Powers the Regulatory outlook tab. Six industries are covered; drones and medical devices also have full data packs.
- `core/foresight.py` joins those rules to a pack's BOM and spend.
- `tools/generate_pack.py packs/<id>` regenerates a synthetic pack.

Add an industry: copy a pack folder, edit `pack.json`, drop in your own CSVs (same columns). No engine code changes.

CLI: `python3 -m core.matcher packs/drones` · `python3 -m core.evaluate packs/drones` · `python3 packs/drones/stress_test.py`.

Caveats: synthetic data; savings are potential, not realized; sourcing rules are screening inputs, not legal determinations. Rule records were reviewed 2026-11-14 from public sources (each links its source) and are maintained by hand; some are marked 'verify' where I found only one source. Engineering must approve interchangeability.
