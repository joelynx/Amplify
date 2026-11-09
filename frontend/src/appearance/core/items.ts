/**
 * Built-in items for the CSS-driven slots: palette, typography, chrome,
 * motion, surface, paper, cursor, icons, logo and loader.
 *
 * Palettes are the `:root[data-theme]` overlays in styles/themes/<id>/.
 * Chrome, motion, surface, paper and cursor are styles/appearance/*.css,
 * keyed on <html data-chrome|data-motion|…> (apply.ts). Typography sets the
 * font variables; fonts themselves are bundled from frontend/fonts/ (fonts.ts).
 */

import type { Item } from "../types";

type Spec = [id: string, name: string, description: string, extra?: Partial<Item>];

function make(slot: Item["slot"], specs: Spec[]): Item[] {
  return specs.map(([id, name, description, extra]) => ({ id: `${slot}.${id}`, slot, name, description, ...extra }));
}

const pal = (theme: string, dark = false, extra: Partial<Item> = {}): Partial<Item> => ({
  data: { theme, dark },
  ...extra,
});

export const PALETTES: Item[] = make("palette", [
  ["default-light", "Amplify Light", "Neutral light, WCAG AA.", pal("default-light")],
  ["default-dark", "Amplify Dark", "Neutral dark, WCAG AA.", pal("default-dark", true)],
  ["pastel", "Pastel", "Soft pink and lilac.", pal("pastel")],
  ["frutiger-aero", "Frutiger Aero", "Sky blue and glass.", pal("frutiger-aero")],
  ["pixel-art", "Pixel Art", "Night blue with arcade yellow.", pal("pixel-art", true)],
  ["windows-xp", "Windows XP", "Early-2000s beige and blue.", pal("windows-xp")],
  ["comic", "Comic", "Newsprint cream, ink, red.", pal("comic")],
  ["ascii", "Terminal Green", "Phosphor green on black.", pal("ascii", true)],
  ["android-kitkat", "KitKat", "Material teal.", pal("android-kitkat")],
  ["sage", "Sage", "Green-grey botanical.", pal("sage", false, { unlock: "milestone:spaced_reviews" })],
  ["ember", "Ember", "Warm paper and deep orange.", pal("ember", false, { unlock: "milestone:comebacks" })],
  ["midnight", "Midnight", "Navy with violet.", pal("midnight", true, { unlock: "milestone:honest_attempts" })],
  ["blackboard", "Blackboard", "Slate green and chalk.", pal("blackboard", true)],
  ["blueprint", "Blueprint", "White on drafting blue.", pal("blueprint", true)],
  ["engineer", "Engineer's Notebook", "Pale green engineering paper.", pal("engineer")],
  ["manuscript", "Manuscript", "Parchment with gilt and lapis.", pal("manuscript")],
  ["dark-academia", "Dark Academia", "Leather brown and brass.", pal("dark-academia", true)],
  ["synthwave", "Synthwave", "Magenta and cyan on purple night.", pal("synthwave", true)],
  ["vaporwave", "Vaporwave", "Pink, teal and marble.", pal("vaporwave", false, { unlock: "secret:vaporwave" })],
  ["handheld", "Handheld", "Four shades of LCD green.", pal("handheld")],
  ["amber-crt", "Amber CRT", "Amber phosphor on black.", pal("amber-crt", true)],
  ["dracula", "Dracula", "The editor palette (MIT).", pal("dracula", true, { credits: [{ what: "palette", who: "Dracula Theme", license: "MIT", url: "https://draculatheme.com" }] })],
  ["nord", "Nord", "Arctic blue-greys (MIT).", pal("nord", true, { credits: [{ what: "palette", who: "Arctic Ice Studio", license: "MIT", url: "https://www.nordtheme.com" }] })],
  ["catppuccin", "Catppuccin Mocha", "Soft pastel dark (MIT).", pal("catppuccin", true, { credits: [{ what: "palette", who: "Catppuccin", license: "MIT", url: "https://catppuccin.com" }] })],
  ["catppuccin-latte", "Catppuccin Latte", "Soft pastel light (MIT).", pal("catppuccin-latte", false, { credits: [{ what: "palette", who: "Catppuccin", license: "MIT", url: "https://catppuccin.com" }] })],
  ["gruvbox", "Gruvbox", "Retro warm dark (MIT).", pal("gruvbox", true, { credits: [{ what: "palette", who: "Pavel Pertsev", license: "MIT", url: "https://github.com/morhetz/gruvbox" }] })],
  ["solarized", "Solarized Light", "Ethan Schoonover's light palette (MIT).", pal("solarized", false, { credits: [{ what: "palette", who: "Ethan Schoonover", license: "MIT", url: "https://ethanschoonover.com/solarized/" }] })],
  ["tokyo-night", "Tokyo Night", "Neon city dark (MIT).", pal("tokyo-night", true, { credits: [{ what: "palette", who: "enkia", license: "MIT", url: "https://github.com/enkia/tokyo-night-vscode-theme" }] })],
  ["lofi-cafe", "Lo-fi Café", "Coffee and dusk.", pal("lofi-cafe", true)],
  ["desert-night", "Desert Night", "Indigo sky over sand.", pal("desert-night", true)],
  ["sakura", "Sakura", "Blossom pink on rice paper.", pal("sakura")],
  ["bauhaus", "Bauhaus", "Primary red, yellow, blue.", pal("bauhaus")],
  ["brutalist", "Brutalist", "Black, white, one loud accent.", pal("brutalist")],
  ["club", "Club", "Mathematics Club red, Coding Club yellow.", pal("club")],
]);

