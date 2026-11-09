/**
 * WCAG contrast helpers for the palette editor and the Theme Lab.
 * Colours are read from computed CSS values (hex or rgb()/rgba()).
 */

export function parseColor(value: string): [number, number, number] | null {
  const v = value.trim();
  const hex = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(v);
  if (hex) {
    const h = hex[1].length === 3 ? hex[1].split("").map((c) => c + c).join("") : hex[1];
    return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16)) as [number, number, number];
  }
  const rgb = /^rgba?\(\s*([\d.]+)[ ,]+([\d.]+)[ ,]+([\d.]+)/i.exec(v);
  if (rgb) return [Number(rgb[1]), Number(rgb[2]), Number(rgb[3])];
  return null;
}

function luminance([r, g, b]: [number, number, number]): number {
  const f = (c: number) => {
    const s = c / 255;
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
}

/** Contrast ratio 1–21, or null if either colour can't be parsed (e.g. a gradient). */
export function contrast(a: string, b: string): number | null {
  const ca = parseColor(a);
  const cb = parseColor(b);
  if (!ca || !cb) return null;
  const [hi, lo] = [luminance(ca), luminance(cb)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

export interface ContrastCheck {
  label: string;
  fg: string;
  bg: string;
  min: number;
  ratio: number | null;
}

/** The pairs every palette must pass, read from an element's computed tokens. */
export function paletteChecks(el: Element = document.documentElement): ContrastCheck[] {
  const cs = getComputedStyle(el);
  const t = (k: string) => cs.getPropertyValue(k).trim();
  const pairs: [string, string, string, number][] = [
    ["Text on background", t("--text"), t("--background"), 4.5],
    ["Text on surface", t("--text"), t("--surface"), 4.5],
    ["Muted on background", t("--muted"), t("--background"), 4.5],
    ["Button text on primary", t("--on-primary") || "#ffffff", t("--primary"), 3],
    ["Error on background", t("--error"), t("--background"), 3],
    ["Success on background", t("--success"), t("--background"), 3],
  ];
  return pairs.map(([label, fg, bg, min]) => ({ label, fg, bg, min, ratio: contrast(fg, bg) }));
}
