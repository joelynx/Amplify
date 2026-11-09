/**
 * Furniture for the illustrated room themes (study, library, observatory,
 * greenhouse, dorm). Each part draws into a rectangle and takes a material
 * set, so a theme re-skins the same objects with its own woods, metals and
 * palette tints. Live data (books, trophies, plant, sticky notes) comes in
 * through the ArtCtx.
 */

import type { ReactNode } from "react";

import {
  PLANT_STAGES,
  chartBars,
  clockHands,
  layoutBooks,
  noteLines,
  relativeDay,
  seeded,
  type Shelf,
} from "./helpers";
import type { ArtCtx, Rect } from "./model";
import { SkyIn } from "./sky";
import { C, ClubLogo, E, Ln, P, R, Tx, mix } from "./svg";

export const FLOOR = 440;

/** Shared positions: the same hotspots in every illustrated theme. */
export const L = {
  door: { x: 40, y: 150, w: 130, h: 290 },
  pennant: { x: 48, y: 48, w: 132, h: 78 },
  noticeboard: { x: 190, y: 92, w: 170, h: 124 },
  window: { x: 390, y: 60, w: 190, h: 180 },
  chart: { x: 610, y: 60, w: 122, h: 94 },
  trophies: { x: 604, y: 166, w: 132, h: 52 },
  bookcase: { x: 758, y: 70, w: 170, h: 370 },
  desk: { x: 290, y: 328, w: 360, h: 112 },
  lamp: { x: 300, y: 222, w: 104, h: 106 },
  mug: { x: 438, y: 268, w: 64, h: 60 },
  printer: { x: 516, y: 264, w: 120, h: 64 },
  cabinet: { x: 662, y: 288, w: 84, h: 152 },
  plant: { x: 184, y: 250, w: 104, h: 190 },
} as const satisfies Record<string, Rect>;

export interface Mat {
  wall: string;
  wallLow: string;
  rail: string;
  floor: string;
  floorLine: string;
  wood: string;
  woodDark: string;
  woodLight: string;
  /** Door and window frames. */
  trim: string;
  metal: string;
  paper: string;
  cork: string;
  ink: string;
  pot: string;
  rug: string;
  rugEdge: string;
  /** Lamp shade / body. */
  shade: string;
}

export const SPINES = [
  mix("var(--primary)", 78, "#1b1b1b"),
  mix("var(--secondary)", 75, "#1b1b1b"),
  mix("var(--accent)", 72, "#1b1b1b"),
  mix("var(--success)", 70, "#1b1b1b"),
  mix("var(--warning)", 62, "#3a2208"),
  mix("var(--error)", 72, "#1b1b1b"),
  "#7a3b2e",
  "#2f4f5f",
];

export const STICKY = ["#fde68a", "#fbcfe8", "#bfdbfe", "#bbf7d0"];
export const LEAF = mix("var(--success)", 40, "#4c8b3a");
export const LEAF_DARK = mix("var(--success)", 30, "#2f6526");
export const PETAL = mix("var(--accent)", 55, "#f49ac1");

/* ------------------------------------------------------------------ */
/* Wall and floor                                                       */
/* ------------------------------------------------------------------ */

export function Wall({ c, m, wainscot = true, stripes = true }: { c: ArtCtx; m: Mat; wainscot?: boolean; stripes?: boolean }) {
  return (
    <g aria-hidden="true">
      <R x={0} y={0} w={960} h={FLOOR} f={m.wall} />
      {stripes && (
        <>
          <defs>
            <pattern id={c.id("stripes")} width="24" height="24" patternUnits="userSpaceOnUse">
              <rect x="0" y="0" width="12" height="24" style={{ fill: "#000", opacity: 0.035 }} />
            </pattern>
          </defs>
          <rect x={0} y={0} width={960} height={FLOOR} style={{ fill: c.url("stripes") }} />
        </>
      )}
      {c.backdrop && <image href={c.backdrop} x={0} y={0} width={960} height={FLOOR} preserveAspectRatio="xMidYMid slice" />}
      {wainscot && (
        <>
          <R x={0} y={334} w={960} h={FLOOR - 334} f={m.wallLow} />
          {Array.from({ length: 16 }, (_, i) => (
            <R key={i} x={i * 60 + 8} y={346} w={44} h={74} rx={2} f="none" s="#000" sw={1} o={0.08} />
          ))}
          <R x={0} y={328} w={960} h={8} f={m.rail} />
          <R x={0} y={328} w={960} h={2} f="#fff" o={0.15} />
        </>
      )}
      <R x={0} y={FLOOR - 12} w={960} h={12} f={m.woodDark} />
    </g>
  );
}

export type FloorKind = "planks" | "tiles" | "carpet" | "plates";

export function Floor({ c, m, kind = "planks" }: { c: ArtCtx; m: Mat; kind?: FloorKind }) {
  const vp = { x: 480, y: 120 };
  const k = (540 - vp.y) / (FLOOR - vp.y);
  const rays: ReactNode[] = [];
  if (kind !== "carpet") {
    const step = kind === "planks" ? 44 : 64;
    for (let i = -14; i <= 14; i++) {
      const x0 = vp.x + i * step;
      rays.push(<Ln key={`r${i}`} x1={x0} y1={FLOOR} x2={vp.x + i * step * k} y2={540} s={m.floorLine} sw={1.2} o={0.55} />);
    }
  }
  const rows = kind === "planks" ? [] : kind === "carpet" ? [] : [452, 468, 489, 515];
  return (
    <g aria-hidden="true">
      <defs>
        <linearGradient id={c.id("floor-g")} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#000" stopOpacity="0.22" />
          <stop offset="1" stopColor="#000" stopOpacity="0" />
        </linearGradient>
      </defs>
      <R x={0} y={FLOOR} w={960} h={100} f={m.floor} />
      {rays}
      {rows.map((y) => (
        <Ln key={y} x1={0} y1={y} x2={960} y2={y} s={m.floorLine} sw={1.2} o={0.55} />
      ))}
      {kind === "planks" &&
        Array.from({ length: 18 }, (_, i) => {
          const rnd = seeded(i + 11);
          const lane = Math.floor(rnd() * 28) - 14;
          const t = 0.2 + rnd() * 0.7;
          const y = FLOOR + t * 100;
          const kk = (y - vp.y) / (FLOOR - vp.y);
          const x0 = vp.x + lane * 44 * kk;
          return <Ln key={`s${i}`} x1={x0} y1={y} x2={x0 + 44 * kk} y2={y} s={m.floorLine} sw={1} o={0.45} />;
        })}
      {kind === "plates" &&
        [452, 468, 489, 515].map((y) =>
          Array.from({ length: 10 }, (_, i) => <C key={`${y}-${i}`} cx={60 + i * 96} cy={y + 4} r={1.6} f={m.floorLine} o={0.6} />),
        )}
      {kind === "carpet" &&
        Array.from({ length: 60 }, (_, i) => {
          const rnd = seeded(i + 101);
          return <C key={i} cx={rnd() * 960} cy={FLOOR + 4 + rnd() * 94} r={1 + rnd()} f={m.floorLine} o={0.25} />;
        })}
      <R x={0} y={FLOOR} w={960} h={100} f={c.url("floor-g")} />
    </g>
  );
}

