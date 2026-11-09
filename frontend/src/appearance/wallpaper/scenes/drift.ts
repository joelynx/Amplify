/**
 * Particle wallpapers: falling leaves, sakura petals, rising embers over a
 * warm vignette, drifting chalk dust over an erased board, rain on glass and
 * falling columns of maths glyphs.
 */

import {
  BLACK,
  TAU,
  WHITE,
  css,
  glowSprite,
  mix,
  parseColor,
  pathLeaf,
  pathPetal,
  pick,
  range,
  type Palette,
  type Rgb,
} from "../kit";
import { defineScene, layer, scatter, vGradient, type SceneEnv } from "../types";

const hex = (s: string): Rgb => parseColor(s) ?? WHITE;

/* ------------------------------------------------------------------ */
/* Leaves and petals                                                    */
/* ------------------------------------------------------------------ */

interface Flake {
  x: number;
  y: number;
  size: number;
  vy: number;
  vx: number;
  amp: number;
  f: number;
  ph: number;
  rot: number;
  vr: number;
  flip: number;
  color: string;
}

interface DrifterSpec {
  perMpx: number;
  size: [number, number];
  fall: [number, number];
  wind: [number, number];
  colors(pal: Palette): string[];
  draw(ctx: CanvasRenderingContext2D, f: Flake, t: number): void;
}

function drifter(spec: DrifterSpec) {
  const spawn = (env: SceneEnv, colors: string[], anywhere: boolean): Flake => {
    const r = env.rand;
    const u = env.unit;
    return {
      x: range(r, -0.1, 1.05) * env.w,
      y: anywhere ? r() * env.h : -range(r, 20, 80) * u,
      size: range(r, spec.size[0], spec.size[1]) * u,
      vy: range(r, spec.fall[0], spec.fall[1]) * u,
      vx: range(r, spec.wind[0], spec.wind[1]) * u,
      amp: range(r, 15, 50) * u,
      f: range(r, 0.3, 0.8),
      ph: r() * TAU,
      rot: r() * TAU,
      vr: range(r, -1, 1),
      flip: range(r, 0.6, 1.6),
      color: pick(r, colors),
    };
  };
  return defineScene({
    animated: true,
    fps: 30,
    init(env) {
      const colors = spec.colors(env.pal);
      const list = Array.from({ length: scatter(env, spec.perMpx, 5, 80) }, () => spawn(env, colors, true));
      return { list, colors };
    },
    draw(ctx, s, env, t, dt) {
      const k = env.scale;
      for (let i = 0; i < s.list.length; i++) {
        const f = s.list[i];
        f.y += f.vy * dt;
        f.x += f.vx * dt;
        f.rot += f.vr * dt;
        const x = f.x + Math.sin(t * f.f + f.ph) * f.amp;
        if (f.y > env.h + 30 || x > env.w + 40) {
          s.list[i] = spawn(env, s.colors, false);
          continue;
        }
        const c = Math.cos(f.rot) * k;
        const sn = Math.sin(f.rot) * k;
        ctx.setTransform(c, sn, -sn, c, x * k, f.y * k);
        spec.draw(ctx, f, t);
      }
      ctx.setTransform(k, 0, 0, k, 0, 0);
    },
  });
}

export const leaves = drifter({
  perMpx: 24,
  size: [12, 22],
  fall: [18, 40],
  wind: [-4, 10],
  colors: (p) => [p.success, p.warning, p.accent, hex("#c96a28"), hex("#d4a017"), hex("#8fae3c")].map((c) => css(c)),
  draw(ctx, f, t) {
    ctx.scale(1, Math.max(0.2, Math.abs(Math.cos(t * f.flip + f.ph))));
    ctx.fillStyle = f.color;
    pathLeaf(ctx, f.size);
    ctx.fill();
    ctx.strokeStyle = "rgba(0,0,0,0.22)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(-f.size, 0);
    ctx.lineTo(f.size * 0.8, 0);
    ctx.stroke();
  },
});

