"""Physics Brawl Style runner (spec §10.1).

N visible widgets at a time, drawn from a pool of size > N. A widget is
"consumed" only when the user submits a CORRECT answer; wrong attempts decay
the question's available score (geometric × 0.5 by default, floor 1) but
don't consume the slot. Switching focus between widgets is free (implicit
skip — no penalty, no advance).

- Numerical answers only. The frontend enforces type at template-creation
  time; we re-enforce at quiz-start (pool already filtered to numerical).
- No hints in PBS.
- Total timer only — no per-question deadline.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app.core.models import Question
from app.interactive.models import AnswerRecord, QuizSession
from app.interactive.scoring import grade, pbs_decayed_score

log = logging.getLogger("amplify.interactive.pbs")


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def initial_widgets(session: QuizSession) -> list[dict[str, Any]]:
    """Snapshot of the N visible slots — used by start_quiz to seed the UI."""
    return [_slot_snapshot(session, i) for i in range(len(session.visible_slots))]


def _slot_snapshot(session: QuizSession, slot_index: int) -> dict[str, Any]:
    q = session.visible_slots[slot_index]
    if q is None:
        return {"slot_index": slot_index, "question": None, "available_score": 0.0}
    return {
        "slot_index": slot_index,
        "question": _question_to_dict(q),
        "available_score": session.available_scores.get(q.question_id, 0.0),
    }


def take_widget(session: QuizSession, slot_index: int) -> dict[str, Any] | None:
    """Re-fetch a slot's current state. PBS doesn't allow forcing a new
    question into a slot (correct submission is the only way to consume),
    so this just returns the current snapshot."""
    if slot_index < 0 or slot_index >= len(session.visible_slots):
        return None
    return _slot_snapshot(session, slot_index)


def submit_answer(
    session: QuizSession,
    *,
    slot_index: int,
    user_answer: str,
    time_taken_ms: int = 0,
) -> dict[str, Any]:
    """Grade a PBS submission. Correct → consume slot, replace with next pool
    question (or None if pool empty). Wrong → halve the available score on
    that slot, no advance."""
    if session.finished:
        return {"correct": None, "finished": True}
    if slot_index < 0 or slot_index >= len(session.visible_slots):
        return {"correct": None, "error": "bad slot_index"}

    q = session.visible_slots[slot_index]
    if q is None:
        return {"correct": None, "error": "slot is empty"}

    auto = grade(q, user_answer)
    correct = bool(auto) if auto is not None else False
    wrong_before = session.wrong_counts.get(q.question_id, 0)

    if correct:
        awarded = session.available_scores.get(q.question_id, session.config.max_points)
        _record(
            session,
            q,
            slot_index=slot_index,
            user_answer=user_answer,
            correct=True,
            score=awarded,
            wrong_attempts=wrong_before,
            time_taken_ms=time_taken_ms,
        )
        # Consume slot — replace from pool, or set to None.
        next_q = _dequeue_next(session)
        session.visible_slots[slot_index] = next_q
        if next_q is None and all(s is None for s in session.visible_slots):
            session.finished = True
        return {
            "correct": True,
            "partial_score": awarded,
            "replacement": _slot_snapshot(session, slot_index),
            "finished": session.finished,
            "current_total": sum(a.score for a in session.answers),
        }

    # Wrong — decay available score.
    session.wrong_counts[q.question_id] = wrong_before + 1
    base = session.base_scores.get(q.question_id, session.config.max_points)
    new_available = pbs_decayed_score(
        base,
        wrong_before + 1,
        decay_factor=session.config.pbs_decay_factor,
        min_score=session.config.pbs_min_score,
    )
    session.available_scores[q.question_id] = new_available
    _record(
        session,
        q,
        slot_index=slot_index,
        user_answer=user_answer,
        correct=False,
        score=0.0,
        wrong_attempts=wrong_before,
        time_taken_ms=time_taken_ms,
    )
    return {
        "correct": False,
        "partial_score": 0.0,
        "replacement": _slot_snapshot(session, slot_index),  # same q, lower available score
        "finished": False,
        "current_total": sum(a.score for a in session.answers),
    }


def _dequeue_next(session: QuizSession) -> Question | None:
    while session.pool_index < len(session.pool):
        candidate = session.pool[session.pool_index]
        session.pool_index += 1
        # Skip questions already in a visible slot (shouldn't happen but defensive).
        if any(s is not None and s.question_id == candidate.question_id for s in session.visible_slots):
            continue
        # Seed available score for this question.
        session.available_scores.setdefault(
            candidate.question_id, session.base_scores.get(candidate.question_id, session.config.max_points)
        )
        return candidate
    return None


def _record(
    session: QuizSession,
    q: Question,
    *,
    slot_index: int,
    user_answer: str,
    correct: bool | None,
    score: float,
    wrong_attempts: int,
    time_taken_ms: int,
) -> None:
    session.answers.append(
        AnswerRecord(
            question_id=q.question_id,
            slot_index=slot_index,
            user_answer=user_answer,
            correct=correct,
            score=score,
            wrong_attempts=wrong_attempts,
            time_taken_ms=time_taken_ms,
            submitted_at=_now(),
        )
    )


def _question_to_dict(q: Question) -> dict[str, Any]:
    return {
        "question_id": q.question_id,
        "topic": q.topic,
        "branch": q.branch,
        "subtopic": q.subtopic,
        "latexcode": q.latexcode,
        "type": q.type,
    }
