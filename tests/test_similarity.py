"""Unit tests for `app/core/similarity.find_similar`.

We inject synthetic 3072-dim vectors directly onto the seeded fixture rows so
the assertions don't depend on the real seed bundle being present.
"""

from __future__ import annotations

import sqlite3

import numpy as np

from app.core.similarity import find_similar


def _vec_blob(dim: int, hot_index: int | None = None) -> bytes:
    v = np.zeros(dim, dtype="<f4")
    if hot_index is not None:
        v[hot_index] = 1.0
    return v.tobytes()


def _set_emb(conn: sqlite3.Connection, qid: int, blob: bytes | None) -> None:
    conn.execute(
        "UPDATE questions SET similarity_emb = ? WHERE question_id = ?",
        (blob, qid),
    )
    conn.commit()


def test_returns_empty_when_question_missing(seeded_conn: sqlite3.Connection):
    assert find_similar(seeded_conn, 9999, k=5) == []


def test_returns_empty_when_query_has_null_embedding(seeded_conn: sqlite3.Connection):
    # Fixture has no embeddings → all rows NULL → empty result.
    assert find_similar(seeded_conn, 1, k=5) == []


def test_top_k_orders_by_cosine_descending(seeded_conn: sqlite3.Connection):
    # Q1 = ê0, Q2 = ê0 (identical → cosine 1.0), Q3 = ê1 (orthogonal → 0).
    _set_emb(seeded_conn, 1, _vec_blob(3072, hot_index=0))
    _set_emb(seeded_conn, 2, _vec_blob(3072, hot_index=0))
    _set_emb(seeded_conn, 3, _vec_blob(3072, hot_index=1))

    hits = find_similar(seeded_conn, 1, k=10)
    assert [h.question_id for h in hits] == [2, 3]
    assert hits[0].score == 1.0
    assert abs(hits[1].score) < 1e-6  # orthogonal


def test_k_caps_results(seeded_conn: sqlite3.Connection):
    for qid in (1, 2, 3, 4):
        _set_emb(seeded_conn, qid, _vec_blob(3072, hot_index=qid % 3072))

    hits = find_similar(seeded_conn, 1, k=2)
    assert len(hits) == 2


def test_skips_null_embedding_rows_silently(seeded_conn: sqlite3.Connection):
    _set_emb(seeded_conn, 1, _vec_blob(3072, hot_index=0))
    _set_emb(seeded_conn, 2, _vec_blob(3072, hot_index=0))
    # Q3..Q6 remain NULL — they should not appear in results.
    hits = find_similar(seeded_conn, 1, k=10)
    assert [h.question_id for h in hits] == [2]


def test_skips_malformed_blob_length(seeded_conn: sqlite3.Connection):
    _set_emb(seeded_conn, 1, _vec_blob(3072, hot_index=0))
    # Q2 gets a malformed BLOB (wrong byte count) — should be skipped.
    _set_emb(seeded_conn, 2, b"\x00" * 17)
    _set_emb(seeded_conn, 3, _vec_blob(3072, hot_index=0))
    hits = find_similar(seeded_conn, 1, k=10)
    assert [h.question_id for h in hits] == [3]


def test_skips_zero_vector_candidate(seeded_conn: sqlite3.Connection):
    _set_emb(seeded_conn, 1, _vec_blob(3072, hot_index=0))
    _set_emb(seeded_conn, 2, _vec_blob(3072))  # all zeros — undefined cosine
    _set_emb(seeded_conn, 3, _vec_blob(3072, hot_index=5))
    hits = find_similar(seeded_conn, 1, k=10)
    assert [h.question_id for h in hits] == [3]


def test_returns_empty_when_query_is_zero_vector(seeded_conn: sqlite3.Connection):
    _set_emb(seeded_conn, 1, _vec_blob(3072))  # all-zero query
    _set_emb(seeded_conn, 2, _vec_blob(3072, hot_index=0))
    assert find_similar(seeded_conn, 1, k=5) == []


def test_k_zero_or_negative_returns_empty(seeded_conn: sqlite3.Connection):
    _set_emb(seeded_conn, 1, _vec_blob(3072, hot_index=0))
    _set_emb(seeded_conn, 2, _vec_blob(3072, hot_index=0))
    assert find_similar(seeded_conn, 1, k=0) == []
    assert find_similar(seeded_conn, 1, k=-3) == []
