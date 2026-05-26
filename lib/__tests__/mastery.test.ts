import { describe, expect, it } from "vitest";
import {
  masteryPercent,
  lowerCredibilityBound,
  updateMastery,
} from "../mastery";

describe("masteryPercent", () => {
  it("returns 50% for the uniform prior", () => {
    expect(masteryPercent({ alpha: 1, beta: 1, total_seen: 0 })).toBe(50);
  });

  it("returns 100 * alpha / (alpha + beta)", () => {
    expect(masteryPercent({ alpha: 9, beta: 1, total_seen: 10 })).toBe(90);
    expect(masteryPercent({ alpha: 3, beta: 1, total_seen: 4 })).toBe(75);
  });
});

describe("lowerCredibilityBound", () => {
  it("returns lower bound below the posterior mean", () => {
    const bound = lowerCredibilityBound({ alpha: 5, beta: 5, total_seen: 10 });
    expect(bound).toBeLessThan(0.5);
    expect(bound).toBeGreaterThan(0);
  });

  it("returns a tighter bound at higher evidence", () => {
    const lowEvidence = lowerCredibilityBound({
      alpha: 1,
      beta: 1,
      total_seen: 0,
    });
    const highEvidence = lowerCredibilityBound({
      alpha: 100,
      beta: 100,
      total_seen: 200,
    });
    // Same posterior mean (0.5), but high-evidence bound is much closer to it.
    expect(highEvidence).toBeGreaterThan(lowEvidence);
  });

  it("ranks 0/5 below 5/5", () => {
    const veryBad = lowerCredibilityBound({ alpha: 1, beta: 6, total_seen: 5 });
    const veryGood = lowerCredibilityBound({
      alpha: 6,
      beta: 1,
      total_seen: 5,
    });
    expect(veryBad).toBeLessThan(veryGood);
  });

  it("never returns negative", () => {
    expect(
      lowerCredibilityBound({ alpha: 1, beta: 100, total_seen: 99 })
    ).toBeGreaterThanOrEqual(0);
  });
});

describe("updateMastery", () => {
  it("increments alpha on correct", () => {
    const out = updateMastery(
      { alpha: 1, beta: 1, total_seen: 0 },
      { correct: 1, incorrect: 0 }
    );
    expect(out).toEqual({ alpha: 2, beta: 1, total_seen: 1 });
  });

  it("increments beta on incorrect", () => {
    const out = updateMastery(
      { alpha: 1, beta: 1, total_seen: 0 },
      { correct: 0, incorrect: 1 }
    );
    expect(out).toEqual({ alpha: 1, beta: 2, total_seen: 1 });
  });

  it("supports fractional updates (partial credit)", () => {
    const out = updateMastery(
      { alpha: 1, beta: 1, total_seen: 0 },
      { correct: 0.5, incorrect: 0.5 }
    );
    expect(out).toEqual({ alpha: 1.5, beta: 1.5, total_seen: 1 });
  });
});
