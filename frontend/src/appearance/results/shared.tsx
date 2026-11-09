/**
 * Pieces shared by the results styles: sample numbers for previews, number
 * and time formatting, the honest stat list every style shows, a single
 * animation clock for count-ups, and small WAAPI helpers (enter, blink).
 */

import { type CSSProperties, type ReactNode, useEffect, useRef, useState } from "react";

import type { SessionSummary } from "../events";
import { resolve } from "../registry";
import { useAppearance } from "../store";

export const SAMPLE: SessionSummary = {
  mode: "quiz",
  answered: 10,
  unaided: 7,
  assisted: 1,
  partial: 1,
  missed: 1,
  toReview: 3,
  elapsedMs: 12 * 60_000 + 34_000,
};

export interface StyleProps {
  s: SessionSummary;
  /** Decoration allowed: 0 none, 1 subtle, 2 full. 0 means no animation at all. */
  level: 0 | 1 | 2;
  onClose?: () => void;
}

/* ------------------------------------------------------------------ formatting */

const pad = (n: number) => String(n).padStart(2, "0");

function parts(ms: number): [number, number, number] {
  const total = Math.max(0, Math.round(ms / 1000));
  return [Math.floor(total / 3600), Math.floor((total % 3600) / 60), total % 60];
}

/** 12:34, or 1:02:03 past an hour. */
export function clock(ms: number): string {
  const [h, m, s] = parts(ms);
  return h ? `${h}:${pad(m)}:${pad(s)}` : `${m}:${pad(s)}`;
}

/** 00:12:34 */
export function hms(ms: number): string {
  const [h, m, s] = parts(ms);
  return `${pad(h)}:${pad(m)}:${pad(s)}`;
}

/** 12 minutes 34 seconds / 1 hour 2 minutes / 45 seconds */
export function longTime(ms: number): string {
  const [h, m, s] = parts(ms);
  const unit = (n: number, w: string) => `${n} ${w}${n === 1 ? "" : "s"}`;
  if (h) return m ? `${unit(h, "hour")} ${unit(m, "minute")}` : unit(h, "hour");
  if (m) return s ? `${unit(m, "minute")} ${unit(s, "second")}` : unit(m, "minute");
  return unit(s, "second");
}

const SMALL = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"];

/** Newspaper style: words below ten, digits from ten. */
export function words(n: number): string {
  return Number.isInteger(n) && n >= 0 && n < 10 ? SMALL[n] : String(n);
}

export function plural(n: number, one: string, many = `${one}s`): string {
  return n === 1 ? one : many;
}

export const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

/** "quiz" → "Quiz", "pbs" → "PBS", "review_session" → "Review session". */
export function modeLabel(mode: string): string {
  const m = mode.trim().replace(/[_-]+/g, " ");
  if (!m) return "Session";
  return m.length <= 3 ? m.toUpperCase() : cap(m);
}

/* ------------------------------------------------------------------ the honest numbers */

export type StatKey = "answered" | "unaided" | "assisted" | "partial" | "missed" | "toReview";

export interface Stat {
  key: StatKey;
  label: string;
  value: number;
}

/** The numbers every style shows, in one order (elapsed time is separate). */
export function stats(s: SessionSummary): Stat[] {
  return [
    { key: "answered", label: "Answered", value: s.answered },
    { key: "unaided", label: "Solved unaided", value: s.unaided },
    { key: "assisted", label: "With help", value: s.assisted },
    { key: "partial", label: "Partial", value: s.partial },
    { key: "missed", label: "Missed", value: s.missed },
    { key: "toReview", label: "To review", value: s.toReview },
  ];
}

/** Share solved unaided, 0–1. */
export function unaidedShare(s: SessionSummary): number {
  return s.answered > 0 ? Math.min(1, s.unaided / s.answered) : 0;
}

/* ------------------------------------------------------------------ animation */

/**
 * Milliseconds since mount while animating, Infinity when done or when
 * animation is off. One requestAnimationFrame loop per screen, stopped at
 * `totalMs`.
 */
