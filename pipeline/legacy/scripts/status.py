"""Session-start summary: where the run stands and what comes next.

Usage: python status.py [--batch-detail]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    RUN_LOG,
    app_conn,
    current_batch,
    get_status,
    is_done,
    load_config,
    pipe_conn,
    target_question_ids,
    write_progress,
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch-detail", action="store_true")
    a = ap.parse_args()
    cfg = load_config()
    app = app_conn(cfg)
    pc = pipe_conn()
    total = len(target_question_ids(app, cfg))
    rows = list(pc.execute("SELECT * FROM status"))
    done = sum(1 for r in rows if is_done(r))
    prog = write_progress(pc)
    pending_fills = pc.execute("SELECT COUNT(*) FROM provenance WHERE applied_at IS NULL").fetchone()[0]
    print(f"prompt_version {cfg['prompt_version']} | app_db_writes {cfg['app_db_writes']} | queued field fills {pending_fills}")
    print(f"target questions {total} | done {done} | in status table {len(rows)}")
    print("counts by status:", json.dumps(prog["counts_by_status"]))
    print("models:", json.dumps({"solver": cfg["solver"], "reviewer": cfg["reviewer"], "hint": cfg["hint"]}))
    b = current_batch()
    if b:
        print(f"current batch {b['batch']} ({b['kind']}): {len(b['ids'])} ids, {len(b['active'])} active, dropped {b.get('dropped', {})}")
        if a.batch_detail:
            for q in b["ids"]:
                r = get_status(pc, q)
                print(f"  {q}: {r['status'] if r else '?'} level={r['level'] if r else '?'} attempts={r['attempts'] if r else '?'} hint={r['hint_status'] if r else '?'} assembled={r['assembled'] if r else '?'} note={(r['note'] or '')[:80] if r else ''}")
    if RUN_LOG.exists():
        lines = [l for l in RUN_LOG.read_text(encoding="utf-8").splitlines() if l.startswith("|")]
        print("last run_log lines:")
        for l in lines[-5:]:
            print("  " + l)


if __name__ == "__main__":
    main()
