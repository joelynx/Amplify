"""Learning views over the practice history (Low_Hanging_Fruit.md §1, 2, 4, 6).

- `review_summary` / `review_question_ids`: the review queue (app/core/review.py
  does the scheduling).
- `learning_stats`: the dashboard measures — first-attempt independent success,
  questions to revisit, delayed-review success, coverage by topic, reviews due —
  always with their denominators, keeping self-assessed and unknown-assistance
  answers apart from auto-graded unaided ones.
- `studied_techniques`: technique tags of questions already practised, for the
  mixed review.
- `milestones`: progress towards the theme rewards.

All read `answer_events` through practice_repo; none of them write.
"""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

from app.core.models import Subject
from app.core.review import (
    RETIRED,
    Event,
    QuestionState,
    assistance_known,
    classify,
    delayed_reviews,
    next_due,
    queue,
    schedule,
)
from app.persistence.repositories import practice as practice_repo

DateRange = tuple[str | None, str | None]
REVIEW_LISTS = ("due", "mistakes", "assisted", "bookmarked")
# Difficulty is a 0-20 heuristic (solution length, novelty, topic depth), not a
# calibrated ability scale; bands only group like with like.
DIFFICULTY_BANDS: tuple[tuple[str, float, float], ...] = (
    ("0-5", 0.0, 5.0),
    ("5-10", 5.0, 10.0),
    ("10-15", 10.0, 15.0),
    ("15-20", 15.0, 20.01),
)


def _iso(dt: datetime | None) -> str | None:
    return dt.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z") if dt else None


def _in_range(dt: datetime, date_range: DateRange) -> bool:
    d = dt.astimezone(UTC).date()
    lo, hi = date_range
    return (not lo or d >= date.fromisoformat(lo[:10])) and (not hi or d <= date.fromisoformat(hi[:10]))


def question_meta(conn: sqlite3.Connection, ids: list[int]) -> dict[int, dict[str, Any]]:
    """Topic path, difficulty and a one-line preview per question."""
    out: dict[int, dict[str, Any]] = {}
    for i in range(0, len(ids), 500):
        chunk = ids[i : i + 500]
        marks = ",".join("?" * len(chunk))
        for r in conn.execute(
            "SELECT question_id, topic, branch, subtopic, difficulty_rating, "
            f"substr(latexcode, 1, 200) FROM questions WHERE question_id IN ({marks})",
            chunk,
        ):
            out[int(r[0])] = {
                "topic": r[1],
                "branch": r[2],
                "subtopic": r[3],
                "difficulty_rating": r[4],
                "preview": " ".join((r[5] or "").split())[:160],
            }
    return out


def _states(conn: sqlite3.Connection, subject: Subject | None) -> dict[int, QuestionState]:
    return schedule(practice_repo.load_events(conn, subject), practice_repo.dismissals(conn))


# ---- review queue -----------------------------------------------------------


def review_summary(
    conn: sqlite3.Connection,
    subject: Subject | None,
    now: datetime | None = None,
    list_limit: int = 30,
) -> dict[str, Any]:
    """Counts and the first `list_limit` questions of each review list."""
    now = now or datetime.now(UTC)
    states = _states(conn, subject)
    lists = {kind: queue(states, kind, now) for kind in ("due", "mistakes", "assisted")}
    bookmarked = practice_repo.bookmarked_ids(conn, subject)
    shown = {s.question_id for rows in lists.values() for s in rows[:list_limit]} | set(bookmarked[:list_limit])
    meta = question_meta(conn, sorted(shown))

    def row(s: QuestionState) -> dict[str, Any]:
        return {
            "question_id": s.question_id,
            **meta.get(s.question_id, {}),
            "last_outcome": s.last_outcome,
            "last_at": _iso(s.last_at),
            "due_at": _iso(s.due_at),
            "attempts": s.attempts,
        }

    return {
        "counts": {
            "due": len(lists["due"]),
            "mistakes": len(lists["mistakes"]),
            "assisted": len(lists["assisted"]),
            "bookmarked": len(bookmarked),
        },
        "next_due": _iso(next_due(states, now)),
        "tracked": len(states),
        "retired": sum(1 for s in states.values() if s.stage >= RETIRED),
        "lists": {
            **{kind: [row(s) for s in rows[:list_limit]] for kind, rows in lists.items()},
            "bookmarked": [
                {"question_id": q, **meta.get(q, {}), **(row(states[q]) if q in states else {})}
                for q in bookmarked[:list_limit]
            ],
        },
    }


