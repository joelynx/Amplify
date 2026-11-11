import { create } from "zustand";

import { useGenerateStore } from "./generate";

interface SubjectState {
  /** Currently-active subject name. `null` = no subject ("Any subject"). */
  active: string | null;
  setActive: (name: string | null) => void;
}

export const useSubjectStore = create<SubjectState>((set, get) => ({
  active: null,
  setActive: (name) => {
    if (name === get().active) return;
    set({ active: name });
    // The active subject is the scope everywhere: the Generate / Quiz form
    // follows it. A page can still pick another subject for itself afterwards.
    useGenerateStore.getState().setSubject(name);
  },
}));
