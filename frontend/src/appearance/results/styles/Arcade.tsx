/**
 * results.arcade: a cabinet scoreboard. Zero-padded scores roll up, rows
 * take the palette's colours, and the blinking attract line is a study line
 * instead of a coin prompt. Scores are this session's numbers only.
 */

import type { CSSProperties } from "react";

import {
  HEADING, MONO, type StyleProps, clock, countAt, screenColors, stats, useAnimClock, useBlink, useGreetingName,
  usePaletteDark,
} from "../shared";

const ROW_TINTS = ["var(--accent)", "var(--success)", "var(--primary)", "var(--warning)", "var(--secondary)", "var(--accent)"];

function initials(name: string): string {
  const letters = name
    .split(/\s+/)
    .map((w) => w.replace(/[^\p{L}\p{N}]/gu, "").charAt(0))
    .join("")
    .toUpperCase();
  return letters.slice(0, 3) || "YOU";
}

const pad6 = (n: number) => String(Math.max(0, n)).padStart(6, "0");

export function Arcade({ s, level, onClose }: StyleProps) {
  const dark = usePaletteDark();
  const { bg, fg } = screenColors(dark);
  const name = initials(useGreetingName());
  const t = useAnimClock(level > 0, 1500);
  const blink = useBlink<HTMLParagraphElement>(level > 0);

  const screen: CSSProperties = {
    ...MONO,
    background: bg,
    color: fg,
    border: "6px solid color-mix(in srgb, var(--primary) 70%, #000)",
    borderRadius: 18,
    boxShadow: "inset 0 0 0 2px color-mix(in srgb, var(--primary) 35%, transparent), 0 8px 24px rgba(0, 0, 0, 0.25)",
  };
  // Light palettes invert the screen, and their deep accents need a lighter touch to stay legible.
  const tint = (c: string) => `color-mix(in srgb, ${c} ${dark ? 38 : 22}%, ${fg})`;
  const glow = (c: string) => `0 0 6px color-mix(in srgb, ${c} 60%, transparent)`;

  return (
    <div className="px-4 py-5 uppercase sm:px-6" style={screen}>
      <div className="flex items-baseline justify-between text-xs tracking-widest">
        <span style={{ color: tint("var(--accent)") }}>1UP {name}</span>
        <span>Time {clock(s.elapsedMs)}</span>
      </div>

      <h2
        className="mt-3 text-center text-2xl font-bold tracking-[0.2em] sm:text-3xl"
        style={{ ...HEADING, color: tint("var(--accent)"), textShadow: glow("var(--accent)") }}
      >
        ★ Score ★
      </h2>
      <p className="mt-1 text-center text-3xl font-bold tabular-nums tracking-[0.15em]" style={{ textShadow: glow("var(--primary)") }}>
        {pad6(countAt(t, s.unaided, 0, 1200))}
      </p>
      <p className="text-center text-xs tracking-widest opacity-80">solved unaided</p>

      <table className="mx-auto mt-4 w-full max-w-xs text-sm">
        <thead>
          <tr className="text-xs tracking-widest opacity-80">
            <th className="pb-1 text-left font-normal">Stat</th>
            <th className="pb-1 text-right font-normal">Score</th>
          </tr>
        </thead>
        <tbody>
          {stats(s).map((st, i) => (
            <tr key={st.key} style={{ color: tint(ROW_TINTS[i]) }}>
              <td className="py-0.5 text-left">{st.label}</td>
              <td className="py-0.5 text-right tabular-nums">{pad6(countAt(t, st.value, 120 + i * 110, 800))}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <p ref={blink} className="mt-5 text-center text-sm font-bold tracking-widest" style={{ color: tint("var(--accent)") }}>
        Insert curiosity to continue
      </p>

      {onClose && (
        <div className="mt-4 flex justify-center">
          <button
            type="button"
            onClick={onClose}
            className="border-2 px-5 py-1.5 text-sm font-bold uppercase tracking-widest focus:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            style={{ borderColor: fg, color: fg, background: "transparent", fontFamily: "inherit" }}
          >
            Continue
          </button>
        </div>
      )}
    </div>
  );
}
