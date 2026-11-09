/**
 * Item registry. Every module that owns a slot exports `ITEMS: Item[]` from an
 * `items.ts` file anywhere under src/appearance/; they are collected here at
 * build time, so adding a module never means editing this file.
 *
 * Drop-in packs (Makeover.md §3.2): a folder under frontend/packs/<id>/ with an
 * item.json (same shape as Item) and its assets. Asset paths inside
 * `data` that start with "./" are rewritten to bundled URLs.
 */

import { SLOTS, type Item, type Loadout, type SlotId } from "./types";

const modules = import.meta.glob<{ ITEMS?: Item[] }>("./**/items.ts", { eager: true });
const packManifests = import.meta.glob<{ default: Item | Item[] }>("../../packs/*/item.json", { eager: true });
const packAssets = import.meta.glob<string>(
  "../../packs/*/**/*.{png,webp,jpg,jpeg,gif,svg,avif,ogg,mp3,wav,json,woff2,woff,ttf,otf,cur}",
  { eager: true, query: "?url", import: "default" },
);

/** Rewrite "./x.png" inside a pack's data to the bundled URL. */
function resolvePackData(dir: string, value: unknown): unknown {
  if (typeof value === "string" && value.startsWith("./")) {
    return packAssets[`${dir}/${value.slice(2)}`] ?? value;
  }
  if (Array.isArray(value)) return value.map((v) => resolvePackData(dir, v));
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, resolvePackData(dir, v)]));
  }
  return value;
}

function collect(): Item[] {
  const out: Item[] = [];
  for (const mod of Object.values(modules)) out.push(...(mod.ITEMS ?? []));
  for (const [path, mod] of Object.entries(packManifests)) {
    const dir = path.slice(0, path.lastIndexOf("/"));
    const list = Array.isArray(mod.default) ? mod.default : [mod.default];
    for (const item of list) {
      out.push({ ...item, tags: [...(item.tags ?? []), "pack"], data: resolvePackData(dir, item.data) as Item["data"] });
    }
  }
  return out;
}

const ALL: Item[] = collect();
const BY_ID = new Map(ALL.map((i) => [i.id, i]));

/** The item each slot falls back to when an id is unknown or missing. */
export const DEFAULT_LOADOUT: Loadout = {
  palette: "palette.default-light",
  typography: "typography.system",
  chrome: "chrome.default",
  motion: "motion.default",
  surface: "surface.none",
  wallpaper: "wallpaper.none",
  paper: "paper.plain",
  icons: "icons.lucide",
  cursor: "cursor.system",
  logo: "logo.auto",
  loader: "loader.classic",
  sfx: "sfx.soft",
  results: "results.report",
  room: "room.study",
  arena: "arena.default",
  charts: "charts.default",
};

export function allItems(): readonly Item[] {
  return ALL;
}

export function itemsFor(slot: SlotId): Item[] {
  return ALL.filter((i) => i.slot === slot);
}

export function getItem(id: string | undefined): Item | undefined {
  return id ? BY_ID.get(id) : undefined;
}

/** The item for a slot in a loadout, falling back to the slot default. */
export function resolve(loadout: Partial<Loadout>, slot: SlotId): Item | undefined {
  const it = getItem(loadout[slot]);
  return it && it.slot === slot ? it : getItem(DEFAULT_LOADOUT[slot]);
}

/** Fill gaps and drop unknown ids. */
export function normalizeLoadout(partial: Partial<Loadout> | undefined): Loadout {
  const out = { ...DEFAULT_LOADOUT };
  for (const slot of SLOTS) {
    const id = partial?.[slot];
    const it = getItem(id);
    if (it && it.slot === slot) out[slot] = it.id;
  }
  return out;
}
