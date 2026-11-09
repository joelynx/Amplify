import { describe, expect, it } from "vitest";

import {
  KONAMI,
  createBurstCounter,
  createKonamiDetector,
  createWordDetector,
  endsWithQed,
  fillsMargin,
  isLateNight,
  stepBounce,
  timeEgg,
} from "../detectors";

const KEYS = ["ArrowUp", "ArrowUp", "ArrowDown", "ArrowDown", "ArrowLeft", "ArrowRight", "ArrowLeft", "ArrowRight", "b", "a"];

function feed(detect: (k: string) => boolean, keys: string[]): boolean[] {
  return keys.map((k) => detect(k));
}

describe("Konami detector", () => {
  it("fires on the last key of the sequence only", () => {
    const out = feed(createKonamiDetector(), KEYS);
    expect(out.slice(0, -1).every((x) => !x)).toBe(true);
    expect(out[out.length - 1]).toBe(true);
    expect(KONAMI).toHaveLength(10);
  });

  it("ignores case on B and A", () => {
    const out = feed(createKonamiDetector(), [...KEYS.slice(0, 8), "B", "A"]);
    expect(out[9]).toBe(true);
  });

  it("matches after a false start with an extra up arrow", () => {
    const out = feed(createKonamiDetector(), ["ArrowUp", ...KEYS]);
    expect(out[out.length - 1]).toBe(true);
  });

  it("does not match with a wrong key in the middle", () => {
    const keys = [...KEYS];
    keys[5] = "ArrowUp";
    expect(feed(createKonamiDetector(), keys).some(Boolean)).toBe(false);
  });

  it("needs the whole sequence again after a match", () => {
    const d = createKonamiDetector();
    feed(d, KEYS);
    expect(feed(d, KEYS.slice(-2)).some(Boolean)).toBe(false);
    expect(feed(d, KEYS).pop()).toBe(true);
  });
});

describe("word detector (quack)", () => {
  it("finds the word and ignores modifier keys", () => {
    const d = createWordDetector("quack");
    const out = feed(d, ["x", "Shift", "Q", "u", "a", "Control", "c", "k"]);
    expect(out.pop()).toBe(true);
  });

  it("does not fire on a typo", () => {
    expect(feed(createWordDetector("quack"), [..."quqck"]).some(Boolean)).toBe(false);
  });
});

describe("burst counter (logo ×7)", () => {
  it("fires on the 7th click within 3 s", () => {
    const c = createBurstCounter(7, 3000);
    const out = [0, 300, 600, 900, 1200, 1500, 1800].map((t) => c.hit(t));
    expect(out).toEqual([false, false, false, false, false, false, true]);
    expect(c.count()).toBe(0);
  });

  it("does not fire when clicks are spread out", () => {
    const c = createBurstCounter(7, 3000);
    expect([0, 600, 1200, 1800, 2400, 3000, 3600].map((t) => c.hit(t)).some(Boolean)).toBe(false);
  });
});

describe("clock and note eggs", () => {
  const at = (h: number, m: number) => new Date(2026, 10, 8, h, m, 30);

  it("spots π o'clock and 13:37", () => {
    expect(timeEgg(at(3, 14))).toBe("pi-time");
    expect(timeEgg(at(15, 14))).toBe("pi-time");
    expect(timeEgg(at(13, 37))).toBe("leet");
    expect(timeEgg(at(3, 15))).toBeNull();
    expect(timeEgg(at(14, 14))).toBeNull();
  });

  it("recognises proofs that end properly", () => {
    expect(endsWithQed("so x = 2. QED")).toBe(true);
    expect(endsWithQed("hence the claim. Q.E.D.  ")).toBe(true);
    expect(endsWithQed("done ∎\n")).toBe(true);
    expect(endsWithQed("QED")).toBe(true);
    expect(endsWithQed("not quite QED yet")).toBe(false);
    expect(endsWithQed("IRAQED")).toBe(false);
  });

  it("fills the margin at the limit", () => {
    expect(fillsMargin("abc", 3)).toBe(true);
    expect(fillsMargin("ab", 3)).toBe(false);
    expect(fillsMargin("", 0)).toBe(false);
  });

  it("knows when it is late", () => {
    expect(isLateNight(at(2, 0))).toBe(true);
    expect(isLateNight(at(4, 59))).toBe(true);
    expect(isLateNight(at(1, 59))).toBe(false);
    expect(isLateNight(at(5, 0))).toBe(false);
  });
});

describe("screensaver bounce", () => {
  it("reflects off a wall", () => {
    const s = stepBounce({ x: 95, y: 50, vx: 100, vy: 0 }, 0.1, 10, 10, 110, 200);
    expect(s.hitX).toBe(true);
    expect(s.next.vx).toBeLessThan(0);
    expect(s.next.x).toBeLessThanOrEqual(100);
    expect(s.corner).toBe(false);
  });

  it("detects a corner hit", () => {
    const s = stepBounce({ x: 99, y: 189, vx: 100, vy: 100 }, 0.02, 10, 10, 110, 200);
    expect(s.hitX && s.hitY).toBe(true);
    expect(s.corner).toBe(true);
  });
});
