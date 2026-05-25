"""Brute-force cosine similarity over the BLOB-stored `similarity_emb` column.

Spec §15 / §12. The runtime never generates embeddings — it only reads the
ones the seed bundle ships. Augmented rows (CSV path) have NULL embeddings
and are skipped silently here.

Performance: at the spec's <100k row cap this is a single pass over the table
with one 3072-float dot product per row. Numpy keeps each comparison in tight
C code, so even unindexed brute force lands at sub-second latency for the
seed sizes we target.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Final

import numpy as np

_VECTOR_DIM: Final = 3072
_VECTOR_BYTES: Final = _VECTOR_DIM * 4  # float32


@dataclass(slots=True, frozen=True)
class SimilarityHit:
    question_id: int
    score: float  # cosine in [-1, 1]


def _decode(blob: bytes | memoryview | None) -> np.ndarray | None:
    """Decode a BLOB into a 3072-element float32 vector, or None if malformed."""
    if blob is None:
        return None
    raw = bytes(blob)
    if len(raw) != _VECTOR_BYTES:
        return None
    return np.frombuffer(raw, dtype="<f4")


def _norm(v: np.ndarray) -> float:
    return float(np.linalg.norm(v))


def find_similar(
    conn: sqlite3.Connection,
    question_id: int,
    k: int = 10,
) -> list[SimilarityHit]:
    """Top-k most similar questions to `question_id` by cosine on `similarity_emb`.

    Returns an empty list when the query question is missing, has a NULL
    embedding, or has a degenerate (all-zero) vector. Skips augmented (NULL)
    candidate rows silently.
    """
    if k <= 0:
        return []

    row = conn.execute(
        "SELECT similarity_emb FROM questions WHERE question_id = ?",
        (question_id,),
    ).fetchone()
    if row is None:
        return []
    query = _decode(row[0])
    if query is None:
        return []
    qn = _norm(query)
    if qn == 0.0:
        return []
    qn_inv = 1.0 / qn

    scored: list[tuple[float, int]] = []
    cur = conn.execute(
        "SELECT question_id, similarity_emb FROM questions "
        "WHERE similarity_emb IS NOT NULL AND question_id != ?",
        (question_id,),
    )
    for qid, blob in cur:
        cand = _decode(blob)
        if cand is None:
            continue
        cn = _norm(cand)
        if cn == 0.0:
            continue
        # cos(θ) = (a · b) / (|a| |b|)
        score = float(np.dot(query, cand) * qn_inv / cn)
        scored.append((score, int(qid)))

    scored.sort(reverse=True)
    return [SimilarityHit(question_id=qid, score=s) for s, qid in scored[:k]]
