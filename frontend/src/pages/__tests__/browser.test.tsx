/**
 * Browser: rows show the question itself and open on a click anywhere; the
 * list says when it is loading or failed, and a slow earlier search cannot
 * overwrite a later one. The backend is a stub bridge.
 */

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { Question, SearchResult } from "../../lib/ipc";
import BrowserPage from "../Browser";

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

vi.mock("../../components/notes/QuestionNotes", () => ({
  BookmarkButton: () => null,
  NoteEditor: () => null,
}));

// The stub bridge has to exist before any module asks for it (the first miss is cached).
const { handlers } = vi.hoisted(() => {
  const handlers: Record<string, (...args: unknown[]) => unknown> = {};
  // Not a thenable: the bridge is passed through a promise.
  const api = new Proxy(
    {},
    {
      get: (_t, name: string) =>
        name === "then" ? undefined : async (...args: unknown[]) => (name in handlers ? handlers[name](...args) : []),
    },
  );
  (window as unknown as { pywebview: unknown }).pywebview = { api };
  return { handlers };
});

const question = (id: number, text: string): Question =>
  ({
    question_id: id,
    topic: "Calculus",
    branch: "Limits",
    subtopic: "Squeeze theorem",
    latexcode: text,
    type: "Proof",
    in_syllabus: 1,
    source: "Tripos",
    solution: null,
    generated_solution: null,
    solution_outline: "Bound it on both sides.",
    hints: "Think of the squeeze theorem.",
    times_used: 0,
    tags: [],
  }) as unknown as Question;

const ROWS = [question(7, "Show that $x^2 \\to 0$ as $x \\to 0$."), question(8, "Evaluate the limit.")];

let root: Root | null = null;
let host: HTMLElement | null = null;

const settle = (ms = 30) =>
  act(async () => {
    await new Promise((r) => setTimeout(r, ms));
  });

async function mount(): Promise<HTMLElement> {
  host = document.createElement("div");
  document.body.appendChild(host);
  root = createRoot(host);
  await act(async () => {
    root!.render(
      <MemoryRouter>
        <BrowserPage />
      </MemoryRouter>,
    );
  });
  return host;
}

beforeEach(() => {
  for (const k of Object.keys(handlers)) delete handlers[k];
  handlers.get_config = () => null;
  handlers.search_questions = (): SearchResult => ({ rows: ROWS, total: 2 });
  handlers.get_question = (id) => ROWS.find((q) => q.question_id === id) ?? null;
});

afterEach(() => {
  act(() => root?.unmount());
  host?.remove();
  root = null;
  host = null;
});

describe("Browser", () => {
  it("says it is loading instead of claiming nothing matches", async () => {
    let release: (r: SearchResult) => void = () => {};
    handlers.search_questions = () => new Promise<SearchResult>((r) => (release = r));
    const el = await mount();
    await settle();
    expect(el.textContent).toContain("Loading questions");
    expect(el.textContent).not.toContain("No questions match");

    await act(async () => release({ rows: [], total: 0 }));
    await settle();
    expect(el.textContent).toContain("No questions match these filters.");
  });

  it("shows each question's text and opens it from anywhere on the row, hints closed", async () => {
    const el = await mount();
    await settle();
    const rows = el.querySelectorAll('[data-ui="question-row"]');
    expect(rows).toHaveLength(2);
    expect(rows[0].querySelector('[data-ui="question-excerpt"]')?.textContent).toContain("Show that");
    expect(rows[0].textContent).toContain("Calculus / Limits / Squeeze theorem");

    await act(async () => (rows[1].querySelector("td:last-child") as HTMLElement).click());
    await settle();
    const panel = el.querySelector('[data-ui="question-panel"]');
    expect(panel?.getAttribute("aria-label")).toBe("Question 8");
    expect(panel?.textContent).toContain("Hints");
    expect(panel?.textContent).not.toContain("Think of the squeeze theorem.");
    expect(panel?.textContent).not.toContain("Bound it on both sides.");
  });

  it("does not open a question when its checkbox is ticked", async () => {
    const el = await mount();
    await settle();
    const box = el.querySelector('[data-ui="question-row"] td:first-child [role="checkbox"], [data-ui="question-row"] td:first-child button, [data-ui="question-row"] td:first-child input') as HTMLElement;
    await act(async () => box.click());
    await settle();
    expect(el.querySelector('[data-ui="question-panel"]')).toBeNull();
    expect(el.textContent).toContain("1 selected");
    expect(el.textContent).toContain("Mark in syllabus");
  });

  it("drops a slow search that a later one has replaced", async () => {
    const pending: ((r: SearchResult) => void)[] = [];
    handlers.search_questions = () => new Promise<SearchResult>((r) => pending.push(r));
    const el = await mount();
    await settle();
    const search = el.querySelector('input[placeholder^="Text, topic"]') as HTMLInputElement;
    await act(async () => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")!.set!.call(search, "limit");
      search.dispatchEvent(new Event("input", { bubbles: true }));
    });
    await settle();
    expect(pending.length).toBeGreaterThanOrEqual(2);

    // The later search answers first; the earlier one arrives afterwards.
    await act(async () => pending[pending.length - 1]({ rows: [ROWS[1]], total: 1 }));
    await act(async () => pending[0]({ rows: ROWS, total: 2 }));
    await settle();
    expect(el.querySelectorAll('[data-ui="question-row"]')).toHaveLength(1);
    expect(el.textContent).toContain("1 match");
  });

  it("reports a failed search and offers to retry", async () => {
    handlers.search_questions = () => {
      throw new Error("database is locked");
    };
    const el = await mount();
    await settle();
    expect(el.querySelector('[role="alert"]')?.textContent).toContain("database is locked");

    handlers.search_questions = (): SearchResult => ({ rows: ROWS, total: 2 });
    const retry = Array.from(el.querySelectorAll("button")).find((b) => b.textContent?.includes("Try again"));
    await act(async () => retry!.click());
    await settle();
    expect(el.querySelectorAll('[data-ui="question-row"]')).toHaveLength(2);
  });
});
