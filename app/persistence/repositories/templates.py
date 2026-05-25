"""Repository for the `templates` table (§3.3).

A template is a saved JSON snapshot of the Generate form. Storage shape mirrors
spec §3.3 — typed columns + JSON-encoded list/dict fields. Names are the PK.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from app.core.models import Template


def _row_to_template(row: sqlite3.Row) -> Template:
    return Template(
        name=row["name"],
        subject=row["subject"],
        topic_list=json.loads(row["topic_list"] or "[]"),
        branch_list=json.loads(row["branch_list"] or "[]"),
        subtopic_list=json.loads(row["subtopic_list"] or "[]"),
        type_list=json.loads(row["type_list"] or "[]"),
        source_list=json.loads(row["source_list"] or "[]"),
        tag_list=json.loads(row["tag_list"] or '{"compulsory": [], "optional": [], "excluded": []}'),
        n_questions=int(row["n_questions"]),
        reuse_questions=int(row["reuse_questions"]),
        include_sources=int(row["include_sources"]),
        in_syllabus_only=int(row["in_syllabus_only"]),
        min_difficulty=row["min_difficulty"],
        save_directory=row["save_directory"],
        solutions=row["solutions"],
    )


def list_names(conn: sqlite3.Connection) -> list[str]:
    return [row[0] for row in conn.execute("SELECT name FROM templates ORDER BY name")]


def exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute("SELECT 1 FROM templates WHERE name = ?", (name,)).fetchone()
    return row is not None


def get(conn: sqlite3.Connection, name: str) -> Template | None:
    row = conn.execute("SELECT * FROM templates WHERE name = ?", (name,)).fetchone()
    return _row_to_template(row) if row else None


def save(conn: sqlite3.Connection, template: Template) -> None:
    conn.execute(
        """
        INSERT INTO templates (
            name, subject, topic_list, branch_list, subtopic_list,
            type_list, source_list, tag_list,
            n_questions, reuse_questions, include_sources, in_syllabus_only,
            min_difficulty, save_directory, solutions
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
            subject = excluded.subject,
            topic_list = excluded.topic_list,
            branch_list = excluded.branch_list,
            subtopic_list = excluded.subtopic_list,
            type_list = excluded.type_list,
            source_list = excluded.source_list,
            tag_list = excluded.tag_list,
            n_questions = excluded.n_questions,
            reuse_questions = excluded.reuse_questions,
            include_sources = excluded.include_sources,
            in_syllabus_only = excluded.in_syllabus_only,
            min_difficulty = excluded.min_difficulty,
            save_directory = excluded.save_directory,
            solutions = excluded.solutions
        """,
        (
            template.name,
            template.subject,
            json.dumps(template.topic_list),
            json.dumps(template.branch_list),
            json.dumps(template.subtopic_list),
            json.dumps(template.type_list),
            json.dumps(template.source_list),
            json.dumps(template.tag_list),
            template.n_questions,
            template.reuse_questions,
            template.include_sources,
            template.in_syllabus_only,
            template.min_difficulty,
            template.save_directory,
            template.solutions,
        ),
    )
    conn.commit()


def delete(conn: sqlite3.Connection, name: str) -> None:
    conn.execute("DELETE FROM templates WHERE name = ?", (name,))
    conn.commit()


def rename(conn: sqlite3.Connection, old_name: str, new_name: str) -> None:
    """UNIQUE constraint on `name` means renaming over an existing name raises
    `sqlite3.IntegrityError`. Callers should check `exists(new_name)` first."""
    if old_name == new_name:
        return
    cur = conn.execute("UPDATE templates SET name = ? WHERE name = ?", (new_name, old_name))
    if cur.rowcount == 0:
        raise KeyError(f"no template named {old_name!r}")
    conn.commit()


def to_payload(template: Template) -> dict[str, Any]:
    """Serializable form for IPC return value."""
    return {
        "name": template.name,
        "subject": template.subject,
        "topic_list": template.topic_list,
        "branch_list": template.branch_list,
        "subtopic_list": template.subtopic_list,
        "type_list": template.type_list,
        "source_list": template.source_list,
        "tag_list": template.tag_list,
        "n_questions": template.n_questions,
        "reuse_questions": bool(template.reuse_questions),
        "include_sources": bool(template.include_sources),
        "in_syllabus_only": bool(template.in_syllabus_only),
        "min_difficulty": template.min_difficulty,
        "save_directory": template.save_directory,
        "solutions": template.solutions,
    }


def from_payload(payload: dict[str, Any]) -> Template:
    """Inverse of `to_payload` — used by `save_template` IPC to inflate the
    JS-side draft into the dataclass."""
    return Template(
        name=payload["name"],
        subject=payload.get("subject"),
        topic_list=list(payload.get("topic_list") or []),
        branch_list=list(payload.get("branch_list") or []),
        subtopic_list=list(payload.get("subtopic_list") or []),
        type_list=list(payload.get("type_list") or []),
        source_list=list(payload.get("source_list") or []),
        tag_list=dict(payload.get("tag_list") or {"compulsory": [], "optional": [], "excluded": []}),
        n_questions=int(payload.get("n_questions", 10)),
        reuse_questions=int(bool(payload.get("reuse_questions", False))),
        include_sources=int(bool(payload.get("include_sources", True))),
        in_syllabus_only=int(bool(payload.get("in_syllabus_only", True))),
        min_difficulty=payload.get("min_difficulty"),
        save_directory=payload.get("save_directory"),
        solutions=payload.get("solutions"),
    )
