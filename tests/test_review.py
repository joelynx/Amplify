"""Review-queue scheduling (app/core/review.py): pure, no DB."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.core.review import (
    FIRST_SUCCESS_STAGE,
    RETIRED,
    Event,
    classify,
    delayed_reviews,
    next_due,
    queue,
    schedule,
)

T0 = datetime(2026, 11, 1, 9, 0, tzinfo=UTC)


def ans(qid: int, days: float, credit: float, hints: int | None = 0, revealed: int = 0) -> Event:
    return Event(qid, T0 + timedelta(days=days), "answered", credit=credit, hints_used=hints, revealed=revealed)


def rev(qid: int, days: float) -> Event:
    return Event(qid, T0 + timedelta(days=days), "revealed", revealed=1)


def test_classify() -> None:
    assert classify(ans(1, 0, 0.0)) == "missed"
    assert classify(ans(1, 0, 0.5)) == "partial"
    assert classify(ans(1, 0, 1.0)) == "independent"
    assert classify(ans(1, 0, 1.0, hints=1)) == "assisted"
    assert classify(rev(1, 0)) == "assisted"
    # Hint use never recorded (old answers) reads as unassisted for scheduling.
    assert classify(ans(1, 0, 1.0, hints=None)) == "independent"


def test_first_independent_success_climbs_then_retires() -> None:
    s = schedule([ans(1, 0, 1.0)])[1]
    assert s.stage == FIRST_SUCCESS_STAGE and s.due_at == T0 + timedelta(days=7)
    s = schedule([ans(1, 0, 1.0), ans(1, 7, 1.0)])[1]
    assert s.due_at == T0 + timedelta(days=7 + 21)
    s = schedule([ans(1, 0, 1.0), ans(1, 7, 1.0), ans(1, 28, 1.0)])[1]
    assert s.stage == RETIRED and s.due_at is None and s.independent == 3


def test_a_miss_comes_back_tomorrow_and_climbs_from_the_bottom() -> None:
    s = schedule([ans(1, 0, 0.0)])[1]
    assert (s.stage, s.due_at, s.is_mistake) == (0, T0 + timedelta(days=1), True)
    s = schedule([ans(1, 0, 0.0), ans(1, 1, 1.0)])[1]
    assert (s.stage, s.due_at, s.is_mistake) == (1, T0 + timedelta(days=4), False)
    # A later slip drops it back to the bottom.
    s = schedule([ans(1, 0, 1.0), ans(1, 7, 0.5)])[1]
    assert (s.stage, s.last_outcome) == (0, "partial")


def test_assisted_and_revealed_need_an_independent_try() -> None:
    states = schedule([ans(1, 0, 1.0, hints=1), rev(2, 0)])
    assert states[1].needs_independent_try and states[2].needs_independent_try
    assert states[2].attempts == 0  # a reveal is not an attempt


def test_dismissal_hides_earlier_events_only() -> None:
    events = [ans(1, 0, 0.0)]
    assert schedule(events, {1: T0 + timedelta(hours=1)}) == {}
    states = schedule([*events, ans(1, 3, 0.0)], {1: T0 + timedelta(hours=1)})
    assert states[1].attempts == 1 and states[1].is_mistake


def test_queue_orders_and_next_due() -> None:
    states = schedule([ans(1, 0, 0.0), ans(2, 1, 0.0), ans(3, 0, 1.0, hints=1), ans(4, 0, 1.0)])
    now = T0 + timedelta(days=5)
    assert [s.question_id for s in queue(states, "due", now)] == [1, 3, 2]
    assert [s.question_id for s in queue(states, "mistakes", now)] == [1, 2]
    assert [s.question_id for s in queue(states, "assisted", now)] == [3]
    assert next_due(states, now) == T0 + timedelta(days=7)


def test_delayed_reviews_need_a_day_gap() -> None:
    events = [ans(1, 0, 0.0), ans(1, 0.2, 1.0), ans(1, 2, 1.0), rev(2, 0), ans(2, 1, 0.0)]
    got = [(e.question_id, o) for e, o in delayed_reviews(events)]
    assert got == [(2, "missed"), (1, "independent")]
