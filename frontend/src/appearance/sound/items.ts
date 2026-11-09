/**
 * Built-in sfx packs. All are procedural (recipes.ts). A drop-in pack can
 * add its own audio through `data.files` (cue name → file), with `data.base`
 * naming the built-in pack to fall back on.
 */

import type { Item } from "../types";

type Spec = [id: string, name: string, description: string, set?: string];

function make(slot: "sfx", specs: Spec[]): Item[] {
  return specs.map(([id, name, description, set]) => ({
    id: `${slot}.${id}`,
    slot,
    name,
    description,
    ...(set ? { set } : {}),
    tags: ["procedural"],
  }));
}

export const SFX_PACKS: Item[] = make("sfx", [
  ["soft", "Soft", "Gentle sine blips. Quiet and unobtrusive.", "default-light"],
  ["chiptune", "Chiptune", "Square and triangle bleeps with little arpeggio jingles.", "pixel-art"],
  ["glass", "Glass", "Bright glassy chimes and bubbles.", "frutiger-aero"],
  ["marimba", "Marimba", "Soft wooden mallet tones.", "pastel"],
  ["keys", "Keyboard", "Mechanical key clacks and a typewriter bell for right answers.", "ascii"],
  ["paper", "Pencil and paper", "Pencil scratches, page turns and chalk taps.", "sage"],
  ["pop", "Pop", "Comic whooshes, pops and boings.", "comic"],
  ["desktop", "Desktop 2001", "An original set of soft early-2000s synth pads and chimes.", "windows-xp"],
  ["material", "Taps", "Short, clean taps.", "android-kitkat"],
  ["chimes", "Celestial", "Night bells with a soft echo.", "midnight"],
  ["warm", "Hearth", "Woody thunks and warm, crackly tones.", "ember"],
]);

export const ITEMS: Item[] = SFX_PACKS;