export function Rug({ m, cx = 470, cy = 488, rx = 250, ry = 30 }: { m: Mat; cx?: number; cy?: number; rx?: number; ry?: number }) {
  return (
    <g aria-hidden="true">
      <E cx={cx} cy={cy} rx={rx} ry={ry} f={m.rug} />
      <E cx={cx} cy={cy} rx={rx - 14} ry={ry - 6} f="none" s={m.rugEdge} sw={2.5} style={{ strokeDasharray: "8 6" }} />
      <E cx={cx} cy={cy} rx={rx - 34} ry={ry - 12} f="none" s={m.rugEdge} sw={1.2} o={0.6} />
    </g>
  );
}

/* ------------------------------------------------------------------ */
/* Window                                                               */
/* ------------------------------------------------------------------ */

export type WindowKind = "cross" | "arched" | "round";

export function WindowFrame({
  c,
  m,
  r = L.window,
  kind = "cross",
  curtains,
}: {
  c: ArtCtx;
  m: Mat;
  r?: Rect;
  kind?: WindowKind;
  curtains?: string | null;
}) {
  const { x, y, w, h } = r;
  const gx = x + 10;
  const gy = y + 10;
  const gw = w - 20;
  const gh = h - 20;
  const label = `Window: ${c.tod} in ${c.season}`;
  let glass: ReactNode;
  let frame: ReactNode;
  if (kind === "round") {
    const cx = x + w / 2;
    const cy = y + h / 2;
    const rad = Math.min(w, h) / 2;
    glass = (
      <g>
        <defs>
          <clipPath id={c.id("win-round")}>
            <circle cx={cx} cy={cy} r={rad - 10} />
          </clipPath>
        </defs>
        <g clipPath={c.url("win-round")}>
          <SkyIn c={c} x={cx - rad} y={cy - rad} w={rad * 2} h={rad * 2} name="win" />
        </g>
      </g>
    );
    frame = (
      <g>
        <C cx={cx} cy={cy} r={rad - 5} f="none" s={m.trim} sw={10} />
        <C cx={cx} cy={cy} r={rad} f="none" s={m.metal} sw={2} />
        {Array.from({ length: 8 }, (_, i) => {
          const a = (i / 8) * Math.PI * 2;
          return <C key={i} cx={cx + Math.cos(a) * (rad - 5)} cy={cy + Math.sin(a) * (rad - 5)} r={2} f={m.metal} />;
        })}
        <Ln x1={cx - rad + 10} y1={cy} x2={cx + rad - 10} y2={cy} s={m.trim} sw={4} />
      </g>
    );
  } else if (kind === "arched") {
    const arch = `M${gx} ${gy + gh} V${gy + gw / 2} A${gw / 2} ${gw / 2} 0 0 1 ${gx + gw} ${gy + gw / 2} V${gy + gh} Z`;
    glass = (
      <g>
        <defs>
          <clipPath id={c.id("win-arch")}>
            <path d={arch} />
          </clipPath>
        </defs>
        <g clipPath={c.url("win-arch")}>
          <SkyIn c={c} x={gx} y={gy} w={gw} h={gh} name="win" />
        </g>
      </g>
    );
    frame = (
      <g>
        <P d={arch} f="none" s={m.trim} sw={12} />
        <Ln x1={gx + gw / 2} y1={gy + 4} x2={gx + gw / 2} y2={gy + gh} s={m.trim} sw={5} />
        <Ln x1={gx} y1={gy + gh * 0.58} x2={gx + gw} y2={gy + gh * 0.58} s={m.trim} sw={5} />
        <P d={`M${gx + gw * 0.15} ${gy + gw / 2} A${gw * 0.35} ${gw * 0.35} 0 0 1 ${gx + gw * 0.85} ${gy + gw / 2}`} f="none" s={m.trim} sw={3} />
      </g>
    );
  } else {
    glass = <SkyIn c={c} x={gx} y={gy} w={gw} h={gh} name="win" />;
    frame = (
      <g>
        <R x={x} y={y} w={w} h={10} f={m.trim} />
        <R x={x} y={y + h - 10} w={w} h={10} f={m.trim} />
        <R x={x} y={y} w={10} h={h} f={m.trim} />
        <R x={x + w - 10} y={y} w={10} h={h} f={m.trim} />
        <R x={x + w / 2 - 3} y={y} w={6} h={h} f={m.trim} />
        <R x={x} y={y + h * 0.45 - 3} w={w} h={6} f={m.trim} />
      </g>
    );
  }
  return (
    <g role="img" aria-label={label}>
      <title>{label}</title>
      {glass}
      <P d={`M${gx + gw * 0.1} ${gy + gh} L${gx + gw * 0.42} ${gy} L${gx + gw * 0.55} ${gy} L${gx + gw * 0.23} ${gy + gh} Z`} f="#fff" o={0.07} />
      {frame}
      {kind !== "round" && (
        <>
          <R x={x - 12} y={y + h} w={w + 24} h={10} rx={2} f={m.trim} />
          <R x={x - 12} y={y + h + 10} w={w + 24} h={3} f="#000" o={0.12} />
        </>
      )}
      {curtains && (
        <g aria-hidden="true">
          <R x={x - 30} y={y - 16} w={w + 60} h={5} rx={2.5} f={m.metal} />
          <P
            d={`M${x - 26} ${y - 12} H${x + 12} C${x + 4} ${y + h * 0.4} ${x + 18} ${y + h * 0.75} ${x + 4} ${y + h + 18} H${x - 26} Z`}
            f={curtains}
          />
          <P
            d={`M${x + w + 26} ${y - 12} H${x + w - 12} C${x + w - 4} ${y + h * 0.4} ${x + w - 18} ${y + h * 0.75} ${x + w - 4} ${y + h + 18} H${x + w + 26} Z`}
            f={curtains}
          />
          {[x - 18, x - 6, x + w + 6, x + w + 18].map((lx) => (
            <Ln key={lx} x1={lx} y1={y - 10} x2={lx + (lx < x ? 4 : -4)} y2={y + h + 14} s="#000" sw={1.2} o={0.12} />
          ))}
        </g>
      )}
    </g>
  );
}

/* ------------------------------------------------------------------ */
/* Door                                                                 */
/* ------------------------------------------------------------------ */

export type DoorKind = "panel" | "double" | "arched" | "glass" | "flat";

