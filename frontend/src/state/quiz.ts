import { create } from "zustand";

import type { QuizAnswerResult, QuizQuestionFull } from "../lib/ipc";

export interface QuizState {
  mode: "traverse" | "discover";
  diversity: number;
  nQuestions: number;
  
  // Seed state
  useSeed: boolean;
  seedId: number | null;
  seedDiversity: number;
  
  // Filter state is managed by useGenerateStore now
  
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

  // Toggle states
  showHint: boolean;
  showAnswer: boolean;
  showSolution: boolean;
  showMetadata: boolean;

  // Actions
  setMode: (mode: "traverse" | "discover") => void;
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
  
  isStarted: false,
  quizId: null,
  questions: [],
  currentIndex: 0,
  quizStartTime: null,
  questionStartTime: null,

  results: {},
  revealedIds: {},

  showHint: false,
  showAnswer: false,
  showSolution: false,
  showMetadata: false,

  setMode: (mode) => set({ mode }),
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
    showHint: false,
    showAnswer: false,
    showSolution: false,
    showMetadata: false,
  }),
}));
