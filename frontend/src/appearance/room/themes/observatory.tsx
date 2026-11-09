/**
 * room.observatory: a dome with ribs, an open slit onto the sky (the window:
 * time of day and season), a refractor on its mount, star charts and an orrery.
 */

import type { ArtCtx, RoomTheme } from "../model";
import { seeded } from "../helpers";
import { SkyIn } from "../sky";
import { C, E, Ln, P, R, Tx, mix } from "../svg";
import { Wall, type Mat } from "../parts";
import { classicScene } from "./classic";

const OBS: Mat = {
  wall: mix("var(--background)", 14, "#1c2444"),
  wallLow: mix("var(--background)", 8, "#141a32"),
  rail: "#b08d4a",
  floor: mix("var(--background)", 8, "#2a2f45"),
  floorLine: "#4f5675",
  wood: "#4a3020",
  woodDark: "#2e1d14",
  woodLight: "#6a4630",
  trim: "#3a4060",
  metal: "#c9a24a",
  paper: "#efe8d6",
  cork: "#6b5a46",
  ink: "#1d1d2b",
  pot: "#5a4a6a",
  rug: mix("var(--primary)", 20, "#262d52"),
  rugEdge: "#c9a24a",
  shade: "#b08d4a",
};

const SLIT = { x: 445, y: 0, w: 80, h: 252 };

function Ribs() {
  return (
    <g>
      {[60, 180, 300, 660, 780, 900].map((x) => (
        <P key={x} d={`M${x} 0 Q${x + (x < 480 ? -30 : 30)} 170 ${x} 330`} f="none" s="#c9d2ff" sw={3} o={0.08} />
      ))}
      {[70, 160, 250].map((y) => (
        <P key={y} d={`M0 ${y + 40} Q480 ${y - 30} 960 ${y + 40}`} f="none" s="#c9d2ff" sw={2} o={0.06} />
      ))}
    </g>
  );
}

function StarPoster({ x, y, w, h, seed }: { x: number; y: number; w: number; h: number; seed: number }) {
  const rnd = seeded(seed);
  const pts = Array.from({ length: 6 }, () => [x + 6 + rnd() * (w - 12), y + 14 + rnd() * (h - 30)] as const);
  return (
    <g>
      <R x={x + 2} y={y + 3} w={w} h={h} f="#000" o={0.2} />
      <R x={x} y={y} w={w} h={h} f="#10173a" s="#c9a24a" sw={1.5} />
      {Array.from({ length: 16 }, (_, i) => (
        <C key={i} cx={x + 3 + rnd() * (w - 6)} cy={y + 3 + rnd() * (h - 6)} r={0.5 + rnd() * 0.6} f="#e8e6ff" o={0.6} />
      ))}
      <polyline points={pts.map((p) => p.join(",")).join(" ")} style={{ fill: "none", stroke: "#9fb0ff", strokeWidth: 0.8, opacity: 0.8 }} />
      {pts.map(([px, py], i) => (
        <C key={i} cx={px} cy={py} r={1.8} f="#fff7d6" />
      ))}
      <Tx x={x + w / 2} y={y + h - 5} size={5} f="#c9a24a" anchor="middle" ls={0.8}>
        {seed % 2 ? "LYRA" : "ORION"}
      </Tx>
    </g>
  );
}

function Slit({ c }: { c: ArtCtx }) {
  const { x, y, w, h } = SLIT;
  const label = `Dome slit: ${c.tod} in ${c.season}`;
  return (
    <g role="img" aria-label={label}>
      <title>{label}</title>
      <SkyIn c={c} x={x} y={y} w={w} h={h} name="slit" land={false} starry />
      <R x={x - 12} y={y} w={12} h={h + 6} f="#3a4060" />
      <R x={x + w} y={y} w={12} h={h + 6} f="#3a4060" />
      <R x={x - 12} y={y} w={3} h={h + 6} f="#fff" o={0.08} />
      {Array.from({ length: 8 }, (_, i) => (
        <g key={i}>
          <C cx={x - 6} cy={y + 16 + i * 30} r={1.6} f="#c9a24a" />
          <C cx={x + w + 6} cy={y + 16 + i * 30} r={1.6} f="#c9a24a" />
        </g>
      ))}
      <P d={`M${x - 16} ${y + h + 6} Q${x + w / 2} ${y + h + 18} ${x + w + 16} ${y + h + 6} V${y + h + 12} Q${x + w / 2} ${y + h + 24} ${x - 16} ${y + h + 12} Z`} f="#3a4060" />
    </g>
  );
}