export const petals = drifter({
  perMpx: 32,
  size: [8, 14],
  fall: [16, 34],
  wind: [8, 26],
  colors: (p) => ["#f8b7cd", "#ffd3e0", "#f4a6c0", css(mix(p.primary, WHITE, 0.45)), css(mix(p.accent, WHITE, 0.55))],
  draw(ctx, f, t) {
    ctx.scale(Math.max(0.2, Math.abs(Math.cos(t * f.flip + f.ph))), 1);
    ctx.fillStyle = f.color;
    pathPetal(ctx, f.size);
    ctx.fill();
    ctx.globalAlpha = 0.3;
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(-f.size * 0.6, 0);
    ctx.lineTo(f.size * 0.55, 0);
    ctx.stroke();
    ctx.globalAlpha = 1;
  },
});

/* ------------------------------------------------------------------ */
/* Embers                                                               */
/* ------------------------------------------------------------------ */

interface Ember {
  x: number;
  y: number;
  vy: number;
  amp: number;
  f: number;
  ph: number;
  size: number;
  color: string;
  core: string;
}

export const embers = defineScene({
  animated: true,
  fps: 30,
  init(env) {
    const { pal, w, h, rand: r } = env;
    const vignette = layer(env);
    const g = vignette.ctx;
    const edge = pal.dark ? mix(pal.background, hex("#2a0a00"), 0.55) : mix(hex("#b4501d"), pal.background, 0.35);
    const vg = g.createRadialGradient(w / 2, h * 0.45, Math.min(w, h) * 0.3, w / 2, h * 0.45, Math.hypot(w, h) * 0.62);
    vg.addColorStop(0, css(edge, 0));
    vg.addColorStop(1, css(edge, pal.dark ? 0.85 : 0.4));
    g.fillStyle = vg;
    g.fillRect(0, 0, w, h);
    g.fillStyle = vGradient(g, h * 0.55, h, [
      [0, "rgba(255,120,30,0)"],
      [1, pal.dark ? "rgba(255,110,30,0.32)" : "rgba(255,130,40,0.22)"],
    ]);
    g.fillRect(0, h * 0.55, w, h * 0.45);
    const colors = ["#ffd36b", "#ff9a3c", "#ff6a1a", "#ffe6a8"].map((c) => css(mix(hex(c), pal.accent, 0.15)));
    const cores = colors.map((c) => css(mix(parseColor(c) ?? WHITE, pal.primary, 0.3)));
    const spawn = (anywhere: boolean): Ember => {
      const i = Math.floor(r() * colors.length);
      return {
        x: r() * w,
        y: anywhere ? range(r, 0.2, 1) * h : h + range(r, 0, 40),
        vy: range(r, 20, 60) * env.unit,
        amp: range(r, 8, 28) * env.unit,
        f: range(r, 0.6, 1.6),
        ph: r() * TAU,
        size: range(r, 1.5, 3.2) * Math.max(0.6, env.unit),
        color: colors[i],
        core: cores[i],
      };
    };
    const list = Array.from({ length: scatter(env, 45, 10, 160) }, () => spawn(true));
    return { vignette, list, spawn };
  },
  back(ctx, s, env) {
    ctx.drawImage(s.vignette.canvas, 0, 0, env.w, env.h);
  },
  draw(ctx, s, env, t, dt) {
    ctx.globalCompositeOperation = env.pal.dark ? "lighter" : "source-over";
    for (let i = 0; i < s.list.length; i++) {
      const e = s.list[i];
      e.y -= e.vy * dt;
      if (e.y < -10) {
        s.list[i] = s.spawn(false);
        continue;
      }
      const x = e.x + Math.sin(t * e.f + e.ph) * e.amp;
      const rise = Math.min(1, e.y / (env.h * 0.75));
      const flicker = 0.7 + 0.3 * Math.sin(t * 2.2 + e.ph * 3);
      ctx.globalAlpha = Math.max(0, rise) * flicker;
      const d = e.size * 7;
      ctx.drawImage(glowSprite(e.color), x - d / 2, e.y - d / 2, d, d);
      if (!env.pal.dark) {
        // On light paper the white-hot core vanishes: give it a solid centre.
        ctx.fillStyle = e.core;
        ctx.beginPath();
        ctx.arc(x, e.y, e.size, 0, TAU);
        ctx.fill();
      }
    }
    ctx.globalAlpha = 1;
    ctx.globalCompositeOperation = "source-over";
  },
});

