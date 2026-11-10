/**
 * Writes the active loadout onto <html>: one data attribute per CSS-driven
 * slot (so any palette composes with any chrome), font variables from the
 * typography item, and the user's token overrides as inline variables.
 */

import { itemsFor, resolve } from "./registry";
import { motionReduced } from "./store";
import type { AppearanceState, SlotId } from "./types";

const ATTR_SLOTS: SlotId[] = ["chrome", "motion", "surface", "paper", "cursor", "icons", "logo", "charts", "arena"];

let appliedTokens: string[] = [];

function suffix(id: string | undefined): string {
  return id ? id.slice(id.indexOf(".") + 1) : "";
}

/**
 * Before settings load: put the saved palette (main.py passes it as
 * `#boot-theme=<id>`) on <html>, so the boot screen is already light or
 * dark. Returns whether the hash was the boot theme, so the caller can clear
 * it before the router reads it.
 */
export function applyBootTheme(hash: string): boolean {
  const m = /^#boot-theme=([\w-]+)$/.exec(hash);
  if (!m) return false;
  const pal = itemsFor("palette").find((it) => it.data?.theme === m[1]);
  if (pal) {
    document.documentElement.setAttribute("data-theme", m[1]);
    document.documentElement.setAttribute("data-dark", pal.data?.dark ? "true" : "false");
  }
  return true;
}

export function applyToDocument(state: Pick<AppearanceState, "loadout" | "settings">, focus: boolean): void {
  const root = document.documentElement;
  const { loadout, settings } = state;

  const pal = resolve(loadout, "palette");
  const theme = typeof pal?.data?.theme === "string" ? pal.data.theme : "default-light";
  root.setAttribute("data-theme", theme);
  root.setAttribute("data-dark", pal?.data?.dark ? "true" : "false");

  for (const slot of ATTR_SLOTS) root.setAttribute(`data-${slot}`, suffix(resolve(loadout, slot)?.id));

  const t = resolve(loadout, "typography")?.data as { body?: string; heading?: string; mono?: string; variation?: string } | undefined;
  if (t?.body) root.style.setProperty("--font-family", t.body);
  if (t?.heading) root.style.setProperty("--font-heading", t.heading);
  if (t?.mono) root.style.setProperty("--font-mono", t.mono);
  if (t?.variation) root.style.setProperty("font-variation-settings", t.variation);
  else root.style.removeProperty("font-variation-settings");

  for (const k of appliedTokens) root.style.removeProperty(k);
  appliedTokens = [];
  for (const [k, v] of Object.entries(settings.tokens)) {
    if (/^--[a-z-]+$/.test(k) && v) {
      root.style.setProperty(k, v);
      appliedTokens.push(k);
    }
  }

  root.setAttribute("data-whimsy", settings.whimsy);
  root.setAttribute("data-focus", focus ? "on" : "off");
  root.setAttribute("data-reduced-motion", motionReduced(settings) ? "on" : "off");
}
