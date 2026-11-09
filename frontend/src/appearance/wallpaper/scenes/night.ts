/**
 * Night scenes: a starry sky with a faint milky band and a rare shooting
 * star, desert dunes under a crescent moon with lantern glows, and a
 * synthwave sun over a perspective grid.
 */

import { BLACK, TAU, WHITE, css, glowSprite, mix, parseColor, pick, range, type Rgb } from "../kit";
import { defineScene, layer, scatter, vGradient, type SceneEnv } from "../types";

const hex = (s: string): Rgb => parseColor(s) ?? WHITE;
/** Roughly normal, in about [-1, 1]. */
const gauss = (r: () => number) => (r() + r() + r() - 1.5) / 1.5;

interface Twinkler {
  x: number;
  y: number;
  s: number;
  speed: number;
  ph: number;
  color: string;
}

function twinklers(env: SceneEnv, perMpx: number, maxY: number, colors: string[]): Twinkler[] {
  const r = env.rand;
  return Array.from({ length: scatter(env, perMpx, 8, 300) }, () => ({
    x: r() * env.w,
    y: r() * env.h * maxY,
    s: range(r, 0.8, 1.9) * Math.max(0.6, env.unit),
    speed: range(r, 0.6, 1.8),
    ph: r() * TAU,
    color: pick(r, colors),
  }));
}

function drawTwinklers(ctx: CanvasRenderingContext2D, list: Twinkler[], t: number): void {
  for (const tw of list) {
    ctx.globalAlpha = 0.35 + 0.65 * (0.5 + 0.5 * Math.sin(t * tw.speed + tw.ph));
    ctx.fillStyle = tw.color;
    if (tw.s < 1.3) {
      ctx.fillRect(tw.x - tw.s / 2, tw.y - tw.s / 2, tw.s, tw.s);
    } else {
      ctx.beginPath();
      ctx.arc(tw.x, tw.y, tw.s * 0.6, 0, TAU);
      ctx.fill();
    }
  }
  ctx.globalAlpha = 1;
}

function dimStars(ctx: CanvasRenderingContext2D, env: SceneEnv, perMpx: number, maxY: number): void {
  const r = env.rand;
  ctx.fillStyle = "#ffffff";
  for (let i = 0, n = scatter(env, perMpx, 20, 900); i < n; i++) {
    const y = r() * env.h * maxY;
    ctx.globalAlpha = range(r, 0.15, 0.55) * (1 - (y / (env.h * maxY)) * 0.5);
    const s = range(r, 0.6, 1.2) * Math.max(0.6, env.unit);
    ctx.fillRect(r() * env.w, y, s, s);
  }
  ctx.globalAlpha = 1;
}

/* ------------------------------------------------------------------ */

interface Shot {
  x: number;
  y: number;
  vx: number;
  vy: number;
  start: number;
  dur: number;
  len: number;
}

