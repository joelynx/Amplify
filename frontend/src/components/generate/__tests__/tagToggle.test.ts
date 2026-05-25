/** Truth table + cascade rules for the TagTray toggles (spec §8.1). */

import { describe, expect, it } from "vitest";
import {
  cascadeOnCompulsoryChange,
  cascadeOnExcludeChange,
  categoryFromToggles,
} from "../tagToggle";

describe("categoryFromToggles", () => {
  it("optional when both off", () => {
    expect(categoryFromToggles({ compulsory: false, exclude: false })).toBe("optional");
  });

  it("compulsory when compulsory on, exclude off", () => {
    expect(categoryFromToggles({ compulsory: true, exclude: false })).toBe("compulsory");
  });

  it("excluded when both on", () => {
    expect(categoryFromToggles({ compulsory: true, exclude: true })).toBe("excluded");
  });

  it("excluded even when compulsory off (unreachable via cascade, but defined)", () => {
    expect(categoryFromToggles({ compulsory: false, exclude: true })).toBe("excluded");
  });
});

describe("cascadeOnCompulsoryChange", () => {
  it("turns Compulsory on without touching Exclude", () => {
    expect(cascadeOnCompulsoryChange({ compulsory: false, exclude: false }, true)).toEqual({
      compulsory: true,
      exclude: false,
    });
  });

  it("turning Compulsory off while Exclude is on also turns Exclude off (spec §8.1)", () => {
    expect(cascadeOnCompulsoryChange({ compulsory: true, exclude: true }, false)).toEqual({
      compulsory: false,
      exclude: false,
    });
  });

  it("turning Compulsory off while Exclude is off leaves Exclude untouched", () => {
    expect(cascadeOnCompulsoryChange({ compulsory: true, exclude: false }, false)).toEqual({
      compulsory: false,
      exclude: false,
    });
  });
});

describe("cascadeOnExcludeChange", () => {
  it("turning Exclude on forces Compulsory on (spec §8.1)", () => {
    expect(cascadeOnExcludeChange({ compulsory: false, exclude: false }, true)).toEqual({
      compulsory: true,
      exclude: true,
    });
  });

  it("turning Exclude on when Compulsory already on just sets Exclude", () => {
    expect(cascadeOnExcludeChange({ compulsory: true, exclude: false }, true)).toEqual({
      compulsory: true,
      exclude: true,
    });
  });

  it("turning Exclude off leaves Compulsory alone", () => {
    expect(cascadeOnExcludeChange({ compulsory: true, exclude: true }, false)).toEqual({
      compulsory: true,
      exclude: false,
    });
  });
});

describe("round-trip", () => {
  it("(false,false) → tick Exclude → tick Compulsory off → both off (impossible state never reached)", () => {
    let state = { compulsory: false, exclude: false };
    state = cascadeOnExcludeChange(state, true);
    expect(state).toEqual({ compulsory: true, exclude: true });
    state = cascadeOnCompulsoryChange(state, false);
    expect(state).toEqual({ compulsory: false, exclude: false });
  });
});
