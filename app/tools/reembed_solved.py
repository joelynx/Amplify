"""Re-embed only rows that have a solution (owner: "ONLY ON THE ROWS WITH BOTH A QUESTION AND SOLUTION"):
reembed.plan() filtered to items whose text has a Solution part, then reembed.run_batch (image rows go by sync).
usage: python -m app.tools.reembed_solved [--apply]   (repo root; without --apply: what would be embedded)"""
import collections
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
from app.tools import reembed as R  # noqa: E402

conn = R.connect()
R.ensure_schema(conn)
pending, backfilled = R.plan(conn)
keep = [it for it in pending if "\n\nSolution:\n" in it["text"]]
# --limit N: only the first N text rows (owner 2026-11-25 10:08: $0.24 of credit left, "run as many as possible";
# image rows go by sync at the full price, so they wait for the reload)
LIMIT = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
if LIMIT is not None:
    keep = [it for it in keep if not it["images"]][:LIMIT]
tokens = sum(len(it["text"]) for it in keep) / 3.5
print(f"back-filled {backfilled} | pending {len(pending)}, with a solution {len(keep)} "
      f"({sum(1 for it in keep if it['images'])} with images) | ~{tokens / 1e6:.1f}M tokens ~ "
      f"{tokens / 1e6 * R.PRICE_PER_MTOK / 2:.2f} USD batch", flush=True)
src = dict(conn.execute("SELECT question_id, source FROM questions").fetchall())
print(collections.Counter(src.get(it["qid"]) for it in keep).most_common(12), flush=True)
if "--apply" not in sys.argv or not keep:
    sys.exit(0)
RESUME = "--resume" in sys.argv  # collect the jobs in reembed_jobs.json first (already paid for)
if not RESUME:
    dst = str(R.DB_PATH) + ".bak-" + time.strftime("%Y%m%d-%H%M%S") + "-pre-reembed"
    b = sqlite3.connect(dst)
    conn.backup(b)
    b.close()
    print("backup=" + dst, flush=True)
client = R.get_client()
t0 = time.time()
done = R.run_batch(conn, client, keep, 250, RESUME)
R.set_model_config(conn)
print(f"done: {done}/{len(keep)} in {int((time.time() - t0) / 60)} min", flush=True)
