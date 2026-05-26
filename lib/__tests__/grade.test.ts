import { describe, expect, it } from "vitest";
import { looselyEqual } from "../grade";

describe("looselyEqual", () => {
  it("exact string match", () => {
    expect(looselyEqual("hello", "hello")).toBe(true);
  });

  it("ignores case", () => {
    expect(looselyEqual("HELLO", "hello")).toBe(true);
  });

  it("ignores whitespace", () => {
    expect(looselyEqual("a b c", "abc")).toBe(true);
  });

  it("strips \\boxed{}", () => {
    expect(looselyEqual("\\boxed{42}", "42")).toBe(true);
  });

  it("exact float match", () => {
    expect(looselyEqual("3.14", "3.14")).toBe(true);
  });

  it("tolerant float match within 0.1%", () => {
    expect(looselyEqual("3.1416", "3.14159")).toBe(true);
  });

  it("rejects mismatched floats", () => {
    expect(looselyEqual("3.14", "3.5")).toBe(false);
  });

  it("rejects mismatched strings", () => {
    expect(looselyEqual("hello", "world")).toBe(false);
  });

  it("zero matches zero", () => {
    expect(looselyEqual("0", "0.000001")).toBe(true);
  });

  it("scales relative tolerance with magnitude", () => {
    // Within 0.0001% of 1M — should pass.
    expect(looselyEqual("1000000", "1000001")).toBe(true);
    // Far outside the 0.1% relative threshold (10:1 difference at scale ≥1).
    expect(looselyEqual("1", "10")).toBe(false);
  });
});
