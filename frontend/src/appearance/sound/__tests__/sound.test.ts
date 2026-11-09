/**
 * Sound module: event → cue mapping, combo pitch, throttling, item coverage
 * for the presets, recipe and file fallbacks, and a fake-Web-Audio run of
 * every recipe (valid parameter values, no leaked nodes).
 */

import { describe, expect, it } from "vitest";

import type { AppEvent } from "../../events";
import { PRESETS } from "../../presets";
import {
  COMBO_MAX_SEMITONES,
  CUES,
  DEFAULT_PACK,
  PREVIEW_CUES,
  comboSemitones,
  cueGate,
  cuesFor,
  fileFor,
  lookupCue,
  rateLimiter,
  recipePack,
} from "../cues";
import { ITEMS } from "../items";
import { PACKS, recipeFor } from "../recipes";
import { fakeAudio } from "./fakeAudio";

const answer = (outcome: "correct" | "partial" | "wrong", combo = 0): AppEvent => ({
  type: "answer",
  outcome,
  unaided: true,
  combo,
  selfAssessed: false,
});

const cueNames = (e: AppEvent) => cuesFor(e).map((r) => `${r.channel}:${r.cue}`);

describe("event → cue mapping", () => {
  it("maps every app event to its cue and channel", () => {
    const table: [AppEvent, string[]][] = [
      [{ type: "click" }, ["ui:click"]],
      [{ type: "toggle", on: true }, ["ui:toggle"]],
      [{ type: "nav", path: "/" }, ["ui:nav"]],
      [answer("correct"), ["feedback:correct"]],
      [answer("partial"), ["feedback:partial"]],
      [answer("wrong"), ["feedback:wrong"]],
      [{ type: "hint" }, ["ui:hint"]],
      [{ type: "reveal" }, ["ui:reveal"]],
      [{ type: "bookmark", on: true }, ["ui:bookmark"]],
      [{ type: "note_saved", text: "x", limit: 500 }, ["ui:note"]],
      [{ type: "session_start", mode: "quiz" }, ["feedback:session_start"]],
      [
        { type: "session_end", summary: { mode: "quiz", answered: 1, unaided: 1, assisted: 0, missed: 0, partial: 0, toReview: 0, elapsedMs: 1 } },
        ["celebration:session_end"],
      ],
      [{ type: "timer_tick", remainingS: 10 }, ["feedback:tick"]],
      [{ type: "time_up" }, ["feedback:time_up"]],
      [{ type: "generate_done" }, ["feedback:generate_done"]],
      [{ type: "generate_error" }, ["feedback:generate_error"]],
      [{ type: "review_due", count: 4 }, ["feedback:review_due"]],
      [{ type: "unlock", what: "x" }, ["celebration:unlock"]],
      [{ type: "egg", id: "konami" }, ["celebration:egg"]],
      [{ type: "theme_switch" }, ["ui:theme_switch"]],
      [{ type: "search", query: "x" }, []],
      [{ type: "logo_click" }, []],
      [{ type: "idle", idle: true }, []],
    ];
    for (const [e, want] of table) expect(cueNames(e), e.type).toEqual(want);
  });

  it("keeps nav very quiet", () => {
    expect(cuesFor({ type: "nav", path: "/x" })[0].gain).toBeLessThan(0.5);
  });

  it("ticks only in the last 10 seconds, a little higher in the last 3", () => {
    expect(cuesFor({ type: "timer_tick", remainingS: 11 })).toEqual([]);
    expect(cuesFor({ type: "timer_tick", remainingS: 0 })).toEqual([]);
    expect(cuesFor({ type: "timer_tick", remainingS: 7 })[0].semitones ?? 0).toBe(0);
    expect(cuesFor({ type: "timer_tick", remainingS: 3 })[0].semitones).toBe(2);
  });

  it("says nothing when no reviews are due", () => {
    expect(cuesFor({ type: "review_due", count: 0 })).toEqual([]);
  });

  it("lowers toggle-off and un-bookmark a little", () => {
    expect(cuesFor({ type: "toggle", on: false })[0].semitones).toBeLessThan(0);
    expect(cuesFor({ type: "bookmark", on: false })[0].semitones).toBeLessThan(0);
  });
});

describe("combo", () => {
  it("adds a combo cue only for correct answers with combo ≥ 2", () => {
    expect(cueNames(answer("correct", 1))).toEqual(["feedback:correct"]);
    expect(cueNames(answer("wrong", 5))).toEqual(["feedback:wrong"]);
    expect(cueNames(answer("partial", 5))).toEqual(["feedback:partial"]);
    const reqs = cuesFor(answer("correct", 3));
    expect(reqs.map((r) => r.cue)).toEqual(["correct", "combo"]);
    expect(reqs[1].semitones).toBe(2);
    expect(reqs[1].delay).toBeGreaterThan(0);
  });

  it("rises a semitone per step and caps", () => {
    expect(comboSemitones(1)).toBe(0);
    expect(comboSemitones(2)).toBe(1);
    expect(comboSemitones(5)).toBe(4);
    expect(comboSemitones(COMBO_MAX_SEMITONES + 1)).toBe(COMBO_MAX_SEMITONES);
    expect(comboSemitones(50)).toBe(COMBO_MAX_SEMITONES);
    expect(cuesFor(answer("correct", 99))[1].semitones).toBe(COMBO_MAX_SEMITONES);
  });
});

