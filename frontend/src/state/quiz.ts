import { create } from "zustand";

import type { ConceptRef, QuizAnswerResult, QuizQuestionFull, ReviewList } from "../lib/ipc";

/** Traverse and Discover browse the bank; review, lecture and mixed run a fixed
 * list the same way Discover does (DiscoverRunner). */
export type QuizMode = "traverse" | "discover" | "review" | "lecture" | "mixed";

export interface QuizState {
  mode: QuizMode;
  diversity: number;
  nQuestions: number;
  
  // Seed state
  useSeed: boolean;
  seedId: number | null;
  seedDiversity: number;
  
  // Filter state is managed by useGenerateStore now

  // What the list modes start from
  reviewKind: ReviewList;
  /** Lecture: the confirmed concepts. Mixed: the chosen technique tags. */
  concepts: ConceptRef[];
  
  // Active quiz state
  isStarted: boolean;
  quizId: string | null;
  questions: QuizQuestionFull[];
  currentIndex: number;
  quizStartTime: number | null;
  questionStartTime: number | null;

  // Answers in this session, by question id: the last submit / self-assess result
  results: Record<number, QuizAnswerResult>;
  // Questions whose answer or solution was opened before answering: not graded
  revealedIds: Record<number, true>;
  // Questions whose hint was opened before answering (sent as hints_used)
  hintedIds: Record<number, true>;
  // Lecture / mixed: the concept each question was picked for, by id
  conceptLabels: Record<string, string>;
  // Typed but unsubmitted answers, by question id (kept across page changes)
  drafts: Record<number, string[]>;
  // Traverse: unseen questions left in the pool; null until the session starts
  remaining: number | null;
  // Discover: the batch's diversity score; list modes: how many fewer than asked
  diversityScore: number | null;
  shortfall: number;

  // Toggle states
  showHint: boolean;
  showAnswer: boolean;
  showSolution: boolean;
  showMetadata: boolean;

  // Actions
  setMode: (mode: QuizMode) => void;
  setReviewKind: (kind: ReviewList) => void;
  setConcepts: (concepts: ConceptRef[]) => void;
  setConceptLabels: (labels: Record<string, string>) => void;
  setDiversity: (diversity: number) => void;
  setNQuestions: (n: number) => void;
  
  setUseSeed: (v: boolean) => void;
  setSeedId: (id: number | null) => void;
  setSeedDiversity: (div: number) => void;
  
  setIsStarted: (started: boolean) => void;
  setQuizId: (quizId: string | null) => void;
  setQuestions: (questions: QuizQuestionFull[]) => void;
  setCurrentIndex: (index: number) => void;
  setQuizStartTime: (time: number | null) => void;
  setQuestionStartTime: (time: number | null) => void;
  setResult: (questionId: number, result: QuizAnswerResult) => void;
  markRevealed: (questionId: number) => void;
  markHinted: (questionId: number) => void;
  setDraft: (questionId: number, inputs: string[]) => void;
  setRemaining: (remaining: number | null) => void;
  setDiversityScore: (score: number | null) => void;
  setShortfall: (shortfall: number) => void;

  setShowHint: (show: boolean) => void;
  setShowAnswer: (show: boolean) => void;
  setShowSolution: (show: boolean) => void;
  setShowMetadata: (show: boolean) => void;
  resetToggles: () => void;
  resetQuizState: () => void;
}

export const useQuizStore = create<QuizState>((set) => ({
  mode: "traverse",
  diversity: 0.5,
  nQuestions: 10,
  
  useSeed: false,
  seedId: null,
  seedDiversity: 0.5,

  reviewKind: "due",
  concepts: [],
  
  isStarted: false,
  quizId: null,
  questions: [],
  currentIndex: 0,
  quizStartTime: null,
  questionStartTime: null,

  results: {},
  revealedIds: {},
  hintedIds: {},
  conceptLabels: {},
  drafts: {},
  remaining: null,
  diversityScore: null,
  shortfall: 0,

  showHint: false,
  showAnswer: false,
  showSolution: false,
  showMetadata: false,

  setMode: (mode) => set({ mode }),
  setReviewKind: (reviewKind) => set({ reviewKind }),
  setConcepts: (concepts) => set({ concepts }),
  setConceptLabels: (conceptLabels) => set({ conceptLabels }),
  setDiversity: (diversity) => set({ diversity }),
  setNQuestions: (nQuestions) => set({ nQuestions }),
  
  setUseSeed: (useSeed) => set({ useSeed }),
  setSeedId: (seedId) => set({ seedId }),
  setSeedDiversity: (seedDiversity) => set({ seedDiversity }),
  
  setIsStarted: (isStarted) => set({ isStarted }),
  setQuizId: (quizId) => set({ quizId }),
  setQuestions: (questions) => set({ questions }),
  setCurrentIndex: (currentIndex) => set({ currentIndex }),
  setQuizStartTime: (quizStartTime) => set({ quizStartTime }),
  setQuestionStartTime: (questionStartTime) => set({ questionStartTime }),
  setResult: (questionId, result) => set((s) => ({ results: { ...s.results, [questionId]: result } })),
  markRevealed: (questionId) => set((s) => ({ revealedIds: { ...s.revealedIds, [questionId]: true } })),
  markHinted: (questionId) => set((s) => ({ hintedIds: { ...s.hintedIds, [questionId]: true } })),
  setDraft: (questionId, inputs) => set((s) => ({ drafts: { ...s.drafts, [questionId]: inputs } })),
  setRemaining: (remaining) => set({ remaining }),
  setDiversityScore: (diversityScore) => set({ diversityScore }),
  setShortfall: (shortfall) => set({ shortfall }),

  setShowHint: (showHint) => set({ showHint }),
  setShowAnswer: (showAnswer) => set({ showAnswer }),
  setShowSolution: (showSolution) => set({ showSolution }),
  setShowMetadata: (showMetadata) => set({ showMetadata }),
  resetToggles: () => set({ showHint: false, showAnswer: false, showSolution: false, showMetadata: false }),
  resetQuizState: () => set({
    isStarted: false,
    quizId: null,
    questions: [],
    currentIndex: 0,
    quizStartTime: null,
    questionStartTime: null,
    results: {},
    revealedIds: {},
    hintedIds: {},
    conceptLabels: {},
    drafts: {},
    remaining: null,
    diversityScore: null,
    shortfall: 0,
    showHint: false,
    showAnswer: false,
    showSolution: false,
    showMetadata: false,
  }),
}));
