"""Scoring + answer-grading helpers (spec §10.1 PBS decay + gradient modes).

Ports `looselyEqual` from the `karth/web-mvp` branch's `lib/grade.ts`:
strip whitespace + `\\boxed{…}`, parse both sides as floats, accept exact
string match OR relative-tolerance numerical match (1e-3).
"""

from __future__ import annotations

import random
import re
from typing import Literal

from app.core.models import Question

_BOXED_OPEN_RE = re.compile(r"^\\boxed\{")
_BOXED_CLOSE_RE = re.compile(r"\}$")

GradientMode = Literal["random", "constant", "custom"]


def _normalize(s: str) -> str:
    out = (s or "").strip().lower()
    out = re.sub(r"\s+", "", out)
    out = _BOXED_OPEN_RE.sub("", out)
    out = _BOXED_CLOSE_RE.sub("", out)
    return out


def loosely_equal(a: str, b: str) -> bool:
    """Approximate numerical equivalence with 1e-3 relative tolerance.

    Falls back to exact string match for non-numerical (proof / explanation)
    answers — usually unhelpful, so callers should pair with self-assessment
    for those types.
    """
    na = _normalize(a)
    nb = _normalize(b)
    if na == nb:
        return True
    try:
        fa = float(na)
        fb = float(nb)
    except ValueError:
        return False
    if fa == fb:
        return True
    diff = abs(fa - fb)
    scale = max(1.0, abs(fa), abs(fb))
    return diff / scale < 1e-3


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
    """Auto-grade if the question carries a canonical numerical answer;
    return None when the question requires self-assessment (proof /
    explanation, or numerical with no canonical answer recorded)."""
    if not question.answer or question.answer.strip().upper() in ("N/A", "NA", ""):
        return None
    if question.type == "numerical":
        return loosely_equal(user_answer, question.answer)
    if question.type == "proof" or question.type == "explanation/reasoning":
        # Auto-grade is unreliable; surface as self-assess.
        return None
    # Unknown type — try string match.
    return loosely_equal(user_answer, question.answer)
