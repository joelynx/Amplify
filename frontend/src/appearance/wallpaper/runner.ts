/**
 * Runs one wallpaper scene on a canvas: sizes it for the device pixel ratio,
 * re-initialises on resize and palette changes, and animates at a capped
 * frame rate only while the window (and, for previews, the element) is
 * visible. With `animate` off it paints a single still frame. A scene's
 * static backdrop goes on the optional `back` canvas, painted once.
 */

import { clamp, readPalette, rng, watchPalette, type Palette } from "./kit";
import type { Scene, SceneEnv } from "./types";

export interface RunOptions {
  scene: Scene;
  animate: boolean;
  density: 1 | 2;
  data?: Record<string, unknown>;
  /** Canvas under the main one for the scene's backdrop. */
  back?: HTMLCanvasElement | null;
  /** Lower frame cap (previews). */
  maxFps?: number;
  /** Pause while the canvas is scrolled out of view (previews). */
  pauseOffscreen?: boolean;
}

const SEED = 0x5eed;

function prepare(ctx: CanvasRenderingContext2D, env: SceneEnv, pixelated: boolean): void {
  ctx.setTransform(env.scale, 0, 0, env.scale, 0, 0);
  ctx.globalAlpha = 1;
  ctx.globalCompositeOperation = "source-over";
  ctx.imageSmoothingEnabled = !pixelated;
  ctx.clearRect(0, 0, env.w, env.h);
}

export function runScene(canvas: HTMLCanvasElement, o: RunOptions): () => void {
  const ctx = canvas.getContext("2d");
  if (!ctx) return () => {};
  const { scene } = o;
  const backCtx = scene.back && o.back ? o.back.getContext("2d") : null;
  const pixelated = !!scene.pixelated;
  const interval = 1000 / Math.min(30, scene.fps ?? 30, o.maxFps ?? 30);

  let pal: Palette = readPalette();
  let env: SceneEnv | null = null;
  let state: unknown = null;
  let t = 0;
  let raf = 0;
  let lastDraw = 0;
  let onScreen = true;
  let size = "";

  const paint = (dt: number) => {
    if (!env) return;
    prepare(ctx, env, pixelated);
    if (scene.back && !backCtx) scene.back(ctx, state, env);
    if (!o.animate && scene.still) scene.still(ctx, state, env);
    else scene.draw(ctx, state, env, t, dt);
  };

  const setup = (force: boolean) => {
    const rect = canvas.getBoundingClientRect();
    const w = Math.max(1, Math.round(rect.width || canvas.clientWidth || window.innerWidth));
    const h = Math.max(1, Math.round(rect.height || canvas.clientHeight || window.innerHeight));
    const key = `${w}x${h}`;
    if (!force && key === size) return;
    size = key;
    const dpr = window.devicePixelRatio || 1;
    const scale = scene.resolution ? scene.resolution(dpr) : Math.min(dpr, 1.5);
    for (const c of [canvas, backCtx ? o.back : null]) {
      if (!c) continue;
      c.width = Math.max(1, Math.round(w * scale));
      c.height = Math.max(1, Math.round(h * scale));
    }
    env = {
      w,
      h,
      scale,
      unit: clamp(Math.min(w, h) / 760, 0.35, 1.2),
      density: o.density,
      pal,
      data: o.data ?? {},
      rand: rng(SEED),
    };
    state = scene.init(env);
    if (backCtx && scene.back) {
      prepare(backCtx, env, pixelated);
      scene.back(backCtx, state, env);
    }
    paint(0);
  };

  const loop = (now: number) => {
    raf = requestAnimationFrame(loop);
    const elapsed = now - lastDraw;
    if (elapsed < interval - 2) return;
    lastDraw = now;
    const dt = Math.min(0.1, elapsed / 1000);
    t += dt;
    paint(dt);
  };

  const play = () => {
    if (!o.animate || !scene.animated || raf || document.hidden || !onScreen) return;
    lastDraw = performance.now();
    raf = requestAnimationFrame(loop);
  };

  const pause = () => {
    if (raf) cancelAnimationFrame(raf);
    raf = 0;
  };

  let timer: ReturnType<typeof setTimeout> | null = null;
  const onResize = () => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => setup(false), 150);
  };
  const ro = typeof ResizeObserver !== "undefined" ? new ResizeObserver(onResize) : null;
  if (ro) ro.observe(canvas);
  else window.addEventListener("resize", onResize);

  const io =
    o.pauseOffscreen && typeof IntersectionObserver !== "undefined"
      ? new IntersectionObserver((entries) => {
          onScreen = entries.some((e) => e.isIntersecting);
          if (onScreen) play();
          else pause();
        })
      : null;
  io?.observe(canvas);

  const onVisibility = () => (document.hidden ? pause() : play());
  document.addEventListener("visibilitychange", onVisibility);

  const unwatch = watchPalette((p) => {
    pal = p;
    setup(true);
  });

  setup(true);
  play();

  return () => {
    pause();
    if (timer) clearTimeout(timer);
    ro?.disconnect();
    if (!ro) window.removeEventListener("resize", onResize);
    io?.disconnect();
    document.removeEventListener("visibilitychange", onVisibility);
    unwatch();
  };
}
