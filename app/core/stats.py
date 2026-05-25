"""Pure stats functions backing the Stats dashboard (spec §9).

Two scopes apply, and they're *different*:

- **PSet-side stats** (PSets Generated, Max Questions in a single PSet) filter by
  both subject name (literal match on `psets.subject`) AND the date range.
- **Question-side stats** (Total / Unique / Max-multiplicity / Avg-difficulty)
  are *lifetime* numbers — they ignore the date range and apply the subject
  curricular gate via topic/branch/subtopic membership.

This mirrors spec §9.1's specified SQL exactly.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any

from app.core.filters import assemble_where
from app.core.models import Subject

DateRange = tuple[str | None, str | None]  # (from_iso, to_iso); inclusive bounds


@dataclass(slots=True)
class StatsBundle:
    psets_generated: int
    total_questions_seen: int
    unique_questions_seen: int
    fraction_questions_seen: float  # percent, 0-100
    max_questions_in_single_pset: int
    max_question_multiplicity: int
    avg_question_multiplicity: float
    avg_difficulty_rating: float | None
    total_questions_in_subject: int  # exposed so the UI can render the fraction's denominator


def _pset_scope(subject: Subject | None, date_range: DateRange) -> tuple[str, list[Any]]:
    """WHERE for psets table — literal subject-name match + date range.

    psets.date_created is stored as a full ISO timestamp (`YYYY-MM-DDTHH:MM:SSZ`).
    The Stats filter dialog gives plain dates (`YYYY-MM-DD`). We compare on the
    date portion only so "to = today" includes events from earlier today.
    """
    parts: list[str] = []
    params: list[Any] = []
    if subject is not None:
        parts.append("subject = ?")
        params.append(subject.name)
    date_from, date_to = date_range
    if date_from:
        parts.append("date(date_created) >= date(?)")
        params.append(date_from)
    if date_to:
        parts.append("date(date_created) <= date(?)")
        params.append(date_to)
    return (" AND ".join(parts) if parts else "1=1"), params


def _question_scope(subject: Subject | None) -> tuple[str, list[Any]]:
    """WHERE for questions table — subject curricular gate only.

    Uses `assemble_where` with non-restrictive defaults so only the subject
    payload contributes clauses.
    """
    payload = subject.to_payload() if subject else None
    return assemble_where({"in_syllabus_only": False, "reuse_questions": True}, payload)


def compute_stats(
    conn: sqlite3.Connection,
    subject: Subject | None = None,
    date_range: DateRange = (None, None),
) -> StatsBundle:
    pset_where, pset_params = _pset_scope(subject, date_range)
    q_where, q_params = _question_scope(subject)

    psets_generated = int(
        conn.execute(f"SELECT COUNT(*) FROM psets WHERE {pset_where}", pset_params).fetchone()[0]
    )
    max_q_row = conn.execute(
        f"SELECT COALESCE(MAX(n_questions), 0) FROM psets WHERE {pset_where}", pset_params
    ).fetchone()
    max_questions_in_pset = int(max_q_row[0])

    total_seen = int(
        conn.execute(
            f"SELECT COALESCE(SUM(times_used), 0) FROM questions WHERE {q_where}", q_params
        ).fetchone()[0]
    )
    unique_seen = int(
        conn.execute(
            f"SELECT COUNT(*) FROM questions WHERE times_used > 0 AND {q_where}", q_params
        ).fetchone()[0]
    )
    total_in_subject = int(
        conn.execute(f"SELECT COUNT(*) FROM questions WHERE {q_where}", q_params).fetchone()[0]
    )
    max_multiplicity = int(
        conn.execute(
            f"SELECT COALESCE(MAX(times_used), 0) FROM questions WHERE {q_where}", q_params
        ).fetchone()[0]
    )
    avg_diff_row = conn.execute(
        f"SELECT AVG(difficulty_rating) FROM questions "
        f"WHERE times_used > 0 AND difficulty_rating IS NOT NULL AND {q_where}",
        q_params,
    ).fetchone()
    avg_difficulty = float(avg_diff_row[0]) if avg_diff_row and avg_diff_row[0] is not None else None

    fraction = (unique_seen / total_in_subject * 100.0) if total_in_subject > 0 else 0.0
    avg_mult = (total_seen / unique_seen) if unique_seen > 0 else 0.0

    return StatsBundle(
        psets_generated=psets_generated,
        total_questions_seen=total_seen,
        unique_questions_seen=unique_seen,
        fraction_questions_seen=fraction,
        max_questions_in_single_pset=max_questions_in_pset,
        max_question_multiplicity=max_multiplicity,
        avg_question_multiplicity=avg_mult,
        avg_difficulty_rating=avg_difficulty,
        total_questions_in_subject=total_in_subject,
    )


def subject_distribution(
    conn: sqlite3.Connection,
    date_range: DateRange = (None, None),
) -> list[dict[str, Any]]:
    """Pset count per `psets.subject` (uses '(no subject)' for NULL rows)."""
    parts: list[str] = []
    params: list[Any] = []
    if date_range[0]:
        parts.append("date(date_created) >= date(?)")
        params.append(date_range[0])
    if date_range[1]:
        parts.append("date(date_created) <= date(?)")
        params.append(date_range[1])
    where = " AND ".join(parts) if parts else "1=1"
    rows = conn.execute(
        f"SELECT COALESCE(subject, '(no subject)') AS s, COUNT(*) AS c "
        f"FROM psets WHERE {where} GROUP BY s ORDER BY c DESC, s",
        params,
    )
    return [{"label": r[0], "count": int(r[1])} for r in rows]


def question_multiplicity_dist(
    conn: sqlite3.Connection,
    subject: Subject | None = None,
) -> dict[int, int]:
    """Spec §5.6 — `{multiplicity: count}` for the histogram.

    For each value of `times_used > 0`, the count of questions at that level.
    Subject-scoped via the curricular gate (no date filtering — multiplicity is
    a lifetime concept).
    """
    q_where, q_params = _question_scope(subject)
    rows = conn.execute(
        f"SELECT times_used, COUNT(*) FROM questions "
        f"WHERE {q_where} AND times_used > 0 "
        f"GROUP BY times_used ORDER BY times_used",
        q_params,
    )
    return {int(r[0]): int(r[1]) for r in rows}


def calendar_heatmap(
    conn: sqlite3.Connection,
    year: int | None = None,
) -> dict[str, int]:
    """Spec §5.6 — `{date_iso: pset_count}` for the heatmap.

    `year` filters to PSets created in that calendar year. None → all years."""
    parts: list[str] = []
    params: list[Any] = []
    if year is not None:
        parts.append("strftime('%Y', date_created) = ?")
        params.append(str(year))
    where = " AND ".join(parts) if parts else "1=1"
    rows = conn.execute(
        f"SELECT date(date_created) AS d, COUNT(*) FROM psets "
        f"WHERE {where} GROUP BY d ORDER BY d",
        params,
    )
    return {r[0]: int(r[1]) for r in rows}


def activity_line(
    conn: sqlite3.Connection,
    date_range: DateRange = (None, None),
) -> list[dict[str, Any]]:
    """Spec §5.6 — `[{date, papers, questions}]` for the line chart.

    Per-day counts of psets created (`papers`) and SUM(n_questions) included
    in those psets (`questions`). One entry per day with activity; days with
    zero activity are omitted (callers fill gaps if needed for plotting)."""
    df, dt = date_range
    parts: list[str] = []
    params: list[Any] = []
    if df:
        parts.append("date(date_created) >= date(?)")
        params.append(df)
    if dt:
        parts.append("date(date_created) <= date(?)")
        params.append(dt)
    where = " AND ".join(parts) if parts else "1=1"
    rows = conn.execute(
        f"SELECT date(date_created) AS d, COUNT(*) AS papers, "
        f"COALESCE(SUM(n_questions), 0) AS qs "
        f"FROM psets WHERE {where} GROUP BY d ORDER BY d",
        params,
    )
    return [
        {"date": r[0], "papers": int(r[1]), "questions": int(r[2])}
        for r in rows
    ]


def source_attribution(
    conn: sqlite3.Connection,
    subject: Subject | None = None,
    date_range: DateRange = (None, None),
) -> list[dict[str, Any]]:
    """Per-source counts among questions the user has actually pulled into PSets
    in the selected date range — answering the braindump's "Source Fraction
    among attempted questions".

    Scope follows the **pset-side** convention: subject is matched literally on
    `psets.subject` (not the curricular gate), and the date range applies to
    `psets.date_created`. Each row in `pset_questions` contributes once — so a
    question included in two PSets shows up twice, which is the intended
    "how much of my practice came from this source" reading.

    Returns rows sorted by count descending with NULL/empty sources rolled into
    '(no source)'. `percent` is a float 0-100.
    """
    parts: list[str] = ["pq.pset_id = p.pset_id", "pq.question_id = q.question_id"]
    params: list[Any] = []
    if subject is not None:
        parts.append("p.subject = ?")
        params.append(subject.name)
    df, dt = date_range
    if df:
        parts.append("date(p.date_created) >= date(?)")
        params.append(df)
    if dt:
        parts.append("date(p.date_created) <= date(?)")
        params.append(dt)
    where = " AND ".join(parts)
    rows = conn.execute(
        f"SELECT COALESCE(NULLIF(q.source, ''), '(no source)') AS s, COUNT(*) AS c "
        f"FROM pset_questions pq, psets p, questions q "
        f"WHERE {where} "
        f"GROUP BY s ORDER BY c DESC, s",
        params,
    ).fetchall()
    total = sum(int(r[1]) for r in rows)
    if total == 0:
        return []
    return [
        {"label": r[0], "count": int(r[1]), "percent": (int(r[1]) / total) * 100.0}
        for r in rows
    ]


def topic_distribution(
    conn: sqlite3.Connection,
    subject: Subject | None,
    date_range: DateRange = (None, None),
) -> list[dict[str, Any]]:
    """Per-topic SUM(times_used) within the subject's curricular bundle.

    Date range is intentionally **not** applied here — multiplicity is a
    lifetime concept (spec §9.1). The Stats v2 line graph (Step 14) is where
    date scoping shows up for per-day activity.
    """
    _ = date_range
    q_where, q_params = _question_scope(subject)
    rows = conn.execute(
        f"SELECT topic, SUM(times_used) FROM questions "
        f"WHERE {q_where} AND times_used > 0 "
        f"GROUP BY topic ORDER BY SUM(times_used) DESC, topic",
        q_params,
    )
    return [{"label": r[0], "count": int(r[1])} for r in rows]
