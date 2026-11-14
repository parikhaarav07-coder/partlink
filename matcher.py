#!/usr/bin/env python3
"""PartLink matching engine: purchase lines -> engineering parts.

Reads ONLY the data/ folder (never the answer key). Pipeline:
  1. normalize text (case, noise words, abbreviations, units like 10000mAh -> 10Ah)
  2. score every line against every master part with IDF-weighted token overlap (+ typo-tolerant fuzzy tokens)
  3. supplier-SKU memory: a SKU confidently matched once vouches for other lines with the same SKU
  4. confidence = score x margin-over-runner-up; route to auto / review / unmatched
  5. normalize unit of measure (PR = pair, BX100 = box of 100) to each-quantity and each-price
  6. sanity-check price per each against the part's median; outliers go to review

Usage: python3 matcher.py [data_dir] [out_csv]
"""
import math
import re
import sys
from collections import Counter, defaultdict

import pandas as pd
from rapidfuzz import fuzz

# ---------------------------------------------------------------- tunable settings
AUTO_CONF = 0.78        # auto-accept at or above this confidence
REVIEW_FLOOR = 0.35     # below this the line is treated as "not a part we track"
PRICE_BAND = 2.5        # flag price per each more than this factor from the part median
UOM_FACTORS = {"EA": 1, "PR": 2, "BX100": 100}   # unknown units always go to review

NOISE = {"rohs", "bulk", "lot", "rev", "w", "the", "and", "of", "for", "with", "no", "a", "in", "ac", "dc"}
SYNONYMS = {
    "mtr": "motor", "bldc": "brushless", "ctrl": "controller", "control": "controller", "brd": "board",
    "pcb": "board", "mod": "module", "pwr": "power", "dist": "distribution", "cam": "camera",
    "flt": "flight", "batt": "battery", "prop": "propeller", "cf": "carbon", "hsg": "housing",
    "assy": "assembly", "thm": "thermal", "ir": "thermal", "imager": "camera", "eo": "visible",
    "rf": "radio", "telemetry": "link", "weatherproof": "", "pogo": "spring", "housing": "enclosure",
    "skid": "gear", "landing": "landing", "gnss": "gps", "speed": "speed", "amp": "a", "pdb": "pdb",
    "fiber": "carbon", "liion": "liion", "pack": "", "smart": "", "outdoor": "", "ax": "axis", "3ax": "3 axis",
    "autopilot": "controller", "harness": "harness", "cable": "", "uf1": "ufl",
}
EXPANSIONS = {"pdb": ["power", "distribution", "board"], "esc": ["electronic", "speed", "controller"],
              "fc": ["flight", "controller"], "psu": ["power", "supply"], "wx": ["weather"]}


def normalize(text: str) -> list[str]:
    t = str(text).lower()
    t = re.sub(r"(\d+(?:\.\d+)?)\s*mah", lambda m: f" {float(m.group(1)) / 1000:g}ah ", t)
    t = re.sub(r"(\d+(?:\.\d+)?)\s*kw", lambda m: f" {float(m.group(1)) * 1000:g}w ", t)
    t = t.replace("u.fl", "ufl").replace("li-ion", "liion").replace("m9n", "m9").replace("3-axis", "3 axis")
    t = re.sub(r"(\d)x(\d)", r"\1 \2", t)            # 10x4.5 -> 10 4.5 ; m3x8 handled below
    t = re.sub(r"\bm(\d)\s*[- ]?\d*\.?\d*\s*x\s*(\d+)", r"m\1 \2", t)
    t = re.sub(r"[^a-z0-9.]+", " ", t)
    t = re.sub(r"(\d+)\s*(in|a|v|w|ah|s|mhz|kv|mm)\b", r"\1 \2", t)   # split number and unit
    toks = []
    for raw in t.split():
        raw = raw.strip(".")
        if not raw:
            continue
        if raw in EXPANSIONS:
            toks += EXPANSIONS[raw]
            continue
        raw = SYNONYMS.get(raw, raw)
        for w in raw.split():
            if w in NOISE or not w:
                continue
            if w.startswith("fc") and w[2:].isdigit():       # fc7 -> fc 7
                toks += ["flight", "controller", w[2:]]
                continue
            toks.append(stem(w))
    return toks


def stem(w: str) -> str:
    if len(w) > 4 and w.endswith("ing"):
        w = w[:-3]
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss") and not re.search(r"\d", w):
        w = w[:-1]
    if len(w) > 3 and w.endswith("e") and not re.search(r"\d", w):
        w = w[:-1]
    return w


