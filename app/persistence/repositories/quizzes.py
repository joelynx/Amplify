"""Repository for `quizzes` / `quiz_questions` / `quiz_attempts` (§3.5).

Quiz row is written at `start_quiz`; question_ids snapshot into
`quiz_questions`. An attempt row is written at `quiz_finish` with the
`summary` JSON containing the full per-question answer log.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from typing import Any

from app.interactive.models import AnswerRecord, QuizConfig

_ATTEMPT_FIELDS = (
    "attempt_id, quiz_id, date_started, date_finished, total_score, summary"
)


def _iso_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def new_quiz_id(prefix: str = "Quiz") -> str:
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{ts}_{uuid.uuid4().hex[:6]}"


def new_attempt_id(quiz_id: str) -> str:
    return f"{quiz_id}_a{uuid.uuid4().hex[:8]}"


def insert_quiz(
    conn: sqlite3.Connection,
    *,
    quiz_id: str,
    subject: str | None,
    filters: dict[str, Any],
    config: QuizConfig,
    template_name: str | None,
    question_ids: list[int],
) -> None:
    """Atomic write: quizzes row + N quiz_questions rows."""
    tags = filters.get("tags") or {}
    try:
        conn.execute(
            """
            INSERT INTO quizzes (
                quiz_id, date_created, subject,
                topic_list, branch_list, subtopic_list,
                source_list, type_list, tag_list,
                n_questions, reuse_questions, template_name,
                time_per_question, total_time, allow_skips, show_scoring,
                penalize_skips_marks, enable_hints, instant_scoring,
                show_solutions, gradient_mode, wait_for_correct,
                pbs_num_widgets, pbs_pool_size
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                quiz_id,
                _iso_now(),
                subject,
                json.dumps(filters.get("topics") or []),
                json.dumps(filters.get("branches") or []),
                json.dumps(filters.get("subtopics") or []),
                json.dumps(filters.get("sources") or []),
                json.dumps(filters.get("types") or []),
                json.dumps(tags),
                len(question_ids),
                int(bool(filters.get("reuse_questions", False))),
                template_name,
                config.time_per_question_s,
                config.total_time_s,
                int(bool(config.allow_skips)),
                int(bool(config.show_scoring)),
                config.penalize_skips_marks,
                int(bool(config.enable_hints)),
                int(bool(config.instant_scoring)),
                int(bool(config.show_solutions)),
                config.gradient_mode,
                int(bool(config.wait_for_correct)),
                config.pbs_num_widgets if config.template == "PBS" else None,
                config.pbs_pool_size if config.template == "PBS" else None,
            ),
        )
        for order, qid in enumerate(question_ids, start=1):
            conn.execute(
                "INSERT INTO quiz_questions (quiz_id, question_id, question_order) VALUES (?, ?, ?)",
                (quiz_id, qid, order),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def insert_attempt(
    conn: sqlite3.Connection,
    *,
    quiz_id: str,
    date_started: str,
    answers: list[AnswerRecord],
    total_score: float,
) -> str:
    attempt_id = new_attempt_id(quiz_id)
    summary = {
        "answers": [
            {
                "question_id": a.question_id,
                "slot_index": a.slot_index,
                "user_answer": a.user_answer,
                "correct": a.correct,
                "score": a.score,
                "wrong_attempts": a.wrong_attempts,
                "self_assessment": a.self_assessment,
                "hints_used": a.hints_used,
                "time_taken_ms": a.time_taken_ms,
                "submitted_at": a.submitted_at,
            }
            for a in answers
        ],
        "n_answers": len(answers),
    }
    try:
        conn.execute(
            """
            INSERT INTO quiz_attempts (attempt_id, quiz_id, date_started, date_finished, total_score, summary)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                attempt_id,
                quiz_id,
                date_started,
                _iso_now(),
                float(total_score),
                json.dumps(summary),
            ),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return attempt_id


def list_attempts(
    conn: sqlite3.Connection,
    *,
    subject: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict[str, Any]]:
    """Reverse-chronological summary list for the History page."""
    parts: list[str] = []
    params: list[Any] = []
    if subject:
        parts.append("q.subject = ?")
        params.append(subject)
    if date_from:
        parts.append("date(a.date_started) >= date(?)")
        params.append(date_from)
    if date_to:
        parts.append("date(a.date_started) <= date(?)")
        params.append(date_to)
    where = " AND ".join(parts) if parts else "1=1"
    rows = conn.execute(
        f"""
        SELECT a.attempt_id, a.quiz_id, a.date_started, a.date_finished, a.total_score,
               q.subject, q.n_questions, q.template_name
        FROM quiz_attempts a JOIN quizzes q ON q.quiz_id = a.quiz_id
        WHERE {where}
        ORDER BY a.date_started DESC
        """,
        params,
    )
    return [
        {
            "attempt_id": r["attempt_id"],
            "quiz_id": r["quiz_id"],
            "date_started": r["date_started"],
            "date_finished": r["date_finished"],
            "total_score": r["total_score"],
            "subject": r["subject"],
            "n_questions": r["n_questions"],
            "template_name": r["template_name"],
        }
        for r in rows
    ]


def get_attempt(conn: sqlite3.Connection, attempt_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        f"SELECT {_ATTEMPT_FIELDS} FROM quiz_attempts WHERE attempt_id = ?",
        (attempt_id,),
    ).fetchone()
    if row is None:
        return None
    summary = json.loads(row["summary"] or "{}")
    quiz = conn.execute(
        "SELECT subject, template_name, n_questions FROM quizzes WHERE quiz_id = ?",
        (row["quiz_id"],),
    ).fetchone()
    return {
        "attempt_id": row["attempt_id"],
        "quiz_id": row["quiz_id"],
        "date_started": row["date_started"],
        "date_finished": row["date_finished"],
        "total_score": row["total_score"],
        "subject": quiz["subject"] if quiz else None,
        "template_name": quiz["template_name"] if quiz else None,
        "n_questions": quiz["n_questions"] if quiz else 0,
        "answers": summary.get("answers", []),
    }