describe("throttling", () => {
  it("lets at most 12 clicks a second through", () => {
    const allow = rateLimiter(12);
    let passed = 0;
    for (let t = 0; t < 1000; t += 10) if (allow(t)) passed++;
    expect(passed).toBeLessThanOrEqual(12);
    expect(passed).toBeGreaterThanOrEqual(10);
  });

  it("lets well-spaced clicks through", () => {
    const allow = rateLimiter(12);
    expect([0, 100, 200, 300].map((t) => allow(t))).toEqual([true, true, true, true]);
  });

  it("throttles clicks per cue and leaves answers alone", () => {
    const gate = cueGate();
    expect(gate("click", 0)).toBe(true);
    expect(gate("click", 20)).toBe(false);
    expect(gate("toggle", 20)).toBe(true);
    expect(gate("correct", 20)).toBe(true);
    expect(gate("correct", 21)).toBe(true);
    expect(gate("click", 100)).toBe(true);
  });
});

describe("items", () => {
  const ids = new Map(ITEMS.map((i) => [i.id, i.slot]));

  it("provides every sfx id the presets use", () => {
    for (const p of PRESETS) {
      if (p.slots.sfx) expect(ids.get(p.slots.sfx), `${p.id} sfx`).toBe("sfx");
    }
  });

  it("has the slot defaults and unique ids", () => {
    expect(ids.get(DEFAULT_PACK)).toBe("sfx");
    expect(ids.size).toBe(ITEMS.length);
  });

  it("backs every sfx item with a recipe pack", () => {
    for (const it of ITEMS) {
      if (it.slot === "sfx") expect(PACKS[it.id], it.id).toBeDefined();
    }
  });
});

describe("fallbacks", () => {
  it("sfx.soft covers every cue", () => {
    for (const cue of CUES) expect(PACKS[DEFAULT_PACK][cue], cue).toBeTypeOf("function");
  });

  it("uses the pack's own recipe when it has one", () => {
    expect(recipeFor("sfx.chiptune", "click")).toBe(PACKS["sfx.chiptune"].click);
  });

  it("falls back to sfx.soft for missing cues and unknown packs", () => {
    expect(PACKS["sfx.material"].reveal).toBeUndefined();
    expect(recipeFor("sfx.material", "reveal")).toBe(PACKS[DEFAULT_PACK].reveal);
    expect(recipeFor("sfx.nope", "click")).toBe(PACKS[DEFAULT_PACK].click);
  });

  it("lookupCue is generic", () => {
    const table = { [DEFAULT_PACK]: { click: "soft-click", hint: "soft-hint" }, "sfx.x": { click: "x-click" } };
    expect(lookupCue(table, "sfx.x", "click")).toBe("x-click");
    expect(lookupCue(table, "sfx.x", "hint")).toBe("soft-hint");
    expect(lookupCue(table, "sfx.x", "egg")).toBeUndefined();
  });

  it("finds pack files by cue name or the spec's file names", () => {
    const files = { correct: "./correct.ogg", note_saved: "./note.ogg", egg_found: "./egg.ogg", wrong: 3 };
    expect(fileFor(files, "correct")).toBe("./correct.ogg");
    expect(fileFor(files, "note")).toBe("./note.ogg");
    expect(fileFor(files, "egg")).toBe("./egg.ogg");
    expect(fileFor(files, "wrong")).toBeUndefined();
    expect(fileFor(undefined, "click")).toBeUndefined();
  });

  it("lets a drop-in pack name a built-in base", () => {
    expect(recipePack({ id: "sfx.mine", data: { base: "sfx.glass" } })).toBe("sfx.glass");
    expect(recipePack({ id: "sfx.glass" })).toBe("sfx.glass");
    expect(recipePack(undefined)).toBe(DEFAULT_PACK);
  });

  it("previews the five demo cues in order", () => {
    expect(PREVIEW_CUES.map((r) => r.cue)).toEqual(["click", "correct", "partial", "wrong", "session_end"]);
  });
});

describe("recipes on a fake audio context", () => {
  it("every pack plays every cue with valid values and frees all nodes", () => {
    for (const packId of Object.keys(PACKS)) {
      for (const cue of CUES) {
        const { fake, ac, out, outNode } = fakeAudio();
        for (const pitch of [1, 2 ** (COMBO_MAX_SEMITONES / 12)]) {
          recipeFor(packId, cue)({ ac, out, t: 0, pitch, gain: 0.8 });
        }
        expect(fake.sources.length, `${packId} ${cue}`).toBeGreaterThan(0);
        expect(fake.sources.every((s) => s.started && s.stopped), `${packId} ${cue} stops`).toBe(true);
        fake.endAll();
        expect(fake.connected([outNode]), `${packId} ${cue} leaks`).toEqual([]);
      }
    }
  });
});
