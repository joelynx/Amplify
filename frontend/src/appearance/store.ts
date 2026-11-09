/**
 * Appearance state: the active loadout, settings and saved loadouts.
 * Persisted as one JSON blob in configs.APPEARANCE. The palette is mirrored
 * into configs.THEME_SELECTED, which the backend uses to enforce reward locks.
 */

import { create } from "zustand";

import { ipc } from "../lib/ipc";
import { PRESETS, getPreset } from "./presets";
import { DEFAULT_LOADOUT, getItem, normalizeLoadout } from "./registry";
import type { AppearanceSettings, AppearanceState, Loadout, SavedLoadout, SlotId } from "./types";

export const DEFAULT_SETTINGS: AppearanceSettings = {
  whimsy: "subtle",
  focus: false,
  focusInTimed: true,
  reducedMotion: "system",
  muted: false,
  volumes: { master: 0.6, ui: 0.35, feedback: 0.6, celebration: 0.6 },
  seasonal: true,
  eggs: true,
  room: true,
  greetingName: "",
  exam: { label: "", date: null },
  tokens: {},
  dayNight: { enabled: false, night: null, from: 19, to: 7 },
};

interface Store extends AppearanceState {
  ready: boolean;
  /** Preset ids the backend reports as locked (reward themes not yet earned). */
  locked: Set<string>;
  /** Set while a timed quiz runs, for settings.focusInTimed. */
  timedActive: boolean;
  /** Secrets found (easter eggs), mirrored from configs.EASTER_EGGS. */
  secrets: Set<string>;
  /** The day loadout, kept while the night loadout is showing. */
  dayStash: Loadout | null;
  load: () => Promise<void>;
  applyPreset: (id: string, keep?: SlotId[]) => void;
  setSlot: (slot: SlotId, id: string) => void;
  setSettings: (patch: Partial<AppearanceSettings>) => void;
  saveLoadout: (name: string) => void;
  deleteLoadout: (name: string) => void;
  useLoadout: (saved: SavedLoadout) => void;
  setTimedActive: (on: boolean) => void;
  addSecret: (id: string) => void;
  /** Swap to / from the night loadout (settings.dayNight) for the given time. */
  syncDayNight: (now?: Date) => void;
}

/** True when `hour` falls in the night window [from, to) (which may wrap midnight). */
export function inNightWindow(hour: number, from: number, to: number): boolean {
  if (from === to) return false;
  return from < to ? hour >= from && hour < to : hour >= from || hour < to;
}

const CONFIG_KEY = "APPEARANCE";
const SECRETS_KEY = "EASTER_EGGS";

function presetLoadout(id: string): Loadout {
  const p = getPreset(id);
  return normalizeLoadout({ ...DEFAULT_LOADOUT, ...(p?.slots ?? {}) });
}

function paletteTheme(loadout: Loadout): string {
  const theme = getItem(loadout.palette)?.data?.theme;
  return typeof theme === "string" ? theme : "default-light";
}

let saveTimer: ReturnType<typeof setTimeout> | null = null;

function persist(state: Store, paletteChanged: boolean): void {
  if (!state.ready) return;
  if (saveTimer) clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {
    const blob: AppearanceState & { dayStash: Loadout | null } = {
      loadout: state.dayStash ?? state.loadout,
      preset: state.preset,
      settings: state.settings,
      saved: state.saved,
      dayStash: null,
    };
    ipc.set_config(CONFIG_KEY, blob).catch(() => {});
  }, 250);
  if (paletteChanged) {
    ipc.set_theme(paletteTheme(state.loadout)).catch((e: unknown) => console.warn("set_theme refused", e));
  }
}

