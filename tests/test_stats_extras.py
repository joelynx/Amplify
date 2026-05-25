"""Tests for Step 20 (source attribution) + Step 21 (trends detectors).

The seeded_conn fixture only gives us questions, not PSets — these tests
build their own pset rows in-memory to exercise the join-based stats.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta

from app.core.stats import source_attribution
from app.core.trends import detect_trends


def _add_pset(
    conn: sqlite3.Connection,
    pset_id: str,
    qids: list[int],
    *,
    subject: str | None = None,
    days_ago: int = 0,
) -> None:
    ts = (datetime.now(UTC) - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")
    conn.execute(
        "INSERT INTO psets (pset_id, date_created, subject, n_questions, reuse_questions) "
        "VALUES (?, ?, ?, ?, 0)",
        (pset_id, ts, subject, len(qids)),
    )
    for i, qid in enumerate(qids):
        conn.execute(
            "INSERT INTO pset_questions (pset_id, question_id, question_order) VALUES (?, ?, ?)",
            (pset_id, qid, i),
        )
    conn.commit()


def test_source_attribution_groups_and_percents(seeded_conn: sqlite3.Connection) -> None:
    # Seed has questions 1..6. Sources: IITD-AD (qids 1,3,4), IITK (2,6), IITM (5).
    _add_pset(seeded_conn, "p1", [1, 2, 3])
    _add_pset(seeded_conn, "p2", [3, 4])

    rows = source_attribution(seeded_conn, None, (None, None))
    by_label = {r["label"]: r for r in rows}

    # q3 appears twice -> IITD-AD: q1+q3+q3+q4 = 4, IITK: q2 = 1
    assert by_label["IITD-AD"]["count"] == 4
    assert by_label["IITK"]["count"] == 1
    total = sum(r["count"] for r in rows)
    assert total == 5
    assert abs(by_label["IITD-AD"]["percent"] - 80.0) < 1e-6


def test_source_attribution_respects_date_range(seeded_conn: sqlite3.Connection) -> None:
    _add_pset(seeded_conn, "old", [1, 2], days_ago=100)
    _add_pset(seeded_conn, "new", [3], days_ago=1)

    today = datetime.now(UTC).strftime("%Y-%m-%d")
    week_ago = (datetime.now(UTC) - timedelta(days=7)).strftime("%Y-%m-%d")

    rows = source_attribution(seeded_conn, None, (week_ago, today))
    labels = {r["label"] for r in rows}
    assert labels == {"IITD-AD"}  # q3 only


def test_source_attribution_empty_when_no_psets(seeded_conn: sqlite3.Connection) -> None:
    assert source_attribution(seeded_conn, None, (None, None)) == []


def test_trends_empty_with_no_activity(seeded_conn: sqlite3.Connection) -> None:
    # No psets and no times_used activity -> nothing to surface.
    assert detect_trends(seeded_conn, None) == []


def test_trends_topic_concentration_fires(seeded_conn: sqlite3.Connection) -> None:
    # 9 Calculus questions vs 1 Linear Algebra in last 30d -> 90% concentration.
    # Repeat the Calculus rows (qids 1,2,3) to reach the >=10 question gate.
    for i in range(3):
        _add_pset(seeded_conn, f"calc-{i}", [1, 2, 3], days_ago=i)
    _add_pset(seeded_conn, "la", [4], days_ago=0)

    insights = detect_trends(seeded_conn, None)
    ids = {i.id for i in insights}
    assert "topic_concentration" in ids
    hit = next(i for i in insights if i.id == "topic_concentration")
    # CTA should pre-fill the OTHER topic ("Linear Algebra"), not Calculus.
    assert "Linear Algebra" in hit.cta_filters["topic_list"]
    assert "Calculus" not in hit.cta_filters["topic_list"]


def test_trends_reuse_pressure(seeded_conn: sqlite3.Connection) -> None:
    # Mark 8 out of 10 questions as heavily used (times_used >= 3). Need >= 20
    # seen total to trip the gate, so add fillers.
    seeded_conn.executemany(
        "INSERT INTO questions (topic, branch, subtopic, latexcode, in_syllabus, times_used, latex_hash) "
        "VALUES ('Calculus', 'X', 'Y', ?, 1, ?, ?)",
        [(f"q{i}", 5, f"h{i}-extra") for i in range(20)],
    )
    seeded_conn.commit()

    insights = detect_trends(seeded_conn, None)
    assert any(i.id == "reuse_pressure" for i in insights)


def test_trends_caps_at_max(seeded_conn: sqlite3.Connection) -> None:
    # Stuff the DB so several detectors fire and confirm the cap holds.
    for i in range(20):
        seeded_conn.execute(
            "INSERT INTO questions (topic, branch, subtopic, latexcode, in_syllabus, times_used, latex_hash) "
            "VALUES ('Calculus', 'X', 'Y', ?, 1, ?, ?)",
            (f"f{i}", 5, f"hf{i}"),
        )
    seeded_conn.commit()
    for i in range(5):
        _add_pset(seeded_conn, f"big-{i}", [1, 2, 3], days_ago=i)

    insights = detect_trends(seeded_conn, None)
    assert len(insights) <= 5
