/**
 * Drawing kit for the wallpaper canvases: reads the
 * palette from the CSS variables on <html> (and watches it change), small
 * colour and maths helpers, a seeded random generator, cached glow sprites
 * and the path builders for the recurring shapes (star, heart, leaf, petal).
 */

export interface Rgb {
  r: number;
  g: number;
  b: number;
}

const TOKENS = [
  "text",
  "background",
  "surface",
  "primary",
  "secondary",
  "accent",
  "border",
  "muted",
  "success",
  "warning",
  "error",
] as const;

type Token = (typeof TOKENS)[number];

export type Palette = Record<Token, Rgb> & {
  dark: boolean;
  fontBody: string;
  fontHeading: string;
  fontMono: string;
  /** Changes whenever any colour, font or the dark flag changes. */
  key: string;
};

export const TAU = Math.PI * 2;
export const WHITE: Rgb = { r: 255, g: 255, b: 255 };
export const BLACK: Rgb = { r: 0, g: 0, b: 0 };

/* ------------------------------------------------------------------ */
/* Maths and randomness                                                 */
/* ------------------------------------------------------------------ */

export const clamp = (v: number, lo: number, hi: number): number => (v < lo ? lo : v > hi ? hi : v);
export const lerp = (a: number, b: number, t: number): number => a + (b - a) * t;

export function smoothstep(e0: number, e1: number, x: number): number {
  const t = clamp((x - e0) / (e1 - e0), 0, 1);
  return t * t * (3 - 2 * t);
}

/** Mulberry32: tiny, fast, good enough for scattering decoration. */
export function rng(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export const range = (r: () => number, lo: number, hi: number): number => lo + (hi - lo) * r();

export function pick<T>(r: () => number, list: readonly T[]): T {
  return list[Math.floor(r() * list.length) % list.length];
}

/* ------------------------------------------------------------------ */
/* Colour                                                               */
/* ------------------------------------------------------------------ */

/** Parse #rgb, #rgba, #rrggbb, #rrggbbaa, rgb() and rgba(); alpha is ignored. */
export function parseColor(input: string): Rgb | null {
  const s = input.trim().toLowerCase();
  if (s.startsWith("#")) {
    const h = s.slice(1);
    if (/^[0-9a-f]{3,4}$/.test(h)) {
      return { r: parseInt(h[0] + h[0], 16), g: parseInt(h[1] + h[1], 16), b: parseInt(h[2] + h[2], 16) };
    }
    if (/^[0-9a-f]{6}([0-9a-f]{2})?$/.test(h)) {
      return { r: parseInt(h.slice(0, 2), 16), g: parseInt(h.slice(2, 4), 16), b: parseInt(h.slice(4, 6), 16) };
    }
    return null;
  }
  const m = /^rgba?\(([^)]+)\)$/.exec(s);
  if (!m) return null;
  const parts = m[1].split(/[\s,/]+/).filter(Boolean);
  if (parts.length < 3) return null;
  const ch = parts.slice(0, 3).map((p) => (p.endsWith("%") ? parseFloat(p) * 2.55 : parseFloat(p)));
  if (ch.some((v) => Number.isNaN(v))) return null;
  return { r: clamp(Math.round(ch[0]), 0, 255), g: clamp(Math.round(ch[1]), 0, 255), b: clamp(Math.round(ch[2]), 0, 255) };
}

let probe: CanvasRenderingContext2D | null | undefined;

/**
 * Any CSS colour token value: hex and rgb() directly, gradients by their
 * first colour (some palettes set --background to a gradient), anything
 * else (hsl, names) through the canvas parser. Null when unreadable.
 */
export function normalizeColor(s: string): Rgb | null {
  const v = s.trim();
  if (!v) return null;
  const direct = parseColor(v);
  if (direct) return direct;
  const inner = /#[0-9a-f]{3,8}\b|rgba?\([^)]*\)/i.exec(v);
  if (inner) return parseColor(inner[0]);
  if (probe === undefined) {
    try {
      probe = document.createElement("canvas").getContext("2d");
    } catch {
      probe = null;
    }
  }
  if (!probe) return null;
  const sentinel = "#010203";
  probe.fillStyle = sentinel;
  probe.fillStyle = v;
  const out = String(probe.fillStyle);
  return out === sentinel ? null : parseColor(out);
}

export function css(c: Rgb, a = 1): string {
  return a >= 1 ? `rgb(${c.r | 0},${c.g | 0},${c.b | 0})` : `rgba(${c.r | 0},${c.g | 0},${c.b | 0},${clamp(a, 0, 1).toFixed(3)})`;
}

export function mix(a: Rgb, b: Rgb, t: number): Rgb {
  return { r: lerp(a.r, b.r, t), g: lerp(a.g, b.g, t), b: lerp(a.b, b.b, t) };
}

/** Relative luminance 0–1 (sRGB, WCAG formula). */
export function luminance(c: Rgb): number {
  const f = (v: number) => {
    const x = v / 255;
    return x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b);
}

const FALLBACK: Record<Token, string> = {
  text: "#111827",
  background: "#ffffff",
  surface: "#f9fafb",
  primary: "#2563eb",
  secondary: "#6366f1",
  accent: "#f59e0b",
  border: "#e5e7eb",
  muted: "#6b7280",
  success: "#16a34a",
  warning: "#d97706",
  error: "#dc2626",
};