export function Door({ m, r = L.door, kind = "panel" }: { m: Mat; r?: Rect; kind?: DoorKind }) {
  const { x, y, w, h } = r;
  const panel = (px: number, py: number, pw: number, ph: number, key: string) => (
    <g key={key}>
      <R x={px} y={py} w={pw} h={ph} rx={2} f={m.woodDark} o={0.35} />
      <R x={px + 4} y={py + 4} w={pw - 8} h={ph - 8} rx={1.5} f={m.woodLight} o={0.25} />
    </g>
  );
  const plaque = (
    <g>
      <R x={x + w / 2 - 22} y={y + h * 0.47 - 9} w={44} h={14} rx={2} f={m.metal} />
      <Tx x={x + w / 2} y={y + h * 0.47 + 1.5} size={8} f={m.ink} anchor="middle" weight={700} ls={1.5}>
        QUIZ
      </Tx>
    </g>
  );
  let body: ReactNode;
  if (kind === "double") {
    const hw = w / 2;
    body = (
      <g>
        <R x={x} y={y} w={w} h={h} f={m.wood} />
        {[0, 1].map((i) => (
          <g key={i}>
            {panel(x + i * hw + 9, y + 14, hw - 18, h * 0.4, `a${i}`)}
            {panel(x + i * hw + 9, y + h * 0.52, hw - 18, h * 0.42, `b${i}`)}
          </g>
        ))}
        <Ln x1={x + hw} y1={y} x2={x + hw} y2={y + h} s={m.woodDark} sw={2} />
        <R x={x + hw - 9} y={y + h * 0.48} w={4} h={22} rx={2} f={m.metal} />
        <R x={x + hw + 5} y={y + h * 0.48} w={4} h={22} rx={2} f={m.metal} />
        <R x={x + w / 2 - 22} y={y + h * 0.43} w={44} h={14} rx={2} f={m.metal} />
        <Tx x={x + w / 2} y={y + h * 0.43 + 10.5} size={8} f={m.ink} anchor="middle" weight={700} ls={1.5}>
          QUIZ
        </Tx>
      </g>
    );
  } else if (kind === "arched") {
    const d = `M${x} ${y + h} V${y + w / 2} A${w / 2} ${w / 2} 0 0 1 ${x + w} ${y + w / 2} V${y + h} Z`;
    body = (
      <g>
        <P d={d} f={m.wood} />
        {Array.from({ length: 5 }, (_, i) => (
          <Ln key={i} x1={x + (w / 6) * (i + 1)} y1={y + 12} x2={x + (w / 6) * (i + 1)} y2={y + h} s={m.woodDark} sw={1.5} o={0.6} />
        ))}
        {[0.3, 0.75].map((f) => (
          <g key={f}>
            <R x={x + 4} y={y + h * f} w={w - 8} h={8} f={m.metal} o={0.85} />
            {Array.from({ length: 6 }, (_, i) => (
              <C key={i} cx={x + 14 + i * ((w - 28) / 5)} cy={y + h * f + 4} r={1.8} f={m.woodDark} />
            ))}
          </g>
        ))}
        <C cx={x + w - 24} cy={y + h * 0.55} r={9} f="none" s={m.metal} sw={3} />
        <C cx={x + w - 24} cy={y + h * 0.55 - 9} r={3} f={m.metal} />
        {plaque}
      </g>
    );
  } else if (kind === "glass") {
    body = (
      <g>
        <R x={x} y={y} w={w} h={h} f={m.trim} />
        {Array.from({ length: 3 }, (_, j) =>
          Array.from({ length: 2 }, (_, i) => (
            <R
              key={`${i}-${j}`}
              x={x + 10 + i * ((w - 26) / 2 + 6)}
              y={y + 10 + j * ((h * 0.72 - 20) / 3 + 4)}
              w={(w - 26) / 2}
              h={(h * 0.72 - 20) / 3 - 4}
              f="#cfe9f5"
              o={0.55}
            />
          )),
        )}
        <R x={x + 10} y={y + h * 0.74} w={w - 20} h={h * 0.22} f={m.woodDark} o={0.25} />
        <R x={x + w - 22} y={y + h * 0.48} w={6} h={34} rx={3} f={m.metal} />
        {plaque}
      </g>
    );
  } else if (kind === "flat") {
    body = (
      <g>
        <R x={x} y={y} w={w} h={h} f={m.wood} />
        <R x={x + 20} y={y + 30} w={w - 40} h={70} rx={2} f={m.paper} />
        <P d={`M${x + 28} ${y + 90} L${x + 52} ${y + 52} L${x + 66} ${y + 72} L${x + 78} ${y + 60} L${x + w - 28} ${y + 90} Z`} f={mix("var(--primary)", 70, "#334")} />
        <C cx={x + w - 40} cy={y + 46} r={7} f={mix("var(--accent)", 80, "#fc6")} />
        <R x={x + w / 2 - 24} y={y + 112} w={48} h={16} rx={3} f={m.paper} s={m.woodDark} sw={1} />
        <Tx x={x + w / 2} y={y + 123.5} size={8} f={m.ink} anchor="middle" weight={700} ls={1.5}>
          QUIZ
        </Tx>
        <C cx={x + 24} cy={y + 150} r={3} f={m.metal} />
        <P d={`M${x + 14} ${y + 178} Q${x + 24} ${y + 140} ${x + 34} ${y + 178}`} f="none" s={mix("var(--primary)", 50, "#333")} sw={2} />
        <R x={x + 8} y={y + 174} w={32} h={38} rx={3} f={mix("var(--primary)", 55, "#fff")} />
        <R x={x + 14} y={y + 186} w={20} h={11} rx={2} f="#fff" o={0.55} />
        <R x={x + w - 22} y={y + h * 0.52} w={14} h={5} rx={2.5} f={m.metal} />
      </g>
    );
  } else {
    body = (
      <g>
        <R x={x} y={y} w={w} h={h} f={m.wood} />
        {panel(x + 14, y + 16, w / 2 - 20, h * 0.4, "a")}
        {panel(x + w / 2 + 6, y + 16, w / 2 - 20, h * 0.4, "b")}
        {panel(x + 14, y + h * 0.53, w / 2 - 20, h * 0.42, "c")}
        {panel(x + w / 2 + 6, y + h * 0.53, w / 2 - 20, h * 0.42, "d")}
        <C cx={x + w - 16} cy={y + h * 0.53} r={6} f={m.metal} />
        <C cx={x + w - 17.5} cy={y + h * 0.53 - 1.5} r={2} f="#fff" o={0.45} />
        {plaque}
      </g>
    );
  }
  const archTop = kind === "arched";
  return (
    <g>
      {archTop ? (
        <P
          d={`M${x - 9} ${y + h} V${y + w / 2} A${w / 2 + 9} ${w / 2 + 9} 0 0 1 ${x + w + 9} ${y + w / 2} V${y + h} Z`}
          f={m.trim}
        />
      ) : (
        <R x={x - 9} y={y - 9} w={w + 18} h={h + 9} f={m.trim} />
      )}
      {body}
      {!archTop && <R x={x - 9} y={y - 9} w={w + 18} h={3} f="#fff" o={0.16} />}
      <R x={x} y={y + h - 3} w={w} h={3} f="#000" o={0.2} />
    </g>
  );
}

/* ------------------------------------------------------------------ */
/* Wall pieces: pennant, noticeboard, chart, trophies, clock            */
/* ------------------------------------------------------------------ */

export function Pennant({ c, r = L.pennant }: { c: ArtCtx; r?: Rect }) {
  const { x, y, w, h } = r;
  const fill = mix("var(--surface)", 88, "var(--primary)");
  const tri = `M${x + 12} ${y + 8} L${x + w} ${y + h / 2} L${x + 12} ${y + h - 8} Z`;
  return (
    <g>
      <C cx={x + 8} cy={y + 2} r={2.2} f="#6b6b6b" />
      <P d={`M${x + 8} ${y + 2} L${x + 4} ${y + 9} M${x + 8} ${y + 2} L${x + 12} ${y + 9}`} f="none" s="#6b6b6b" sw={1} />
      <P d={tri} f="#000" o={0.12} t="translate(3 3)" />
      <P d={tri} f={fill} />
      <P d={`M${x + 16} ${y + 13} L${x + w - 10} ${y + h / 2} L${x + 16} ${y + h - 13}`} f="none" s="var(--primary)" sw={1.2} style={{ strokeDasharray: "3 3" }} />
      <R x={x + 2} y={y + 6} w={12} h={h - 12} rx={2} f="var(--primary)" />
      <C cx={x + w} cy={y + h / 2} r={3} f="var(--primary)" />
      <ClubLogo name="inline" x={x + 18} y={y + h / 2 - 9} w={70} h={18} preview={c.preview} />
    </g>
  );
}

export type BoardKind = "cork" | "slate";

