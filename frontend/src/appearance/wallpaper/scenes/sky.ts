/**
 * Daytime sky scenes: soft pastel clouds, rolling hills (an original
 * early-2000s desktop mood, not any particular photo) and chunky pixel
 * clouds with stars that move in steps.
 */

import { BLACK, TAU, WHITE, css, mix, parseColor, pick, range, type Rgb } from "../kit";
import { defineScene, layer, scatter, vGradient, type Layer, type SceneEnv } from "../types";

const hex = (s: string): Rgb => parseColor(s) ?? WHITE;

interface Sprite extends Layer {
  w: number;
  h: number;
}

/** A soft cumulus cloud pre-rendered once: overlapping puffs, blurred, with a shaded underside. */
export function cloudSprite(env: SceneEnv, cw: number, body: Rgb, shade: Rgb, r: () => number): Sprite {
  const ch = cw * 0.6;
  const pad = Math.ceil(cw * 0.08);
  const L = layer(env, cw + pad * 2, ch + pad * 2);
  const g = L.ctx;
  g.translate(pad, pad);
  g.filter = `blur(${Math.max(1, cw * 0.02 * env.scale).toFixed(1)}px)`;
  g.fillStyle = css(body);
  const k = 5 + Math.floor(r() * 4);
  for (let i = 0; i < k; i++) {
    const u = i / (k - 1);
    const hump = Math.sin(Math.PI * u);
    const rad = ch * (0.18 + 0.16 * hump + range(r, 0, 0.06));
    const cx = cw * (0.14 + 0.72 * u) + range(r, -0.03, 0.03) * cw;
    const cy = ch * 0.7 - rad * 0.5 - hump * ch * 0.1;
    g.beginPath();
    g.arc(cx, cy, rad, 0, TAU);
    g.fill();
  }
  g.beginPath();
  g.ellipse(cw / 2, ch * 0.72, cw * 0.42, ch * 0.13, 0, 0, TAU);
  g.fill();
  g.filter = "none";
  g.globalCompositeOperation = "source-atop";
  g.fillStyle = vGradient(g, ch * 0.35, ch * 0.9, [
    [0, css(shade, 0)],
    [1, css(shade, 0.55)],
  ]);
  g.fillRect(-pad, -pad, cw + pad * 2, ch + pad * 2);
  g.globalCompositeOperation = "source-over";
  return { ...L, w: cw + pad * 2, h: ch + pad * 2 };
}

interface Cloud {
  sprite: Sprite;
  x: number;
  y: number;
  v: number;
  a: number;
}

function driftClouds(ctx: CanvasRenderingContext2D, list: Cloud[], w: number, dt: number): void {
  for (const c of list) {
    c.x += c.v * dt;
    if (c.x > w) c.x = -c.sprite.w;
    ctx.globalAlpha = c.a;
    ctx.drawImage(c.sprite.canvas, c.x, c.y, c.sprite.w, c.sprite.h);
  }
  ctx.globalAlpha = 1;
}

/* ------------------------------------------------------------------ */

