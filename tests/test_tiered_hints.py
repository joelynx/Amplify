"""Tiered hints (migration 012): `hints` is the first tier, `more_hints` a JSON
array of up to two more; the quiz reveals them one at a time and counts the
tiers opened before answering as `hints_used`."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime

import pytest

from app.core.models import MAX_HINT_TIERS, Question, hint_tiers
from app.interactive import runner, session_manager
from app.interactive.models import QuizConfig, QuizSession
from app.ipc.api import Api, _question_full_dict
from app.persistence.repositories import questions as questions_repo

THREE = json.dumps(["Which quantity stays fixed?", "Write the energy balance for the turbine alone."])


@pytest.mark.parametrize(
    ("hints", "more", "want"),
    [
        (None, None, []),
        ("  ", THREE, []),  # no first hint: no hints at all
        ("Look at the ends.", None, ["Look at the ends."]),
        ("Look at the ends.", "", ["Look at the ends."]),
        ("Look at the ends.", "not json", ["Look at the ends."]),
        ("Look at the ends.", '{"a": 1}', ["Look at the ends."]),
        ("Look at the ends.", '["", 3, "Pair them up."]', ["Look at the ends.", "Pair them up."]),
        ("A", THREE, ["A", *json.loads(THREE)]),
        ("A", json.dumps(["B", "C", "D", "E"]), ["A", "B", "C"]),
    ],
)
def test_hint_tiers(hints: str | None, more: str | None, want: list[str]) -> None:
    assert hint_tiers(hints, more) == want
    assert len(hint_tiers(hints, more)) <= MAX_HINT_TIERS


def _insert(conn: sqlite3.Connection, latex: str, **cols) -> int:
    cols = {"topic": "Thermo", "branch": "Cycles", "subtopic": "Rankine", "latexcode": latex,
            "type": "numerical", "in_syllabus": 1, "latex_hash": f"h-{latex}", "answer": "12.5 kW", **cols}
    conn.execute(f"INSERT INTO questions ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
                 list(cols.values()))
    conn.commit()
    return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])


def test_repository_and_quiz_payloads_carry_the_tiers(seeded_conn: sqlite3.Connection) -> None:
    qid = _insert(seeded_conn, "Rankine work?", hints="Start at the boiler.", more_hints=THREE)
    q = questions_repo.get_by_id(seeded_conn, qid)
    assert q is not None and q.more_hints == THREE
    tiers = ["Start at the boiler.", *json.loads(THREE)]
    assert q.hint_tiers() == tiers
    assert _question_full_dict(q)["hint_tiers"] == tiers
    assert runner._question_to_dict(q)["hint_tiers"] == tiers

    res = Api(lambda: seeded_conn).quiz_discover({"question_ids": [qid], "reuse_questions": True}, 1)
    assert res["questions"][0]["hint_tiers"] == tiers


def test_old_rows_have_one_tier(seeded_conn: sqlite3.Connection) -> None:
    qid = _insert(seeded_conn, "Old row?", hints="Use the steam tables.")
    q = questions_repo.get_by_id(seeded_conn, qid)
    assert q is not None and q.more_hints is None
    assert q.hint_tiers() == ["Use the steam tables."]


def _q(qid: int, **kw) -> Question:
    base = dict(question_id=qid, topic="T", branch="B", subtopic="S", latexcode=f"Q{qid}", latex_hash=f"h{qid}",
                in_syllabus=1, times_used=0, interactive_times_used=0, type="numerical")
    return Question(**{**base, **kw})


def test_request_hint_walks_the_tiers(seeded_conn: sqlite3.Connection) -> None:
    q = _q(1, hints="A", more_hints=json.dumps(["B", "C"]))
    session = QuizSession(
        quiz_id="tiers", mode="non_pbs", config=QuizConfig(template="FREE_ANSWERING", max_points=10.0),
        pool=[q], started_at=datetime.now(UTC), deadline=None, visible_slots=[q], pool_index=1,
        current_index=0, base_scores={1: 10.0}, available_scores={1: 10.0},
    )
    session_manager.register(session)
    api = Api(lambda: seeded_conn)
    assert api.quiz_request_hint("tiers", 0) == {"hint": "A", "hint_index": 1, "hint_count": 3}
    assert api.quiz_request_hint("tiers", 0, 3) == {"hint": "C", "hint_index": 3, "hint_count": 3}
    assert api.quiz_request_hint("tiers", 0, 4) == {"hint": None, "hint_index": 0, "hint_count": 3}
    assert api.quiz_request_hint("missing", 0) == {"hint": None, "hint_index": 0, "hint_count": 0}


def test_hints_used_counts_the_tiers_opened(seeded_conn: sqlite3.Connection) -> None:
    qid = _insert(seeded_conn, "Tiered?", hints="A", more_hints=json.dumps(["B", "C"]))
    api = Api(lambda: seeded_conn)
    res = api.quiz_discover({"question_ids": [qid], "reuse_questions": True}, 1)
    api.quiz_submit_answer(res["quiz_id"], 0, {"question_id": qid, "user_answer": "12.5 kW", "hints_used": 3})
    used = seeded_conn.execute("SELECT hints_used FROM answer_events WHERE question_id = ?", (qid,)).fetchone()[0]
    assert used == 3
