/**
 * Generate and Quiz setup: the main action sits in a bar that is always
 * rendered, says what is missing, and the optional settings start collapsed.
 * Home leads with the study actions. The backend is a stub bridge.
 */

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { filterSummary, paperSummary } from "../../components/generate/OutputSettings";
import { todayStatus } from "../../components/quiz/TodayCard";
import type { ReviewSummary } from "../../lib/ipc";
import { useGenerateStore } from "../../state/generate";
import { useQuizStore } from "../../state/quiz";
import GeneratePage from "../Generate";
import QuizPage from "../Quiz";
import WelcomePage from "../Welcome";

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

// The stub bridge has to exist before any module asks for it (the first miss is cached).
const { SUMMARY } = vi.hoisted(() => {
  const SUMMARY = {
    counts: { due: 3, mistakes: 1, assisted: 0 },
    next_due: null,
    tracked: 4,
    retired: 0,
    lists: { due: [], mistakes: [], assisted: [] },
  } as unknown as import("../../lib/ipc").ReviewSummary;
  const replies: Record<string, unknown> = {
    list_subjects: ["Calculus"],
    get_concept_tree: { Calculus: { Limits: ["Squeeze theorem"] } },
    get_config: null,
    get_active_subject: null,
    count_matching_questions: 42,
    get_review_summary: SUMMARY,
  };
  // Any other call answers with an empty list. Not a thenable: the bridge is passed through a promise.
  const api = new Proxy(
    {},
    { get: (_t, name: string) => (name === "then" ? undefined : async () => (name in replies ? replies[name] : [])) },
  );
  (window as unknown as { pywebview: unknown }).pywebview = { api };
  return { SUMMARY };
});

let root: Root | null = null;
let host: HTMLElement | null = null;

async function mount(page: React.ReactElement): Promise<HTMLElement> {
  host = document.createElement("div");
  document.body.appendChild(host);
  root = createRoot(host);
  await act(async () => {
    root!.render(<MemoryRouter>{page}</MemoryRouter>);
  });
  // Let the lookups and the debounced count settle.
  await act(async () => {
    await new Promise((r) => setTimeout(r, 400));
  });
  return host;
}

afterEach(() => {
  act(() => root?.unmount());
  host?.remove();
  root = null;
  host = null;
});

const button = (el: HTMLElement, text: string) =>
  Array.from(el.querySelectorAll("button")).find((b) => b.textContent?.includes(text));

describe("Generate setup", () => {
  it("keeps the action bar in view with the count and what is missing", async () => {
    const el = await mount(<GeneratePage />);
    const bar = el.querySelector('[data-ui="action-bar"]');
    expect(bar?.textContent).toContain("42 match");
    expect(bar?.textContent).toContain("Tick at least one topic");
    expect(button(el, "Generate PDF")?.disabled).toBe(true);
  });

  it("collapses the other filters and print options until asked for", async () => {
    const el = await mount(<GeneratePage />);
    const more = button(el, "More filters");
    expect(more?.getAttribute("aria-expanded")).toBe("false");
    expect(el.textContent).not.toContain("Minimum difficulty");
    expect(el.textContent).not.toContain("Save directory");
    act(() => more!.click());
    expect(el.textContent).toContain("Minimum difficulty");
    act(() => button(el, "More filters")!.click());
  });
});

describe("Quiz setup", () => {
  it("recommends Review while questions are waiting, and can start another mode at once", async () => {
    const el = await mount(<QuizPage />);
    expect(button(el, "Questions due again")?.textContent).toContain("Recommended");
    expect(useQuizStore.getState().mode).toBe("review");

    act(() => button(el, "One question at a time")!.click());
    const bar = el.querySelector('[data-ui="action-bar"]');
    expect(bar?.textContent).toContain("42 questions available");
    const start = button(el, "Start Traverse session");
    expect(start?.disabled).toBe(false);
    expect(button(el, "More options")?.getAttribute("aria-expanded")).toBe("false");
  });
});

describe("Home", () => {
  it("leads with review, practice and creating a paper", async () => {
    const el = await mount(<WelcomePage />);
    expect(el.textContent).toContain("3 questions due for review");
    for (const label of ["Review due questions", "Start practice", "From a lecture", "Create a paper"]) {
      expect(button(el, label), label).toBeDefined();
    }
    expect(button(el, "Enter")).toBeUndefined();
  });

  it("offers the running session first", async () => {
    useQuizStore.getState().setIsStarted(true);
    const el = await mount(<WelcomePage />);
    expect(button(el, "Resume session")).toBeDefined();
    expect(button(el, "Start practice")).toBeUndefined();
    useQuizStore.getState().resetQuizState();
  });
});

describe("summaries", () => {
  it("says what is waiting today", () => {
    expect(todayStatus(SUMMARY).action).toEqual({ label: "Review due questions", kind: "due" });
    expect(todayStatus({ ...SUMMARY, counts: { due: 0, mistakes: 0, assisted: 0 } as ReviewSummary["counts"] }).action).toBeNull();
    expect(todayStatus(null).action).toBeNull();
  });

  it("names what is set inside the collapsed sections", () => {
    const d = useGenerateStore.getState();
    expect(filterSummary(d)).toBe("None set");
    expect(filterSummary({ ...d, sources: ["A", "B"], minDifficulty: 3, inSyllabusOnly: false })).toBe(
      "2 sources · difficulty 3+ · outside syllabus too",
    );
    expect(paperSummary({ ...d, solutions: "appendix", saveDirectory: "C:\\Users\\me\\Papers" })).toBe(
      "Solutions: appendix · saved to Papers",
    );
    expect(paperSummary({ ...d, solutions: "none", saveDirectory: null })).toBe("No solutions · no save folder chosen");
  });
});
