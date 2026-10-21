"""Web-view check of every stored question text and solution in one go.

Runs the app's real renderer (frontend LatexContent.tsx, bundled by
check_web.mjs) over all rows and reports what would show wrong in the web
view. Nothing is written to the app db. Much faster than check_old_solutions.py
because one node process renders hundreds of texts.

Usage (repo root):
  python pipeline/scripts/check_web_all.py [--limit N] [--out pipeline/reports/web_check.csv] [--chunk 250]
      [--parts solution,question,generated_solution]
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import PIPELINE_DIR, app_conn, load_config  # noqa: E402

CHECK_WEB = PIPELINE_DIR / "scripts" / "check_web.mjs"
REPORTS_DIR = PIPELINE_DIR / "reports"


def run_chunk(files: list[Path]) -> list[dict]:
    proc = subprocess.run(["node", str(CHECK_WEB), *map(str, files)], capture_output=True, text=True, encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(f"check_web.mjs failed: {proc.stderr[-800:]}")
    return json.loads(proc.stdout)


def kind(err: str) -> str:
    e = re.sub(r"raw LaTeX would show as text in the web view: ", "raw: ", err)
    return e[:60]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--chunk", type=int, default=250)
    ap.add_argument("--parts", default="solution,question")
    ap.add_argument("--out", default=str(REPORTS_DIR / "web_check.csv"))
    ap.add_argument("--only-failed", help="re-check only the question ids that have ok=0 in this earlier web_check CSV")
    a = ap.parse_args()
    parts = [p.strip() for p in a.parts.split(",") if p.strip()]
    cfg = load_config()
    app = app_conn(cfg)
    rows = app.execute("SELECT question_id, source, latexcode, solution, generated_solution FROM questions ORDER BY question_id").fetchall()
    app.close()
    if a.only_failed:
        with open(a.only_failed, encoding="utf-8", newline="") as f:
            failed = {int(r["question_id"]) for r in csv.DictReader(f) if r["ok"] == "0"}
        rows = [r for r in rows if r[0] in failed]
    if a.limit:
        rows = rows[: a.limit]
    t0 = time.time()
    results: dict[tuple[int, str], dict] = {}
    with tempfile.TemporaryDirectory(prefix="amp_weball_") as td:
        tdir = Path(td)
        items: list[tuple[int, str, Path]] = []
        for qid, src, q, sol, gen in rows:
            texts = {"solution": sol, "question": q, "generated_solution": gen}
            for part in parts:
                txt = texts.get(part)
                if txt and txt.strip():
                    p = tdir / f"{qid}_{part}.tex"
                    p.write_text(txt, encoding="utf-8")
                    items.append((qid, part, p))
        print(json.dumps({"rows": len(rows), "texts": len(items), "chunk": a.chunk}), flush=True)
        for i in range(0, len(items), a.chunk):
            chunk = items[i:i + a.chunk]
            res = run_chunk([p for _, _, p in chunk])
            for (qid, part, _), r in zip(chunk, res):
                results[(qid, part)] = r
            if (i // a.chunk) % 10 == 0:
                print(json.dumps({"done": min(i + a.chunk, len(items)), "of": len(items), "elapsed_s": int(time.time() - t0)}), flush=True)
    src_of = {r[0]: r[1] for r in rows}
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = Path(a.out)
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["question_id", "source", "part", "ok", "error"])
        for (qid, part), r in sorted(results.items()):
            w.writerow([qid, src_of.get(qid, ""), part, int(r["ok"]), " | ".join(r["errors"])[:400]])
    bad = {k: r for k, r in results.items() if not r["ok"]}
    by_part = Counter(part for (_, part) in bad)
    kinds = Counter(kind(e) for r in bad.values() for e in r["errors"])
    summary = {"texts": len(results), "with_issues": len(bad), "by_part": dict(by_part),
               "questions_with_any_issue": len({q for (q, _) in bad}), "elapsed_s": int(time.time() - t0),
               "top_kinds": kinds.most_common(20), "csv": out.as_posix()}
    print(json.dumps(summary, indent=1, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
