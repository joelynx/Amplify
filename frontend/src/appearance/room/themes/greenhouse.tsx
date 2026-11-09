/**
 * room.greenhouse: a wall of glass panes (the whole wall is the window), a
 * low brick wall, hanging plants, a potting bench and a watering can.
 */

import type { ArtCtx, RoomTheme } from "../model";
import { SkyIn } from "../sky";
import { E, Ln, P, R, mix } from "../svg";
import { FLOOR, LEAF, LEAF_DARK, type Mat } from "../parts";
import { classicScene } from "./classic";

const GREEN: Mat = {
  wall: "#dfeee6",
  wallLow: mix("var(--surface)", 12, "#b5654a"),
  rail: mix("var(--surface)", 40, "#e9f0ea"),
  floor: mix("var(--surface)", 15, "#c47a55"),
  floorLine: "#9a5a3c",
  wood: "#a77b4f",
  woodDark: "#7a5534",
  woodLight: "#c9a06c",
  trim: mix("var(--surface)", 40, "#e9f0ea"),
  metal: "#9aa5a0",
  paper: "#fbf8ee",
  cork: "#c9a77c",
  ink: "#2f3a2f",
  pot: "#c0653f",
  rug: "#7d9a6a",
  rugEdge: "#e9f0ea",
  shade: mix("var(--primary)", 50, "#3e6b55"),
};

const GLASS_H = 334;

function GlassWall({ c }: { c: ArtCtx }) {
  const label = `Glass wall: ${c.tod} in ${c.season}`;
  const frame = mix("var(--surface)", 30, "#eef3ee");
  return (
    <g role="img" aria-label={label}>
      <title>{label}</title>
      <SkyIn c={c} x={0} y={0} w={960} h={GLASS_H} name="glass" horizon={0.74} tree={0.4} />
      <R x={0} y={0} w={960} h={GLASS_H} f="#dff3f0" o={0.1} />
      {[0.08, 0.36, 0.64].map((f) => (
        <P key={f} d={`M${960 * f} ${GLASS_H} L${960 * f + 120} 0 L${960 * f + 150} 0 L${960 * f + 30} ${GLASS_H} Z`} f="#fff" o={0.06} />
      ))}
      {Array.from({ length: 9 }, (_, i) => (
        <R key={i} x={i * 120 - 4} y={0} w={8} h={GLASS_H} f={frame} />
      ))}
      <R x={956} y={0} w={8} h={GLASS_H} f={frame} />
      {[112, 224].map((y) => (
        <R key={y} x={0} y={y - 3} w={960} h={6} f={frame} />
      ))}
      <R x={0} y={0} w={960} h={10} f={frame} />
      <R x={0} y={GLASS_H - 6} w={960} h={8} f={frame} />
      <R x={0} y={GLASS_H + 2} w={960} h={FLOOR - GLASS_H - 2} f={GREEN.wallLow} />
      {Array.from({ length: 5 }, (_, j) => (
        <g key={j}>
          <Ln x1={0} y1={GLASS_H + 22 + j * 20} x2={960} y2={GLASS_H + 22 + j * 20} s="#000" sw={1} o={0.12} />
          {Array.from({ length: 21 }, (_, i) => {
            const x = i * 48 + (j % 2) * 24;
            return <Ln key={i} x1={x} y1={GLASS_H + 2 + j * 20} x2={x} y2={GLASS_H + 22 + j * 20} s="#000" sw={1} o={0.12} />;
          })}
        </g>
      ))}
      <R x={0} y={FLOOR - 12} w={960} h={12} f={GREEN.woodDark} />
    </g>
  );
}

function Hanging({ x, drop, s = 1 }: { x: number; drop: number; s?: number }) {
  const py = 10 + drop;
  return (
    <g>
      <Ln x1={x} y1={10} x2={x - 12 * s} y2={py} s="#6b6b6b" sw={1} />
      <Ln x1={x} y1={10} x2={x + 12 * s} y2={py} s="#6b6b6b" sw={1} />
      {[-20, -8, 6, 18].map((dx, i) => (
        <P key={dx} d={`M${x + dx * s * 0.6} ${py + 6} q${dx * 0.3} ${30 + i * 8} ${dx * 0.1} ${50 + i * 12}`} f="none" s={LEAF_DARK} sw={1.4} />
      ))}
      {[-20, -8, 6, 18].map((dx, i) =>
        Array.from({ length: 4 }, (_, k) => (
          <E key={`${i}-${k}`} cx={x + dx * s * 0.6 + (k % 2 ? 3 : -3)} cy={py + 18 + k * (10 + i * 2.5)} rx={4} ry={2.6} f={k % 2 ? LEAF : LEAF_DARK} t={`rotate(${k % 2 ? 30 : -30} ${x + dx * s * 0.6} ${py + 18 + k * (10 + i * 2.5)})`} />
        )),
      )}
      <P d={`M${x - 16 * s} ${py} h${32 * s} l-${4 * s} ${18 * s} h-${24 * s} Z`} f={GREEN.pot} />
      <R x={x - 18 * s} y={py - 3} w={36 * s} h={5} rx={1} f={GREEN.pot} />
      <E cx={x} cy={py - 4} rx={14 * s} ry={6} f={LEAF} />
    </g>
  );
}

