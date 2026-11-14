#!/usr/bin/env python3
"""Grade the matcher against the hidden answer key. Reports separate metrics (one 'accuracy' hides trade-offs).

Usage: python3 evaluate.py [matches.csv] [answer_key.csv]
"""
import sys

import pandas as pd


def grade(matches: pd.DataFrame, key: pd.DataFrame) -> dict:
    d = matches.merge(key, on="spend_id", suffixes=("", "_k"))
    is_part = d.true_part_id != "NONE"
    parts = d[is_part]
    auto = d[d.status == "auto"]
    auto_correct = (auto.pred_part == auto.true_part_id)
    top3 = parts.candidates.str.split("; ").apply(lambda xs: [x.split(":")[0] for x in xs])
    recall_top3 = float(pd.Series([t in c for t, c in zip(parts.true_part_id, top3)]).mean())
    in_review = d[d.status == "review"]
    non = d[~is_part]
    res = {
        "lines": len(d),
        "part_lines": int(is_part.sum()),
        "candidate_recall_top3": round(recall_top3, 4),
        "auto_accept_share_of_part_lines": round(float((parts.status == "auto").mean()), 4),
        "auto_accept_share_of_part_spend": round(float(parts[parts.status == "auto"].extended_spend.sum() / parts.extended_spend.sum()), 4),
        "auto_accept_precision": round(float(auto_correct.mean()), 4),
        "auto_accepted_wrong_lines": int((~auto_correct).sum()),
        "auto_accepted_wrong_spend": round(float(auto[~auto_correct].extended_spend.sum()), 2),
        "review_lines": len(in_review),
        "review_spend": round(float(in_review.extended_spend.sum()), 2),
        "review_share_of_all_lines": round(len(in_review) / len(d), 4),
        "review_contains_true_part_in_top3": round(float(pd.Series(
            [t in [x.split(':')[0] for x in c.split('; ')] for t, c in zip(
                in_review.true_part_id, in_review.candidates)]).mean()), 4) if len(in_review) else None,
        "non_part_lines": int((~is_part).sum()),
        "non_part_correctly_unmatched": round(float((non.status == "unmatched").mean()), 4),
        "non_part_wrongly_auto_accepted": int((non.status == "auto").sum()),
        "part_lines_wrongly_unmatched": int((parts.status == "unmatched").sum()),
        "uom_qty_each_exact": round(float((d.qty_each == d.qty_each_k).mean()), 4),
        "uom_price_each_within_0.1pct": round(float(((d.price_each - d.unit_price_each).abs() / d.unit_price_each <= 0.001).mean()), 4),
        "channel_accuracy": round(float((d[is_part].channel_guess == d[is_part].channel).mean()), 4),
    }
    return res


if __name__ == "__main__":
    mp = sys.argv[1] if len(sys.argv) > 1 else "matches.csv"
    kp = sys.argv[2] if len(sys.argv) > 2 else "_answer_key/answer_key.csv"
    res = grade(pd.read_csv(mp), pd.read_csv(kp))
    for k, v in res.items():
        print(f"{k:42s} {v}")
