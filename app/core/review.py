"""Review queue: when each practised question should come back (Low_Hanging_Fruit.md §1).

Pure: takes answer events (rows of `answer_events`) and returns per-question
state. Every event gets one outcome:

- `missed`      credit 0
- `partial`     credit between 0 and 1
- `assisted`    full credit with a hint, or the answer / solution opened first
                (a 'revealed' event has no grade and counts here too)
- `independent` full credit, no hint, nothing revealed. Hint use that was never
                recorded (NULL, answers from before migration 009) is read as
                unassisted here; the stats keep it apart as "unknown".

Scheduling is a small ladder over `INTERVALS_DAYS`. Anything short of an
independent success puts the question back at the bottom (due the next day). An
independent success climbs one rung; a question solved independently on its
first attempt starts at `FIRST_SUCCESS_STAGE` (back in a week, then three weeks).
Past the top rung it retires: no longer due. The intervals are a product
heuristic, not a research result; they live here so they can be tuned.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

Outcome = Literal["independent", "assisted", "partial", "missed"]

INTERVALS_DAYS: tuple[int, ...] = (1, 3, 7, 21)
FIRST_SUCCESS_STAGE = 2
RETIRED = len(INTERVALS_DAYS)
# An answer counts as a delayed review when the question's previous event is at
# least this old.
DELAYED_MIN = timedelta(days=1)
_EPS = 1e-9


@dataclass(slots=True, frozen=True)
class Event:
    question_id: int
    occurred_at: datetime
    kind: str  # 'answered' | 'revealed'
    credit: float | None = None
    hints_used: int | None = None
    revealed: int | None = None
    self_assessed: int | None = None
    mode: str = ""


@dataclass(slots=True)
class QuestionState:
    question_id: int
    last_outcome: Outcome
    last_at: datetime
    stage: int  # rung on INTERVALS_DAYS; RETIRED = no longer due
    due_at: datetime | None
    attempts: int = 0  # answered events (not reveals)
    independent: int = 0  # independent successes

    def is_due(self, now: datetime) -> bool:
        return self.due_at is not None and self.due_at <= now

    @property
    def is_mistake(self) -> bool:
        return self.last_outcome in ("missed", "partial")

    @property
    def needs_independent_try(self) -> bool:
        return self.last_outcome == "assisted"


def parse_time(value: str) -> datetime:
    """ISO8601 from the DB (`...Z`, `+00:00` or naive UTC) as an aware datetime."""
    s = value.strip().replace("Z", "+00:00")
    if " " in s and "T" not in s:
        s = s.replace(" ", "T", 1)
    dt = datetime.fromisoformat(s)
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def classify(e: Event) -> Outcome:
    if e.kind == "revealed":
        return "assisted"
    credit = e.credit or 0.0
    if credit <= _EPS:
        return "missed"
    if credit < 1.0 - _EPS:
        return "partial"
    if (e.hints_used or 0) > 0 or e.revealed:
        return "assisted"
    return "independent"


def assistance_known(e: Event) -> bool:
    """False for answers whose hint use was never recorded."""
    return e.kind == "revealed" or e.hints_used is not None or bool(e.revealed)


def _step(state: QuestionState | None, e: Event) -> QuestionState:
    outcome = classify(e)
    attempts = (state.attempts if state else 0) + (1 if e.kind == "answered" else 0)
    independent = (state.independent if state else 0) + (1 if outcome == "independent" else 0)
    if outcome == "independent":
        stage = FIRST_SUCCESS_STAGE if state is None else min(state.stage + 1, RETIRED)
    else:
        stage = 0
    due = None if stage >= RETIRED else e.occurred_at + timedelta(days=INTERVALS_DAYS[stage])
    return QuestionState(
        question_id=e.question_id,
        last_outcome=outcome,
        last_at=e.occurred_at,
        stage=stage,
        due_at=due,
        attempts=attempts,
        independent=independent,
    )


def schedule(
    events: Iterable[Event], dismissed: dict[int, datetime] | None = None
) -> dict[int, QuestionState]:
    """Walk each question's events in time order. Events at or before a
    question's dismissal are ignored, so a dismissed question returns only when
    it is answered again."""
    dismissed = dismissed or {}
    states: dict[int, QuestionState] = {}
    for e in sorted(events, key=lambda x: (x.occurred_at, x.question_id)):
        cut = dismissed.get(e.question_id)
        if cut is not None and e.occurred_at <= cut:
            continue
        states[e.question_id] = _step(states.get(e.question_id), e)
    return states


def queue(
    states: dict[int, QuestionState], kind: str, now: datetime | None = None
) -> list[QuestionState]:
    """The questions in one review list, in the order to practise them:
    `due` most overdue first; `mistakes` and `assisted` oldest first (the ones
    left longest are the best review)."""
    now = now or datetime.now(UTC)
    if kind == "due":
        rows = [s for s in states.values() if s.is_due(now)]
        return sorted(rows, key=lambda s: (s.due_at, s.question_id))  # type: ignore[arg-type,return-value]
    if kind == "mistakes":
        rows = [s for s in states.values() if s.is_mistake]
    elif kind == "assisted":
        rows = [s for s in states.values() if s.needs_independent_try]
    else:
        raise ValueError(f"unknown review list: {kind!r}")
    return sorted(rows, key=lambda s: (s.last_at, s.question_id))


def next_due(states: dict[int, QuestionState], now: datetime | None = None) -> datetime | None:
    now = now or datetime.now(UTC)
    upcoming = [s.due_at for s in states.values() if s.due_at is not None and s.due_at > now]
    return min(upcoming) if upcoming else None


def delayed_reviews(events: Iterable[Event]) -> list[tuple[Event, Outcome]]:
    """Answers given at least DELAYED_MIN after the question's previous event,
    with their outcome. Reveals are never reviews but do count as the previous
    event."""
    last: dict[int, datetime] = {}
    out: list[tuple[Event, Outcome]] = []
    for e in sorted(events, key=lambda x: (x.occurred_at, x.question_id)):
        prev = last.get(e.question_id)
        if e.kind == "answered" and prev is not None and e.occurred_at - prev >= DELAYED_MIN:
            out.append((e, classify(e)))
        last[e.question_id] = e.occurred_at
    return out
