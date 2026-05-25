"""Random question selection.

Spec §7.4: a single `SELECT ... ORDER BY RANDOM() LIMIT n` over the matching set.
If fewer than `n` questions match, the caller surfaces a "shortfall" so the UI
can warn the user instead of silently undershooting.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any

from app.core.models import Question, Subject
from app.persistence.repositories import questions as questions_repo


@dataclass(slots=True)
class Selection:
    questions: list[Question]
    shortfall: int  # 0 when matches >= n


def pick(
    conn: sqlite3.Connection,
    filters: dict[str, Any] | None,
    n: int,
    subject: Subject | None = None,
) -> Selection:
    n = max(0, int(n))
    if n == 0:
        return Selection(questions=[], shortfall=0)
    picked = questions_repo.get_random(conn, filters, n, subject=subject)
    return Selection(questions=picked, shortfall=max(0, n - len(picked)))
