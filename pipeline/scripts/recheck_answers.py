"""Re-check accepted subject replies against the source's stored answers with the current
comparison (subjects.reference_mismatch and keys_agree), after the checker was tightened
(owner 2026-11-12: the judge's tolerance, not the solver's TOL; differing numbers of values
compared in order; unit factors only between different units; subscripts not read as values).

No model, no compile, and both databases are opened read-only. For each subject question
(mode solve or aids) whose reply was accepted:
  - reference: the source's own answer, i.e. answer_before_replace when the pipeline replaced
    it, else the app's answer unless the pipeline wrote it;
  - a reply that replaced the stored answer after a tie-break: whether an earlier solve still
    agrees with it (keys_agree); a review solve's replacement is final and only listed;
  - any other accepted reply: whether its key now disagrees with the reference.

Usage (from the repo root):
  python pipeline/scripts/recheck_answers.py [--ids 1,2,3]
Output: pipeline/reports/answer_recheck.csv and a summary on stdout.
"""

from __future__ import annotations

import argparse
import collections
import csv
import sqlite3
import sys

import subjects
from common import (
    OUTPUTS_DIR,
    PIPELINE_DB,
    PIPELINE_DIR,
    app_conn,
    fetch_question,
    is_blank,
    load_config,
    read_text,
    strip_code_fences,
)

REPORT = PIPELINE_DIR / "reports" / "answer_recheck.csv"
FIELDS = ("question_id", "mode", "subject", "outcome", "reference", "key_values", "detail")


def accepted_key(qid: int, attempt: int, mode: str, latex: str) -> dict | None:
    f = OUTPUTS_DIR / str(qid) / f"solver_{attempt}.tex"
    if not f.exists():
        return None
    text, _ = strip_code_fences(read_text(f))
    parts, _ = subjects.parse_reply(text, mode)
    if parts is None:
        return None
    key, _ = subjects.parse_key(parts["key_text"], latex)
    return key


def key_values(key: dict | None) -> str:
    if key is None:
        return ""
    return "; ".join(f"{p['label'] or '-'}={p['value']}{(' ' + p['unit']) if p.get('unit') else ''}"
                     for p in key["parts"] if p["kind"] in ("number", "choice", "truefalse"))


def recheck(cfg: dict, app: sqlite3.Connection, pc: sqlite3.Connection, ids: set[int] | None) -> list[dict]:
    before = {r[0]: r[1] for r in pc.execute(
        "SELECT question_id, value FROM provenance WHERE field='answer_before_replace' ORDER BY id")}
    # pipeline_wrote(pc, qid, "answer", value) for every question at once (provenance has no index).
    wrote = {(r[0], r[1]) for r in pc.execute(
        "SELECT question_id, value FROM provenance WHERE field='answer' AND applied_at IS NOT NULL "
        "AND applied_at NOT LIKE 'skipped%'")}
    rows = pc.execute("SELECT * FROM status WHERE mode IN ('solve', 'aids') AND status='passed' "
                      "AND accepted_attempt IS NOT NULL ORDER BY question_id").fetchall()
    out = []
    for r in rows:
        qid, mode = r["question_id"], r["mode"]
        if ids and qid not in ids:
            continue
        q = fetch_question(app, qid)
        if q is None:
            continue
        rec = {"question_id": qid, "mode": mode, "subject": r["subject"] or "", "reference": "", "detail": ""}
        key = accepted_key(qid, int(r["accepted_attempt"]), mode, q["latexcode"])
        rec["key_values"] = key_values(key)
        if key is None:
            out.append({**rec, "outcome": "no_key"})
            continue
        if qid in before:
            rec["reference"] = before[qid]
            if r["review_from"]:
                out.append({**rec, "outcome": "replaced_by_review"})
                continue
            agree = subjects.earlier_agreement(qid, int(r["accepted_attempt"]), q, mode)
            out.append({**rec, "outcome": "replaced_tiebreak_holds" if agree else "replaced_tiebreak_broken",
                        "detail": f"agrees with attempt {agree}" if agree else "no earlier solve agrees within the judge tolerance"})
            continue
        own = q["answer"] is not None and (qid, q["answer"]) in wrote
        stored = None if is_blank(q["answer"], cfg["empty_answer_sentinels"]) or own else q["answer"]
        rec["reference"] = stored or ""
        ref = subjects.stored_reference(stored)
        if ref is None:
            out.append({**rec, "outcome": "not_comparable" if stored else "no_reference"})
            continue
        why = subjects.reference_mismatch(key, ref)
        out.append({**rec, "outcome": "mismatch" if why else "agrees", "detail": why or ""})
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ids", help="comma-separated question ids (default: every accepted subject reply)")
    a = ap.parse_args()
    ids = {int(x) for x in a.ids.split(",")} if a.ids else None
    cfg = load_config()
    app = app_conn(cfg)
    pc = sqlite3.connect(f"file:{PIPELINE_DB.as_posix()}?mode=ro", uri=True)
    pc.row_factory = sqlite3.Row
    try:
        rows = recheck(cfg, app, pc, ids)
    finally:
        app.close()
        pc.close()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    counts = collections.Counter((r["mode"], r["outcome"]) for r in rows)
    for (mode, outcome), n in sorted(counts.items()):
        print(f"{mode:5} {outcome:26} {n}")
    print(f"report: {REPORT}")


if __name__ == "__main__":
    sys.exit(main())
