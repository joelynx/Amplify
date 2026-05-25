/**
 * Theme application + sound playback (spec §11.2).
 *
 * `applyTheme` flips a `data-theme` attribute on `<html>`, which causes the
 * `:root[data-theme="X"]` rules in `styles/themes/<id>/theme.css` to take over
 * the CSS-variable tokens. No reload required.
 *
 * `playSound` is fire-and-forget: it asks the backend to surface the event
 * (for logging / potential server-side hooks) AND, when an asset exists,
 * tries to play it via the Web Audio API. Missing files fail silently — the
 * sound pack is allowed to be incomplete (spec §11.2).
 */

import { ipc } from "./ipc";

export type ThemeId =
  | "default-light"
  | "default-dark"
  | "pastel"
  | "frutiger-aero"
  | "pixel-art"
  | "windows-xp"
  | "comic"
  | "ascii"
  | "android-kitkat";

export type SoundEvent = "click" | "generate" | "error" | "success" | "theme_switch";

const DEFAULT_THEME: ThemeId = "default-light";

/** Themes for which the Accessibility-mode toggle is meaningful (spec §11.4 —
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

let currentTheme: ThemeId = DEFAULT_THEME;
let a11yMode = false;

export function getCurrentTheme(): ThemeId {
  return currentTheme;
}

export function getAccessibilityMode(): boolean {
  return a11yMode;
}

export function isFlavorTheme(id: ThemeId): boolean {
  return (FLAVOR_THEMES as readonly string[]).includes(id);
}

export async function applyTheme(themeId: ThemeId, opts?: { persist?: boolean }): Promise<void> {
  document.documentElement.setAttribute("data-theme", themeId);
  currentTheme = themeId;
  if (opts?.persist !== false) {
    await ipc.set_theme(themeId);
  }
  // Fire-and-forget switch sound.
  void playSound("theme_switch");
}

/** Toggle high-contrast text override (spec §11.4). Only meaningful for
 * flavor themes — default-light / default-dark already hit WCAG AA. */
export async function setAccessibilityMode(
  on: boolean,
  opts?: { persist?: boolean },
): Promise<void> {
  if (on) document.documentElement.setAttribute("data-a11y", "on");
  else document.documentElement.removeAttribute("data-a11y");
  a11yMode = on;
  if (opts?.persist !== false) {
    await ipc.set_config("THEME_A11Y_MODE", on);
  }
}

/** Frontend-side audio playback; fail-soft when the asset is missing. The
 * backend's `play_sound` is also called so server-side hooks see the event. */
export function playSound(event: SoundEvent): void {
  ipc.play_sound(event).catch(() => {
    /* fail soft — bridge may not be up yet */
  });
  // Future: try `new Audio(asset_url)` once theme sound packs are shipped.
  // For Step 12 the asset directories are empty placeholders.
}
