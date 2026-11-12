"""Non-PBS quiz runner — one visible widget at a time.

Honors the four spec §10 flags that aren't PBS-specific:
- `allow_skips`         — disables `next_question` IPC nav when off
- `wait_for_correct`    — refuses to advance past a submission with a wrong
                          auto-graded part
- `instant_scoring`     — free navigation between questions disabled (we
                          enforce by refusing to take_widget without a submit
                          on the current slot)
- `show_solutions`      — surfaced in the IPC return so the frontend can
                          reveal post-submit; we don't gate it server-side

Grading follows the question's answer key (pipeline/answer_key_spec.md): one
input per part. Parts that need self-assessment make the submission pending
until `self_assess` records the student's marks.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from app.core import answer_key as ak
from app.core.models import Question
from app.interactive.models import AnswerRecord, QuizSession
from app.interactive.scoring import Graded, grade_submission, pending_result

log = logging.getLogger("amplify.interactive.runner")


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


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
    credit: float | None = None,
    parts: list[dict[str, Any]] | None = None,
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
            credit=credit,
            parts=parts,
        )
    )


def submit_answer(
    session: QuizSession,
    *,
    slot_index: int,
    user_answer: str = "",
    answers: list[Any] | None = None,
    self_assessment: str | None = None,
    time_taken_ms: int = 0,
    hints_used: int = 0,
) -> dict[str, Any]:
    """Submit the current slot's answer. Returns a result dict.

    `answers` holds one input per answer-key part; without it `user_answer` is
    the first part's input. Auto-graded parts are graded and locked in at once.
    If a part needs self-assessment the result is `pending`: nothing is recorded,
    every part comes back with its expected answer / checklist, and
    `self_assess` finishes the question. `self_assessment` (the old one-call
    path) marks every such part up front.

    Shape:
        {
            "correct": bool | None,    # None while pending
            "pending": bool,
            "retry": bool,             # wait_for_correct kept the question up
            "credit": float | None,    # mean part credit
            "parts": [answer_key.part_result, ...],
            "partial_score": float,
            "canonical_answer": str | None,
            "solution": str | None,    # if show_solutions (or nothing else to self-assess against)
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
    if 0 in session.pending:
        return {"correct": None, "pending": True, "error": "self-assess the revealed parts first"}

    g = grade_submission(q, answers=answers, user_answer=user_answer, self_assessment=self_assessment)
    held = session.config.wait_for_correct and g.auto_wrong
    if g.awaiting and not held:
        session.pending[0] = g.pending(q.question_id, user_answer, time_taken_ms, hints_used)
        show = session.config.show_solutions or g.needs_solution
        return {
            **pending_result(g),
            "canonical_answer": q.answer,
            "solution": q.best_solution() if show else None,
            "replacement": None,
            "finished": False,
            "current_total": sum(a.score for a in session.answers),
        }
    return _finalize(session, q, g, held=held, time_taken_ms=time_taken_ms, hints_used=hints_used)


def self_assess(session: QuizSession, *, slot_index: int = 0, marks: list[str | None]) -> dict[str, Any]:
    """Record the student's marks (`got_it` / `partial` / `missed`, aligned with
    the parts; entries for auto-graded parts are ignored) for a pending
    submission and finish the question. Same result shape as `submit_answer`."""
    _ = slot_index
    p = session.pending.get(0)
    if p is None:
        return {"correct": None, "pending": False, "error": "nothing is awaiting self-assessment"}
    q = take_widget(session)
    if q is None or q.question_id != p.question_id:
        session.pending.pop(0, None)
        return {"correct": None, "pending": False, "error": "the pending question is no longer current"}
    g = Graded.from_pending(q, p).with_marks(marks)
    if g.awaiting:
        return {"correct": None, "pending": True, "error": "mark every revealed part"}
    del session.pending[0]
    return _finalize(session, q, g, held=False, time_taken_ms=p.time_taken_ms, hints_used=p.hints_used)


def flush_pending(session: QuizSession) -> None:
    """The quiz is ending: record a submission still awaiting self-assessment,
    its unmarked parts credited 0, so its auto-graded credit is kept."""
    p = session.pending.pop(0, None)
    q = take_widget(session)
    if p is None or q is None or q.question_id != p.question_id:
        return
    g = Graded.from_pending(q, p).closed()
    _finalize(session, q, g, held=False, time_taken_ms=p.time_taken_ms, hints_used=p.hints_used)


def _finalize(
    session: QuizSession,
    q: Question,
    g: Graded,
    *,
    held: bool,
    time_taken_ms: int,
    hints_used: int,
) -> dict[str, Any]:
    """Record a graded submission and advance (unless `held`: wait_for_correct
    with a wrong auto-graded part scores 0 and reveals nothing)."""
    credit = g.credit
    correct = credit >= 1.0
    base = session.base_scores.get(q.question_id, session.config.max_points)
    score = 0.0 if held else float(base) * credit

    wrong_before = session.wrong_counts.get(q.question_id, 0)
    if not correct:
        session.wrong_counts[q.question_id] = wrong_before + 1

    _record_answer(
        session,
        q,
        slot_index=0,
        user_answer=g.answer_text(),
        correct=correct,
        score=score,
        wrong_attempts=wrong_before,
        time_taken_ms=time_taken_ms,
        self_assessment=g.single_mark,
        hints_used=hints_used,
        credit=credit,
        parts=g.results(),
    )

    replacement: Question | None = None
    finished = False
    if not held:
        session.current_index += 1
        if session.current_index >= len(session.pool):
            session.finished = True
            finished = True
        else:
            replacement = session.pool[session.current_index]
            session.visible_slots[0] = replacement

    return {
        "correct": correct,
        "pending": False,
        "retry": held,
        "credit": credit,
        "parts": g.results(reveal=not held),
        "partial_score": score,
        "canonical_answer": None if held else q.answer,
        "solution": q.best_solution() if session.config.show_solutions and not held else None,
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
    if 0 in session.pending:
        return {"finished": False, "skipped": False, "error": "self-assess the revealed parts first"}
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
    """Project a Question for the quiz UI. Strips the canonical `answer` (and
    the key: `answer_fields` is its public projection) so the user can't peek
    at it via dev-tools mid-quiz."""
    return {
        "question_id": q.question_id,
        "topic": q.topic,
        "branch": q.branch,
        "subtopic": q.subtopic,
        "latexcode": q.latexcode,
        "type": q.type,
        "hints": q.hints,
        "hint_tiers": q.hint_tiers(),
        "instructions": q.instructions,
        "answer_fields": ak.public_fields(ak.parts_for(q)),
    }