const type = (body: string, heading?: string, mono?: string, extra: Partial<Item> = {}): Partial<Item> => ({
  data: { body, heading: heading ?? body, mono: mono ?? '"JetBrains Mono", "Cascadia Mono", Consolas, monospace' },
  ...extra,
});

export const TYPOGRAPHY: Item[] = make("typography", [
  ["system", "System", "Whatever Windows provides.", type('system-ui, "Segoe UI", sans-serif')],
  ["inter", "Inter", "The house sans.", type('"Inter", system-ui, "Segoe UI", sans-serif')],
  ["rounded", "Rounded", "Nunito with Quicksand headings.", type('"Nunito", "Segoe UI", sans-serif', '"Quicksand", "Nunito", sans-serif')],
  ["aero", "Aero", "Nunito Sans; Segoe UI as a fallback.", type('"Nunito Sans", "Segoe UI", sans-serif')],
  ["pixel", "Pixel", "Pixelify Sans, Press Start 2P headings.", type('"Pixelify Sans", "VT323", ui-monospace, monospace', '"Press Start 2P", "Pixelify Sans", monospace', '"VT323", ui-monospace, monospace')],
  ["xp", "Desktop 2001", "Tahoma, as installed on Windows.", type('Tahoma, Verdana, "Segoe UI", sans-serif')],
  ["comic", "Comic", "Comic Neue with Bangers headings.", type('"Comic Neue", "Comic Sans MS", "Patrick Hand", cursive', '"Bangers", "Comic Neue", cursive')],
  ["terminal", "Terminal", "IBM Plex Mono with VT323 headings.", type('"IBM Plex Mono", "Cascadia Mono", Consolas, monospace', '"VT323", "IBM Plex Mono", monospace', '"IBM Plex Mono", Consolas, monospace')],
  ["kitkat", "Roboto", "Early-mobile Roboto.", type('"Roboto", "Segoe UI", sans-serif')],
  ["botanical", "Botanical", "Source Serif 4 with Fraunces headings.", type('"Source Serif 4", Georgia, serif', '"Fraunces", "Source Serif 4", Georgia, serif')],
  ["oldstyle", "Old Style", "Crimson Pro with EB Garamond headings.", type('"Crimson Pro", Georgia, serif', '"EB Garamond", "Crimson Pro", Georgia, serif')],
  ["grotesk", "Grotesk", "Space Grotesk.", type('"Space Grotesk", "Inter", "Segoe UI", sans-serif')],
  ["chalk", "Chalk", "Patrick Hand with Cabin Sketch headings.", type('"Patrick Hand", "Segoe Print", cursive', '"Cabin Sketch", "Patrick Hand", cursive')],
  ["technical", "Technical", "IBM Plex Sans with Architects Daughter headings.", type('"IBM Plex Sans", "Segoe UI", sans-serif', '"Architects Daughter", "IBM Plex Sans", sans-serif')],
  ["code", "Code", "JetBrains Mono everywhere.", type('"JetBrains Mono", "Cascadia Mono", Consolas, monospace')],
  ["geometric", "Geometric", "Jost, a Futura-like sans.", type('"Jost", "Century Gothic", "Segoe UI", sans-serif')],
  ["typewriter", "Typewriter", "Courier Prime, close to the logo's LaTeX typewriter face.", type('"Courier Prime", "CMU Typewriter Text", "Courier New", monospace', '"CMU Typewriter Text", "Courier Prime", "Courier New", monospace')],
]);

