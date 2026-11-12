/**
 * Safeguards around help, flags, resets and unsaved text: the quiz says what a
 * hint or reveal costs before the click, a flagged hint is hidden, the subject
 * reset names its subject, and unsaved edits survive leaving the page.
 * The backend is a stub bridge.
 */

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { TagTray } from "../../components/generate/TagTray";
import { NoteEditor } from "../../components/notes/QuestionNotes";
import { QuestionViewer } from "../../components/quiz/QuestionViewer";
import type { QuizQuestionFull } from "../../lib/ipc";
import { useGenerateStore } from "../../state/generate";
import { useQuizStore } from "../../state/quiz";
import { useSubjectStore } from "../../state/subject";
import SettingsPage from "../Settings";
import SubjectsPage from "../Subjects";

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

// The stub bridge has to exist before any module asks for it (the first miss is cached).
const { calls, replies } = vi.hoisted(() => {
  const calls: Array<[string, unknown[]]> = [];
  const replies: Record<string, unknown> = {
    get_config: null,
    get_active_subject: null,
    get_question_notes: {},
    get_content_flags: {},
    get_concept_tree: {},
    get_seed_diagnostics: null,
    get_difficulty_state: null,
  };
  // Any other call answers with an empty list. Not a thenable: the bridge is passed through a promise.
  const api = new Proxy(
    {},
    {
      get: (_t, name: string) =>
        name === "then"
          ? undefined
          : async (...args: unknown[]) => {
              calls.push([name, args]);
              return name in replies ? replies[name] : [];
            },
    },
  );
  (window as unknown as { pywebview: unknown }).pywebview = { api };
  return { calls, replies };
});

let root: Root | null = null;
let host: HTMLElement | null = null;

const settle = () =>
  act(async () => {
    await new Promise((r) => setTimeout(r, 50));
  });

async function mount(node: React.ReactElement): Promise<HTMLElement> {
  host = document.createElement("div");
  document.body.appendChild(host);
  root = createRoot(host);
  await act(async () => {
    root!.render(<MemoryRouter>{node}</MemoryRouter>);
  });
  await settle();
  return host;
}

function unmount() {
  act(() => root?.unmount());
  host?.remove();
  root = null;
  host = null;
}

afterEach(() => {
  unmount();
  calls.length = 0;
  replies.get_content_flags = {};
});

const button = (el: ParentNode, text: string) =>
  Array.from(el.querySelectorAll("button")).find((b) => b.textContent?.includes(text));

/** Type into a controlled input the way a keystroke would. */
function type(el: HTMLInputElement | HTMLTextAreaElement, value: string) {
  const proto = el instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
  Object.getOwnPropertyDescriptor(proto, "value")!.set!.call(el, value);
  act(() => {
    el.dispatchEvent(new Event("input", { bubbles: true }));
  });
}

const QUESTION = {
  question_id: 7,
  topic: "Calculus",
  branch: "Limits",
  subtopic: "Squeeze theorem",
  type: "numerical",
  source: "Book",
  difficulty_rating: null,
  tags: [],
  instructions: "",
  latexcode: "Find the limit.",
  hints: "Bound the sine.",
  answer: "0",
  solution: "Squeeze it.",
  answer_fields: [{ label: "", kind: "number" }],
} as unknown as QuizQuestionFull;

