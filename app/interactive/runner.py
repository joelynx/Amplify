"""Non-PBS quiz runner — one visible widget at a time.

Honors the four spec §10 flags that aren't PBS-specific:
- `allow_skips`         — disables `next_question` IPC nav when off
- `wait_for_correct`    — refuses to advance past a wrong submission
- `instant_scoring`     — free navigation between questions disabled (we
                          enforce by refusing to take_widget without a submit
                          on the current slot)
- `show_solutions`      — surfaced in the IPC return so the frontend can
                          reveal post-submit; we don't gate it server-side
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app.core.models import Question
from app.interactive.models import AnswerRecord, QuizSession
from app.interactive.scoring import grade

log = logging.getLogger("amplify.interactive.runner")


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def take_widget(session: QuizSession, slot_index: int = 0) -> Question | None:
    """Non-PBS only — returns the question currently bound to slot 0 (or None
    when the pool is exhausted). Treats out-of-range `slot_index` as 0 since
    non-PBS has exactly one slot."""
    _ = slot_index  # non-PBS has a single slot
    if session.current_index >= len(session.pool):
        return None
    return session.pool[session.current_index]


def _record_answer(
    session: QuizSession,
    q: Question,
    *,
    slot_index: int,
    user_answer: str,
    correct: bool | None,
    score: float,
    wrong_attempts: int,
    time_taken_ms: int,
    self_assessment: str | None,
    hints_used: int,
) -> None:
    session.answers.append(
        AnswerRecord(
            question_id=q.question_id,
            slot_index=slot_index,
            user_answer=user_answer,
            correct=correct,
            score=score,
            wrong_attempts=wrong_attempts,
            self_assessment=self_assessment,
            hints_used=hints_used,
            time_taken_ms=time_taken_ms,
            submitted_at=_now(),
        )
    )


def submit_answer(
    session: QuizSession,
    *,
    slot_index: int,
    user_answer: str,
    self_assessment: str | None = None,
    time_taken_ms: int = 0,
    hints_used: int = 0,
) -> dict[str, Any]:
    """Submit the current slot's answer. Returns a result dict.

    Shape:
        {
            "correct": bool | None,
            "partial_score": float,
            "canonical_answer": str | None,
            "solution": str | None,    # only if show_solutions
            "replacement": Question or None or {sentinel: 'wait_for_correct'},
            "finished": bool,
        }
    """
    if session.finished:
        return {"correct": None, "partial_score": 0.0, "finished": True}
    q = take_widget(session, slot_index)
    if q is None:
        session.finished = True
        return {"correct": None, "partial_score": 0.0, "finished": True}

    auto = grade(q, user_answer)
    # Resolve correctness: self_assessment wins when provided, else auto.
    if self_assessment is not None:
        if self_assessment == "got_it":
            correct: bool | None = True
        elif self_assessment == "missed":
            correct = False
        else:
            correct = False  # "partial" treated as wrong for scoring; flag preserved
    else:
        correct = auto

    base = session.base_scores.get(q.question_id, session.config.max_points)
    if correct is True:
        score = float(base) if self_assessment != "partial" else float(base) * 0.5
    elif self_assessment == "partial":
        score = float(base) * 0.5
    else:
        score = 0.0

    wrong_before = session.wrong_counts.get(q.question_id, 0)
    if correct is False:
        session.wrong_counts[q.question_id] = wrong_before + 1

    _record_answer(
        session,
        q,
        slot_index=slot_index,
        user_answer=user_answer,
        correct=correct,
        score=score,
        wrong_attempts=wrong_before,
        time_taken_ms=time_taken_ms,
        self_assessment=self_assessment,
        hints_used=hints_used,
    )

    advance = True
    if session.config.wait_for_correct and correct is False:
        advance = False

    replacement: Question | None = None
    finished = False
    if advance:
        session.current_index += 1
        if session.current_index >= len(session.pool):
            session.finished = True
            finished = True
        else:
            replacement = session.pool[session.current_index]
            session.visible_slots[0] = replacement

    return {
        "correct": correct,
        "partial_score": score,
        "canonical_answer": q.answer,
        "solution": q.solution if session.config.show_solutions else None,
        "replacement": _question_to_dict(replacement) if replacement else None,
        "finished": finished,
        "current_total": sum(a.score for a in session.answers),
    }


def skip(session: QuizSession, slot_index: int = 0) -> dict[str, Any]:
    """Record an unanswered slot and advance (only if allow_skips on)."""
    _ = slot_index
    if session.finished:
        return {"finished": True}
    if not session.config.allow_skips:
        return {"finished": False, "skipped": False, "error": "skips disabled"}
    q = take_widget(session)
    if q is None:
        session.finished = True
        return {"finished": True}
    penalty = float(session.config.penalize_skips_marks or 0.0)
    _record_answer(
        session,
        q,
        slot_index=0,
        user_answer="",
        correct=None,
        score=-penalty,
        wrong_attempts=session.wrong_counts.get(q.question_id, 0),
        time_taken_ms=0,
        self_assessment="skipped",
        hints_used=0,
    )
    session.current_index += 1
    finished = session.current_index >= len(session.pool)
    if finished:
        session.finished = True
    repl = None if finished else session.pool[session.current_index]
    if repl is not None:
        session.visible_slots[0] = repl
    return {
        "finished": finished,
        "replacement": _question_to_dict(repl) if repl else None,
        "current_total": sum(a.score for a in session.answers),
    }


def _question_to_dict(q: Question) -> dict[str, Any]:
    """Project a Question for the quiz UI. Strips the canonical `answer`
    so the user can't peek at it via dev-tools mid-quiz."""
    return {
        "question_id": q.question_id,
        "topic": q.topic,
        "branch": q.branch,
        "subtopic": q.subtopic,
        "latexcode": q.latexcode,
        "type": q.type,
        "hints": q.hints,
        "instructions": q.instructions,
    }