export function useAnimClock(animate: boolean, totalMs: number): number {
  const [t, setT] = useState(0);
  useEffect(() => {
    if (!animate) return;
    let raf = 0;
    let start: number | null = null;
    const tick = (now: number) => {
      start ??= now;
      const e = now - start;
      setT(e >= totalMs ? Infinity : e);
      if (e < totalMs) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [animate, totalMs]);
  return animate ? t : Infinity;
}

/** Progress 0–1 of a segment that starts at `delay` and lasts `dur`. */
export function progressAt(t: number, delay: number, dur: number): number {
  if (t === Infinity) return 1;
  return Math.min(1, Math.max(0, (t - delay) / dur));
}

/** A number counting up (ease-out) between delay and delay + dur. */
export function countAt(t: number, target: number, delay = 0, dur = 700): number {
  const p = progressAt(t, delay, dur);
  return Math.round(target * (1 - (1 - p) ** 3));
}

/** Fades/moves its content in once on mount (Web Animations API). */
export function Enter({
  animate,
  delay = 0,
  duration = 380,
  from = "translateY(6px)",
  to = "none",
  easing = "cubic-bezier(.2,.8,.2,1)",
  className,
  style,
  children,
}: {
  animate: boolean;
  delay?: number;
  duration?: number;
  from?: string;
  to?: string;
  easing?: string;
  className?: string;
  style?: CSSProperties;
  children?: ReactNode;
}) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!animate || !el || typeof el.animate !== "function") return;
    const a = el.animate(
      [
        { opacity: 0, transform: from },
        { opacity: 1, transform: to },
      ],
      { duration, delay, easing, fill: "backwards" },
    );
    return () => a.cancel();
    // Runs once on mount; later prop changes do not replay it.
  }, []);
  return (
    <div ref={ref} className={className} style={to === "none" ? style : { ...style, transform: to }}>
      {children}
    </div>
  );
}

/** A ref whose element blinks once a second (well under 3 flashes/s) while enabled. */
export function useBlink<T extends HTMLElement>(enabled: boolean) {
  const ref = useRef<T>(null);
  useEffect(() => {
    const el = ref.current;
    if (!enabled || !el || typeof el.animate !== "function") return;
    const a = el.animate([{ opacity: 1 }, { opacity: 0.12 }], {
      duration: 1100,
      iterations: Infinity,
      easing: "steps(2, jump-none)",
    });
    return () => a.cancel();
  }, [enabled]);
  return ref;
}

/* ------------------------------------------------------------------ palette helpers */

export function usePaletteDark(): boolean {
  return useAppearance((st) => Boolean(resolve(st.loadout, "palette")?.data?.dark));
}

export function useGreetingName(): string {
  return useAppearance((st) => st.settings.greetingName.trim());
}

/**
 * Colours for a "screen" (arcade, terminal): the palette's own dark
 * background on dark palettes, inverted text/background on light ones. Both
 * pairs are AA by construction.
 */
export function screenColors(dark: boolean): { bg: string; fg: string } {
  return dark ? { bg: "var(--background)", fg: "var(--text)" } : { bg: "var(--text)", fg: "var(--background)" };
}

export const HEADING: CSSProperties = { fontFamily: "var(--font-heading, var(--font-family))" };
export const MONO: CSSProperties = { fontFamily: "var(--font-mono, ui-monospace, monospace)" };

/** Shared primary button (chrome skins it through data-ui). */
export function DoneButton({ onClose, label = "Done", className }: { onClose?: () => void; label?: string; className?: string }) {
  if (!onClose) return null;
  return (
    <button
      type="button"
      data-ui="button"
      onClick={onClose}
      className={
        "inline-flex h-10 items-center justify-center rounded-md bg-primary px-5 text-sm font-medium text-on-primary " +
        "transition-opacity hover:opacity-90 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 " +
        (className ?? "")
      }
    >
      {label}
    </button>
  );
}
