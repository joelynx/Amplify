/**
 * Theme compatibility layer (spec §11.2). Since the makeover a "theme" is a
 * preset loadout in the appearance system (src/appearance/); this module
 * keeps the old entry points working on top of it.
 *
 * `applyTheme(id)` applies the preset with that id (the original twelve
 * theme ids are preset ids). Sounds are played by the appearance sound
 * engine from app events, so `playSound` now just emits the matching event.
 */

import { emit } from "../appearance/events";
import { useAppearance } from "../appearance/store";
import { ipc } from "./ipc";

export type ThemeId = string;

export type SoundEvent = "click" | "generate" | "error" | "success" | "theme_switch";

/** Presets for which the Accessibility-mode toggle is meaningful (spec §11.4 —
 * flavor themes only; the two defaults are already WCAG AA). */
export const FLAVOR_THEMES: readonly ThemeId[] = [
  "pastel",
  "frutiger-aero",
  "pixel-art",
  "windows-xp",
  "comic",
  "ascii",
  "android-kitkat",
];

export function getCurrentTheme(): ThemeId {
  return useAppearance.getState().preset ?? "custom";
}

export function getAccessibilityMode(): boolean {
  return document.documentElement.getAttribute("data-a11y") === "on";
}

export function isFlavorTheme(id: ThemeId): boolean {
  return id !== "default-light" && id !== "default-dark";
}

export async function applyTheme(themeId: ThemeId): Promise<void> {
  useAppearance.getState().applyPreset(themeId);
  emit({ type: "theme_switch" });
}

/** High-contrast text override (spec §11.4), stored in configs.THEME_A11Y_MODE. */
export async function setAccessibilityMode(on: boolean, opts?: { persist?: boolean }): Promise<void> {
  if (on) document.documentElement.setAttribute("data-a11y", "on");
  else document.documentElement.removeAttribute("data-a11y");
  if (opts?.persist !== false) {
    await ipc.set_config("THEME_A11Y_MODE", on);
  }
}

const SOUND_EVENTS = {
  click: { type: "click" },
  generate: { type: "generate_done" },
  error: { type: "generate_error" },
  success: { type: "generate_done" },
  theme_switch: { type: "theme_switch" },
} as const;

export function playSound(event: SoundEvent): void {
  emit(SOUND_EVENTS[event]);
}
