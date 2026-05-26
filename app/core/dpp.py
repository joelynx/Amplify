"""Determinantal Point Process — greedy MAP for diverse subset selection.

Port of the web-mvp `lib/dpp.ts` reference algorithm (Kulesza & Taskar, 2012)
to numpy. Given N candidate items with embedding vectors, pick a subset of
size k that approximately maximizes log det of the cosine-similarity
submatrix. Deterministic: same candidate pool + same k always returns the
same selection.

Complexity is O(k * n^2). At n=200, k=10 that's ~400k ops, well under 10ms.
Never run this on the full question bank — pre-filter via SQL first and cap
the candidate pool with `CANDIDATE_POOL_SIZE`.
"""

from __future__ import annotations

from typing import Final

import numpy as np

# Hard cap on how many filter-matching questions we feed into DPP. The
# algorithm is O(k * n^2); above ~500 candidates the wall-clock cost starts to
# show on cold cache reads. 200 hits the sweet spot — plenty of variety to
# pick from without paying the quadratic-blow-up tax.
CANDIDATE_POOL_SIZE: Final[int] = 200


def _normalize_rows(matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return (unit-normalized matrix, original norms). Zero-norm rows are
    left as-is and their norm reported as 0 so callers can filter them out.
    """
    norms = np.linalg.norm(matrix, axis=1)
    safe = np.where(norms > 0, norms, 1.0)
    return matrix / safe[:, None], norms


def cosine_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """Symmetric N×N cosine similarity matrix, diagonal = 1.0.

    Rows are unit-normalized internally so callers can pass raw embeddings.
    Degenerate (all-zero) vectors get a row/column of zeros except the
    diagonal — the DPP loop treats them as "perfectly orthogonal" which is
    benign but the caller is expected to have stripped them already.
    """
    if embeddings.size == 0:
        return np.zeros((0, 0), dtype=np.float64)
    unit, _norms = _normalize_rows(embeddings.astype(np.float64))
    sim = unit @ unit.T
    np.fill_diagonal(sim, 1.0)
    return sim


def diversity_score(embeddings: np.ndarray) -> float:
    """1 - mean pairwise cosine similarity. Higher = more diverse.

    Returns 1.0 when there are fewer than 2 vectors (a single question is
    "maximally diverse" by convention — there's nothing to be similar to)."""
    n = embeddings.shape[0]
    if n < 2:
        return 1.0
    sim = cosine_similarity_matrix(embeddings)
    # Mean of the strict upper triangle.
    iu = np.triu_indices(n, k=1)
    mean_sim = float(np.mean(sim[iu]))
    return 1.0 - mean_sim


def greedy_map(embeddings: np.ndarray, k: int) -> list[int]:
    """Greedy MAP-DPP. Returns indices into `embeddings` in selection order.

    Maintains a Cholesky-style row factor `c[i]` such that
    `di[i] = L[i,i] - ||c[i,:t]||^2` is the marginal log-det gain from
    selecting item i next. The diagonal of the cosine kernel is 1.0, so
    `di` starts as the all-ones vector.

    Stops early if no remaining item has positive marginal gain (the pool is
    effectively exhausted) — returns whatever was picked up to that point.
    """
    n = int(embeddings.shape[0])
    if n == 0 or k <= 0:
        return []
    if n <= k:
        return list(range(n))

    L = cosine_similarity_matrix(embeddings)
    di = np.ones(n, dtype=np.float64)  # L diagonal is 1.0
    # c[i] grows by one float per selection round; backed by a list of lists
    # because the per-step length varies and ndarray reshaping would be more
    # overhead than savings at our sizes.
    c: list[list[float]] = [[] for _ in range(n)]
    picked = np.zeros(n, dtype=bool)
    selected: list[int] = []

    for _ in range(k):
        # Mask picked items out of consideration; argmax returns 0 if all are
        # masked, but the `di` check below catches the empty case.
        candidate_scores = np.where(picked, -np.inf, di)
        best = int(np.argmax(candidate_scores))
        if not np.isfinite(candidate_scores[best]) or candidate_scores[best] <= 1e-10:
            break
        selected.append(best)
        picked[best] = True

        sqrt_di = float(np.sqrt(candidate_scores[best]))
        c_best = c[best]
        # Update di and c for remaining unselected items.
        for i in range(n):
            if picked[i]:
                continue
            c_i = c[i]
            dot = 0.0
            # The two arrays grow in lockstep, so they have equal length here.
            for s in range(len(c_best)):
                dot += c_i[s] * c_best[s]
            new_comp = (float(L[best, i]) - dot) / sqrt_di
            c_i.append(new_comp)
            di[i] -= new_comp * new_comp
        c[best].append(sqrt_di)

    return selected
