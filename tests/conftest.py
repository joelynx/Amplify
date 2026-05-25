"""Pytest fixtures.

`seeded_conn` builds an in-memory SQLite, runs migrations, and inserts a small
synthetic question set with predictable taxonomy, sources, types, and tags. Used
by tests that need actual rows (selection, repo). Filter-assembly tests don't
need a DB — they assert on the generated WHERE clause directly.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator

import pytest

from app.persistence.db import migrate


@pytest.fixture
def conn() -> Iterator[sqlite3.Connection]:
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    try:
        migrate(c)
        yield c
    finally:
        c.close()


@pytest.fixture
def seeded_conn(conn: sqlite3.Connection) -> sqlite3.Connection:
    """A 6-question synthetic corpus exercising every filter dimension."""
    rows = [
        # qid is auto-assigned; the tuple order matches the INSERT below.
        # (topic, branch, subtopic, type, in_syllabus, source, difficulty, times_used, tags)
        ("Calculus",       "Differential", "Limits",    "proof",     1, "IITD-AD", 3.0, 0, ["induction"]),
        ("Calculus",       "Differential", "Continuity","numerical", 1, "IITK",    5.0, 0, ["induction", "diagram"]),
        ("Calculus",       "Integral",     "Riemann",   "proof",     1, "IITD-AD", 7.0, 1, ["coloring"]),
        ("Linear Algebra", "Eigen",        "Diagonal",  "numerical", 1, "IITD-AD", 4.0, 0, ["diagram"]),
        ("Linear Algebra", "Eigen",        "Spectral",  "numerical", 0, "IITM",    9.0, 0, ["off-syllabus"]),
        ("Linear Algebra", "Bases",        "Orthogonal","explanation", 1, "IITK",  2.0, 0, []),
    ]
    for i, (topic, branch, sub, qtype, in_syll, source, diff, used, tags) in enumerate(rows, start=1):
        latex = f"Q{i}: prove something about {topic}/{branch}/{sub}"
        conn.execute(
            """
            INSERT INTO questions (
                topic, branch, subtopic, latexcode, type, in_syllabus, source,
                difficulty_rating, times_used, latex_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (topic, branch, sub, latex, qtype, in_syll, source, diff, used, f"hash{i}"),
        )
        qid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        for t in tags:
            conn.execute("INSERT INTO question_tags (question_id, tag) VALUES (?, ?)", (qid, t))
    conn.commit()
    return conn
