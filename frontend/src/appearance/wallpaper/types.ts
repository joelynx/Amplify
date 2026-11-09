/**
 * Wallpaper scene contract. A scene is plain functions: init() builds its
 * state (particles, pre-rendered layers) for a size and palette, draw()
 * paints one frame, still() the frame shown when animation is off, and the
 * optional back() a static backdrop drawn once. Scenes draw in CSS pixels;
 * the runner handles device pixel ratio, frame rate, resizing, palette
 * changes and pausing.
 */

import { clamp, type Palette } from "./kit";

export interface SceneEnv {
  /** Size in CSS px. */
  w: number;
  h: number;
  /** Canvas pixels per CSS px. */
  scale: number;
  /** Multiplier for absolute sizes: about 1 in a window, smaller in previews. */
  unit: number;
  /** 1 subtle, 2 full: how busy the scene is. */
  density: 1 | 2;
  pal: Palette;
  /** The item's data (pack items can pass scene parameters). */
  data: Record<string, unknown>;
  /** Seeded, so a scene looks the same after a palette change. */
  rand: () => number;
}

export interface Scene<S = unknown> {
  /** False for scenes drawn once. */
  animated: boolean;
  /** Frame cap; the runner never exceeds 30. */
  fps?: number;
  /** Canvas pixels per CSS px for a device pixel ratio (default min(dpr, 1.5)). */
  resolution?(dpr: number): number;
  /** Render with crisp, unsmoothed pixels. */
  pixelated?: boolean;
  init(env: SceneEnv): S;
  /**
   * The unchanging backdrop, painted once per init onto a canvas under the
   * animated one, so frames only redraw what moves.
   */
  back?(ctx: CanvasRenderingContext2D, s: S, env: SceneEnv): void;
  draw(ctx: CanvasRenderingContext2D, s: S, env: SceneEnv, t: number, dt: number): void;
  /** The frame shown when animation is off (default: draw at t = 0). */
  still?(ctx: CanvasRenderingContext2D, s: S, env: SceneEnv): void;
}

export function defineScene<S>(scene: Scene<S>): Scene {
  return scene as unknown as Scene;
}

export interface Layer {
  canvas: HTMLCanvasElement;
  ctx: CanvasRenderingContext2D;
}

/** An offscreen canvas at the scene's resolution, drawn on in CSS px. */
export function layer(env: SceneEnv, w = env.w, h = env.h, scale = env.scale): Layer {
  const canvas = document.createElement("canvas");
  canvas.width = Math.max(1, Math.round(w * scale));
  canvas.height = Math.max(1, Math.round(h * scale));
  const ctx = canvas.getContext("2d") as CanvasRenderingContext2D;
  ctx.setTransform(scale, 0, 0, scale, 0, 0);
  return { canvas, ctx };
}

/** Number of things to scatter: `perMpx` per megapixel at full density, ~60% when subtle. */
export function scatter(env: SceneEnv, perMpx: number, min = 3, max = 400): number {
  const n = ((env.w * env.h) / 1e6) * perMpx * (env.density === 2 ? 1 : 0.6);
  return Math.round(clamp(n, min, max));
}

export function vGradient(
  ctx: CanvasRenderingContext2D,
  y0: number,
  y1: number,
  stops: [number, string][],
): CanvasGradient {
  const g = ctx.createLinearGradient(0, y0, 0, y1);
  for (const [at, c] of stops) g.addColorStop(at, c);
  return g;
}
