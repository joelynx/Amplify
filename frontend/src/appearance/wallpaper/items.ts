/**
 * Wallpaper items (slot "wallpaper"). Each id's suffix names a scene in
 * scenes/index.ts. Pack items may instead set `data.image` (and `data.night`
 * for 19:00–07:00) to show their own picture.
 */

import type { Item } from "../types";

type Spec = [id: string, name: string, description: string, extra?: Partial<Item>];

const SPECS: Spec[] = [
  ["none", "None", "No wallpaper: the palette's background."],
  ["clouds", "Pastel Clouds", "Soft clouds in a pastel sky.", { set: "pastel", swatch: ["var(--background)", "var(--primary)", "#ffffff"] }],
  ["aquarium", "Aquarium", "Glossy water, light caustics, bubbles and a few fish.", { set: "frutiger-aero", swatch: ["#bfeefa", "#22a6c9", "#ff8a3d"] }],
  ["pixel-clouds", "Pixel Sky", "Chunky pixel clouds and stars.", { set: "pixel-art", swatch: ["var(--background)", "var(--accent)", "#ffffff"] }],
  ["hills", "Rolling Hills", "Green hills under a blue sky with soft clouds.", { set: "windows-xp", swatch: ["#2a6fdb", "#bfe4ff", "#5fbf47"] }],
  ["burst", "Comic Burst", "Radiating speed lines over halftone dots.", { set: "comic", swatch: ["var(--accent)", "var(--primary)", "var(--text)"] }],
  ["glyph-rain", "Glyph Rain", "Columns of maths symbols.", { set: "ascii", swatch: ["var(--background)", "var(--primary)"] }],
  ["leaves", "Falling Leaves", "Scattered autumn leaves.", { set: "sage", swatch: ["var(--success)", "#c96a28", "#d4a017"] }],
  ["embers", "Embers", "Embers over a warm vignette.", { set: "ember", swatch: ["#2a0a00", "#ff9a3c", "#ffd36b"] }],
  ["night-sky", "Night Sky", "Stars and a milky band.", { set: "midnight", swatch: ["#070b1f", "var(--secondary)", "#ffffff"] }],
  ["chalk-dust", "Chalk Dust", "Dust motes over a well-erased board.", { set: "blackboard", swatch: ["var(--background)", "var(--text)"] }],
  ["synth-grid", "Synth Grid", "A striped sunset over a neon grid.", { set: "synthwave", swatch: ["#12002a", "var(--primary)", "var(--secondary)"] }],
  ["rain", "Rainy Window", "Rain streaks and droplets on the glass.", { set: "lofi-cafe", swatch: ["#5b6b7d", "var(--background)", "#ffffff"] }],
  ["dunes", "Desert Night", "Dunes under an indigo sky, a crescent moon and lanterns.", { set: "desert-night", swatch: ["#141043", "#6a3f7e", "#ffcf7a"] }],
  ["petals", "Sakura Petals", "Scattered cherry-blossom petals.", { set: "sakura", swatch: ["#f8b7cd", "#ffd3e0", "var(--background)"] }],
];

export const ITEMS: Item[] = SPECS.map(([id, name, description, extra]) => ({
  id: `wallpaper.${id}`,
  slot: "wallpaper",
  name,
  description,
  tags: id === "none" ? [] : ["static"],
  ...extra,
}));
