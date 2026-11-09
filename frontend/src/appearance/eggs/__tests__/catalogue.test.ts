import { describe, expect, it } from "vitest";

import { EGGS, VAPORWAVE_THRESHOLD, shouldUnlockVaporwave } from "../catalogue";

const n = (k: number) => Array.from({ length: k }, (_, i) => `egg-${i}`);

describe("Vaporwave unlock rule", () => {
  it("needs ten secrets", () => {
    expect(VAPORWAVE_THRESHOLD).toBe(10);
    expect(shouldUnlockVaporwave(n(9))).toBe(false);
    expect(shouldUnlockVaporwave(n(10))).toBe(true);
    expect(shouldUnlockVaporwave(new Set(n(14)))).toBe(true);
  });

  it("does not fire again once Vaporwave is found", () => {
    expect(shouldUnlockVaporwave([...n(12), "vaporwave"])).toBe(false);
  });

  it("does not count Vaporwave towards its own threshold", () => {
    expect(shouldUnlockVaporwave(["vaporwave", ...n(9)])).toBe(false);
  });
});

describe("catalogue", () => {
  it("has unique ids and a hint and reward for each egg", () => {
    expect(new Set(EGGS.map((e) => e.id)).size).toBe(EGGS.length);
    for (const e of EGGS) {
      expect(e.hint.length).toBeGreaterThan(0);
      expect(e.reward).toBeTruthy();
    }
  });

  it("rewards Vaporwave with the hidden preset", () => {
    expect(EGGS.find((e) => e.id === "vaporwave")?.reward).toMatchObject({ type: "preset", preset: "vaporwave" });
  });
});
