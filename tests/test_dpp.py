"""Tests for the DPP greedy-MAP port (Step 22).

We don't need to verify global optimality — the algorithm is a known greedy
heuristic — but we do verify:

- Same input → same output (deterministic).
- Trivial cases (n <= k) return the full pool.
- Selection on a synthetic dataset visibly prefers vectors far apart.
- `diversity_score` correctly inverts the mean pairwise cosine.
"""

from __future__ import annotations

import numpy as np

from app.core.dpp import diversity_score, greedy_map


def _orthogonal_basis(d: int) -> np.ndarray:
    """`d × d` identity is a maximally-separated set of unit vectors."""
    return np.eye(d, dtype=np.float32)


def test_greedy_map_returns_all_when_n_le_k() -> None:
    emb = _orthogonal_basis(5)
    assert greedy_map(emb, 5) == [0, 1, 2, 3, 4]
    assert greedy_map(emb, 10) == [0, 1, 2, 3, 4]


def test_greedy_map_empty() -> None:
    assert greedy_map(np.zeros((0, 8), dtype=np.float32), 5) == []
    assert greedy_map(_orthogonal_basis(5), 0) == []


def test_greedy_map_is_deterministic() -> None:
    rng = np.random.default_rng(7)
    pool = rng.normal(size=(20, 16)).astype(np.float32)
    a = greedy_map(pool, 5)
    b = greedy_map(pool, 5)
    assert a == b


def test_greedy_map_prefers_orthogonal_vectors() -> None:
    # 4 near-identical vectors + 2 orthogonal outliers. With k=2 the first pick
    # is the argmax of an all-ones diagonal (any vector); the second must be
    # one of the orthogonal outliers since the cluster mates have already had
    # their marginal gain crushed by the Cholesky update. So we assert the
    # selected set straddles the two clusters rather than staying inside one.
    near = np.tile(np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32), (4, 1))
    near += np.random.default_rng(0).normal(scale=1e-3, size=near.shape).astype(np.float32)
    outliers = np.array(
        [[0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0]], dtype=np.float32
    )
    pool = np.vstack([near, outliers])
    picked = greedy_map(pool, 2)
    assert len(picked) == 2
    # Exactly one must be an outlier (index >= 4), and they must be distinct.
    assert any(i >= 4 for i in picked)
    assert picked[0] != picked[1]


def test_diversity_score_extremes() -> None:
    # Identical vectors → mean cos = 1 → diversity = 0.
    same = np.tile(np.array([1.0, 0.0, 0.0], dtype=np.float32), (3, 1))
    assert abs(diversity_score(same) - 0.0) < 1e-6
    # Orthogonal → mean cos = 0 → diversity = 1.
    ortho = _orthogonal_basis(3)
    assert abs(diversity_score(ortho) - 1.0) < 1e-6


def test_diversity_score_single() -> None:
    assert diversity_score(np.array([[1.0, 2.0]], dtype=np.float32)) == 1.0
    assert diversity_score(np.zeros((0, 4), dtype=np.float32)) == 1.0
