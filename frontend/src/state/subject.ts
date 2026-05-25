import { create } from "zustand";

interface SubjectState {
  /** Currently-active subject name. `null` = no subject ("Any subject"). */
  active: string | null;
  setActive: (name: string | null) => void;
}

export const useSubjectStore = create<SubjectState>((set) => ({
  active: null,
  setActive: (name) => set({ active: name }),
}));
