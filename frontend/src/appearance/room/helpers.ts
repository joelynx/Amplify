/**
 * Pure helpers for the study room: time of day and season from a Date, plant
 * growth from a review count, book layout on shelves, greeting and countdown
 * text, and turning IPC payloads into the scene's data. No React, no DOM.
 */

import type { LearningStats, Milestone, ReviewSummary } from "../../lib/ipc";

/* ------------------------------------------------------------------ */
/* Time and season                                                      */
/* ------------------------------------------------------------------ */

export type TimeOfDay = "dawn" | "day" | "dusk" | "night";
export type Season = "spring" | "summer" | "autumn" | "winter";

/** dawn 5–8, day 8–17, dusk 17–20, night otherwise (local time). */
export function timeOfDay(d: Date): TimeOfDay {
  const h = d.getHours();
  if (h >= 5 && h < 8) return "dawn";
  if (h >= 8 && h < 17) return "day";
  if (h >= 17 && h < 20) return "dusk";
  return "night";
}

/** Meteorological seasons, northern hemisphere. */
export function season(d: Date): Season {
  const m = d.getMonth();
  if (m >= 2 && m <= 4) return "spring";
  if (m >= 5 && m <= 7) return "summer";
  if (m >= 8 && m <= 10) return "autumn";
  return "winter";
}

export type DayPart = "morning" | "afternoon" | "evening" | "night";

export function dayPart(d: Date): DayPart {
  const h = d.getHours();
  if (h >= 5 && h < 12) return "morning";
  if (h >= 12 && h < 17) return "afternoon";
  if (h >= 17 && h < 22) return "evening";
  return "night";
}

/** "Good evening, Joel", or "Good evening" without a name. */
export function greeting(d: Date, name: string): string {
  const base = `Good ${dayPart(d)}`;
  const n = name.trim();
  return n ? `${base}, ${n}` : base;
}

function startOfDay(d: Date): number {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
}

/** Parse "YYYY-MM-DD" (or an ISO string) as a local calendar date. */
export function parseLocalDate(s: string): Date | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(s.trim());
  if (!m) return null;
  const d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  return Number.isNaN(d.getTime()) ? null : d;
}

/** Whole calendar days from `now` to `date` (negative when past). */
export function daysUntil(date: string, now: Date): number | null {
  const d = parseLocalDate(date);
  if (!d) return null;
  return Math.round((startOfDay(d) - startOfDay(now)) / 86_400_000);
}

/** "12 days to Finals", "1 day to Finals", "Finals is today"; null when unset or past. */
export function examCountdown(exam: { label: string; date: string | null }, now: Date): string | null {
  if (!exam.date) return null;
  const n = daysUntil(exam.date, now);
  if (n === null || n < 0) return null;
  const label = exam.label.trim() || "the exam";
  if (n === 0) return `${label.charAt(0).toUpperCase()}${label.slice(1)} is today`;
  return `${n} day${n === 1 ? "" : "s"} to ${label}`;
}

/** "today", "tomorrow", "in 3 days", "2 days ago" for an ISO timestamp. */
export function relativeDay(iso: string | null | undefined, now: Date): string | null {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return null;
  const days = Math.round((startOfDay(d) - startOfDay(now)) / 86_400_000);
  if (days === 0) return "today";
  if (days === 1) return "tomorrow";
  if (days === -1) return "yesterday";
  return days > 0 ? `in ${days} days` : `${-days} days ago`;
}

