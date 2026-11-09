/**
 * Small UI state that should survive a restart: dismissed seasonal banners,
 * the last Themes tab. PyWebView runs in private mode, so localStorage is
 * wiped on every launch; these live in configs.UI_PREFS instead. Loaded once at startup (App.tsx), then read
 * synchronously.
 */

import { useSyncExternalStore } from "react";

import { ipc } from "../lib/ipc";

const CONFIG_KEY = "UI_PREFS";

let prefs: Record<string, unknown> = {};
const listeners = new Set<() => void>();
let saveTimer: ReturnType<typeof setTimeout> | null = null;

export async function loadPrefs(): Promise<void> {
  const v = await ipc.get_config(CONFIG_KEY).catch(() => null);
  prefs = v && typeof v === "object" && !Array.isArray(v) ? (v as Record<string, unknown>) : {};
  listeners.forEach((fn) => fn());
}

export function getPref<T>(key: string, fallback: T): T {
  return key in prefs ? (prefs[key] as T) : fallback;
}

export function setPref(key: string, value: unknown): void {
  prefs = { ...prefs, [key]: value };
  listeners.forEach((fn) => fn());
  if (saveTimer) clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {
    ipc.set_config(CONFIG_KEY, prefs).catch(() => {});
  }, 300);
}

export function subscribePrefs(fn: () => void): () => void {
  listeners.add(fn);
  return () => {
    listeners.delete(fn);
  };
}

/** A pref as React state. `fallback` must be stable (a literal or a module constant). */
export function usePref<T>(key: string, fallback: T): T {
  return useSyncExternalStore(subscribePrefs, () => getPref(key, fallback), () => fallback);
}
