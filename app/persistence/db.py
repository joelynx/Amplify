"""SQLite connection manager and forward-only migrator.

Spec §3.8: schema changes ship as numbered SQL files in `migrations/`; the
`migrations` table records which ones have run, making `migrate()` idempotent.
"""

from __future__ import annotations

import logging
import re
import sqlite3
from pathlib import Path
from typing import Final

log = logging.getLogger("amplify.db")

_MIGRATIONS_DIR: Final[Path] = Path(__file__).resolve().parent / "migrations"
_MIGRATION_NAME_RE: Final = re.compile(r"^(\d{3,})_[a-z0-9_]+\.sql$", re.IGNORECASE)


def connect(db_path: Path) -> sqlite3.Connection:
    """Open a SQLite connection with FK enforcement and a Row factory."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def _ensure_migrations_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS migrations (
            id         TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.commit()


def _applied_ids(conn: sqlite3.Connection) -> set[str]:
    return {row["id"] for row in conn.execute("SELECT id FROM migrations")}


def _discover_migrations() -> list[Path]:
    if not _MIGRATIONS_DIR.exists():
        return []
    return sorted(
        p for p in _MIGRATIONS_DIR.iterdir() if p.is_file() and _MIGRATION_NAME_RE.match(p.name)
    )


def migrate(conn: sqlite3.Connection) -> list[str]:
    """Apply all un-applied migrations in numeric order. Returns ids applied this call."""
    _ensure_migrations_table(conn)
    applied = _applied_ids(conn)
    just_applied: list[str] = []
    for path in _discover_migrations():
        mid = path.stem  # e.g. "001_initial"
        if mid in applied:
            continue
        sql = path.read_text(encoding="utf-8")
        log.info("applying migration %s", mid)
        try:
            conn.executescript(sql)
            conn.execute("INSERT INTO migrations (id) VALUES (?)", (mid,))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        just_applied.append(mid)
    if just_applied:
        log.info("applied %d migration(s): %s", len(just_applied), just_applied)
    return just_applied
