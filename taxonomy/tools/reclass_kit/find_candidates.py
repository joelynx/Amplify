"""Rows to reclassify (owner 2026-11-25): labelled from the question alone, or whose solution changed since the label.
Label time: the newest taxonomy/full_run*/final_labels.json that lists the row (file time, or the known apply time
where git rewrote the file). What the classifier saw then: the generated solution in effect at that time (the
newest generated_solution provenance value at or before it), else the book solution (a fix applied after the
label counts as a change). A row is a candidate when it has a solution now and
  question_only: neither a generated nor a book solution existed at its label time, or
  changed: the generated solution at its label time differs from the current one, or its book solution was fixed.
Also reports whether its embedding is current (the reclassification runs only after it).
usage: python find_candidates.py  (repo root) -> reclass/candidates.json + a summary"""
import collections
import glob
import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, os.getcwd())
sys.stdout.reconfigure(encoding="utf-8")
from app.tools import reembed as R  # noqa: E402

# label files that git rewrote (pull --rebase 2026-11-25 09:18): the time the chain applied them
APPLIED = {"full_run_20261125_wave7b": "2026-11-25T03:41:00", "full_run_20261125_wave8": "2026-11-25T04:49:00",
           "full_run_20261125_wave9": "2026-11-25T08:46:16"}
label_at, label_run = {}, {}
for d in sorted(glob.glob("taxonomy/full_run*")):
    f = os.path.join(d, "final_labels.json")
    if not os.path.exists(f):
        continue
    name = os.path.basename(d)
    t = datetime.fromisoformat(APPLIED[name]).timestamp() if name in APPLIED else os.path.getmtime(f)
    lab = json.load(open(f, encoding="utf-8"))
    for v in (lab.values() if isinstance(lab, dict) else lab):
        q = int(v["id"])
        if t >= label_at.get(q, 0):
            label_at[q], label_run[q] = t, name

norm = lambda s: " ".join((s or "").split())
p = sqlite3.connect("file:pipeline/pipeline.db?mode=ro", uri=True)
gen_hist = collections.defaultdict(list)  # qid -> [(time, value)]
for q, ts, val in p.execute("SELECT question_id, coalesce(applied_at, created_at), value FROM provenance "
                            "WHERE field='generated_solution' ORDER BY id"):
    gen_hist[q].append((datetime.fromisoformat(ts).timestamp(), val))
fixed_at = {q: datetime.fromisoformat(ts).timestamp() for q, ts in p.execute(
    "SELECT question_id, max(applied_at) FROM solution_fixes WHERE applied_at IS NOT NULL AND reverted_at IS NULL GROUP BY question_id")}

a = sqlite3.connect("file:app/data/appdata/amplify.db?mode=ro", uri=True)
a.row_factory = sqlite3.Row
out, kinds, by_run, by_src = [], collections.Counter(), collections.Counter(), collections.Counter()
no_label = 0
for r in a.execute(R.ROW_SQL.replace("FROM questions", ", source, subject_of_row FROM questions").replace(", subject_of_row", "")):
    q = r["question_id"]
    gen_now, book = (r["generated_solution"] or "").strip(), (r["solution"] or "").strip()
    if not (gen_now or book):
        continue
    if q not in label_at:
        no_label += 1
        continue
    t = label_at[q]
    seen = [v for ts, v in gen_hist.get(q, []) if ts <= t]
    gen_then = seen[-1] if seen else None
    if gen_then is None and not book:
        kind = "question_only"
    elif gen_then is not None and norm(gen_then) != norm(gen_now):
        kind = "generated_changed"
    elif gen_then is None and gen_now:
        kind = "book_then_generated_added"  # the classifier saw the book solution; a generated one came later
    elif fixed_at.get(q, 0) > t:
        kind = "book_fixed"
    else:
        continue
    kinds[kind] += 1
    if kind == "book_then_generated_added":
        continue  # not queued: the label already rests on a full solution
    embedded = R.build_item(r)["hash"] == r["emb_text_hash"]
    out.append({"id": q, "kind": kind, "run": label_run[q], "source": r["source"], "embedded": embedded})
    by_run[(label_run[q], kind)] += 1
    by_src[r["source"]] += 1
(HERE / "candidates.json").write_text(json.dumps(out), "utf-8")
print("kinds:", dict(kinds))
print("queued:", len(out), "| embedding current:", sum(x["embedded"] for x in out))
for k, v in sorted(by_run.items()):
    print("  ", k, v)
print("top sources:", by_src.most_common(12))
print("rows with a solution in no full_run:", no_label)
