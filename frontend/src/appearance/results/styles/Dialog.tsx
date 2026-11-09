/**
 * results.dialog: an early-2000s setup-wizard window (original look): a
 * glossy title bar, a side banner, a segmented progress bar for the share
 * solved unaided, a Details group box and Back / Finish / Cancel buttons.
 */

import type { CSSProperties } from "react";

import { type StyleProps, clock, progressAt, stats, unaidedShare, useAnimClock } from "../shared";

const BLOCKS = 20;

const BEVEL: CSSProperties = {
  border: "1px solid color-mix(in srgb, var(--text) 45%, transparent)",
  borderRadius: 3,
  background: "linear-gradient(180deg, var(--surface), color-mix(in srgb, var(--surface) 80%, var(--border)))",
  color: "var(--text)",
  boxShadow: "inset 1px 1px 0 rgba(255, 255, 255, 0.55)",
  minWidth: "5.5rem",
};

function CheckBadge() {
  return (
    <svg viewBox="0 0 48 48" className="h-14 w-14" aria-hidden>
      <circle cx="24" cy="24" r="21" fill="rgba(255,255,255,0.18)" stroke="#fff" strokeWidth="2.5" />
      <path d="M14 25 l7 7 l13 -15" fill="none" stroke="#fff" strokeWidth="4.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function Dialog({ s, level, onClose }: StyleProps) {
  const t = useAnimClock(level > 0, 1600);
  const share = unaidedShare(s);
  const filled = Math.round(BLOCKS * share * progressAt(t, 200, 1200));
  const pct = Math.round(share * 100);

  return (
    <div
      className="overflow-hidden text-sm"
      style={{
        border: "1px solid color-mix(in srgb, var(--primary) 70%, #000)",
        borderRadius: "8px 8px 3px 3px",
        boxShadow: "0 10px 28px rgba(0, 0, 0, 0.28)",
        background: "var(--surface)",
        color: "var(--text)",
      }}
    >
      <div
        className="flex items-center justify-between px-2.5 py-1.5 font-bold text-white"
        style={{
          background:
            "linear-gradient(180deg, color-mix(in srgb, var(--primary) 70%, #fff) 0%, var(--primary) 18%, color-mix(in srgb, var(--primary) 85%, #000) 100%)",
          textShadow: "1px 1px 0 rgba(0, 0, 0, 0.35)",
        }}
      >
        <span className="flex items-center gap-2">
          <span aria-hidden className="grid h-4 w-4 place-items-center rounded-sm bg-white/25 text-[0.65rem] leading-none">Σ</span>
          Session Complete
        </span>
        {onClose && (
          <button
            type="button"
            aria-label="Close"
            onClick={onClose}
            className="grid h-5 w-5 place-items-center rounded-[3px] border border-white/70 text-xs leading-none focus:outline-none focus-visible:ring-2 focus-visible:ring-white"
            style={{ background: "linear-gradient(180deg, #e8735f, #c2391f)" }}
          >
            ✕
          </button>
        )}
      </div>

      <div className="flex">
        <div
          className="hidden w-28 shrink-0 flex-col items-center justify-start gap-2 p-4 text-white sm:flex"
          style={{ background: "linear-gradient(180deg, color-mix(in srgb, var(--primary) 85%, #000), color-mix(in srgb, var(--secondary) 70%, #000))" }}
        >
          <CheckBadge />
        </div>

        <div className="flex-1 p-4">
          <h2 className="text-lg font-bold" style={{ fontFamily: "var(--font-heading, var(--font-family))" }}>
            Completing your study session
          </h2>
          <p className="mt-1">Your answers have been checked. Here is the summary.</p>

          <p className="mt-3">
            Solved unaided: <span className="tabular-nums">{s.unaided}</span> of <span className="tabular-nums">{s.answered}</span> ({pct}%)
          </p>
          <div
            className="mt-1 flex h-5 gap-[2px] p-[2px]"
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={pct}
            aria-label="Share solved unaided"
            style={{ border: "1px solid color-mix(in srgb, var(--text) 40%, transparent)", borderRadius: 3, background: "var(--background)" }}
          >
            {Array.from({ length: BLOCKS }, (_, i) => (
              <span
                key={i}
                className="flex-1"
                style={{
                  borderRadius: 1,
                  background: i < filled ? "linear-gradient(180deg, color-mix(in srgb, var(--success) 60%, #fff), var(--success))" : "transparent",
                }}
              />
            ))}
          </div>

          <fieldset className="mt-4 rounded-[3px] border px-3 pb-2 pt-1" style={{ borderColor: "color-mix(in srgb, var(--text) 30%, transparent)" }}>
            <legend className="px-1">Details</legend>
            <dl className="grid grid-cols-[1fr_auto] gap-x-6 gap-y-0.5">
              {stats(s).map((st) => (
                <div key={st.key} className="contents">
                  <dt>{st.label}:</dt>
                  <dd className="text-right tabular-nums">{st.value}</dd>
                </div>
              ))}
              <div className="contents">
                <dt>Time elapsed:</dt>
                <dd className="text-right tabular-nums">{clock(s.elapsedMs)}</dd>
              </div>
            </dl>
          </fieldset>
        </div>
      </div>

      {onClose && (
        <div className="flex justify-end gap-2 border-t px-4 py-3" style={{ borderColor: "var(--border)", boxShadow: "inset 0 1px 0 rgba(255,255,255,0.5)" }}>
          <button type="button" disabled className="px-3 py-1 opacity-50" style={BEVEL}>
            &lt; Back
          </button>
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1 font-semibold focus:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            style={{ ...BEVEL, border: "2px solid color-mix(in srgb, var(--primary) 80%, #000)" }}
          >
            Finish
          </button>
          <button type="button" disabled className="px-3 py-1 opacity-50" style={BEVEL}>
            Cancel
          </button>
        </div>
      )}
    </div>
  );
}
