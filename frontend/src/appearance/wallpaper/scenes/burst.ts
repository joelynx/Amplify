/**
 * Comic burst: radiating wedges and speed lines from an off-centre focus,
 * over halftone dots that grow towards the edges. Static.
 */

import { TAU, css, mix, range, rng, smoothstep } from "../kit";
import { defineScene } from "../types";

export const burst = defineScene({
  animated: false,
  resolution: (dpr) => Math.min(dpr, 1.5),
  init: () => ({}),
  draw(ctx, _s, env) {
    const { pal, w, h } = env;
    const r = rng(99);
    const fx = w * 0.7;
    const fy = h * 0.32;
    const R = Math.hypot(w, h);

    // Alternating wedges.
    const N = 32;
    ctx.fillStyle = css(mix(pal.background, pal.accent, pal.dark ? 0.25 : 0.4));
    ctx.beginPath();
    for (let i = 0; i < N; i += 2) {
      const a0 = (i / N) * TAU + range(r, -0.03, 0.03);
      const a1 = ((i + 1) / N) * TAU + range(r, -0.03, 0.03);
      ctx.moveTo(fx, fy);
      ctx.lineTo(fx + Math.cos(a0) * R, fy + Math.sin(a0) * R);
      ctx.lineTo(fx + Math.cos(a1) * R, fy + Math.sin(a1) * R);
      ctx.closePath();
    }
    ctx.fill();

    // Halftone on a staggered grid, larger away from the focus.
    const step = Math.max(8, 14 * env.unit);
    ctx.fillStyle = css(pal.primary, pal.dark ? 0.35 : 0.28);
    ctx.beginPath();
    for (let row = 0, y = 0; y < h + step; row++, y += step * 0.866) {
      for (let x = row % 2 ? step / 2 : 0; x < w + step; x += step) {
        const d = Math.hypot(x - fx, y - fy) / (R * 0.75);
        const rad = step * 0.48 * smoothstep(0.15, 1, d);
        if (rad < 0.4) continue;
        ctx.moveTo(x + rad, y);
        ctx.arc(x, y, rad, 0, TAU);
      }
    }
    ctx.fill();

    // Speed lines: thin wedges pointing at the focus.
    ctx.fillStyle = css(pal.text, pal.dark ? 0.3 : 0.22);
    ctx.beginPath();
    for (let i = 0; i < 44; i++) {
      const a = r() * TAU;
      const r0 = range(r, 0.09, 0.2) * R;
      const half = (range(r, 3, 8) * Math.max(0.6, env.unit)) / R;
      ctx.moveTo(fx + Math.cos(a) * r0, fy + Math.sin(a) * r0);
      ctx.lineTo(fx + Math.cos(a - half) * R, fy + Math.sin(a - half) * R);
      ctx.lineTo(fx + Math.cos(a + half) * R, fy + Math.sin(a + half) * R);
      ctx.closePath();
    }
    ctx.fill();
  },
});
