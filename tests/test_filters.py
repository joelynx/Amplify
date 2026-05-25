"""Unit tests for `app/core/filters.assemble_where` — no DB required."""

from __future__ import annotations

import re

import pytest

from app.core.filters import FilterError, assemble_where


def _has(where: str, fragment: str) -> bool:
    """Word-boundary substring match — keeps `topic IN` from matching `subtopic IN`."""
    return re.search(rf"(?:^|[\s(]){re.escape(fragment)}", where) is not None


def test_empty_filters_returns_tautology():
    where, params = assemble_where({"in_syllabus_only": False, "reuse_questions": True})
    assert where == "1=1"
    assert params == []


def test_default_filters_apply_in_syllabus_and_times_used():
    """An empty filter dict still applies the spec's defaults: in_syllabus_only=True
    and reuse_questions=False — i.e. "fresh in-syllabus questions only"."""
    where, params = assemble_where({})
    assert "in_syllabus = 1" in where
    assert "times_used = 0" in where
    assert params == []


def test_deepest_level_only_subtopics_then_branches_then_topics():
    where, params = assemble_where(
        {
            "topics": ["Calculus"],
            "branches": ["Differential"],
            "subtopics": ["Limits", "Continuity"],
            "in_syllabus_only": False,
            "reuse_questions": True,
        },
    )
    # Subtopics win; topic/branch IN clauses are absent.
    assert _has(where, "subtopic IN (?,?)")
    assert not _has(where, "topic IN")
    assert not _has(where, "branch IN")
    assert params == ["Limits", "Continuity"]


def test_branches_used_when_subtopics_empty():
    where, params = assemble_where(
        {
            "topics": ["Calculus"],
            "branches": ["Differential"],
            "in_syllabus_only": False,
            "reuse_questions": True,
        },
    )
    assert _has(where, "branch IN (?)")
    assert not _has(where, "topic IN")
    assert params == ["Differential"]


def test_topics_used_when_branches_and_subtopics_empty():
    where, params = assemble_where(
        {"topics": ["Calculus", "Linear Algebra"], "in_syllabus_only": False, "reuse_questions": True},
    )
    assert _has(where, "topic IN (?,?)")
    assert params == ["Calculus", "Linear Algebra"]


def test_subject_payload_applies_curricular_gate():
    payload = {
        "topics": ["Calculus"],
        "excluded_branches": {"Calculus": ["Differential"]},
        "excluded_subtopics": {"Linear Algebra": {"Eigen": ["Spectral"]}},
    }
    where, params = assemble_where(
        {"in_syllabus_only": False, "reuse_questions": True}, subject_payload=payload
    )
    assert _has(where, "topic IN (?)")
    assert "NOT (topic = ? AND branch IN (?))" in where
    assert "NOT (topic = ? AND branch = ? AND subtopic IN (?))" in where
    assert params == ["Calculus", "Calculus", "Differential", "Linear Algebra", "Eigen", "Spectral"]


def test_compulsory_tags_use_count_subquery():
    where, params = assemble_where(
        {
            "tags": {"compulsory": ["induction", "diagram"]},
            "in_syllabus_only": False,
            "reuse_questions": True,
        }
    )
    assert "SELECT COUNT(*) FROM question_tags" in where
    assert params == ["induction", "diagram", 2]


def test_optional_tags_use_exists_subquery():
    where, params = assemble_where(
        {"tags": {"optional": ["a", "b"]}, "in_syllabus_only": False, "reuse_questions": True},
    )
    assert "EXISTS (SELECT 1 FROM question_tags" in where
    assert "NOT EXISTS" not in where
    assert params == ["a", "b"]


def test_excluded_tags_use_not_exists():
    where, params = assemble_where(
        {"tags": {"excluded": ["off-syllabus"]}, "in_syllabus_only": False, "reuse_questions": True},
    )
    assert "NOT EXISTS (SELECT 1 FROM question_tags" in where
    assert params == ["off-syllabus"]


def test_compulsory_and_excluded_overlap_raises():
    with pytest.raises(FilterError) as exc:
        assemble_where(
            {"tags": {"compulsory": ["x", "y"], "excluded": ["y", "z"]}},
        )
    assert "y" in str(exc.value)


def test_min_difficulty_zero_imposes_no_restriction():
    where, _ = assemble_where(
        {"min_difficulty": 0, "in_syllabus_only": False, "reuse_questions": True},
    )
    assert "difficulty_rating" not in where


def test_min_difficulty_positive_filters():
    where, params = assemble_where(
        {"min_difficulty": 5, "in_syllabus_only": False, "reuse_questions": True},
    )
    assert "difficulty_rating >= ?" in where
    assert params == [5]


def test_in_syllabus_only_default_true_independent_of_subject():
    where, _ = assemble_where({"reuse_questions": True})
    assert "in_syllabus = 1" in where


def test_reuse_questions_false_restricts_to_unused():
    where, _ = assemble_where({"in_syllabus_only": False})
    assert "times_used = 0" in where


def test_reuse_questions_true_drops_times_used_filter():
    where, _ = assemble_where({"in_syllabus_only": False, "reuse_questions": True})
    assert "times_used" not in where


def test_sources_and_types_use_in():
    where, params = assemble_where(
        {
            "sources": ["IITD-AD", "IITK"],
            "types": ["proof"],
            "in_syllabus_only": False,
            "reuse_questions": True,
        }
    )
    assert _has(where, "source IN (?,?)")
    assert _has(where, "type IN (?)")
    assert params == ["IITD-AD", "IITK", "proof"]
