/**
 * Small SVG primitives for the room art. Paint goes through `style` so CSS
 * variables and color-mix() work everywhere, which lets the palette tint the
 * room. Also: club logos placed inside the scene, and a bitmap helper for the
 * pixel cabin.
 */

import type { CSSProperties, ReactNode } from "react";

import { Logo, useLogoVariant, type LogoName } from "../brand/Logo";

export interface Paint {
  f?: string;
  s?: string;
  sw?: number;
  o?: number;
  cls?: string;
  style?: CSSProperties;
  t?: string;
}

const st = (p: Paint): CSSProperties => ({ fill: p.f, stroke: p.s, strokeWidth: p.sw, opacity: p.o, ...p.style });

/** color-mix shorthand: `pct`% of `a`, the rest `b`. */
export const mix = (a: string, pct: number, b: string): string => `color-mix(in srgb, ${a} ${pct}%, ${b})`;

export function R({ x, y, w, h, rx, ...p }: { x: number; y: number; w: number; h: number; rx?: number } & Paint) {
  return <rect x={x} y={y} width={Math.max(0, w)} height={Math.max(0, h)} rx={rx} className={p.cls} style={st(p)} transform={p.t} />;
}

export function P({ d, ...p }: { d: string } & Paint) {
  return <path d={d} className={p.cls} style={st(p)} transform={p.t} />;
}

export function C({ cx, cy, r, ...p }: { cx: number; cy: number; r: number } & Paint) {
  return <circle cx={cx} cy={cy} r={r} className={p.cls} style={st(p)} transform={p.t} />;
}

export function E({ cx, cy, rx, ry, ...p }: { cx: number; cy: number; rx: number; ry: number } & Paint) {
  return <ellipse cx={cx} cy={cy} rx={rx} ry={ry} className={p.cls} style={st(p)} transform={p.t} />;
}

export function Ln({ x1, y1, x2, y2, ...p }: { x1: number; y1: number; x2: number; y2: number } & Paint) {
  return (
    <line x1={x1} y1={y1} x2={x2} y2={y2} className={p.cls} style={{ strokeLinecap: "round", ...st(p) }} transform={p.t} />
  );
}

export function Tx({
  x,
  y,
  size,
  f,
  anchor = "start",
  weight,
  mono,
  ls,
  o,
  t,
  children,
}: {
  x: number;
  y: number;
  size: number;
  f: string;
  anchor?: "start" | "middle" | "end";
  weight?: number;
  mono?: boolean;
  ls?: number;
  o?: number;
  t?: string;
  children: ReactNode;
}) {
  return (
    <text
      x={x}
      y={y}
      transform={t}
      textAnchor={anchor}
      style={{
        fill: f,
        fontSize: size,
        fontWeight: weight,
        letterSpacing: ls,
        opacity: o,
        fontFamily: mono ? "var(--font-mono, ui-monospace, monospace)" : undefined,
      }}
    >
      {children}
    </text>
  );
}

/**
 * A club logo inside the scene (foreignObject, so every logo variant works,
 * including the pixel canvas). Thumbnails draw plain text instead.
 */
export function ClubLogo({
  name,
  x,
  y,
  w,
  h,
  preview,
  color = "var(--text)",
}: {
  name: LogoName;
  x: number;
  y: number;
  w: number;
  h: number;
  preview: boolean;
  color?: string;
}) {
  // Text art doesn't fit on a pennant or a mug; draw the one-ink outline instead.
  const variant = useLogoVariant();
  if (preview) {
    return (
      <Tx x={x + w / 2} y={y + h * 0.78} size={h * 0.8} f={color} anchor="middle" weight={700}>
        {name === "coding" ? "CODING CLUB" : "ampliφ"}
      </Tx>
    );
  }
  return (
    <foreignObject x={x} y={y} width={w} height={h} style={{ overflow: "visible", pointerEvents: "none" }}>
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: Math.max(4, h * 0.55),
          lineHeight: 1,
          color,
        }}
      >
        <Logo name={name} variant={variant === "terminal" ? "mono" : undefined} style={{ width: "100%", height: "auto", maxHeight: "100%" }} />
      </div>
    </foreignObject>
  );
}

/**
 * Pixel art from rows of characters; each character is a palette key, "." is
 * transparent. Horizontal runs merge into one rect.
 */
export function Bitmap({
  x,
  y,
  u,
  rows,
  pal,
}: {
  x: number;
  y: number;
  u: number;
  rows: readonly string[];
  pal: Record<string, string>;
}) {
  const out: ReactNode[] = [];
  rows.forEach((row, j) => {
    let i = 0;
    while (i < row.length) {
      const ch = row[i];
      if (!pal[ch]) {
        i++;
        continue;
      }
      let k = i + 1;
      while (k < row.length && row[k] === ch) k++;
      out.push(<rect key={`${j}-${i}`} x={x + i * u} y={y + j * u} width={(k - i) * u} height={u} style={{ fill: pal[ch] }} />);
      i = k;
    }
  });
  return <g>{out}</g>;
}
