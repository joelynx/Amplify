"""Question selection strategies (Step 22).

Originally spec §7.4 only described `random`: a single
`SELECT ... ORDER BY RANDOM() LIMIT n` over the matching set. The post-MVP
roadmap adds three more, all layered on top of the same SQL-side filter:

| strategy   | algorithm                                                              |
| ---------- | ---------------------------------------------------------------------- |
| `random`   | uniform random (the default; unchanged).                               |
| `diverse`  | greedy MAP-DPP over `similarity_emb` to maximize concept-space spread. |
| `focused`  | nearest-neighbor cluster around an anchor (first match by default).    |
| `frontier` | rank by `difficulty_rating / (1 + times_used)` to push hardest-unseen. |

Each non-random branch first pulls a capped candidate pool via SQL (so DPP /
similarity work doesn't degenerate to O(bank²)) and falls back gracefully to
random when there aren't enough embedded candidates to do meaningful work.
"""

from __future__ import annotations

import random as _random
import sqlite3
from dataclasses import dataclass
from typing import Any, Literal

import numpy as np

from app.core.dpp import CANDIDATE_POOL_SIZE, diversity_score, greedy_map
from app.core.models import Question, Subject
from app.core.similarity import _VECTOR_BYTES, _decode
from app.persistence.repositories import questions as questions_repo

Strategy = Literal["random", "diverse", "focused", "frontier"]
_ALLOWED: tuple[Strategy, ...] = ("random", "diverse", "focused", "frontier")


@dataclass(slots=True)
class Selection:
    questions: list[Question]
    shortfall: int  # 0 when matches >= n
    # Step 22 additions — pass-through to the caller for persistence + UI.
    strategy: Strategy = "random"
    diversity_score: float | None = None  # populated for `diverse`
    used_fallback: bool = False  # True when a non-random strategy degraded


def _normalize_strategy(value: str | None) -> Strategy:
    s = (value or "random").lower()
    return s if s in _ALLOWED else "random"  # type: ignore[return-value]


def _embeddings_for(
    conn: sqlite3.Connection, ids: list[int]
) -> tuple[list[int], np.ndarray]:
    """Decode the candidate pool's similarity_emb BLOBs into a float32 matrix.

    Returns `(usable_ids, matrix)` — IDs with NULL or malformed embeddings are
    dropped, and the matrix rows align positionally with `usable_ids`.
    """
    blobs = questions_repo.fetch_similarity_embeddings(conn, ids)
    usable_ids: list[int] = []
    vectors: list[np.ndarray] = []
    for qid in ids:
        blob = blobs.get(qid)
        if blob is None or len(blob) != _VECTOR_BYTES:
            continue
        vec = _decode(blob)
        if vec is None:
            continue
        usable_ids.append(qid)
        vectors.append(vec)
    if not vectors:
        return [], np.zeros((0, 0), dtype=np.float32)
    return usable_ids, np.stack(vectors).astype(np.float32)


def _pick_random(
    conn: sqlite3.Connection,
    filters: dict[str, Any] | None,
    n: int,
    subject: Subject | None,
) -> Selection:
    picked = questions_repo.get_random(conn, filters, n, subject=subject)
    return Selection(
        questions=picked,
        shortfall=max(0, n - len(picked)),
        strategy="random",
    )


def _pick_diverse(
    conn: sqlite3.Connection,
    filters: dict[str, Any] | None,
    n: int,
    subject: Subject | None,
) -> Selection:
    candidate_ids = questions_repo.get_candidate_pool_ids(
        conn, filters, CANDIDATE_POOL_SIZE, subject=subject
    )
    if not candidate_ids:
        return Selection(questions=[], shortfall=n, strategy="diverse")
    usable_ids, matrix = _embeddings_for(conn, candidate_ids)
    if len(usable_ids) < max(2, min(n, 2)):
        # Not enough embedded candidates — degrade to random so the user
        # still gets a usable PSet. The UI surfaces `used_fallback`.
        fallback = _pick_random(conn, filters, n, subject)
        return Selection(
            questions=fallback.questions,
            shortfall=fallback.shortfall,
            strategy="diverse",
            diversity_score=None,
            used_fallback=True,
        )

    selected_indices = greedy_map(matrix, n)
    selected_ids = [usable_ids[i] for i in selected_indices]
    questions = questions_repo.fetch_by_ids(conn, selected_ids, preserve_order=True)
    selected_matrix = matrix[selected_indices]
    score = diversity_score(selected_matrix) if len(selected_indices) >= 2 else None
    return Selection(
        questions=questions,
        shortfall=max(0, n - len(questions)),
        strategy="diverse",
        diversity_score=score,
    )


