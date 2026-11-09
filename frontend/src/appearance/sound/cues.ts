/**
 * Pure sound logic: the cue catalogue (Makeover.md §5.7), which cues an app
 * event plays and on which mixer channel, combo pitch, per-cue rate limits,
 * the preview demo and the recipe/file lookups with their fallbacks. No Web
 * Audio here, so all of it is unit-tested.
 */

import type { AppEvent } from "../events";
import type { SoundChannel } from "../store";

export const CUES = [
  "click",
  "toggle",
  "nav",
  "correct",
  "partial",
  "wrong",
  "combo",
  "hint",
  "reveal",
  "bookmark",
  "note",
  "session_start",
  "session_end",
  "tick",
  "time_up",
  "generate_done",
  "generate_error",
  "review_due",
  "unlock",
  "egg",
  "theme_switch",
] as const;

export type Cue = (typeof CUES)[number];

export interface CueRequest {
  cue: Cue;
  channel: SoundChannel;
  /** Pitch shift in semitones (combo steps, toggle off). */
  semitones?: number;
  /** Gain multiplier on top of the channel level. */
  gain?: number;
  /** Seconds after the event. */
  delay?: number;
}

/** The pack every other pack falls back to for cues it leaves out. */
export const DEFAULT_PACK = "sfx.soft";

export const COMBO_MAX_SEMITONES = 8;

/** Combo 2 plays one semitone up, combo 3 two, … capped. */
export function comboSemitones(combo: number): number {
  return Math.max(0, Math.min(COMBO_MAX_SEMITONES, Math.floor(combo) - 1));
}

const one = (cue: Cue, channel: SoundChannel, extra: Partial<CueRequest> = {}): CueRequest[] => [
  { cue, channel, ...extra },
];

/**
 * The cues an app event plays. UI basics and practice actions go on "ui",
 * answers and quiz/status signals on "feedback", rewards on "celebration".
 */
export function cuesFor(e: AppEvent): CueRequest[] {
  switch (e.type) {
    case "click":
      return one("click", "ui");
    case "toggle":
      return one("toggle", "ui", e.on ? {} : { semitones: -3 });
    case "nav":
      return one("nav", "ui", { gain: 0.4 });
    case "answer": {
      const out = one(e.outcome, "feedback");
      if (e.outcome === "correct" && e.combo >= 2) {
        out.push({ cue: "combo", channel: "feedback", semitones: comboSemitones(e.combo), delay: 0.16 });
      }
      return out;
    }
    case "hint":
      return one("hint", "ui");
    case "reveal":
      return one("reveal", "ui");
    case "bookmark":
      return one("bookmark", "ui", e.on ? {} : { semitones: -3 });
    case "note_saved":
      return one("note", "ui");
    case "session_start":
      return one("session_start", "feedback");
    case "session_end":
      return one("session_end", "celebration");
    case "timer_tick":
      if (e.remainingS <= 0 || e.remainingS > 10) return [];
      return one("tick", "feedback", e.remainingS <= 3 ? { semitones: 2 } : { gain: 0.8 });
    case "time_up":
      return one("time_up", "feedback");
    case "generate_done":
      return one("generate_done", "feedback");
    case "generate_error":
      return one("generate_error", "feedback");
    case "review_due":
      return e.count > 0 ? one("review_due", "feedback") : [];
    case "unlock":
      return one("unlock", "celebration");
    case "egg":
      return one("egg", "celebration");
    case "theme_switch":
      return one("theme_switch", "ui");
    default:
      return [];
  }
}

/** Most plays per second for cues that can fire in bursts. */
export const THROTTLE: Partial<Record<Cue, number>> = { click: 12, toggle: 12, nav: 6, tick: 4 };

/** True at most `perSecond` times per second (minimum gap between passes). */
export function rateLimiter(perSecond: number): (nowMs: number) => boolean {
  const gap = 1000 / perSecond;
  let last = -Infinity;
  return (now) => {
    if (now - last < gap) return false;
    last = now;
    return true;
  };
}

/** Per-cue throttle: `gate(cue, nowMs)` says whether this play may go ahead. */
export function cueGate(limits: Partial<Record<Cue, number>> = THROTTLE): (cue: Cue, nowMs: number) => boolean {
  const limiters = new Map<Cue, (now: number) => boolean>();
  for (const [cue, n] of Object.entries(limits) as [Cue, number][]) limiters.set(cue, rateLimiter(n));
  return (cue, now) => limiters.get(cue)?.(now) ?? true;
}

/** What previewSfx plays: a short tour of the pack. */
export const PREVIEW_CUES: CueRequest[] = [
  { cue: "click", channel: "ui" },
  { cue: "correct", channel: "feedback", delay: 0.3 },
  { cue: "partial", channel: "feedback", delay: 1.0 },
  { cue: "wrong", channel: "feedback", delay: 1.7 },
  { cue: "session_end", channel: "celebration", delay: 2.4 },
];

/** Seconds a previewSfx demo lasts (active-pack UI sounds stay quiet meanwhile). */
export const PREVIEW_SECONDS = 4;

export type PackTable<T> = Record<string, Partial<Record<Cue, T>>>;

/** A pack's recipe for a cue, or the default pack's when the pack leaves it out. */
export function lookupCue<T>(packs: PackTable<T>, packId: string, cue: Cue): T | undefined {
  return packs[packId]?.[cue] ?? packs[DEFAULT_PACK]?.[cue];
}

/** File names a pack may use instead of the cue name (Makeover.md §5.7 table). */
const FILE_ALIASES: Partial<Record<Cue, string[]>> = { note: ["note_saved"], egg: ["egg_found"] };

/** The audio file a pack item provides for a cue (`data.files`), if any. */
export function fileFor(files: unknown, cue: Cue): string | undefined {
  if (!files || typeof files !== "object") return undefined;
  const rec = files as Record<string, unknown>;
  for (const key of [cue, ...(FILE_ALIASES[cue] ?? [])]) {
    const v = rec[key];
    if (typeof v === "string" && v) return v;
  }
  return undefined;
}

/**
 * Which procedural recipe set an item plays: its own id, or `data.base` for a
 * drop-in pack that wants a built-in pack behind its files.
 */
export function recipePack(item: { id: string; data?: Record<string, unknown> } | undefined): string {
  const base = item?.data?.base;
  if (typeof base === "string" && base) return base;
  return item?.id ?? DEFAULT_PACK;
}
