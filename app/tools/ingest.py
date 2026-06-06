"""CLI: `python -m app.tools.ingest`.

Runs migrations against the appdata SQLite, then ingests the seed CSV +
LanceDB embeddings into it. Idempotent — safe to re-run.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from app.logging_setup import appdata_dir, setup_logging
from app.persistence.db import connect, migrate
from app.persistence.ingest.seed import ingest

log = logging.getLogger("amplify.tools.ingest")

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_CSV = _REPO_ROOT / "Files" / "TEST.csv"
_DEFAULT_LANCEDB = _REPO_ROOT / "Files" / "Testing" / "lancedb"
_DEFAULT_OUTLINES = _REPO_ROOT / "app" / "data" / "seed" / "pre_db.outlines.json"
_DEFAULT_TOPIC_DEPTH = _REPO_ROOT / "app" / "data" / "seed" / "pre_db.topic_depth.json"


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="amplify-ingest", description=__doc__)
    p.add_argument("--csv", type=Path, default=_DEFAULT_CSV, help="Seed CSV path")
    p.add_argument("--lancedb", type=Path, default=_DEFAULT_LANCEDB, help="LanceDB directory for embeddings")
    p.add_argument(
        "--outlines",
        type=Path,
        default=_DEFAULT_OUTLINES,
        help="solution_outline JSON ({question_id: outline}); optional, no-op if missing",
    )
    p.add_argument(
        "--topic-depth",
        type=Path,
        default=_DEFAULT_TOPIC_DEPTH,
        help="topic→depth JSON; optional, stored verbatim into configs.TOPIC_DEPTH_MAP",
    )
    p.add_argument(
        "--db",
        type=Path,
        default=None,
        help="SQLite DB path (defaults to app/data/appdata/amplify.db)",
    )
    p.add_argument(
        "--images-dir",
        type=Path,
        default=None,
        help="Directory of image files to copy into teximages/ (e.g. Files/images)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    setup_logging()

    db_path = args.db or (appdata_dir() / "amplify.db")
    log.info("opening db at %s", db_path)

    conn = connect(db_path)
    try:
        migrate(conn)
        result = ingest(
            conn,
            csv_path=args.csv,
            lancedb_path=args.lancedb,
            outlines_json=args.outlines,
            topic_depth_json=args.topic_depth,
            images_source_dir=args.images_dir,
        )
    finally:
        conn.close()

    print(
        f"imported={result.imported} skipped={result.skipped} "
        f"embeddings_loaded={result.embeddings_loaded} outlines_loaded={result.outlines_loaded}"
    )
    if result.warnings:
        print(f"\nWarnings ({len(result.warnings)}):")
        for w in result.warnings:
            print(f"  [WARNING]  {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
