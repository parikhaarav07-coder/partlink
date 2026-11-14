# PartLink (demo)
BOM-to-spend cost linkage on synthetic drone-maker data. Hackathon: UIUC x Kearney PERLab, Track 3.

Run: `pip install -r requirements.txt && streamlit run app.py`
CLI: `python3 matcher.py` (matching) · `python3 evaluate.py` (grade vs `_answer_key/`, demo-only).

Caveats: synthetic data; savings are potential, not realized; sourcing rules are screening inputs, not legal
determinations (rules checked 2026-11-01); engineering must approve interchangeability; the optional Claude
wording polish is untested.
