// lib/dpp.ts
// Determinantal Point Process — greedy MAP for diverse subset selection.
//
// Given a set of N candidate items with embedding vectors, pick a subset of
// size k that approximately maximizes log det of the cosine-similarity
// submatrix. This is the "Diverse" generation algorithm.
//
// Reference: Kulesza & Taskar, "Determinantal Point Processes for Machine
// Learning", NeurIPS 2012. We use the greedy MAP algorithm (not stochastic
// sampling) for determinism — the same candidate pool + same k produces the
// same selection.
//
// Complexity: O(k * n^2). At n=200, k=10, this is ~400K ops → <1ms.
// Never run this on the full question bank — pre-filter via SQL first.

/** Cosine similarity between two vectors. Handles non-unit-norm input. */
export function cosineSimilarity(a: number[], b: number[]): number {
  let dot = 0;
  let magA = 0;
  let magB = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    magA += a[i] * a[i];
    magB += b[i] * b[i];
  }
  const denom = Math.sqrt(magA) * Math.sqrt(magB);
  return denom === 0 ? 0 : dot / denom;
}

/**
 * Mean pairwise cosine similarity for a set of embeddings.
 * Used for the visible "Diversity: 0.XX" badge on generated practice sets.
 * Lower = more diverse. We display (1 - mean) so higher = more diverse.
 */
export function diversityScore(embeddings: number[][]): number {
  if (embeddings.length < 2) return 1.0;
  let total = 0;
  let pairs = 0;
  for (let i = 0; i < embeddings.length; i++) {
    for (let j = i + 1; j < embeddings.length; j++) {
      total += cosineSimilarity(embeddings[i], embeddings[j]);
      pairs++;
    }
  }
  const meanSim = total / pairs;
  return 1.0 - meanSim;
}

/**
 * Greedy MAP DPP — select k indices from the candidate pool that
 * approximately maximize log det of the similarity submatrix.
 *
 * Maintains a Cholesky-style factor c such that di[i] = L[i,i] - ||c[i,:t]||^2
 * is the marginal gain in log det from adding item i next.
 *
 * @param embeddings  Candidate embeddings (N items, each a number[]).
 * @param k           Number of items to select.
 * @returns           Indices into the candidate array, in selection order.
 */
export function dppGreedyMAP(embeddings: number[][], k: number): number[] {
  const n = embeddings.length;
  if (n === 0) return [];
  if (n <= k) return Array.from({ length: n }, (_, i) => i);

  // Precompute the kernel matrix L = pairwise cosine similarities.
  // Symmetric, n x n. Diagonal = 1.0 (cos(x, x) = 1).
  const L: number[][] = Array.from({ length: n }, () => new Array(n).fill(0));
  for (let i = 0; i < n; i++) L[i][i] = 1.0;
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      const s = cosineSimilarity(embeddings[i], embeddings[j]);
      L[i][j] = s;
      L[j][i] = s;
    }
  }

  // di[i] = marginal log-det gain from adding item i. Initially L[i,i] = 1.0.
  const di = new Array<number>(n).fill(1.0);
  // c[i] = evolving Cholesky-style row for item i (length = number of items already picked).
  const c: number[][] = Array.from({ length: n }, () => []);

  const selected: number[] = [];
  const picked = new Array<boolean>(n).fill(false);

  for (let t = 0; t < k; t++) {
    // Pick the unselected index with max di.
    let best = -1;
    let bestVal = -Infinity;
    for (let i = 0; i < n; i++) {
      if (!picked[i] && di[i] > bestVal) {
        bestVal = di[i];
        best = i;
      }
    }
    if (best === -1 || bestVal <= 1e-10) break;

    selected.push(best);
    picked[best] = true;

    const sqrtDi = Math.sqrt(bestVal);

    // Update di and c for remaining unselected items.
    for (let i = 0; i < n; i++) {
      if (picked[i]) continue;
      let dot = 0;
      const cBest = c[best];
      const cI = c[i];
      for (let s = 0; s < cBest.length; s++) {
        dot += cI[s] * cBest[s];
      }
      const newComp = (L[best][i] - dot) / sqrtDi;
      cI.push(newComp);
      di[i] -= newComp * newComp;
    }
    c[best].push(sqrtDi);
  }

  return selected;
}