def review_question_ids(
    conn: sqlite3.Connection,
    subject: Subject | None,
    kind: str,
    n: int,
    now: datetime | None = None,
) -> list[int]:
    """The next `n` questions of one review list, in practice order."""
    if kind not in REVIEW_LISTS:
        raise ValueError(f"unknown review list: {kind!r}")
    if kind == "bookmarked":
        return practice_repo.bookmarked_ids(conn, subject)[: max(0, n)]
    return [s.question_id for s in queue(_states(conn, subject), kind, now)[: max(0, n)]]


# ---- dashboard measures -----------------------------------------------------


def _exposure(conn: sqlite3.Connection, subject: Subject | None, date_range: DateRange) -> tuple[int, int]:
    """(generated, presented) question slots in the range: quiz questions created
    vs actually shown, plus questions on PSets (a printed sheet is both)."""
    clause, gate = practice_repo.subject_question_clause(subject)
    lo, hi = date_range

    def ranged(col: str) -> tuple[str, list[Any]]:
        parts, params = [], []
        if lo:
            parts.append(f"date({col}) >= date(?)")
            params.append(lo)
        if hi:
            parts.append(f"date({col}) <= date(?)")
            params.append(hi)
        return (" AND ".join(parts) or "1=1"), params

    w, p = ranged("z.date_created")
    generated = conn.execute(
        f"SELECT COUNT(*) FROM quiz_questions qq JOIN quizzes z ON z.quiz_id = qq.quiz_id "
        f"WHERE {w} AND qq.{clause}",
        [*p, *gate],
    ).fetchone()[0]
    w, p = ranged("qq.presented_at")
    presented = conn.execute(
        f"SELECT COUNT(*) FROM quiz_questions qq WHERE qq.presented_at IS NOT NULL AND {w} AND qq.{clause}",
        [*p, *gate],
    ).fetchone()[0]
    w, p = ranged("ps.date_created")
    printed = conn.execute(
        f"SELECT COUNT(*) FROM pset_questions pq JOIN psets ps ON ps.pset_id = pq.pset_id "
        f"WHERE {w} AND pq.{clause}",
        [*p, *gate],
    ).fetchone()[0]
    return int(generated) + int(printed), int(presented) + int(printed)


def _band(difficulty: float | None) -> str | None:
    if difficulty is None:
        return None
    for label, lo, hi in DIFFICULTY_BANDS:
        if lo <= difficulty < hi:
            return label
    return None