/** The current palette from the CSS variables on <html>. */
export function readPalette(root: HTMLElement = document.documentElement): Palette {
  const cs = getComputedStyle(root);
  const out = {} as Record<Token, Rgb>;
  for (const t of TOKENS) {
    out[t] = normalizeColor(cs.getPropertyValue(`--${t}`)) ?? (parseColor(FALLBACK[t]) as Rgb);
  }
  const attr = root.getAttribute("data-dark");
  const dark = attr === "true" ? true : attr === "false" ? false : luminance(out.background) < 0.35;
  const fontBody = cs.getPropertyValue("--font-family").trim() || "system-ui, sans-serif";
  const fontHeading = cs.getPropertyValue("--font-heading").trim() || fontBody;
  const fontMono = cs.getPropertyValue("--font-mono").trim() || "Consolas, monospace";
  const key = [...TOKENS.map((t) => css(out[t])), dark, fontBody, fontHeading, fontMono].join("|");
  return { ...out, dark, fontBody, fontHeading, fontMono, key };
}

/** Call `cb` with the new palette whenever <html> attributes change it. */
export function watchPalette(cb: (p: Palette) => void): () => void {
  const root = document.documentElement;
  let key = readPalette(root).key;
  const mo = new MutationObserver(() => {
    const p = readPalette(root);
    if (p.key === key) return;
    key = p.key;
    cb(p);
  });
  mo.observe(root, { attributes: true });
  return () => mo.disconnect();
}

/* ------------------------------------------------------------------ */
/* Sprites and shapes                                                   */
/* ------------------------------------------------------------------ */

const glowCache = new Map<string, HTMLCanvasElement>();

/** A soft round glow (white-hot core fading through `color`), cached per colour. */
export function glowSprite(color: string, core = 0.25): HTMLCanvasElement {
  const k = `${color}|${core}`;
  const hit = glowCache.get(k);
  if (hit) return hit;
  const c = document.createElement("canvas");
  c.width = c.height = 64;
  const g = c.getContext("2d");
  if (g) {
    const grad = g.createRadialGradient(32, 32, 0, 32, 32, 32);
    grad.addColorStop(0, "rgba(255,255,255,1)");
    grad.addColorStop(core, color);
    grad.addColorStop(1, "rgba(0,0,0,0)");
    g.fillStyle = grad;
    g.fillRect(0, 0, 64, 64);
  }
  if (glowCache.size > 64) glowCache.clear();
  glowCache.set(k, c);
  return c;
}

/** A star with `points` tips, centred on 0,0. */
export function pathStar(ctx: CanvasRenderingContext2D, points: number, outer: number, inner: number): void {
  ctx.beginPath();
  for (let i = 0; i < points * 2; i++) {
    const r = i % 2 === 0 ? outer : inner;
    const a = (i / (points * 2)) * TAU - Math.PI / 2;
    if (i === 0) ctx.moveTo(Math.cos(a) * r, Math.sin(a) * r);
    else ctx.lineTo(Math.cos(a) * r, Math.sin(a) * r);
  }
  ctx.closePath();
}

/** A four-point sparkle with concave sides. */
export function pathSparkle(ctx: CanvasRenderingContext2D, s: number): void {
  const k = s * 0.18;
  ctx.beginPath();
  ctx.moveTo(0, -s);
  ctx.quadraticCurveTo(k, -k, s, 0);
  ctx.quadraticCurveTo(k, k, 0, s);
  ctx.quadraticCurveTo(-k, k, -s, 0);
  ctx.quadraticCurveTo(-k, -k, 0, -s);
  ctx.closePath();
}

export function pathHeart(ctx: CanvasRenderingContext2D, s: number): void {
  ctx.beginPath();
  ctx.moveTo(0, s * 0.35);
  ctx.bezierCurveTo(-s * 1.1, -s * 0.35, -s * 0.55, -s * 1.05, 0, -s * 0.45);
  ctx.bezierCurveTo(s * 0.55, -s * 1.05, s * 1.1, -s * 0.35, 0, s * 0.35);
  ctx.closePath();
}

/** A pointed leaf along the x axis, tip at +s. */
export function pathLeaf(ctx: CanvasRenderingContext2D, s: number): void {
  ctx.beginPath();
  ctx.moveTo(-s, 0);
  ctx.quadraticCurveTo(-s * 0.1, -s * 0.75, s, 0);
  ctx.quadraticCurveTo(-s * 0.1, s * 0.75, -s, 0);
  ctx.closePath();
}

/** A cherry-blossom petal: narrow at the base (-s), notched at the tip (+s). */
export function pathPetal(ctx: CanvasRenderingContext2D, s: number): void {
  ctx.beginPath();
  ctx.moveTo(-s, 0);
  ctx.bezierCurveTo(-s * 0.4, -s * 0.85, s * 0.75, -s * 0.8, s, -s * 0.22);
  ctx.lineTo(s * 0.72, 0);
  ctx.lineTo(s, s * 0.22);
  ctx.bezierCurveTo(s * 0.75, s * 0.8, -s * 0.4, s * 0.85, -s, 0);
  ctx.closePath();
}
