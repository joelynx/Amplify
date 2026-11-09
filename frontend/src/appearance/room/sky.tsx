/**
 * The view through a window: sky colour, sun or moon and stars by time of day;
 * hills, a tree and weather by season. Drawn into a rectangle; the caller
 * clips it to the window shape.
 */

import type { CSSProperties, ReactNode } from "react";

import { hashString, seeded, type Season, type TimeOfDay } from "./helpers";
import type { ArtCtx } from "./model";
import { C, E, Ln, P, R, mix } from "./svg";

export const SKY: Record<TimeOfDay, [string, string, string]> = {
  dawn: ["#7b86c6", "#f2a487", "#fde0b6"],
  day: ["#4c9de6", "#8ac6f3", "#d6eefc"],
  dusk: ["#2b2861", "#9c4f86", "#f29b5e"],
  night: ["#060a20", "#111a43", "#232d5c"],
};

export const HILLS: Record<Season, [string, string]> = {
  spring: ["#a5d08a", "#7cb562"],
  summer: ["#79b45a", "#56913f"],
  autumn: ["#d2a95a", "#ad7a3c"],
  winter: ["#eef3f9", "#d3deeb"],
};

const SHADE: Record<TimeOfDay, number> = { dawn: 14, day: 0, dusk: 30, night: 60 };

/** A colour as it looks at this time of day (darker at night). */
export function shade(color: string, tod: TimeOfDay): string {
  const s = SHADE[tod];
  return s ? mix(color, 100 - s, "#0a0f2c") : color;
}

export const CROWN: Record<Season, string[]> = {
  spring: ["#7fbf6a", "#93cc78", "#f6b8cb"],
  summer: ["#4f9a3f", "#5fae4a", "#3f8434"],
  autumn: ["#e07a2e", "#c9452f", "#e8b03a"],
  winter: [],
};

export function fallStyle(dur: number, delay: number, fall: number, dx: number): CSSProperties {
  return {
    animationDuration: `${dur}s`,
    animationDelay: `${delay}s`,
    ["--fall" as string]: `${fall}px`,
    ["--dx" as string]: `${dx}px`,
  } as CSSProperties;
}

interface SkyProps {
  c: ArtCtx;
  x: number;
  y: number;
  w: number;
  h: number;
  /** Unique per sky in a scene (defs ids). */
  name?: string;
  /** Hills and tree. */
  land?: boolean;
  /** Fraction of the height where the hills start. */
  horizon?: number;
  /** Tree height as a fraction of the sky height. */
  tree?: number;
  /** Always show some stars (observatory slit). */
  starry?: boolean;
  /** Snow, leaves, petals, fireflies. */
  weather?: boolean;
  /** Sun/moon position as fractions of the width and of the sky above the hills. */
  body?: [number, number];
  /** Sun/moon radius as a fraction of the smaller side. */
  bodySize?: number;
}

