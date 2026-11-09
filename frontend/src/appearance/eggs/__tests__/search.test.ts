import { describe, expect, it } from "vitest";

import { EGGS } from "../catalogue";
import { SEARCH_EGG_IDS, matchSearchEgg, normalizeQuery } from "../searchMatch";

const id = (q: string) => matchSearchEgg(q)?.id ?? null;

describe("search egg matching", () => {
  it("normalizes case, whitespace and accents", () => {
    expect(normalizeQuery("  Hello \t  WORLD ")).toBe("hello world");
    expect(normalizeQuery("Erdős")).toBe("erdos");
  });

  it("matches the plain queries", () => {
    expect(id("42")).toBe("42");
    expect(id(" 1729 ")).toBe("1729");
    expect(id("XYZZY")).toBe("xyzzy");
    expect(id("coffee")).toBe("coffee");
    expect(id("Riemann")).toBe("riemann");
    expect(id("riemann hypothesis")).toBe("riemann");
  });

  it("handles sudo and rm -rf", () => {
    expect(id("sudo")).toBe("sudo");
    expect(id("sudo make me a sandwich")).toBe("sudo");
    expect(id("rm -rf")).toBe("rm-rf");
    expect(id("rm  -rf /")).toBe("rm-rf");
    expect(id("sudo rm -rf /")).toBe("rm-rf");
    expect(id("sudoku")).toBeNull();
  });

  it("matches hello world variants", () => {
    expect(id("hello world")).toBe("hello-world");
    expect(id("Hello, World!")).toBe("hello-world");
    expect(id("  HELLO    world  ")).toBe("hello-world");
  });

  it("matches P = NP however it is spaced", () => {
    expect(id("P=NP")).toBe("p-np");
    expect(id("p = np")).toBe("p-np");
    expect(id("P vs NP?")).toBe("p-np");
    expect(id("p != np")).toBe("p-np");
  });

  it("matches Erdős with or without the accent", () => {
    expect(id("erdos")).toBe("erdos");
    expect(id("Erdős")).toBe("erdos");
    expect(id("ERDÖS")).toBe("erdos");
  });

  it("matches Euler's identity in several spellings", () => {
    expect(id("e^(i pi)")).toBe("euler");
    expect(id("e^{i\\pi}")).toBe("euler");
    expect(id("e^(iπ)")).toBe("euler");
    expect(id("e^{i \\pi} + 1 = 0")).toBe("euler");
    expect(id("Euler")).toBe("euler");
    expect(id("euler's identity")).toBe("euler");
  });

  it("matches the barrel roll", () => {
    expect(id("do a barrel roll")).toBe("barrel-roll");
    expect(id("Do  a Barrel Roll!")).toBe("barrel-roll");
  });

  it("leaves ordinary searches alone", () => {
    for (const q of ["", "   ", "4 2", "421", "integration by parts", "riemann sums", "coffee cup", "hello"]) {
      expect(id(q)).toBeNull();
    }
  });

  it("returns cards with a title and body", () => {
    const card = matchSearchEgg("42");
    expect(card).toEqual({ id: "42", title: "42", body: "The answer. Now, what was the question?" });
  });

  it("has a catalogue entry for every search egg", () => {
    const ids = new Set(EGGS.map((e) => e.id));
    for (const s of SEARCH_EGG_IDS) expect(ids.has(`search-${s}`)).toBe(true);
  });
});