export const useAppearance = create<Store>((set, get) => ({
  loadout: presetLoadout("default-light"),
  preset: "default-light",
  settings: DEFAULT_SETTINGS,
  saved: [],
  ready: false,
  locked: new Set(),
  timedActive: false,
  secrets: new Set(),
  dayStash: null,

  load: async () => {
    const [blob, oldTheme, oldA11y, themes, secrets] = await Promise.all([
      ipc.get_config(CONFIG_KEY).catch(() => null) as Promise<Partial<AppearanceState> | null>,
      ipc.get_config("THEME_SELECTED").catch(() => null) as Promise<string | null>,
      ipc.get_config("THEME_A11Y_MODE").catch(() => null) as Promise<boolean | null>,
      ipc.list_themes().catch(() => []),
      ipc.get_config(SECRETS_KEY).catch(() => null) as Promise<string[] | null>,
    ]);
    const locked = new Set(themes.filter((t) => t.locked).map((t) => t.id));
    if (blob && blob.loadout) {
      set({
        loadout: normalizeLoadout(blob.loadout),
        preset: blob.preset ?? null,
        settings: { ...DEFAULT_SETTINGS, ...(blob.settings ?? {}) },
        saved: blob.saved ?? [],
        locked,
        secrets: new Set(secrets ?? []),
        ready: true,
      });
    } else {
      // First run with the new system: start from the old theme choice.
      const presetId = oldTheme && getPreset(oldTheme) && !locked.has(oldTheme) ? oldTheme : "default-light";
      set({
        loadout: presetLoadout(presetId),
        preset: presetId,
        locked,
        secrets: new Set(secrets ?? []),
        ready: true,
      });
    }
    if (oldA11y) document.documentElement.setAttribute("data-a11y", "on");
  },

  applyPreset: (id, keep = []) => {
    const p = getPreset(id);
    if (!p || get().locked.has(id)) return;
    const next = presetLoadout(id);
    const cur = get().loadout;
    for (const slot of keep) next[slot] = cur[slot];
    set({ loadout: next, preset: id });
    persist(get(), true);
  },

  setSlot: (slot, id) => {
    const it = getItem(id);
    if (!it || it.slot !== slot) return;
    const loadout = { ...get().loadout, [slot]: id };
    set({ loadout, preset: null });
    persist(get(), slot === "palette");
  },

  setSettings: (patch) => {
    set({ settings: { ...get().settings, ...patch } });
    persist(get(), false);
  },

  saveLoadout: (name) => {
    const saved = [...get().saved.filter((s) => s.name !== name), { name, loadout: get().loadout }];
    set({ saved });
    persist(get(), false);
  },

  deleteLoadout: (name) => {
    set({ saved: get().saved.filter((s) => s.name !== name) });
    persist(get(), false);
  },

  useLoadout: (saved) => {
    set({ loadout: normalizeLoadout(saved.loadout), preset: null });
    persist(get(), true);
  },

  setTimedActive: (on) => set({ timedActive: on }),

  syncDayNight: (now = new Date()) => {
    const st = get();
    const dn = st.settings.dayNight;
    const night = dn.enabled ? st.saved.find((x) => x.name === dn.night) : undefined;
    const isNight = !!night && inNightWindow(now.getHours(), dn.from, dn.to);
    if (isNight && !st.dayStash) set({ dayStash: st.loadout, loadout: normalizeLoadout(night!.loadout) });
    else if (!isNight && st.dayStash) set({ loadout: st.dayStash, dayStash: null });
  },

  addSecret: (id) => {
    if (get().secrets.has(id)) return;
    const secrets = new Set(get().secrets).add(id);
    set({ secrets });
    ipc.set_config(SECRETS_KEY, [...secrets]).catch(() => {});
  },
}));

/** Presets the user can apply now (secret presets appear once found). */
export function visiblePresets(state: Pick<Store, "secrets">) {
  return PRESETS.filter((p) => !p.secret || state.secrets.has(p.secret));
}

/* ------------------------------------------------------------------ */
/* Helpers for modules (sound, effects, wallpaper …)                    */
/* ------------------------------------------------------------------ */

function prefersReducedMotion(): boolean {
  return typeof window !== "undefined" && !!window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
}

/** True when decorative animation must not run. */
export function motionReduced(s: AppearanceSettings = useAppearance.getState().settings): boolean {
  if (s.reducedMotion === "on") return true;
  if (s.reducedMotion === "off") return false;
  return prefersReducedMotion();
}

export function focusActive(): boolean {
  const st = useAppearance.getState();
  return st.settings.focus || (st.settings.focusInTimed && st.timedActive);
}

/**
 * How much decoration to show: 0 none, 1 subtle, 2 full. Celebrations,
 * the room and results animations, and wallpaper strength scale with this.
 */
export function effectsLevel(): 0 | 1 | 2 {
  const st = useAppearance.getState();
  if (focusActive() || st.settings.whimsy === "off") return 0;
  if (motionReduced(st.settings)) return 0;
  return st.settings.whimsy === "full" ? 2 : 1;
}

export type SoundChannel = "ui" | "feedback" | "celebration";

/** Effective gain 0–1 for a sound channel (0 when muted or in focus for decoration). */
export function channelGain(ch: SoundChannel): number {
  const s = useAppearance.getState().settings;
  if (s.muted) return 0;
  return Math.max(0, Math.min(1, s.volumes.master * s.volumes[ch]));
}