function Telescope() {
  const tube = "#e8e2d0";
  return (
    <g>
      <R x={578} y={248} w={16} h={92} f="#3a4060" />
      <R x={562} y={238} w={48} h={16} rx={4} f="#2a2f45" />
      <g transform="translate(586 244) rotate(-122)">
        <R x={-72} y={-10} w={210} h={20} rx={3} f={tube} />
        <R x={-72} y={-10} w={210} h={5} f="#fff" o={0.25} />
        <R x={132} y={-14} w={36} h={28} rx={3} f={tube} />
        <R x={164} y={-14} w={4} h={28} f="#1d1d2b" />
        {[-20, 40, 100].map((p) => (
          <R key={p} x={p} y={-11} w={6} h={22} f="#c9a24a" />
        ))}
        <R x={-6} y={-24} w={70} h={7} rx={3} f="#c9d2e0" />
        <R x={-96} y={-5} w={26} h={10} rx={2} f="#2a2f45" />
        <R x={-104} y={-7} w={9} h={14} rx={2} f="#1d1d2b" />
      </g>
      <C cx={586} cy={244} r={9} f="#c9a24a" />
      <C cx={586} cy={244} r={3.5} f="#2a2f45" />
    </g>
  );
}

function Orrery() {
  return (
    <g>
      <R x={694} y={280} w={20} h={8} rx={2} f="#2e1d14" />
      <R x={702} y={262} w={4} h={20} f="#c9a24a" />
      <E cx={704} cy={258} rx={38} ry={10} f="none" s="#c9a24a" sw={1.2} />
      <E cx={704} cy={258} rx={24} ry={6.5} f="none" s="#c9a24a" sw={1.2} />
      <C cx={704} cy={258} r={6} f="#ffcf5a" />
      <C cx={680} cy={256} r={3} f="#7fb0ff" />
      <C cx={740} cy={261} r={3.6} f="#e07a5f" />
      <C cx={718} cy={252} r={2.2} f="#d9d4c8" />
      <Ln x1={704} y1={262} x2={680} y2={256} s="#c9a24a" sw={0.6} />
      <Ln x1={704} y1={262} x2={740} y2={261} s="#c9a24a" sw={0.6} />
    </g>
  );
}

export const observatory: RoomTheme = {
  id: "room.observatory",
  render: (c) =>
    classicScene(c, {
      m: OBS,
      wall: <Wall c={c} m={OBS} stripes={false} />,
      floor: "plates",
      back: (
        <>
          <Ribs />
          <StarPoster x={396} y={70} w={42} h={128} seed={3} />
          <StarPoster x={532} y={70} w={42} h={128} seed={8} />
        </>
      ),
      window: <Slit c={c} />,
      door: "arched",
      board: "slate",
      chart: "stars",
      lamp: "banker",
      cabinet: "chest",
      mid: <Telescope />,
      front: <Orrery />,
      rug: (
        <g aria-hidden="true">
          <E cx={470} cy={490} rx={240} ry={30} f={OBS.rug} />
          <E cx={470} cy={490} rx={220} ry={24} f="none" s="#c9a24a" sw={1.5} />
          {Array.from({ length: 12 }, (_, i) => {
            const a = (i / 12) * Math.PI * 2;
            return <C key={i} cx={470 + Math.cos(a) * 180} cy={490 + Math.sin(a) * 18} r={1.6} f="#c9a24a" />;
          })}
          <P d="M470 474 l4 12 l12 4 l-12 4 l-4 12 l-4 -12 l-12 -4 l12 -4 Z" f="#c9a24a" o={0.8} />
        </g>
      ),
    }),
};