export function Noticeboard({ c, m, r = L.noticeboard, kind = "cork" }: { c: ArtCtx; m: Mat; r?: Rect; kind?: BoardKind }) {
  const { x, y, w, h } = r;
  const { due, nextDue, notes } = c.data;
  const slate = kind === "slate";
  const rnd = seeded(7);
  const next = relativeDay(nextDue, c.now);
  const head = due === null ? "—" : due > 0 ? String(due) : "✓";
  const sub = due === null ? "reviews" : due > 0 ? (due === 1 ? "review due" : "reviews due") : "all caught up";
  const slots = [
    [x + 92, y + 14, -3],
    [x + 128, y + 18, 4],
    [x + 96, y + 62, 2],
  ] as const;
  return (
    <g>
      <R x={x + 3} y={y + 4} w={w} h={h} rx={3} f="#000" o={0.14} />
      <R x={x} y={y} w={w} h={h} rx={3} f={m.woodDark} />
      <R x={x + 8} y={y + 8} w={w - 16} h={h - 16} rx={1} f={slate ? "#2f3a3a" : m.cork} />
      {!slate &&
        Array.from({ length: 40 }, (_, i) => (
          <C key={i} cx={x + 10 + rnd() * (w - 20)} cy={y + 10 + rnd() * (h - 20)} r={0.8 + rnd()} f="#000" o={0.12} />
        ))}
      {slate && <Tx x={x + 22} y={y + h - 16} size={9} f="#e9e6dc" o={0.55} t={`rotate(-4 ${x + 22} ${y + h - 16})`}>∮ dt</Tx>}
      <g transform={`rotate(-2 ${x + 47} ${y + 40})`}>
        <R x={x + 14} y={y + 14} w={68} h={54} rx={1.5} f={m.paper} />
        <R x={x + 14} y={y + 14} w={68} h={9} f="var(--primary)" o={0.85} />
        <Tx x={x + 48} y={y + 21} size={6.5} f="#fff" anchor="middle" weight={700} ls={1}>
          TODAY
        </Tx>
        <Tx x={x + 48} y={y + 46} size={20} f="var(--primary)" anchor="middle" weight={700}>
          {head}
        </Tx>
        <Tx x={x + 48} y={y + 56} size={6.5} f={m.ink} anchor="middle">
          {sub}
        </Tx>
        {next && (due ?? 0) === 0 && (
          <Tx x={x + 48} y={y + 64} size={5.5} f={m.ink} anchor="middle" o={0.75}>
            next: {next}
          </Tx>
        )}
        <C cx={x + 48} cy={y + 15} r={3} f="var(--accent)" />
      </g>
      {notes.slice(0, 3).map((n, i) => {
        const [nx, ny, rot] = slots[i];
        const lines = noteLines(n, 8, 3);
        return (
          <g key={i} transform={`rotate(${rot} ${nx + 17} ${ny + 17})`}>
            <R x={nx + 1.5} y={ny + 2} w={34} h={34} f="#000" o={0.12} />
            <R x={nx} y={ny} w={34} h={34} f={STICKY[i % STICKY.length]} />
            {lines.map((l, k) => (
              <Tx key={k} x={nx + 17} y={ny + 13 + k * 8} size={6.6} f="#3b3326" anchor="middle">
                {l}
              </Tx>
            ))}
            <C cx={nx + 17} cy={ny + 3} r={2.4} f="var(--primary)" />
          </g>
        );
      })}
      <g transform={`rotate(3 ${x + 40} ${y + 92})`}>
        <R x={x + 20} y={y + 76} w={42} h={30} f={slate ? "#e9e6dc" : "#f8fafc"} o={slate ? 0.15 : 1} />
        {!slate &&
          [0, 1, 2, 3].map((i) => <Ln key={i} x1={x + 20} y1={y + 82 + i * 6} x2={x + 62} y2={y + 82 + i * 6} s="#93c5fd" sw={0.6} />)}
        <P
          d={`M${x + 25} ${y + 100} C${x + 32} ${y + 80} ${x + 40} ${y + 104} ${x + 47} ${y + 86} S${x + 55} ${y + 92} ${x + 58} ${y + 82}`}
          f="none"
          s={slate ? "#e9e6dc" : "var(--primary)"}
          sw={1.2}
        />
      </g>
    </g>
  );
}

export type ChartKind = "bars" | "stars";

export function WallChart({ c, m, r = L.chart, kind = "bars" }: { c: ArtCtx; m: Mat; r?: Rect; kind?: ChartKind }) {
  const { x, y, w, h } = r;
  const bars = c.data.topics.length
    ? chartBars(c.data.topics)
    : [0.35, 0.55, 0.45, 0.8, 0.65].map((v) => ({ value: v, share: 0.6 }));
  const px = x + 8;
  const py = y + 8;
  const pw = w - 16;
  const ph = h - 16;
  const ax = px + 12;
  const ay = py + ph - 10;
  const bw = (pw - 24) / Math.max(5, bars.length);
  const tops = bars.map((b, i) => [ax + 4 + i * bw + bw * 0.35, ay - b.value * (ph - 26)] as const);
  const stars = kind === "stars";
  return (
    <g>
      <R x={x + 3} y={y + 4} w={w} h={h} rx={2} f="#000" o={0.14} />
      <R x={x} y={y} w={w} h={h} rx={2} f={m.trim} />
      <R x={px} y={py} w={pw} h={ph} f={stars ? "#141c3d" : m.paper} />
      {stars ? (
        <g>
          {Array.from({ length: 22 }, (_, i) => {
            const rnd = seeded(i + 31);
            return <C key={i} cx={px + rnd() * pw} cy={py + rnd() * ph} r={0.5 + rnd() * 0.7} f="#e8e6ff" o={0.6} />;
          })}
          <C cx={px + pw / 2} cy={py + ph / 2} r={ph * 0.42} f="none" s="#8ea0ff" sw={0.6} o={0.4} />
          <C cx={px + pw / 2} cy={py + ph / 2} r={ph * 0.25} f="none" s="#8ea0ff" sw={0.6} o={0.3} />
          <polyline points={tops.map((t) => t.join(",")).join(" ")} style={{ fill: "none", stroke: "#cdd5ff", strokeWidth: 1, opacity: 0.8 }} />
          {tops.map(([tx, ty], i) => (
            <C key={i} cx={tx} cy={ty} r={2.4} f={i % 2 ? "#ffe9a8" : "#ffffff"} />
          ))}
        </g>
      ) : (
        <g>
          {[0.25, 0.5, 0.75].map((f) => (
            <Ln key={f} x1={ax} y1={ay - f * (ph - 26)} x2={px + pw - 6} y2={ay - f * (ph - 26)} s={m.ink} sw={0.5} o={0.15} />
          ))}
          <Ln x1={ax} y1={py + 8} x2={ax} y2={ay} s={m.ink} sw={1.2} />
          <Ln x1={ax} y1={ay} x2={px + pw - 6} y2={ay} s={m.ink} sw={1.2} />
          {bars.map((b, i) => {
            const bh = b.value * (ph - 26);
            const bx = ax + 4 + i * bw;
            return (
              <g key={i}>
                <R x={bx} y={ay - bh} w={bw * 0.7} h={bh} f={mix("var(--primary)", 35, m.paper)} />
                <R x={bx} y={ay - bh * b.share} w={bw * 0.7} h={bh * b.share} f="var(--primary)" />
              </g>
            );
          })}
          <polyline
            points={tops.map(([tx, ty]) => `${tx},${ty - 4}`).join(" ")}
            style={{ fill: "none", stroke: "var(--accent)", strokeWidth: 1.6, strokeLinejoin: "round" }}
          />
        </g>
      )}
      <Tx x={px + pw - 4} y={py + 9} size={6.5} f={stars ? "#cdd5ff" : m.ink} anchor="end" o={0.7} ls={0.5}>
        {stars ? "STAR CHART" : "STATS"}
      </Tx>
    </g>
  );
}

