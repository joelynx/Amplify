// Pure mastery math, factored out of /app/me/page.tsx so it's unit-testable.

export interface BetaPrior {
  alpha: number;
  beta: number;
  total_seen: number;
}

// Posterior mean of Beta(alpha, beta).
export function masteryPercent(prior: BetaPrior): number {
  return (prior.alpha / (prior.alpha + prior.beta)) * 100;
}

// Lower credibility bound (posterior mean - 1 SD). Used to rank "weakest"
// — penalises high uncertainty so a 0/0 prior doesn't beat a 5/5 prior.
export function lowerCredibilityBound(prior: BetaPrior): number {
  const { alpha, beta } = prior;
  const mean = alpha / (alpha + beta);
  const variance =
    (alpha * beta) / ((alpha + beta) ** 2 * (alpha + beta + 1));
  return Math.max(0, mean - Math.sqrt(variance));
}

export function updateMastery(
  prior: BetaPrior,
  outcome: { correct: number; incorrect: number }
): BetaPrior {
  return {
    alpha: prior.alpha + outcome.correct,
    beta: prior.beta + outcome.incorrect,
    total_seen: prior.total_seen + 1,
  };
}
