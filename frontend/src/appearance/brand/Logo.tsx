/**
 * Club logos drawn from their glyph outlines (logoData.ts), so every variant
 * keeps the exact letterforms; variants only change colour, stroke, filters
 * and motion (styles/appearance/logo.css). The variant follows the `logo`
 * slot; "auto" picks one that suits the palette.
 */

import { type CSSProperties, useEffect, useId, useRef } from "react";

import { useAppearance } from "../store";
import { resolve } from "../registry";
import { LOGOS, type LogoDef, type LogoItem } from "./logoData";

export type LogoName = "matrix" | "inline" | "coding";
export type LogoVariant =
  | "original" | "tinted" | "mono" | "pixel" | "terminal" | "comic" | "glossy" | "chalk" | "neon" | "blueprint";

const AUTO: Record<string, LogoVariant> = {
  "pixel-art": "pixel", handheld: "pixel",
  ascii: "terminal", "amber-crt": "terminal",
  comic: "comic", "frutiger-aero": "glossy", blackboard: "chalk",
  midnight: "neon", synthwave: "neon", vaporwave: "neon", "tokyo-night": "neon",
  blueprint: "blueprint", ember: "tinted", manuscript: "mono", "dark-academia": "tinted",
  pastel: "tinted", sakura: "tinted", "android-kitkat": "tinted", sage: "tinted",
};

/** The variant "auto" picks for a palette (theme id). */
export function autoLogoVariant(theme: string | undefined): LogoVariant {
  return (theme && AUTO[theme]) || "original";
}

/** The logo variant the current loadout asks for. */
export function useLogoVariant(): LogoVariant {
  return useAppearance((s) => {
    const id = resolve(s.loadout, "logo")?.id ?? "logo.auto";
    const v = id.slice(5);
    if (v !== "auto") return v as LogoVariant;
    const theme = resolve(s.loadout, "palette")?.data?.theme;
    return autoLogoVariant(typeof theme === "string" ? theme : undefined);
  });
}

function safeId(raw: string): string {
  return raw.replace(/[^a-zA-Z0-9_-]/g, "");
}

interface SvgProps {
  name: LogoName;
  variant: Exclude<LogoVariant, "pixel" | "terminal">;
  className?: string;
  style?: CSSProperties;
  /** Extra overlays for the row-reduce animation. */
  reduce?: boolean;
  title?: string;
  svgRef?: React.Ref<SVGSVGElement>;
}

/** Comic shadow offset per logo, in viewBox units (about a tenth of a letter's height). */
const COMIC_SHADOW: Record<LogoName, number> = { matrix: 4, inline: 1.5, coding: 5 };
/** The inked parts that cast the comic shadow (not the grey zeros and arguments). */
const CASTS_SHADOW = /^(br|d|cw|cc)\b/;

/** Overlays: variables that row-reduce to the zeros (z, x, n from the argument font). */
const REDUCE_CELLS: [string, string, number, number][] = [
  ["12", "glyph-1-4", 137.5, 40.5],
  ["13", "glyph-1-1", 231, 40.5],
  ["21", "glyph-1-3", 43.5, 96.5],
  ["23", "glyph-1-4", 231, 96.5],
  ["31", "glyph-1-1", 43.5, 152.5],
  ["32", "glyph-1-3", 137.5, 152.5],
];

function renderItem(it: LogoItem, i: number, prefix: string) {
  return it.d ? (
    <path key={i} className={it.role} d={it.d} />
  ) : (
    <g key={i} className={it.role}>
      {it.uses!.map((u, k) => (
        <use key={k} className="ch" href={`#${prefix}${u.g}`} x={u.x} y={u.y} />
      ))}
    </g>
  );
}

export function LogoSvg({ name, variant, className, style, reduce, title, svgRef }: SvgProps) {
  const uid = safeId(useId());
  const L: LogoDef = LOGOS[name];
  const p = `${uid}-`;
  return (
    <svg
      ref={svgRef}
      className={`amp-logo amp-logo-${name} v-${variant} ${className ?? ""}`}
      viewBox={L.viewBox}
      style={style}
      role="img"
      aria-label={title ?? (name === "coding" ? "Coding Club" : "ampliφ")}
    >
      <defs>
        {Object.entries(L.glyphs).map(([id, d]) => (
          <path key={id} id={`${p}${id}`} d={d} />
        ))}
      </defs>
      {reduce && name === "matrix" && <rect className="rowbar" x="10" y="0" width="262" height="44" rx="6" />}
      {variant === "comic" && (
        // One shadow layer under everything, so no piece's shadow lands on a neighbouring piece.
        <g className="comic-shadow" transform={`translate(${COMIC_SHADOW[name]} ${COMIC_SHADOW[name]})`} aria-hidden="true">
          {L.items.filter((it) => CASTS_SHADOW.test(it.role)).map((it, i) => renderItem(it, i, p))}
        </g>
      )}
      {L.items.map((it, i) => renderItem(it, i, p))}
      {reduce &&
        name === "matrix" &&
        REDUCE_CELLS.map(([c, g, x, y]) => (
          <g key={c} className={`v v${c}`}>
            <use href={`#${p}${g}`} transform={`translate(${x} ${y}) scale(1.35)`} />
          </g>
        ))}
    </svg>
  );
}

