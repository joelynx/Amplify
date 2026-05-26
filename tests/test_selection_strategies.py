"""Strategy-aware `pick()` tests (Step 22).

These exercise the dispatcher + each non-random branch's fallback behaviour.
The seeded_conn fixture has no embeddings, so we attach synthetic 3072-dim
ones inline. The bare existence of strategy outputs is what we care about —
DPP/cosine correctness is covered in test_dpp.py.
"""

from __future__ import annotations

import sqlite3

import numpy as np

from app.core.selection import pick
from app.core.similarity import _VECTOR_BYTES, _VECTOR_DIM


def _set_embedding(conn: sqlite3.Connection, qid: int, vec: np.ndarray) -> None:
    blob = vec.astype("<f4").tobytes()
    assert len(blob) == _VECTOR_BYTES
    conn.execute(
        "UPDATE questions SET similarity_emb = ? WHERE question_id = ?",
        (blob, qid),
    )
    conn.commit()


def _give_distinct_embeddings(conn: sqlite3.Connection) -> None:
    """Assign each seeded question a distinct one-hot embedding so DPP /
    cosine have signal to work with."""
    rng = np.random.default_rng(0)
    qids = [int(r[0]) for r in conn.execute("SELECT question_id FROM questions").fetchall()]
    for i, qid in enumerate(qids):
        vec = rng.normal(scale=0.01, size=_VECTOR_DIM).astype("<f4")
        # Plant a "topic" axis to make this question clearly different from peers.
        vec[i] += 1.0
        _set_embedding(conn, qid, vec)


def test_random_strategy_unchanged(seeded_conn: sqlite3.Connection) -> None:
    res = pick(seeded_conn, {"reuse_questions": True}, 3)
    assert res.strategy == "random"
    assert res.diversity_score is None
    assert res.used_fallback is False
    assert len(res.questions) == 3


def test_diverse_falls_back_when_no_embeddings(seeded_conn: sqlite3.Connection) -> None:
    # Seed has no embeddings; diverse must degrade to random.
    res = pick(seeded_conn, {"reuse_questions": True}, 3, strategy="diverse")
    assert res.strategy == "diverse"
    assert res.used_fallback is True
    assert res.diversity_score is None
    assert len(res.questions) == 3


def test_diverse_with_embeddings_reports_score(seeded_conn: sqlite3.Connection) -> None:
    _give_distinct_embeddings(seeded_conn)
    res = pick(seeded_conn, {"reuse_questions": True}, 3, strategy="diverse")
    assert res.strategy == "diverse"
    assert res.used_fallback is False
    assert res.diversity_score is not None
    # Orthogonal-ish vectors → diversity should be near 1.0.
    assert res.diversity_score > 0.5
    assert len(res.questions) == 3


def test_focused_falls_back_without_embeddings(seeded_conn: sqlite3.Connection) -> None:
    res = pick(seeded_conn, {"reuse_questions": True}, 3, strategy="focused")
    assert res.strategy == "focused"
    assert res.used_fallback is True


def test_focused_clusters_around_pinned_anchor(seeded_conn: sqlite3.Connection) -> None:
    # Build a tight cluster of 3 questions sharing axis 0, plus 3 far-away
    # questions on other axes. Pin Q1 → expect the cluster mates first.
    qids = [int(r[0]) for r in seeded_conn.execute("SELECT question_id FROM questions ORDER BY question_id")]
    for i, qid in enumerate(qids):
        vec = np.zeros(_VECTOR_DIM, dtype="<f4")
        # First three share axis 0; remaining are orthogonal.
        vec[0 if i < 3 else i] = 1.0
        _set_embedding(seeded_conn, qid, vec)

    res = pick(
        seeded_conn,
        {"question_ids": [qids[0]], "reuse_questions": True, "in_syllabus_only": False},
        3,
        strategy="focused",
    )
    assert res.strategy == "focused"
    picked = {q.question_id for q in res.questions}
    assert qids[0] in picked  # the anchor itself is in the cluster
    # All three should be from the axis-0 cluster (qids[0..2]).
    assert picked.issubset(set(qids[:3]))


def test_frontier_prefers_hard_unseen(seeded_conn: sqlite3.Connection) -> None:
    # Boost q5 (off-syllabus, difficulty 9) by relaxing in_syllabus_only.
    res = pick(
        seeded_conn,
        {"reuse_questions": True, "in_syllabus_only": False},
        2,
        strategy="frontier",
    )
    assert res.strategy == "frontier"
    # qid 5 is the highest difficulty (9.0) and unused; should be in the top 2.
    assert any(q.question_id == 5 for q in res.questions)


def test_unknown_strategy_normalizes_to_random(seeded_conn: sqlite3.Connection) -> None:
    res = pick(seeded_conn, {"reuse_questions": True}, 2, strategy="banana")
    assert res.strategy == "random"
    assert len(res.questions) == 2