export const TROPHY_TINT: Record<string, string> = {
  spaced_reviews: "var(--success)",
  comebacks: "var(--warning)",
  honest_attempts: "var(--accent)",
};

export function Trophy({ x, base, tint, s = 1 }: { x: number; base: number; tint: string; s?: number }) {
  const gold = "#e2b13c";
  return (
    <g transform={`translate(${x} ${base}) scale(${s})`}>
      <R x={-9} y={-7} w={18} h={7} rx={1} f="#5b3b22" />
      <R x={-9} y={-5} w={18} h={2} f={tint} />
      <R x={-2} y={-15} w={4} h={8} f={gold} />
      <P d="M-11 -36 H11 C11 -24 6 -17 0 -16 C-6 -17 -11 -24 -11 -36 Z" f={gold} />
      <P d="M-11 -33 C-17 -33 -17 -24 -9 -23 M11 -33 C17 -33 17 -24 9 -23" f="none" s={gold} sw={2} />
      <P d="M-7 -34 C-7 -27 -5 -22 -2 -20" f="none" s="#fff" sw={1.5} o={0.5} />
      <C cx={0} cy={-28} r={3.2} f={tint} />
    </g>
  );
}

export function TrophyShelf({ c, m, r = L.trophies }: { c: ArtCtx; m: Mat; r?: Rect }) {
  const { x, y, w, h } = r;
  const base = y + h - 8;
  const list = c.data.trophies.slice(0, 5);
  const label = list.length ? `Trophies: ${list.map((t) => t.title).join(", ")}` : "Trophy shelf: no milestones yet";
  const step = 26;
  const start = x + w / 2 - ((list.length - 1) * step) / 2;
  return (
    <g role="img" aria-label={label}>
      <title>{label}</title>
      <R x={x} y={base} w={w} h={8} rx={1} f={m.wood} />
      <R x={x} y={base + 8} w={w} h={2} f="#000" o={0.18} />
      <P d={`M${x + 14} ${base + 8} h10 l-10 14 Z M${x + w - 14} ${base + 8} h-10 l10 14 Z`} f={m.woodDark} />
      {list.map((t, i) => (
        <g key={t.id}>
          <title>{t.title}</title>
          <Trophy x={start + i * step} base={base} tint={TROPHY_TINT[t.id] ?? "var(--primary)"} />
        </g>
      ))}
    </g>
  );
}

export function WallClock({ c, m, cx, cy, r = 24 }: { c: ArtCtx; m: Mat; cx: number; cy: number; r?: number }) {
  const { hour, minute } = clockHands(c.now);
  const hand = (deg: number, len: number, sw: number) => {
    const a = ((deg - 90) * Math.PI) / 180;
    return <Ln x1={cx} y1={cy} x2={cx + Math.cos(a) * len} y2={cy + Math.sin(a) * len} s={m.ink} sw={sw} />;
  };
  return (
    <g aria-hidden="true">
      <C cx={cx + 2} cy={cy + 3} r={r + 4} f="#000" o={0.14} />
      <C cx={cx} cy={cy} r={r + 4} f={m.woodDark} />
      <C cx={cx} cy={cy} r={r} f={m.paper} />
      {Array.from({ length: 12 }, (_, i) => {
        const a = (i / 12) * Math.PI * 2;
        const l = i % 3 === 0 ? 5 : 2.5;
        return (
          <Ln key={i} x1={cx + Math.cos(a) * (r - 2)} y1={cy + Math.sin(a) * (r - 2)} x2={cx + Math.cos(a) * (r - 2 - l)} y2={cy + Math.sin(a) * (r - 2 - l)} s={m.ink} sw={i % 3 === 0 ? 1.6 : 1} />
        );
      })}
      {hand(hour, r * 0.5, 2.6)}
      {hand(minute, r * 0.78, 1.6)}
      <C cx={cx} cy={cy} r={2} f="var(--primary)" />
    </g>
  );
}

/* ------------------------------------------------------------------ */
/* Bookcase and books                                                   */
/* ------------------------------------------------------------------ */

export type BookcaseKind = "case" | "tall" | "crate" | "cubes";

export function Books({ c, shelves, spines = SPINES }: { c: ArtCtx; shelves: Shelf[]; spines?: string[] }) {
  const { books, overflow } = layoutBooks(c.data.topics, shelves, { colors: spines.length });
  const last = shelves[shelves.length - 1];
  return (
    <g>
      {books.map((b) => (
        <g key={b.topic}>
          <title>{b.topic}</title>
          <R x={b.x} y={b.y} w={b.w} h={b.h} rx={1} f={spines[b.color]} />
          <R x={b.x} y={b.y} w={1.5} h={b.h} f="#fff" o={0.14} />
          <R x={b.x} y={b.y + 4} w={b.w} h={1.6} f="#fff" o={0.3} />
          <R x={b.x} y={b.y + b.h - 6} w={b.w} h={1.6} f="#fff" o={0.3} />
          {b.label && (
            <Tx
              x={0}
              y={0}
              size={b.fontSize}
              f="#fbf7ee"
              anchor="middle"
              t={`translate(${b.x + b.w / 2 + b.fontSize * 0.35} ${b.y + b.h / 2}) rotate(-90)`}
            >
              {b.label}
            </Tx>
          )}
        </g>
      ))}
      {overflow > 0 && last && (
        <g>
          <R x={last.x + last.width - 20} y={last.base - 14} w={20} h={12} rx={2} f="#fbf7ee" s="#000" sw={0.5} />
          <Tx x={last.x + last.width - 10} y={last.base - 5} size={7} f="#3b3326" anchor="middle" weight={700}>
            +{overflow}
          </Tx>
        </g>
      )}
      {books.length === 0 && shelves[0] && (
        <g>
          <P d={`M${shelves[0].x + 4} ${shelves[0].base} v-26 h10 l6 26 Z`} f={mix("var(--primary)", 60, "#555")} />
          <P d={`M${shelves[0].x + 60} ${shelves[0].base} v-26 h-10 l-6 26 Z`} f={mix("var(--primary)", 60, "#555")} />
        </g>
      )}
    </g>
  );
}

