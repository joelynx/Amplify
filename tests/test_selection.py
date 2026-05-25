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


# --- §7.2 edge cases: combined categories (Step 9 lock-in) -----------------
#
# Fixture tags by row (conftest.py):
#   Limits      → ["induction"]
#   Continuity  → ["induction", "diagram"]
#   Riemann     → ["coloring"]               (out-of-syllabus? no — used=1)
#   Diagonal    → ["diagram"]
#   Spectral    → ["off-syllabus"]            (out-of-syllabus, used=0)
#   Orthogonal  → []
#
# These tests use `reuse_questions: True` + `in_syllabus_only: False` so the
# default filters don't mask the tag semantics under test.


def test_compulsory_plus_optional_combined(seeded_conn: sqlite3.Connection):
    # induction compulsory AND (coloring OR diagram) → only Continuity matches.
    n = questions_repo.count_matching(
        seeded_conn,
        {
            "tags": {"compulsory": ["induction"], "optional": ["coloring", "diagram"]},
            "in_syllabus_only": False,
            "reuse_questions": True,
        },
    )
    assert n == 1


def test_compulsory_plus_excluded_combined(seeded_conn: sqlite3.Connection):
    # induction compulsory AND NOT diagram → only Limits matches (Continuity has diagram).
    n = questions_repo.count_matching(
        seeded_conn,
        {
            "tags": {"compulsory": ["induction"], "excluded": ["diagram"]},
            "in_syllabus_only": False,
            "reuse_questions": True,
        },
    )
    assert n == 1


def test_compulsory_optional_and_excluded(seeded_conn: sqlite3.Connection):
    # induction compulsory, (coloring | diagram) optional, off-syllabus excluded.
    # Limits has induction but no coloring/diagram → fails optional.
    # Continuity has induction + diagram, no off-syllabus → matches.
    n = questions_repo.count_matching(
        seeded_conn,
        {
            "tags": {
                "compulsory": ["induction"],
                "optional": ["coloring", "diagram"],
                "excluded": ["off-syllabus"],
            },
            "in_syllabus_only": False,
            "reuse_questions": True,
        },
    )
    assert n == 1


def test_spec_example_compulsory_and_optional(seeded_conn: sqlite3.Connection):
    """Spec §7.2 / dev cycle Step 9 walk: "Mathematical Induction & Invariants
    compulsory, Coloring/Diagram optional".

    Maps to our fixture as: induction+diagram both compulsory, coloring optional
    — i.e. a question must carry BOTH compulsory tags AND have at least one
    optional. Only Continuity has both induction and diagram; it doesn't have
    coloring, so the optional clause filters it out.
    """
    n = questions_repo.count_matching(
        seeded_conn,
        {
            "tags": {
                "compulsory": ["induction", "diagram"],
                "optional": ["coloring"],
            },
            "in_syllabus_only": False,
            "reuse_questions": True,
        },
    )
    assert n == 0  # Continuity has the compulsory pair but no `coloring`.

    # Sanity: drop the optional clause and Continuity comes back.
    n_no_optional = questions_repo.count_matching(
        seeded_conn,
        {
            "tags": {"compulsory": ["induction", "diagram"]},
            "in_syllabus_only": False,
            "reuse_questions": True,
        },
    )
    assert n_no_optional == 1


def test_unknown_tag_in_any_category_yields_zero(seeded_conn: sqlite3.Connection):
    """A tag that doesn't exist anywhere should not match — exercising the
    "no-match" surface so the API behaves predictably under user typos."""
    n_comp = questions_repo.count_matching(
        seeded_conn,
        {
            "tags": {"compulsory": ["nonexistent_tag"]},
            "in_syllabus_only": False,
            "reuse_questions": True,
        },
    )
    assert n_comp == 0
    n_opt = questions_repo.count_matching(
        seeded_conn,
        {
            "tags": {"optional": ["nonexistent_tag"]},
            "in_syllabus_only": False,
            "reuse_questions": True,
        },
    )
    assert n_opt == 0


def test_empty_tag_categories_match_everything_else_being_equal(
    seeded_conn: sqlite3.Connection,
):
    """Empty compulsory + empty optional + empty excluded → tag clause is a no-op."""
    n = questions_repo.count_matching(
        seeded_conn,
        {
            "tags": {"compulsory": [], "optional": [], "excluded": []},
            "in_syllabus_only": False,
            "reuse_questions": True,
        },
    )
    assert n == 6  # all six fixture rows


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


# --- Step 10: remaining filter surface verification ---------------------