def learning_stats(
    conn: sqlite3.Connection,
    subject: Subject | None,
    date_range: DateRange = (None, None),
    now: datetime | None = None,
) -> dict[str, Any]:
    """The learning panel: quizzes and recorded paper results together. "First
    attempt" is a question's first event ever (a reveal counts, so opening the
    solution first is never an independent first attempt); it is counted in the
    range when that event falls in it."""
    now = now or datetime.now(UTC)
    events = practice_repo.load_events(conn, subject)
    ranged = [e for e in events if _in_range(e.occurred_at, date_range)]
    answered = [e for e in ranged if e.kind == "answered"]

    first: dict[int, Event] = {}
    for e in events:
        first.setdefault(e.question_id, e)
    firsts = [e for e in first.values() if _in_range(e.occurred_at, date_range)]
    delayed = [(e, o) for e, o in delayed_reviews(events) if _in_range(e.occurred_at, date_range)]
    latest: dict[int, Event] = {}
    for e in ranged:
        latest[e.question_id] = e

    meta = question_meta(conn, sorted({e.question_id for e in events}))

    def topic(q: int) -> str:
        return meta.get(q, {}).get("topic") or "(unknown)"

    clause, gate = practice_repo.subject_question_clause(subject)
    in_scope = {
        r[0]: int(r[1])
        for r in conn.execute(f"SELECT topic, COUNT(*) FROM questions WHERE {clause} GROUP BY topic", gate)
    }

    rows: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "attempted": set(),
            "independent": set(),
            "independent_self": set(),
            "first_attempts": 0,
            "first_independent": 0,
            "revisit": set(),
            "delayed": 0,
            "delayed_success": 0,
            "difficulty": [],
        }
    )
    for e in answered:
        t = rows[topic(e.question_id)]
        t["attempted"].add(e.question_id)
        if classify(e) == "independent":
            t["independent"].add(e.question_id)
            if e.self_assessed:
                t["independent_self"].add(e.question_id)
    for e in firsts:
        t = rows[topic(e.question_id)]
        t["first_attempts"] += 1
        t["first_independent"] += int(e.kind == "answered" and classify(e) == "independent")
    for q, e in latest.items():
        if classify(e) != "independent":
            rows[topic(q)]["revisit"].add(q)
    for e, o in delayed:
        t = rows[topic(e.question_id)]
        t["delayed"] += 1
        t["delayed_success"] += int(o == "independent")
    for q in {e.question_id for e in answered}:
        d = meta.get(q, {}).get("difficulty_rating")
        if d is not None:
            rows[topic(q)]["difficulty"].append(float(d))

    topics_out = []
    for name in sorted(set(in_scope) | set(rows)):
        t = rows.get(name)
        if t is None:
            topics_out.append({"topic": name, "in_scope": in_scope.get(name, 0), "attempted": 0,
                               "independent": 0, "independent_self": 0, "first_attempts": 0,
                               "first_independent": 0, "revisit": 0, "delayed": 0,
                               "delayed_success": 0, "avg_difficulty": None})
            continue
        diffs = t["difficulty"]
        topics_out.append(
            {
                "topic": name,
                "in_scope": in_scope.get(name, 0),
                "attempted": len(t["attempted"]),
                "independent": len(t["independent"]),
                "independent_self": len(t["independent_self"]),
                "first_attempts": t["first_attempts"],
                "first_independent": t["first_independent"],
                "revisit": len(t["revisit"]),
                "delayed": t["delayed"],
                "delayed_success": t["delayed_success"],
                "avg_difficulty": round(sum(diffs) / len(diffs), 1) if diffs else None,
            }
        )
    topics_out.sort(key=lambda r: (-r["attempted"], -r["in_scope"], r["topic"]))

    bands: dict[str, dict[str, int]] = {label: {"first_attempts": 0, "first_independent": 0}
                                        for label, _, _ in DIFFICULTY_BANDS}
    for e in firsts:
        b = _band(meta.get(e.question_id, {}).get("difficulty_rating"))
        if b:
            bands[b]["first_attempts"] += 1
            bands[b]["first_independent"] += int(e.kind == "answered" and classify(e) == "independent")

    independent_events = [e for e in answered if classify(e) == "independent"]
    generated, presented = _exposure(conn, subject, date_range)
    states = schedule(events, practice_repo.dismissals(conn))
    return {
        "funnel": {
            "generated": generated,
            "presented": presented,
            "attempted": len({e.question_id for e in answered}),
            "assisted": len({e.question_id for e in ranged if classify(e) == "assisted"}),
            "independent": len({e.question_id for e in independent_events}),
            "independent_self": len({e.question_id for e in independent_events if e.self_assessed}),
            "independent_unknown": len(
                {e.question_id for e in independent_events if not assistance_known(e)}
            ),
        },
        "first_attempts": {
            "n": len(firsts),
            "independent": sum(1 for e in firsts if e.kind == "answered" and classify(e) == "independent"),
        },
        "delayed": {"n": len(delayed), "independent": sum(1 for _, o in delayed if o == "independent")},
        "revisit": sum(1 for e in latest.values() if classify(e) != "independent"),
        "reviews": {
            "due": len(queue(states, "due", now)),
            "mistakes": len(queue(states, "mistakes", now)),
            "assisted": len(queue(states, "assisted", now)),
            "next_due": _iso(next_due(states, now)),
        },
        "topics": topics_out,
        "bands": [{"band": label, **bands[label]} for label, _, _ in DIFFICULTY_BANDS],
    }