export function Bookcase({ c, m, r = L.bookcase, kind = "case", shelves: n = 4 }: { c: ArtCtx; m: Mat; r?: Rect; kind?: BookcaseKind; shelves?: number }) {
  const { x, y, w, h } = r;
  const top = y + 12;
  const bottom = y + h - 12;
  const plank = 8;
  const comp = (bottom - top - (n - 1) * plank) / n;
  const label = c.data.topics.length
    ? `${c.data.topics.length} topic${c.data.topics.length === 1 ? "" : "s"} practised`
    : "No topics practised yet";
  const shelves: Shelf[] = [];
  const cubes = kind === "cubes";
  for (let i = 0; i < n; i++) {
    const base = top + comp * (i + 1) + plank * i;
    if (cubes) {
      const half = (w - 24 - 8) / 2;
      shelves.push({ x: x + 12, base, width: half - 2, height: comp - 4 });
      shelves.push({ x: x + 12 + half + 8, base, width: half - 2, height: comp - 4 });
    } else shelves.push({ x: x + 12, base, width: w - 24, height: comp - 4 });
  }
  const crate = kind === "crate";
  return (
    <g>
      <title>{label}</title>
      <R x={x + 4} y={y + 6} w={w} h={h} f="#000" o={0.15} />
      {!crate && <R x={x} y={y} w={w} h={h} rx={2} f={m.woodDark} />}
      {!crate && <R x={x + 10} y={top} w={w - 20} h={bottom - top} f={mix(m.woodDark, 70, "#000")} />}
      {crate && (
        <>
          <R x={x} y={y} w={10} h={h} f={m.wood} />
          <R x={x + w - 10} y={y} w={10} h={h} f={m.wood} />
          {[0.3, 0.7].map((f) => (
            <Ln key={f} x1={x + 10} y1={y + h * f} x2={x + w - 10} y2={y + h * (f + 0.18)} s={m.wood} sw={3} o={0.6} />
          ))}
        </>
      )}
      {Array.from({ length: n - 1 }, (_, i) => {
        const py = top + comp * (i + 1) + plank * i;
        return <R key={i} x={x + 6} y={py} w={w - 12} h={plank} f={m.wood} />;
      })}
      {cubes && <R x={x + w / 2 - 4} y={top} w={8} h={bottom - top} f={m.wood} />}
      {kind === "tall" && (
        <>
          <P d={`M${x - 8} ${y + 2} Q${x + w / 2} ${y - 22} ${x + w + 8} ${y + 2} Z`} f={m.wood} />
          <C cx={x + w / 2} cy={y - 6} r={5} f={m.metal} />
        </>
      )}
      <R x={x - 6} y={y - 4} w={w + 12} h={12} rx={2} f={m.wood} />
      <R x={x - 4} y={y + h - 12} w={w + 8} h={12} f={m.wood} />
      <Books c={c} shelves={shelves} />
    </g>
  );
}

/* ------------------------------------------------------------------ */
/* Desk and what stands on it                                           */
/* ------------------------------------------------------------------ */

export type DeskKind = "desk" | "bench";

export function Desk({ m, r = L.desk, kind = "desk" }: { m: Mat; r?: Rect; kind?: DeskKind }) {
  const { x, y, w, h } = r;
  return (
    <g aria-hidden="true">
      <E cx={x + w / 2} cy={FLOOR + 3} rx={w / 2 + 10} ry={7} f="#000" o={0.18} />
      <R x={x + 8} y={y + 12} w={14} h={h - 12} f={m.woodDark} />
      <R x={x + w - 22} y={y + 12} w={14} h={h - 12} f={m.woodDark} />
      {kind === "bench" ? (
        <>
          <R x={x + 8} y={y + h - 34} w={w - 16} h={8} f={m.wood} />
          {[0.2, 0.42, 0.66].map((f, i) => (
            <g key={f}>
              <P d={`M${x + w * f - 14} ${y + h - 62} h28 l-4 28 h-20 Z`} f={m.pot} />
              <R x={x + w * f - 16} y={y + h - 66} w={32} h={6} rx={1} f={m.pot} />
              {i !== 1 && <E cx={x + w * f} cy={y + h - 72} rx={10} ry={8} f={LEAF} />}
            </g>
          ))}
        </>
      ) : (
        <>
          <R x={x + 6} y={y + 12} w={w - 12} h={26} f={m.wood} />
          <R x={x + 30} y={y + 17} w={120} h={16} rx={2} f={m.woodDark} o={0.25} />
          <R x={x + w - 150} y={y + 17} w={120} h={16} rx={2} f={m.woodDark} o={0.25} />
          <R x={x + 82} y={y + 23} w={16} h={4} rx={2} f={m.metal} />
          <R x={x + w - 98} y={y + 23} w={16} h={4} rx={2} f={m.metal} />
        </>
      )}
      <R x={x - 8} y={y} w={w + 16} h={14} rx={2} f={m.woodLight} />
      <R x={x - 8} y={y + 11} w={w + 16} h={3} f="#000" o={0.18} />
    </g>
  );
}

export function ChairBack({ m, x = 428, color }: { m: Mat; x?: number; color?: string }) {
  const col = color ?? mix("var(--primary)", 45, m.woodDark);
  return (
    <g aria-hidden="true">
      <E cx={x + 42} cy={FLOOR + 14} rx={44} ry={6} f="#000" o={0.15} />
      <R x={x + 12} y={392} w={6} h={62} f={m.woodDark} />
      <R x={x + 66} y={392} w={6} h={62} f={m.woodDark} />
      <R x={x} y={350} w={84} h={58} rx={12} f={col} />
      <R x={x + 8} y={358} w={68} h={10} rx={5} f="#fff" o={0.12} />
    </g>
  );
}

/** Papers and a pencil between the lamp and the mug. */
export function Notebook({ m, x = 392, y = 328 }: { m: Mat; x?: number; y?: number }) {
  return (
    <g aria-hidden="true">
      <P d={`M${x} ${y} l6 -9 h40 l-4 9 Z`} f={m.paper} s="#000" sw={0.4} />
      <P d={`M${x + 3} ${y - 2} l5 -8 h38 l-3 8 Z`} f="#fff" s="#000" sw={0.3} />
      <P d={`M${x + 12} ${y - 6} q4 -3 8 0 t8 0`} f="none" s="var(--primary)" sw={0.8} />
      <Ln x1={x + 10} y1={y - 3} x2={x + 36} y2={y - 3} s={m.ink} sw={0.5} o={0.4} />
      <Ln x1={x + 30} y1={y - 1} x2={x + 46} y2={y - 6} s="#e8b33a" sw={2.2} />
    </g>
  );
}

export type LampKind = "angle" | "banker";

/** Where the light comes from, for the ambient glow. */
export function lampHead(kind: LampKind, r: Rect = L.lamp): { x: number; y: number } {
  return kind === "banker" ? { x: r.x + 46, y: r.y + 56 } : { x: r.x + 80, y: r.y + 38 };
}

export function Lamp({ c, m, r = L.lamp, kind = "angle" }: { c: ArtCtx; m: Mat; r?: Rect; kind?: LampKind }) {
  const { x, y } = r;
  const base = y + r.h;
  const on = c.lampOn;
  const bulb = on ? "#fff6c9" : "#d8d2c0";
  if (kind === "banker") {
    const sx = x + 46;
    const sy = y + 50;
    return (
      <g>
        {on && (
          <g className="rm-glow">
            <P d={`M${sx - 34} ${sy + 8} L${sx + 34} ${sy + 8} L${sx + 70} ${base} L${sx - 60} ${base} Z`} f="#ffe9a8" o={0.28} />
          </g>
        )}
        <R x={sx - 22} y={base - 6} w={44} h={6} rx={2} f={m.metal} />
        <R x={sx - 2} y={sy + 6} w={4} h={base - sy - 10} f={m.metal} />
        <Ln x1={sx + 18} y1={sy + 8} x2={sx + 18} y2={sy + 30} s={m.metal} sw={1} />
        <C cx={sx + 18} cy={sy + 31} r={1.8} f={m.metal} />
        <E cx={sx} cy={sy + 8} rx={30} ry={4} f={bulb} />
        <P d={`M${sx - 34} ${sy + 8} C${sx - 32} ${sy - 12} ${sx + 32} ${sy - 12} ${sx + 34} ${sy + 8} Z`} f={m.shade} />
        <P d={`M${sx - 24} ${sy - 2} C${sx - 12} ${sy - 9} ${sx + 6} ${sy - 9} ${sx + 18} ${sy - 4}`} f="none" s="#fff" sw={2} o={0.35} />
      </g>
    );
  }
  const bx = x + 30;
  return (
    <g>
      {on && (
        <g className="rm-glow">
          <P d={`M${x + 66} ${y + 40} L${x + 98} ${y + 42} L${x + 180} ${base} L${x + 50} ${base} Z`} f="#ffe9a8" o={0.3} />
        </g>
      )}
      <E cx={bx} cy={base - 3} rx={22} ry={5} f={m.shade} />
      <R x={bx - 14} y={base - 9} w={28} h={6} rx={3} f={m.shade} />
      <Ln x1={bx} y1={base - 8} x2={x + 46} y2={y + 40} s={m.shade} sw={5} />
      <Ln x1={x + 46} y1={y + 40} x2={x + 74} y2={y + 22} s={m.shade} sw={5} />
      <C cx={x + 46} cy={y + 40} r={4.5} f={m.metal} />
      <C cx={x + 74} cy={y + 22} r={3.5} f={m.metal} />
      <E cx={x + 82} cy={y + 41} rx={10} ry={4} f={bulb} />
      <P d={`M${x + 70} ${y + 14} L${x + 84} ${y + 16} L${x + 100} ${y + 42} L${x + 64} ${y + 40} Z`} f={m.shade} />
      <P d={`M${x + 73} ${y + 19} L${x + 80} ${y + 20}`} f="none" s="#fff" sw={1.5} o={0.4} />
    </g>
  );
}

