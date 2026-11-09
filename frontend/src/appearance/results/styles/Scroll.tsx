/**
 * results.scroll: a parchment scroll with rolled ends that unrolls once,
 * an illuminated first letter, a ledger of the numbers and a Q.E.D. seal.
 * The parchment is a warm tint of the palette's surface, so text keeps the
 * palette's own contrast on light and dark themes alike.
 */

import type { CSSProperties } from "react";

import { HEADING, type StyleProps, DoneButton, Enter, cap, clock, longTime, plural, stats, words } from "../shared";

const PARCHMENT = "color-mix(in srgb, var(--surface) 74%, #c9a66b)";

const ROLL: CSSProperties = {
  height: 18,
  borderRadius: 999,
  background: `linear-gradient(180deg, color-mix(in srgb, ${PARCHMENT} 70%, #000) 0%, color-mix(in srgb, ${PARCHMENT} 85%, #fff) 45%, color-mix(in srgb, ${PARCHMENT} 75%, #000) 100%)`,
  boxShadow: "0 2px 4px rgba(0, 0, 0, 0.25)",
  position: "relative",
  zIndex: 1,
};

function Fleuron() {
  return (
    <div aria-hidden className="my-3 flex items-center gap-3 text-muted">
      <span className="h-px flex-1" style={{ background: "currentColor", opacity: 0.4 }} />
      <span className="text-lg" style={{ color: "var(--accent)" }}>❦</span>
      <span className="h-px flex-1" style={{ background: "currentColor", opacity: 0.4 }} />
    </div>
  );
}

function account(s: StyleProps["s"]): string {
  return (
    `Be it recorded that in ${longTime(s.elapsedMs)} you answered ${words(s.answered)} ${plural(s.answered, "question")}: ` +
    `${words(s.unaided)} solved unaided, ${words(s.assisted)} with help, ${words(s.partial)} in part and ${words(s.missed)} missed. ` +
    (s.toReview > 0
      ? `${cap(words(s.toReview))} ${plural(s.toReview, "is", "are")} entered in the ledger for review.`
      : "None are entered in the ledger for review.")
  );
}

export function Scroll({ s, level, onClose }: StyleProps) {
  const animate = level > 0;
  return (
    <div className="mx-auto max-w-xl text-text">
      <div style={ROLL} />
      <Enter
        animate={animate}
        delay={80}
        duration={760}
        from="scaleY(0.04)"
        easing="cubic-bezier(.3,.7,.2,1)"
        className="relative -my-2 mx-3 px-6 pb-7 pt-8 sm:px-9"
        style={{
          transformOrigin: "top center",
          backgroundColor: PARCHMENT,
          backgroundImage:
            "radial-gradient(circle at 18% 22%, rgba(110, 70, 20, 0.10), transparent 38%), radial-gradient(circle at 85% 75%, rgba(110, 70, 20, 0.12), transparent 42%), radial-gradient(circle at 60% 10%, rgba(255, 255, 255, 0.10), transparent 30%)",
          boxShadow: "inset 0 0 28px rgba(80, 50, 10, 0.25)",
        }}
      >
        <h2 className="text-center text-2xl font-semibold italic sm:text-3xl" style={HEADING}>
          Here endeth the session
        </h2>
        <Fleuron />

        <p className="text-[0.95rem] leading-relaxed first-letter:float-left first-letter:mr-2 first-letter:mt-1 first-letter:text-5xl first-letter:font-bold first-letter:leading-[0.8] first-letter:text-primary"
          style={HEADING}>
          {account(s)}
        </p>

        <Fleuron />

        <table className="mx-auto w-full max-w-xs text-sm" style={HEADING}>
          <tbody>
            {stats(s).map((st) => (
              <tr key={st.key}>
                <td className="whitespace-nowrap py-0.5 pr-2 [font-variant:small-caps]">{st.label}</td>
                <td className="w-full border-b border-dotted" style={{ borderColor: "color-mix(in srgb, var(--text) 35%, transparent)" }} />
                <td className="py-0.5 pl-2 text-right font-semibold tabular-nums">{st.value}</td>
              </tr>
            ))}
            <tr>
              <td className="whitespace-nowrap py-0.5 pr-2 [font-variant:small-caps]">Time</td>
              <td className="w-full border-b border-dotted" style={{ borderColor: "color-mix(in srgb, var(--text) 35%, transparent)" }} />
              <td className="py-0.5 pl-2 text-right font-semibold tabular-nums">{clock(s.elapsedMs)}</td>
            </tr>
          </tbody>
        </table>

        <div className="mt-5 flex items-end justify-between gap-3">
          <div
            aria-hidden
            className="grid h-14 w-14 shrink-0 place-items-center rounded-full text-center text-[0.6rem] font-bold leading-tight text-white"
            style={{
              background: "radial-gradient(circle at 35% 30%, color-mix(in srgb, var(--primary) 70%, #fff), color-mix(in srgb, var(--primary) 75%, #400) 70%)",
              boxShadow: "0 2px 4px rgba(0,0,0,0.3), inset 0 0 0 3px rgba(0,0,0,0.12)",
              transform: "rotate(-12deg)",
            }}
          >
            <span>
              <span className="block text-base leading-none">∎</span>Q.E.D.
            </span>
          </div>
          <DoneButton onClose={onClose} label="Roll up the scroll" />
        </div>
      </Enter>
      <div style={ROLL} />
    </div>
  );
}
