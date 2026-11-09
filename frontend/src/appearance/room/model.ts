/**
 * Shared shapes for the study room: the clickable objects, the context every
 * room theme draws from, and the theme contract.
 */

import type { ReactNode } from "react";

import type { PlantStage, SceneData, Season, TimeOfDay } from "./helpers";

/** Clickable objects. Every theme draws all of them. */
export type ObjectId = "door" | "printer" | "cabinet" | "chart" | "bookcase" | "noticeboard" | "lamp" | "pennant" | "mug";

export const OBJECT_IDS: readonly ObjectId[] = [
  "door", "noticeboard", "pennant", "chart", "bookcase", "lamp", "mug", "printer", "cabinet",
];

export interface Rect {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface ArtCtx {
  /** Unique id for a <defs> entry in this scene instance. */
  id: (name: string) => string;
  /** `url(#…)` for a <defs> entry. */
  url: (name: string) => string;
  now: Date;
  tod: TimeOfDay;
  season: Season;
  lampOn: boolean;
  /** Decorative motion allowed. */
  motion: boolean;
  /** Wardrobe thumbnail: no logos, no interaction. */
  preview: boolean;
  data: SceneData;
  plant: PlantStage;
  /** A pack's wall picture, when the item supplies one. */
  backdrop: string | null;
  /** Wrap an object's art as a clickable hotspot. */
  hs: (id: ObjectId, rect: Rect, art: ReactNode) => ReactNode;
}

export interface RoomTheme {
  id: string;
  /** Draw with shape-rendering crispEdges. */
  pixel?: boolean;
  render: (c: ArtCtx) => ReactNode;
}
