"""Repository for `concept_query_vectors` (migration 010): one precomputed
query vector per concept, for lecture-keyword retrieval (app/core/retrieval.py).
Vectors are raw float32 BLOBs; callers decode them."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable


def get(conn: sqlite3.Connection, query_key: str) -> bytes | None:
    row = conn.execute("SELECT emb FROM concept_query_vectors WHERE query_key = ?", (query_key,)).fetchone()
    return bytes(row[0]) if row else None


def by_label(conn: sqlite3.Connection, kind: str, label: str) -> list[bytes]:
    """Every vector stored for a concept name (a subtopic name can sit under
    more than one branch)."""
    rows = conn.execute(
        "SELECT emb FROM concept_query_vectors WHERE kind = ? AND label = ? ORDER BY query_key", (kind, label)
    )
    return [bytes(r[0]) for r in rows]


def count(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM concept_query_vectors").fetchone()[0])


def replace_all(conn: sqlite3.Connection, rows: Iterable[tuple[str, str, str, bytes, str, str]]) -> int:
    """Replace the whole table with `(query_key, kind, label, emb, emb_model,
    emb_text_hash)` rows, in one transaction. Returns the number written."""
    rows = list(rows)
    try:
        conn.execute("DELETE FROM concept_query_vectors")
        conn.executemany(
            "INSERT INTO concept_query_vectors (query_key, kind, label, emb, emb_model, emb_text_hash) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            rows,
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return len(rows)