/* ------------------------------------------------------------------ */
/* Chalk dust                                                           */
/* ------------------------------------------------------------------ */

const GHOSTS = ["∫ f(x) dx", "a² + b² = c²", "∑ 1/n² = π²/6", "dy/dx", "e^{iπ} + 1 = 0", "lim x→0"];

interface Mote {
  x: number;
  y: number;
  vx: number;
  vy: number;
  r: number;
  a: number;
  f: number;
  ph: number;
}

export const chalkDust = defineScene({
  animated: true,
  fps: 24,
  init(env) {
    const { pal, w, h, rand: r } = env;
    const chalk = pal.dark ? mix(pal.text, WHITE, 0.4) : mix(pal.text, pal.background, 0.25);
    const board = layer(env);
    const g = board.ctx;
    g.lineCap = "round";
    // Eraser swipes left on the board.
    for (let i = 0, n = 3 + Math.floor(r() * 3); i < n; i++) {
      g.strokeStyle = css(chalk, range(r, 0.035, 0.06));
      g.lineWidth = range(r, 40, 80) * env.unit;
      const x0 = r() * w;
      const y0 = r() * h;
      const len = range(r, 0.2, 0.45) * w;
      g.beginPath();
      g.moveTo(x0, y0);
      g.quadraticCurveTo(x0 + len / 2, y0 + range(r, -60, 60), x0 + len, y0 + range(r, -40, 40));
      g.stroke();
    }
    // Ghosts of erased working.
    g.filter = `blur(${(1.2 * env.scale).toFixed(1)}px)`;
    g.fillStyle = css(chalk, 0.09);
    for (let i = 0, n = 3 + Math.floor(r() * 3); i < n; i++) {
      g.font = `${Math.round(range(r, 22, 40) * env.unit)}px ${pal.fontHeading}`;
      g.fillText(pick(r, GHOSTS), range(r, 0.02, 0.75) * w, range(r, 0.1, 0.95) * h);
    }
    g.filter = "none";
    const list: Mote[] = Array.from({ length: scatter(env, 40, 10, 140) }, () => {
      const big = r() < 0.12;
      return {
        x: r() * w,
        y: r() * h,
        vx: range(r, -6, 6) * env.unit,
        vy: range(r, -4, 5) * env.unit,
        r: (big ? range(r, 4, 7) : range(r, 0.8, 2.6)) * Math.max(0.6, env.unit),
        a: big ? range(r, 0.1, 0.2) : range(r, 0.35, 0.7),
        f: range(r, 0.2, 0.6),
        ph: r() * TAU,
      };
    });
    return { board, list, color: css(chalk) };
  },
  back(ctx, s, env) {
    ctx.drawImage(s.board.canvas, 0, 0, env.w, env.h);
  },
  draw(ctx, s, env, t, dt) {
    ctx.fillStyle = s.color;
    for (const m of s.list) {
      m.x += (m.vx + Math.sin(t * m.f + m.ph) * 6 * env.unit) * dt;
      m.y += (m.vy + Math.cos(t * m.f * 0.8 + m.ph) * 4 * env.unit) * dt;
      if (m.x < -10) m.x = env.w + 10;
      else if (m.x > env.w + 10) m.x = -10;
      if (m.y < -10) m.y = env.h + 10;
      else if (m.y > env.h + 10) m.y = -10;
      ctx.globalAlpha = m.a * (0.75 + 0.25 * Math.sin(t * 0.7 + m.ph));
      ctx.beginPath();
      ctx.arc(m.x, m.y, m.r, 0, TAU);
      ctx.fill();
    }
    ctx.globalAlpha = 1;
  },
});