export function Sky({ c, x, y, w, h, name = "sky", land = true, horizon = 0.68, tree = 0.42, starry = false, weather = true, body: bodyAt, bodySize }: SkyProps) {
  const { tod, season } = c;
  const g = SKY[tod];
  const rnd = seeded(hashString(name) + Math.round(w * 7 + h));
  const hy = y + h * (land ? horizon : 1);
  const night = tod === "night";

  const starAlpha = night ? 0.95 : tod === "dusk" || tod === "dawn" ? 0.35 : starry ? 0.25 : 0;
  const nStars = Math.round((w * (hy - y)) / (starry ? 700 : 1300));
  const stars = Array.from({ length: nStars }, () => ({
    x: x + rnd() * w,
    y: y + rnd() * (hy - y) * 0.92,
    r: 0.6 + rnd() * 1.1,
    d: rnd() * 3,
  }));

  const big = Math.min(w, h);
  let body: ReactNode = null;
  if (night) {
    const mx = x + w * (bodyAt?.[0] ?? 0.26);
    const my = y + (hy - y) * (bodyAt?.[1] ?? 0.28);
    const r = Math.max(6, big * (bodySize ?? 0.08));
    body = (
      <g>
        <defs>
          <mask id={c.id(`${name}-moon`)}>
            <circle cx={mx} cy={my} r={r} fill="#fff" />
            <circle cx={mx + r * 0.45} cy={my - r * 0.2} r={r * 0.85} fill="#000" />
          </mask>
        </defs>
        <C cx={mx} cy={my} r={r * 2.4} f="#f4f1de" o={0.06} />
        <circle cx={mx} cy={my} r={r} mask={c.url(`${name}-moon`)} style={{ fill: "#f4f1de" }} />
      </g>
    );
  } else {
    const pos: Record<Exclude<TimeOfDay, "night">, [number, number, string]> = {
      dawn: [0.22, 0.78, "#ffd59a"],
      day: [0.72, 0.22, "#fff3b0"],
      dusk: [0.8, 0.8, "#ff9b54"],
    };
    const [fx, fy, col] = pos[tod];
    const sx = x + w * (bodyAt?.[0] ?? fx);
    const sy = y + (hy - y) * (bodyAt?.[1] ?? fy);
    const r = Math.max(6, big * (bodySize ?? 0.075));
    body = (
      <g>
        <C cx={sx} cy={sy} r={r * 2.6} f={col} o={0.18} />
        <C cx={sx} cy={sy} r={r * 1.6} f={col} o={0.3} />
        <C cx={sx} cy={sy} r={r} f={col} />
      </g>
    );
  }

  const cloudCol = tod === "day" ? "#ffffff" : tod === "dawn" ? "#ffe3d1" : tod === "dusk" ? "#d9a0b8" : "#3a4470";
  const clouds = [0.18, 0.62].map((fx, i) => {
    const cx = x + w * fx;
    const cy = y + (hy - y) * (0.3 + i * 0.18);
    const s = big * 0.05;
    return (
      <g key={i} className="rm-drift" style={{ animationDelay: `${-i * 17}s` }} opacity={night ? 0.5 : 0.85}>
        <E cx={cx} cy={cy} rx={s * 2.2} ry={s * 0.8} f={cloudCol} />
        <E cx={cx - s * 0.9} cy={cy - s * 0.4} rx={s} ry={s * 0.8} f={cloudCol} />
        <E cx={cx + s * 0.6} cy={cy - s * 0.6} rx={s * 1.2} ry={s} f={cloudCol} />
      </g>
    );
  });

  const [farHill, nearHill] = HILLS[season];
  const hills = land ? (
    <g>
      <P
        d={`M${x} ${hy} C${x + w * 0.25} ${hy - h * 0.09} ${x + w * 0.5} ${hy + h * 0.04} ${x + w * 0.75} ${hy - h * 0.05} S${x + w} ${hy - h * 0.02} ${x + w} ${hy - h * 0.02} V${y + h} H${x} Z`}
        f={shade(farHill, tod)}
      />
      <P
        d={`M${x} ${hy + h * 0.16} C${x + w * 0.3} ${hy + h * 0.06} ${x + w * 0.6} ${hy + h * 0.2} ${x + w} ${hy + h * 0.1} V${y + h} H${x} Z`}
        f={shade(nearHill, tod)}
      />
      {season === "spring" &&
        Array.from({ length: Math.round(w / 14) }, (_, i) => (
          <C key={i} cx={x + rnd() * w} cy={hy + h * (0.2 + rnd() * 0.12)} r={1.2} f={shade(i % 2 ? "#fff6a8" : "#f7b6c8", tod)} />
        ))}
    </g>
  ) : null;

  const treeEl = land && tree > 0 ? <Tree c={c} x={x + w * 0.8} base={y + h} size={h * tree} rnd={rnd} /> : null;

  return (
    <g>
      <defs>
        <linearGradient id={c.id(`${name}-g`)} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={g[0]} />
          <stop offset="0.6" stopColor={g[1]} />
          <stop offset="1" stopColor={g[2]} />
        </linearGradient>
      </defs>
      <rect x={x} y={y} width={w} height={h} style={{ fill: c.url(`${name}-g`) }} />
      {starAlpha > 0 && (
        <g opacity={starAlpha}>
          {stars.map((s, i) => (
            <C key={i} cx={s.x} cy={s.y} r={s.r} f="#fffbe8" cls={i % 3 === 0 ? "rm-twinkle" : undefined} style={{ animationDelay: `${-s.d}s` }} />
          ))}
        </g>
      )}
      {body}
      {tod !== "night" && clouds}
      {hills}
      {treeEl}
      {weather && <Weather c={c} x={x} y={y} w={w} h={h} rnd={rnd} />}
    </g>
  );
}

