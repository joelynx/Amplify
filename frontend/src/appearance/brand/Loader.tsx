/**
 * Loading animations made from the ampliφ matrix (Makeover.md §4):
 *   sweep   amp → li → φ light up in turn (the default loop)
 *   reduce  off-diagonal variables are eliminated row by row (Gaussian elimination)
 *   build   brackets open, zeros pop in, the diagonal types itself; plays once, on the boot screen
 * and the φ coin as the small spinner for buttons and inline status.
 * The `loader` slot picks the looping one. With reduced motion the static
 * logo / φ is shown instead.
 */

import { useEffect, useRef } from "react";

import { cn } from "../../lib/cn";
import { resolve } from "../registry";
import { motionReduced, useAppearance } from "../store";
import { LOGOS } from "./logoData";
import { LogoSvg, useLogoVariant, type LogoVariant } from "./Logo";

export type LoopKind = "sweep" | "reduce";

function useLoopKind(): LoopKind {
  // Select the (stable) item, not a fresh object: zustand re-renders on every new reference.
  const item = useAppearance((s) => resolve(s.loadout, "loader"));
  return (item?.data as { big?: LoopKind } | undefined)?.big ?? "sweep";
}

function useReduced(): boolean {
  return useAppearance((s) => motionReduced(s.settings));
}

function animatedVariant(v: LogoVariant): Exclude<LogoVariant, "pixel" | "terminal"> {
  if (v === "pixel") return "tinted";
  if (v === "terminal") return "mono";
  return v;
}

function loop(el: Element | null, frames: Keyframe[], duration: number): Animation | null {
  if (!el || !("animate" in el)) return null;
  return (el as HTMLElement).animate(frames, { duration, iterations: Infinity, easing: "linear" });
}

function once(el: Element | null, frames: Keyframe[], duration: number): Animation | null {
  if (!el || !("animate" in el)) return null;
  return (el as HTMLElement).animate(frames, { duration, easing: "linear", fill: "both" });
}

function prepare(el: Element | null): void {
  const s = (el as SVGElement | null)?.style;
  if (s) {
    s.transformBox = "fill-box";
    s.transformOrigin = "center";
  }
}

/** The matrix builds itself once and holds the finished logo (the boot screen). */
export function animateBuild(svg: SVGSVGElement, T = 2000): Animation[] {
  const out: (Animation | null)[] = [];
  const end: Keyframe = { offset: 1, opacity: 1 };
  svg.querySelectorAll(".br").forEach((b) => {
    prepare(b);
    out.push(once(b, [
      { offset: 0, transform: "scaleY(0)", opacity: 0 },
      { offset: 0.13, transform: "scaleY(1)", opacity: 1, easing: "ease-out" },
      { ...end, transform: "scaleY(1)" },
    ], T));
  });
  const wave: Record<string, number> = { z21: 0, z12: 0, z31: 1, z13: 1, z32: 2, z23: 2 };
  for (const [c, w] of Object.entries(wave)) {
    const el = svg.querySelector(`.${c}`);
    prepare(el);
    const t0 = 0.16 + w * 0.067;
    out.push(once(el, [
      { offset: 0, opacity: 0, transform: "scale(0)" },
      { offset: t0, opacity: 0, transform: "scale(0)" },
      { offset: t0 + 0.067, opacity: 1, transform: "scale(1.15)" },
      { offset: t0 + 0.1, opacity: 1, transform: "scale(1)" },
      { ...end, transform: "scale(1)" },
    ], T));
  }
  // amp(z), li(x), φ(n) type themselves in; the last letter lands just before the end.
  let t = 0.42;
  for (const d of ["1", "2", "3"]) {
    svg.querySelectorAll(`.d${d} .ch, .s${d} .ch`).forEach((ch) => {
      out.push(once(ch, [{ offset: 0, opacity: 0 }, { offset: t, opacity: 0 }, { offset: t + 0.028, opacity: 1 }, end], T));
      t += 0.031;
    });
    t += 0.034;
  }
  return out.filter((a): a is Animation => !!a);
}

