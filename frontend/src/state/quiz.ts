import { create } from "zustand";

import type { QuizQuestionFull } from "../lib/ipc";

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
  questions: QuizQuestionFull[];
  currentIndex: number;
  quizStartTime: number | null;
  questionStartTime: number | null;
  
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
  setQuestions: (questions: QuizQuestionFull[]) => void;
  setCurrentIndex: (index: number) => void;
  setQuizStartTime: (time: number | null) => void;
  setQuestionStartTime: (time: number | null) => void;
  
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
  questions: [],
  currentIndex: 0,
  quizStartTime: null,
  questionStartTime: null,
  
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
  setQuestions: (questions) => set({ questions }),
  setCurrentIndex: (currentIndex) => set({ currentIndex }),
  setQuizStartTime: (quizStartTime) => set({ quizStartTime }),
  setQuestionStartTime: (questionStartTime) => set({ questionStartTime }),
  
  setShowHint: (showHint) => set({ showHint }),
  setShowAnswer: (showAnswer) => set({ showAnswer }),
  setShowSolution: (showSolution) => set({ showSolution }),
  setShowMetadata: (showMetadata) => set({ showMetadata }),
  resetToggles: () => set({ showHint: false, showAnswer: false, showSolution: false, showMetadata: false }),
  resetQuizState: () => set({
    isStarted: false,
    questions: [],
    currentIndex: 0,
    quizStartTime: null,
    questionStartTime: null,
    showHint: false,
    showAnswer: false,
    showSolution: false,
    showMetadata: false,
  }),
}));
