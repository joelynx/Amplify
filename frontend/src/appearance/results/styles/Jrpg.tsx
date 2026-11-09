/**
 * results.jrpg: a "QUIZ CLEAR!" victory window. The tally counts up line by
 * line like an EXP screen, an unaided gauge fills, and the review queue is
 * the item you obtained. The numbers are the session's own; nothing extra
 * is invented.
 */

import type { CSSProperties } from "react";

import {
  HEADING, type StyleProps, clock, countAt, progressAt, stats, unaidedShare, useAnimClock, useBlink,
} from "../shared";

const ROW_GAP = 260;
const ROW_DUR = 480;

const WINDOW: CSSProperties = {
  background:
    "linear-gradient(180deg, color-mix(in srgb, var(--primary) 26%, var(--surface)), color-mix(in srgb, var(--primary) 9%, var(--surface)))",
  border: "3px solid var(--text)",
  borderRadius: 10,
  boxShadow:
    "inset 0 0 0 2px var(--surface), inset 0 0 0 3px color-mix(in srgb, var(--text) 40%, transparent), 0 6px 0 rgba(0, 0, 0, 0.22)",
  color: "var(--text)",
};

function title(mode: string): string {
  const m = mode.trim().toUpperCase();
  return /^[A-Z]{2,10}$/.test(m) ? `${m} CLEAR!` : "QUIZ CLEAR!";
}

export function Jrpg({ s, level, onClose }: StyleProps) {
  const rows = stats(s).filter((r) => r.key !== "toReview");
  const timeAt = 300 + rows.length * ROW_GAP;
  const itemAt = timeAt + ROW_GAP;
  const doneAt = itemAt + ROW_DUR;
  const t = useAnimClock(level > 0, doneAt + 100);
  const done = t === Infinity || t >= doneAt;
  const caret = useBlink<HTMLSpanElement>(level > 0 && done);
  const gauge = unaidedShare(s) * progressAt(t, 300 + ROW_GAP, ROW_DUR * 2);

  return (
    <div className="p-5 sm:p-6" style={WINDOW}>
      <h2
        className="text-center text-2xl font-bold uppercase tracking-[0.12em] sm:text-3xl"
        style={{ ...HEADING, textShadow: "2px 2px 0 color-mix(in srgb, var(--primary) 45%, transparent)" }}
      >
        {title(s.mode)}
      </h2>

      <dl className="mx-auto mt-5 max-w-sm space-y-1.5 text-base">
        {rows.map((r, i) => (
          <div key={r.key} className="flex items-baseline gap-2" style={{ opacity: progressAt(t, 300 + i * ROW_GAP - 120, 120) }}>
            <dt>{r.label}</dt>
            <span aria-hidden className="flex-1 translate-y-[-3px] border-b-2 border-dotted" style={{ borderColor: "color-mix(in srgb, var(--text) 35%, transparent)" }} />
            <dd className="min-w-[3ch] text-right font-bold tabular-nums">{countAt(t, r.value, 300 + i * ROW_GAP, ROW_DUR)}</dd>
          </div>
        ))}
        <div className="flex items-baseline gap-2" style={{ opacity: progressAt(t, timeAt - 120, 120) }}>
          <dt>Time</dt>
          <span aria-hidden className="flex-1 translate-y-[-3px] border-b-2 border-dotted" style={{ borderColor: "color-mix(in srgb, var(--text) 35%, transparent)" }} />
          <dd className="text-right font-bold tabular-nums">{clock(countAt(t, s.elapsedMs, timeAt, ROW_DUR))}</dd>
        </div>
      </dl>

      <div className="mx-auto mt-4 max-w-sm">
        <div className="flex justify-between text-xs font-semibold uppercase tracking-wider">
          <span>Unaided</span>
          <span className="tabular-nums">{s.unaided}/{s.answered}</span>
        </div>
        <div className="mt-1 h-3 overflow-hidden rounded-sm border-2" style={{ borderColor: "var(--text)", background: "var(--background)" }}>
          <div className="h-full" style={{ width: `${gauge * 100}%`, background: "var(--success)" }} />
        </div>
      </div>

      <div
        className="mx-auto mt-4 max-w-sm rounded-md border-2 px-3 py-2 text-sm"
        style={{ borderColor: "color-mix(in srgb, var(--text) 50%, transparent)", opacity: progressAt(t, itemAt - 120, 200) }}
      >
        <span className="font-bold">Obtained:</span>{" "}
        <span className="tabular-nums">{countAt(t, s.toReview, itemAt, ROW_DUR)}</span>{" "}
        {s.toReview === 1 ? "question" : "questions"} for the review queue
      </div>

      <div className="mt-5 flex items-center justify-end gap-2">
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="rounded-md border-2 px-4 py-1.5 text-sm font-bold uppercase tracking-wider focus:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            style={{ borderColor: "var(--text)", background: "var(--surface)", color: "var(--text)" }}
          >
            <span ref={caret} aria-hidden className="mr-1.5">▶</span>
            Continue
          </button>
        )}
      </div>
    </div>
  );
}
