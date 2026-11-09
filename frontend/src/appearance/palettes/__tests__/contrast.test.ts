/**
 * Palette contrast (Makeover.md §5.1, §11). Reads the palette overlays in
 * styles/themes with node fs, parses each `[data-theme]` block and checks
 * WCAG 2 contrast ratios. The makeover palettes in extra.css must pass every
 * check; the original theme.css overlays are only reported, and the test
 * fails if one of them gets worse than the known list below.
 */

import { readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { PALETTES } from "../../core/items";

const THEMES = resolve(dirname(fileURLToPath(import.meta.url)), "../../../../styles/themes");
const EXTRA = join(THEMES, "extra.css");

/* ------------------------------------------------------------------ colour maths */

type RGBA = [number, number, number, number];

const NAMED: Record<string, RGBA> = {
  white: [255, 255, 255, 1],
  black: [0, 0, 0, 1],
  transparent: [0, 0, 0, 0],
};

const COLOR_TOKEN = /#[0-9a-f]{3,8}\b|rgba?\([^)]*\)|\b(?:white|black|transparent)\b/gi;

function parseColor(raw: string): RGBA | null {
  const s = raw.trim().toLowerCase();
  if (NAMED[s]) return NAMED[s];
  let m = s.match(/^#([0-9a-f]{3,8})$/);
  if (m) {
    let h = m[1];
    if (h.length === 3 || h.length === 4) h = [...h].map((c) => c + c).join("");
    if (h.length !== 6 && h.length !== 8) return null;
    const n = (i: number) => parseInt(h.slice(i, i + 2), 16);
    return [n(0), n(2), n(4), h.length === 8 ? n(6) / 255 : 1];
  }
  m = s.match(/^rgba?\(([^)]*)\)$/);
  if (m) {
    const parts = m[1].split(/[\s,/]+/).filter(Boolean);
    if (parts.length < 3) return null;
    const ch = parts.slice(0, 3).map((p) => (p.endsWith("%") ? (parseFloat(p) * 255) / 100 : parseFloat(p)));
    const a = parts[3] === undefined ? 1 : parts[3].endsWith("%") ? parseFloat(parts[3]) / 100 : parseFloat(parts[3]);
    if ([...ch, a].some((x) => Number.isNaN(x))) return null;
    return [ch[0], ch[1], ch[2], a];
  }
  return null;
}

/** Every colour in a value (one for a plain colour, several for a gradient). */
function colorsIn(value: string | undefined): RGBA[] {
  if (!value) return [];
  return (value.match(COLOR_TOKEN) ?? []).map(parseColor).filter((c): c is RGBA => c !== null);
}

function over(top: RGBA, bottom: RGBA): RGBA {
  const a = top[3];
  return [0, 1, 2].map((i) => top[i] * a + bottom[i] * (1 - a)).concat(1) as RGBA;
}

function luminance([r, g, b]: RGBA): number {
  const lin = (c: number) => {
    const v = c / 255;
    return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
}

function contrast(a: RGBA, b: RGBA): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

/* ------------------------------------------------------------------ CSS parsing */

type Vars = Record<string, string>;

interface ThemeBlocks {
  base: Map<string, Vars>;
  a11y: Map<string, Vars>;
  /** Selectors of rules that are not palette blocks. */
  other: string[];
}

const BASE_SEL = /^(?::root)?\[data-theme="([\w-]+)"\]$/;
const A11Y_SEL = /^:root\[data-a11y="on"\]\[data-theme="([\w-]+)"\]$/;

function parseThemes(css: string): ThemeBlocks {
  const out: ThemeBlocks = { base: new Map(), a11y: new Map(), other: [] };
  const clean = css.replace(/\/\*[\s\S]*?\*\//g, "");
  for (const m of clean.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
    const vars: Vars = {};
    for (const decl of m[2].split(";")) {
      const i = decl.indexOf(":");
      const key = decl.slice(0, i).trim();
      if (i > 0 && key.startsWith("--")) vars[key] = decl.slice(i + 1).trim();
    }
    for (const sel of m[1].split(",").map((s) => s.trim())) {
      const base = sel.match(BASE_SEL);
      const a11y = sel.match(A11Y_SEL);
      if (base && Object.keys(vars).length) out.base.set(base[1], { ...out.base.get(base[1]), ...vars });
      else if (a11y && Object.keys(vars).length) out.a11y.set(a11y[1], { ...out.a11y.get(a11y[1]), ...vars });
      else out.other.push(sel);
    }
  }
  return out;
}

/* ------------------------------------------------------------------ checks */

interface Check {
  name: string;
  fg: string;
  bg: string;
  min: number;
}

const pair = (fg: string, bg: string, min: number): Check => ({
  name: `${fg.replace(/^--/, "")} on ${bg.replace(/^--/, "")}`,
  fg,
  bg,
  min,
});

/** What the brief requires of every palette. */
const REQUIRED: Check[] = [
  pair("--text", "--background", 4.5),
  pair("--text", "--surface", 4.5),
  pair("--muted", "--background", 4.5),
  pair("--on-primary", "--primary", 3),
];

/** Held to for the makeover palettes too: muted text sits on cards, primary is used as text. */
const ALSO: Check[] = [
  pair("--muted", "--surface", 4.5),
  pair("--primary", "--background", 3),
  pair("--success", "--background", 3),
  pair("--warning", "--background", 3),
  pair("--error", "--background", 3),
];

const HIGH_CONTRAST: Check[] = [
  pair("--text", "--background", 7),
  pair("--text", "--surface", 7),
  pair("--muted", "--background", 7),
  pair("--on-primary", "--primary", 3),
];

/** Colours a token can take, composited down to opaque. Backgrounds sit on white. */
function resolveToken(vars: Vars, token: string, under: RGBA[]): RGBA[] {
  // --on-primary is optional: buttons fall back to white text (tailwind.config.ts).
  const raw = token.startsWith("--") ? (vars[token] ?? (token === "--on-primary" ? "#ffffff" : undefined)) : token;
  const own = colorsIn(raw);
  return under.flatMap((u) => own.map((c) => over(c, u)));
}

/** Worst-case ratio for a check, or null when a colour could not be parsed. */
function ratioFor(vars: Vars, check: Check): number | null {
  const page = resolveToken(vars, "--background", [NAMED.white]);
  if (!page.length) return null;
  const bgs = check.bg === "--background" ? page : resolveToken(vars, check.bg, page);
  let worst = Infinity;
  for (const bg of bgs) {
    const fgs = resolveToken(vars, check.fg, [bg]);
    if (!fgs.length) return null;
    for (const fg of fgs) worst = Math.min(worst, contrast(fg, bg));
  }
  return Number.isFinite(worst) ? worst : null;
}

interface Failure {
  theme: string;
  mode: "normal" | "a11y";
  check: string;
  ratio: number | null;
  min: number;
}

function audit(theme: string, vars: Vars, checks: Check[], mode: Failure["mode"]): Failure[] {
  const out: Failure[] = [];
  for (const c of checks) {
    const ratio = ratioFor(vars, c);
    if (ratio === null || ratio < c.min) out.push({ theme, mode, check: c.name, ratio, min: c.min });
  }
  return out;
}

const fmt = (f: Failure) =>
  `${f.theme}${f.mode === "a11y" ? " (a11y)" : ""}: ${f.check} = ${f.ratio === null ? "unparseable" : f.ratio.toFixed(2)} (needs ${f.min})`;

/* ------------------------------------------------------------------ data */

const extra = parseThemes(readFileSync(EXTRA, "utf8"));

const existing = new Map<string, ThemeBlocks>();
for (const dir of readdirSync(THEMES)) {
  const file = join(THEMES, dir, "theme.css");
  try {
    if (statSync(file).isFile()) existing.set(dir, parseThemes(readFileSync(file, "utf8")));
  } catch {
    /* not a theme folder */
  }
}

const COLOUR_TOKENS = [
  "--text", "--background", "--surface", "--primary", "--secondary", "--accent",
  "--border", "--muted", "--success", "--warning", "--error",
];

/**
 * Required checks the original overlays fail today (reported, not fixed).
 * The test fails if a new failure appears; remove entries as they get fixed.
 */
const KNOWN_EXISTING: string[] = [];

/* ------------------------------------------------------------------ tests */

describe("makeover palettes (extra.css)", () => {
  const ids = [...extra.base.keys()];

  it("holds palette blocks only (no chrome or component rules)", () => {
    expect(extra.other).toEqual([]);
  });

  it("covers every palette item that has no overlay of its own", () => {
    const missing = PALETTES.map((p) => String(p.data?.theme)).filter(
      (t) => !extra.base.has(t) && ![...existing.values()].some((b) => b.base.has(t)),
    );
    expect(missing).toEqual([]);
  });

  it.each(ids)("%s defines every token, a plain background and a high-contrast override", (id) => {
    const vars = extra.base.get(id)!;
    for (const t of [...COLOUR_TOKENS, "--font-family", "--rem"]) expect(vars[t], `${id} ${t}`).toBeTruthy();
    expect(vars["--background"]).toMatch(/^(#[0-9a-f]{3,8}|rgba?\([^)]*\))$/i);
    expect(colorsIn(vars["--background"])[0][3], `${id} background alpha`).toBe(1);
    expect(extra.a11y.has(id), `${id} a11y block`).toBe(true);
  });

  it.each(ids)("%s passes contrast", (id) => {
    const vars = extra.base.get(id)!;
    const failures = [
      ...audit(id, vars, [...REQUIRED, ...ALSO], "normal"),
      ...audit(id, { ...vars, ...extra.a11y.get(id) }, HIGH_CONTRAST, "a11y"),
    ];
    expect(failures.map(fmt)).toEqual([]);
  });

  it.each(ids)("%s matches the dark flag on its palette item", (id) => {
    const item = PALETTES.find((p) => p.data?.theme === id);
    expect(item, `palette item for ${id}`).toBeTruthy();
    const bg = colorsIn(extra.base.get(id)!["--background"])[0];
    expect(luminance(bg) < 0.2, `${id} background luminance`).toBe(Boolean(item!.data?.dark));
  });
});

describe("original overlays (styles/themes/*/theme.css)", () => {
  it("reports required-contrast failures and gets no worse", () => {
    const failures: Failure[] = [];
    for (const blocks of existing.values()) {
      for (const [id, vars] of blocks.base) failures.push(...audit(id, vars, REQUIRED, "normal"));
    }
    if (failures.length) console.info(`Original palettes failing contrast:\n  ${failures.map(fmt).join("\n  ")}`);
    const unknown = failures.filter((f) => !KNOWN_EXISTING.includes(`${f.theme}: ${f.check}`));
    expect(unknown.map(fmt)).toEqual([]);
  });
});
