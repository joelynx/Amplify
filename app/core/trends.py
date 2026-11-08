"""Pattern detectors for the Stats "Trends" panel (Step 21).

Each detector is a small pure-ish function that reads from SQLite and either
returns an `Insight` or `None`. The registry at the bottom is the only place
that needs to grow when new detectors are added. Order matters — earlier
insights are shown first in the UI, and `detect_trends` caps the surfaced
list at `_MAX_INSIGHTS`.

Every detector takes the Stats page's mode: "generate" reads PSet usage
(`pset_questions` by PSet date, `times_used`), "quiz" reads quiz usage (shown
`quiz_questions` by `presented_at`, `interactive_times_used`). CTAs open the
matching page (`cta_target`): Generate, Quiz, or a review session.

Detectors are intentionally cheap (single SQL query, small Python loop) so
the panel can refresh on every Stats page visit without caching.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from app.core.filters import assemble_where
from app.core.models import Subject
from app.core.review import parse_time, queue, schedule
from app.persistence.repositories import practice as practice_repo

# Hard caps so the panel never goes wider than the eye can scan.
_MAX_INSIGHTS = 5
_RECENT_DAYS = 30
_STALE_WINDOW_FROM = 90
_STALE_WINDOW_TO = 30
# Reuse is unproductive when a question keeps coming back although it was
# already solved independently twice, or when its last three uses were
# crammed into less than this window.
_MASSED_WINDOW = timedelta(days=7)

# Each detector returns Insights with one of these IDs. Kept here so callers
# can dedupe / hide specific rules without grepping strings across the file.
INSIGHT_IDS = {
    "reviews_due",
    "topic_concentration",
    "tag_concentration_more",
    "tag_concentration_switch",
    "stale_topic",
    "reuse_pressure",
    "coverage_gap",
}


@dataclass(slots=True)
class Insight:
    """One row in the Trends panel.

    `cta_filters` is a `TemplatePayload`-shaped partial — the frontend feeds
    it straight into `navigate("/generate" | "/quiz", { state: { template } })`,
    reusing the same plumbing History's "Generate similar" uses. Only the
    fields the user should land on need to be set; missing fields default in
    the form. For `cta_target == "review"` it holds `{"kind": <review list>}`.
    """

    id: str
    title: str
    body: str
    cta_label: str
    cta_filters: dict[str, Any] = field(default_factory=dict)
    cta_target: str = "generate"  # "generate" | "quiz" | "review"


# --- helpers --------------------------------------------------------------

def _question_scope(subject: Subject | None) -> tuple[str, list[Any]]:
    """Subject curricular gate only, mirroring stats._question_scope."""
    payload = subject.to_payload() if subject else None
    return assemble_where({"in_syllabus_only": False, "reuse_questions": True}, payload)


def _uses(mode: str) -> tuple[str, str, str]:
    """(FROM with the use row `u` and its session `p`, date column, extra
    condition) for one row per question use."""
    if mode == "quiz":
        return "quiz_questions u JOIN quizzes p ON p.quiz_id = u.quiz_id", "u.presented_at", "u.presented_at IS NOT NULL"
    return "pset_questions u JOIN psets p ON p.pset_id = u.pset_id", "p.date_created", "1=1"


def _used_col(mode: str) -> str:
    return "interactive_times_used" if mode == "quiz" else "times_used"


def _target(mode: str) -> str:
    return "quiz" if mode == "quiz" else "generate"


def _build_template_payload(
    subject: Subject | None,
    *,
    topics: list[str] | None = None,
    compulsory_tags: list[str] | None = None,
    excluded_tags: list[str] | None = None,
    reuse_questions: bool | None = None,
) -> dict[str, Any]:
    """Minimal TemplatePayload-shaped dict for the CTA pre-fill.

    Only sets the fields a particular insight cares about. The Generate form
    fills the rest with defaults when keys are missing.
    """
    payload: dict[str, Any] = {
        "name": "",
        "subject": subject.name if subject else None,
        "topic_list": list(topics or []),
        "branch_list": [],
        "subtopic_list": [],
        "type_list": [],
        "source_list": [],
        "tag_list": {
            "compulsory": list(compulsory_tags or []),
            "optional": [],
            "excluded": list(excluded_tags or []),
        },
        "n_questions": 10,
        "reuse_questions": bool(reuse_questions) if reuse_questions is not None else False,
        "include_sources": True,
        "in_syllabus_only": True,
        "min_difficulty": None,
        "save_directory": None,
        "solutions": None,
    }
    return payload


# --- detectors ------------------------------------------------------------

def _reviews_due(conn: sqlite3.Connection, subject: Subject | None, mode: str) -> Insight | None:
    """Questions whose review is due (app/core/review.py). The most useful next
    step, so it comes first."""
    states = schedule(practice_repo.load_events(conn, subject), practice_repo.dismissals(conn))
    due = queue(states, "due")
    if not due:
        return None
    n = len(due)
    return Insight(
        id="reviews_due",
        title=f"{n} question{'s' if n != 1 else ''} due for review",
        body="Coming back to them after a gap is what makes them stick. A short review takes a few minutes.",
        cta_label="Start a short review",
        cta_filters={"kind": "due"},
        cta_target="review",
    )


def _topic_concentration(conn: sqlite3.Connection, subject: Subject | None, mode: str) -> Insight | None:
    """Fires when one topic accounts for >=70% of recent (last 30d) uses.
    CTA pre-fills the OTHER in-subject topics so the user can branch out.
    """
    src, dcol, cond = _uses(mode)
    parts: list[str] = [cond, f"date({dcol}) >= date('now', ?)"]
    params: list[Any] = [f"-{_RECENT_DAYS} days"]
    if subject is not None:
        parts.append("p.subject = ?")
        params.append(subject.name)
    rows = conn.execute(
        f"SELECT q.topic AS t, COUNT(*) AS c FROM {src} JOIN questions q ON q.question_id = u.question_id "
        f"WHERE {' AND '.join(parts)} GROUP BY t ORDER BY c DESC",
        params,
    ).fetchall()
    total = sum(int(r["c"]) for r in rows)
    if total < 10 or not rows:
        return None
    top_topic, top_count = rows[0]["t"], int(rows[0]["c"])
    if top_count / total < 0.7:
        return None

    # CTA pre-fills the *other* topics in the subject (or globally) so the form
    # opens with a "branch out" filter ready to go.
    where, par = _question_scope(subject)
    other_topics = [
        r[0] for r in conn.execute(
            f"SELECT DISTINCT topic FROM questions WHERE {where} AND topic != ? ORDER BY topic",
            [*par, top_topic],
        ).fetchall()
    ]
    if not other_topics:
        return None
    pct = round(top_count / total * 100)
    return Insight(
        id="topic_concentration",
        title=f"{pct}% of recent practice was {top_topic}",
        body=(
            f"Out of {total} questions practiced in the last {_RECENT_DAYS} days, "
            f"{top_count} came from {top_topic}. Want to branch out?"
        ),
        cta_label="Branch out",
        cta_filters=_build_template_payload(subject, topics=other_topics),
        cta_target=_target(mode),
    )


def _tag_concentration(conn: sqlite3.Connection, subject: Subject | None, mode: str) -> list[Insight]:
    """Fires when one tag dominates recent practice (>=40% of tag occurrences).
    Emits two CTAs: "More like this" (compulsory) and "Switch it up" (excluded).
    """
    src, dcol, cond = _uses(mode)
    parts: list[str] = [cond, f"date({dcol}) >= date('now', ?)"]
    params: list[Any] = [f"-{_RECENT_DAYS} days"]
    if subject is not None:
        parts.append("p.subject = ?")
        params.append(subject.name)
    rows = conn.execute(
        f"SELECT qt.tag AS t, COUNT(*) AS c FROM {src} JOIN question_tags qt ON qt.question_id = u.question_id "
        f"WHERE {' AND '.join(parts)} GROUP BY t ORDER BY c DESC",
        params,
    ).fetchall()
    total = sum(int(r["c"]) for r in rows)
    if total < 15 or not rows:
        return []
    top_tag, top_count = rows[0]["t"], int(rows[0]["c"])
    if top_count / total < 0.4:
        return []
    pct = round(top_count / total * 100)
    return [
        Insight(
            id="tag_concentration_more",
            title=f"You've been drilling \"{top_tag}\"",
            body=(
                f"{pct}% of tagged questions in the last {_RECENT_DAYS} days carry "
                f"the {top_tag} tag — keep the streak going?"
            ),
            cta_label="More like this",
            cta_filters=_build_template_payload(subject, compulsory_tags=[top_tag]),
            cta_target=_target(mode),
        ),
        Insight(
            id="tag_concentration_switch",
            title=f"Or break out of \"{top_tag}\"",
            body="Skip questions carrying that tag for a refresher set.",
            cta_label="Switch it up",
            cta_filters=_build_template_payload(subject, excluded_tags=[top_tag]),
            cta_target=_target(mode),
        ),
    ]


def _stale_topic(conn: sqlite3.Connection, subject: Subject | None, mode: str) -> Insight | None:
    """A topic active 30–90d ago but cold in the last 30d. CTA refreshes it."""
    if subject is None:
        return None  # only meaningful inside a subject's curricular scope
    src, dcol, cond = _uses(mode)
    base = f"FROM {src} JOIN questions q ON q.question_id = u.question_id WHERE {cond} AND p.subject = ?"

    older = {
        r["t"]: int(r["c"])
        for r in conn.execute(
            f"SELECT q.topic AS t, COUNT(*) AS c {base} "
            f"AND date({dcol}) >= date('now', ?) AND date({dcol}) < date('now', ?) GROUP BY t",
            [subject.name, f"-{_STALE_WINDOW_FROM} days", f"-{_STALE_WINDOW_TO} days"],
        ).fetchall()
    }
    recent = {
        r["t"]: int(r["c"])
        for r in conn.execute(
            f"SELECT q.topic AS t, COUNT(*) AS c {base} AND date({dcol}) >= date('now', ?) GROUP BY t",
            [subject.name, f"-{_STALE_WINDOW_TO} days"],
        ).fetchall()
    }
    stale = [(t, c) for t, c in older.items() if recent.get(t, 0) == 0 and c >= 3]
    if not stale:
        return None
    stale.sort(key=lambda x: -x[1])
    topic = stale[0][0]
    return Insight(
        id="stale_topic",
        title=f"{topic} has gone quiet",
        body=(
            f"You practiced {stale[0][1]} {topic} questions 30-90 days ago but "
            f"none in the last 30. Brush it up?"
        ),
        cta_label="Refresh",
        cta_filters=_build_template_payload(subject, topics=[topic]),
        cta_target=_target(mode),
    )


def _reuse_pressure(conn: sqlite3.Connection, subject: Subject | None, mode: str) -> Insight | None:
    """Repetition is only a problem when it is unproductive. Of the questions
    used 3+ times, count those that are not review material (no open mistake,
    no assisted attempt, not due) and either were already solved independently
    twice or had their last three uses crammed into under a week. Fires when
    those are >=30% of the questions seen. Spaced returns to missed questions
    are review, and never count."""
    where, params = _question_scope(subject)
    col = _used_col(mode)
    seen = int(conn.execute(
        f"SELECT COUNT(*) FROM questions WHERE {where} AND {col} > 0", params
    ).fetchone()[0])
    if seen < 20:
        return None
    heavy = [
        int(r[0])
        for r in conn.execute(f"SELECT question_id FROM questions WHERE {where} AND {col} >= 3", params)
    ]
    if len(heavy) / seen < 0.3:
        return None

    now = datetime.now(UTC)
    states = schedule(practice_repo.load_events(conn, subject), practice_repo.dismissals(conn))
    src, dcol, cond = _uses(mode)
    uses: dict[int, list[datetime]] = {}
    for i in range(0, len(heavy), 500):
        chunk = heavy[i : i + 500]
        marks = ",".join("?" * len(chunk))
        for qid, when in conn.execute(
            f"SELECT u.question_id, {dcol} FROM {src} WHERE {cond} AND u.question_id IN ({marks})", chunk
        ):
            if when:
                uses.setdefault(int(qid), []).append(parse_time(when))

    def unproductive(qid: int) -> bool:
        st = states.get(qid)
        if st is not None and (st.is_mistake or st.needs_independent_try or st.is_due(now)):
            return False
        if st is not None and st.independent >= 2:
            return True
        last3 = sorted(uses.get(qid, []))[-3:]
        return len(last3) == 3 and last3[-1] - last3[0] < _MASSED_WINDOW

    wasted = sum(1 for q in heavy if unproductive(q))
    if wasted / seen < 0.3:
        return None
    pct = round(wasted / seen * 100)
    return Insight(
        id="reuse_pressure",
        title="Some repetition isn't paying off",
        body=(
            f"{pct}% of the questions you've seen keep coming back although you already "
            f"solved them, or came back within a week. Spaced reviews of missed questions "
            f"are worth it; for the rest, try a fresh set."
        ),
        cta_label="Fresh only",
        cta_filters=_build_template_payload(subject, reuse_questions=False),
        cta_target=_target(mode),
    )


def _coverage_gap(conn: sqlite3.Connection, subject: Subject | None, mode: str) -> Insight | None:
    """When the user has seen <25% of the active subject's bank, nudge them
    toward unseen questions."""
    if subject is None:
        return None  # coverage is a per-subject concept
    where, params = _question_scope(subject)
    col = _used_col(mode)
    total = int(conn.execute(f"SELECT COUNT(*) FROM questions WHERE {where}", params).fetchone()[0])
    if total < 50:
        return None
    seen = int(conn.execute(
        f"SELECT COUNT(*) FROM questions WHERE {where} AND {col} > 0", params
    ).fetchone()[0])
    if total == 0 or seen / total >= 0.25:
        return None
    pct = round(seen / total * 100)
    return Insight(
        id="coverage_gap",
        title=f"You've seen {pct}% of {subject.name}",
        body=(
            f"{seen} of {total} questions explored. Lots of unseen ground — "
            f"a reuse-disabled set will go straight for the gaps."
        ),
        cta_label="Explore unseen",
        cta_filters=_build_template_payload(subject, reuse_questions=False),
        cta_target=_target(mode),
    )


# --- registry + entry point ----------------------------------------------

# Returns either an Insight, None, or a list — flattened by detect_trends.
Detector = Callable[[sqlite3.Connection, Subject | None, str], Insight | list[Insight] | None]

_REGISTRY: list[Detector] = [
    _reviews_due,
    _topic_concentration,
    _tag_concentration,
    _stale_topic,
    _reuse_pressure,
    _coverage_gap,
]


def detect_trends(
    conn: sqlite3.Connection, subject: Subject | None = None, mode: str = "generate"
) -> list[Insight]:
    """Run every detector, flatten, dedupe by id, cap at _MAX_INSIGHTS."""
    mode = "quiz" if mode == "quiz" else "generate"
    out: list[Insight] = []
    seen: set[str] = set()
    for fn in _REGISTRY:
        try:
            result = fn(conn, subject, mode)
        except Exception:
            # A detector misfiring shouldn't take down the whole panel.
            continue
        if result is None:
            continue
        items = result if isinstance(result, list) else [result]
        for item in items:
            if item.id in seen:
                continue
            seen.add(item.id)
            out.append(item)
            if len(out) >= _MAX_INSIGHTS:
                return out
    return out


# Re-export for typing parity with the IPC layer that asdict()s these.
__all__ = ["Insight", "INSIGHT_IDS", "detect_trends", "asdict"]
