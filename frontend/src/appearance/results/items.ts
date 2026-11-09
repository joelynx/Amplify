/**
 * Results items (slot "results"): the session-end styles ResultsScreen can
 * draw. `data.style` names the renderer in ResultsScreen.RESULT_STYLES, so a
 * drop-in pack can reuse a renderer under a new name.
 */

import type { Item } from "../types";

type Spec = [id: string, name: string, description: string, set?: string];

const SPECS: Spec[] = [
  ["report", "Report card", "A clean report card: a headline number, a stacked bar and a tile per stat.", "default-light"],
  ["jrpg", "Victory window", "QUIZ CLEAR! The tally counts up like an EXP screen; the review queue is your loot.", "pixel-art"],
  ["arcade", "High score", "A cabinet scoreboard with rolling zero-padded scores and a blinking attract line."],
  ["newspaper", "Front page", "Tomorrow's paper today: a headline built from your numbers.", "comic"],
  ["terminal", "Session log", "A timestamped log that types itself out and ends in exit 0.", "ascii"],
  ["dialog", "Setup wizard", "An early-2000s dialog with a segmented progress bar and a Finish button.", "windows-xp"],
  ["sticker", "Sticker sheet", "Each number is a die-cut sticker: flowers, stars, hearts, clouds.", "pastel"],
  ["scroll", "Scroll", "A parchment scroll that unrolls, with a ledger and a Q.E.D. seal.", "manuscript"],
];

export const ITEMS: Item[] = SPECS.map(([id, name, description, set]) => ({
  id: `results.${id}`,
  slot: "results",
  name,
  description,
  set,
  data: { style: id },
}));