/** 24-hour "HH:MM". */
export function clockText(d: Date): string {
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

/** Clock hand angles in degrees (0 = 12 o'clock, clockwise). */
export function clockHands(d: Date): { hour: number; minute: number } {
  const m = d.getMinutes();
  return { hour: ((d.getHours() % 12) + m / 60) * 30, minute: m * 6 };
}

/** Split a short label into at most `lines` lines of about `per` characters. */
export function noteLines(text: string, per: number, lines = 2): string[] {
  const words = text
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .flatMap((w) => {
      if (w.length <= per || per < 3) return [w];
      const parts: string[] = [];
      let rest = w;
      while (rest.length > per) {
        parts.push(`${rest.slice(0, per - 1)}-`);
        rest = rest.slice(per - 1);
      }
      parts.push(rest);
      return parts;
    });
  const out: string[] = [];
  let cur = "";
  for (const w of words) {
    const next = cur ? `${cur} ${w}` : w;
    if (next.length <= per) cur = next;
    else {
      if (cur) out.push(cur);
      cur = w;
    }
  }
  if (cur) out.push(cur);
  const fitted = out.slice(0, lines).map((l) => (l.length > per ? `${l.slice(0, per - 1)}…` : l));
  if (out.length > lines && fitted.length) {
    const last = fitted[lines - 1];
    fitted[lines - 1] = last.length >= per ? `${last.slice(0, per - 1)}…` : `${last}…`;
  }
  return fitted;
}

/* ------------------------------------------------------------------ */
/* Plant                                                                */
/* ------------------------------------------------------------------ */

export const PLANT_STAGES = ["pot", "seedling", "sprout", "leafy", "flowering"] as const;
export type PlantStage = 0 | 1 | 2 | 3 | 4;
/** Spaced reviews needed for each stage. */
export const PLANT_THRESHOLDS = [0, 1, 3, 8, 20] as const;

/** Stage index for a count of spaced reviews. It only ever grows. */
export function plantStage(count: number): PlantStage {
  const n = Number.isFinite(count) ? count : 0;
  let s = 0;
  for (let i = 0; i < PLANT_THRESHOLDS.length; i++) if (n >= PLANT_THRESHOLDS[i]) s = i;
  return s as PlantStage;
}

/** Reviews still needed for the next stage; null once flowering. */
export function reviewsToNextStage(count: number): number | null {
  const s = plantStage(count);
  if (s === 4) return null;
  return PLANT_THRESHOLDS[s + 1] - Math.max(0, Math.floor(Number.isFinite(count) ? count : 0));
}

/* ------------------------------------------------------------------ */
/* Books                                                                */
/* ------------------------------------------------------------------ */

export interface TopicBook {
  topic: string;
  attempted: number;
  independent: number;
}

export interface Shelf {
  /** Left edge of the usable shelf. */
  x: number;
  /** Top surface of the shelf plank (books stand on it). */
  base: number;
  width: number;
  /** Clear height above the plank. */
  height: number;
}

export interface BookSpot {
  topic: string;
  /** Text for the spine, "" when the book is too thin. */
  label: string;
  x: number;
  y: number;
  w: number;
  h: number;
  shelf: number;
  /** Stable colour slot for the topic. */
  color: number;
  fontSize: number;
}

export interface BookLayout {
  books: BookSpot[];
  /** Topics that did not fit. */
  overflow: number;
}

export interface BookOptions {
  minWidth?: number;
  maxWidth?: number;
  gap?: number;
  colors?: number;
  /** Narrowest spine that gets a title. */
  labelFrom?: number;
}

/** FNV-1a: a stable small hash for per-topic variation. */
export function hashString(s: string): number {
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return h >>> 0;
}

/** Deterministic pseudo-random numbers in [0, 1) (mulberry32). */
export function seeded(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Spine thickness grows with the square root of independent solves. */
export function bookWidth(independent: number, opts: BookOptions = {}): number {
  const min = opts.minWidth ?? 9;
  const max = opts.maxWidth ?? 30;
  const n = Math.max(0, Number.isFinite(independent) ? independent : 0);
  return Math.round(Math.min(max, min + 3 * Math.sqrt(n)));
}

const STOP = new Set(["and", "of", "the", "in", "to", "for", "with", "a", "an", "on", "&"]);

/** Fit a title into `max` characters: whole, "Lin. Alg.", "LA", or cut with an ellipsis. */
export function abbreviate(title: string, max: number): string {
  const t = title.trim();
  if (max <= 0) return "";
  if (t.length <= max) return t;
  const words = t.split(/[\s\-–—:,/]+/).filter((w) => w && !STOP.has(w.toLowerCase()));
  if (words.length) {
    for (const k of [6, 5, 4, 3]) {
      const s = words.map((w) => (w.length <= k ? w : `${w.slice(0, k)}.`)).join(" ");
      if (s.length <= max) return s;
    }
    if (words.length > 1) {
      const initials = words.map((w) => w.charAt(0).toUpperCase()).join("");
      if (initials.length <= max) return initials;
    }
  }
  return max >= 2 ? `${t.slice(0, max - 1)}…` : "";
}

/**
 * Place one book per practised topic on the shelves, left to right, top shelf
 * first, alphabetically. When they cannot all fit, the most practised topics
 * win and the rest are counted in `overflow`.
 */
export function layoutBooks(topics: TopicBook[], shelves: Shelf[], opts: BookOptions = {}): BookLayout {
  const gap = opts.gap ?? 1;
  const colors = Math.max(1, opts.colors ?? 8);
  const labelFrom = opts.labelFrom ?? 14;
  const list = topics
    .filter((t) => t.attempted > 0 && t.topic.trim())
    .map((t) => ({ ...t, w: bookWidth(t.independent, opts) }));
  if (!shelves.length) return { books: [], overflow: list.length };

  const capacity = shelves.reduce((s, sh) => s + sh.width, 0);
  const reserve = 22; // room for the "+N" tag when something is left out
  const chosen = [...list].sort((a, b) => b.attempted - a.attempted || a.topic.localeCompare(b.topic));
  let used = chosen.reduce((s, b) => s + b.w + gap, 0);
  while (chosen.length && used > capacity - (chosen.length < list.length ? reserve : 0)) {
    const dropped = chosen.pop()!;
    used -= dropped.w + gap;
  }
  chosen.sort((a, b) => a.topic.localeCompare(b.topic));

  const books: BookSpot[] = [];
  let si = 0;
  let x = shelves[0].x;
  for (const b of chosen) {
    while (si < shelves.length && x + b.w > shelves[si].x + shelves[si].width) {
      si++;
      if (si < shelves.length) x = shelves[si].x;
    }
    if (si >= shelves.length) break;
    const sh = shelves[si];
    const hv = hashString(b.topic);
    const h = Math.round(sh.height * (0.66 + ((hv % 1000) / 1000) * 0.28));
    const fontSize = Math.max(6, Math.min(10, b.w - 5));
    const chars = Math.floor((h - 8) / (fontSize * 0.62));
    books.push({
      topic: b.topic,
      label: b.w >= labelFrom && chars >= 2 ? abbreviate(b.topic, chars) : "",
      x,
      y: sh.base - h,
      w: b.w,
      h,
      shelf: si,
      color: (hv >>> 10) % colors,
      fontSize,
    });
    x += b.w + gap;
  }
  return { books, overflow: list.length - books.length };
}

/* ------------------------------------------------------------------ */
/* Scene data                                                           */
/* ------------------------------------------------------------------ */

export interface SceneData {
  subject: string | null;
  topics: TopicBook[];
  /** Earned milestones. */
  trophies: { id: string; title: string }[];
  /** Spaced reviews so far (drives the plant). */
  plantCount: number;
  /** Reviews due now; null when unknown (bridge unavailable). */
  due: number | null;
  nextDue: string | null;
  /** Short labels for the sticky notes (topics of due reviews). */
  notes: string[];
}

export const EMPTY_SCENE: SceneData = {
  subject: null,
  topics: [],
  trophies: [],
  plantCount: 0,
  due: null,
  nextDue: null,
  notes: [],
};

/** Build the scene's data from whatever the bridge returned (any part may be null). */
export function toSceneData(
  subject: string | null,
  stats: LearningStats | null,
  reviews: ReviewSummary | null,
  milestones: Milestone[] | null,
): SceneData {
  const topics = (stats?.topics ?? [])
    .filter((t) => t.attempted > 0)
    .map((t) => ({ topic: t.topic, attempted: t.attempted, independent: t.independent }));
  const spaced = milestones?.find((m) => m.id === "spaced_reviews")?.progress ?? 0;
  const notes: string[] = [];
  for (const r of reviews?.lists?.due ?? []) {
    const label = (r.subtopic || r.topic || r.branch || "").trim();
    if (label && !notes.includes(label)) notes.push(label);
    if (notes.length >= 3) break;
  }
  return {
    subject,
    topics,
    trophies: (milestones ?? []).filter((m) => m.unlocked).map((m) => ({ id: m.id, title: m.title })),
    plantCount: Math.max(spaced, stats?.delayed?.n ?? 0),
    due: reviews ? (reviews.counts?.due ?? 0) : null,
    nextDue: reviews?.next_due ?? null,
    notes,
  };
}

/** Bars for the wall chart: the five most practised topics, with the independent share. */
export function chartBars(topics: TopicBook[], n = 5): { value: number; share: number }[] {
  const top = [...topics].sort((a, b) => b.attempted - a.attempted).slice(0, n);
  const max = Math.max(1, ...top.map((t) => t.attempted));
  return top.map((t) => ({ value: t.attempted / max, share: t.attempted ? t.independent / t.attempted : 0 }));
}
