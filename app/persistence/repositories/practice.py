"""Repository for practice history (migration 009): `answer_events`,
`question_notes`, `review_dismissals`, and `quiz_questions.presented_at`.

Every finished answer is written here as well as onto its attempt's summary
JSON (which the attempt review page reads); the review queue and the learning
stats read only from here.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from app.core.filters import assemble_where
from app.core.models import Subject
from app.core.review import Event, parse_time
from app.interactive.models import AnswerRecord

PAPER_MODE = "PAPER"
PAPER_CREDIT: dict[str, float] = {"solved": 1.0, "partial": 0.5, "missed": 0.0}


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _commit(conn: sqlite3.Connection, fn: Any) -> Any:
    try:
        out = fn()
        conn.commit()
        return out
    except Exception:
        conn.rollback()
        raise


def subject_question_clause(subject: Subject | None) -> tuple[str, list[Any]]:
    """`question_id IN (...)` for the subject's curricular gate (no syllabus or
    reuse restriction), for tables keyed by question_id."""
    payload = subject.to_payload() if subject else None
    where, params = assemble_where({"in_syllabus_only": False, "reuse_questions": True}, payload)
    return f"question_id IN (SELECT question_id FROM questions WHERE {where})", params


# ---- answers --------------------------------------------------------------


def record_answer(
    conn: sqlite3.Connection, *, quiz_id: str | None, mode: str, record: AnswerRecord
) -> None:
    """Log one finished answer. Skips (`self_assessment == "skipped"`) are not
    answers and are not logged."""
    if record.self_assessment == "skipped":
        return
    credit = record.credit
    if credit is None:
        credit = {"got_it": 1.0, "partial": 0.5, "missed": 0.0}.get(record.self_assessment or "")
    if credit is None:
        credit = 1.0 if record.correct else 0.0
    self_assessed = int(
        bool(record.self_assessment) or any((p or {}).get("mark") for p in (record.parts or []))
    )
    _commit(
        conn,
        lambda: conn.execute(
            """
            INSERT INTO answer_events (
                question_id, quiz_id, mode, occurred_at, kind, credit,
                self_assessed, hints_used, revealed, time_taken_ms
            ) VALUES (?, ?, ?, ?, 'answered', ?, ?, ?, 0, ?)
            """,
            (
                record.question_id,
                quiz_id,
                mode,
                record.submitted_at or _now(),
                float(credit),
                self_assessed,
                int(record.hints_used or 0),
                int(record.time_taken_ms or 0),
            ),
        ),
    )


def record_reveal(conn: sqlite3.Connection, *, quiz_id: str, mode: str, question_id: int) -> bool:
    """The answer or solution was opened before answering: no grade, and the
    question goes on the "try it independently" list. Once per quiz and
    question; returns False when already logged."""
    exists = conn.execute(
        "SELECT 1 FROM answer_events WHERE quiz_id = ? AND question_id = ? AND kind = 'revealed'",
        (quiz_id, question_id),
    ).fetchone()
    if exists:
        return False
    _commit(
        conn,
        lambda: conn.execute(
            "INSERT INTO answer_events (question_id, quiz_id, mode, occurred_at, kind, revealed) "
            "VALUES (?, ?, ?, ?, 'revealed', 1)",
            (question_id, quiz_id, mode, _now()),
        ),
    )
    return True


def record_paper_results(
    conn: sqlite3.Connection, pset_id: str, results: Iterable[dict[str, Any]]
) -> int:
    """Results for a printed PSet: per question `outcome` (solved / partial /
    missed, or null to clear) and `assisted` (used a hint or the solution).
    Re-recording a question replaces its earlier paper result for this PSet.
    Questions not on the PSet are ignored. Returns the number recorded."""
    on_pset = {
        int(r[0]) for r in conn.execute("SELECT question_id FROM pset_questions WHERE pset_id = ?", (pset_id,))
    }
    now = _now()

    def write() -> int:
        n = 0
        for r in results:
            qid = int(r.get("question_id", -1))
            if qid not in on_pset:
                continue
            conn.execute(
                "DELETE FROM answer_events WHERE pset_id = ? AND question_id = ? AND mode = ?",
                (pset_id, qid, PAPER_MODE),
            )
            outcome = r.get("outcome")
            if outcome not in PAPER_CREDIT:
                continue
            conn.execute(
                """
                INSERT INTO answer_events (
                    question_id, pset_id, mode, occurred_at, kind, credit,
                    self_assessed, hints_used, revealed
                ) VALUES (?, ?, ?, ?, 'answered', ?, 1, ?, 0)
                """,
                (qid, pset_id, PAPER_MODE, now, PAPER_CREDIT[outcome], 1 if r.get("assisted") else 0),
            )
            n += 1
        return n

    return _commit(conn, write)


def paper_results(conn: sqlite3.Connection, pset_id: str) -> dict[int, dict[str, Any]]:
    """The recorded paper results of a PSet, by question id."""
    back = {v: k for k, v in PAPER_CREDIT.items()}
    out: dict[int, dict[str, Any]] = {}
    for r in conn.execute(
        "SELECT question_id, credit, hints_used, occurred_at FROM answer_events "
        "WHERE pset_id = ? AND mode = ? ORDER BY occurred_at",
        (pset_id, PAPER_MODE),
    ):
        out[int(r[0])] = {
            "outcome": back.get(float(r[1]), "partial"),
            "assisted": bool(r[2]),
            "recorded_at": r[3],
        }
    return out


def load_events(
    conn: sqlite3.Connection,
    subject: Subject | None = None,
    date_range: tuple[str | None, str | None] = (None, None),
) -> list[Event]:
    """Answer events inside the subject's gate, optionally limited to a date
    range (inclusive, on the date part)."""
    clause, params = subject_question_clause(subject)
    parts = [clause]
    df, dt = date_range
    if df:
        parts.append("date(occurred_at) >= date(?)")
        params.append(df)
    if dt:
        parts.append("date(occurred_at) <= date(?)")
        params.append(dt)
    rows = conn.execute(
        "SELECT question_id, occurred_at, kind, credit, hints_used, revealed, self_assessed, mode "
        f"FROM answer_events WHERE {' AND '.join(parts)} ORDER BY occurred_at, event_id",
        params,
    )
    return [
        Event(
            question_id=int(r[0]),
            occurred_at=parse_time(r[1]),
            kind=r[2],
            credit=r[3],
            hints_used=r[4],
            revealed=r[5],
            self_assessed=r[6],
            mode=r[7] or "",
        )
        for r in rows
    ]


# ---- review dismissals ------------------------------------------------------


def dismissals(conn: sqlite3.Connection) -> dict[int, datetime]:
    return {int(r[0]): parse_time(r[1]) for r in conn.execute("SELECT question_id, dismissed_at FROM review_dismissals")}


def dismiss(conn: sqlite3.Connection, question_id: int) -> None:
    _commit(
        conn,
        lambda: conn.execute(
            "INSERT INTO review_dismissals (question_id, dismissed_at) VALUES (?, ?) "
            "ON CONFLICT(question_id) DO UPDATE SET dismissed_at = excluded.dismissed_at",
            (question_id, _now()),
        ),
    )


# ---- presentation -----------------------------------------------------------


def mark_presented(conn: sqlite3.Connection, quiz_id: str, question_id: int) -> bool:
    """Stamp the first time a quiz question is shown and count it as used then.
    Returns False when it was already shown (or is not on the quiz)."""

    def write() -> bool:
        cur = conn.execute(
            "UPDATE quiz_questions SET presented_at = ? "
            "WHERE quiz_id = ? AND question_id = ? AND presented_at IS NULL",
            (_now(), quiz_id, question_id),
        )
        if cur.rowcount != 1:
            return False
        conn.execute(
            "UPDATE questions SET interactive_times_used = interactive_times_used + 1 WHERE question_id = ?",
            (question_id,),
        )
        return True

    return _commit(conn, write)


# ---- notes and bookmarks ----------------------------------------------------


def notes_for(conn: sqlite3.Connection, question_ids: list[int]) -> dict[int, dict[str, Any]]:
    if not question_ids:
        return {}
    marks = ",".join("?" * len(question_ids))
    return {
        int(r[0]): {"note": r[1], "bookmarked": bool(r[2]), "updated_at": r[3]}
        for r in conn.execute(
            f"SELECT question_id, note, bookmarked, updated_at FROM question_notes WHERE question_id IN ({marks})",
            question_ids,
        )
    }


def save_note(conn: sqlite3.Connection, question_id: int, note: str) -> None:
    _commit(
        conn,
        lambda: conn.execute(
            "INSERT INTO question_notes (question_id, note, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(question_id) DO UPDATE SET note = excluded.note, updated_at = excluded.updated_at",
            (question_id, note, _now()),
        ),
    )


def set_bookmark(conn: sqlite3.Connection, question_id: int, on: bool) -> None:
    _commit(
        conn,
        lambda: conn.execute(
            "INSERT INTO question_notes (question_id, bookmarked, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(question_id) DO UPDATE SET bookmarked = excluded.bookmarked, updated_at = excluded.updated_at",
            (question_id, int(bool(on)), _now()),
        ),
    )


def bookmarked_ids(conn: sqlite3.Connection, subject: Subject | None = None) -> list[int]:
    clause, params = subject_question_clause(subject)
    return [
        int(r[0])
        for r in conn.execute(
            f"SELECT question_id FROM question_notes WHERE bookmarked = 1 AND {clause} ORDER BY updated_at DESC",
            params,
        )
    ]
