import { describe, expect, it } from "vitest";

import { hintTiers } from "../ipc";

// Mirrors tests/test_tiered_hints.py::test_hint_tiers.
describe("hintTiers", () => {
  it("puts `hints` first and appends the tiers in `more_hints`", () => {
    expect(hintTiers({ hints: "A", more_hints: '["B", "C"]' })).toEqual(["A", "B", "C"]);
    expect(hintTiers({ hints: "A", more_hints: null })).toEqual(["A"]);
    expect(hintTiers({ hints: "A" })).toEqual(["A"]);
  });

  it("has no hints without a first one", () => {
    expect(hintTiers({ hints: null, more_hints: '["B"]' })).toEqual([]);
    expect(hintTiers({ hints: "  ", more_hints: '["B"]' })).toEqual([]);
  });

  it("ignores bad JSON, blank or non-string entries, and tiers past the third", () => {
    expect(hintTiers({ hints: "A", more_hints: "not json" })).toEqual(["A"]);
    expect(hintTiers({ hints: "A", more_hints: '{"a": 1}' })).toEqual(["A"]);
    expect(hintTiers({ hints: "A", more_hints: '["", 3, "B"]' })).toEqual(["A", "B"]);
    expect(hintTiers({ hints: "A", more_hints: '["B", "C", "D", "E"]' })).toEqual(["A", "B", "C"]);
  });
});
