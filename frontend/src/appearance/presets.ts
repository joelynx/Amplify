/**
 * Presets: curated loadouts (Makeover.md §7–8). The first twelve keep the ids
 * of the original themes, so configs.THEME_SELECTED and the backend's reward
 * locks keep working. Slots a preset leaves out use the slot default.
 *
 * Item ids that no module provides yet simply fall back to the default, so a
 * preset can name items before their assets exist.
 */

import type { Preset } from "./types";

export const PRESETS: Preset[] = [
  {
    id: "default-light",
    name: "Amplify Light",
    description: "The house style: clean, quiet, club colours in the logo.",
    slots: {
      palette: "palette.default-light", typography: "typography.inter", chrome: "chrome.default", motion: "motion.default",
      sfx: "sfx.soft", results: "results.report",
      room: "room.study", loader: "loader.classic",
    },
  },
  {
    id: "default-dark",
    name: "Amplify Dark",
    description: "The house style on dark surfaces.",
    slots: {
      palette: "palette.default-dark", typography: "typography.inter", chrome: "chrome.default", motion: "motion.default",
      sfx: "sfx.soft", results: "results.report",
      room: "room.study", loader: "loader.classic",
    },
  },
  {
    id: "pastel",
    name: "Pastel",
    description: "Kawaii stationery: washi tape, stickers, soft marimba.",
    slots: {
      palette: "palette.pastel", typography: "typography.rounded", chrome: "chrome.soft", motion: "motion.springy",
      surface: "surface.dots", wallpaper: "wallpaper.clouds", paper: "paper.notebook", cursor: "cursor.heart",
      sfx: "sfx.marimba",
      results: "results.sticker", room: "room.dorm", charts: "charts.pastel",
    },
  },
  {
    id: "frutiger-aero",
    name: "Frutiger Aero",
    description: "Glossy optimism: sky, water, bubbles, glass chimes.",
    slots: {
      palette: "palette.frutiger-aero", typography: "typography.system", chrome: "chrome.glass", motion: "motion.glassy",
      wallpaper: "wallpaper.aquarium", logo: "logo.glossy", sfx: "sfx.glass",
      results: "results.report",
      room: "room.greenhouse", charts: "charts.glossy",
    },
  },
  {
    id: "pixel-art",
    name: "Pixel Art",
    description: "16-bit adventure: chunky borders, chiptune, an overworld map.",
    slots: {
      palette: "palette.pixel-art", typography: "typography.pixel", chrome: "chrome.pixel", motion: "motion.stepped",
      wallpaper: "wallpaper.pixel-clouds", icons: "icons.pixel", cursor: "cursor.pixel", logo: "logo.pixel",
      sfx: "sfx.chiptune",
      results: "results.jrpg", room: "room.pixel-cabin",
      arena: "arena.arcade", charts: "charts.pixel",
    },
  },
  {
    id: "windows-xp",
    name: "Windows XP",
    description: "Early-2000s desktop: rolling hills, beveled title bars, tray balloons.",
    slots: {
      palette: "palette.windows-xp", typography: "typography.xp", chrome: "chrome.bevel", motion: "motion.default",
      wallpaper: "wallpaper.hills", cursor: "cursor.system", sfx: "sfx.desktop",
      results: "results.dialog",
      room: "room.desktop", charts: "charts.default",
    },
  },
  {
    id: "comic",
    name: "Comic",
    description: "Saturday-morning ink: halftone, speech bubbles, KA-POW.",
    slots: {
      palette: "palette.comic", typography: "typography.comic", chrome: "chrome.ink", motion: "motion.snappy",
      surface: "surface.halftone", wallpaper: "wallpaper.burst", cursor: "cursor.glove", logo: "logo.comic",
      sfx: "sfx.pop", results: "results.newspaper",
      room: "room.study", charts: "charts.hand-drawn",
    },
  },
  {
    id: "ascii",
    name: "ASCII",
    description: "Terminal: phosphor green, box drawing, keyboard clicks.",
    slots: {
      palette: "palette.ascii", typography: "typography.terminal", chrome: "chrome.terminal", motion: "motion.typewriter",
      surface: "surface.scanlines", wallpaper: "wallpaper.glyph-rain", icons: "icons.terminal", cursor: "cursor.block",
      logo: "logo.terminal", loader: "loader.elimination", sfx: "sfx.keys",
      results: "results.terminal",
      paper: "paper.terminal", arena: "arena.terminal", charts: "charts.phosphor",
    },
  },
  {
    id: "android-kitkat",
    name: "Android KitKat",
    description: "Early mobile: flat cards, toasts, a notification shade for reviews.",
    slots: {
      palette: "palette.android-kitkat", typography: "typography.inter", chrome: "chrome.material", motion: "motion.default",
      sfx: "sfx.material", results: "results.report",
      room: "room.study", charts: "charts.default",
    },
  },
  {
    id: "sage",
    name: "Sage",
    description: "Botanical study journal. Earned with spaced reviews.",
    reward: true,
    slots: {
      palette: "palette.sage", typography: "typography.botanical", chrome: "chrome.paper", motion: "motion.default",
      surface: "surface.linen", wallpaper: "wallpaper.leaves", paper: "paper.notebook", sfx: "sfx.paper",
      results: "results.report", room: "room.greenhouse", charts: "charts.garden",
    },
  },
  {
    id: "ember",
    name: "Ember",
    description: "Candlelit comeback. Earned by fixing old mistakes.",
    reward: true,
    slots: {
      palette: "palette.ember", typography: "typography.oldstyle", chrome: "chrome.paper", motion: "motion.default",
      surface: "surface.grain", wallpaper: "wallpaper.embers", paper: "paper.parchment", cursor: "cursor.quill",
      logo: "logo.tinted", sfx: "sfx.warm",
      results: "results.newspaper",
      room: "room.library", charts: "charts.default",
    },
  },
  {
    id: "midnight",
    name: "Midnight",
    description: "An observatory under the stars. Earned with honest attempts.",
    reward: true,
    slots: {
      palette: "palette.midnight", typography: "typography.grotesk", chrome: "chrome.neon", motion: "motion.glassy",
      wallpaper: "wallpaper.night-sky", logo: "logo.neon", sfx: "sfx.chimes",
      results: "results.report",
      room: "room.observatory", charts: "charts.night-sky",
    },
  },
  /* ---------------- new presets (Makeover.md §8) ---------------- */
  {
    id: "blackboard",
    name: "Blackboard",
    description: "Slate, chalk dust and eraser swipes.",
    slots: {
      palette: "palette.blackboard", typography: "typography.chalk", chrome: "chrome.chalk", motion: "motion.default",
      surface: "surface.slate", wallpaper: "wallpaper.chalk-dust", paper: "paper.blackboard", cursor: "cursor.chalk",
      logo: "logo.chalk", loader: "loader.elimination", sfx: "sfx.paper",
      arena: "arena.chalkboard", charts: "charts.hand-drawn",
    },
  },
  {
    id: "blueprint",
    name: "Blueprint",
    description: "White line work on blue, dimension-line dividers.",
    slots: {
      palette: "palette.blueprint", typography: "typography.technical", chrome: "chrome.flat", surface: "surface.blueprint",
      paper: "paper.blueprint", logo: "logo.blueprint", cursor: "cursor.crosshair", sfx: "sfx.soft",
      charts: "charts.default",
    },
  },
  {
    id: "engineer",
    name: "Engineer's Notebook",
    description: "Green engineering paper and a technical pen.",
    slots: {
      palette: "palette.engineer", typography: "typography.technical", chrome: "chrome.flat", surface: "surface.engineering",
      paper: "paper.engineering", sfx: "sfx.paper", charts: "charts.hand-drawn",
    },
  },
  {
    id: "manuscript",
    name: "Illuminated Manuscript",
    description: "Parchment, drop caps and gilded ornaments, as in Euclid's Elements.",
    slots: {
      palette: "palette.manuscript", typography: "typography.oldstyle", chrome: "chrome.paper", surface: "surface.parchment",
      paper: "paper.parchment", logo: "logo.mono", cursor: "cursor.quill", sfx: "sfx.paper",
      results: "results.scroll", room: "room.library",
    },
  },
  {
    id: "dark-academia",
    name: "Dark Academia",
    description: "Leather, brass and a quiet library.",
    slots: {
      palette: "palette.dark-academia", typography: "typography.oldstyle", chrome: "chrome.paper", surface: "surface.grain",
      logo: "logo.tinted", cursor: "cursor.quill", sfx: "sfx.warm",
      room: "room.library",
    },
  },
  {
    id: "synthwave",
    name: "Synthwave",
    description: "Neon grid sunset, chrome type.",
    slots: {
      palette: "palette.synthwave", typography: "typography.grotesk", chrome: "chrome.neon", motion: "motion.glassy",
      wallpaper: "wallpaper.synth-grid", logo: "logo.neon", sfx: "sfx.chimes",
      charts: "charts.night-sky",
    },
  },
  {
    id: "vaporwave",
    name: "Vaporwave",
    description: "A E S T H E T I C. Found, not given.",
    secret: "vaporwave",
    slots: {
      palette: "palette.vaporwave", typography: "typography.grotesk", chrome: "chrome.bevel", motion: "motion.glassy",
      wallpaper: "wallpaper.synth-grid", logo: "logo.neon", sfx: "sfx.glass",
      results: "results.dialog",
    },
  },
  {
    id: "handheld",
    name: "Handheld",
    description: "Four shades of green on a dot-matrix screen.",
    slots: {
      palette: "palette.handheld", typography: "typography.pixel", chrome: "chrome.pixel", motion: "motion.stepped",
      icons: "icons.pixel", cursor: "cursor.pixel", logo: "logo.pixel", sfx: "sfx.chiptune",
      results: "results.jrpg", arena: "arena.arcade",
      charts: "charts.pixel",
    },
  },
  {
    id: "amber-crt",
    name: "Amber CRT",
    description: "A monochrome amber terminal.",
    slots: {
      palette: "palette.amber-crt", typography: "typography.terminal", chrome: "chrome.terminal", motion: "motion.typewriter",
      surface: "surface.scanlines", icons: "icons.terminal", cursor: "cursor.block", logo: "logo.terminal",
      sfx: "sfx.keys",
      results: "results.terminal", paper: "paper.terminal", arena: "arena.terminal", charts: "charts.phosphor",
    },
  },
  {
    id: "code-editor",
    name: "Code Editor",
    description: "Dracula colours, a monospace UI and line numbers. Pick another editor palette in the Wardrobe.",
    slots: {
      palette: "palette.dracula", typography: "typography.code", chrome: "chrome.flat", motion: "motion.default",
      icons: "icons.lucide", sfx: "sfx.keys",
      results: "results.terminal", charts: "charts.default",
    },
  },
  {
    id: "lofi-cafe",
    name: "Lo-fi Café",
    description: "A rainy window and a warm mug.",
    slots: {
      palette: "palette.lofi-cafe", typography: "typography.rounded", chrome: "chrome.soft", motion: "motion.glassy",
      wallpaper: "wallpaper.rain", sfx: "sfx.marimba",
      room: "room.dorm",
    },
  },
  {
    id: "desert-night",
    name: "Desert Night",
    description: "Dunes, stars and lanterns, for the Abu Dhabi campus.",
    slots: {
      palette: "palette.desert-night", typography: "typography.grotesk", chrome: "chrome.default", motion: "motion.glassy",
      wallpaper: "wallpaper.dunes", sfx: "sfx.chimes",
      room: "room.observatory", charts: "charts.night-sky",
    },
  },
  {
    id: "sakura",
    name: "Sakura",
    description: "Spring petals on soft paper.",
    slots: {
      palette: "palette.sakura", typography: "typography.rounded", chrome: "chrome.soft", motion: "motion.springy",
      wallpaper: "wallpaper.petals", sfx: "sfx.marimba",
      charts: "charts.garden",
    },
  },
  {
    id: "bauhaus",
    name: "Bauhaus",
    description: "Primary shapes on a strict grid.",
    slots: {
      palette: "palette.bauhaus", typography: "typography.geometric", chrome: "chrome.brutal", motion: "motion.snappy",
      surface: "surface.none", sfx: "sfx.pop",
    },
  },
  {
    id: "brutalist",
    name: "Brutalist",
    description: "Raw borders, system mono, no rounding.",
    slots: {
      palette: "palette.brutalist", typography: "typography.code", chrome: "chrome.brutal", motion: "motion.none",
      sfx: "sfx.keys", results: "results.terminal",
    },
  },
  {
    id: "club",
    name: "Club Edition",
    description: "Mathematics Club red and Coding Club yellow.",
    slots: {
      palette: "palette.club", typography: "typography.code", chrome: "chrome.default", motion: "motion.default",
      logo: "logo.original", loader: "loader.elimination", sfx: "sfx.soft",
      room: "room.study",
    },
  },
];

const BY_ID = new Map(PRESETS.map((p) => [p.id, p]));

export function getPreset(id: string | null | undefined): Preset | undefined {
  return id ? BY_ID.get(id) : undefined;
}