/* ------------------------------------------------------------------ */
/* Pixel and terminal variants                                          */
/* ------------------------------------------------------------------ */

const PIXEL_CSS =
  ".tag{fill:none}.br{fill:var(--px-ink)}.d1{fill:var(--px-r1)}.d2{fill:var(--px-r2)}.d3{fill:var(--px-r3)}" +
  ".s{fill:var(--px-sub)}.z{fill:var(--px-zero)}.cw{fill:var(--px-cw)}.cc{fill:var(--px-club)}";

/**
 * The logo as a standalone SVG for rasterizing at `width` px. Each glyph is
 * moved onto the pixel grid, so a glyph used several times (the six zeros)
 * comes out as the same pixels every time.
 */
export function pixelSvg(name: LogoName, width: number, height: number, colors: Record<string, string>): string {
  const L = LOGOS[name];
  const [vx, vy, vw, vh] = L.viewBox.split(/\s+/).map(Number);
  const snap = (v: number, origin: number, unit: number) => origin + Math.round((v - origin) / unit) * unit;
  const css = PIXEL_CSS.replace(/var\((--px-[a-z0-9]+)\)/g, (_, k: string) => colors[k] ?? "#888");
  const defs = Object.entries(L.glyphs).map(([id, d]) => `<path id="g${id}" d="${d}"/>`).join("");
  const body = L.items
    .map((it) =>
      it.d
        ? `<path class="${it.role}" d="${it.d}"/>`
        : `<g class="${it.role}">${it.uses!
            .map((u) => `<use href="#g${u.g}" x="${snap(u.x, vx, vw / width).toFixed(4)}" y="${snap(u.y, vy, vh / height).toFixed(4)}"/>`)
            .join("")}</g>`,
    )
    .join("");
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${L.viewBox}" preserveAspectRatio="none"><defs>${defs}</defs><style>${css}</style>${body}</svg>`;
}

const PIXEL_WIDTH: Record<LogoName, number> = { matrix: 110, inline: 84, coding: 120 };

/** Rasterize at a tiny width with hard alpha, then show it scaled up crisply. */
export function PixelLogo({ name, className, style }: { name: LogoName; className?: string; style?: CSSProperties }) {
  const ref = useRef<HTMLCanvasElement>(null);
  const theme = useAppearance((s) => resolve(s.loadout, "palette")?.id);
  useEffect(() => {
    const c = ref.current;
    if (!c) return;
    const cs = getComputedStyle(c);
    const v = (k: string, fb: string) => cs.getPropertyValue(k).trim() || fb;
    const colors = {
      "--px-ink": v("--primary", "#ffd166"),
      "--px-r1": "#ff4d4d",
      "--px-r2": "#ef476f",
      "--px-r3": "#c9184a",
      "--px-sub": v("--border", "#3d5a73"),
      "--px-zero": v("--muted", "#8aa3b8"),
      "--px-cw": v("--text", "#e8e8e8"),
      "--px-club": "#ffd60a",
    };
    const L = LOGOS[name];
    const [, , vw, vh] = L.viewBox.split(/\s+/).map(Number);
    const w = PIXEL_WIDTH[name];
    const h = Math.round((w * vh) / vw);
    const img = new Image();
    img.onload = () => {
      c.width = w;
      c.height = h;
      const g = c.getContext("2d");
      if (!g) return;
      g.clearRect(0, 0, w, h);
      g.drawImage(img, 0, 0, w, h);
      const px = g.getImageData(0, 0, w, h);
      for (let i = 3; i < px.data.length; i += 4) px.data[i] = px.data[i] > 90 ? 255 : 0;
      g.putImageData(px, 0, 0);
    };
    img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(pixelSvg(name, w, h, colors));
  }, [name, theme]);
  return (
    <canvas
      ref={ref}
      className={`amp-logo amp-logo-${name} v-pixel ${className ?? ""}`}
      style={{ imageRendering: "pixelated", ...style }}
      role="img"
      aria-label={name === "coding" ? "Coding Club" : "ampliφ"}
    />
  );
}