export function animateReduce(svg: SVGSVGElement, T = 3600): Animation[] {
  const out: (Animation | null)[] = [];
  const rows: [number, string[], number][] = [[2, ["21", "23"], 0.1], [3, ["31", "32"], 0.38], [1, ["12", "13"], 0.66]];
  const ys: Record<number, number> = { 1: 4, 2: 60, 3: 116 };
  const bar: Keyframe[] = [{ offset: 0, opacity: 0, transform: `translateY(${ys[2]}px)` }];
  for (const [r, cells, t0] of rows) {
    const tr = `translateY(${ys[r]}px)`;
    bar.push({ offset: t0, opacity: 0, transform: tr }, { offset: t0 + 0.04, opacity: 1, transform: tr },
      { offset: t0 + 0.2, opacity: 1, transform: tr }, { offset: t0 + 0.24, opacity: 0, transform: tr });
    for (const c of cells) {
      const sw = t0 + 0.12;
      out.push(loop(svg.querySelector(`.v${c}`), [{ offset: 0, opacity: 1 }, { offset: sw, opacity: 1 },
        { offset: sw + 0.05, opacity: 0 }, { offset: 0.95, opacity: 0 }, { offset: 1, opacity: 1 }], T));
      out.push(loop(svg.querySelector(`.z${c}`), [{ offset: 0, opacity: 0 }, { offset: sw, opacity: 0 },
        { offset: sw + 0.05, opacity: 1 }, { offset: 0.95, opacity: 1 }, { offset: 1, opacity: 0 }], T));
    }
  }
  bar.push({ offset: 1, opacity: 0, transform: `translateY(${ys[1]}px)` });
  out.push(loop(svg.querySelector(".rowbar"), bar, T));
  return out.filter((a): a is Animation => !!a);
}

/** The looping matrix loader. `kind` forces an animation; otherwise the loader slot decides. */
export function MatrixLoader({ kind, className, label = "Loading" }: { kind?: LoopKind; className?: string; label?: string }) {
  const slot = useLoopKind();
  const big = kind ?? slot;
  const reduced = useReduced();
  const variant = animatedVariant(useLogoVariant());
  const ref = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const svg = ref.current;
    if (!svg || reduced || big !== "reduce") return;
    const anims = animateReduce(svg);
    return () => anims.forEach((a) => a.cancel());
  }, [big, reduced, variant]);

  return (
    <div className={cn("amp-loader", className)} role="status" aria-label={label}>
      <LogoSvg
        name="matrix"
        variant={variant}
        svgRef={ref}
        reduce={big === "reduce" && !reduced}
        className={reduced ? "" : big === "sweep" ? "ld-sweep" : ""}
      />
    </div>
  );
}

/**
 * The φ coin: the small spinner for buttons and inline status, sized by
 * className (h-4 w-4 …). Coloured like the φ of the theme's logo variant;
 * inside a button it takes the button's text colour.
 */
export function Spinner({ className }: { className?: string }) {
  const reduced = useReduced();
  const variant = useLogoVariant();
  return (
    <svg className={cn("amp-phi", `v-${variant}`, !reduced && "spin", className)} viewBox="0 -26 23.5 35" role="status" aria-label="Loading">
      <path d={LOGOS.matrix.glyphs["glyph-3-0"]} />
    </svg>
  );
}

function prefersReducedMotion(): boolean {
  return typeof window !== "undefined" && !!window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
}

/**
 * Boot screen: the matrix builds itself once and stays. `onDone` fires when
 * the build has finished (straight away with reduced motion, or on a click
 * or key press), so the app can keep the screen up until then. Settings are
 * not loaded yet, so it always uses the original logo; main.tsx has already
 * put the saved palette (light or dark) on <html>.
 */
export function BootScreen({ message, onDone }: { message: string; onDone?: () => void }) {
  const ref = useRef<SVGSVGElement>(null);
  const done = useRef(onDone);
  done.current = onDone;

  useEffect(() => {
    let finished = false;
    const finish = () => {
      if (finished) return;
      finished = true;
      done.current?.();
    };
    const svg = ref.current;
    if (!svg || prefersReducedMotion()) {
      finish();
      return;
    }
    const anims = animateBuild(svg);
    let hold: ReturnType<typeof setTimeout> | undefined;
    Promise.all(anims.map((a) => a.finished))
      .then(() => {
        hold = setTimeout(finish, 350);
      })
      .catch(() => undefined);
    const skip = () => {
      anims.forEach((a) => a.finish());
      finish();
    };
    window.addEventListener("pointerdown", skip, { once: true });
    window.addEventListener("keydown", skip, { once: true });
    return () => {
      clearTimeout(hold);
      anims.forEach((a) => a.cancel());
      window.removeEventListener("pointerdown", skip);
      window.removeEventListener("keydown", skip);
    };
  }, []);

  return (
    <main className="flex h-full flex-col items-center justify-center gap-4">
      <div className="amp-loader w-40" role="status" aria-label={message}>
        <LogoSvg name="matrix" variant="original" svgRef={ref} />
      </div>
      <p className="text-xs tracking-wide text-muted">{message}</p>
    </main>
  );
}
