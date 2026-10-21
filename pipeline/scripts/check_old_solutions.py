"""Check that the solutions already stored in the app (questions.solution)
compile the way the app compiles them, for every question that has no valid
pipeline-generated solution.

Owner request (2026-10-20): "verify even the solutions already stored in the
application, for which solutions were not generated with our script (ignore old
solutions where valid solutions we generated now exist). Some of them break
compilation, and I need to figure out which ones."

For each question in scope:
  1. XeLaTeX: compile the solution the way the app's interleaved mode does
     (question text + solution, app preamble, app image folder). If that fails,
     compile the solution alone to tell a broken question text from a broken
     solution.
  2. Web: run the KaTeX/markdown renderer check on the solution and on the
     question text.

Usage (from the repo root; no API key needed, nothing is written to the app db):
  python pipeline/scripts/check_old_solutions.py [--workers 2] [--limit N] [--ids 1,2,3] [--dry-run]
  python pipeline/scripts/check_old_solutions.py --summary        # recompute the summary from the CSV

Output (resumable: rows already in the CSV are skipped on rerun):
  pipeline/reports/old_solutions_check.csv
  pipeline/reports/old_solutions_summary.json
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import tempfile
import threading
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_pdf import check_pdf  # noqa: E402
from common import PIPELINE_DIR, app_conn, check_web_parts, load_config, pipe_conn  # noqa: E402

REPORTS_DIR = PIPELINE_DIR / "reports"
CSV_PATH = REPORTS_DIR / "old_solutions_check.csv"
SUMMARY_PATH = REPORTS_DIR / "old_solutions_summary.json"
FIELDS = ["question_id", "source", "pdf_ok", "pdf_fault", "web_ok", "web_fault", "error", "checked_at"]


def in_scope(cfg: dict, ids: list[int] | None = None) -> list[dict]:
    """Questions with an old solution and no valid generated one. A question the
    pipeline marked `passed` is excluded even if the app-db write is still
    queued (apply_pending runs at the end of a judge round)."""
    app = app_conn(cfg)
    pc = pipe_conn()
    passed = {r[0] for r in pc.execute("SELECT question_id FROM status WHERE status='passed'")}
    pc.close()
    col = cfg.get("generated_solution_column") or "generated_solution"
    rows = app.execute(
        f"SELECT question_id, source, latexcode, solution FROM questions "
        f"WHERE solution IS NOT NULL AND TRIM(solution) <> '' "
        f"AND ({col} IS NULL OR TRIM({col}) = '') ORDER BY question_id"
    ).fetchall()
    app.close()
    want = set(ids) if ids else None
    out = []
    for qid, src, q, sol in rows:
        if qid in passed:
            continue
        if want is not None and qid not in want:
            continue
        out.append({"question_id": qid, "source": src, "question": q or "", "solution": sol})
    return out


def already_checked() -> set[int]:
    if not CSV_PATH.exists():
        return set()
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        return {int(r["question_id"]) for r in csv.DictReader(f) if r.get("question_id")}


def _first(errs: list[str]) -> str:
    return (errs[0] if errs else "").replace("\r", " ").replace("\n", " | ")[:300]


def check_one(row: dict, cfg: dict) -> dict:
    qid, sol, q = row["question_id"], row["solution"], row["question"]
    pdf_fault, error = "", ""
    r = check_pdf(sol, question_tex=q or None, cfg=cfg)
    pdf_ok = r["ok"]
    if not pdf_ok:
        error = _first(r["errors"])
        if q:
            alone = check_pdf(sol, cfg=cfg)
            pdf_fault = "solution" if not alone["ok"] else "question"
            if not alone["ok"]:
                error = _first(alone["errors"])
        else:
            pdf_fault = "solution"
    with tempfile.TemporaryDirectory(prefix="amp_oldweb_") as td:
        w = check_web_parts({"solution": sol, "question": q}, Path(td))
    web_ok = w["ok"]
    web_fault = ""
    if not web_ok:
        kinds = {e.split("]")[0].lstrip("[") for e in w["errors"] if e.startswith("[")}
        web_fault = "+".join(sorted(kinds)) or "solution"
        if not error:
            error = _first(w["errors"])
    return {
        "question_id": qid, "source": row["source"], "pdf_ok": int(pdf_ok), "pdf_fault": pdf_fault,
        "web_ok": int(web_ok), "web_fault": web_fault, "error": error,
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


def summarize() -> dict:
    per: dict[str, Counter] = defaultdict(Counter)
    tot: Counter = Counter()
    if CSV_PATH.exists():
        with open(CSV_PATH, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                c = per[r["source"]]
                c["checked"] += 1
                if r["pdf_ok"] != "1":
                    c["pdf_fail"] += 1
                    c[f"pdf_fault_{r['pdf_fault'] or 'unknown'}"] += 1
                if r["web_ok"] != "1":
                    c["web_fail"] += 1
                if r["pdf_ok"] != "1" or r["web_ok"] != "1":
                    c["any_fail"] += 1
    for c in per.values():
        tot.update(c)
    out = {
        "csv": CSV_PATH.as_posix(),
        "totals": dict(tot),
        "by_source": {s: dict(c) for s, c in sorted(per.items(), key=lambda kv: -kv[1]["any_fail"])},
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--ids")
    ap.add_argument("--dry-run", action="store_true", help="only count what is in scope; no compiles")
    ap.add_argument("--summary", action="store_true", help="recompute the summary from the CSV and exit")
    a = ap.parse_args()
    if a.summary:
        print(json.dumps(summarize()["totals"]))
        return

    cfg = load_config()
    ids = [int(x) for x in a.ids.split(",") if x.strip()] if a.ids else None
    rows = in_scope(cfg, ids)
    done = already_checked()
    todo = [r for r in rows if r["question_id"] not in done]
    if a.limit:
        todo = todo[: a.limit]
    print(json.dumps({"in_scope": len(rows), "already_checked": len(done), "to_check": len(todo),
                      "sources": len({r["source"] for r in rows}), "workers": a.workers}), flush=True)
    if a.dry_run or not todo:
        return

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    new_file = not CSV_PATH.exists()
    lock = threading.Lock()
    counts: Counter = Counter()
    t0 = time.time()
    with open(CSV_PATH, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            w.writeheader()
            f.flush()
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            futs = {ex.submit(check_one, r, cfg): r["question_id"] for r in todo}
            for i, fut in enumerate(as_completed(futs), 1):
                qid = futs[fut]
                try:
                    rec = fut.result()
                except Exception as e:  # keep going; the row is marked as a checker crash
                    rec = {"question_id": qid, "source": "", "pdf_ok": 0, "pdf_fault": "checker_crashed",
                           "web_ok": 0, "web_fault": "checker_crashed", "error": str(e)[:300],
                           "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
                with lock:
                    w.writerow(rec)
                    f.flush()
                counts["checked"] += 1
                counts["pdf_fail"] += 0 if rec["pdf_ok"] else 1
                counts["web_fail"] += 0 if rec["web_ok"] else 1
                if i % 100 == 0 or i == len(todo):
                    print(json.dumps({"checked": i, "of": len(todo), "elapsed_s": int(time.time() - t0), **counts}), flush=True)
    print(json.dumps(summarize()["totals"]), flush=True)


if __name__ == "__main__":
    main()