export function Mug({ c, r = L.mug }: { c: ArtCtx; r?: Rect }) {
  const { x, y, h } = r;
  const base = y + h;
  const mx = x + 6;
  const mw = 44;
  const top = base - 36;
  const body = mix("var(--surface)", 90, "var(--text)");
  return (
    <g>
      <g className="rm-steam-wrap">
        {[0, 1].map((i) => (
          <P
            key={i}
            d={`M${mx + 15 + i * 12} ${top - 4} c-5 -6 5 -10 0 -16 c-4 -5 3 -8 1 -12`}
            f="none"
            s="var(--muted)"
            sw={1.6}
            cls="rm-steam"
            style={{ animationDelay: `${i * -1.8}s` }}
          />
        ))}
      </g>
      <E cx={mx + mw / 2} cy={base} rx={mw / 2 + 2} ry={3} f="#000" o={0.15} />
      <P d={`M${mx + mw - 2} ${top + 8} c14 0 14 20 0 20`} f="none" s={body} sw={5} />
      <P d={`M${mx + mw - 2} ${top + 8} c14 0 14 20 0 20`} f="none" s="#000" sw={0.6} o={0.25} />
      <P d={`M${mx} ${top} V${base - 4} Q${mx} ${base} ${mx + 4} ${base} H${mx + mw - 4} Q${mx + mw} ${base} ${mx + mw} ${base - 4} V${top} Z`} f={body} s="#000" sw={0.6} />
      <E cx={mx + mw / 2} cy={top} rx={mw / 2} ry={3.5} f="#5b3a29" s="#000" sw={0.5} />
      <R x={mx} y={top + 5} w={mw} h={2.5} f="#ffd60a" />
      <ClubLogo name="coding" x={mx + 3} y={top + 13} w={mw - 6} h={11} preview={c.preview} />
    </g>
  );
}

export function Printer({ m, r = L.printer }: { m: Mat; r?: Rect }) {
  const { x, y, h } = r;
  const base = y + h;
  const body = mix("var(--surface)", 65, "#c9ced6");
  return (
    <g>
      <E cx={x + 60} cy={base} rx={58} ry={3} f="#000" o={0.15} />
      <R x={x + 28} y={y + 2} w={62} h={24} f={m.paper} s="#000" sw={0.4} />
      {[0, 1, 2].map((i) => (
        <Ln key={i} x1={x + 36} y1={y + 9 + i * 5} x2={x + 80 - i * 8} y2={y + 9 + i * 5} s={m.ink} sw={0.6} o={0.35} />
      ))}
      <R x={x + 4} y={y + 18} w={112} h={40} rx={6} f={body} s="#000" sw={0.6} />
      <R x={x + 4} y={y + 18} w={112} h={11} rx={6} f="#000" o={0.08} />
      <R x={x + 18} y={y + 40} w={84} h={4} rx={2} f="#2b2b2b" o={0.6} />
      <R x={x + 24} y={y + 43} w={72} h={h - 43} f={m.paper} s="#000" sw={0.4} />
      <Tx x={x + 34} y={y + 55} size={8} f="var(--primary)" weight={700}>
        Σ
      </Tx>
      <Ln x1={x + 44} y1={y + 51} x2={x + 86} y2={y + 51} s={m.ink} sw={0.6} o={0.4} />
      <Ln x1={x + 44} y1={y + 55} x2={x + 76} y2={y + 55} s={m.ink} sw={0.6} o={0.4} />
      <C cx={x + 104} cy={y + 26} r={2.6} f="var(--success)" />
      <R x={x + 88} y={y + 23} w={10} h={5} rx={2} f="#000" o={0.25} />
    </g>
  );
}

/* ------------------------------------------------------------------ */
/* Filing cabinet                                                       */
/* ------------------------------------------------------------------ */

export type CabinetKind = "drawers" | "catalogue" | "chest" | "seeds" | "tower";

export function Cabinet({ m, r = L.cabinet, kind = "drawers", body }: { m: Mat; r?: Rect; kind?: CabinetKind; body?: string }) {
  const { x, y, w, h } = r;
  const col = body ?? m.wood;
  const card = (cx: number, cy: number, cw: number, text?: string) => (
    <g>
      <R x={cx - cw / 2} y={cy} w={cw} h={8} f={m.metal} />
      <R x={cx - cw / 2 + 1.5} y={cy + 1.5} w={cw - 3} h={5} f={m.paper} />
      {text && (
        <Tx x={cx} y={cy + 5.6} size={4.4} f={m.ink} anchor="middle" weight={700} ls={0.4}>
          {text}
        </Tx>
      )}
    </g>
  );
  let fronts: ReactNode;
  if (kind === "catalogue") {
    fronts = Array.from({ length: 6 }, (_, j) =>
      Array.from({ length: 3 }, (_, i) => {
        const dw = (w - 16) / 3;
        const dh = (h - 22) / 6;
        const dx = x + 8 + i * dw;
        const dy = y + 12 + j * dh;
        return (
          <g key={`${i}-${j}`}>
            <R x={dx + 1} y={dy + 1} w={dw - 2} h={dh - 2} rx={1} f={m.woodLight} o={0.35} />
            {card(dx + dw / 2, dy + 4, dw - 10)}
            <C cx={dx + dw / 2} cy={dy + dh - 6} r={1.8} f={m.metal} />
          </g>
        );
      }),
    );
  } else if (kind === "chest") {
    fronts = Array.from({ length: 6 }, (_, j) => {
      const dh = (h - 22) / 6;
      const dy = y + 12 + j * dh;
      return (
        <g key={j}>
          <R x={x + 6} y={dy + 1} w={w - 12} h={dh - 2} rx={1} f={m.woodLight} o={0.3} />
          <R x={x + w / 2 - 10} y={dy + dh / 2 - 1.5} w={20} h={3} rx={1.5} f={m.metal} />
        </g>
      );
    });
  } else if (kind === "seeds") {
    const tints = ["#f4a261", "#e9c46a", "#90be6d", "#f28482"];
    fronts = Array.from({ length: 4 }, (_, j) =>
      Array.from({ length: 2 }, (_, i) => {
        const dw = (w - 14) / 2;
        const dh = (h - 22) / 4;
        const dx = x + 7 + i * dw;
        const dy = y + 12 + j * dh;
        return (
          <g key={`${i}-${j}`}>
            <R x={dx + 1} y={dy + 1} w={dw - 2} h={dh - 2} rx={1.5} f={m.woodLight} o={0.4} />
            <R x={dx + 8} y={dy + 5} w={dw - 16} h={12} f={tints[(i + j) % 4]} />
            <C cx={dx + dw / 2} cy={dy + dh - 8} r={2} f={m.metal} />
          </g>
        );
      }),
    );
  } else {
    const tower = kind === "tower";
    const tints = [mix("var(--primary)", 55, "#fff"), mix("var(--accent)", 55, "#fff"), mix("var(--secondary)", 55, "#fff")];
    fronts = Array.from({ length: 3 }, (_, j) => {
      const dh = (h - 22) / 3;
      const dy = y + 12 + j * dh;
      return (
        <g key={j}>
          <R x={x + 6} y={dy + 2} w={w - 12} h={dh - 4} rx={tower ? 4 : 2} f={tower ? tints[j] : m.woodLight} o={tower ? 0.9 : 0.35} />
          <R x={x + w / 2 - 12} y={dy + dh / 2 + 4} w={24} h={5} rx={2.5} f={tower ? "#fff" : m.metal} o={tower ? 0.7 : 1} />
          {!tower && card(x + w / 2, dy + 8, 30, j === 0 ? "HISTORY" : undefined)}
        </g>
      );
    });
  }
  return (
    <g>
      <R x={x + 4} y={y + 5} w={w} h={h} f="#000" o={0.15} />
      <R x={x} y={y + 4} w={w} h={h - 4} rx={3} f={col} />
      <R x={x - 3} y={y} w={w + 6} h={7} rx={2} f={kind === "tower" ? "#fff" : m.woodDark} o={kind === "tower" ? 0.8 : 1} />
      {fronts}
      {kind === "catalogue" && (
        <Tx x={x + w / 2} y={y + h - 3} size={5} f={m.paper} anchor="middle" ls={1} o={0.8}>
          HISTORY
        </Tx>
      )}
    </g>
  );
}