describe("Quiz help", () => {
  it("puts help after the answer area and says what it costs before the click", async () => {
    useQuizStore.setState({ hintLevel: 0, showAnswer: false, showSolution: false, results: {} });
    const el = await mount(
      <QuestionViewer question={QUESTION}>
        <div data-ui="answer-area" />
      </QuestionViewer>,
    );
    const help = el.querySelector('[data-ui="help-row"]')!;
    const answer = el.querySelector('[data-ui="answer-area"]')!;
    expect(answer.compareDocumentPosition(help) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    const note = el.querySelector('[data-ui="help-consequence"]')?.textContent ?? "";
    expect(note).toContain("solved with help");
    expect(note).toContain("ungraded");
    expect(el.textContent).not.toContain("Bound the sine.");
  });

  it("hides a hint the student flagged, and files a new flag", async () => {
    replies.get_content_flags = { "7": ["hint"] };
    useQuizStore.setState({ hintLevel: 1, showAnswer: false, showSolution: true, results: {} });
    const el = await mount(<QuestionViewer question={QUESTION} />);
    const hint = el.querySelector('[data-ui="flaggable-hint"]')!;
    expect(hint.textContent).toContain("You flagged this hint as unusable.");
    expect(hint.textContent).not.toContain("Bound the sine.");
    act(() => button(hint, "Show it anyway")!.click());
    expect(hint.textContent).toContain("Bound the sine.");

    const solution = el.querySelector('[data-ui="flaggable-solution"]')!;
    expect(solution.textContent).toContain("Squeeze it.");
    await act(async () => button(solution, "Report a problem with this solution")!.click());
    expect(calls).toContainEqual(["set_content_flag", [7, "solution", true]]);
    expect(solution.textContent).not.toContain("Squeeze it.");
    useQuizStore.setState({ hintLevel: 0, showSolution: false });
  });

  it("reveals the hint tiers one at a time, then greys the button out", async () => {
    useQuizStore.setState({ hintLevel: 0, showAnswer: false, showSolution: false, results: {}, hintedIds: {} });
    const tiered = {
      ...QUESTION,
      hint_tiers: ["Bound the sine.", "Use $|\\sin x| \\le 1$.", "Squeeze between $\\pm 1/x$."],
    } as QuizQuestionFull;
    const el = await mount(<QuestionViewer question={tiered} />);
    const shown = () => Array.from(el.querySelectorAll('[data-ui="hint-tier"]'));

    act(() => button(el, "Show hint")!.click());
    expect(shown()).toHaveLength(1);
    expect(shown()[0].textContent).toContain("Hint 1 of 3");
    expect(useQuizStore.getState().hintedIds[7]).toBe(1);

    act(() => button(el, "Show additional hint")!.click());
    act(() => button(el, "Show additional hint")!.click());
    expect(shown()).toHaveLength(3);
    expect(useQuizStore.getState().hintedIds[7]).toBe(3);
    expect(button(el, "Show additional hint")!.disabled).toBe(true);
    useQuizStore.setState({ hintLevel: 0, hintedIds: {} });
  });

  it("greys the button out after a question's only hint", async () => {
    useQuizStore.setState({ hintLevel: 0, showAnswer: false, showSolution: false, results: {}, hintedIds: {} });
    const el = await mount(<QuestionViewer question={{ ...QUESTION, hint_tiers: ["Bound the sine."] }} />);
    act(() => button(el, "Show hint")!.click());
    expect(el.textContent).toContain("Bound the sine.");
    expect(el.textContent).not.toContain("Hint 1 of");
    expect(button(el, "Show additional hint")!.disabled).toBe(true);
    useQuizStore.setState({ hintLevel: 0, hintedIds: {} });
  });
});

describe("Tag rules", () => {
  it("names the rule on the selector and on every chip", async () => {
    useGenerateStore.setState({ tags: { compulsory: ["proof"], optional: ["limits"], excluded: ["long"] } });
    const el = await mount(<TagTray available={["proof", "limits", "long", "series"]} />);
    const group = el.querySelector('[aria-label="Rule for the next tag"]')!;
    expect(button(group, "Match any")?.getAttribute("aria-pressed")).toBe("true");
    act(() => button(group, "Exclude")!.click());
    expect(button(group, "Exclude")?.getAttribute("aria-pressed")).toBe("true");
    expect(el.textContent).toContain("Must include:proof");
    expect(el.textContent).toContain("Match any:limits");
    expect(el.textContent).toContain("Exclude:long");
    useGenerateStore.setState({ tags: { compulsory: [], optional: [], excluded: [] } });
  });
});

describe("Settings maintenance", () => {
  it("keeps the resets at the bottom and names the subject before clearing it", async () => {
    useSubjectStore.setState({ active: null });
    let el = await mount(<SettingsPage />);
    const section = () => el.querySelector('[data-ui="maintenance"]')!;
    expect(section().compareDocumentPosition(el.querySelector('[data-ui="content-flags"]')!) & Node.DOCUMENT_POSITION_PRECEDING).toBeTruthy();
    expect(button(section(), "Clear subject usage")?.disabled).toBe(true);
    unmount();

    useSubjectStore.setState({ active: "Calculus" });
    el = await mount(<SettingsPage />);
    act(() => button(section(), "Clear subject usage")!.click());
    const dialog = document.querySelector('[role="dialog"]')!;
    expect(dialog.textContent).toContain("Clear usage for “Calculus”?");
    expect(button(dialog, "Clear usage for Calculus")).toBeTruthy();
    expect(calls.some(([name]) => name.includes("reset"))).toBe(false);
    act(() => button(dialog, "Cancel")!.click());
    useSubjectStore.setState({ active: null });
  });
});

describe("Unsaved text", () => {
  it("keeps an unsaved subject edit while the student is on another page", async () => {
    let el = await mount(<SubjectsPage />);
    type(el.querySelector<HTMLInputElement>('input[placeholder="e.g. Math I"]')!, "Signals");
    expect(el.textContent).toContain("Unsaved changes");
    unmount();

    el = await mount(<SubjectsPage />);
    expect(el.querySelector<HTMLInputElement>('input[placeholder="e.g. Math I"]')!.value).toBe("Signals");
    expect(el.textContent).toContain("kept from before you left this page");

    // Starting a new subject asks before it throws the edit away.
    act(() => button(el, "New")!.click());
    const dialog = document.querySelector('[role="dialog"]')!;
    expect(dialog.textContent).toContain("Discard unsaved changes?");
    act(() => button(dialog, "Discard changes")!.click());
    expect(el.querySelector<HTMLInputElement>('input[placeholder="e.g. Math I"]')!.value).toBe("");
  });

  it("keeps an unsaved note when the question is left and opened again", async () => {
    let el = await mount(<NoteEditor questionId={7} />);
    type(el.querySelector("textarea")!, "Dominated convergence.");
    expect(el.textContent).toContain("Not saved yet");
    unmount();

    el = await mount(<NoteEditor questionId={7} />);
    expect(el.querySelector("textarea")!.value).toBe("Dominated convergence.");
    await act(async () => button(el, "Save note")!.click());
    expect(calls).toContainEqual(["save_question_note", [7, "Dominated convergence."]]);
    expect(el.textContent).not.toContain("Not saved yet");
  });
});
