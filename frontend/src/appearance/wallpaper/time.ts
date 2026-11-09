/**
 * Image wallpapers from packs: `data.image` by day and the optional
 * `data.night` from 19:00 to 07:00 local time.
 */

import type { Item } from "../types";

export const NIGHT_FROM = 19;
export const NIGHT_TO = 7;

export function isNight(date: Date): boolean {
  const h = date.getHours();
  return h >= NIGHT_FROM || h < NIGHT_TO;
}

/** The image URL to show for an item at `date`, or null for procedural scenes. */
export function imageFor(item: Item | undefined, date: Date): string | null {
  const d = item?.data;
  const day = typeof d?.image === "string" && d.image ? d.image : null;
  const night = typeof d?.night === "string" && d.night ? d.night : null;
  if (!day) return null;
  return night && isNight(date) ? night : day;
}