export const nightSky = defineScene({
  animated: true,
  fps: 24,
  init(env) {
    const { pal, w, h, rand: r } = env;
    const bg = layer(env);
    const g = bg.ctx;
    const top = pal.dark ? mix(pal.background, BLACK, 0.35) : mix(hex("#070b1f"), pal.primary, 0.15);
    const bottom = pal.dark ? mix(pal.background, pal.secondary, 0.22) : mix(hex("#1f2b5a"), pal.secondary, 0.25);
    g.fillStyle = vGradient(g, 0, h, [
      [0, css(top)],
      [1, css(bottom)],
    ]);
    g.fillRect(0, 0, w, h);

    // A faint milky band from lower left to upper right.
    const x0 = -0.1 * w;
    const y0 = 0.95 * h;
    const dx = 1.2 * w;
    const dy = -0.9 * h;
    const len = Math.hypot(dx, dy);
    const nx = -dy / len;
    const ny = dx / len;
    const band = Math.min(w, h) * 0.22;
    const haze = mix(WHITE, pal.secondary, 0.3);
    g.filter = `blur(${(band * 0.12 * env.scale).toFixed(1)}px)`;
    for (let i = 0; i < 140; i++) {
      const u = r();
      const off = gauss(r) * band * 0.45;
      const cx = x0 + dx * u + nx * off;
      const cy = y0 + dy * u + ny * off;
      const rad = range(r, 0.05, 0.13) * Math.min(w, h);
      const grad = g.createRadialGradient(cx, cy, 0, cx, cy, rad);
      grad.addColorStop(0, css(haze, 0.03));
      grad.addColorStop(1, css(haze, 0));
      g.fillStyle = grad;
      g.fillRect(cx - rad, cy - rad, rad * 2, rad * 2);
    }
    g.filter = "none";
    g.fillStyle = "#ffffff";
    for (let i = 0, n = scatter(env, 420, 40, 900); i < n; i++) {
      const u = r();
      const off = gauss(r) * band * 0.5;
      g.globalAlpha = range(r, 0.15, 0.5);
      const s = range(r, 0.5, 1.1) * Math.max(0.6, env.unit);
      g.fillRect(x0 + dx * u + nx * off, y0 + dy * u + ny * off, s, s);
    }
    g.globalAlpha = 1;
    dimStars(g, env, 650, 1);

    const colors = ["#ffffff", css(mix(WHITE, pal.accent, 0.35)), css(mix(WHITE, pal.secondary, 0.3))];
    return {
      bg,
      stars: twinklers(env, 150, 1, colors),
      shot: null as Shot | null,
      next: range(r, 20, 50),
    };
  },
  back(ctx, s, env) {
    ctx.drawImage(s.bg.canvas, 0, 0, env.w, env.h);
  },
  draw(ctx, s, env, t) {
    drawTwinklers(ctx, s.stars, t);
    if (!s.shot && t >= s.next) {
      const a = range(Math.random, 0.25, 0.6) * Math.PI;
      const speed = Math.max(env.w, env.h) * 0.9;
      s.shot = {
        x: range(Math.random, 0.15, 0.85) * env.w,
        y: range(Math.random, 0.02, 0.35) * env.h,
        vx: Math.cos(a) * speed * (Math.random() < 0.5 ? -1 : 1),
        vy: Math.sin(a) * speed,
        start: t,
        dur: 0.9,
        len: Math.min(env.w, env.h) * 0.18,
      };
    }
    const sh = s.shot;
    if (!sh) return;
    const p = (t - sh.start) / sh.dur;
    if (p >= 1) {
      s.shot = null;
      s.next = t + range(Math.random, 45, 75);
      return;
    }
    const hx = sh.x + sh.vx * p * sh.dur;
    const hy = sh.y + sh.vy * p * sh.dur;
    const sp = Math.hypot(sh.vx, sh.vy);
    const tail = sh.len * Math.min(1, p * 3);
    const tx = hx - (sh.vx / sp) * tail;
    const ty = hy - (sh.vy / sp) * tail;
    const a = p < 0.15 ? p / 0.15 : 1 - (p - 0.15) / 0.85;
    const grad = ctx.createLinearGradient(hx, hy, tx, ty);
    grad.addColorStop(0, `rgba(255,255,255,${(0.9 * a).toFixed(3)})`);
    grad.addColorStop(1, "rgba(255,255,255,0)");
    ctx.strokeStyle = grad;
    ctx.lineWidth = 1.6 * Math.max(0.6, env.unit);
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(hx, hy);
    ctx.lineTo(tx, ty);
    ctx.stroke();
  },
  still(ctx, s) {
    drawTwinklers(ctx, s.stars, 0);
  },
});

/* ------------------------------------------------------------------ */

const DUNES = [
  { base: 0.62, amp: 0.045 },
  { base: 0.7, amp: 0.06 },
  { base: 0.8, amp: 0.07 },
  { base: 0.91, amp: 0.06 },
];

