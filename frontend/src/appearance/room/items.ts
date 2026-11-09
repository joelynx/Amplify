/**
 * Room themes for the Home study room (slot "room"). Each re-skins the same
 * clickable objects. `data.base` names the built-in renderer; a drop-in pack
 * can reuse one and add `data.backdrop` (a wall picture, "./wall.png").
 */

import type { Item } from "../types";

export const ITEMS: Item[] = [
  {
    id: "room.study",
    slot: "room",
    name: "Study",
    description: "A warm wooden study: desk lamp, rug, curtains and a wall clock that keeps real time.",
    unlock: "starter",
    tags: ["cozy"],
    swatch: ["#8b5a34", "#e7d2ac", "#c9a86a", "#7a2f2f"],
    data: { base: "room.study" },
  },
  {
    id: "room.library",
    slot: "room",
    name: "Library",
    description: "Tall shelves with a rolling ladder, a card catalogue, a banker's lamp and a leather reading chair.",
    set: "dark-academia",
    unlock: "starter",
    tags: ["cozy", "academia"],
    swatch: ["#2f4a3a", "#5a3420", "#c9a24a", "#6b1f2a"],
    data: { base: "room.library" },
  },
  {
    id: "room.observatory",
    slot: "room",
    name: "Observatory",
    description: "A dome with its slit open to the sky, a refractor on its mount, star charts and an orrery.",
    set: "midnight",
    unlock: "starter",
    tags: ["night", "space"],
    swatch: ["#1c2444", "#e8e2d0", "#c9a24a", "#111a43"],
    data: { base: "room.observatory" },
  },
  {
    id: "room.pixel-cabin",
    slot: "room",
    name: "Pixel Cabin",
    description: "A log cabin in crisp pixels: gingham curtains, a lantern, a sleeping cat.",
    set: "pixel-art",
    unlock: "starter",
    tags: ["pixel", "retro"],
    swatch: ["#8b5a33", "#5c3a22", "#f2c14e", "#c0392b"],
    data: { base: "room.pixel-cabin" },
  },
  {
    id: "room.desktop",
    slot: "room",
    name: "Desktop 2001",
    description: "Your room as an early-2000s desktop: icons, a bookshelf window, a sticky note and a taskbar over rolling hills.",
    set: "windows-xp",
    unlock: "starter",
    tags: ["retro"],
    swatch: ["#4c9de6", "#5cae3c", "#2563eb", "#fde68a"],
    data: { base: "room.desktop" },
  },
  {
    id: "room.greenhouse",
    slot: "room",
    name: "Greenhouse",
    description: "A wall of glass panes, hanging plants, a potting bench and a watering can.",
    set: "sage",
    unlock: "starter",
    tags: ["nature"],
    swatch: ["#dfeee6", "#5aa83c", "#c47a55", "#a77b4f"],
    data: { base: "room.greenhouse" },
  },
  {
    id: "room.dorm",
    slot: "room",
    name: "Dorm",
    description: "Fairy lights, maths posters, a bed in the corner and a beanbag.",
    set: "pastel",
    unlock: "starter",
    tags: ["cozy"],
    swatch: ["#dfe6f3", "#d8b98a", "#ff9ecb", "#8d8aa6"],
    data: { base: "room.dorm" },
  },
];