export const clouds = defineScene({
  animated: true,
  fps: 20,
  resolution: (dpr) => Math.min(dpr, 1),
  init(env) {
    const { pal, w, h, rand: r } = env;
    const sky = layer(env);
    const top = mix(pal.background, pal.primary, pal.dark ? 0.25 : 0.32);
    const mid = mix(pal.background, pal.secondary, 0.18);
    const bot = mix(pal.background, pal.accent, 0.12);
    sky.ctx.fillStyle = vGradient(sky.ctx, 0, h, [
      [0, css(top)],
      [0.55, css(mid)],
      [1, css(bot)],
    ]);
    sky.ctx.fillRect(0, 0, w, h);
    const tints = [pal.primary, pal.secondary, pal.accent];
    const list: Cloud[] = [];
    const n = scatter(env, 7, 4, 14);
    for (let i = 0; i < n; i++) {
      const cw = range(r, 200, 420) * env.unit;
      const tint = pick(r, tints);
      const body = pal.dark ? mix(pal.background, mix(pal.text, tint, 0.3), 0.3) : mix(WHITE, tint, range(r, 0.02, 0.08));
      const shade = pal.dark ? mix(pal.background, tint, 0.18) : mix(WHITE, tint, 0.45);
      const sprite = cloudSprite(env, cw, body, shade, r);
      list.push({ sprite, x: range(r, -sprite.w, w), y: range(r, -0.05, 0.7) * h, v: (3 + cw / 40) * env.unit, a: range(r, 0.75, 1) });
    }
    list.sort((a, b) => a.sprite.w - b.sprite.w);
    return { sky, list };
  },
  back(ctx, s, env) {
    ctx.drawImage(s.sky.canvas, 0, 0, env.w, env.h);
  },
  draw(ctx, s, env, _t, dt) {
    driftClouds(ctx, s.list, env.w, dt);
  },
});

/* ------------------------------------------------------------------ */

const HILLS = [
  { base: 0.6, amp: 0.05, light: "#a6dc8e", deep: "#77bd5f", haze: 0.35 },
  { base: 0.71, amp: 0.07, light: "#7acb5c", deep: "#43a035", haze: 0.15 },
  { base: 0.83, amp: 0.08, light: "#72d44c", deep: "#2e8a22", haze: 0 },
];

export const hills = defineScene({
  animated: true,
  fps: 15,
  resolution: (dpr) => Math.min(dpr, 1.25),
  init(env) {
    const { pal, w, h, rand: r } = env;
    const dark = pal.dark;
    const night = hex("#08142a");

    const sky = layer(env);
    const g = sky.ctx;
    const top = dark ? mix(hex("#0b1736"), pal.primary, 0.15) : mix(hex("#2a6fdb"), pal.primary, 0.15);
    const horizon = dark ? mix(hex("#34507e"), pal.secondary, 0.1) : mix(hex("#bfe4ff"), pal.primary, 0.05);
    g.fillStyle = vGradient(g, 0, h * 0.75, [
      [0, css(top)],
      [1, css(horizon)],
    ]);
    g.fillRect(0, 0, w, h);
    const gx = w * 0.82;
    const gy = h * 0.16;
    const glow = g.createRadialGradient(gx, gy, 0, gx, gy, Math.max(w, h) * 0.35);
    glow.addColorStop(0, dark ? "rgba(220,230,255,0.22)" : "rgba(255,255,240,0.55)");
    glow.addColorStop(1, "rgba(255,255,255,0)");
    g.fillStyle = glow;
    g.fillRect(0, 0, w, h);
    if (dark) {
      g.fillStyle = "#ffffff";
      for (let i = 0, n = scatter(env, 120); i < n; i++) {
        g.globalAlpha = range(r, 0.25, 0.8);
        const s = range(r, 0.8, 1.6) * env.unit;
        g.fillRect(r() * w, r() * h * 0.5, s, s);
      }
      g.globalAlpha = 1;
    }

    const ground = layer(env);
    const G = ground.ctx;
    for (const L of HILLS) {
      const f1 = range(r, 0.5, 1.1);
      const f2 = range(r, 1.4, 2.4);
      const p1 = r() * TAU;
      const p2 = r() * TAU;
      const yAt = (x: number) =>
        h * (L.base - L.amp * (0.65 * Math.sin((x / w) * TAU * f1 + p1) + 0.35 * Math.sin((x / w) * TAU * f2 + p2)));
      let light = mix(hex(L.light), pal.success, 0.2);
      let deep = mix(hex(L.deep), pal.success, 0.2);
      if (dark) {
        light = mix(light, night, 0.62);
        deep = mix(deep, night, 0.7);
      }
      light = mix(light, horizon, L.haze);
      deep = mix(deep, horizon, L.haze);
      G.beginPath();
      G.moveTo(0, yAt(0));
      for (let x = 8; x <= w + 8; x += 8) G.lineTo(x, yAt(x));
      const crest = new Path2D();
      crest.moveTo(0, yAt(0));
      for (let x = 8; x <= w + 8; x += 8) crest.lineTo(x, yAt(x));
      G.lineTo(w + 8, h);
      G.lineTo(0, h);
      G.closePath();
      G.fillStyle = vGradient(G, h * (L.base - L.amp), h, [
        [0, css(light)],
        [1, css(deep)],
      ]);
      G.fill();
      G.strokeStyle = css(mix(light, WHITE, dark ? 0.1 : 0.35), 0.5);
      G.lineWidth = 2 * env.unit;
      G.stroke(crest);
    }
    G.globalCompositeOperation = "source-atop";
    const patch = G.createRadialGradient(w * 0.3, h * 0.88, 0, w * 0.3, h * 0.88, w * 0.45);
    patch.addColorStop(0, dark ? "rgba(140,170,255,0.08)" : "rgba(255,255,170,0.22)");
    patch.addColorStop(1, "rgba(255,255,170,0)");
    G.fillStyle = patch;
    G.fillRect(0, 0, w, h);
    G.globalCompositeOperation = "source-over";

    const list: Cloud[] = [];
    const n = scatter(env, 3, 2, 8);
    for (let i = 0; i < n; i++) {
      const cw = range(r, 140, 320) * env.unit;
      const body = dark ? mix(horizon, WHITE, 0.12) : WHITE;
      const shade = dark ? mix(top, BLACK, 0.2) : hex("#c3d8ef");
      const sprite = cloudSprite(env, cw, body, shade, r);
      list.push({ sprite, x: range(r, -sprite.w, w), y: range(r, 0.03, 0.36) * h, v: range(r, 3, 9) * env.unit, a: dark ? 0.45 : 0.95 });
    }
    list.sort((a, b) => a.sprite.w - b.sprite.w);
    return { sky, ground, list };
  },
  back(ctx, s, env) {
    ctx.drawImage(s.sky.canvas, 0, 0, env.w, env.h);
  },
  draw(ctx, s, env, _t, dt) {
    // Clouds can dip behind the far hills, so the ground is redrawn over them.
    driftClouds(ctx, s.list, env.w, dt);
    ctx.drawImage(s.ground.canvas, 0, 0, env.w, env.h);
  },
});