def test_sources_filter_selects_correct_set(seeded_conn: sqlite3.Connection):
    """sources=[IITD-AD] → Limits + Riemann + Diagonal (3 rows)."""
    n = questions_repo.count_matching(
        seeded_conn,
        {"sources": ["IITD-AD"], "in_syllabus_only": False, "reuse_questions": True},
    )
    assert n == 3


def test_sources_multiselect_unions(seeded_conn: sqlite3.Connection):
    n = questions_repo.count_matching(
        seeded_conn,
        {"sources": ["IITD-AD", "IITK"], "in_syllabus_only": False, "reuse_questions": True},
    )
    # IITD-AD (Limits, Riemann, Diagonal) + IITK (Continuity, Orthogonal) = 5
    assert n == 5


def test_types_filter_selects_correct_set(seeded_conn: sqlite3.Connection):
    """types=[proof] → Limits + Riemann (2 rows)."""
    n = questions_repo.count_matching(
        seeded_conn,
        {"types": ["proof"], "in_syllabus_only": False, "reuse_questions": True},
    )
    assert n == 2


def test_types_multiselect_unions(seeded_conn: sqlite3.Connection):
    n = questions_repo.count_matching(
        seeded_conn,
        {
            "types": ["proof", "explanation"],
            "in_syllabus_only": False,
            "reuse_questions": True,
        },
    )
    # proof: 2 (Limits, Riemann); explanation: 1 (Orthogonal) → 3
    assert n == 3


def test_min_difficulty_drops_null_ratings(seeded_conn: sqlite3.Connection):
    """Spec §7.2: SQL inequality on NULL is NULL, so NULL-rated rows are
    excluded when min_difficulty > 0. We null out one row and confirm."""
    seeded_conn.execute(
        "UPDATE questions SET difficulty_rating = NULL WHERE subtopic = 'Limits'"
    )
    seeded_conn.commit()
    n = questions_repo.count_matching(
        seeded_conn,
        {"min_difficulty": 1, "in_syllabus_only": False, "reuse_questions": True},
    )
    # 6 fixture rows, Limits now NULL → 5 remain ≥ 1.
    assert n == 5


def test_reuse_questions_combined_with_subject(seeded_conn: sqlite3.Connection):
    subj = Subject(name="Calc", topics=["Calculus"])
    # Calculus rows: Limits, Continuity (used=0), Riemann (used=1).
    # reuse=false drops Riemann → 2.
    n = questions_repo.count_matching(
        seeded_conn,
        {"in_syllabus_only": False, "reuse_questions": False},
        subject=subj,
    )
    assert n == 2


def test_in_syllabus_only_is_independent_of_subject(seeded_conn: sqlite3.Connection):
    """Dev cycle Step 10: "Cover the case where the active subject includes a
    topic but a row has in_syllabus = 0 (it should not match)."

    Spectral is Linear Algebra / Eigen with in_syllabus=0. Subject "LA"
    includes Linear Algebra entirely — so the curricular gate alone lets
    Spectral through. The in_syllabus_only flag is a second independent gate
    that must also pass.
    """
    la = Subject(name="LA", topics=["Linear Algebra"])
    # Both gates open → all 3 LA rows.
    n_open = questions_repo.count_matching(
        seeded_conn, {"in_syllabus_only": False, "reuse_questions": True}, subject=la
    )
    assert n_open == 3
    # in_syllabus_only=True drops Spectral (in_syllabus=0) → 2.
    n_gated = questions_repo.count_matching(
        seeded_conn, {"in_syllabus_only": True, "reuse_questions": True}, subject=la
    )
    assert n_gated == 2


def test_dynamic_sources_reflect_filter_context(seeded_conn: sqlite3.Connection):
    """spec §7.3 — sources dropdown re-queries with the rest of the filter set."""
    rows = questions_repo.distinct_sources(
        seeded_conn,
        {"topics": ["Linear Algebra"], "in_syllabus_only": False, "reuse_questions": True},
    )
    assert set(rows) == {"IITD-AD", "IITM", "IITK"}


def test_dynamic_types_reflect_filter_context(seeded_conn: sqlite3.Connection):
    """topic=Linear Algebra → only numerical + explanation reachable; no proof."""
    rows = questions_repo.distinct_types(
        seeded_conn,
        {"topics": ["Linear Algebra"], "in_syllabus_only": False, "reuse_questions": True},
    )
    assert "proof" not in rows
    assert set(rows) == {"numerical", "explanation"}
