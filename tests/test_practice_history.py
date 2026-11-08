"""Practice history end to end (migration 009): answer events, presentation,
review queue, paper results, notes, learning stats, milestones and the
date-scoped stats."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

from app.core import learning
from app.core.stats import compute_stats, question_multiplicity_dist
from app.ipc.api import Api
from app.persistence.db import _discover_migrations


def _iso(days_ago: float = 0) -> str:
    return (datetime.now(UTC) - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _insert(conn: sqlite3.Connection, latex: str, **cols) -> int:
    cols = {"topic": "Thermo", "branch": "Cycles", "subtopic": "Rankine", "latexcode": latex,
            "type": "numerical", "in_syllabus": 1, "latex_hash": f"h-{latex}", "answer": "12.5 kW", **cols}
    conn.execute(f"INSERT INTO questions ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
                 list(cols.values()))
    conn.commit()
    return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])


def _event(conn: sqlite3.Connection, qid: int, days_ago: float, credit: float | None,
           kind: str = "answered", hints: int | None = 0) -> None:
    conn.execute(
        "INSERT INTO answer_events (question_id, mode, occurred_at, kind, credit, hints_used) "
        "VALUES (?, 'DISCOVER', ?, ?, ?, ?)",
        (qid, _iso(days_ago), kind, credit, hints),
    )
    conn.commit()


# ---- migration back-fill ------------------------------------------------------

def test_migration_backfills_answers_from_attempt_summaries() -> None:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    migrations = _discover_migrations()
    for path in migrations:
        if path.stem.startswith("009"):
            break
        conn.executescript(path.read_text(encoding="utf-8"))
    conn.execute("INSERT INTO questions (topic, branch, subtopic, latexcode, latex_hash) VALUES ('T','B','S','q','h')")
    conn.execute("INSERT INTO quizzes (quiz_id, date_created, n_questions, reuse_questions, template_name) "
                 "VALUES ('z', '2026-10-01T10:00:00Z', 3, 1, 'TRAVERSE')")
    conn.execute("INSERT INTO quiz_questions (quiz_id, question_id, question_order) VALUES ('z', 1, 1)")
    answers = [
        {"question_id": 1, "credit": 0.5, "correct": False, "self_assessment": None, "hints_used": 0,
         "submitted_at": "2026-10-01T10:05:00Z", "time_taken_ms": 900, "parts": [{"mark": "partial"}]},
        {"question_id": 1, "correct": True, "self_assessment": None, "submitted_at": ""},  # pre-answer-key record
        {"question_id": 1, "correct": None, "self_assessment": "skipped"},  # a skip: not an answer
        {"question_id": 999, "credit": 1.0},  # question gone: dropped
    ]
    conn.execute("INSERT INTO quiz_attempts (attempt_id, quiz_id, date_started, summary) VALUES (?, 'z', ?, ?)",
                 ("a", "2026-10-01T10:00:00Z", json.dumps({"answers": answers})))
    conn.executescript(next(p for p in migrations if p.stem.startswith("009")).read_text(encoding="utf-8"))
    rows = [tuple(r) for r in conn.execute(
        "SELECT credit, self_assessed, hints_used, revealed, occurred_at FROM answer_events ORDER BY event_id")]
    # Traverse never recorded hints: unknown (NULL), not "no hint".
    assert rows == [(0.5, 1, None, None, "2026-10-01T10:05:00Z"), (1.0, 0, None, None, "2026-10-01T10:00:00Z")]
    assert conn.execute("SELECT presented_at FROM quiz_questions").fetchone()[0] == "2026-10-01T10:00:00Z"


# ---- presentation, answers, reveals -------------------------------------------

def test_discover_counts_only_shown_questions(seeded_conn: sqlite3.Connection) -> None:
    ids = [_insert(seeded_conn, f"Power {i}?") for i in range(3)]
    api = Api(lambda: seeded_conn)
    res = api.quiz_discover({"question_ids": ids, "reuse_questions": True}, 3)
    shown = res["questions"][0]["question_id"]
    used = dict(seeded_conn.execute(
        f"SELECT question_id, interactive_times_used FROM questions WHERE question_id IN ({','.join('?' * 3)})", ids))
    assert used[shown] == 1 and sum(used.values()) == 1
    second = res["questions"][1]["question_id"]
    assert api.quiz_mark_presented(res["quiz_id"], second) is True
    assert api.quiz_mark_presented(res["quiz_id"], second) is False  # once only
    assert seeded_conn.execute("SELECT interactive_times_used FROM questions WHERE question_id = ?",
                               (second,)).fetchone()[0] == 1


def test_answers_and_reveals_are_logged(seeded_conn: sqlite3.Connection) -> None:
    a, b = _insert(seeded_conn, "Power A?"), _insert(seeded_conn, "Power B?")
    api = Api(lambda: seeded_conn)
    res = api.quiz_discover({"question_ids": [a, b], "reuse_questions": True}, 2)
    quiz_id = res["quiz_id"]
    api.quiz_submit_answer(quiz_id, 0, {"question_id": a, "user_answer": "12.5 kW", "hints_used": 1})
    assert api.quiz_log_reveal(quiz_id, b) is True
    assert api.quiz_log_reveal(quiz_id, b) is False
    rows = [tuple(r) for r in seeded_conn.execute(
        "SELECT question_id, mode, kind, credit, hints_used FROM answer_events ORDER BY event_id")]
    assert rows == [(a, "DISCOVER", "answered", 1.0, 1), (b, "DISCOVER", "revealed", None, None)]
    summary = api.get_review_summary(None)
    # Both need an unaided try: one used a hint, one opened the solution.
    assert summary["counts"]["assisted"] == 2 and summary["counts"]["due"] == 0


def test_slot_quiz_finish_logs_answers(seeded_conn: sqlite3.Connection) -> None:
    qid = _insert(seeded_conn, "Power slot?")
    api = Api(lambda: seeded_conn)
    start = api.start_quiz({"question_ids": [qid], "reuse_questions": True},
                           {"template": "FREE_ANSWERING", "n_questions": 1})
    api.quiz_submit_answer(start["quiz_id"], 0, {"answers": ["3 kW"]})
    api.quiz_finish(start["quiz_id"])
    assert [tuple(r) for r in seeded_conn.execute("SELECT mode, credit FROM answer_events")] == [
        ("FREE_ANSWERING", 0.0)]


# ---- review queue -------------------------------------------------------------

def test_review_session_and_dismissal(seeded_conn: sqlite3.Connection) -> None:
    a, b, c = (_insert(seeded_conn, f"R{i}", subtopic=f"S{i}") for i in range(3))
    _event(seeded_conn, a, 3, 0.0)
    _event(seeded_conn, b, 2, 0.5)
    _event(seeded_conn, c, 10, 1.0)  # independent, due after 7 days: due now
    api = Api(lambda: seeded_conn)
    summary = api.get_review_summary(None)
    assert summary["counts"] == {"due": 3, "mistakes": 2, "assisted": 0, "bookmarked": 0}
    assert summary["lists"]["mistakes"][0]["question_id"] == a  # oldest first
    assert summary["lists"]["due"][0]["topic"] == "Thermo"

    res = api.quiz_review_start(None, "mistakes", 8)
    assert {q["question_id"] for q in res["questions"]} == {a, b}
    assert seeded_conn.execute("SELECT template_name FROM quizzes WHERE quiz_id = ?",
                               (res["quiz_id"],)).fetchone()[0] == "REVIEW"
    assert api.quiz_review_start(None, "assisted", 8)["success"] is False

    api.dismiss_review(a)
    assert api.get_review_summary(None)["counts"]["mistakes"] == 1
    # Answering it again brings it back.
    _event(seeded_conn, a, -0.001, 0.0)
    assert api.get_review_summary(None)["counts"]["mistakes"] == 2


def test_review_lists_respect_the_subject(seeded_conn: sqlite3.Connection) -> None:
    a = _insert(seeded_conn, "In scope", topic="Thermo")
    b = _insert(seeded_conn, "Out of scope", topic="Optics")
    _event(seeded_conn, a, 2, 0.0)
    _event(seeded_conn, b, 2, 0.0)
    api = Api(lambda: seeded_conn)
    api.save_subject("Heat", {"topics": ["Thermo"], "excluded_branches": {}, "excluded_subtopics": {}})
    assert api.get_review_summary("Heat")["counts"]["mistakes"] == 1
    assert api.get_review_summary(None)["counts"]["mistakes"] == 2


# ---- paper results, notes -----------------------------------------------------

def test_paper_results_replace_and_feed_review(seeded_conn: sqlite3.Connection) -> None:
    a, b = _insert(seeded_conn, "P1"), _insert(seeded_conn, "P2")
    seeded_conn.execute("INSERT INTO psets (pset_id, date_created, n_questions, reuse_questions) VALUES ('p', ?, 2, 0)",
                        (_iso(1),))
    seeded_conn.executemany("INSERT INTO pset_questions (pset_id, question_id, question_order) VALUES ('p', ?, ?)",
                            [(a, 1), (b, 2)])
    seeded_conn.commit()
    api = Api(lambda: seeded_conn)
    out = api.record_paper_results("p", [{"question_id": a, "outcome": "missed"},
                                         {"question_id": b, "outcome": "solved", "assisted": True},
                                         {"question_id": 1, "outcome": "solved"}])  # not on the PSet
    assert out == {"recorded": 2}
    got = {q["question_id"]: (q["outcome"], q["assisted"]) for q in api.get_paper_results("p")["questions"]}
    assert got == {a: ("missed", False), b: ("solved", True)}
    api.record_paper_results("p", [{"question_id": a, "outcome": "partial"}, {"question_id": b, "outcome": None}])
    got = {q["question_id"]: q["outcome"] for q in api.get_paper_results("p")["questions"]}
    assert got == {a: "partial", b: None}
    assert seeded_conn.execute("SELECT COUNT(*) FROM answer_events").fetchone()[0] == 1
    assert api.get_review_summary(None)["counts"]["mistakes"] == 1


def test_notes_bookmarks_and_bookmark_filter(seeded_conn: sqlite3.Connection) -> None:
    api = Api(lambda: seeded_conn)
    api.save_question_note(2, "Why: the limit swaps with the sum by dominated convergence.")
    api.set_question_bookmark(3, True)
    notes = api.get_question_notes([2, 3, 4])
    assert notes["2"]["note"].startswith("Why") and not notes["2"]["bookmarked"]
    assert notes["3"]["bookmarked"] and notes["3"]["note"] == ""
    found = api.search_questions({"bookmarked_only": True, "reuse_questions": True, "in_syllabus_only": False})
    assert [q["question_id"] for q in found["rows"]] == [3]
    assert api.get_review_summary(None)["counts"]["bookmarked"] == 1


# ---- learning stats, milestones -----------------------------------------------

def test_learning_stats(seeded_conn: sqlite3.Connection) -> None:
    a, b, c = (_insert(seeded_conn, f"L{i}", difficulty_rating=6.0) for i in range(3))
    _event(seeded_conn, a, 5, 1.0)  # first attempt, independent
    _event(seeded_conn, a, 1, 1.0)  # delayed review, independent
    _event(seeded_conn, b, 4, 0.0)  # first attempt missed
    _event(seeded_conn, c, 2, 1.0, hints=None)  # independent, assistance unknown
    _event(seeded_conn, 1, 40, 1.0)  # outside the range below (Calculus)
    stats = learning.learning_stats(seeded_conn, None, (_iso(30)[:10], _iso(0)[:10]))
    f = stats["funnel"]
    assert (f["attempted"], f["independent"], f["independent_unknown"]) == (3, 2, 1)
    assert stats["first_attempts"] == {"n": 3, "independent": 2}
    assert stats["delayed"] == {"n": 1, "independent": 1}
    assert stats["revisit"] == 1
    thermo = next(t for t in stats["topics"] if t["topic"] == "Thermo")
    assert (thermo["in_scope"], thermo["attempted"], thermo["first_independent"]) == (3, 3, 2)
    calculus = next(t for t in stats["topics"] if t["topic"] == "Calculus")
    assert calculus["attempted"] == 0 and calculus["in_scope"] == 3  # a gap, still listed
    band = next(b for b in stats["bands"] if b["band"] == "5-10")
    assert band == {"band": "5-10", "first_attempts": 3, "first_independent": 2}


def test_reward_theme_unlocks_with_its_milestone(seeded_conn: sqlite3.Connection) -> None:
    api = Api(lambda: seeded_conn)
    sage = next(t for t in api.list_themes() if t["id"] == "sage")
    assert sage["reward"] and sage["locked"] and sage["milestone"]["target"] == 5
    with pytest.raises(ValueError):
        api.set_theme("sage")
    api.set_theme("pastel")  # built-in themes stay free
    qid = _insert(seeded_conn, "M")
    for d in (12, 10, 8, 6, 4, 2):  # five answers each a day or more after the previous one
        _event(seeded_conn, qid, d, 0.0)
    progress = {m["id"]: m for m in api.get_milestones()}
    assert progress["spaced_reviews"]["unlocked"] and progress["spaced_reviews"]["progress"] == 5
    assert not next(t for t in api.list_themes() if t["id"] == "sage")["locked"]
    api.set_theme("sage")


def test_comeback_milestone_needs_a_later_day(seeded_conn: sqlite3.Connection) -> None:
    qid = _insert(seeded_conn, "C")
    _event(seeded_conn, qid, 3, 0.0)
    _event(seeded_conn, qid, 3, 1.0)  # same day: not a comeback
    _event(seeded_conn, qid, 2, 0.5)
    _event(seeded_conn, qid, 1, 1.0)  # later day: a comeback
    assert {m["id"]: m["progress"] for m in learning.milestones(seeded_conn)}["comebacks"] == 1


# ---- lecture keywords / mixed review ------------------------------------------

def test_concept_sessions(seeded_conn: sqlite3.Connection) -> None:
    api = Api(lambda: seeded_conn)
    base = {"reuse_questions": True, "in_syllabus_only": False}
    res = api.quiz_concepts_start(base, [{"kind": "topic", "label": "Calculus"},
                                         {"kind": "topic", "label": "Linear Algebra"}], 4)
    labels = list(res["concept_labels"].values())
    assert len(res["questions"]) == 4 and labels.count("Calculus") == 2 and labels.count("Linear Algebra") == 2
    assert all(labels[i] != labels[i + 1] for i in range(3))  # interleaved
    assert api.quiz_concepts_start(base, [{"kind": "tag", "label": "induction"}], 4, "MIXED")["success"] is False
    mixed = api.quiz_concepts_start({}, [{"kind": "tag", "label": "induction"},
                                         {"kind": "tag", "label": "diagram"}], 3, "MIXED")
    assert mixed["success"] and len(mixed["questions"]) == 3  # mixed review allows reused questions
    sets = api.save_lecture_set("Monday", "calculus, linear algebra", [{"kind": "topic", "label": "Calculus"}])
    assert sets[0]["name"] == "Monday" and api.list_lecture_sets()[0]["concepts"][0]["label"] == "Calculus"
    assert api.delete_lecture_set("Monday") == []


# ---- date-scoped stats ---------------------------------------------------------

def test_question_stats_follow_the_date_range(seeded_conn: sqlite3.Connection) -> None:
    for pid, days, qids in (("old", 60, [1, 2]), ("new", 2, [2, 3])):
        seeded_conn.execute("INSERT INTO psets (pset_id, date_created, n_questions, reuse_questions) "
                            "VALUES (?, ?, ?, 0)", (pid, _iso(days), len(qids)))
        seeded_conn.executemany("INSERT INTO pset_questions (pset_id, question_id, question_order) VALUES (?, ?, ?)",
                                [(pid, q, i) for i, q in enumerate(qids)])
    seeded_conn.commit()
    recent = (_iso(30)[:10], _iso(0)[:10])
    s = compute_stats(seeded_conn, None, recent)
    assert (s.sessions_completed, s.total_questions_seen, s.unique_questions_seen) == (1, 2, 2)
    s = compute_stats(seeded_conn, None, (None, None))
    assert (s.total_questions_seen, s.unique_questions_seen, s.max_question_multiplicity) == (4, 3, 2)
    assert question_multiplicity_dist(seeded_conn, None, date_range=recent) == {1: 2}
    assert question_multiplicity_dist(seeded_conn, None) == {1: 2, 2: 1}