/* ------------------------------------------------------------------ */

/** CSS px per art pixel. */
const PX = 5;

interface PixelStar {
  x: number;
  y: number;
  period: number;
  phase: number;
  big: boolean;
}

interface PixelCloud {
  sprite: HTMLCanvasElement;
  cw: number;
  x0: number;
  y: number;
  speed: number;
}

function pixelCloud(env: SceneEnv, cw: number, body: string, shade: string, light: string, r: () => number): HTMLCanvasElement {
  const ch = Math.max(4, Math.ceil(cw * 0.4));
  const L = layer(env, cw, ch, 1);
  const g = L.ctx;
  const blobs = Array.from({ length: 3 + Math.floor(r() * 2) }, () => ({
    cx: range(r, 0.22, 0.78) * cw,
    cy: ch * range(r, 0.45, 0.65),
    rad: range(r, 0.18, 0.3) * cw,
  }));
  const inside = (x: number, y: number) =>
    x >= 0 &&
    y >= 0 &&
    x < cw &&
    y < ch &&
    ((y >= ch * 0.6 && y < ch - 1 && x >= cw * 0.1 && x < cw * 0.9) ||
      blobs.some((b) => (x + 0.5 - b.cx) ** 2 + ((y + 0.5 - b.cy) * 1.7) ** 2 < b.rad * b.rad));
  for (let y = 0; y < ch; y++) {
    for (let x = 0; x < cw; x++) {
      if (!inside(x, y)) continue;
      g.fillStyle = !inside(x, y + 1) ? shade : !inside(x, y - 1) ? light : body;
      g.fillRect(x, y, 1, 1);
    }
  }
  return L.canvas;
}

