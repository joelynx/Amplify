"""Pilot A/B report: does the answer section in the solver prompt change
error rates or explanation quality?

For each question that has both a normal review (review_1.json of solver_1.tex)
and an A/B review (review_ab.json of solver_ab.tex, produced from
prompts/solver_noanswer.md), print the reviewer verdicts side by side and the
solution lengths, then totals.

Usage: python ab_report.py [qid ...]   (default: every question with review_ab.json)
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import OUTPUTS_DIR, parse_solver_output, read_json, read_text  # noqa: E402


def main() -> None:
    ids = [int(x) for x in sys.argv[1:]]
    if not ids:
        ids = sorted(int(p.parent.name) for p in OUTPUTS_DIR.glob("*/review_ab.json") if p.parent.name.isdigit())
    rows = []
    for qid in ids:
        d = OUTPUTS_DIR / str(qid)
        try:
            normal = read_json(d / "review_1.json")
            ab = read_json(d / "review_ab.json")
        except Exception as e:
            print(f"{qid}: missing review ({e})")
            continue
        pn, _ = parse_solver_output(read_text(d / "solver_1.tex"))
        pa, _ = parse_solver_output(read_text(d / "solver_ab.tex"), with_answer=False)
        rows.append({
            "qid": qid,
            "normal_correct": normal["new_solution_correct"], "ab_correct": ab["new_solution_correct"],
            "normal_errors": len(normal["errors"]), "ab_errors": len(ab["errors"]),
            "normal_agree": normal["answers_agree"], "ab_agree": ab["answers_agree"],
            "normal_rigor": normal["has_rigor_notes"], "ab_rigor": ab["has_rigor_notes"],
            "normal_len": len(pn["solution"]) if pn else None, "ab_len": len(pa["solution"]) if pa else None,
        })
    if not rows:
        print("no A/B pairs found")
        return
    print("qid | correct normal/ab | errors normal/ab | answers agree normal/ab | rigor normal/ab | solution chars normal/ab")
    for r in rows:
        print(f"{r['qid']} | {r['normal_correct']}/{r['ab_correct']} | {r['normal_errors']}/{r['ab_errors']} | {r['normal_agree']}/{r['ab_agree']} | {r['normal_rigor']}/{r['ab_rigor']} | {r['normal_len']}/{r['ab_len']}")
    n = len(rows)
    summary = {
        "pairs": n,
        "correct_rate_with_answer_section": sum(1 for r in rows if r["normal_correct"]) / n,
        "correct_rate_without": sum(1 for r in rows if r["ab_correct"]) / n,
        "mean_errors_with": statistics.mean(r["normal_errors"] for r in rows),
        "mean_errors_without": statistics.mean(r["ab_errors"] for r in rows),
        "mean_len_with": statistics.mean(r["normal_len"] for r in rows if r["normal_len"]),
        "mean_len_without": statistics.mean(r["ab_len"] for r in rows if r["ab_len"]),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
