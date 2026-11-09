/**
 * App event bus. Pages emit what happened; sounds, the session summary and
 * easter eggs listen. Nothing here affects grading or the
 * practice record: listeners only react.
 */

export type AnswerOutcome = "correct" | "partial" | "wrong";

export interface SessionSummary {
  mode: string;
  answered: number;
  unaided: number;
  assisted: number;
  missed: number;
  partial: number;
  /** Questions that go into (or stay in) the review queue. */
  toReview: number;
  elapsedMs: number;
}

export type AppEvent =
  | { type: "click" }
  | { type: "toggle"; on: boolean }
  | { type: "nav"; path: string }
  | {
      type: "answer";
      outcome: AnswerOutcome;
      /** No hint and no reveal before answering. */
      unaided: boolean;
      /** Consecutive unaided correct answers in this session, including this one. */
      combo: number;
      selfAssessed: boolean;
    }
  | { type: "hint" }
  | { type: "reveal" }
  | { type: "bookmark"; on: boolean }
  | { type: "note_saved"; text: string; limit: number }
  | { type: "session_start"; mode: string }
  | { type: "session_end"; summary: SessionSummary }
  | { type: "timer_tick"; remainingS: number }
  | { type: "time_up" }
  | { type: "generate_done" }
  | { type: "generate_error" }
  | { type: "review_due"; count: number }
  | { type: "unlock"; what: string }
  | { type: "egg"; id: string }
  | { type: "search"; query: string }
  | { type: "logo_click" }
  | { type: "idle"; idle: boolean }
  | { type: "theme_switch" };

export type AppEventType = AppEvent["type"];
type Handler<T extends AppEventType> = (e: Extract<AppEvent, { type: T }>) => void;

const handlers = new Map<string, Set<(e: AppEvent) => void>>();

export function emit(e: AppEvent): void {
  for (const key of [e.type, "*"]) {
    handlers.get(key)?.forEach((h) => {
      try {
        h(e);
      } catch (err) {
        console.error("appearance event handler failed", e.type, err);
      }
    });
  }
}

/** Subscribe to one event type ("*" for all). Returns the unsubscribe function. */
export function on<T extends AppEventType>(type: T, handler: Handler<T>): () => void;
export function on(type: "*", handler: (e: AppEvent) => void): () => void;
export function on(type: string, handler: (e: never) => void): () => void {
  const set = handlers.get(type) ?? new Set();
  const h = handler as unknown as (e: AppEvent) => void;
  set.add(h);
  handlers.set(type, set);
  return () => set.delete(h);
}
