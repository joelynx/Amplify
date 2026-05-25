"""Repository for the `questions` table (§3.1) and the related dropdown helpers.

Every method returns `core/models.Question` (or primitives) — never raw rows.
Embedding BLOBs are intentionally not projected here; similarity search reads
them via its own dedicated path.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from app.core.filters import assemble_where
from app.core.models import Question, Subject

# Columns we project for the dataclass. `classification_emb` / `similarity_emb`
# are deliberately omitted — see module docstring.
_QUESTION_COLS = (
    "question_id, semester, topic, branch, subtopic, latexcode, type, in_syllabus, "
    "source, subsource, answer, solution, solution_outline, hints, instructions, "
    "date_last_accessed, times_used, interactive_times_used, difficulty_rating, latex_hash"
)


def _row_to_question(row: sqlite3.Row, tags: list[str] | None = None) -> Question:
    return Question(
        question_id=row["question_id"],
        semester=row["semester"],
        topic=row["topic"],
        branch=row["branch"],
        subtopic=row["subtopic"],
        latexcode=row["latexcode"],
        type=row["type"],
        in_syllabus=row["in_syllabus"],
        source=row["source"],
        subsource=row["subsource"],
        answer=row["answer"],
        solution=row["solution"],
        solution_outline=row["solution_outline"],
        hints=row["hints"],
        instructions=row["instructions"],
        date_last_accessed=row["date_last_accessed"],
        times_used=row["times_used"],
        interactive_times_used=row["interactive_times_used"],
        difficulty_rating=row["difficulty_rating"],
        latex_hash=row["latex_hash"],
        tags=list(tags or []),
    )


def _tag_map(conn: sqlite3.Connection, question_ids: list[int]) -> dict[int, list[str]]:
    if not question_ids:
        return {}
    placeholders = ",".join(["?"] * len(question_ids))
    rows = conn.execute(
        f"SELECT question_id, tag FROM question_tags WHERE question_id IN ({placeholders})",
        question_ids,
    )
    out: dict[int, list[str]] = {}
    for r in rows:
        out.setdefault(r["question_id"], []).append(r["tag"])
    return out


def get_by_id(conn: sqlite3.Connection, question_id: int) -> Question | None:
    row = conn.execute(
        f"SELECT {_QUESTION_COLS} FROM questions WHERE question_id = ?", (question_id,)
    ).fetchone()
    if row is None:
        return None
    return _row_to_question(row, _tag_map(conn, [question_id]).get(question_id, []))


def count_matching(
    conn: sqlite3.Connection,
    filters: dict[str, Any] | None,
    subject: Subject | None = None,
) -> int:
    payload = subject.to_payload() if subject else None
    where, params = assemble_where(filters, payload)
    sql = f"SELECT COUNT(*) FROM questions WHERE {where}"
    return int(conn.execute(sql, params).fetchone()[0])


def get_random(
    conn: sqlite3.Connection,
    filters: dict[str, Any] | None,
    n: int,
    subject: Subject | None = None,
) -> list[Question]:
    payload = subject.to_payload() if subject else None
    where, params = assemble_where(filters, payload)
    sql = f"SELECT {_QUESTION_COLS} FROM questions WHERE {where} ORDER BY RANDOM() LIMIT ?"
    rows = list(conn.execute(sql, [*params, int(n)]))
    tags = _tag_map(conn, [r["question_id"] for r in rows])
    return [_row_to_question(r, tags.get(r["question_id"], [])) for r in rows]


# ---- Dropdown helpers (spec §5.1) ----------------------------------------

def _scoped_where(subject: Subject | None, in_syllabus_only: bool) -> tuple[str, list[Any]]:
    """A trimmed version of assemble_where for the dropdown queries — only the
    subject curricular gate and the in-syllabus flag, no tree/tags/etc."""
    payload = subject.to_payload() if subject else None
    pseudo: dict[str, Any] = {"in_syllabus_only": in_syllabus_only, "reuse_questions": True}
    where, params = assemble_where(pseudo, payload)
    return where, params


def distinct_topics(conn: sqlite3.Connection, subject: Subject | None, in_syllabus_only: bool) -> list[str]:
    where, params = _scoped_where(subject, in_syllabus_only)
    sql = f"SELECT DISTINCT topic FROM questions WHERE {where} ORDER BY topic"
    return [row[0] for row in conn.execute(sql, params)]


def distinct_branches(
    conn: sqlite3.Connection,
    subject: Subject | None,
    topic: str,
    in_syllabus_only: bool,
) -> list[str]:
    where, params = _scoped_where(subject, in_syllabus_only)
    sql = f"SELECT DISTINCT branch FROM questions WHERE {where} AND topic = ? ORDER BY branch"
    return [row[0] for row in conn.execute(sql, [*params, topic])]


def distinct_subtopics(
    conn: sqlite3.Connection,
    subject: Subject | None,
    topic: str,
    branch: str,
    in_syllabus_only: bool,
) -> list[str]:
    where, params = _scoped_where(subject, in_syllabus_only)
    sql = (
        f"SELECT DISTINCT subtopic FROM questions WHERE {where} "
        "AND topic = ? AND branch = ? ORDER BY subtopic"
    )
    return [row[0] for row in conn.execute(sql, [*params, topic, branch])]


def concept_tree(
    conn: sqlite3.Connection, subject: Subject | None, in_syllabus_only: bool
) -> dict[str, dict[str, list[str]]]:
    """Nested {topic: {branch: [subtopic, …]}} for the CheckableTree widget."""
    where, params = _scoped_where(subject, in_syllabus_only)
    sql = (
        f"SELECT DISTINCT topic, branch, subtopic FROM questions WHERE {where} "
        "ORDER BY topic, branch, subtopic"
    )
    tree: dict[str, dict[str, list[str]]] = {}
    for topic, branch, subtopic in conn.execute(sql, params):
        tree.setdefault(topic, {}).setdefault(branch, []).append(subtopic)
    return tree


def distinct_types(
    conn: sqlite3.Connection,
    filters: dict[str, Any] | None = None,
    subject: Subject | None = None,
) -> list[str]:
    """Distinct `type` values that still yield ≥1 match under `filters` (spec §7.3).

    When `filters` is None and no subject, returns every distinct type in the
    DB. Callers (Api.get_types) strip the `types` key from `filters` before
    passing so the dropdown shows "what types are still reachable" rather than
    just the currently-selected types."""
    if filters is None and subject is None:
        return [
            row[0]
            for row in conn.execute(
                "SELECT DISTINCT type FROM questions WHERE type IS NOT NULL ORDER BY type"
            )
        ]
    payload = subject.to_payload() if subject else None
    where, params = assemble_where(filters, payload)
    return [
        row[0]
        for row in conn.execute(
            f"SELECT DISTINCT type FROM questions WHERE {where} AND type IS NOT NULL ORDER BY type",
            params,
        )
    ]


def distinct_sources(
    conn: sqlite3.Connection,
    filters: dict[str, Any] | None = None,
    subject: Subject | None = None,
) -> list[str]:
    """Distinct `source` values that still yield ≥1 match under `filters` (spec §7.3)."""
    if filters is None and subject is None:
        return [
            row[0]
            for row in conn.execute(
                "SELECT DISTINCT source FROM questions WHERE source IS NOT NULL ORDER BY source"
            )
        ]
    payload = subject.to_payload() if subject else None
    where, params = assemble_where(filters, payload)
    return [
        row[0]
        for row in conn.execute(
            f"SELECT DISTINCT source FROM questions WHERE {where} AND source IS NOT NULL ORDER BY source",
            params,
        )
    ]


def all_tags(
    conn: sqlite3.Connection,
    filters: dict[str, Any] | None = None,
    subject: Subject | None = None,
) -> list[str]:
    """Tags that appear on at least one question matching `filters`. Powers the
    dynamic tag dropdown from spec §7.3.

    When `filters` is None, returns every distinct tag in the DB.
    """
    if filters is None and subject is None:
        return [row[0] for row in conn.execute("SELECT DISTINCT tag FROM question_tags ORDER BY tag")]
    payload = subject.to_payload() if subject else None
    where, params = assemble_where(filters, payload)
    sql = (
        f"SELECT DISTINCT qt.tag FROM question_tags qt "
        f"JOIN questions ON questions.question_id = qt.question_id "
        f"WHERE {where} ORDER BY qt.tag"
    )
    return [row[0] for row in conn.execute(sql, params)]


def mark_used(conn: sqlite3.Connection, question_ids: list[int]) -> None:
    """Bump `times_used` and stamp `date_last_accessed` for the listed ids.

    Called by `pdfgen.assemble` after a successful PDF compile (Step 5). Lives
    here to keep all write paths in one repo.
    """
    if not question_ids:
        return
    placeholders = ",".join(["?"] * len(question_ids))
    conn.execute(
        f"UPDATE questions SET times_used = times_used + 1, "
        f"date_last_accessed = datetime('now') "
        f"WHERE question_id IN ({placeholders})",
        question_ids,
    )
    conn.commit()
