/**
 * Scene registry: wallpaper key → renderer. A wallpaper item's key is its id
 * suffix ("wallpaper.rain" → "rain"); pack items can pick a scene with
 * `data.scene`, or show their own art with `data.image` (and `data.night`).
 * To add a scene, write it with defineScene() and list it here.
 */

import type { Item } from "../../types";
import { defineScene, type Scene } from "../types";
import { aquarium } from "./aquarium";
import { burst } from "./burst";
import { chalkDust, embers, glyphRain, leaves, petals, rain } from "./drift";
import { dunes, nightSky, synthGrid } from "./night";
import { clouds, hills, pixelClouds } from "./sky";

const none = defineScene({ animated: false, init: () => null, draw: () => {} });

export const SCENES: Record<string, Scene> = {
  none,
  clouds,
  aquarium,
  "pixel-clouds": pixelClouds,
  hills,
  burst,
  "glyph-rain": glyphRain,
  leaves,
  embers,
  "night-sky": nightSky,
  "chalk-dust": chalkDust,
  "synth-grid": synthGrid,
  rain,
  dunes,
  petals,
};

/** "image" for pack art, a SCENES key otherwise ("none" when unknown). */
export function sceneKeyFor(item: Item | undefined): string {
  if (!item) return "none";
  const d = item.data ?? {};
  if (typeof d.image === "string" && d.image) return "image";
  const key = typeof d.scene === "string" ? d.scene : item.id.slice(item.id.indexOf(".") + 1);
  return key in SCENES ? key : "none";
}
