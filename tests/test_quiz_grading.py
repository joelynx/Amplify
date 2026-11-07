"""Quiz flows graded from answer keys: the non-PBS runner, PBS, and the
Traverse / Discover IPC path. Auto-graded parts are locked in; parts needing
self-assessment make the submission pending until the student has seen the
expected answers and marked them."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime

import pytest

from app.core.models import Question
from app.interactive import pbs, runner
from app.interactive.models import QuizConfig, QuizSession
from app.ipc.api import Api

KEY3 = {
    "v": 1,
    "parts": [
        {"label": "a", "ask": "net work per kg of steam", "kind": "number", "value": 1236, "unit": "kJ/kg", "tol": None},
        {"label": "b", "ask": "", "kind": "choice", "value": "b", "options": 4},
        {"label": "c", "ask": "function of a cooling tower", "kind": "points",
         "points": ["rejects the condenser heat to the atmosphere", "cools the circulating water"]},
    ],
}
KEY_AUTO = {
    "v": 1,
    "parts": [
        {"label": "i", "ask": "efficiency", "kind": "number", "value": 38.6, "unit": "%", "tol": None},
        {"label": "ii", "ask": "", "kind": "truefalse", "value": True},
    ],
}


def _q(qid: int, **kw) -> Question:
    base = dict(question_id=qid, topic="T", branch="B", subtopic="S", latexcode=f"Q{qid}", latex_hash=f"h{qid}",
                in_syllabus=1, times_used=0, interactive_times_used=0, type="numerical")
    return Question(**{**base, **kw})


def _session(pool: list[Question], *, mode: str = "non_pbs", widgets: int = 1, **cfg) -> QuizSession:
    config = QuizConfig(template="PBS" if mode == "pbs" else "FREE_ANSWERING", max_points=10.0, **cfg)
    visible = list(pool[:widgets])
    return QuizSession(
        quiz_id="test", mode=mode, config=config, pool=pool, started_at=datetime.now(UTC), deadline=None,
        visible_slots=visible, pool_index=widgets, current_index=0,
        base_scores={q.question_id: 10.0 for q in pool},
        available_scores={q.question_id: 10.0 for q in visible},
    )


MULTI = _q(1, answer_key=json.dumps(KEY3), answer="(a) 1236 kJ/kg (b) (b) (c) see solution")
AUTO = _q(2, answer_key=json.dumps(KEY_AUTO))
LEGACY_NUM = _q(3, answer="12.5 kW")
LEGACY_PROOF = _q(4, answer="", type="proof", solution="The proof.")


# ---- Non-PBS runner ----------------------------------------------------------

def test_question_payload_carries_only_the_public_fields():
    d = runner._question_to_dict(MULTI)
    assert "answer" not in d and "answer_key" not in d
    assert [f["kind"] for f in d["answer_fields"]] == ["number", "choice", "points"]
    assert d["answer_fields"][0]["unit"] == "kJ/kg"
    assert "1236" not in json.dumps(d) and "condenser" not in json.dumps(d)
    assert pbs._question_to_dict(MULTI)["answer_fields"] == d["answer_fields"]


def test_single_part_numeric_is_one_call():
    s = _session([LEGACY_NUM, AUTO])
    r = runner.submit_answer(s, slot_index=0, user_answer="12.6")  # old single-string path
    assert (r["correct"], r["pending"], r["retry"], r["credit"], r["partial_score"]) == (True, False, False, 1.0, 10.0)
    assert r["parts"][0] == {"label": "", "ask": "", "kind": "number", "unit": "kW", "input": "12.6",
                             "read": "12.6", "credit": 1.0, "mark": None, "expected": "12.5", "points": []}
    assert r["replacement"]["question_id"] == AUTO.question_id
    [rec] = s.answers
    assert (rec.correct, rec.credit, rec.user_answer, rec.score) == (True, 1.0, "12.6", 10.0)


def test_multi_part_pending_then_self_assess():
    s = _session([MULTI, LEGACY_NUM])
    r = runner.submit_answer(s, slot_index=0, answers=["1.24 MJ/kg", "2", "it dumps heat"], time_taken_ms=900)
    assert (r["pending"], r["correct"], r["credit"], r["partial_score"]) == (True, None, None, 0.0)
    # every part is revealed now that the auto-graded ones are locked in
    a, b, c = r["parts"]
    assert (a["credit"], a["read"], a["expected"], a["unit"]) == (1.0, "1240", "1236", "kJ/kg")
    assert (b["credit"], b["read"], b["expected"]) == (1.0, "b", "b")
    assert (c["credit"], c["expected"], c["points"]) == (None, None, KEY3["parts"][2]["points"])
    assert r["canonical_answer"] == MULTI.answer
    assert s.answers == [] and s.current_index == 0

    # nothing else moves while the reveal is waiting for marks
    assert "error" in runner.submit_answer(s, slot_index=0, answers=["1236", "b", ""])
    assert "error" in runner.skip(s)
    assert runner.self_assess(s, marks=[None, None, None])["pending"] is True

    r = runner.self_assess(s, marks=["missed", "missed", "partial"])  # marks on auto parts are ignored
    assert r["pending"] is False and r["correct"] is False
    assert r["credit"] == pytest.approx(2.5 / 3)
    assert r["partial_score"] == pytest.approx(10 * 2.5 / 3)
    assert [p["credit"] for p in r["parts"]] == [1.0, 1.0, 0.5]
    assert [p["mark"] for p in r["parts"]] == [None, None, "partial"]
    assert r["replacement"]["question_id"] == LEGACY_NUM.question_id
    [rec] = s.answers
    assert rec.user_answer == "(a) 1.24 MJ/kg; (b) 2; (c) it dumps heat"
    assert rec.time_taken_ms == 900 and rec.self_assessment is None
    assert [p["input"] for p in rec.parts] == ["1.24 MJ/kg", "2", "it dumps heat"]
    assert rec.parts[2]["points"] == KEY3["parts"][2]["points"]
    assert "error" in runner.self_assess(s, marks=["got_it"] * 3)  # nothing pending any more


def test_wait_for_correct_holds_and_reveals_nothing():
    s = _session([MULTI, LEGACY_NUM], wait_for_correct=True)
    r = runner.submit_answer(s, slot_index=0, answers=["1000", "b", ""])
    assert (r["correct"], r["pending"], r["retry"], r["partial_score"]) == (False, False, True, 0.0)
    assert [p["credit"] for p in r["parts"]] == [0.0, 1.0, None]
    assert all(p["expected"] is None and p["points"] == [] for p in r["parts"])
    assert r["canonical_answer"] is None and r["replacement"] is None
    assert s.current_index == 0 and not s.pending and s.wrong_counts[MULTI.question_id] == 1
    # right this time: the points part is revealed for self-assessment
    r = runner.submit_answer(s, slot_index=0, answers=["1236", "b", ""])
    assert r["pending"] is True
    r = runner.self_assess(s, marks=[None, None, "got_it"])
    assert (r["correct"], r["credit"], r["partial_score"]) == (True, 1.0, 10.0)
    assert [a.score for a in s.answers] == [0.0, 10.0]


def test_old_one_call_self_assessment_still_works():
    s = _session([LEGACY_PROOF])
    r = runner.submit_answer(s, slot_index=0, user_answer="my proof", self_assessment="got_it")
    assert (r["pending"], r["correct"], r["credit"], r["finished"]) == (False, True, 1.0, True)
    assert s.answers[0].self_assessment == "got_it"


def test_reveal_includes_the_solution_when_there_is_no_checklist():
    s = _session([LEGACY_PROOF])
    r = runner.submit_answer(s, slot_index=0, user_answer="my proof")
    assert r["pending"] is True and r["solution"] == "The proof."
    r = runner.self_assess(s, marks=["partial"])
    assert (r["credit"], r["partial_score"], s.answers[0].self_assessment) == (0.5, 5.0, "partial")


def test_flush_pending_keeps_auto_credit():
    s = _session([MULTI])
    runner.submit_answer(s, slot_index=0, answers=["1236", "a", "x"])
    runner.flush_pending(s)
    [rec] = s.answers
    assert rec.credit == pytest.approx(1 / 3) and rec.score == pytest.approx(10 / 3)
    assert not s.pending


# ---- PBS ---------------------------------------------------------------------

def test_pbs_wrong_auto_part_decays_and_reveals_nothing():
    s = _session([MULTI, AUTO, LEGACY_NUM], mode="pbs", widgets=2)
    r = pbs.submit_answer(s, slot_index=0, answers=["1236", "c", "a full answer"])
    assert (r["correct"], r["pending"], r["retry"]) == (False, False, True)
    assert [p["credit"] for p in r["parts"]] == [1.0, 0.0, None]
    assert all(p["expected"] is None for p in r["parts"])
    assert r["replacement"]["question"]["question_id"] == MULTI.question_id
    assert r["replacement"]["available_score"] == 5.0
    assert not s.pending and s.answers[0].correct is False

    # auto parts right: the points part is revealed and self-assessed, then the slot is consumed
    r = pbs.submit_answer(s, slot_index=0, answers=["1.236 MJ/kg", "(b)", "a full answer"])
    assert r["pending"] is True and r["parts"][2]["points"] == KEY3["parts"][2]["points"]
    assert "error" in pbs.submit_answer(s, slot_index=0, answers=["1236", "b", ""])
    r = pbs.self_assess(s, slot_index=0, marks=[None, None, "got_it"])
    assert (r["correct"], r["credit"], r["partial_score"]) == (True, 1.0, 5.0)
    assert r["replacement"]["question"]["question_id"] == LEGACY_NUM.question_id
    assert s.answers[-1].wrong_attempts == 1


def test_pbs_partial_self_assessment_scales_the_award():
    s = _session([MULTI], mode="pbs")
    pbs.submit_answer(s, slot_index=0, answers=["1236", "2", ""])
    r = pbs.self_assess(s, slot_index=0, marks=[None, None, "missed"])
    assert r["correct"] is False and r["partial_score"] == pytest.approx(10 * 2 / 3)
    assert r["finished"] is True and r["replacement"]["question"] is None


def test_pbs_all_auto_parts_consume_at_once():
    s = _session([AUTO, LEGACY_NUM], mode="pbs")
    r = pbs.submit_answer(s, slot_index=0, answers=["38.9 %", "yes"])
    assert (r["correct"], r["pending"], r["partial_score"]) == (True, False, 10.0)
    assert r["parts"][0]["expected"] == "38.6"
    r = pbs.submit_answer(s, slot_index=0, user_answer="12500 W")  # legacy single string, converted
    assert r["correct"] is True and r["finished"] is True


def test_pbs_flush_pending_records_the_slot():
    s = _session([MULTI], mode="pbs")
    pbs.submit_answer(s, slot_index=0, answers=["1236", "b", ""])
    pbs.flush_pending(s)
    assert s.answers[0].credit == pytest.approx(2 / 3) and not s.pending


# ---- IPC: Traverse / Discover / start_quiz -----------------------------------

def _insert(conn: sqlite3.Connection, latex: str, **cols) -> int:
    cols = {"topic": "Thermo", "branch": "Cycles", "subtopic": "Rankine", "latexcode": latex,
            "type": "numerical", "in_syllabus": 1, "latex_hash": f"h-{latex}", **cols}
    conn.execute(f"INSERT INTO questions ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
                 list(cols.values()))
    conn.commit()
    return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])


def test_traverse_answers_are_graded_and_logged(seeded_conn: sqlite3.Connection):
    qid = _insert(seeded_conn, "Reheat cycle (a) (b) (c)", answer_key=json.dumps(KEY3), answer="see key")
    api = Api(lambda: seeded_conn)
    start = api.quiz_traverse_start({"question_ids": [qid], "reuse_questions": True})
    quiz_id, q = start["quiz_id"], start["question"]
    assert [f["kind"] for f in q["answer_fields"]] == ["number", "choice", "points"]
    assert "1236" not in json.dumps(q["answer_fields"])

    r = api.quiz_submit_answer(quiz_id, 0, {"question_id": qid, "answers": ["1236 kJ/kg", "a", "rejects heat"],
                                            "time_taken_ms": 1200})
    assert r["pending"] is True and "current_total" not in r
    r = api.quiz_self_assess(quiz_id, 0, {"question_id": qid, "marks": [None, None, "got_it"]})
    assert r["credit"] == pytest.approx(2 / 3) and r["current_total"] == pytest.approx(2 / 3)

    attempt_id = seeded_conn.execute("SELECT attempt_id FROM quiz_attempts WHERE quiz_id = ?", (quiz_id,)).fetchone()[0]
    attempt = api.get_quiz_attempt(attempt_id)
    [a] = attempt["answers"]
    assert attempt["total_score"] == pytest.approx(2 / 3)
    assert (a["question_id"], a["credit"], a["time_taken_ms"]) == (qid, pytest.approx(2 / 3), 1200)
    assert [p["credit"] for p in a["parts"]] == [1.0, 0.0, 1.0]
    assert a["parts"][1]["expected"] == "b"

    assert "error" in api.quiz_submit_answer(quiz_id, 0, {"answers": ["1"]})  # no question named
    assert "error" in api.quiz_submit_answer("no-such-quiz", 0, {"question_id": qid, "answers": ["1"]})


def test_discover_returns_its_quiz_id_and_grades_single_part(seeded_conn: sqlite3.Connection):
    qid = _insert(seeded_conn, "Power output?", answer="12.5 kW")
    api = Api(lambda: seeded_conn)
    res = api.quiz_discover({"question_ids": [qid], "reuse_questions": True}, 1)
    assert res["quiz_id"] and res["questions"][0]["answer_fields"] == [
        {"label": "", "ask": "", "kind": "number", "unit": "kW", "options": None, "multi": False}]
    r = api.quiz_submit_answer(res["quiz_id"], 0, {"question_id": qid, "user_answer": "12500 W"})
    assert (r["correct"], r["pending"], r["current_total"]) == (True, False, 1.0)


def test_start_quiz_submit_finish_review(seeded_conn: sqlite3.Connection):
    qid = _insert(seeded_conn, "Reheat cycle", answer_key=json.dumps(KEY3))
    api = Api(lambda: seeded_conn)
    start = api.start_quiz({"question_ids": [qid], "reuse_questions": True},
                           {"template": "FREE_ANSWERING", "n_questions": 1, "max_points": 10})
    quiz_id = start["quiz_id"]
    assert start["initial_widgets"][0]["question"]["answer_fields"][2]["kind"] == "points"
    r = api.quiz_submit_answer(quiz_id, 0, {"answers": ["1236", "b", "x"]})
    assert r["pending"] is True
    # finishing mid self-assessment keeps the auto-graded credit
    done = api.quiz_finish(quiz_id)
    assert done["summary"]["total_score"] == pytest.approx(10 * 2 / 3)
    [a] = api.get_quiz_attempt(done["attempt_id"])["answers"]
    assert [p["credit"] for p in a["parts"]] == [1.0, 1.0, 0.0]


def test_old_attempts_without_parts_still_load(seeded_conn: sqlite3.Connection):
    api = Api(lambda: seeded_conn)
    start = api.quiz_traverse_start({"question_ids": [1], "reuse_questions": True})
    old = {"answers": [{"question_id": 1, "slot_index": 0, "user_answer": "5", "correct": True, "score": 10.0,
                        "wrong_attempts": 0, "self_assessment": None, "hints_used": 0, "time_taken_ms": 0,
                        "submitted_at": ""}], "n_answers": 1}
    seeded_conn.execute("UPDATE quiz_attempts SET summary = ? WHERE quiz_id = ?", (json.dumps(old), start["quiz_id"]))
    attempt_id = seeded_conn.execute(
        "SELECT attempt_id FROM quiz_attempts WHERE quiz_id = ?", (start["quiz_id"],)).fetchone()[0]
    [a] = api.get_quiz_attempt(attempt_id)["answers"]
    assert "parts" not in a and a["score"] == 10.0