const MATRIX_CELLS: [string, string | null][][] = [
  [["amp", "(z)"], ["0", null], ["0", null]],
  [["0", null], ["li", "(x)"], ["0", null]],
  [["0", null], ["0", null], ["φ", "(n)"]],
];

export function TerminalLogo({ name, className }: { name: LogoName; className?: string }) {
  if (name === "inline") {
    return (
      <pre className={`amp-ascii ${className ?? ""}`} aria-label="ampliφ">
        <span className="r">ampliφ</span>
        <span className="dim">@iitd-ad</span>
      </pre>
    );
  }
  if (name === "coding") {
    return (
      <pre className={`amp-ascii ${className ?? ""}`} aria-label="Coding Club">
        <span className="dim">$ </span>
        <span className="r">coding</span>
        <span className="dim">_</span>
        <span className="club">club</span>
      </pre>
    );
  }
  const W = 9;
  const inner = W * 3;
  const cell = ([main, arg]: [string, string | null], key: number) => {
    const len = main.length + (arg?.length ?? 0);
    const left = Math.floor((W - len) / 2);
    return (
      <span key={key}>
        {" ".repeat(left)}
        {arg ? (
          <>
            <span className="r">{main}</span>
            <span className="fnt">{arg}</span>
          </>
        ) : (
          <span className="dim">{main}</span>
        )}
        {" ".repeat(W - len - left)}
      </span>
    );
  };
  return (
    <pre className={`amp-ascii ${className ?? ""}`} aria-label="ampliφ">
      <span className="dim">{"┌─" + " ".repeat(inner - 2) + "─┐"}</span>
      {"\n"}
      {MATRIX_CELLS.map((row, r) => (
        <span key={r}>
          <span className="dim">│</span>
          {row.map(cell)}
          <span className="dim">│</span>
          {"\n"}
        </span>
      ))}
      <span className="dim">{"└─" + " ".repeat(inner - 2) + "─┘"}</span>
    </pre>
  );
}

/** A club logo in the variant the theme asks for (or `variant` to force one). */
export function Logo({
  name,
  variant,
  className,
  style,
}: {
  name: LogoName;
  variant?: LogoVariant;
  className?: string;
  style?: CSSProperties;
}) {
  const auto = useLogoVariant();
  const v = variant ?? auto;
  if (v === "pixel") return <PixelLogo name={name} className={className} style={style} />;
  if (v === "terminal") return <TerminalLogo name={name} className={className} />;
  return <LogoSvg name={name} variant={v} className={className} style={style} />;
}

/** Gradients and filters the variants reference. Rendered once by AppearanceRoot. */
export function BrandDefs() {
  return (
    <svg width="0" height="0" style={{ position: "absolute" }} aria-hidden="true" focusable="false">
      <defs>
        <linearGradient id="amp-gloss1" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#ff9a9a" />
          <stop offset=".48" stopColor="#ff2a2a" />
          <stop offset=".52" stopColor="#d40000" />
          <stop offset="1" stopColor="#ff4a4a" />
        </linearGradient>
        <linearGradient id="amp-gloss2" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#ff7d7d" />
          <stop offset=".5" stopColor="#c90000" />
          <stop offset="1" stopColor="#e53030" />
        </linearGradient>
        <linearGradient id="amp-gloss3" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#d45a5a" />
          <stop offset=".5" stopColor="#7d0000" />
          <stop offset="1" stopColor="#a51e1e" />
        </linearGradient>
        <filter id="amp-chalk" x="-5%" y="-5%" width="110%" height="110%">
          <feTurbulence type="fractalNoise" baseFrequency="1.1" numOctaves={2} seed={3} result="n" />
          <feDisplacementMap in="SourceGraphic" in2="n" scale="1.6" result="d" />
          <feTurbulence type="fractalNoise" baseFrequency="2.2" numOctaves={1} seed={9} result="n2" />
          <feColorMatrix in="n2" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -2.2 1.55" result="holes" />
          <feComposite in="d" in2="holes" operator="in" />
        </filter>
        <filter id="amp-rough" x="-3%" y="-3%" width="106%" height="106%">
          <feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves={2} seed={7} result="n" />
          <feDisplacementMap in="SourceGraphic" in2="n" scale="3.5" />
        </filter>
        <filter id="amp-neon" x="-20%" y="-30%" width="140%" height="160%">
          <feGaussianBlur in="SourceGraphic" stdDeviation="2.2" result="b1" />
          <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="b2" />
          <feMerge>
            <feMergeNode in="b2" />
            <feMergeNode in="b1" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
    </svg>
  );
}
