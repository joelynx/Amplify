/**
 * Chart skins (Stats) and quiz arena skins. Both are CSS keyed on
 * <html data-charts|data-arena> (styles/appearance/places.css), plus the
 * heatmap's cell shape, which CalendarHeatmap reads from `data.cell`.
 */

import type { Item } from "../types";

export const ITEMS: Item[] = [
  { id: "charts.default", slot: "charts", name: "Clean", description: "Plain, readable charts.", data: { cell: "square" } },
  { id: "charts.night-sky", slot: "charts", name: "Night sky", description: "Heatmap days as stars; brighter with more activity.", data: { cell: "star" } },
  { id: "charts.garden", slot: "charts", name: "Garden", description: "Heatmap days as flowers that bloom with activity.", data: { cell: "flower" } },
  { id: "charts.pixel", slot: "charts", name: "Pixel", description: "Hard-edged pixel tiles and stepped lines.", data: { cell: "pixel" } },
  { id: "charts.hand-drawn", slot: "charts", name: "Hand-drawn", description: "Wobbly sketched lines and cells.", data: { cell: "sketch" } },
  { id: "charts.phosphor", slot: "charts", name: "Phosphor", description: "Glowing CRT lines.", data: { cell: "square" } },
  { id: "charts.glossy", slot: "charts", name: "Glossy", description: "Glass highlights on bars and cells.", data: { cell: "round" } },
  { id: "charts.pastel", slot: "charts", name: "Pastel", description: "Soft rounded cells.", data: { cell: "round" } },
  { id: "charts.contrib", slot: "charts", name: "Contribution graph", description: "Green squares, like a code-hosting site's activity graph.", data: { cell: "square", green: true } },
  { id: "arena.default", slot: "arena", name: "Clean", description: "The plain quiz layout." },
  { id: "arena.chalkboard", slot: "arena", name: "Chalkboard", description: "Questions on a slate in a wooden frame; answers in chalk." },
  { id: "arena.arcade", slot: "arena", name: "Arcade", description: "An arcade cabinet bezel and a pixel answer box." },
  { id: "arena.gameshow", slot: "arena", name: "Game show", description: "Spotlit stage panels and a big answer plate." },
  { id: "arena.questboard", slot: "arena", name: "Quest board", description: "Each question a notice pinned to a tavern board." },
  { id: "arena.terminal", slot: "arena", name: "Terminal", description: "A shell prompt for answers." },
];
