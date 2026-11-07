"""Apply queued Answer / Hint fills to the app database.

Fills are queued in pipeline.db (table `provenance`, applied_at NULL) by
assemble.py (and subjects.py, which also fills answer_key and takeaways). They are written to app/data/appdata/amplify.db only when
config.app_db_writes is true (or --force is given), and only into fields that
are still empty at write time. Filled fields are never overwritten, except a
value the pipeline itself wrote earlier: a redo at a higher effort replaces it,
while a value from the source or the owner is never touched.

Usage: python apply_fields.py [--force] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import app_conn, is_blank, load_config, now_iso, pipe_conn, pipeline_wrote  # noqa: E402


def _ensure_schema(app) -> None:
    """Apply the app's own pending migrations (adds the generated_solution
    column, migration 005) exactly as the app does at startup, so the app and
    the pipeline never disagree about the schema."""
    from common import REPO_DIR

    sys.path.insert(0, str(REPO_DIR))
    from app.persistence.db import migrate  # noqa: WPS433

    migrate(app)


def apply_pending(cfg: dict, pc, *, force: bool = False, dry_run: bool = False) -> dict:
    pending = pc.execute("SELECT * FROM provenance WHERE applied_at IS NULL ORDER BY id").fetchall()
    if not pending:
        return {"applied": 0, "skipped_not_empty": 0, "queued": 0}
    if not (cfg.get("app_db_writes") or force):
        return {"applied": 0, "skipped_not_empty": 0, "queued": len(pending), "note": "app_db_writes is false; fills stay queued"}
    app = app_conn(cfg, readonly=False)
    if not dry_run:
        _ensure_schema(app)
    gen_col = cfg.get("generated_solution_column") or "generated_solution"
    applied = skipped = 0
    sentinels = cfg["empty_answer_sentinels"]
    for row in pending:
        field = row["field"]
        if field not in ("answer", "hints", "answer_key", "takeaways", gen_col):
            continue
        cur = app.execute(f"SELECT {field} FROM questions WHERE question_id=?", (row["question_id"],)).fetchone()
        if cur is None:
            continue
        if field == gen_col:
            # Pipeline-owned column: a newer run may replace an older one.
            empty = True
        else:
            empty = (is_blank(cur[0], sentinels if field == "answer" else ())
                     or pipeline_wrote(pc, row["question_id"], field, cur[0], before_id=row["id"]))
        if not empty:
            skipped += 1
            if not dry_run:
                pc.execute("UPDATE provenance SET applied_at=? WHERE id=?", (f"skipped:not-empty:{now_iso()}", row["id"]))
            continue
        if dry_run:
            applied += 1
            continue
        app.execute(f"UPDATE questions SET {field}=? WHERE question_id=?", (row["value"], row["question_id"]))
        pc.execute("UPDATE provenance SET applied_at=? WHERE id=?", (now_iso(), row["id"]))
        if field in ("answer", "hints"):
            col = "answer_filled" if field == "answer" else "hint_filled"
            pc.execute(f"UPDATE finals SET {col}=1 WHERE question_id=?", (row["question_id"],))
        applied += 1
    if not dry_run:
        app.commit()
        pc.commit()
    app.close()
    return {"applied": applied, "skipped_not_empty": skipped, "queued": 0 if not dry_run else len(pending), "dry_run": dry_run}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    cfg = load_config()
    pc = pipe_conn()
    print(json.dumps(apply_pending(cfg, pc, force=a.force, dry_run=a.dry_run)))


if __name__ == "__main__":
    main()
