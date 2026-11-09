/**
 * Appearance model (Makeover.md §3).
 *
 * A *slot* is one swappable dimension (palette, chrome, sounds, room…).
 * An *item* fills one slot. A *loadout* picks one item per slot, and a
 * *preset* (what the Themes page used to call a theme) is a curated loadout.
 * Items are plain data; the module that owns a slot knows how to render them.
 */

export const SLOTS = [
  "palette",
  "typography",
  "chrome",
  "motion",
  "surface",
  "wallpaper",
  "paper",
  "icons",
  "cursor",
  "logo",
  "loader",
  "sfx",
  "results",
  "room",
  "arena",
  "charts",
] as const;

export type SlotId = (typeof SLOTS)[number];

export type Loadout = Record<SlotId, string>;

export interface Credit {
  what: string;
  who: string;
  license: string;
  url?: string;
}

/** How an item becomes available. Currency prices come later (Makeover.md §9). */
export type Unlock = "starter" | `milestone:${string}` | `secret:${string}` | `seasonal:${string}`;

export interface Item {
  id: string;
  slot: SlotId;
  name: string;
  description: string;
  /** Preset (theme set) the item was made for. */
  set?: string;
  unlock?: Unlock;
  tags?: string[];
  credits?: Credit[];
  /** Up to 4 CSS colours shown as a swatch in the Wardrobe. */
  swatch?: string[];
  /** Slot-specific configuration, read only by the module that owns the slot. */
  data?: Record<string, unknown>;
}

export interface Preset {
  id: string;
  name: string;
  description: string;
  /** Earned through a milestone; the backend says whether it is unlocked. */
  reward?: boolean;
  /** Hidden until found (easter egg). */
  secret?: string;
  slots: Partial<Loadout>;
}

export type Whimsy = "off" | "subtle" | "full";

export interface Volumes {
  master: number;
  ui: number;
  feedback: number;
  celebration: number;
}

export interface AppearanceSettings {
  whimsy: Whimsy;
  /** Hide the wallpaper and strip decorative animation. */
  focus: boolean;
  /** Turn focus on automatically in timed quizzes. */
  focusInTimed: boolean;
  /** "system" follows prefers-reduced-motion. */
  reducedMotion: "system" | "on" | "off";
  muted: boolean;
  volumes: Volumes;
  seasonal: boolean;
  eggs: boolean;
  /** Home: use the study room (true) or the plain widget layout. */
  room: boolean;
  greetingName: string;
  exam: { label: string; date: string | null };
  /** Per-token overrides on top of the palette (spec §11.3), e.g. {"--primary": "#ff0000"}. */
  tokens: Record<string, string>;
  /** Switch to `night` loadout between these hours (local time). */
  dayNight: { enabled: boolean; night: string | null; from: number; to: number };
}

export interface SavedLoadout {
  name: string;
  loadout: Loadout;
}

export interface AppearanceState {
  loadout: Loadout;
  /** Preset the loadout started from; null once fully custom. */
  preset: string | null;
  settings: AppearanceSettings;
  saved: SavedLoadout[];
}
