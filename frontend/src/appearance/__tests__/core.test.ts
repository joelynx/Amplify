import { describe, expect, it } from "vitest";

import { contrast, parseColor } from "../contrast";
import { on } from "../events";
import { parseFontPath } from "../fonts";
import { PRESETS } from "../presets";
import { DEFAULT_LOADOUT, getItem, itemsFor, normalizeLoadout, resolve } from "../registry";
import { endSession, outcomeOf, recordAnswer, startSession } from "../session";
import { inNightWindow } from "../store";
import { SLOTS } from "../types";
import { decodeLoadout, encodeLoadout } from "../../pages/themes/SavedLoadouts";

describe("registry", () => {
  it("has a default item for every slot", () => {
    for (const slot of SLOTS) expect(getItem(DEFAULT_LOADOUT[slot])?.slot).toBe(slot);
  });

  it("fills gaps and drops unknown or wrong-slot ids", () => {
    const l = normalizeLoadout({ palette: "palette.pastel", chrome: "palette.ascii", sfx: "sfx.nope" });
    expect(l.palette).toBe("palette.pastel");
    expect(l.chrome).toBe(DEFAULT_LOADOUT.chrome);
    expect(l.sfx).toBe(DEFAULT_LOADOUT.sfx);
    expect(resolve({}, "logo")?.id).toBe("logo.auto");
  });

  it("gives every palette a theme id and every loader a looping animation", () => {
    for (const p of itemsFor("palette")) expect(typeof p.data?.theme).toBe("string");
    for (const l of itemsFor("loader")) expect(["sweep", "reduce"]).toContain(l.data?.big);
  });
});

describe("presets", () => {
  it("only name real slots, and ids are unique", () => {
    const ids = new Set<string>();
    for (const p of PRESETS) {
      expect(ids.has(p.id)).toBe(false);
      ids.add(p.id);
      for (const slot of Object.keys(p.slots)) expect(SLOTS).toContain(slot);
    }
  });

  it("reference CSS-slot items that exist", () => {
    for (const p of PRESETS) {
      for (const slot of ["palette", "typography", "chrome", "motion", "surface", "paper", "cursor", "icons", "logo", "loader", "charts", "arena"] as const) {
        const id = p.slots[slot];
        if (id) expect(getItem(id)?.slot, `${p.id}.${slot} = ${id}`).toBe(slot);
      }
    }
  });
});

describe("session", () => {
  it("classifies credit", () => {
    expect(outcomeOf(1)).toBe("correct");
    expect(outcomeOf(0.5)).toBe("partial");
    expect(outcomeOf(0)).toBe("wrong");
  });

  it("counts a combo of unaided full solves and summarises honestly", () => {
    const seen: number[] = [];
    const off = on("answer", (e) => seen.push(e.combo));
    startSession("discover", 0);
    recordAnswer({ credit: 1, assisted: false, selfAssessed: false });
    recordAnswer({ credit: 1, assisted: false, selfAssessed: false });
    recordAnswer({ credit: 1, assisted: true, selfAssessed: false });
    recordAnswer({ credit: 0.5, assisted: false, selfAssessed: true });
    recordAnswer({ credit: 1, assisted: false, selfAssessed: false });
    off();
    expect(seen).toEqual([1, 2, 0, 0, 1]);
    const s = endSession(60_000)!;
    expect(s).toMatchObject({ answered: 5, unaided: 3, assisted: 1, partial: 1, missed: 0, toReview: 2, elapsedMs: 60_000 });
    expect(endSession()).toBeNull();
  });
});

describe("fonts", () => {
  it("reads family, weight and style from Google Fonts file names", () => {
    expect(parseFontPath("../../fonts/Inter/Inter-VariableFont_opsz,wght.ttf", "u")).toMatchObject({ family: "Inter", weight: "100 900", style: "normal" });
    expect(parseFontPath("../../fonts/Comic Neue/ComicNeue-BoldItalic.ttf", "u")).toMatchObject({ family: "Comic Neue", weight: "700", style: "italic" });
    expect(parseFontPath("../../fonts/Crimson Pro/CrimsonPro-SemiBold.ttf", "u").weight).toBe("600");
    expect(parseFontPath("../../fonts/Press Start 2P/PressStart2P-Regular.ttf", "u").weight).toBe("400");
  });
});

describe("contrast", () => {
  it("parses hex and rgb and computes WCAG ratios", () => {
    expect(parseColor("#fff")).toEqual([255, 255, 255]);
    expect(parseColor("rgb(0, 0, 0)")).toEqual([0, 0, 0]);
    expect(contrast("#000000", "#ffffff")).toBeCloseTo(21, 0);
    expect(contrast("linear-gradient(red, blue)", "#fff")).toBeNull();
  });
});

describe("loadout codes", () => {
  it("round-trips a loadout", () => {
    const l = normalizeLoadout({ palette: "palette.nord", chrome: "chrome.pixel", sfx: "sfx.chiptune" });
    const code = encodeLoadout(l);
    expect(code.startsWith("AMP1:")).toBe(true);
    expect(decodeLoadout(code)).toEqual(l);
    expect(decodeLoadout("nonsense")).toBeNull();
  });
});

describe("night window", () => {
  it("handles windows that wrap midnight", () => {
    expect(inNightWindow(20, 19, 7)).toBe(true);
    expect(inNightWindow(3, 19, 7)).toBe(true);
    expect(inNightWindow(12, 19, 7)).toBe(false);
    expect(inNightWindow(23, 22, 23)).toBe(false);
    expect(inNightWindow(22, 22, 23)).toBe(true);
    expect(inNightWindow(5, 5, 5)).toBe(false);
  });
});
