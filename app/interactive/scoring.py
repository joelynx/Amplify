"""Scoring + answer-grading helpers (spec §10.1 PBS decay + gradient modes).

Grading goes through the question's answer key (`app/core/answer_key.py`,
pipeline/answer_key_spec.md): one input per part, a credit in [0, 1] per part,
the question's credit is their mean. `Graded` is one submission on its way
through the quiz flows (non-PBS runner, PBS, Traverse / Discover).

`loosely_equal` (the port of `looselyEqual` from the `karth/web-mvp` branch's
`lib/grade.ts`) now lives in the answer-key module, which uses it for
`expression` parts; it is re-exported here for existing callers.
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Literal

from app.core import answer_key as ak
from app.core.answer_key import loosely_equal
from app.core.models import Question
from app.interactive.models import PendingAnswer

__all__ = [
    "Graded",
    "build_gradient",
    "grade",
    "grade_submission",
    "loosely_equal",
    "pbs_decayed_score",
    "pending_result",
]

GradientMode = Literal["random", "constant", "custom"]


@dataclass(slots=True)
class Graded:
    """One submission: the key's parts, the student's input per part, and the
    credit per part (None = awaiting self-assessment) with its mark, if any."""

    parts: list[ak.Part]
    inputs: list[str]
    credits: list[float | None]
    marks: list[str | None]

    @property
    def awaiting(self) -> bool:
        return any(c is None for c in self.credits)

    @property
    def auto_wrong(self) -> bool:
        """Some auto-graded part is wrong (PBS / wait_for_correct: the whole
        submission then counts as wrong)."""
        return any(c is not None and c < 1.0 and m is None for c, m in zip(self.credits, self.marks))

    @property
    def credit(self) -> float:
        return ak.question_credit(self.credits)

    @property
    def needs_solution(self) -> bool:
        """A self-assessed part has nothing to compare against (a `points` part
        without a checklist): show the solution with the reveal."""
        return any(p.kind == "points" and not p.points for p in self.parts)

    @property
    def single_mark(self) -> str | None:
        """The self-assessment of a one-part question (AnswerRecord.self_assessment)."""
        return self.marks[0] if len(self.parts) == 1 else None

    def results(self, *, reveal: bool = True) -> list[dict[str, Any]]:
        return [
            ak.part_result(p, t, c, m, reveal=reveal)
            for p, t, c, m in zip(self.parts, self.inputs, self.credits, self.marks)
        ]

    def answer_text(self) -> str:
        """The inputs as one string (AnswerRecord.user_answer)."""
        if len(self.parts) == 1:
            return self.inputs[0]
        return "; ".join(f"({p.label}) {t}" if p.label else t for p, t in zip(self.parts, self.inputs))

    def with_marks(self, marks: Sequence[str | None]) -> Graded:
        credits, new_marks = ak.apply_marks(self.credits, marks)
        merged = [old if old is not None else new for old, new in zip(self.marks, new_marks)]
        return Graded(self.parts, self.inputs, credits, merged)

    def closed(self) -> Graded:
        """Unmarked parts credited 0 (a quiz that ends mid self-assessment)."""
        return Graded(self.parts, self.inputs, [c or 0.0 for c in self.credits], self.marks)

    def pending(self, question_id: int, user_answer: str, time_taken_ms: int, hints_used: int = 0) -> PendingAnswer:
        return PendingAnswer(
            question_id=question_id,
            inputs=list(self.inputs),
            credits=list(self.credits),
            user_answer=user_answer,
            time_taken_ms=time_taken_ms,
            hints_used=hints_used,
        )

    @classmethod
    def from_pending(cls, q: Question, p: PendingAnswer) -> Graded:
        parts = ak.parts_for(q)
        return cls(parts, list(p.inputs), list(p.credits), [None] * len(parts))


def grade_submission(
    q: Question,
    *,
    answers: Sequence[Any] | None = None,
    user_answer: str = "",
    self_assessment: str | None = None,
) -> Graded:
    """Grade the auto-gradable parts. `answers` holds one input per part; without
    it `user_answer` is the first part's input (the old single-string path).
    `self_assessment` (the old one-call path) marks every part that needs it."""
    parts = ak.parts_for(q)
    inputs = ak.align_inputs(parts, answers, user_answer)
    g = Graded(parts, inputs, ak.grade_parts(parts, inputs), [None] * len(parts))
    if self_assessment in ak.MARK_CREDIT:
        g = g.with_marks([self_assessment] * len(parts))
    return g


def pending_result(g: Graded) -> dict[str, Any]:
    """The submit result while parts await self-assessment: every part with its
    expected answer / checklist, auto-graded ones already credited."""
    return {"correct": None, "pending": True, "retry": False, "credit": None, "parts": g.results(), "partial_score": 0.0}


def build_gradient(
    mode: GradientMode,
    n_questions: int,
    max_points: float,
    rng: random.Random | None = None,
) -> list[float]:
    """Per-question base point assignment, indexed by quiz pool position.

    - `constant`: every question worth `max_points`.
    - `random`:   uniform(1, max_points), rounded to the nearest .1.
    - `custom`:   not parametrized at this level — caller supplies values
      (here we just fall back to constant). Hook for future per-template
      custom curves.
    """
    n = max(0, int(n_questions))
    if n == 0:
        return []
    if mode == "constant":
        return [float(max_points)] * n
    if mode == "random":
        r = rng or random.Random()
        return [round(r.uniform(1.0, max_points), 1) for _ in range(n)]
    return [float(max_points)] * n


def pbs_decayed_score(
    base: float,
    wrong_attempts: int,
    *,
    decay_factor: float = 0.5,
    min_score: float = 1.0,
) -> float:
    """PBS available-score after `wrong_attempts` wrong submissions.

    Geometric decay (spec §10.1): `base * decay_factor^wrong`, floored at
    `min_score`. Never negative.
    """
    if wrong_attempts <= 0:
        return max(min_score, float(base))
    decayed = float(base) * (decay_factor ** wrong_attempts)
    return max(min_score, decayed)


def grade(question: Question, user_answer: str) -> bool | None:
    """Single-string grade against the answer key: True / False when every part
    is auto-graded, None when some part needs self-assessment."""
    g = grade_submission(question, user_answer=user_answer)
    if g.awaiting:
        return None
    return g.credit >= 1.0
