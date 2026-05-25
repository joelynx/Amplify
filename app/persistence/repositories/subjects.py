"""Repository for the `subjects` table (§3.6).

Subjects are user-defined curricular bundles. The runtime DB starts empty; the
seed bundle does not populate this table.
"""

from __future__ import annotations

import json
import sqlite3

from app.core.models import Subject


def _row_to_subject(row: sqlite3.Row) -> Subject:
    payload = json.loads(row["payload"])
    return Subject(
        name=row["name"],
        topics=list(payload.get("topics") or []),
        excluded_branches=dict(payload.get("excluded_branches") or {}),
        excluded_subtopics=dict(payload.get("excluded_subtopics") or {}),
        description=str(payload.get("description") or ""),
        schema_version=int(payload.get("schema_version") or 1),
        is_active=bool(row["is_active"]),
    )


def list_names(conn: sqlite3.Connection) -> list[str]:
    return [row["name"] for row in conn.execute("SELECT name FROM subjects ORDER BY name")]


def exists(conn: sqlite3.Connection, name: str) -> bool:
    return conn.execute("SELECT 1 FROM subjects WHERE name = ?", (name,)).fetchone() is not None


def rename(conn: sqlite3.Connection, old_name: str, new_name: str) -> None:
    if old_name == new_name:
        return
    cur = conn.execute("UPDATE subjects SET name = ? WHERE name = ?", (new_name, old_name))
    if cur.rowcount == 0:
        raise KeyError(f"no subject named {old_name!r}")
    conn.commit()


def get(conn: sqlite3.Connection, name: str) -> Subject | None:
    row = conn.execute("SELECT name, payload, is_active FROM subjects WHERE name = ?", (name,)).fetchone()
    return _row_to_subject(row) if row else None


def get_active(conn: sqlite3.Connection) -> Subject | None:
    row = conn.execute(
        "SELECT name, payload, is_active FROM subjects WHERE is_active = 1 LIMIT 1"
    ).fetchone()
    return _row_to_subject(row) if row else None


def save(conn: sqlite3.Connection, subject: Subject) -> None:
    conn.execute(
        """
        INSERT INTO subjects (name, payload, is_active) VALUES (?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET payload = excluded.payload
        """,
        (subject.name, json.dumps(subject.to_payload()), int(subject.is_active)),
    )
    conn.commit()


def delete(conn: sqlite3.Connection, name: str) -> None:
    conn.execute("DELETE FROM subjects WHERE name = ?", (name,))
    conn.commit()


def activate(conn: sqlite3.Connection, name: str | None) -> None:
    """Set exactly one subject active, or zero when `name` is None.

    Deactivation precedes activation because of the partial-unique index that
    enforces "at most one active at a time" (see migration 001).
    """
    conn.execute("UPDATE subjects SET is_active = 0 WHERE is_active = 1")
    if name is not None:
        cur = conn.execute("UPDATE subjects SET is_active = 1 WHERE name = ?", (name,))
        if cur.rowcount == 0:
            conn.rollback()
            raise KeyError(f"no subject named {name!r}")
    conn.commit()
