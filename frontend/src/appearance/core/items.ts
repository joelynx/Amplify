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

const JETBRAINS = '"JetBrains Mono", "Cascadia Mono", Consolas, monospace';
const DM_MONO = '"DM Mono", "JetBrains Mono", Consolas, monospace';

/** `variation` sets font-variation-settings on the page (e.g. Recursive's Casual axis). */
const type = (body: string, heading?: string, mono?: string, extra: Partial<Item> = {}, variation?: string): Partial<Item> => ({
  data: { body, heading: heading ?? body, mono: mono ?? JETBRAINS, ...(variation ? { variation } : {}) },
  ...extra,
});

const ofl = (font: string, who: string, url: string) => ({ what: `${font} font`, who, license: "SIL OFL 1.1", url });

// Only fonts bundled in frontend/fonts (the owner's picks) and fonts Windows
// ships are named, so each description says what actually shows.
export const TYPOGRAPHY: Item[] = make("typography", [
  ["system", "System", "Whatever Windows provides (Segoe UI).", type('system-ui, "Segoe UI", sans-serif')],
  ["inter", "Inter", "The house sans.", type('"Inter", system-ui, "Segoe UI", sans-serif', undefined, undefined, { credits: [ofl("Inter", "Rasmus Andersson", "https://github.com/rsms/inter")] })],
  ["geometric", "Geometric", "Figtree, a friendly geometric sans.", type('"Figtree", "Segoe UI", sans-serif', undefined, DM_MONO, { credits: [ofl("Figtree", "Erik Kennedy", "https://github.com/erikdkennedy/figtree")] })],
  ["rubik", "Rubik", "Slightly rounded corners on every letter.", type('"Rubik", "Segoe UI", sans-serif', undefined, DM_MONO, { credits: [ofl("Rubik", "Hubert and Fischer", "https://github.com/googlefonts/rubik")] })],
  ["rounded", "Rounded", "Nunito: rounded ends on every stroke.", type('"Nunito", "Segoe UI", sans-serif', undefined, DM_MONO, {
    credits: [ofl("Nunito", "Vernon Adams", "https://github.com/googlefonts/nunito"), ofl("DM Mono", "Colophon Foundry", "https://github.com/googlefonts/dm-mono")],
  })],
  ["grotesk", "Grotesk", "Bricolage Grotesque: calm in text, quirkier in headings.", type('"Bricolage Grotesque", "Inter", "Segoe UI", sans-serif', undefined, undefined, { credits: [ofl("Bricolage Grotesque", "Mathieu Triay", "https://github.com/ateliertriay/bricolage")] })],
  ["recursive", "Recursive", "Recursive set half casual, for a light brush-drawn feel.", type('"Recursive", "Segoe UI", sans-serif', undefined, undefined, { credits: [ofl("Recursive", "Arrow Type", "https://github.com/arrowtype/recursive")] }, '"CASL" 0.5')],
  ["technical", "Technical", "Fira Sans, Mozilla's humanist sans.", type('"Fira Sans", "Segoe UI", sans-serif', undefined, undefined, { credits: [ofl("Fira Sans", "Carrois and Edenspiekermann for Mozilla", "https://fonts.google.com/specimen/Fira+Sans")] })],
  ["literata", "Literata", "A warm book face made for reading on screens.", type('"Literata", Georgia, serif', undefined, undefined, { credits: [ofl("Literata", "Veronika Burian and José Scaglione (TypeTogether)", "https://github.com/googlefonts/literata")] })],
  ["botanical", "Botanical", "Source Serif 4, a sturdy screen serif.", type('"Source Serif 4", Georgia, serif', undefined, undefined, { credits: [ofl("Source Serif 4", "Frank Grießhammer, Adobe", "https://github.com/adobe-fonts/source-serif")] })],
  ["oldstyle", "Old Style", "Alegreya with EB Garamond headings.", type('"Alegreya", Georgia, serif', '"EB Garamond", "Alegreya", Georgia, serif', undefined, {
    credits: [ofl("Alegreya", "Juan Pablo del Peral (Huerta Tipográfica)", "https://github.com/huertatipografica/Alegreya"), ofl("EB Garamond", "Georg Duffner and Octavio Pardo", "https://github.com/octaviopardo/EBGaramond12")],
  })],
  ["pixel", "Pixel", "Pixelify Sans, with VT323 for code.", type('"Pixelify Sans", "VT323", ui-monospace, monospace', undefined, '"VT323", ui-monospace, monospace', {
    credits: [ofl("Pixelify Sans", "Stefie Justprince", "https://github.com/eifetx/Pixelify-Sans"), ofl("VT323", "Peter Hull", "https://fonts.google.com/specimen/VT323")],
  })],
  ["xp", "Desktop 2001", "Tahoma, as installed on Windows.", type('Tahoma, Verdana, "Segoe UI", sans-serif')],
  ["comic", "Comic", "Comic Neue, a tidier Comic Sans.", type('"Comic Neue", "Comic Sans MS", cursive', undefined, undefined, { credits: [ofl("Comic Neue", "Craig Rozynski", "https://github.com/crozynski/comicneue")] })],
  ["terminal", "Terminal", "JetBrains Mono with VT323 headings.", type(JETBRAINS, '"VT323", "JetBrains Mono", monospace')],
  ["chalk", "Chalk", "Segoe Print, Windows' handwriting font.", type('"Segoe Print", "Comic Neue", cursive')],
  ["code", "Code", "JetBrains Mono everywhere.", type(JETBRAINS, undefined, undefined, { credits: [ofl("JetBrains Mono", "Philipp Nurullin and Konstantin Bulenkov (JetBrains)", "https://github.com/JetBrains/JetBrainsMono")] })],
  ["typewriter", "Typewriter", "Courier New, as installed on Windows.", type('"Courier New", "JetBrains Mono", monospace')],
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