class PartIndex:
    def __init__(self, parts: pd.DataFrame):
        self.ids = list(parts.part_id)
        self.tokens = {p: set(normalize(d)) for p, d in zip(parts.part_id, parts.description)}
        df = Counter(tok for ts in self.tokens.values() for tok in ts)
        n = len(self.ids)
        self.idf = {tok: math.log((n + 1) / (c + 0.5)) + 0.2 for tok, c in df.items()}
        self.vocab = set(self.idf)

    def w(self, tok):
        return self.idf.get(tok, 0.0)

    def score_line(self, text: str):
        """Return list of (part_id, score, shared_tokens) sorted best-first."""
        line_tokens = set(normalize(text))
        # typo tolerance: map unknown word tokens to the closest vocabulary word
        fixed = set()
        for tok in line_tokens:
            if tok in self.vocab or tok.replace(".", "").isdigit():
                fixed.add(tok)
                continue
            if len(tok) >= 5 and tok.isalpha():
                best = max(self.vocab, key=lambda v: fuzz.ratio(tok, v) if v.isalpha() else 0)
                if fuzz.ratio(tok, best) >= 86:
                    fixed.add(best)
                    continue
            fixed.add(tok)
        known = {t for t in fixed if t in self.vocab}
        out = []
        for p in self.ids:
            mt = self.tokens[p]
            shared = mt & fixed
            recall = sum(self.w(t) for t in shared) / max(1e-9, sum(self.w(t) for t in mt))
            prec = sum(self.w(t) for t in shared) / max(1e-9, sum(self.w(t) for t in known)) if known else 0.0
            # a line carrying a model number that belongs to another part is a conflict
            conflict = sum(self.w(t) for t in known - mt if re.search(r"\d", t) and self.w(t) > 1.6)
            score = 0.65 * recall + 0.35 * prec - 0.10 * min(1.0, conflict / 3)
            out.append((p, max(0.0, score), sorted(shared)))
        out.sort(key=lambda x: -x[1])
        return out


def confidence(top: float, runner: float) -> float:
    margin = max(0.0, top - runner)
    return top * (1 - math.exp(-margin * 12))


def run_matching(data_dir: str = "data", use_sku: bool = True) -> pd.DataFrame:
    parts = pd.read_csv(f"{data_dir}/parts_master.csv")
    spend = pd.read_csv(f"{data_dir}/spend_lines.csv")
    idx = PartIndex(parts)

    rows = []
    for r in spend.itertuples(index=False):
        ranked = idx.score_line(r.line_description)
        (p1, s1, sh1), (p2, s2, _) = ranked[0], ranked[1]
        conf = confidence(s1, s2)
        rows.append({
            "spend_id": r.spend_id, "pred_part": p1, "score": round(s1, 4), "runner_up": p2,
            "runner_score": round(s2, 4), "confidence": round(conf, 4), "method": "text",
            "shared_tokens": " ".join(sh1),
            "candidates": "; ".join(f"{p}:{s:.2f}" for p, s, _ in ranked[:3]),
        })
    m = pd.DataFrame(rows).merge(spend, on="spend_id")

    # ---- step 3: supplier SKU memory (a confidently matched SKU vouches for its other lines)
    votes = defaultdict(Counter)
    for r in m[m.confidence >= AUTO_CONF].itertuples():
        votes[(r.supplier_id, r.supplier_sku)][r.pred_part] += 1
    sku_part = {k: c.most_common(1)[0][0] for k, c in votes.items() if len(c) == 1} if use_sku else {}
    for i, r in m.iterrows():
        key = (r.supplier_id, r.supplier_sku)
        if r.confidence < AUTO_CONF and key in sku_part:
            part = sku_part[key]
            m.at[i, "method"] = "sku-history"
            m.at[i, "pred_part"] = part
            m.at[i, "confidence"] = max(r.confidence, 0.82 if r.score >= 0.25 else 0.5)
            m.at[i, "shared_tokens"] = f"SKU {r.supplier_sku} previously confirmed as {part}"

    # ---- step 5: unit-of-measure normalization
    m["uom_factor"] = m.uom.map(UOM_FACTORS)
    unknown_uom = m.uom_factor.isna()
    m["uom_factor"] = m.uom_factor.fillna(1).astype(int)
    m["qty_each"] = m.qty * m.uom_factor
    m["price_each"] = m.unit_price / m.uom_factor

    # ---- step 6: price sanity vs part median (same channel)
    m["channel_guess"] = m.plant.str.startswith("MEM").map({True: "spares", False: "production"})
    ok = m[(m.confidence >= AUTO_CONF)]
    med = ok.groupby(["pred_part", "channel_guess"]).price_each.median()
    m["price_vs_median"] = [
        r.price_each / med.get((r.pred_part, r.channel_guess), r.price_each) for r in m.itertuples()]
    price_outlier = (m.price_vs_median > PRICE_BAND) | (m.price_vs_median < 1 / PRICE_BAND)

    # ---- routing
    status, why = [], []
    for i, r in m.iterrows():
        notes = []
        if r.confidence < REVIEW_FLOOR:
            status.append("unmatched")
            notes.append("no part scored high enough: likely not a tracked part")
        elif unknown_uom[i]:
            status.append("review")
            notes.append(f"unknown unit of measure '{r.uom}'")
        elif price_outlier[i]:
            status.append("review")
            notes.append("price per each far from median: check unit of measure")
        elif r.confidence >= AUTO_CONF:
            status.append("auto")
        else:
            status.append("review")
            gap = r.score - r.runner_score
            if gap < 0.12:
                notes.append(f"close call with {r.runner_up} (gap {gap:.2f})")
            else:
                notes.append("weak text evidence")
        if r.uom != "EA" and status[-1] != "unmatched":
            notes.append(f"{r.uom} converted x{r.uom_factor}")
        if r.method == "text" and status[-1] != "unmatched":
            notes.insert(0, f"matched on: {r.shared_tokens}")
        elif r.method == "sku-history":
            notes.insert(0, r.shared_tokens)
        why.append(" | ".join(notes))
    m["status"] = status
    m["reason"] = why
    m.loc[m.status == "unmatched", "pred_part"] = "NONE"
    return m


if __name__ == "__main__":
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "data"
    out = sys.argv[2] if len(sys.argv) > 2 else "matches.csv"
    res = run_matching(data_dir)
    res.to_csv(out, index=False)
    print(res.status.value_counts().to_dict(), "->", out)
