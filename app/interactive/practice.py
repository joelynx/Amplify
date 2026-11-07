"""Answers in the browse-style quiz modes (Traverse, Discover).

They have no slots, timer or point gradient: each question is answered on its
own, graded from its answer key (pipeline/answer_key_spec.md), and worth one
point times its credit. As in the slot runners, parts that need
self-assessment make the submission pending until `self_assess`; the pending
state lives here (keyed by quiz and question) because Discover keeps no
session. The caller (the IPC layer) appends each finished AnswerRecord to the
quiz's attempt row.
"""

from __future__ import annotations

import threading
from datetime import UTC, datetime
from typing import Any

from app.core.models import Question
from app.interactive.models import AnswerRecord, PendingAnswer
from app.interactive.scoring import Graded, grade_submission, pending_result

_lock = threading.Lock()
_pending: dict[tuple[str, int], PendingAnswer] = {}


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def submit(
    quiz_id: str,
    q: Question,
    *,
    answers: list[Any] | None = None,
    user_answer: str = "",
    time_taken_ms: int = 0,
) -> tuple[dict[str, Any], AnswerRecord | None]:
    """Grade an answer to `q`. Returns the result (same shape as the slot
    runners' minus slots and replacements) and the record to log, which is
    None while the submission awaits self-assessment."""
    key = (quiz_id, q.question_id)
    with _lock:
        if key in _pending:
            return {"correct": None, "pending": True, "error": "self-assess the revealed parts first"}, None
        g = grade_submission(q, answers=answers, user_answer=user_answer)
        if g.awaiting:
            _pending[key] = g.pending(q.question_id, user_answer, time_taken_ms)
            return {**pending_result(g), "solution": q.best_solution() if g.needs_solution else None}, None
    return _finish(q, g, time_taken_ms)


def self_assess(
    quiz_id: str, q: Question, marks: list[str | None]
) -> tuple[dict[str, Any], AnswerRecord | None]:
    """Record the marks for the pending answer to `q` and finish it."""
    key = (quiz_id, q.question_id)
    with _lock:
        p = _pending.get(key)
        if p is None:
            return {"correct": None, "pending": False, "error": "nothing is awaiting self-assessment"}, None
        g = Graded.from_pending(q, p).with_marks(marks)
        if g.awaiting:
            return {"correct": None, "pending": True, "error": "mark every revealed part"}, None
        del _pending[key]
    return _finish(q, g, p.time_taken_ms)


def _finish(q: Question, g: Graded, time_taken_ms: int) -> tuple[dict[str, Any], AnswerRecord]:
    credit = g.credit
    record = AnswerRecord(
        question_id=q.question_id,
        slot_index=0,
        user_answer=g.answer_text(),
        correct=credit >= 1.0,
        score=credit,
        self_assessment=g.single_mark,
        time_taken_ms=time_taken_ms,
        submitted_at=_now(),
        credit=credit,
        parts=g.results(),
    )
    result = {
        "correct": credit >= 1.0,
        "pending": False,
        "retry": False,
        "credit": credit,
        "parts": g.results(),
        "partial_score": credit,
    }
    return result, record