function Tree({ c, x, base, size, rnd }: { c: ArtCtx; x: number; base: number; size: number; rnd: () => number }) {
  const { tod, season } = c;
  const trunk = shade("#6b4a33", tod);
  const tw = size * 0.08;
  const top = base - size;
  const crownY = top + size * 0.32;
  const r = size * 0.3;
  const cols = CROWN[season];
  return (
    <g>
      <P d={`M${x - tw} ${base} L${x - tw * 0.6} ${crownY} L${x + tw * 0.6} ${crownY} L${x + tw} ${base} Z`} f={trunk} />
      {season === "winter" ? (
        <g>
          {[
            [-0.9, -0.6],
            [0.8, -0.7],
            [-0.5, -1.1],
            [0.4, -1.15],
            [0, -1.3],
          ].map(([dx, dy], i) => (
            <g key={i}>
              <Ln x1={x} y1={crownY + r * 0.4} x2={x + dx * r} y2={crownY + dy * r * 0.7} s={trunk} sw={Math.max(1, tw * 0.5)} />
              <C cx={x + dx * r} cy={crownY + dy * r * 0.7 - 1} r={Math.max(1.2, tw * 0.45)} f={shade("#ffffff", tod)} />
            </g>
          ))}
        </g>
      ) : (
        <g>
          {[
            [0, -0.25, 1],
            [-0.55, 0.1, 0.75],
            [0.55, 0.12, 0.75],
            [-0.25, -0.6, 0.7],
            [0.3, -0.55, 0.7],
          ].map(([dx, dy, s], i) => (
            <C key={i} cx={x + dx * r} cy={crownY + dy * r} r={r * s} f={shade(cols[i % 2], tod)} />
          ))}
          {(season === "spring" || season === "autumn") &&
            Array.from({ length: 14 }, (_, i) => {
              const a = rnd() * Math.PI * 2;
              const d = rnd() * r * 1.05;
              return (
                <C
                  key={i}
                  cx={x + Math.cos(a) * d}
                  cy={crownY - r * 0.2 + Math.sin(a) * d * 0.8}
                  r={Math.max(1.2, r * 0.12)}
                  f={shade(season === "spring" ? cols[2] : cols[i % 3], tod)}
                />
              );
            })}
        </g>
      )}
    </g>
  );
}

export function Weather({ c, x, y, w, h, rnd }: { c: ArtCtx; x: number; y: number; w: number; h: number; rnd: () => number }) {
  const { season, tod, motion } = c;
  if (season === "summer") {
    if (tod === "night") {
      return (
        <g>
          {Array.from({ length: Math.max(3, Math.round(w / 40)) }, (_, i) => (
            <C
              key={i}
              cx={x + rnd() * w}
              cy={y + h * (0.6 + rnd() * 0.35)}
              r={1.6}
              f="#e9ff8a"
              cls="rm-twinkle"
              style={{ animationDelay: `${-rnd() * 3}s`, animationDuration: "2.6s" }}
            />
          ))}
        </g>
      );
    }
    return (
      <g>
        {[0.3, 0.42].map((fx, i) => {
          const bx = x + w * fx;
          const by = y + h * (0.22 + i * 0.07);
          const s = Math.max(3, w * 0.018);
          return <P key={i} d={`M${bx - s} ${by} Q${bx - s / 2} ${by - s * 0.6} ${bx} ${by} Q${bx + s / 2} ${by - s * 0.6} ${bx + s} ${by}`} s={shade("#3b3b4a", tod)} sw={1.2} f="none" />;
        })}
      </g>
    );
  }
  // Capped so a wall-sized sky stays cheap to animate.
  const n = Math.min(season === "winter" ? 36 : 18, Math.round(w / (season === "winter" ? 10 : 28)));
  const col =
    season === "winter" ? "#ffffff" : season === "spring" ? "#f7c1d2" : undefined;
  const autumn = ["#e07a2e", "#c9452f", "#e8b03a"];
  return (
    <g>
      {Array.from({ length: n }, (_, i) => {
        const px = x + rnd() * w;
        const py = y + rnd() * h;
        const dur = 7 + rnd() * 6;
        const delay = -rnd() * 13;
        const dx = (rnd() - 0.5) * (season === "winter" ? 24 : 60);
        const fill = shade(col ?? autumn[i % 3], tod);
        const shape =
          season === "winter" ? (
            <C cx={0} cy={0} r={0.9 + rnd() * 1.4} f={fill} o={0.9} />
          ) : (
            <E cx={0} cy={0} rx={season === "spring" ? 1.8 : 2.6} ry={season === "spring" ? 1.2 : 1.5} f={fill} t={`rotate(${rnd() * 180})`} />
          );
        if (motion) {
          return (
            <g key={i} transform={`translate(${px} ${y - 6})`}>
              <g className="rm-fall" style={fallStyle(dur, delay, h + 12, dx)}>
                {shape}
              </g>
            </g>
          );
        }
        return (
          <g key={i} transform={`translate(${px} ${py})`}>
            {shape}
          </g>
        );
      })}
    </g>
  );
}

/** A bare window rectangle with the sky clipped into it. */
export function SkyIn({ c, x, y, w, h, name = "sky", ...rest }: SkyProps) {
  return (
    <g>
      <defs>
        <clipPath id={c.id(`${name}-clip`)}>
          <rect x={x} y={y} width={w} height={h} />
        </clipPath>
      </defs>
      <g clipPath={c.url(`${name}-clip`)}>
        <Sky c={c} x={x} y={y} w={w} h={h} name={name} {...rest} />
      </g>
      <R x={x} y={y} w={w} h={h} f="none" />
    </g>
  );
}
