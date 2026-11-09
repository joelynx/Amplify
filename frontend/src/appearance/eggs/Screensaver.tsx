/**
 * Idle screensaver: the club's inline logo drifts around a dimmed screen
 * like an old DVD player, changing tint at every wall. A corner hit calls
 * `onCorner`. Animates with requestAnimationFrame only while visible.
 */

import { type CSSProperties, useEffect, useRef } from "react";

import { Logo } from "../brand/Logo";
import { stepBounce, type Bouncer } from "./detectors";

const SPEED = 110;
const CORNER_COOLDOWN_MS = 1500;

export function Screensaver({ onCorner }: { onCorner: () => void }) {
  const boxRef = useRef<HTMLDivElement>(null);
  const cornerRef = useRef(onCorner);
  useEffect(() => {
    cornerRef.current = onCorner;
  });

  useEffect(() => {
    const el = boxRef.current;
    if (!el) return;
    let { width: w, height: h } = el.getBoundingClientRect();
    let hue = Math.floor(Math.random() * 360);
    let b: Bouncer = {
      x: Math.random() * Math.max(0, window.innerWidth - w),
      y: Math.random() * Math.max(0, window.innerHeight - h),
      vx: (Math.random() < 0.5 ? -1 : 1) * SPEED,
      vy: (Math.random() < 0.5 ? -1 : 1) * SPEED * 0.82,
    };
    let lastCorner = 0;
    let raf = 0;
    let last = 0;

    const paint = () => {
      el.style.transform = `translate3d(${b.x.toFixed(1)}px, ${b.y.toFixed(1)}px, 0)`;
      el.style.setProperty("--primary", `hsl(${hue} 85% 60%)`);
    };

    const frame = (t: number) => {
      const dt = last ? Math.min(0.05, (t - last) / 1000) : 0;
      last = t;
      const step = stepBounce(b, dt, w, h, window.innerWidth, window.innerHeight);
      b = step.next;
      if (step.hitX || step.hitY) hue = (hue + 60 + Math.floor(Math.random() * 120)) % 360;
      if (step.corner && t - lastCorner > CORNER_COOLDOWN_MS) {
        lastCorner = t;
        cornerRef.current();
      }
      paint();
      raf = requestAnimationFrame(frame);
    };

    const start = () => {
      if (raf || document.hidden) return;
      last = 0;
      raf = requestAnimationFrame(frame);
    };
    const stop = () => {
      cancelAnimationFrame(raf);
      raf = 0;
    };
    const onVis = () => (document.hidden ? stop() : start());
    const onResize = () => {
      ({ width: w, height: h } = el.getBoundingClientRect());
    };

    paint();
    start();
    document.addEventListener("visibilitychange", onVis);
    window.addEventListener("resize", onResize);
    return () => {
      stop();
      document.removeEventListener("visibilitychange", onVis);
      window.removeEventListener("resize", onResize);
    };
  }, []);

  // The tinted variant draws in --primary and --text; pin them for the dark backdrop.
  const vars = { "--text": "#f2f2f2", "--muted": "#9a9a9a", "--surface": "#1c1c1c" } as CSSProperties;
  return (
    <div className="amp-egg-saver" aria-hidden="true">
      <div ref={boxRef} className="bouncer" style={vars}>
        <Logo name="inline" variant="tinted" style={{ width: "100%" }} />
      </div>
    </div>
  );
}
