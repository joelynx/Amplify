"""Dataclasses for the interactive practice engine (spec §10).

QuizConfig is the user-set options (template + toggles + filters).
QuizSession is the in-memory state of a live run (slots / pool / answers).
AnswerRecord is one user submission, serialized into `quiz_attempts.summary`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from app.core.models import Question

QuizMode = Literal["pbs", "non_pbs"]
GradientMode = Literal["random", "constant", "custom"]
TemplateId = Literal["PBS", "MIT_INTEGRATION_BEE", "FREE_ANSWERING"]


@dataclass(slots=True)
class QuizConfig:
    """Settings panel state at start_quiz time (spec §10 / §3.5)."""

    template: TemplateId
    n_questions: int = 10
    # Timing — total_time wins for PBS (per_question forbidden there).
    time_per_question_s: int | None = None
    total_time_s: int | None = None
    # Flags
    allow_skips: bool = True
    show_scoring: bool = True
    penalize_skips_marks: float | None = None  # only when skips+scoring both on
    enable_hints: bool = True
    instant_scoring: bool = False
    show_solutions: bool = False
    wait_for_correct: bool = False
    # Point gradient
    gradient_mode: GradientMode = "constant"
    max_points: float = 10.0
    # PBS overlay
    pbs_num_widgets: int = 3
    pbs_pool_size: int = 10
    pbs_decay_factor: float = 0.5  # geometric decay per wrong attempt
    pbs_min_score: float = 1.0     # floor


@dataclass(slots=True)
class AnswerRecord:
    """One user submission within an attempt. Stored as JSON in
    `quiz_attempts.summary` (a list[AnswerRecord]).
    """

    question_id: int
    slot_index: int
    user_answer: str
    correct: bool | None              # None for proof/explanation pending self-assessment
    score: float                      # awarded points (after decay / penalties)
    wrong_attempts: int = 0           # count BEFORE this submission landed (for PBS decay history)
    self_assessment: str | None = None  # "got_it" | "partial" | "missed" — for non-auto-gradable
    hints_used: int = 0
    time_taken_ms: int = 0
    submitted_at: str = ""            # ISO8601 Z


@dataclass(slots=True)
class QuizSession:
    """Live run state. In-process only — lost if the app closes mid-quiz.

    Spec §10.1 PBS model is layered on the same struct:
      - non_pbs: visible_slots is length-1, current_index walks the pool.
      - pbs    : visible_slots is length-N, pool_index advances on each
                 correct submission, available_scores tracks per-question decay.
    """

    quiz_id: str
    mode: QuizMode
    config: QuizConfig
    pool: list[Question]
    started_at: datetime
    deadline: datetime | None
    visible_slots: list[Question | None]
    pool_index: int                                # next pool index to dequeue
    current_index: int                             # non-PBS: index of question in slot 0
    answers: list[AnswerRecord] = field(default_factory=list)
    available_scores: dict[int, float] = field(default_factory=dict)  # question_id → current
    wrong_counts: dict[int, int] = field(default_factory=dict)        # question_id → attempts so far
    base_scores: dict[int, float] = field(default_factory=dict)       # question_id → starting points
    finished: bool = False

@dataclass(slots=True)
class TraverseSession:
    quiz_id: str
    pool_ids: list[int]
    seen_ids: set[int]
    current_question_id: int
    started_at: datetime
