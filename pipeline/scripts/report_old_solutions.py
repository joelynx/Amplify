"""Turn pipeline/reports/old_solutions_check.csv into the owner's answer:
which stored solutions break the app's PDF compile.

Classification of a PDF failure (the app runs one XeLaTeX pass with
-halt-on-error, exactly like the checker):
  hard  - an error that halts XeLaTeX ("! ..." lines, timeouts, non-zero exit):
          the app's PDF generation fails for any set containing the question.
  soft  - the PDF is produced but is wrong somewhere: an undefined \\ref prints
          "??", a character missing from the font is dropped.
Rows whose first recorded error is soft are recompiled here to make sure no
hard error follows it (the CSV keeps only the first error).

Web issues (KaTeX view) are listed separately; most are commands such as
\\vspace that the web view shows as raw text, which is cosmetic.

Usage: python pipeline/scripts/report_old_solutions.py
Writes pipeline/reports/old_solutions_breaks.csv (hard failures, one row each),
       pipeline/reports/old_solutions_report.md (summary by source + counts).
"""

from __future__ import annotations

import csv
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_old_solutions import CSV_PATH, REPORTS_DIR  # noqa: E402
from check_pdf import check_pdf  # noqa: E402
from common import app_conn, load_config  # noqa: E402

BREAKS_CSV = REPORTS_DIR / "old_solutions_breaks.csv"
REPORT_MD = REPORTS_DIR / "old_solutions_report.md"
SOFT = re.compile(r"^(LaTeX Warning: (Reference|Citation) .* undefined|Missing character: There is no)")


def is_hard(err: str) -> bool:
    return bool(err) and not SOFT.match(err)


def error_kind(err: str) -> str:
    e = re.sub(r"l\.\d+.*", "", err)
    e = re.sub(r"line \d+", "line N", e)
    e = re.sub(r"`[^']*'", "`...'", e)
    return e.split("|")[0].strip()[:80] or "(no message)"


def main() -> None:
    rows = list(csv.DictReader(open(CSV_PATH, encoding="utf-8", newline="")))
    cfg = load_config()
    app = app_conn(cfg)

    pdf_fail = [r for r in rows if r["pdf_ok"] != "1"]
    # Recompile the soft-first rows to collect every error.
    recheck = [r for r in pdf_fail if not is_hard(r["error"])]
    full_errors: dict[str, list[str]] = {}
    for r in recheck:
        q = app.execute("SELECT latexcode, solution FROM questions WHERE question_id=?", (int(r["question_id"]),)).fetchone()
        if not q:
            continue
        # a "question" fault only shows up when the question text is included
        res = check_pdf(q[1], question_tex=q[0] if r["pdf_fault"] == "question" else None, cfg=cfg)
        full_errors[r["question_id"]] = res["errors"]

    hard, soft = [], []
    for r in pdf_fail:
        errs = full_errors.get(r["question_id"], [r["error"]])
        hard_errs = [e for e in errs if is_hard(e)]
        if hard_errs:
            r = dict(r, error=hard_errs[0].replace("\r", " ").replace("\n", " | ")[:300])
            hard.append(r)
        else:
            soft.append(r)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(BREAKS_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["question_id", "source", "pdf_fault", "error"])
        w.writeheader()
        for r in sorted(hard, key=lambda r: (r["source"], int(r["question_id"]))):
            w.writerow({k: r[k] for k in ("question_id", "source", "pdf_fault", "error")})

    by_src: dict[str, Counter] = defaultdict(Counter)
    for r in rows:
        by_src[r["source"]]["checked"] += 1
    for r in hard:
        by_src[r["source"]]["hard"] += 1
    for r in soft:
        by_src[r["source"]]["soft"] += 1
    web = [r for r in rows if r["web_ok"] != "1"]
    for r in web:
        by_src[r["source"]]["web"] += 1
    kinds = Counter(error_kind(r["error"]) for r in hard)
    faults = Counter(r["pdf_fault"] for r in hard)
    web_kinds = Counter(error_kind(r["error"]) for r in web if r["pdf_ok"] == "1")

    lines = [
        "# Stored solutions that break the app's PDF compile",
        "",
        f"Generated {time.strftime('%Y-%m-%d %H:%M')} from `{CSV_PATH.name}` ({len(rows)} questions checked, "
        f"{len(by_src)} sources; only questions without a pipeline-generated solution).",
        "",
        f"- **Break the compile (hard):** {len(hard)} questions, listed in `{BREAKS_CSV.name}` "
        f"(fault in the solution: {faults.get('solution', 0)}, in the question text: {faults.get('question', 0)}).",
        f"- **Compile but render wrong (soft):** {len(soft)} questions (undefined `\\ref` printing `??`, or a character missing from the font).",
        f"- **Web view issues (KaTeX):** {len(web)} questions; almost all are commands the web view shows as raw text.",
        "",
        "## Hard failures by error kind",
        "",
        "| Count | Error |",
        "|---|---|",
    ]
    lines += [f"| {n} | `{k}` |" for k, n in kinds.most_common(15)]
    lines += ["", "## By source", "", "| Source | Checked | Hard | Soft | Web |", "|---|---|---|---|---|"]
    for s, c in sorted(by_src.items(), key=lambda kv: (-kv[1]["hard"], -kv[1]["soft"], kv[0])):
        lines.append(f"| {s} | {c['checked']} | {c['hard']} | {c['soft']} | {c['web']} |")
    lines += ["", "## Web view issues by kind (questions whose PDF is fine)", "", "| Count | Issue |", "|---|---|"]
    lines += [f"| {n} | `{k}` |" for k, n in web_kinds.most_common(10)]
    lines += ["", "## Hard failures (first 40)", "", "| Question | Source | Fault | Error |", "|---|---|---|---|"]
    for r in sorted(hard, key=lambda r: (r["source"], int(r["question_id"])))[:40]:
        lines.append(f"| {r['question_id']} | {r['source'][:40]} | {r['pdf_fault']} | `{r['error'][:110]}` |")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print({"checked": len(rows), "hard": len(hard), "soft": len(soft), "web": len(web),
           "breaks_csv": BREAKS_CSV.as_posix(), "report": REPORT_MD.as_posix()})


if __name__ == "__main__":
    main()