export const CHROME: Item[] = make("chrome", [
  ["default", "Clean", "Soft rounded cards with a light shadow."],
  ["flat", "Flat", "No shadows, hairline borders."],
  ["soft", "Pillowy", "Big radii, washi-tape corners on cards, bouncy buttons."],
  ["glass", "Glass", "Frosted cards, glossy pill buttons and progress bars."],
  ["pixel", "Pixel", "Stepped corners, hard drop shadows, HP-bar progress."],
  ["bevel", "Bevel", "Early-2000s bevels with a title bar on every card."],
  ["ink", "Ink", "Heavy ink borders, offset shadows, pill buttons."],
  ["terminal", "Box drawing", "No rounding, thin lines, [ titled ] cards."],
  ["material", "Material", "Flat cards with 1–2dp elevation, uppercase buttons."],
  ["paper", "Paper", "Cards like paper sheets: warm edge shadow, deckled top."],
  ["brutal", "Brutalist", "Thick black borders and hard offset shadows."],
  ["neon", "Neon", "Glowing borders on dark glass."],
  ["chalk", "Chalk", "Rough, hand-drawn borders."],
]);

export const MOTION: Item[] = make("motion", [
  ["default", "Smooth", "Short fades and slides."],
  ["springy", "Springy", "Overshooting springs."],
  ["stepped", "Stepped", "Frame-stepped, like sprites."],
  ["glassy", "Glassy", "Slow, soft fades."],
  ["typewriter", "Typewriter", "Headings type themselves in."],
  ["snappy", "Snappy", "Quick pops."],
  ["none", "None", "No transitions at all."],
]);

export const SURFACES: Item[] = make("surface", [
  ["none", "None", "Plain background."],
  ["graph", "Graph paper", "5 mm squares."],
  ["dots", "Dot grid", "Bullet-journal dots."],
  ["ruled", "Ruled", "Notebook lines with a red margin."],
  ["engineering", "Engineering", "Green engineering paper."],
  ["slate", "Slate", "Blackboard texture."],
  ["parchment", "Parchment", "Mottled parchment."],
  ["blueprint", "Blueprint grid", "Fine and coarse white grid."],
  ["scanlines", "Scanlines", "CRT lines."],
  ["halftone", "Halftone", "Comic print dots."],
  ["linen", "Linen", "Woven paper."],
  ["grain", "Grain", "Fine film grain."],
  ["cork", "Cork", "A cork board."],
]);

export const PAPERS: Item[] = make("paper", [
  ["plain", "Plain", "The theme's surface colour."],
  ["notebook", "Notebook", "Ruled lines and a margin."],
  ["graph", "Graph", "Squared paper."],
  ["blackboard", "Blackboard", "Slate with chalk-coloured maths."],
  ["parchment", "Parchment", "Warm parchment with brown ink."],
  ["index", "Index card", "A ruled index card with a red top line."],
  ["terminal", "Terminal", "Black with phosphor maths."],
  ["blueprint", "Blueprint", "White line work on blue."],
  ["engineering", "Engineering", "Pale green squares."],
]);

export const CURSORS: Item[] = make("cursor", [
  ["system", "System", "The Windows pointer."],
  ["chalk", "Chalk", "A stick of chalk."],
  ["pixel", "Pixel", "A pixel arrow."],
  ["quill", "Quill", "A feather quill."],
  ["glove", "Glove", "A cartoon pointing glove."],
  ["block", "Block", "A terminal block caret for text."],
  ["heart", "Heart", "A little heart."],
  ["crosshair", "Crosshair", "A drafting crosshair."],
]);

export const ICON_SETS: Item[] = make("icons", [
  ["lucide", "Line icons", "The default outline icons."],
  ["pixel", "Pixel", "Square-capped, crisp-edged icons."],
  ["terminal", "Text glyphs", "Icons as ASCII glyphs: [#], $_, <>."],
]);

export const LOGOS: Item[] = make("logo", [
  ["auto", "Match the theme", "Picks the logo variant that suits the palette."],
  ["original", "Original", "The club colours as designed."],
  ["tinted", "Theme-tinted", "The reds become the theme's primary colour."],
  ["mono", "One ink", "The text colour only."],
  ["pixel", "Pixel", "Rasterized, hard-edged."],
  ["terminal", "Terminal", "Text art."],
  ["comic", "Comic", "Inked, with an offset shadow."],
  ["glossy", "Glossy", "Glass gradients."],
  ["chalk", "Chalk", "Chalk on slate."],
  ["neon", "Neon", "Glowing tubes."],
  ["blueprint", "Blueprint", "Outlines only."],
]);

export const LOADERS: Item[] = make("loader", [
  ["classic", "Diagonal sweep", "amp → li → φ light up in turn.", { data: { big: "sweep" } }],
  ["elimination", "Row-reduce", "The off-diagonal variables are eliminated row by row.", { data: { big: "reduce" } }],
]);

export const ITEMS: Item[] = [
  ...PALETTES,
  ...TYPOGRAPHY,
  ...CHROME,
  ...MOTION,
  ...SURFACES,
  ...PAPERS,
  ...CURSORS,
  ...ICON_SETS,
  ...LOGOS,
  ...LOADERS,
];
