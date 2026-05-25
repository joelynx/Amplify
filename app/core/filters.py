"""Filter → SQL WHERE assembler.

Pure: takes a filters dict (shape from spec §7.1) and an optional resolved
`Subject` payload, returns `(where_sql, params)` suitable for plugging into
`SELECT ... FROM questions WHERE <where_sql>`.

Spec §7.2 semantics:
- Concept tree honors the deepest non-empty level only.
- Subject scoping is a separate gate applied on top of the form's tree.
- Tag semantics: compulsory ⊆ tags, optional ∩ tags ≠ ∅ (if optional non-empty),
  excluded ∩ tags = ∅. Compulsory ∩ excluded raises FilterError.
- min_difficulty == 0 is treated as "no restriction" (covers questions without
  a difficulty_rating; smart difficulty is Phase 2).
- in_syllabus_only defaults True (independent of subject — both gates must pass).
- reuse_questions defaults False, which restricts to `times_used = 0`.

The pure separation matters: this file is unit-testable without a DB, and
repositories own the actual SQL execution.
"""

from __future__ import annotations

from typing import Any, TypedDict


class FilterError(ValueError):
    """Raised when the filter dict is internally inconsistent (e.g. compulsory ∩ excluded ≠ ∅)."""


class TagFilters(TypedDict, total=False):
    compulsory: list[str]
    optional: list[str]
    excluded: list[str]


class Filters(TypedDict, total=False):
    subject: str | None
    topics: list[str]
    branches: list[str]
    subtopics: list[str]
    sources: list[str]
    types: list[str]
    tags: TagFilters
    min_difficulty: float
    reuse_questions: bool
    in_syllabus_only: bool


def _in_clause(col: str, values: list[str]) -> tuple[str, list[Any]]:
    placeholders = ",".join(["?"] * len(values))
    return f"{col} IN ({placeholders})", list(values)


def assemble_where(
    filters: dict[str, Any] | None,
    subject_payload: dict[str, Any] | None = None,
) -> tuple[str, list[Any]]:
    """Build the WHERE clause for `questions`. Always returns a non-empty clause
    (`1=1` when there are no filters) so callers can splice without conditionals."""
    filters = filters or {}
    parts: list[str] = []
    params: list[Any] = []

    # Subject curricular gate (spec §3.6 / §7.2). Independent of in_syllabus_only.
    if subject_payload:
        subj_topics = subject_payload.get("topics") or []
        if subj_topics:
            sql, p = _in_clause("topic", subj_topics)
            parts.append(sql)
            params.extend(p)
        for topic, branches in (subject_payload.get("excluded_branches") or {}).items():
            if branches:
                sql, p = _in_clause("branch", branches)
                parts.append(f"NOT (topic = ? AND {sql})")
                params.append(topic)
                params.extend(p)
        for topic, by_branch in (subject_payload.get("excluded_subtopics") or {}).items():
            for branch, subtopics in (by_branch or {}).items():
                if subtopics:
                    sql, p = _in_clause("subtopic", subtopics)
                    parts.append(f"NOT (topic = ? AND branch = ? AND {sql})")
                    params.append(topic)
                    params.append(branch)
                    params.extend(p)

    # Deepest non-empty level of the concept tree.
    subtopics = filters.get("subtopics") or []
    branches = filters.get("branches") or []
    topics = filters.get("topics") or []
    if subtopics:
        sql, p = _in_clause("subtopic", subtopics)
        parts.append(sql)
        params.extend(p)
    elif branches:
        sql, p = _in_clause("branch", branches)
        parts.append(sql)
        params.extend(p)
    elif topics:
        sql, p = _in_clause("topic", topics)
        parts.append(sql)
        params.extend(p)

    sources = filters.get("sources") or []
    if sources:
        sql, p = _in_clause("source", sources)
        parts.append(sql)
        params.extend(p)

    types_ = filters.get("types") or []
    if types_:
        sql, p = _in_clause("type", types_)
        parts.append(sql)
        params.extend(p)

    tags = filters.get("tags") or {}
    compulsory = tags.get("compulsory") or []
    optional = tags.get("optional") or []
    excluded = tags.get("excluded") or []
    overlap = sorted(set(compulsory) & set(excluded))
    if overlap:
        raise FilterError(f"tag(s) present in both compulsory and excluded: {overlap}")

    if compulsory:
        placeholders = ",".join(["?"] * len(compulsory))
        parts.append(
            "(SELECT COUNT(*) FROM question_tags qt "
            "WHERE qt.question_id = questions.question_id "
            f"AND qt.tag IN ({placeholders})) = ?"
        )
        params.extend(compulsory)
        params.append(len(compulsory))

    if optional:
        placeholders = ",".join(["?"] * len(optional))
        parts.append(
            "EXISTS (SELECT 1 FROM question_tags qt "
            "WHERE qt.question_id = questions.question_id "
            f"AND qt.tag IN ({placeholders}))"
        )
        params.extend(optional)

    if excluded:
        placeholders = ",".join(["?"] * len(excluded))
        parts.append(
            "NOT EXISTS (SELECT 1 FROM question_tags qt "
            "WHERE qt.question_id = questions.question_id "
            f"AND qt.tag IN ({placeholders}))"
        )
        params.extend(excluded)

    min_diff = filters.get("min_difficulty")
    if min_diff is not None and min_diff > 0:
        # NULL difficulty_rating never satisfies the inequality, which is the
        # intended behavior — questions without a rating shouldn't pass a "min
        # difficulty 5" filter.
        parts.append("difficulty_rating >= ?")
        params.append(min_diff)

    if filters.get("in_syllabus_only", True):
        parts.append("in_syllabus = 1")

    if not filters.get("reuse_questions", False):
        parts.append("times_used = 0")

    if not parts:
        return "1=1", []
    return " AND ".join(parts), params
