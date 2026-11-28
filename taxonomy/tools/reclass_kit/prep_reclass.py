"""Route the reclassification (owner 2026-11-25: "Queue a reclassification for all the classifications done on the basis of
question only, or whose solution changed, and do the reclassification strictly after the embedding"; run after the solves)
into full/routed.json: the rows of ../reclass/candidates.json whose embedding is current, each with its solution as the
embedding sees it (the generated solution without its attribution line, else the book's). Candidates: the row's current
subject (its node's, or its last label's when it is Uncategorized), then the subjects its source's placed rows use most
(each at least 3% of them), four at most. Hint: the subsource. A solution longer than CAP characters is cut there
(the method shows early; the median is about 5,300 characters, and uncut the wave would be about 5,200 requests).
usage: python prep_reclass.py (repo root)"""
import collections
import glob
import json
import os
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("AMPLIFY_ROOT") or Path(__file__).resolve().parents[3])  # the repo; set AMPLIFY_ROOT when the kit runs from a copy
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
from app.tools.reembed import best_solution  # noqa: E402

CAP = 3000
WAVE = set(json.loads((HERE / "wave_ids.json").read_text("utf-8")))  # the extra books, parts 2 and 3: rows labelled from the question alone whose solutions passed jobs 20261128-142030 and -145909
cands = [c for c in json.loads((HERE / "candidates.json").read_text("utf-8"))
         if c.get("embedded") and c["kind"] == "question_only" and c["id"] in WAVE]
T = json.loads((ROOT / "taxonomy" / "taxonomy.json").read_text("utf-8"))
node_subject = {(n["topic"], n["branch"], n["subtopic"]): n["subject"] for n in T}
SUBJECTS = {n["subject"] for n in T}
last_label = {}  # Uncategorized rows: the subject of their newest label
for d in sorted(glob.glob(str(ROOT / "taxonomy" / "full_run*")),
                key=lambda d: os.path.getmtime(os.path.join(d, "final_labels.json")) if os.path.exists(os.path.join(d, "final_labels.json")) else 0):
    f = os.path.join(d, "final_labels.json")
    if os.path.exists(f):
        lab = json.load(open(f, encoding="utf-8"))
        for v in (lab.values() if isinstance(lab, dict) else lab):
            if v.get("subject") in SUBJECTS:
                last_label[int(v["id"])] = v["subject"]
conn = sqlite3.connect(f"file:{(ROOT / 'app' / 'data' / 'appdata' / 'amplify.db').as_posix()}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
by_source = collections.defaultdict(collections.Counter)
for r in conn.execute("SELECT source, topic, branch, subtopic FROM questions WHERE subtopic != 'Uncategorized'"):
    s = node_subject.get((r["topic"], r["branch"], r["subtopic"]))
    if s:
        by_source[r["source"]][s] += 1
want = {c["id"] for c in cands}


def cut(s: str) -> str:
    return s if len(s) <= CAP else s[:CAP].rstrip() + "\n[... the solution continues]"


rows, no_subject = [], 0
for r in conn.execute("SELECT question_id, source, subsource, topic, branch, subtopic, latexcode, solution, generated_solution "
                      "FROM questions ORDER BY question_id"):
    q = r["question_id"]
    if q not in want:
        continue
    cur = node_subject.get((r["topic"], r["branch"], r["subtopic"])) or last_label.get(q)
    dist = by_source[r["source"]]
    total = sum(dist.values()) or 1
    common = [s for s, n in dist.most_common() if n / total >= 0.03]
    cand = list(dict.fromkeys(([cur] if cur else []) + common))[:4]
    if not cand:
        no_subject += 1
        continue
    rows.append({"id": q, "src": r["source"], "group": "text", "cand": cand, "hint": r["subsource"] or "",
                 "q": r["latexcode"] or "", "sol": cut(best_solution(r["solution"], r["generated_solution"])),
                 "now": [r["topic"], r["branch"], r["subtopic"]]})
(HERE / "full").mkdir(exist_ok=True)
(HERE / "full" / "routed.json").write_text(json.dumps(rows, ensure_ascii=False), "utf-8")
print(len(rows), "routed of", len(cands), "| no candidate subject:", no_subject)
print("first candidate:", collections.Counter(r["cand"][0] for r in rows).most_common(12))
print("candidates per row:", collections.Counter(len(r["cand"]) for r in rows))
print("with a solution:", sum(1 for r in rows if r["sol"].strip()), "| chars per row (q+sol):",
      sum(len(r["q"]) + len(r["sol"]) for r in rows) // max(1, len(rows)))
