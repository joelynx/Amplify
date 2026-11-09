/**
 * Frutiger Aero aquarium: bright water with shimmering light caustics,
 * slanting light shafts, a few glossy fish gliding past and rising bubbles.
 */

import { BLACK, TAU, WHITE, css, mix, parseColor, pick, range, rng, smoothstep, type Rgb } from "../kit";
import { defineScene, layer, scatter, vGradient, type Layer, type SceneEnv } from "../types";

const hex = (s: string): Rgb => parseColor(s) ?? WHITE;

let causticTile: HTMLCanvasElement | null = null;

/** A seamless tile of Voronoi edges: the bright network of light on a pool floor. Built once. */
function caustics(): HTMLCanvasElement {
  if (causticTile) return causticTile;
  const T = 192;
  const c = document.createElement("canvas");
  c.width = c.height = T;
  const g = c.getContext("2d");
  if (!g) return c;
  const img = g.createImageData(T, T);
  const r = rng(7);
  const pts = Array.from({ length: 11 }, () => [r() * T, r() * T]);
  for (let y = 0; y < T; y++) {
    for (let x = 0; x < T; x++) {
      let f1 = Infinity;
      let f2 = Infinity;
      for (const [px, py] of pts) {
        let dx = Math.abs(x - px);
        let dy = Math.abs(y - py);
        if (dx > T / 2) dx = T - dx;
        if (dy > T / 2) dy = T - dy;
        const d = Math.sqrt(dx * dx + dy * dy);
        if (d < f1) {
          f2 = f1;
          f1 = d;
        } else if (d < f2) {
          f2 = d;
        }
      }
      const v = 1 - smoothstep(0, 7, f2 - f1);
      const i = (y * T + x) * 4;
      img.data[i] = img.data[i + 1] = img.data[i + 2] = 255;
      img.data[i + 3] = Math.round(v * v * v * 230);
    }
  }
  g.putImageData(img, 0, 0);
  causticTile = c;
  return c;
}

interface Bubble {
  x: number;
  y: number;
  r: number;
  vy: number;
  amp: number;
  f: number;
  ph: number;
}

interface Fish {
  x: number;
  y: number;
  dir: 1 | -1;
  speed: number;
  size: number;
  ph: number;
  color: string;
  body: Layer;
  bw: number;
  bh: number;
}

function bubbleSprite(env: SceneEnv): HTMLCanvasElement {
  const L = layer(env, 32, 32);
  const g = L.ctx;
  g.fillStyle = "rgba(255,255,255,0.12)";
  g.strokeStyle = "rgba(255,255,255,0.75)";
  g.lineWidth = 1.6;
  g.beginPath();
  g.arc(16, 16, 13, 0, TAU);
  g.fill();
  g.stroke();
  g.fillStyle = "rgba(255,255,255,0.9)";
  g.beginPath();
  g.ellipse(11, 10, 4.5, 2.5, -0.7, 0, TAU);
  g.fill();
  return L.canvas;
}

/** A glossy fish body facing right (the tail is drawn live so it can swish). */
function fishBody(env: SceneEnv, size: number, color: Rgb): { body: Layer; bw: number; bh: number } {
  const bw = size * 1.5;
  const bh = size * 0.9;
  const body = layer(env, bw, bh);
  const g = body.ctx;
  const cx = bw * 0.5;
  const cy = bh * 0.5;
  const rx = size * 0.6;
  const ry = size * 0.32;
  g.fillStyle = css(mix(color, BLACK, 0.2));
  g.beginPath();
  g.moveTo(cx - rx * 0.2, cy - ry * 0.85);
  g.quadraticCurveTo(cx, cy - ry * 1.6, cx + rx * 0.35, cy - ry * 0.8);
  g.fill();
  g.fillStyle = vGradient(g, cy - ry, cy + ry, [
    [0, css(mix(color, WHITE, 0.45))],
    [0.5, css(color)],
    [1, css(mix(color, BLACK, 0.3))],
  ]);
  g.beginPath();
  g.ellipse(cx, cy, rx, ry, 0, 0, TAU);
  g.fill();
  g.fillStyle = "rgba(255,255,255,0.45)";
  g.beginPath();
  g.ellipse(cx + rx * 0.1, cy - ry * 0.45, rx * 0.55, ry * 0.25, 0, 0, TAU);
  g.fill();
  g.fillStyle = "#ffffff";
  g.beginPath();
  g.arc(cx + rx * 0.58, cy - ry * 0.15, ry * 0.26, 0, TAU);
  g.fill();
  g.fillStyle = "#10202c";
  g.beginPath();
  g.arc(cx + rx * 0.63, cy - ry * 0.15, ry * 0.13, 0, TAU);
  g.fill();
  return { body, bw, bh };
}

