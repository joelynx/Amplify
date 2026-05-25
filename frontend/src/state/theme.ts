import { create } from "zustand";

export type ThemeId = "default-light" | "default-dark" | "pastel"; // expanded in Step 12

interface ThemeState {
  id: ThemeId;
  setId: (id: ThemeId) => void;
}

export const useThemeStore = create<ThemeState>((set) => ({
  id: "default-light",
  setId: (id) => set({ id }),
}));