def _pick_focused(
    conn: sqlite3.Connection,
    filters: dict[str, Any] | None,
    n: int,
    subject: Subject | None,
) -> Selection:
    """Nearest-neighbor cluster around an anchor.

    Anchor selection: if `filters["question_ids"]` is set we use that
    selection's centroid (multi-anchor focus, useful via "Generate from
    selection"). Otherwise we pick a random candidate as the seed. Either way
    the rest of the set is filled with the highest-cosine matches to the
    anchor centroid, in descending order.
    """
    anchor_ids: list[int] = list(filters.get("question_ids") or []) if filters else []
    # The candidate pool we'll cluster from must NOT exclude the anchors —
    # rebuild filters without the question_ids constraint so the pool is the
    # user's actual concept-space gate.
    sub_filters = dict(filters or {})
    sub_filters.pop("question_ids", None)

    candidate_ids = questions_repo.get_candidate_pool_ids(
        conn, sub_filters, CANDIDATE_POOL_SIZE, subject=subject
    )
    if not candidate_ids:
        return Selection(questions=[], shortfall=n, strategy="focused")

    usable_ids, matrix = _embeddings_for(conn, candidate_ids)
    if len(usable_ids) < 2:
        fallback = _pick_random(conn, filters, n, subject)
        return Selection(
            questions=fallback.questions,
            shortfall=fallback.shortfall,
            strategy="focused",
            used_fallback=True,
        )

    # Build the anchor centroid. If the user pinned a selection, average those
    # vectors (skipping anything without an embedding). Otherwise pick a random
    # candidate from the pool.
    if anchor_ids:
        anchor_usable, anchor_matrix = _embeddings_for(conn, anchor_ids)
        if anchor_matrix.shape[0] == 0:
            anchor_idx = _random.randrange(len(usable_ids))
            anchor_vec = matrix[anchor_idx]
        else:
            anchor_vec = anchor_matrix.mean(axis=0)
            _ = anchor_usable  # only the centroid is used
    else:
        anchor_idx = _random.randrange(len(usable_ids))
        anchor_vec = matrix[anchor_idx]

    # Unit-normalize both anchor + pool to get cosine via a single matmul.
    pool_norms = np.linalg.norm(matrix, axis=1)
    pool_safe = np.where(pool_norms > 0, pool_norms, 1.0)
    unit_pool = matrix / pool_safe[:, None]
    anchor_norm = float(np.linalg.norm(anchor_vec))
    anchor_unit = anchor_vec / (anchor_norm if anchor_norm > 0 else 1.0)
    scores = unit_pool @ anchor_unit  # cosine in [-1, 1]

    # argsort descending → take top n. Ties broken by argsort's stable order,
    # which is good enough; the candidate pool is already randomized.
    order = np.argsort(-scores)
    selected_ids = [usable_ids[int(i)] for i in order[:n]]
    questions = questions_repo.fetch_by_ids(conn, selected_ids, preserve_order=True)
    return Selection(
        questions=questions,
        shortfall=max(0, n - len(questions)),
        strategy="focused",
    )


def _pick_frontier(
    conn: sqlite3.Connection,
    filters: dict[str, Any] | None,
    n: int,
    subject: Subject | None,
) -> Selection:
    """Difficulty × novelty signal.

    `score = (difficulty_rating or 0) / (1 + times_used)` ranks
    hardest-unseen-first. A small uniform jitter (≤ 5% of the max score)
    prevents the same top-N showing up identically across runs.
    """
    candidate_ids = questions_repo.get_candidate_pool_ids(
        conn, filters, CANDIDATE_POOL_SIZE, subject=subject
    )
    if not candidate_ids:
        return Selection(questions=[], shortfall=n, strategy="frontier")

    signals = questions_repo.fetch_difficulty_signals(conn, candidate_ids)
    if not signals:
        fallback = _pick_random(conn, filters, n, subject)
        return Selection(
            questions=fallback.questions,
            shortfall=fallback.shortfall,
            strategy="frontier",
            used_fallback=True,
        )

    raw_scores: dict[int, float] = {}
    for qid, (diff, used) in signals.items():
        base = (diff if diff is not None else 0.0) / (1.0 + used)
        raw_scores[qid] = base
    max_score = max(raw_scores.values(), default=0.0)
    jitter = max_score * 0.05 if max_score > 0 else 0.05
    scored: list[tuple[float, int]] = []
    for qid, base in raw_scores.items():
        scored.append((base + _random.uniform(0.0, jitter), qid))
    scored.sort(reverse=True)
    selected_ids = [qid for _score, qid in scored[:n]]
    questions = questions_repo.fetch_by_ids(conn, selected_ids, preserve_order=True)
    return Selection(
        questions=questions,
        shortfall=max(0, n - len(questions)),
        strategy="frontier",
    )


def pick(
    conn: sqlite3.Connection,
    filters: dict[str, Any] | None,
    n: int,
    subject: Subject | None = None,
    *,
    strategy: str = "random",
) -> Selection:
    n = max(0, int(n))
    if n == 0:
        return Selection(questions=[], shortfall=0, strategy=_normalize_strategy(strategy))

    s = _normalize_strategy(strategy)
    if s == "diverse":
        return _pick_diverse(conn, filters, n, subject)
    if s == "focused":
        return _pick_focused(conn, filters, n, subject)
    if s == "frontier":
        return _pick_frontier(conn, filters, n, subject)
    return _pick_random(conn, filters, n, subject)