export const aquarium = defineScene({
  animated: true,
  fps: 24,
  resolution: (dpr) => Math.min(dpr, 1),
  init(env) {
    const { pal, w, h, rand: r } = env;
    const aqua = hex("#22a6c9");
    const deep = hex("#0b4f7a");
    const top = pal.dark ? mix(pal.background, aqua, 0.35) : mix(mix(WHITE, aqua, 0.38), pal.primary, 0.1);
    const bottom = pal.dark ? mix(mix(pal.background, deep, 0.4), BLACK, 0.3) : mix(mix(aqua, deep, 0.6), pal.primary, 0.1);

    const water = layer(env);
    const g = water.ctx;
    g.fillStyle = vGradient(g, 0, h, [
      [0, css(top)],
      [1, css(bottom)],
    ]);
    g.fillRect(0, 0, w, h);
    const bloom = g.createRadialGradient(w * 0.3, -h * 0.1, 0, w * 0.3, -h * 0.1, Math.max(w, h) * 0.9);
    bloom.addColorStop(0, pal.dark ? "rgba(255,255,255,0.18)" : "rgba(255,255,255,0.45)");
    bloom.addColorStop(1, "rgba(255,255,255,0)");
    g.fillStyle = bloom;
    g.fillRect(0, 0, w, h);
    const sandCol = pal.dark ? mix(hex("#c9b98a"), pal.background, 0.6) : hex("#efe2b4");
    g.fillStyle = vGradient(g, h * 0.88, h, [
      [0, css(sandCol, 0)],
      [1, css(sandCol, 0.45)],
    ]);
    g.fillRect(0, h * 0.88, w, h * 0.12);

    const causticH = h * 0.7;
    const caustic = layer(env, w, causticH, env.scale * 0.5);
    const pattern = caustic.ctx.createPattern(caustics(), "repeat");

    const shafts = Array.from({ length: 4 }, () => ({
      x: range(r, 0.05, 0.85) * w,
      width: range(r, 60, 150) * env.unit,
      tilt: range(r, -0.15, 0.2) * w,
      ph: r() * TAU,
    }));

    const spawnBubble = (anywhere: boolean): Bubble => ({
      x: r() * w,
      y: anywhere ? r() * h : h + range(r, 0, 40),
      r: range(r, 2, 6.5) * env.unit,
      vy: range(r, 22, 55) * env.unit,
      amp: range(r, 4, 12) * env.unit,
      f: range(r, 0.8, 2),
      ph: r() * TAU,
    });
    const bubbles = Array.from({ length: scatter(env, 18, 6, 80) }, () => spawnBubble(true));

    const fishColors = [pal.accent, pal.warning, hex("#ff8a3d"), pal.secondary, mix(pal.primary, WHITE, 0.3)];
    const fish: Fish[] = Array.from({ length: env.density === 2 ? 5 : 3 }, () => {
      const size = range(r, 40, 72) * Math.max(0.5, env.unit);
      const color = pick(r, fishColors);
      return {
        x: r() * w,
        y: range(r, 0.25, 0.85) * h,
        dir: r() < 0.5 ? 1 : -1,
        speed: range(r, 18, 40) * env.unit,
        size,
        ph: r() * TAU,
        color: css(mix(color, BLACK, 0.1)),
        ...fishBody(env, size, color),
      };
    });

    return { water, caustic, causticH, pattern, shafts, bubbles, spawnBubble, fish, bubble: bubbleSprite(env) };
  },
  back(ctx, s, env) {
    ctx.drawImage(s.water.canvas, 0, 0, env.w, env.h);
  },
  draw(ctx, s, env, t, dt) {
    const { w, h } = env;

    // Caustics: two drifting copies of the tile, faded out with depth.
    if (s.pattern) {
      const c = s.caustic.ctx;
      const k = 1.6 * Math.max(0.6, env.unit);
      c.globalCompositeOperation = "source-over";
      c.clearRect(0, 0, w, s.causticH);
      c.fillStyle = s.pattern;
      s.pattern.setTransform(new DOMMatrix().translateSelf(t * 9, t * 5).scaleSelf(k, k));
      c.globalAlpha = 0.75;
      c.fillRect(0, 0, w, s.causticH);
      s.pattern.setTransform(new DOMMatrix().translateSelf(-t * 7, t * 8).rotateSelf(35).scaleSelf(k * 2.1, k * 2.1));
      c.globalAlpha = 0.5;
      c.fillRect(0, 0, w, s.causticH);
      c.globalAlpha = 1;
      c.globalCompositeOperation = "destination-in";
      c.fillStyle = vGradient(c, 0, s.causticH, [
        [0, "rgba(0,0,0,1)"],
        [1, "rgba(0,0,0,0)"],
      ]);
      c.fillRect(0, 0, w, s.causticH);
      c.globalCompositeOperation = "source-over";
      ctx.globalCompositeOperation = "lighter";
      ctx.globalAlpha = env.pal.dark ? 0.14 : 0.17;
      ctx.drawImage(s.caustic.canvas, 0, 0, w, s.causticH);
    }

    // Light shafts.
    ctx.globalCompositeOperation = "lighter";
    ctx.fillStyle = vGradient(ctx, 0, h * 0.85, [
      [0, "rgba(255,255,255,0.16)"],
      [1, "rgba(255,255,255,0)"],
    ]);
    for (const sh of s.shafts) {
      const sway = Math.sin(t * 0.15 + sh.ph) * 30 * env.unit;
      ctx.globalAlpha = 0.6 * (0.7 + 0.3 * Math.sin(t * 0.3 + sh.ph));
      ctx.beginPath();
      ctx.moveTo(sh.x + sway, 0);
      ctx.lineTo(sh.x + sway + sh.width, 0);
      ctx.lineTo(sh.x + sh.tilt + sh.width * 1.8, h * 0.85);
      ctx.lineTo(sh.x + sh.tilt, h * 0.85);
      ctx.closePath();
      ctx.fill();
    }
    ctx.globalAlpha = 1;
    ctx.globalCompositeOperation = "source-over";

    // Fish.
    const k = env.scale;
    for (const f of s.fish) {
      f.x += f.dir * f.speed * dt;
      const edge = f.size * 1.5;
      if (f.dir > 0 && f.x > w + edge) {
        f.x = -edge;
        f.y = range(Math.random, 0.25, 0.85) * h;
      } else if (f.dir < 0 && f.x < -edge) {
        f.x = w + edge;
        f.y = range(Math.random, 0.25, 0.85) * h;
      }
      const y = f.y + Math.sin(t * 0.8 + f.ph) * 6 * env.unit;
      ctx.setTransform(k * f.dir, 0, 0, k, f.x * k, y * k);
      const swish = Math.sin(t * 5 + f.ph) * 0.35;
      const rx = f.size * 0.6;
      ctx.fillStyle = f.color;
      ctx.beginPath();
      ctx.moveTo(-rx * 0.85, 0);
      ctx.lineTo(-rx - f.size * 0.45, -f.size * 0.3 * (1 + swish));
      ctx.lineTo(-rx - f.size * 0.38, 0);
      ctx.lineTo(-rx - f.size * 0.45, f.size * 0.3 * (1 - swish));
      ctx.closePath();
      ctx.fill();
      ctx.drawImage(f.body.canvas, -f.bw / 2, -f.bh / 2, f.bw, f.bh);
    }
    ctx.setTransform(k, 0, 0, k, 0, 0);

    // Bubbles.
    for (let i = 0; i < s.bubbles.length; i++) {
      const b = s.bubbles[i];
      b.y -= b.vy * dt;
      if (b.y < -10) {
        s.bubbles[i] = s.spawnBubble(false);
        continue;
      }
      const x = b.x + Math.sin(t * b.f + b.ph) * b.amp;
      ctx.drawImage(s.bubble, x - b.r, b.y - b.r, b.r * 2, b.r * 2);
    }
  },
});