# ---- techniques for mixed review -------------------------------------------


def studied_techniques(conn: sqlite3.Connection, subject: Subject | None) -> list[dict[str, Any]]:
    """Technique tags (key / supporting) in scope: how many questions carry each,
    how many of those were practised and when last. Practised first."""
    clause, gate = practice_repo.subject_question_clause(subject)
    practised = {
        r[0]: (int(r[1]), r[2])
        for r in conn.execute(
            "SELECT qt.tag, COUNT(DISTINCT e.question_id), MAX(e.occurred_at) "
            "FROM answer_events e JOIN question_tags qt ON qt.question_id = e.question_id "
            f"WHERE qt.role IN ('key', 'supporting') AND e.{clause} GROUP BY qt.tag",
            gate,
        )
    }
    out = []
    for tag, role, n in conn.execute(
        "SELECT tag, MIN(role), COUNT(DISTINCT question_id) FROM question_tags "
        f"WHERE role IN ('key', 'supporting') AND {clause} GROUP BY tag",
        gate,
    ):
        done, last = practised.get(tag, (0, None))
        out.append({"tag": tag, "role": role, "available": int(n), "practised": done, "last_at": last})
    out.sort(key=lambda r: (-r["practised"], -r["available"], r["tag"]))
    return out


# ---- milestones (theme rewards) --------------------------------------------


@dataclass(slots=True, frozen=True)
class Milestone:
    id: str
    title: str
    description: str
    target: int
    theme_id: str


# Rewards follow the practice loop: spaced reviews, fixing old mistakes, and
# honest attempts at anything (so hard material still pays). Generating PDFs or
# leaving the app open earns nothing.
MILESTONES: tuple[Milestone, ...] = (
    Milestone(
        "spaced_reviews",
        "Spaced reviewer",
        "Answer 5 questions again at least a day after you last saw them.",
        5,
        "sage",
    ),
    Milestone(
        "comebacks",
        "Comeback",
        "On a later day, solve 3 questions on your own that you had missed or half-solved.",
        3,
        "ember",
    ),
    Milestone(
        "honest_attempts",
        "Honest effort",
        "Answer 25 questions without opening the answer or solution first. Any result counts.",
        25,
        "midnight",
    ),
)


def _comebacks(events: list[Event]) -> int:
    prev: dict[int, Event] = {}
    n = 0
    for e in events:
        p = prev.get(e.question_id)
        if (
            p is not None
            and e.kind == "answered"
            and classify(e) == "independent"
            and classify(p) in ("missed", "partial")
            and e.occurred_at.date() > p.occurred_at.date()
        ):
            n += 1
        if e.kind == "answered":
            prev[e.question_id] = e
    return n


def milestones(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    events = practice_repo.load_events(conn, None)
    progress = {
        "spaced_reviews": len(delayed_reviews(events)),
        "comebacks": _comebacks(events),
        "honest_attempts": sum(1 for e in events if e.kind == "answered"),
    }
    return [
        {
            "id": m.id,
            "title": m.title,
            "description": m.description,
            "target": m.target,
            "progress": min(progress[m.id], m.target),
            "unlocked": progress[m.id] >= m.target,
            "theme_id": m.theme_id,
        }
        for m in MILESTONES
    ]


def locked_themes(conn: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    """Reward themes not yet earned, with their milestone."""
    return {m["theme_id"]: m for m in milestones(conn) if not m["unlocked"]}
