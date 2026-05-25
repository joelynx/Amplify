"""Repository for the `configs` key/value store (§3.7).

Values are JSON-encoded on write and decoded on read so callers can pass any
JSON-able Python value without re-stringifying.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any


def get(conn: sqlite3.Connection, key: str, default: Any = None) -> Any:
    row = conn.execute("SELECT value FROM configs WHERE key = ?", (key,)).fetchone()
    if row is None:
        return default
    return json.loads(row[0])


def set_(conn: sqlite3.Connection, key: str, value: Any) -> None:
    conn.execute(
        """
        INSERT INTO configs (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (key, json.dumps(value)),
    )
    conn.commit()


def all_(conn: sqlite3.Connection) -> dict[str, Any]:
    return {row["key"]: json.loads(row["value"]) for row in conn.execute("SELECT key, value FROM configs")}
