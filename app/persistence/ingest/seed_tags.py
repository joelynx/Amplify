"""Synthesize `question_tags` rows from existing question metadata.

Spec §3.2 keeps `question_tags` as M:N; the bundled `TEST.csv` has **no**
Tags column, so the tag tray on the Generate / Browser pages currently has
nothing to filter on. This helper fills the gap by deriving tags from each
question's existing fields:

- one slug per slash-separated chunk in `subtopic`
- one slug for `type`
- one slug for `source`

All inserts use `ON CONFLICT (question_id, tag) DO NOTHING`, so re-running
is safe and only adds tags for new questions / new metadata.

Ported from the `karth/web-mvp` branch's `scripts/seed-tags.ts`. Same
slugify rules so the two ports produce identical tag values.
"""

from __future__ import annotations

import logging
import re
import sqlite3
from dataclasses import dataclass

log = logging.getLogger("amplify.ingest.seed_tags")

_APOSTROPHE_RE = re.compile(r"[\u2018\u2019\u02bc']")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
_TRIM_DASH_RE = re.compile(r"^-+|-+$")

_MAX_SLUG_CHARS = 40


def slugify(s: str) -> str:
    """Lowercase, strip apostrophes, replace runs of non-alphanum with `-`,
    trim leading/trailing dashes, cap at 40 chars. Matches the web-mvp port."""
    if not s:
        return ""
    out = s.lower()
    out = _APOSTROPHE_RE.sub("", out)
    out = _NON_ALNUM_RE.sub("-", out)
    out = _TRIM_DASH_RE.sub("", out)
    return out[:_MAX_SLUG_CHARS]


def _tags_for_row(subtopic: str, type_: str | None, source: str | None) -> set[str]:
    tags: set[str] = set()
    for chunk in (subtopic or "").split("/"):
        slug = slugify(chunk.strip())
        if slug:
            tags.add(slug)
    if type_:
        slug = slugify(type_)
        if slug:
            tags.add(slug)
    if source:
        slug = slugify(source)
        if slug:
            tags.add(slug)
    return tags


@dataclass(slots=True)
class SeedTagsResult:
    questions_scanned: int
    rows_inserted: int


def run(conn: sqlite3.Connection) -> SeedTagsResult:
    """Insert derived tags for every question. Returns (scanned, inserted).

    Inserted reflects *new* rows only (existing tags are left alone). Wrapped
    in a single transaction.
    """
    rows = list(
        conn.execute("SELECT question_id, subtopic, type, source FROM questions")
    )
    scanned = len(rows)
    inserted = 0
    try:
        for r in rows:
            qid = int(r["question_id"]) if isinstance(r, sqlite3.Row) else int(r[0])
            sub = r["subtopic"] if isinstance(r, sqlite3.Row) else r[1]
            t = r["type"] if isinstance(r, sqlite3.Row) else r[2]
            src = r["source"] if isinstance(r, sqlite3.Row) else r[3]
            for tag in _tags_for_row(sub or "", t, src):
                cur = conn.execute(
                    "INSERT INTO question_tags (question_id, tag) VALUES (?, ?) "
                    "ON CONFLICT(question_id, tag) DO NOTHING",
                    (qid, tag),
                )
                inserted += 1 if cur.rowcount > 0 else 0
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    log.info(
        "seed_tags: scanned %d questions, inserted %d new tag rows",
        scanned,
        inserted,
    )
    return SeedTagsResult(questions_scanned=scanned, rows_inserted=inserted)
