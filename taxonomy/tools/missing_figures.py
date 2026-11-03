"""List questions that cite a figure which is not embedded in the question.

Run from the repo root: python taxonomy/tools/missing_figures.py
Writes taxonomy/data_quality/missing_figures.csv. Read-only on the database.
"""
import csv
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "app" / "data" / "appdata" / "amplify.db"
OUT = ROOT / "taxonomy" / "data_quality" / "missing_figures.csv"

# An explicit figure reference ("Fig. P2.33", "Figure 1.9", "Fig. C11.6") or wording that
# points at a picture ("in the figure", "the figure at right", "as shown").
FIG = re.compile(
    r"\bFig(?:ure|s?\.)\s*~?\(?[A-Z]{0,2}\d+(?:[.\-]\d+)*[a-z]?"
    r"|\b(?:in|from|of) the (?:figure|diagram|sketch|picture)\b"
    r"|\bthe (?:figure|diagram|sketch) (?:below|above|at (?:right|left))"
    r"|\bas shown\b(?!\s+(?:in|by)\s+(?:Prob|Eq|Example|Sec|Chap|Table|Ref))",
    re.I,
)


def main() -> None:
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    rows = []
    for qid, source, topic, branch, subtopic, tex in conn.execute(
        "SELECT question_id, source, topic, branch, subtopic, latexcode FROM questions ORDER BY question_id"
    ):
        if "includegraphics" in tex:
            continue
        m = FIG.search(tex)
        if m:
            rows.append([qid, source, topic, branch, subtopic, m.group(0), " ".join(tex.split())[:160]])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["question_id", "source", "topic", "branch", "subtopic", "reference", "question_start"])
        w.writerows(rows)
    by_source: dict[str, int] = {}
    for r in rows:
        by_source[r[1]] = by_source.get(r[1], 0) + 1
    print(f"{len(rows)} questions cite a figure that is not embedded -> {OUT}")
    for s, n in sorted(by_source.items(), key=lambda x: -x[1]):
        print(f"  {n:5d}  {s}")


if __name__ == "__main__":
    main()