export const dunes = defineScene({
  animated: true,
  fps: 12,
  resolution: (dpr) => Math.min(dpr, 1.25),
  init(env) {
    const { pal, w, h, rand: r } = env;
    const indigo = hex("#141043");
    const top = pal.dark ? mix(pal.background, indigo, 0.5) : mix(indigo, pal.primary, 0.12);
    const horizon = pal.dark ? mix(pal.background, hex("#6a3f7e"), 0.45) : mix(hex("#5b3f86"), pal.secondary, 0.2);
    const warm = mix(hex("#f29e5c"), pal.accent, 0.3);
    const moonCol = mix(hex("#fff1c9"), pal.text, 0.08);

    const sky = layer(env);
    const g = sky.ctx;
    g.fillStyle = vGradient(g, 0, h * 0.66, [
      [0, css(top)],
      [1, css(horizon)],
    ]);
    g.fillRect(0, 0, w, h);
    g.fillStyle = vGradient(g, h * 0.42, h * 0.68, [
      [0, css(warm, 0)],
      [1, css(warm, 0.28)],
    ]);
    g.fillRect(0, h * 0.42, w, h * 0.3);
    dimStars(g, env, 240, 0.55);

    // Crescent moon with a soft glow.
    const R = Math.min(w, h) * 0.045;
    const mx = w * 0.78;
    const my = h * 0.2;
    const mg = g.createRadialGradient(mx, my, R * 0.5, mx, my, R * 4);
    mg.addColorStop(0, css(moonCol, 0.22));
    mg.addColorStop(1, css(moonCol, 0));
    g.fillStyle = mg;
    g.fillRect(mx - R * 4, my - R * 4, R * 8, R * 8);
    const moon = layer(env, R * 2 + 4, R * 2 + 4);
    moon.ctx.fillStyle = css(moonCol);
    moon.ctx.beginPath();
    moon.ctx.arc(R + 2, R + 2, R, 0, TAU);
    moon.ctx.fill();
    moon.ctx.globalCompositeOperation = "destination-out";
    moon.ctx.beginPath();
    moon.ctx.arc(R + 2 + R * 0.42, R + 2 - R * 0.18, R * 0.92, 0, TAU);
    moon.ctx.fill();
    g.drawImage(moon.canvas, mx - R - 2, my - R - 2, R * 2 + 4, R * 2 + 4);

    // Dune layers, back to front, with moonlit ridges.
    const sand = layer(env);
    const G = sand.ctx;
    const front = mix(mix(indigo, hex("#3a2238"), 0.4), BLACK, 0.35);
    const lanterns: { x: number; y: number; ph: number }[] = [];
    DUNES.forEach((D, li) => {
      const f1 = range(r, 0.6, 1.3);
      const f2 = range(r, 1.6, 2.8);
      const p1 = r() * TAU;
      const p2 = r() * TAU;
      const wave = (x: number, f: number, p: number) => (0.5 + 0.5 * Math.sin((x / w) * TAU * f + p)) ** 1.6;
      const yAt = (x: number) => h * (D.base - D.amp * (0.65 * wave(x, f1, p1) + 0.35 * wave(x, f2, p2)));
      const k = li / (DUNES.length - 1);
      const col = mix(mix(horizon, indigo, 0.35), front, k);
      const crest = new Path2D();
      crest.moveTo(0, yAt(0));
      for (let x = 6; x <= w + 6; x += 6) crest.lineTo(x, yAt(x));
      const body = new Path2D(crest);
      body.lineTo(w + 6, h);
      body.lineTo(0, h);
      body.closePath();
      G.fillStyle = vGradient(G, h * (D.base - D.amp), h, [
        [0, css(mix(col, moonCol, 0.08))],
        [1, css(mix(col, BLACK, 0.25))],
      ]);
      G.fill(body);
      G.strokeStyle = css(moonCol, 0.16);
      G.lineWidth = 1.2 * Math.max(0.6, env.unit);
      G.stroke(crest);
      if (li === 2) {
        for (const lx of [range(r, 0.18, 0.32) * w, range(r, 0.5, 0.64) * w]) {
          const ly = yAt(lx) - 2 * env.unit;
          const u = Math.max(0.5, env.unit);
          G.fillStyle = "#2a1a10";
          G.fillRect(lx - 4 * u, ly - 13 * u, 8 * u, 2 * u);
          G.fillRect(lx - 0.5 * u, ly - 16 * u, 1 * u, 3 * u);
          G.fillStyle = "#ffcf7a";
          G.fillRect(lx - 3 * u, ly - 11 * u, 6 * u, 9 * u);
          G.fillStyle = "#2a1a10";
          G.fillRect(lx - 4 * u, ly - 2 * u, 8 * u, 2 * u);
          lanterns.push({ x: lx, y: ly - 6.5 * u, ph: r() * TAU });
        }
      }
    });

    const colors = ["#ffffff", css(mix(WHITE, warm, 0.25)), css(mix(WHITE, pal.secondary, 0.3))];
    return {
      sky,
      sand,
      lanterns,
      stars: twinklers(env, 30, 0.5, colors),
      glow: css(mix(hex("#ffb347"), pal.accent, 0.2)),
      radius: 46 * Math.max(0.5, env.unit),
    };
  },
  back(ctx, s, env) {
    ctx.drawImage(s.sky.canvas, 0, 0, env.w, env.h);
    ctx.drawImage(s.sand.canvas, 0, 0, env.w, env.h);
  },
  draw(ctx, s, env, t) {
    // Twinkling stars stay in the upper half, clear of the dunes.
    drawTwinklers(ctx, s.stars, t);
    ctx.globalCompositeOperation = env.pal.dark ? "lighter" : "source-over";
    const sprite = glowSprite(s.glow, 0.15);
    for (const l of s.lanterns) {
      ctx.globalAlpha = 0.5 + 0.1 * Math.sin(t * 1.3 + l.ph) + 0.05 * Math.sin(t * 2.9 + l.ph * 2);
      ctx.drawImage(sprite, l.x - s.radius, l.y - s.radius, s.radius * 2, s.radius * 2);
    }
    ctx.globalAlpha = 1;
    ctx.globalCompositeOperation = "source-over";
  },
});

/* ------------------------------------------------------------------ */