function Fern() {
  const leaves: [number, number][] = [
    [-84, 0.8],
    [-62, 1],
    [-40, 1.1],
    [-16, 1.15],
    [8, 1.05],
    [30, 0.9],
    [50, 0.75],
  ];
  return (
    <g>
      <E cx={40} cy={538} rx={70} ry={8} f="#000" o={0.2} />
      {leaves.map(([a, s], i) => (
        <g key={a} transform={`translate(40 500) rotate(${a}) scale(${s})`}>
          <P d="M0 0 C-3 -30 -2 -60 0 -84" f="none" s={LEAF_DARK} sw={2.5} />
          <P d="M0 -70 C-34 -84 -38 -132 0 -160 C38 -132 34 -84 0 -70 Z" f={i % 2 ? LEAF : LEAF_DARK} />
          <Ln x1={0} y1={-72} x2={0} y2={-156} s={i % 2 ? LEAF_DARK : LEAF} sw={1.4} />
          {[-1, 1].map((d) =>
            [92, 112, 132].map((y) => <Ln key={`${d}${y}`} x1={d * 6} y1={-y} x2={d * 22} y2={-y - 8} s={mix("var(--surface)", 40, "#dff3f0")} sw={2} o={0.55} />),
          )}
        </g>
      ))}
      <P d="M-6 500 h92 l-8 40 h-76 Z" f="#b85a3a" />
      <R x={-10} y={494} w={100} h={10} rx={2} f="#c0653f" />
    </g>
  );
}

function WateringCan() {
  const col = mix("var(--primary)", 45, "#5d8a7a");
  return (
    <g>
      <E cx={620} cy={512} rx={40} ry={5} f="#000" o={0.2} />
      <P d="M596 476 h48 l-4 36 h-40 Z" f={col} />
      <P d="M644 484 L676 462 L680 468 L648 494 Z" f={col} />
      <R x={672} y={456} w={12} h={8} rx={2} f={col} t="rotate(-35 678 460)" />
      <P d="M600 476 Q620 452 640 476" f="none" s={col} sw={4} />
      <R x={596} y={476} w={48} h={5} f="#fff" o={0.2} />
    </g>
  );
}

function Stool() {
  return (
    <g aria-hidden="true">
      <E cx={470} cy={456} rx={34} ry={5} f="#000" o={0.18} />
      <Ln x1={452} y1={392} x2={444} y2={456} s={GREEN.woodDark} sw={5} />
      <Ln x1={488} y1={392} x2={496} y2={456} s={GREEN.woodDark} sw={5} />
      <Ln x1={448} y1={430} x2={492} y2={430} s={GREEN.woodDark} sw={3} />
      <R x={436} y={384} w={68} h={10} rx={4} f={GREEN.wood} />
    </g>
  );
}

export const greenhouse: RoomTheme = {
  id: "room.greenhouse",
  render: (c) =>
    classicScene(c, {
      m: GREEN,
      wall: <GlassWall c={c} />,
      window: null,
      floor: "tiles",
      back: (
        <>
          <Hanging x={430} drop={56} />
          <Hanging x={548} drop={84} s={0.85} />
          <Hanging x={890} drop={0} s={0.7} />
        </>
      ),
      door: "glass",
      desk: "bench",
      bookcase: "crate",
      cabinet: "seeds",
      cabinetBody: GREEN.woodDark,
      rug: (
        <g aria-hidden="true">
          <R x={60} y={474} w={110} h={20} rx={3} f="#8a7a52" />
          <R x={66} y={478} w={98} h={12} rx={2} f="none" s="#c9b27a" sw={1} />
        </g>
      ),
      chair: <Stool />,
      front: (
        <>
          <WateringCan />
          <Fern />
        </>
      ),
    }),
};
