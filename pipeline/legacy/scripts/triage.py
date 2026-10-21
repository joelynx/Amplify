"""Assign a difficulty level (ROUTINE / MODERATE / INSIGHT) to each active question.

Option A (default, `triage_method: heuristic`): the length of the old solution
is the difficulty proxy, with thresholds from config.json. A question with no
old solution is INSIGHT (when unsure, choose the higher level).

Option B (`triage_method: router`): read the level the router subagent wrote
to outputs/<id>/triage.txt (render_prompt.py router + spawn first).

Usage: python triage.py [qid ...]   (default: the current batch)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    active_ids,
    app_conn,
    fetch_question,
    get_status,
    is_blank,
    load_config,
    pipe_conn,
    q_dir,
    read_text,
    upsert_status,
    write_progress,
    write_text,
)

LEVELS = ("ROUTINE", "MODERATE", "INSIGHT")


def heuristic_level(old_solution: str | None, thr: dict) -> str:
    if is_blank(old_solution):
        return "INSIGHT"
    n = len(old_solution)
    r = thr.get("routine_max_chars")
    m = thr.get("moderate_max_chars")
    if r is not None and n <= r:
        return "ROUTINE"
    if m is not None and n <= m:
        return "MODERATE"
    return "INSIGHT"


def main() -> None:
    cfg = load_config()
    app = app_conn(cfg)
    pc = pipe_conn()
    ids = [int(x) for x in sys.argv[1:]] or active_ids()
    out = {}
    for qid in ids:
        q = fetch_question(app, qid)
        row = get_status(pc, qid)
        if q is None or row is None:
            out[qid] = "ERROR: not in batch/database"
            continue
        d = q_dir(qid)
        if cfg.get("triage_method") == "router":
            p = d / "triage.txt"
            level = read_text(p).strip().upper() if p.exists() else ""
            if level not in LEVELS:
                out[qid] = f"ERROR: router output missing/invalid ({level!r})"
                continue
        else:
            level = heuristic_level(q["solution"], cfg["triage_thresholds"])
            write_text(d / "triage.txt", level + "\n")
        fields = {"level": level}
        if row["status"] == "pending":
            fields["status"] = "triaged"
        upsert_status(pc, qid, **fields)
        out[qid] = f"{level} (old solution {len(q['solution'] or '')} chars)"
    write_progress(pc)
    print(json.dumps(out, indent=0))


if __name__ == "__main__":
    main()
