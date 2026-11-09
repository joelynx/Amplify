/**
 * results.sticker: a Pastel sticker sheet. Each number is a die-cut sticker
 * (flower, star, heart, cloud …) in a soft tint of the palette, popping on
 * with a springy wobble when whimsy allows.
 */

import { HEADING, type StyleProps, DoneButton, Enter, clock, modeLabel, stats, type StatKey } from "../shared";

type Shape = "flower" | "star" | "heart" | "circle" | "cloud" | "square" | "ticket";

function starPath(cx: number, cy: number, R: number, r: number, n = 5): string {
  const pts: string[] = [];
  for (let i = 0; i < n * 2; i++) {
    const a = -Math.PI / 2 + (i * Math.PI) / n;
    const rad = i % 2 ? r : R;
    pts.push(`${(cx + rad * Math.cos(a)).toFixed(1)} ${(cy + rad * Math.sin(a)).toFixed(1)}`);
  }
  return `M${pts.join(" L")} Z`;
}

/** A scalloped circle: arcs bulging outward between points on a ring. */
function flowerPath(cx: number, cy: number, R: number, n: number, bulge: number): string {
  const pt = (i: number) => {
    const a = -Math.PI / 2 + (i * 2 * Math.PI) / n;
    return `${(cx + R * Math.cos(a)).toFixed(1)} ${(cy + R * Math.sin(a)).toFixed(1)}`;
  };
  let d = `M${pt(0)}`;
  for (let i = 1; i <= n; i++) d += ` A${bulge} ${bulge} 0 0 1 ${pt(i)}`;
  return `${d} Z`;
}

const PATHS: Record<Shape, string> = {
  flower: flowerPath(50, 50, 33, 8, 15),
  star: starPath(50, 54, 47, 23),
  heart: "M50 88 C22 68 6 50 12 32 C18 14 40 12 50 30 C60 12 82 14 88 32 C94 50 78 68 50 88 Z",
  circle: "M50 8 A42 42 0 1 1 49.9 8 Z",
  cloud: "M26 80 C10 80 6 60 20 56 C14 40 32 30 42 38 C46 22 70 20 76 38 C92 36 98 58 86 64 C96 76 84 86 72 80 Z",
  square: "M30 10 H70 A20 20 0 0 1 90 30 V70 A20 20 0 0 1 70 90 H30 A20 20 0 0 1 10 70 V30 A20 20 0 0 1 30 10 Z",
  ticket: "M14 24 H86 A8 8 0 0 1 94 32 V42 A8 8 0 0 0 94 58 V68 A8 8 0 0 1 86 76 H14 A8 8 0 0 1 6 68 V58 A8 8 0 0 0 6 42 V32 A8 8 0 0 1 14 24 Z",
};

/** Where the number sits inside each shape (percent from the top). */
const CENTRE: Record<Shape, number> = { flower: 50, star: 57, heart: 47, circle: 50, cloud: 60, square: 50, ticket: 50 };

const LOOK: Record<StatKey | "time", { shape: Shape; color: string; label: string }> = {
  answered: { shape: "flower", color: "var(--secondary)", label: "answered" },
  unaided: { shape: "star", color: "var(--success)", label: "on your own" },
  assisted: { shape: "heart", color: "var(--primary)", label: "with help" },
  partial: { shape: "circle", color: "var(--warning)", label: "partly" },
  missed: { shape: "cloud", color: "var(--muted)", label: "missed" },
  toReview: { shape: "square", color: "var(--accent)", label: "to review" },
  time: { shape: "ticket", color: "var(--secondary)", label: "time" },
};

const TILT = [-6, 4, -3, 7, -5, 3, -2];

function StickerShape({ shape, color, value, tilt, animate, delay, label }: {
  shape: Shape; color: string; value: string; tilt: number; animate: boolean; delay: number; label: string;
}) {
  return (
    <figure className="m-0 flex flex-col items-center gap-1">
      <Enter
        animate={animate}
        delay={delay}
        duration={520}
        from={`scale(0.2) rotate(${tilt - 25}deg)`}
        to={`rotate(${tilt}deg)`}
        easing="cubic-bezier(.34,1.56,.64,1)"
        className="relative h-20 w-20 sm:h-24 sm:w-24"
      >
        <svg viewBox="0 0 100 100" className="absolute inset-0 h-full w-full overflow-visible" aria-hidden
          style={{ filter: "drop-shadow(0 2px 2px rgba(0,0,0,0.18))" }}>
          <path
            d={PATHS[shape]}
            style={{ fill: `color-mix(in srgb, ${color} 32%, var(--surface))` }}
            stroke="#fff"
            strokeWidth={6}
            strokeLinejoin="round"
          />
        </svg>
        <span
          className={
            "absolute left-1/2 -translate-x-1/2 -translate-y-1/2 whitespace-nowrap font-bold tabular-nums " +
            (value.length > 4 ? "text-base sm:text-lg" : "text-xl sm:text-2xl")
          }
          style={{ ...HEADING, top: `${CENTRE[shape]}%`, color: "var(--text)" }}
        >
          {value}
        </span>
      </Enter>
      <figcaption className="text-xs lowercase text-muted">{label}</figcaption>
    </figure>
  );
}

export function Sticker({ s, level, onClose }: StyleProps) {
  const items = [
    ...stats(s).map((st) => ({ key: st.key as StatKey | "time", value: String(st.value) })),
    { key: "time" as const, value: clock(s.elapsedMs) },
  ];

  return (
    <div
      className="rounded-[22px] border-2 border-dashed p-5 text-text sm:p-6"
      style={{
        borderColor: "color-mix(in srgb, var(--text) 22%, transparent)",
        backgroundColor: "color-mix(in srgb, var(--accent) 12%, var(--surface))",
        backgroundImage: "radial-gradient(color-mix(in srgb, var(--text) 10%, transparent) 1px, transparent 1.6px)",
        backgroundSize: "14px 14px",
      }}
    >
      <header className="text-center">
        <h2 className="text-2xl font-bold lowercase" style={HEADING}>session stickers ✿</h2>
        <p className="mt-0.5 text-xs lowercase text-muted">
          {modeLabel(s.mode)} · {clock(s.elapsedMs)}
        </p>
      </header>

      <div className="mt-5 grid grid-cols-3 justify-items-center gap-x-3 gap-y-4 sm:grid-cols-4">
        {items.map((it, i) => (
          <StickerShape
            key={it.key}
            shape={LOOK[it.key].shape}
            color={LOOK[it.key].color}
            label={LOOK[it.key].label}
            value={it.value}
            tilt={TILT[i % TILT.length]}
            animate={level > 0}
            delay={120 + i * 110}
          />
        ))}
      </div>

      {onClose && (
        <div className="mt-5 flex justify-center">
          <DoneButton onClose={onClose} label="all done ✿" className="rounded-full lowercase" />
        </div>
      )}
    </div>
  );
}
