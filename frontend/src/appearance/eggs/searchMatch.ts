/**
 * Pure matching for the Browser search eggs (Makeover.md §6). Queries are
 * compared case-insensitively, trimmed, with whitespace collapsed and
 * accents folded (so "Erdős" and "erdos" match). No store access here.
 */

import type { SearchEgg } from "./search";

export function normalizeQuery(q: string): string {
  return q
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .trim()
    .replace(/\s+/g, " ");
}

/** Formula form: no spaces, no backslashes or `*`, braces as parens, π as "pi". */
function compactFormula(q: string): string {
  return q
    .replace(/\s+/g, "")
    .replace(/[\\*]/g, "")
    .replace(/\{/g, "(")
    .replace(/\}/g, ")")
    .replace(/π/g, "pi");
}

const EULER_FORMULAS = new Set([
  "e^(ipi)", "e^ipi", "e^(pii)", "e^pii", "exp(ipi)",
  "e^(ipi)+1=0", "e^ipi+1=0", "e^(ipi)=-1", "e^ipi=-1",
]);
const EULER_WORDS = new Set(["euler", "euler's identity", "eulers identity", "euler identity"]);

interface Spec extends SearchEgg {
  /** `q` is normalized with trailing ! ? . removed. */
  test: (q: string) => boolean;
}

const SPECS: Spec[] = [
  { id: "42", title: "42", body: "The answer. Now, what was the question?", test: (q) => q === "42" },
  {
    id: "1729",
    title: "1729",
    body:
      "Visiting Ramanujan in hospital, Hardy remarked that his taxi's number, 1729, seemed rather dull. " +
      "Ramanujan replied that it was very interesting: the smallest number expressible as the sum of two cubes in two different ways (1³ + 12³ = 9³ + 10³).",
    test: (q) => q === "1729",
  },
  { id: "xyzzy", title: "xyzzy", body: "Nothing happens.", test: (q) => q === "xyzzy" },
  // Before sudo, so "sudo rm -rf /" gets the scarier card.
  { id: "rm-rf", title: "rm -rf", body: "Not today.", test: (q) => /^(?:sudo )?rm -(?:rf|fr)(?: |$)/.test(q) },
  { id: "sudo", title: "sudo", body: "Nice try.", test: (q) => q === "sudo" || q.startsWith("sudo ") },
  { id: "hello-world", title: "hello, world", body: "Hello!", test: (q) => /^hello,? world$/.test(q) },
  {
    id: "p-np",
    title: "P = NP",
    body: "Proof left as an exercise to the reader.",
    test: (q) => /^p(?:=|==|!=|≠|vs\.?|versus)np$/.test(q.replace(/\s+/g, "")),
  },
  {
    id: "riemann",
    title: "The Riemann hypothesis",
    body: "Still open. Get to work.",
    test: (q) => q === "riemann" || q === "riemann hypothesis" || q === "the riemann hypothesis",
  },
  {
    id: "erdos",
    title: "Paul Erdős",
    body: "Erdős number of this app: ∞.",
    test: (q) => q === "erdos" || q === "paul erdos" || q === "erdos number",
  },
  {
    id: "coffee",
    title: "Coffee",
    body: "A mathematician is a machine for turning coffee into theorems. — attributed to Alfréd Rényi",
    test: (q) => q === "coffee",
  },
  {
    id: "euler",
    title: "Euler's identity",
    body: "e^(iπ) + 1 = 0. Five fundamental constants, three operations, one line.",
    test: (q) => EULER_WORDS.has(q) || EULER_FORMULAS.has(compactFormula(q)),
  },
  { id: "barrel-roll", title: "Do a barrel roll", body: "Press Z or R twice!", test: (q) => q === "do a barrel roll" },
];

/** The egg card for a query, or null. Pure: records nothing. */
export function matchSearchEgg(query: string): SearchEgg | null {
  const q = normalizeQuery(query).replace(/\s*[!?.]+$/, "");
  if (!q) return null;
  const hit = SPECS.find((s) => s.test(q));
  return hit ? { id: hit.id, title: hit.title, body: hit.body } : null;
}

/** Every search egg id, for the catalogue tests. */
export const SEARCH_EGG_IDS = SPECS.map((s) => s.id);
