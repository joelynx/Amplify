"""End-to-end tests for the filter + selection path against the in-memory fixture."""

from __future__ import annotations

import sqlite3

import pytest

from app.core.filters import FilterError
from app.core.models import Subject
from app.core.selection import pick
from app.persistence.repositories import questions as questions_repo


def test_count_matching_default_fresh_in_syllabus(seeded_conn: sqlite3.Connection):
    """Defaults filter to in-syllabus, unused questions. 5 of 6 fixtures satisfy."""
    n = questions_repo.count_matching(seeded_conn, {})
    # Spectral row is out-of-syllabus; Riemann row has times_used=1 so dropped by default.
    assert n == 4


def test_count_matching_includes_used_when_reuse_true(seeded_conn: sqlite3.Connection):
    n = questions_repo.count_matching(seeded_conn, {"reuse_questions": True})
    # Out-of-syllabus row still excluded; Riemann now included.
    assert n == 5


def test_count_matching_includes_off_syllabus(seeded_conn: sqlite3.Connection):
    n = questions_repo.count_matching(
        seeded_conn, {"in_syllabus_only": False, "reuse_questions": True}
    )
    assert n == 6


def test_count_matching_topic_filter(seeded_conn: sqlite3.Connection):
    n = questions_repo.count_matching(
        seeded_conn,
        {"topics": ["Calculus"], "in_syllabus_only": False, "reuse_questions": True},
    )
    assert n == 3


def test_count_matching_subtopic_overrides_topic(seeded_conn: sqlite3.Connection):
    n = questions_repo.count_matching(
        seeded_conn,
        {
            "topics": ["Calculus"],
            "branches": ["Differential"],
            "subtopics": ["Continuity"],
            "in_syllabus_only": False,
            "reuse_questions": True,
        },
    )
    assert n == 1


def test_count_matching_compulsory_all_required(seeded_conn: sqlite3.Connection):
    n = questions_repo.count_matching(
        seeded_conn,
        {
            "tags": {"compulsory": ["induction", "diagram"]},
            "in_syllabus_only": False,
            "reuse_questions": True,
        },
    )
    # Only the Continuity row has BOTH tags.
    assert n == 1


def test_count_matching_optional_any(seeded_conn: sqlite3.Connection):
    n = questions_repo.count_matching(
        seeded_conn,
        {
            "tags": {"optional": ["induction", "coloring"]},
            "in_syllabus_only": False,
            "reuse_questions": True,
        },
    )
    # Rows tagged induction (Limits, Continuity) or coloring (Riemann) — 3 total.
    assert n == 3


def test_count_matching_excluded_removes(seeded_conn: sqlite3.Connection):
    n = questions_repo.count_matching(
        seeded_conn,
        {
            "tags": {"excluded": ["off-syllabus"]},
            "in_syllabus_only": False,
            "reuse_questions": True,
        },
    )
    assert n == 5


def test_count_matching_min_difficulty(seeded_conn: sqlite3.Connection):
    n = questions_repo.count_matching(
        seeded_conn,
        {"min_difficulty": 5, "in_syllabus_only": False, "reuse_questions": True},
    )
    # Continuity(5), Riemann(7), Spectral(9) — three rows ≥ 5.
    assert n == 3


def test_count_matching_with_subject_curricular_gate(seeded_conn: sqlite3.Connection):
    subj = Subject(
        name="Math I",
        topics=["Calculus"],
        excluded_branches={"Calculus": ["Integral"]},
    )
    n = questions_repo.count_matching(
        seeded_conn,
        {"in_syllabus_only": False, "reuse_questions": True},
        subject=subj,
    )
    # Calculus rows minus the Integral branch (Riemann) → Limits, Continuity.
    assert n == 2


def test_pick_returns_shortfall_when_undersized(seeded_conn: sqlite3.Connection):
    sel = pick(seeded_conn, {"topics": ["Linear Algebra"]}, 10)
    # 3 LA rows, 1 out-of-syllabus, 0 used → 2 fresh in-syllabus rows. Want 10 → short 8.
    assert len(sel.questions) == 2
    assert sel.shortfall == 8


def test_pick_returns_exact_count_when_enough(seeded_conn: sqlite3.Connection):
    sel = pick(seeded_conn, {"in_syllabus_only": False, "reuse_questions": True}, 3)
    assert len(sel.questions) == 3
    assert sel.shortfall == 0


def test_pick_includes_tags_on_returned_questions(seeded_conn: sqlite3.Connection):
    sel = pick(seeded_conn, {"reuse_questions": True}, 10)
    cont = next((q for q in sel.questions if q.subtopic == "Continuity"), None)
    assert cont is not None
    assert set(cont.tags) == {"induction", "diagram"}


def test_compulsory_excluded_overlap_raises(seeded_conn: sqlite3.Connection):
    with pytest.raises(FilterError):
        questions_repo.count_matching(
            seeded_conn,
            {"tags": {"compulsory": ["induction"], "excluded": ["induction"]}},
        )


def test_distinct_topics(seeded_conn: sqlite3.Connection):
    topics = questions_repo.distinct_topics(seeded_conn, subject=None, in_syllabus_only=False)
    assert topics == ["Calculus", "Linear Algebra"]


def test_concept_tree_shape(seeded_conn: sqlite3.Connection):
    tree = questions_repo.concept_tree(seeded_conn, subject=None, in_syllabus_only=False)
    assert set(tree.keys()) == {"Calculus", "Linear Algebra"}
    assert set(tree["Calculus"].keys()) == {"Differential", "Integral"}
    assert tree["Calculus"]["Differential"] == ["Continuity", "Limits"]
