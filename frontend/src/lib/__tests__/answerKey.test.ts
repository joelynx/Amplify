/** Display helpers for answer-key parts: option labels, expected / input text,
 * the marks payload for quiz_self_assess, and bestSolution with takeaways. */

import { describe, expect, it } from "vitest";
import {
  awaitingIndices,
  canSubmit,
  choiceText,
  creditLabel,
  expectedText,
  expressionTex,
  inputText,
  marksPayload,
  nextTypedField,
  optionLabel,
  optionLetter,
  readNote,
  toggleChoice,
  withUnit,
} from "../answerKey";
import { bestSolution, TAKEAWAYS_HEADING, type AnswerField, type PartResult } from "../ipc";

function part(over: Partial<PartResult>): PartResult {
  return {
    label: "",
    ask: "",
    kind: "number",
    unit: "",
    input: "",
    read: null,
    credit: 1,
    mark: null,
    expected: null,
    points: [],
    ...over,
  };
}

function field(over: Partial<AnswerField>): AnswerField {
  return { label: "", ask: "", kind: "number", unit: "", options: null, multi: false, ...over };
}

describe("options", () => {
  it("numbers the letters as a plain enumerate does", () => {
    expect(optionLetter(0)).toBe("a");
    expect(optionLetter(3)).toBe("d");
    expect(optionLabel("b")).toBe("2 · b");
    expect(optionLabel("B")).toBe("2 · b");
    expect(optionLabel("??")).toBe("??");
    expect(choiceText("a, c")).toBe("1 · a, 3 · c");
  });

  it("single-select replaces or clears", () => {
    expect(toggleChoice("", "b", false)).toBe("b");
    expect(toggleChoice("a", "b", false)).toBe("b");
    expect(toggleChoice("b", "b", false)).toBe("");
  });

  it("multi-select toggles and keeps the letters sorted", () => {
    expect(toggleChoice("", "c", true)).toBe("c");
    expect(toggleChoice("c", "a", true)).toBe("a, c");
    expect(toggleChoice("a, c", "c", true)).toBe("a");
  });
});

describe("expected and input text", () => {
  it("puts the unit after a number", () => {
    expect(withUnit("1236", "kJ/kg")).toBe("1236 kJ/kg");
    expect(withUnit("38.6", "%")).toBe("38.6%");
    expect(withUnit("12", "")).toBe("12");
    expect(expectedText(part({ expected: "1236", unit: "kJ/kg" }))).toBe("1236 kJ/kg");
  });

  it("shows options and booleans in both forms", () => {
    expect(expectedText(part({ kind: "choice", expected: "a, c" }))).toBe("1 · a, 3 · c");
    expect(expectedText(part({ kind: "truefalse", expected: "false" }))).toBe("False");
    expect(inputText(part({ kind: "choice", input: "(b)", read: "b" }))).toBe("2 · b");
    expect(inputText(part({ kind: "choice", input: "zz", read: null }))).toBe("zz");
    expect(inputText(part({ kind: "truefalse", input: "t", read: "true" }))).toBe("True");
  });

  it("has no plain text for expressions, checklists, or withheld answers", () => {
    expect(expectedText(part({ kind: "expression", expected: "x^2" }))).toBeNull();
    expect(expectedText(part({ kind: "points", points: ["a"] }))).toBeNull();
    expect(expectedText(part({ expected: null }))).toBeNull();
  });

  it("notes a converted or unreadable number", () => {
    expect(readNote(part({ input: "1.24 MJ/kg", read: "1240", unit: "kJ/kg" }))).toBe("read as 1240 kJ/kg");
    expect(readNote(part({ input: "1/8", read: "0.125" }))).toBe("read as 0.125");
    expect(readNote(part({ input: "1240 kJ/kg", read: "1240", unit: "kJ/kg" }))).toBeNull();
    expect(readNote(part({ input: "1.2e5", read: "120000" }))).toBeNull();
    expect(readNote(part({ input: "lots", read: null }))).toBe("not read as a number");
    expect(readNote(part({ input: "", read: null }))).toBeNull();
    expect(readNote(part({ kind: "choice", input: "b", read: "b" }))).toBeNull();
  });

  it("wraps bare math for LatexContent, leaves delimited math and prose", () => {
    expect(expressionTex("\\frac{\\pi}{4}")).toBe("$\\frac{\\pi}{4}$");
    expect(expressionTex("x^2+1")).toBe("$x^2+1$");
    expect(expressionTex("2n")).toBe("$2n$");
    expect(expressionTex("$\\frac{\\pi}{4}$")).toBe("$\\frac{\\pi}{4}$");
    expect(expressionTex("\\(x\\)")).toBe("\\(x\\)");
    expect(expressionTex("It diverges")).toBe("It diverges");
  });

  it("labels credit", () => {
    expect(creditLabel(1)).toBe("Correct");
    expect(creditLabel(0.5)).toBe("Partial");
    expect(creditLabel(0)).toBe("Wrong");
    expect(creditLabel(null)).toBe("To mark");
  });
});

