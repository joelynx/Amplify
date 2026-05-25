"""Repository for `psets` and `pset_questions` (§3.4).

The "successful generate" write path is atomic per spec §6.1:
  - INSERT INTO psets
  - INSERT N rows into pset_questions
  - UPDATE questions: times_used += 1, date_last_accessed = now()
all in one transaction.

Step 8 adds list / get / delete / get_filters_payload for the History page.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from typing import Any

from app.core.models import PSet, PSetSummary


def count(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM psets").fetchone()[0])


def insert_pset(
    conn: sqlite3.Connection,
    *,
    pset_id: str,
    subject: str | None,
    filters: dict[str, Any],
    output_settings: dict[str, Any],
    template_name: str | None,
    question_ids: list[int],
) -> None:
    """Atomic write: psets row + pset_questions rows + times_used bumps."""

    tags = filters.get("tags") or {}
    topic_list = filters.get("topics") or []
    branch_list = filters.get("branches") or []
    subtopic_list = filters.get("subtopics") or []
    source_list = filters.get("sources") or []
    type_list = filters.get("types") or []

    n = len(question_ids)
    date_created = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")

    topic_dist: dict[str, int] = {}
    subtopic_dist: dict[str, int] = {}
    if question_ids:
        placeholders = ",".join(["?"] * len(question_ids))
        rows = conn.execute(
            f"SELECT topic, subtopic FROM questions WHERE question_id IN ({placeholders})",
            question_ids,
        )
        for topic, subtopic in rows:
            topic_dist[topic] = topic_dist.get(topic, 0) + 1
            subtopic_dist[subtopic] = subtopic_dist.get(subtopic, 0) + 1

    try:
        conn.execute(
            """
            INSERT INTO psets (
                pset_id, date_created, subject,
                topic_list, branch_list, subtopic_list,
                source_list, type_list, tag_list,
                n_questions, reuse_questions, template_name,
                topic_dist, subtopic_dist, solutions,
                save_directory, include_sources
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pset_id,
                date_created,
                subject,
                json.dumps(topic_list),
                json.dumps(branch_list),
                json.dumps(subtopic_list),
                json.dumps(source_list),
                json.dumps(type_list),
                json.dumps(tags),
                n,
                int(bool(filters.get("reuse_questions", False))),
                template_name,
                json.dumps(topic_dist),
                json.dumps(subtopic_dist),
                output_settings.get("solutions"),
                output_settings.get("save_directory"),
                int(bool(output_settings.get("include_sources", True))),
            ),
        )
        for order, qid in enumerate(question_ids, start=1):
            conn.execute(
                "INSERT INTO pset_questions (pset_id, question_id, question_order) VALUES (?, ?, ?)",
                (pset_id, qid, order),
            )
        if question_ids:
            placeholders = ",".join(["?"] * len(question_ids))
            conn.execute(
                f"UPDATE questions SET times_used = times_used + 1, "
                f"date_last_accessed = datetime('now') "
                f"WHERE question_id IN ({placeholders})",
                question_ids,
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise


# ---- Step 8: History reads ---------------------------------------------

def _pset_question_ids(conn: sqlite3.Connection, pset_id: str) -> list[int]:
    rows = conn.execute(
        "SELECT question_id FROM pset_questions WHERE pset_id = ? ORDER BY question_order",
        (pset_id,),
    )
    return [int(r[0]) for r in rows]


def _row_to_pset(row: sqlite3.Row, conn: sqlite3.Connection) -> PSet:
    return PSet(
        pset_id=row["pset_id"],
        date_created=row["date_created"],
        n_questions=int(row["n_questions"]),
        reuse_questions=int(row["reuse_questions"]),
        subject=row["subject"],
        topic_list=json.loads(row["topic_list"] or "[]"),
        branch_list=json.loads(row["branch_list"] or "[]"),
        subtopic_list=json.loads(row["subtopic_list"] or "[]"),
        source_list=json.loads(row["source_list"] or "[]"),
        type_list=json.loads(row["type_list"] or "[]"),
        tag_list=json.loads(row["tag_list"] or '{"compulsory": [], "optional": [], "excluded": []}'),
        template_name=row["template_name"],
        topic_dist=json.loads(row["topic_dist"] or "{}"),
        subtopic_dist=json.loads(row["subtopic_dist"] or "{}"),
        solutions=row["solutions"],
        question_ids=_pset_question_ids(conn, row["pset_id"]),
    )


def list_summaries(
    conn: sqlite3.Connection,
    *,
    subject: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[PSetSummary]:
    """Reverse-chronological list for the History page (spec §8.5)."""
    parts: list[str] = []
    params: list[Any] = []
    if subject is not None:
        parts.append("subject = ?")
        params.append(subject)
    if date_from:
        parts.append("date(date_created) >= date(?)")
        params.append(date_from)
    if date_to:
        parts.append("date(date_created) <= date(?)")
        params.append(date_to)
    where = " AND ".join(parts) if parts else "1=1"
    rows = conn.execute(
        f"SELECT pset_id, date_created, subject, n_questions, template_name "
        f"FROM psets WHERE {where} ORDER BY date_created DESC, pset_id DESC",
        params,
    )
    return [
        PSetSummary(
            pset_id=r["pset_id"],
            date_created=r["date_created"],
            n_questions=int(r["n_questions"]),
            subject=r["subject"],
            template_name=r["template_name"],
        )
        for r in rows
    ]


def get(conn: sqlite3.Connection, pset_id: str) -> PSet | None:
    row = conn.execute("SELECT * FROM psets WHERE pset_id = ?", (pset_id,)).fetchone()
    return _row_to_pset(row, conn) if row else None


def get_save_directory(conn: sqlite3.Connection, pset_id: str) -> str | None:
    row = conn.execute(
        "SELECT save_directory FROM psets WHERE pset_id = ?", (pset_id,)
    ).fetchone()
    return row["save_directory"] if row else None


def get_include_sources(conn: sqlite3.Connection, pset_id: str) -> bool:
    row = conn.execute(
        "SELECT include_sources FROM psets WHERE pset_id = ?", (pset_id,)
    ).fetchone()
    return bool(row["include_sources"]) if row else True


def delete(conn: sqlite3.Connection, pset_id: str) -> None:
    """Removes the psets row + cascading pset_questions. Does NOT delete the
    saved PDF on disk (spec §8.5: "stays on disk wherever the user saved it")."""
    conn.execute("DELETE FROM psets WHERE pset_id = ?", (pset_id,))
    conn.commit()


def get_filters_payload(conn: sqlite3.Connection, pset_id: str) -> dict[str, Any] | None:
    """Reconstruct a Generate-form-shaped payload from the stored PSet — the
    "Generate similar" flow consumes this on the frontend."""
    p = get(conn, pset_id)
    if p is None:
        return None
    return {
        "name": p.pset_id,  # placeholder; History uses this as "source PSet"
        "subject": p.subject,
        "topic_list": p.topic_list,
        "branch_list": p.branch_list,
        "subtopic_list": p.subtopic_list,
        "type_list": p.type_list,
        "source_list": p.source_list,
        "tag_list": p.tag_list,
        "n_questions": p.n_questions,
        "reuse_questions": bool(p.reuse_questions),
        "include_sources": bool(get_include_sources(conn, pset_id)),
        "in_syllabus_only": True,  # not stored; safe default
        "min_difficulty": None,
        "save_directory": get_save_directory(conn, pset_id),
        "solutions": p.solutions,
    }