/* ------------------------------------------------------------------ */
/* Plant                                                                */
/* ------------------------------------------------------------------ */

function Leaf({ x, y, a, s = 1, f = LEAF }: { x: number; y: number; a: number; s?: number; f?: string }) {
  return (
    <g transform={`translate(${x} ${y}) rotate(${a}) scale(${s})`}>
      <P d="M0 0 C5 -6 14 -6 19 0 C14 6 5 6 0 0 Z" f={f} />
      <Ln x1={1} y1={0} x2={16} y2={0} s={LEAF_DARK} sw={0.7} o={0.7} />
    </g>
  );
}

function Flower({ x, y, s = 1 }: { x: number; y: number; s?: number }) {
  return (
    <g transform={`translate(${x} ${y}) scale(${s})`}>
      {Array.from({ length: 5 }, (_, i) => (
        <E key={i} cx={0} cy={-5} rx={3.2} ry={5} f={PETAL} t={`rotate(${i * 72})`} />
      ))}
      <C cx={0} cy={0} r={2.6} f="#ffd166" />
    </g>
  );
}

/** Stems and leaves for a plant rooted at (x, y), by stage. */
export function PlantGrowth({ stage, x, y, s = 1 }: { stage: number; x: number; y: number; s?: number }) {
  const stem = (d: string, k: string) => <P key={k} d={d} f="none" s={LEAF_DARK} sw={2.2 / s} />;
  let parts: ReactNode = null;
  if (stage === 1) {
    parts = (
      <>
        {stem("M0 0 V-12", "s")}
        <Leaf x={0} y={-12} a={-35} s={0.55} />
        <Leaf x={0} y={-12} a={-145} s={0.55} />
      </>
    );
  } else if (stage === 2) {
    parts = (
      <>
        {stem("M0 0 C-3 -14 3 -26 0 -40", "s")}
        <Leaf x={-1} y={-12} a={-160} s={0.8} />
        <Leaf x={1} y={-18} a={-20} s={0.8} />
        <Leaf x={0} y={-30} a={-150} s={0.7} />
        <Leaf x={0} y={-36} a={-35} s={0.7} />
        <Leaf x={0} y={-40} a={-95} s={0.45} />
      </>
    );
  } else if (stage >= 3) {
    parts = (
      <>
        {stem("M0 0 C-4 -30 4 -60 0 -88", "a")}
        {stem("M0 0 C-10 -20 -24 -40 -30 -62", "b")}
        {stem("M0 0 C10 -20 22 -38 30 -58", "c")}
        {[
          [-6, -18, -160, 1],
          [6, -22, -20, 1],
          [-14, -34, -150, 0.95],
          [14, -36, -30, 0.95],
          [-2, -48, -140, 0.9],
          [2, -56, -40, 0.9],
          [-26, -52, -120, 0.85],
          [26, -48, -60, 0.85],
          [-1, -72, -130, 0.8],
          [1, -78, -50, 0.8],
          [-30, -62, -100, 0.7],
          [30, -58, -80, 0.7],
        ].map(([lx, ly, a, ls], i) => (
          <Leaf key={i} x={lx} y={ly} a={a} s={ls} f={i % 3 === 0 ? LEAF_DARK : LEAF} />
        ))}
        {stage >= 4 && (
          <>
            <Flower x={0} y={-90} />
            <Flower x={-31} y={-64} s={0.85} />
            <Flower x={31} y={-60} s={0.85} />
            <Flower x={-12} y={-44} s={0.6} />
          </>
        )}
      </>
    );
  }
  return (
    <g transform={`translate(${x} ${y}) scale(${s})`}>
      <g className="rm-sway">{parts}</g>
    </g>
  );
}

export function plantLabel(c: ArtCtx): string {
  const n = c.data.plantCount;
  return `Plant: ${n} spaced review${n === 1 ? "" : "s"} (${PLANT_STAGES[c.plant]})`;
}

export function Plant({ c, m, r = L.plant }: { c: ArtCtx; m: Mat; r?: Rect }) {
  const cx = r.x + r.w / 2;
  const top = FLOOR - 46;
  const label = plantLabel(c);
  return (
    <g role="img" aria-label={label}>
      <title>{label}</title>
      <E cx={cx} cy={FLOOR + 3} rx={34} ry={5} f="#000" o={0.18} />
      <PlantGrowth stage={c.plant} x={cx} y={top + 2} />
      <P d={`M${cx - 30} ${top + 6} L${cx - 23} ${FLOOR} H${cx + 23} L${cx + 30} ${top + 6} Z`} f={m.pot} />
      <R x={cx - 34} y={top - 2} w={68} h={10} rx={2} f={m.pot} />
      <R x={cx - 34} y={top - 2} w={68} h={3} f="#fff" o={0.15} />
      <P d={`M${cx - 30} ${top + 10} L${cx - 26} ${FLOOR - 4}`} f="none" s="#fff" sw={3} o={0.12} />
      <E cx={cx} cy={top} rx={29} ry={3.5} f="#4a3426" />
      {c.plant === 0 && (
        <g>
          <R x={cx + 12} y={top - 26} w={2} h={26} f={m.woodLight} />
          <R x={cx + 4} y={top - 32} w={18} h={10} rx={1} f={m.paper} s="#000" sw={0.4} />
          <C cx={cx - 8} cy={top - 1.5} r={2.2} f="#8a6a52" />
        </g>
      )}
    </g>
  );
}
