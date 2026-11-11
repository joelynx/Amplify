/**
 * Coming back to a running Traverse session (the runner remounts on every
 * page change): the question, the remaining count, a typed draft and a
 * working Next button are all still there. Activating a subject scopes the
 * Generate / Quiz form.
 */

import { act } from "react";
import { createRoot } from "react-dom/client";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { QuizQuestionFull } from "../../../lib/ipc";
import { useGenerateStore } from "../../../state/generate";
import { useQuizStore } from "../../../state/quiz";
import { useSubjectStore } from "../../../state/subject";
import { TraverseRunner } from "../TraverseRunner";

// Bookmarks and notes talk to the backend; they are not part of this test.
vi.mock("../../notes/QuestionNotes", () => ({ BookmarkButton: () => null, SelfExplain: () => null }));

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const QUESTION: QuizQuestionFull = {
  question_id: 42,
  topic: "Calculus",
  branch: "Limits",
  subtopic: "Squeeze theorem",
  latexcode: "Evaluate the limit.",
  type: null,
  hints: null,
  answer: null,
  solution: null,
  instructions: null,
  source: null,
  difficulty_rating: null,
  tags: [],
  answer_fields: [{ kind: "number", label: "", ask: "", unit: null }] as unknown as QuizQuestionFull["answer_fields"],
};

beforeEach(() => {
  useQuizStore.getState().resetQuizState();
});

describe("returning to a Traverse session", () => {
  it("keeps the count, the draft and a usable Next button", () => {
    const s = useQuizStore.getState();
    s.setIsStarted(true);
    s.setQuizId("quiz-1");
    s.setQuestions([QUESTION]);
    s.setRemaining(199);
    s.setDraft(42, ["3.14"]);

    const host = document.createElement("div");
    document.body.appendChild(host);
    const root = createRoot(host);
    act(() => root.render(<TraverseRunner />));
    try {
      expect(host.textContent).toContain("199");
      expect(host.querySelector("input:not([type=range])")).toHaveProperty("value", "3.14");
      const next = Array.from(host.querySelectorAll("button")).find((b) => b.textContent?.includes("Next Question"));
      expect(next).toBeDefined();
      expect(next?.disabled).toBe(false);
      expect(host.querySelector<HTMLInputElement>("input[type=range]")?.disabled).toBe(false);
    } finally {
      act(() => root.unmount());
      host.remove();
    }
  });

  it("clears drafts and the count when the session ends", () => {
    const s = useQuizStore.getState();
    s.setRemaining(5);
    s.setDraft(42, ["1"]);
    s.resetQuizState();
    expect(useQuizStore.getState().remaining).toBeNull();
    expect(useQuizStore.getState().drafts).toEqual({});
  });
});

describe("active subject", () => {
  it("scopes the Generate / Quiz form when it changes", () => {
    useSubjectStore.getState().setActive("Calculus");
    expect(useGenerateStore.getState().subject).toBe("Calculus");

    // A page-level override survives a refresh that reports the same active subject.
    useGenerateStore.getState().setSubject(null);
    useSubjectStore.getState().setActive("Calculus");
    expect(useGenerateStore.getState().subject).toBeNull();

    useSubjectStore.getState().setActive(null);
    expect(useGenerateStore.getState().subject).toBeNull();
  });
});
