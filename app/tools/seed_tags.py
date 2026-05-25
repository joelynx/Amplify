"""CLI: `python -m app.tools.seed_tags`.

Idempotent — re-running only inserts tags for new questions / new metadata.
"""

from __future__ import annotations

from app.logging_setup import setup_logging
from app.main import _open_db
from app.persistence.ingest.seed_tags import run


def main() -> int:
    setup_logging()
    conn = _open_db()
    try:
        result = run(conn)
    finally:
        conn.close()
    print(f"scanned={result.questions_scanned} inserted={result.rows_inserted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