describe("self-assessment marks", () => {
  const parts = [part({ credit: 1 }), part({ kind: "points", credit: null }), part({ kind: "expression", credit: null })];

  it("finds the parts awaiting marks", () => {
    expect(awaitingIndices(parts)).toEqual([1, 2]);
  });

  it("is incomplete until every awaiting part is marked", () => {
    expect(marksPayload(parts, {})).toBeNull();
    expect(marksPayload(parts, { 1: "got_it" })).toBeNull();
    expect(marksPayload(parts, { 1: "got_it", 2: "missed" })).toEqual([null, "got_it", "missed"]);
    // marks on auto-graded parts are not sent
    expect(marksPayload(parts, { 0: "missed", 1: "partial", 2: "partial" })).toEqual([null, "partial", "partial"]);
    expect(marksPayload([part({ credit: 1 })], {})).toBeNull();
  });
});

describe("inputs", () => {
  it("needs some input unless every part is self-assessed", () => {
    expect(canSubmit([field({})], [""])).toBe(false);
    expect(canSubmit([field({})], [" 12 "])).toBe(true);
    expect(canSubmit([field({}), field({ kind: "points" })], ["", "x"])).toBe(true);
    expect(canSubmit([field({ kind: "points" })], [""])).toBe(true);
    expect(canSubmit([field({ kind: "expression" }), field({ kind: "points" })], ["", ""])).toBe(true);
    expect(canSubmit([], [])).toBe(false);
  });

  it("moves Enter to the next typed input, skipping option buttons", () => {
    const fields = [
      field({}),
      field({ kind: "choice", options: 4 }),
      field({ kind: "truefalse" }),
      field({ kind: "expression" }),
      field({ kind: "choice", options: null }),
    ];
    expect(nextTypedField(fields, 0)).toBe(3);
    expect(nextTypedField(fields, 3)).toBe(4);
    expect(nextTypedField(fields, 4)).toBe(-1);
    expect(nextTypedField([field({})], 0)).toBe(-1);
  });
});

describe("bestSolution", () => {
  const take = "\\begin{itemize}\\item x\\end{itemize}\n\\hfill [Generated by Claude]";

  it("returns a generated solution unchanged", () => {
    expect(bestSolution({ solution: "orig", generated_solution: "gen", takeaways: take })).toBe("gen");
  });

  it("appends takeaways to the source solution", () => {
    expect(bestSolution({ solution: "orig", generated_solution: null, takeaways: take })).toBe(
      "orig" + TAKEAWAYS_HEADING + take,
    );
    expect(TAKEAWAYS_HEADING).toBe("\n\n\\medskip\\noindent\\textbf{Takeaways}\n\n");
  });

  it("falls back to the source solution", () => {
    expect(bestSolution({ solution: "orig", generated_solution: "  ", takeaways: " " })).toBe("orig");
    expect(bestSolution({ solution: "orig", generated_solution: null })).toBe("orig");
    expect(bestSolution({ solution: null, generated_solution: null, takeaways: null })).toBeNull();
  });
});
