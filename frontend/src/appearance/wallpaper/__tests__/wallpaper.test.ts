/** Wallpaper items, the scene registry and the day/night image rule. */

import { describe, expect, it } from "vitest";

import { PRESETS } from "../../presets";
import type { Item } from "../../types";
import { ITEMS } from "../items";
import { normalizeColor } from "../kit";
import { SCENES, sceneKeyFor } from "../scenes";
import { imageFor, isNight } from "../time";
import { scatter, type SceneEnv } from "../types";

const at = (h: number, m = 0) => new Date(2026, 10, 9, h, m);

describe("wallpaper items", () => {
  const byId = new Map(ITEMS.map((i) => [i.id, i]));

  it("provide every wallpaper a preset uses, each with a scene", () => {
    for (const p of PRESETS) {
      const id = p.slots.wallpaper;
      if (!id) continue;
      const item = byId.get(id);
      expect(item?.slot, id).toBe("wallpaper");
      const key = sceneKeyFor(item);
      expect(key).toBe(id.slice("wallpaper.".length));
      expect(SCENES[key], id).toBeDefined();
    }
  });

  it("include the full set of built-in wallpapers", () => {
    const ids = [
      "none", "clouds", "aquarium", "pixel-clouds", "hills", "burst", "glyph-rain", "leaves",
      "embers", "night-sky", "chalk-dust", "synth-grid", "rain", "dunes", "petals",
    ];
    for (const s of ids) {
      const item = byId.get(`wallpaper.${s}`);
      expect(item, s).toBeDefined();
      expect(SCENES[sceneKeyFor(item)], s).toBeDefined();
    }
  });

  it("keep every scene at or under 30 fps", () => {
    for (const [key, scene] of Object.entries(SCENES)) {
      expect(scene.fps ?? 30, key).toBeLessThanOrEqual(30);
    }
  });

  it("map unknown scenes to none and pack images to the image renderer", () => {
    const pack: Item = { id: "wallpaper.mine", slot: "wallpaper", name: "Mine", description: "", data: { image: "/a.png" } };
    expect(sceneKeyFor(pack)).toBe("image");
    expect(sceneKeyFor({ ...pack, data: {} })).toBe("none");
    expect(sceneKeyFor({ ...pack, data: { scene: "rain" } })).toBe("rain");
    expect(sceneKeyFor(undefined)).toBe("none");
  });
});

describe("night images", () => {
  it("counts 19:00 to 06:59 as night", () => {
    expect(isNight(at(18, 59))).toBe(false);
    expect(isNight(at(19, 0))).toBe(true);
    expect(isNight(at(23, 30))).toBe(true);
    expect(isNight(at(0, 0))).toBe(true);
    expect(isNight(at(6, 59))).toBe(true);
    expect(isNight(at(7, 0))).toBe(false);
    expect(isNight(at(12, 0))).toBe(false);
  });

  it("shows the night image only at night, and the day image otherwise", () => {
    const both: Item = { id: "wallpaper.x", slot: "wallpaper", name: "X", description: "", data: { image: "day.png", night: "night.png" } };
    expect(imageFor(both, at(12))).toBe("day.png");
    expect(imageFor(both, at(20))).toBe("night.png");
    expect(imageFor(both, at(5))).toBe("night.png");
    const dayOnly: Item = { ...both, data: { image: "day.png" } };
    expect(imageFor(dayOnly, at(22))).toBe("day.png");
    expect(imageFor({ ...both, data: {} }, at(12))).toBeNull();
    expect(imageFor(undefined, at(12))).toBeNull();
  });
});

describe("scatter", () => {
  it("is busier at full density and scales with area", () => {
    const env = (w: number, h: number, density: 1 | 2) => ({ w, h, density }) as SceneEnv;
    expect(scatter(env(1920, 1080, 2), 20)).toBeGreaterThan(scatter(env(1920, 1080, 1), 20));
    expect(scatter(env(1920, 1080, 2), 20)).toBeGreaterThan(scatter(env(800, 600, 2), 20));
    expect(scatter(env(100, 60, 2), 20, 3)).toBe(3);
  });
});

describe("palette colours", () => {
  it("reads hex, rgba and the first colour of a gradient", () => {
    expect(normalizeColor(" #2563eb")).toEqual({ r: 37, g: 99, b: 235 });
    expect(normalizeColor("rgba(255, 255, 255, 0.72)")).toEqual({ r: 255, g: 255, b: 255 });
    expect(normalizeColor("linear-gradient(180deg, #b3e0ff 0%, #d6f0ff 60%)")).toEqual({ r: 179, g: 224, b: 255 });
    expect(normalizeColor("")).toBeNull();
  });
});