export const pixelClouds = defineScene({
  animated: true,
  fps: 8,
  pixelated: true,
  resolution: () => 1 / PX,
  init(env) {
    const { pal, rand: r } = env;
    const gw = Math.max(1, Math.round(env.w / PX));
    const gh = Math.max(1, Math.round(env.h / PX));
    const dark = pal.dark;
    const sky = layer(env, gw, gh, 1);
    const g = sky.ctx;
    const top = dark ? mix(pal.background, BLACK, 0.25) : mix(hex("#4f8fe8"), pal.primary, 0.25);
    const bot = dark ? mix(pal.background, pal.secondary, 0.3) : mix(hex("#bde3ff"), pal.background, 0.3);
    const bands = 7;
    for (let i = 0; i < bands; i++) {
      const y0 = Math.floor((i * gh) / bands);
      const y1 = Math.floor(((i + 1) * gh) / bands);
      g.fillStyle = css(mix(top, bot, i / (bands - 1)));
      g.fillRect(0, y0, gw, y1 - y0);
      if (i === bands - 1) continue;
      // Dither the edge into the next band.
      g.fillStyle = css(mix(top, bot, (i + 1) / (bands - 1)));
      for (let x = 0; x < gw; x++) {
        if (x % 2 === (y1 - 1) % 2) g.fillRect(x, y1 - 1, 1, 1);
        if (x % 4 === 0) g.fillRect(x + ((y1 - 2) % 2) * 2, y1 - 2, 1, 1);
      }
    }
    const stars: PixelStar[] = [];
    if (dark) {
      for (let i = 0, n = scatter(env, 140, 8, 260); i < n; i++) {
        stars.push({ x: Math.floor(r() * gw), y: Math.floor(r() * gh * 0.75), period: range(r, 1.4, 3.2), phase: r(), big: r() < 0.12 });
      }
    }
    const body = dark ? css(mix(pal.background, pal.text, 0.42)) : "#ffffff";
    const shade = dark ? css(mix(pal.background, pal.text, 0.22)) : css(mix(WHITE, pal.primary, 0.28));
    const light = dark ? css(mix(pal.background, pal.text, 0.62)) : css(mix(WHITE, hex("#fff6c8"), 0.6));
    const list: PixelCloud[] = [];
    for (let i = 0, n = scatter(env, 3.5, 3, 9); i < n; i++) {
      const cw = Math.max(10, Math.round(range(r, 24, 48) * Math.max(0.6, env.unit)));
      list.push({
        sprite: pixelCloud(env, cw, body, shade, light, r),
        cw,
        x0: r() * (gw + cw),
        y: Math.floor(range(r, 0.04, 0.6) * gh),
        speed: range(r, 0.6, 1.8),
      });
    }
    return {
      sky,
      stars,
      list,
      gw,
      gh,
      starColor: css(mix(pal.text, WHITE, 0.5)),
      bigColor: css(mix(pal.accent, WHITE, 0.2)),
      dimColor: css(mix(pal.background, pal.text, 0.35)),
    };
  },
  back(ctx, s) {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.drawImage(s.sky.canvas, 0, 0);
  },
  draw(ctx, s, _env, t) {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    for (const st of s.stars) {
      const ph = (t / st.period + st.phase) % 1;
      if (ph < 0.12) continue;
      ctx.fillStyle = ph < 0.3 ? s.dimColor : st.big ? s.bigColor : s.starColor;
      if (st.big && ph >= 0.3) {
        ctx.fillRect(st.x - 1, st.y, 3, 1);
        ctx.fillRect(st.x, st.y - 1, 1, 3);
      } else {
        ctx.fillRect(st.x, st.y, 1, 1);
      }
    }
    for (const c of s.list) {
      const span = s.gw + c.cw;
      const x = Math.floor((c.x0 + t * c.speed) % span) - c.cw;
      ctx.drawImage(c.sprite, x, c.y);
    }
  },
});