/* ------------------------------------------------------------------ */
/* Rain on glass                                                        */
/* ------------------------------------------------------------------ */

interface Streak {
  x: number;
  y: number;
  len: number;
  v: number;
}

interface Drop {
  x: number;
  y: number;
  r: number;
  v: number;
  wait: number;
  trail: number;
}

function dropSprite(env: SceneEnv, pal: Palette): HTMLCanvasElement {
  const L = layer(env, 32, 32);
  const g = L.ctx;
  const body = g.createRadialGradient(13, 12, 1, 16, 17, 15);
  const rim = pal.dark ? mix(pal.background, BLACK, 0.4) : mix(pal.text, pal.background, 0.55);
  body.addColorStop(0, "rgba(255,255,255,0.35)");
  body.addColorStop(0.7, css(mix(pal.background, WHITE, 0.3), 0.15));
  body.addColorStop(1, css(rim, 0.75));
  g.fillStyle = body;
  g.beginPath();
  g.arc(16, 16, 14, 0, TAU);
  g.fill();
  g.fillStyle = "rgba(255,255,255,0.85)";
  g.beginPath();
  g.ellipse(11, 10, 4, 2.4, -0.6, 0, TAU);
  g.fill();
  return L.canvas;
}

export const rain = defineScene({
  animated: true,
  fps: 30,
  init(env) {
    const { pal, w, h, rand: r } = env;
    const glass = layer(env);
    const tint = pal.dark ? mix(pal.background, hex("#0a1420"), 0.35) : mix(pal.background, hex("#5b6b7d"), 0.2);
    glass.ctx.fillStyle = vGradient(glass.ctx, 0, h, [
      [0, css(tint, 0.9)],
      [1, css(tint, 0.5)],
    ]);
    glass.ctx.fillRect(0, 0, w, h);
    const streaks: Streak[] = Array.from({ length: scatter(env, 70, 15, 260) }, () => ({
      x: r() * w,
      y: r() * h,
      len: range(r, 14, 34) * env.unit,
      v: range(r, 600, 1000) * env.unit,
    }));
    const drop = (): Drop => ({
      x: r() * w,
      y: r() * h * 0.9,
      r: range(r, 4, 11) * Math.max(0.6, env.unit),
      v: 0,
      wait: range(r, 2, 14),
      trail: 0,
    });
    const drops = Array.from({ length: scatter(env, 24, 6, 80) }, drop);
    const streakColor = pal.dark ? css(mix(pal.text, WHITE, 0.3), 0.28) : css(mix(pal.muted, pal.primary, 0.2), 0.3);
    return { glass, streaks, drops, drop, sprite: dropSprite(env, pal), streakColor, trailColor: css(mix(pal.background, WHITE, 0.5), 0.18) };
  },
  back(ctx, s, env) {
    ctx.drawImage(s.glass.canvas, 0, 0, env.w, env.h);
  },
  draw(ctx, s, env, _t, dt) {
    ctx.strokeStyle = s.streakColor;
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (const st of s.streaks) {
      st.y += st.v * dt;
      st.x += st.v * 0.12 * dt;
      if (st.y > env.h + st.len) {
        st.y = -st.len - Math.random() * 60;
        st.x = Math.random() * (env.w + 60) - 60;
      }
      ctx.moveTo(st.x, st.y);
      ctx.lineTo(st.x - st.len * 0.12, st.y - st.len);
    }
    ctx.stroke();
    for (let i = 0; i < s.drops.length; i++) {
      const d = s.drops[i];
      if (d.v === 0) {
        d.wait -= dt;
        if (d.wait <= 0) d.v = range(Math.random, 30, 90) * env.unit;
      } else {
        d.y += d.v * dt;
        d.trail = Math.min(d.trail + d.v * dt, 80 * env.unit);
        if (d.y > env.h + 10) {
          s.drops[i] = s.drop();
          s.drops[i].y = -10;
          continue;
        }
        ctx.strokeStyle = s.trailColor;
        ctx.lineWidth = d.r * 0.6;
        ctx.beginPath();
        ctx.moveTo(d.x, d.y - d.trail);
        ctx.lineTo(d.x, d.y);
        ctx.stroke();
      }
      ctx.drawImage(s.sprite, d.x - d.r, d.y - d.r, d.r * 2, d.r * 2);
    }
  },
});

