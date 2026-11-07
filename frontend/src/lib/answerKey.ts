/**
 * Display helpers for answer-key parts (pipeline/answer_key_spec.md). Grading
 * happens in Python (`app/core/answer_key.py`); these only format what the
 * quiz shows and shape the inputs and self-assessment marks it sends back.
 */

import type { AnswerField, PartResult, SelfMark } from "./ipc";

export const MARK_LABELS: Record<SelfMark, string> = {
  got_it: "Got it",
  partial: "Partial",
  missed: "Missed",
};

/** Option `i` (0-based) as the letter keys store: 0 -> "a". */
export function optionLetter(i: number): string {
  return String.fromCharCode(97 + i);
}

/** "b" -> "2 · b": the number a plain `enumerate` shows, then the stored letter. */
export function optionLabel(letter: string): string {
  const l = letter.trim().toLowerCase();
  return /^[a-z]$/.test(l) ? `${l.charCodeAt(0) - 96} · ${l}` : letter;
}

/** "a, c" -> ["a", "c"]. */
export function splitLetters(value: string): string[] {
  return value
    .split(/[\s,]+/)
    .map((s) => s.trim().toLowerCase())
    .filter(Boolean);
}

/** "a, c" -> "1 · a, 3 · c". */
export function choiceText(letters: string): string {
  return splitLetters(letters).map(optionLabel).join(", ");
}

/** Click on option `letter` given the current choice input ("a, c"): a
 * single-select part takes the letter (or clears it); a multi-select part
 * toggles it, kept sorted. */
export function toggleChoice(current: string, letter: string, multi: boolean): string {
  if (!multi) return current === letter ? "" : letter;
  const picked = new Set(splitLetters(current));
  if (picked.has(letter)) picked.delete(letter);
  else picked.add(letter);
  return [...picked].sort().join(", ");
}

/** "38.6%", "1236 kJ/kg", "12". */
export function withUnit(value: string, unit: string): string {
  if (!unit) return value;
  return unit === "%" || unit === "°" ? `${value}${unit}` : `${value} ${unit}`;
}

/** "(a)", or "" for a one-part question. */
export function partLabel(label: string): string {
  return label ? `(${label})` : "";
}

/** The expected answer as plain text; null for `expression` (render
 * `expressionTex`), `points` (a checklist), and when withheld. */
export function expectedText(part: PartResult): string | null {
  if (part.expected == null) return null;
  switch (part.kind) {
    case "number":
      return withUnit(part.expected, part.unit);
    case "choice":
      return choiceText(part.expected);
    case "truefalse":
      return part.expected === "true" ? "True" : "False";
    default:
      return null;
  }
}

/** The student's input as the result shows it (options with both forms). */
export function inputText(part: PartResult): string {
  if (part.kind === "choice" && part.read) return choiceText(part.read);
  if (part.kind === "truefalse" && part.read) return part.read === "true" ? "True" : "False";
  return part.input;
}

/** For a number part, how the input was read when that is not what the student
 * typed ("1.24 MJ/kg" -> "read as 1240 kJ/kg"), or that it could not be read. */
export function readNote(part: PartResult): string | null {
  if (part.kind !== "number" || !part.input.trim()) return null;
  if (part.read == null) return "not read as a number";
  return parseFloat(part.input) === parseFloat(part.read) ? null : `read as ${withUnit(part.read, part.unit)}`;
}

/** LaTeX for an `expression` value: put in `$...$` unless it already has math
 * delimiters or reads as prose (legacy answers are text-mode LaTeX; pipeline
 * keys are bare math). */
export function expressionTex(value: string): string {
  const v = value.trim();
  if (/\$|\\\(|\\\[|\\begin\{/.test(v)) return v;
  if (/[\\^_{}]/.test(v) || !/\s/.test(v)) return `$${v}$`;
  return v;
}

/** "Correct" / "Partial" / "Wrong" for a credit in [0, 1]. */
export function creditLabel(credit: number | null | undefined): string {
  if (credit == null) return "To mark";
  if (credit >= 1) return "Correct";
  if (credit <= 0) return "Wrong";
  return "Partial";
}

/** Indices of the parts awaiting self-assessment. */
export function awaitingIndices(parts: PartResult[]): number[] {
  return parts.flatMap((p, i) => (p.credit == null ? [i] : []));
}

/** The `marks` for quiz_self_assess (null for parts not awaiting), or null
 * while some awaiting part is still unmarked. */
export function marksPayload(
  parts: PartResult[],
  marks: Partial<Record<number, SelfMark>>,
): (SelfMark | null)[] | null {
  const awaiting = awaitingIndices(parts);
  if (awaiting.length === 0 || awaiting.some((i) => !marks[i])) return null;
  return parts.map((p, i) => (p.credit == null ? (marks[i] ?? null) : null));
}

/** Whether there is something to submit: any input, or only parts the student
 * self-assesses (a descriptive answer may live on paper). */
export function canSubmit(fields: AnswerField[], inputs: string[]): boolean {
  if (fields.length === 0) return false;
  if (inputs.some((s) => s.trim() !== "")) return true;
  return fields.every((f) => f.kind === "points" || f.kind === "expression");
}

/** The index of the next typed input after `i` (Enter moves there), or -1. */
export function nextTypedField(fields: AnswerField[], i: number): number {
  for (let j = i + 1; j < fields.length; j++) {
    const f = fields[j];
    if (f.kind === "number" || f.kind === "expression" || f.kind === "points") return j;
    if (f.kind === "choice" && !f.options) return j;
  }
  return -1;
}
