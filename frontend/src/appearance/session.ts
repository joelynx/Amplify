/**
 * Turns quiz activity into app events: tracks the combo of consecutive
 * unaided correct answers and the counts for the session-end screen. Purely
 * presentational; the practice record is kept by the backend.
 */

import { emit, type AnswerOutcome, type SessionSummary } from "./events";

interface Session {
  mode: string;
  startedAt: number;
  combo: number;
  answered: number;
  unaided: number;
  assisted: number;
  partial: number;
  missed: number;
  toReview: number;
}

let current: Session | null = null;

export function startSession(mode: string, now = Date.now()): void {
  current = { mode, startedAt: now, combo: 0, answered: 0, unaided: 0, assisted: 0, partial: 0, missed: 0, toReview: 0 };
  emit({ type: "session_start", mode });
}

export function outcomeOf(credit: number): AnswerOutcome {
  if (credit >= 0.999) return "correct";
  return credit > 0 ? "partial" : "wrong";
}

/** Record a graded answer. `credit` is 0–1. Returns the event that was emitted. */
export function recordAnswer(opts: {
  credit: number;
  assisted: boolean;
  selfAssessed: boolean;
}): { outcome: AnswerOutcome; combo: number } {
  const outcome = outcomeOf(opts.credit);
  const unaided = !opts.assisted;
  const s = current;
  let combo = 0;
  if (s) {
    s.combo = outcome === "correct" && unaided ? s.combo + 1 : 0;
    combo = s.combo;
    s.answered += 1;
    if (outcome === "correct" && unaided) s.unaided += 1;
    if (opts.assisted) s.assisted += 1;
    if (outcome === "partial") s.partial += 1;
    if (outcome === "wrong") s.missed += 1;
    // Mirrors the review scheduler: anything but an unaided full solve comes back.
    if (!(outcome === "correct" && unaided)) s.toReview += 1;
  } else if (outcome === "correct" && unaided) {
    combo = 1;
  }
  emit({ type: "answer", outcome, unaided, combo, selfAssessed: opts.selfAssessed });
  return { outcome, combo };
}

/** End the session. Returns its summary (null when no session or nothing answered). */
export function endSession(now = Date.now()): SessionSummary | null {
  const s = current;
  current = null;
  if (!s || s.answered === 0) return null;
  const summary: SessionSummary = {
    mode: s.mode,
    answered: s.answered,
    unaided: s.unaided,
    assisted: s.assisted,
    missed: s.missed,
    partial: s.partial,
    toReview: s.toReview,
    elapsedMs: now - s.startedAt,
  };
  emit({ type: "session_end", summary });
  return summary;
}

export function sessionActive(): boolean {
  return current !== null;
}