/* ------------------------------------------------------------------ */
/* Glyph rain                                                           */
/* ------------------------------------------------------------------ */

const GLYPHS = ["∑", "∫", "∂", "π", "φ", "∞", "0", "1", "λ", "Δ", "√", "θ"];

interface Column {
  x: number;
  head: number;
  speed: number;
  len: number;
  cells: number[];
}

function glyphAtlas(env: SceneEnv, cell: number, color: string): HTMLCanvasElement {
  const L = layer(env, cell * GLYPHS.length, cell);
  const g = L.ctx;
  g.font = `${Math.round(cell * 0.78)}px ${env.pal.fontMono}`;
  g.textAlign = "center";
  g.textBaseline = "middle";
  g.fillStyle = color;
  GLYPHS.forEach((ch, i) => g.fillText(ch, i * cell + cell / 2, cell / 2));
  return L.canvas;
}

export const glyphRain = defineScene({
  animated: true,
  fps: 20,
  init(env) {
    const { pal, w, h, rand: r } = env;
    const cell = Math.max(10, Math.round(18 * env.unit));
    const rows = Math.ceil(h / cell);
    const share = env.density === 2 ? 0.5 : 0.32;
    const cols: Column[] = [];
    const reset = (c: Column, anywhere: boolean) => {
      c.len = 6 + Math.floor(r() * 12);
      c.speed = range(r, 3, 8);
      c.head = anywhere ? range(r, -c.len, rows) : -range(r, 0, rows * 0.6);
    };
    for (let i = 0, n = Math.ceil(w / cell); i < n; i++) {
      if (r() > share) continue;
      const c: Column = { x: i * cell, head: 0, speed: 0, len: 0, cells: Array.from({ length: rows + 1 }, () => Math.floor(r() * GLYPHS.length)) };
      reset(c, true);
      cols.push(c);
    }
    const head = pal.dark ? css(mix(pal.primary, WHITE, 0.55)) : css(mix(pal.primary, pal.text, 0.35));
    return { cell, rows, cols, reset, body: glyphAtlas(env, cell, css(pal.primary)), headAtlas: glyphAtlas(env, cell, head) };
  },
  draw(ctx, s, env, _t, dt) {
    const { cell, rows } = s;
    const src = cell * env.scale;
    for (const c of s.cols) {
      c.head += c.speed * dt;
      if (c.head - c.len > rows) s.reset(c, false);
      if (Math.random() < dt * 0.8) c.cells[Math.floor(Math.random() * c.cells.length)] = Math.floor(Math.random() * GLYPHS.length);
      const top = Math.floor(c.head);
      for (let k = 0; k < c.len; k++) {
        const row = top - k;
        if (row < 0 || row > rows) continue;
        ctx.globalAlpha = 0.85 * (1 - k / c.len) ** 1.5;
        const gi = c.cells[row];
        ctx.drawImage(k === 0 ? s.headAtlas : s.body, gi * src, 0, src, src, c.x, row * cell, cell, cell);
      }
    }
    ctx.globalAlpha = 1;
  },
});
