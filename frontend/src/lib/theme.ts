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

export type ThemeId = "default-light" | "default-dark" | "pastel";
export type SoundEvent = "click" | "generate" | "error" | "success" | "theme_switch";

const DEFAULT_THEME: ThemeId = "default-light";

let currentTheme: ThemeId = DEFAULT_THEME;

export function getCurrentTheme(): ThemeId {
  return currentTheme;
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

/** Frontend-side audio playback; fail-soft when the asset is missing. The
 * backend's `play_sound` is also called so server-side hooks see the event. */
export function playSound(event: SoundEvent): void {
  ipc.play_sound(event).catch(() => {
    /* fail soft — bridge may not be up yet */
  });
  // Future: try `new Audio(asset_url)` once theme sound packs are shipped.
  // For Step 12 the asset directories are empty placeholders.
}