export const synthGrid = defineScene({
  animated: true,
  fps: 30,
  resolution: (dpr) => Math.min(dpr, 1.25),
  init(env) {
    const { pal, w, h, rand: r } = env;
    const H = Math.round(h * 0.62);
    const back = layer(env);
    const g = back.ctx;
    const top = pal.dark ? mix(pal.background, BLACK, 0.3) : mix(hex("#12002a"), pal.primary, 0.1);
    const mid = mix(top, pal.primary, 0.35);
    const glowCol = mix(pal.primary, pal.accent, 0.45);
    g.fillStyle = vGradient(g, 0, H, [
      [0, css(top)],
      [0.7, css(mid)],
      [1, css(glowCol)],
    ]);
    g.fillRect(0, 0, w, H);
    dimStars(g, env, 120, 0.45);

    // The sun: a striped disc with a glow behind it.
    const R = Math.min(w, h * 1.2) * 0.2;
    const cx = w / 2;
    const cy = H - R * 0.25;
    const halo = g.createRadialGradient(cx, cy, R * 0.6, cx, cy, R * 2.2);
    halo.addColorStop(0, css(pal.primary, 0.35));
    halo.addColorStop(1, css(pal.primary, 0));
    g.fillStyle = halo;
    g.fillRect(0, 0, w, H);
    const sun = layer(env, R * 2 + 4, R * 2 + 4);
    const sg = sun.ctx;
    sg.fillStyle = vGradient(sg, 2, R * 2 + 2, [
      [0, css(mix(hex("#ffd166"), pal.accent, 0.4))],
      [1, css(mix(hex("#ff3d8b"), pal.primary, 0.4))],
    ]);
    sg.beginPath();
    sg.arc(R + 2, R + 2, R, 0, TAU);
    sg.fill();
    sg.globalCompositeOperation = "destination-out";
    for (let i = 0; i < 7; i++) {
      const yy = R + 2 + R * (0.12 + i * 0.13);
      sg.fillRect(0, yy, R * 2 + 4, R * (0.025 + i * 0.016));
    }
    g.save();
    g.beginPath();
    g.rect(0, 0, w, H);
    g.clip();
    g.drawImage(sun.canvas, cx - R - 2, cy - R - 2, R * 2 + 4, R * 2 + 4);
    g.restore();

    // Low mountains either side, leaving the sun clear.
    g.beginPath();
    g.moveTo(0, H);
    for (let x = 0; x <= w; x += Math.max(8, w / 60)) {
      const side = Math.abs(x - cx) / (w / 2);
      const peak = h * 0.09 * Math.max(0, side - 0.25) * range(r, 0.55, 1);
      g.lineTo(x, H - peak);
    }
    g.lineTo(w, H);
    g.closePath();
    g.fillStyle = css(mix(top, BLACK, 0.25));
    g.fill();
    g.strokeStyle = css(mix(pal.secondary, WHITE, 0.2), 0.55);
    g.lineWidth = 1.2 * Math.max(0.6, env.unit);
    g.stroke();

    g.fillStyle = vGradient(g, H, h, [
      [0, css(mix(glowCol, top, 0.55))],
      [1, css(mix(top, BLACK, 0.4))],
    ]);
    g.fillRect(0, H, w, h - H);
    g.fillStyle = css(mix(glowCol, WHITE, 0.3), 0.8);
    g.fillRect(0, H - 1, w, 2);
    return { back, H, grid: mix(pal.secondary, WHITE, 0.15) };
  },
  back(ctx, s, env) {
    ctx.drawImage(s.back.canvas, 0, 0, env.w, env.h);
  },
  draw(ctx, s, env, t) {
    const { w, h } = env;
    const H = s.H;
    const cx = w / 2;
    const fade = ctx.createLinearGradient(0, H, 0, h);
    fade.addColorStop(0, css(s.grid, 0));
    fade.addColorStop(0.25, css(s.grid, 0.5));
    fade.addColorStop(1, css(s.grid, 0.95));
    ctx.beginPath();
    const sp = w / 9;
    for (let i = -14; i <= 14; i++) {
      const xb = cx + i * sp;
      ctx.moveTo(cx + (xb - cx) * 0.02, H + (h - H) * 0.02);
      ctx.lineTo(xb, h);
    }
    const phase = (t * 0.5) % 1;
    for (let j = 1; j < 26; j++) {
      const z = j + 1 - phase;
      const y = H + (h - H) / z;
      if (y > h) continue;
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
    }
    ctx.strokeStyle = fade;
    const u = Math.max(0.6, env.unit);
    ctx.globalAlpha = 0.18;
    ctx.lineWidth = 4 * u;
    ctx.stroke();
    ctx.globalAlpha = 0.9;
    ctx.lineWidth = 1.3 * u;
    ctx.stroke();
    ctx.globalAlpha = 1;
  },
});
