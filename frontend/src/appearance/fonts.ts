/**
 * Bundled fonts. Drop font files into frontend/fonts/<Family Name>/ and they
 * are registered under that family name; typography items refer to families
 * by name, so a missing font just falls back down the stack.
 *
 * Weight and style come from the file name, as Google Fonts names them:
 *   Inter-VariableFont_opsz,wght.ttf   → 100–900
 *   Inter-BoldItalic.ttf               → 700 italic
 *   PressStart2P-Regular.ttf           → 400
 * The runtime is offline, so fonts are never fetched from a CDN.
 */

const files = import.meta.glob<string>("../../fonts/*/*.{woff2,woff,ttf,otf}", {
  eager: true,
  query: "?url",
  import: "default",
});

const WEIGHTS: [RegExp, number][] = [
  [/extra-?light|ultra-?light/i, 200],
  [/semi-?bold|demi-?bold/i, 600],
  [/extra-?bold|ultra-?bold/i, 800],
  [/thin|hairline/i, 100],
  [/light/i, 300],
  [/medium/i, 500],
  [/black|heavy/i, 900],
  [/bold/i, 700],
];

export interface FontFile {
  family: string;
  url: string;
  weight: string;
  style: "normal" | "italic";
}

export function parseFontPath(path: string, url: string): FontFile {
  const parts = path.split("/");
  const family = parts[parts.length - 2];
  const name = parts[parts.length - 1].replace(/\.[a-z0-9]+$/i, "");
  const style = /italic/i.test(name) ? "italic" : "normal";
  let weight = "400";
  if (/variable|\[.*wght.*\]|_wght|,wght/i.test(name)) weight = "100 900";
  else {
    const hit = WEIGHTS.find(([re]) => re.test(name.replace(/italic/i, "")));
    if (hit) weight = String(hit[1]);
  }
  return { family, url, weight, style };
}

export function bundledFonts(): FontFile[] {
  return Object.entries(files).map(([path, url]) => parseFontPath(path, url));
}

let registered = false;

/** Register every bundled font with the document (loaded lazily on first use). */
export function registerFonts(): void {
  if (registered || typeof document === "undefined" || !("fonts" in document)) return;
  registered = true;
  for (const f of bundledFonts()) {
    try {
      const face = new FontFace(f.family, `url("${f.url}")`, { weight: f.weight, style: f.style, display: "swap" });
      document.fonts.add(face);
    } catch (e) {
      console.warn("font not registered", f.family, e);
    }
  }
}

/** Families present in frontend/fonts (for the Theme Lab's missing-font report). */
export function bundledFamilies(): Set<string> {
  return new Set(bundledFonts().map((f) => f.family));
}
