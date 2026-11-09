/**
 * room.study (the default: a warm wooden study with a real-time wall clock)
 * and room.library (tall shelves, a rolling ladder, a leather reading chair).
 */

import type { RoomTheme } from "../model";
import { seeded } from "../helpers";
import { C, E, Ln, P, R, mix } from "../svg";
import { WallClock, type Mat } from "../parts";
import { classicScene } from "./classic";

const STUDY: Mat = {
  wall: mix("var(--surface)", 50, "#e7d2ac"),
  wallLow: mix("var(--surface)", 25, "#a87a50"),
  rail: "#7a5032",
  floor: mix("var(--background)", 20, "#9c6b43"),
  floorLine: "#6e4a2e",
  wood: "#8b5a34",
  woodDark: "#5e3b22",
  woodLight: "#b07a4c",
  trim: mix("var(--surface)", 15, "#6e4528"),
  metal: "#c9a86a",
  paper: "#fbf6ea",
  cork: "#c49a6c",
  ink: "#3b2a1e",
  pot: "#c0653f",
  rug: mix("var(--primary)", 22, "#7a2f2f"),
  rugEdge: "#e8c98f",
  shade: mix("var(--primary)", 60, "#2d4a3e"),
};

export const study: RoomTheme = {
  id: "room.study",
  render: (c) =>
    classicScene(c, {
      m: STUDY,
      curtains: mix("var(--accent)", 40, "#8a3b3b"),
      back: <WallClock c={c} m={STUDY} cx={275} cy={50} />,
    }),
};

const LIBRARY: Mat = {
  wall: mix("var(--surface)", 28, "#2f4a3a"),
  wallLow: mix("var(--surface)", 12, "#4a2c1a"),
  rail: "#3a2214",
  floor: mix("var(--background)", 12, "#5a3a24"),
  floorLine: "#3a2416",
  wood: "#5a3420",
  woodDark: "#3a2014",
  woodLight: "#7a4a2c",
  trim: "#4a2a18",
  metal: "#c9a24a",
  paper: "#f3ead2",
  cork: "#a07850",
  ink: "#2a1c12",
  pot: "#7a4a3a",
  rug: mix("var(--primary)", 12, "#6b1f2a"),
  rugEdge: "#c9a24a",
  shade: mix("var(--success)", 25, "#2f6b45"),
};

const LEATHER = mix("var(--primary)", 14, "#6b2a22");

const OLD_BOOKS = ["#6b2a22", "#2f4a3a", "#5a3420", "#3a3f58", "#7a5a2a", "#4a2a3a", "#8a6a3a", "#2a3a4a"];

/** A high shelf of old books running along the top of the wall. */
function HighShelf() {
  const rnd = seeded(21);
  const books = [];
  let x = 194;
  let i = 0;
  while (x < 730) {
    const w = 7 + Math.floor(rnd() * 8);
    const h = 22 + Math.floor(rnd() * 14);
    if (rnd() < 0.06) {
      x += 14;
      continue;
    }
    books.push(
      <g key={i++}>
        <R x={x} y={52 - h} w={w} h={h} f={OLD_BOOKS[Math.floor(rnd() * OLD_BOOKS.length)]} />
        <R x={x} y={56 - h} w={w} h={1.5} f="#c9a24a" o={0.6} />
      </g>,
    );
    x += w + 1;
  }
  return (
    <g>
      {books}
      <R x={186} y={52} w={556} h={6} f="#5a3420" />
      <R x={186} y={58} w={556} h={2} f="#000" o={0.2} />
      {[200, 470, 728].map((bx) => (
        <P key={bx} d={`M${bx} 58 h8 l-8 10 Z`} f="#3a2014" />
      ))}
    </g>
  );
}

function Ladder() {
  const rungs = Array.from({ length: 12 }, (_, i) => i);
  const at = (t: number, x0: number, x1: number) => x0 + (x1 - x0) * t;
  return (
    <g>
      <R x={750} y={24} w={210} h={4} rx={2} f="#c9a24a" />
      <Ln x1={906} y1={26} x2={928} y2={472} s="#6a4128" sw={6} />
      <Ln x1={934} y1={26} x2={956} y2={472} s="#6a4128" sw={6} />
      {rungs.map((i) => {
        const t = (i + 0.6) / 12.4;
        const y = 26 + t * 446;
        return <Ln key={i} x1={at(t, 906, 928)} y1={y} x2={at(t, 934, 956)} y2={y} s="#7a4a2c" sw={4} />;
      })}
      <C cx={928} cy={474} r={5} f="#2a1c12" />
      <C cx={956} cy={474} r={5} f="#2a1c12" />
      <C cx={906} cy={26} r={4} f="#c9a24a" />
      <C cx={934} cy={26} r={4} f="#c9a24a" />
    </g>
  );
}

function ReadingChair() {
  const tufts = [];
  for (let j = 0; j < 2; j++) for (let i = 0; i < 4; i++) tufts.push([4 + i * 28 + (j % 2) * 14, 404 + j * 22]);
  return (
    <g>
      <E cx={60} cy={538} rx={110} ry={10} f="#000" o={0.25} />
      <R x={-20} y={384} w={140} h={112} rx={26} f={LEATHER} />
      <R x={-12} y={392} w={124} h={20} rx={10} f="#fff" o={0.08} />
      {tufts.map(([x, y], i) => (
        <C key={i} cx={x} cy={y} r={2} f="#000" o={0.3} />
      ))}
      <R x={2} y={466} w={108} h={30} rx={10} f={mix(LEATHER, 85, "#fff")} />
      <R x={-30} y={440} w={42} h={84} rx={14} f={mix(LEATHER, 90, "#000")} />
      <R x={98} y={440} w={42} h={84} rx={14} f={mix(LEATHER, 90, "#000")} />
      <R x={-22} y={498} w={164} h={28} rx={6} f={mix(LEATHER, 75, "#000")} />
      <R x={-10} y={524} w={10} h={16} f="#2a1c12" />
      <R x={122} y={524} w={10} h={16} f="#2a1c12" />
      <R x={150} y={512} w={44} h={10} rx={1} f="#7a3b2e" />
      <R x={154} y={502} w={38} h={10} rx={1} f="#2f4f5f" />
      <R x={148} y={492} w={40} h={10} rx={1} f="#c9a24a" o={0.85} />
    </g>
  );
}

function Globe() {
  return (
    <g>
      <R x={694} y={280} w={20} h={8} rx={2} f="#3a2014" />
      <R x={702} y={262} w={4} h={20} f="#c9a24a" />
      <C cx={704} cy={254} r={18} f="#3f7a8a" />
      <P d="M692 246 c6 -6 14 -4 16 2 c2 6 -6 8 -4 14 c-6 2 -12 -6 -12 -16 Z M708 258 c4 -2 10 0 9 6 c-4 4 -9 2 -9 -6 Z" f="#c9b27a" />
      <P d="M686 254 A18 18 0 0 0 722 254" f="none" s="#c9a24a" sw={2} />
      <C cx={697} cy={246} r={5} f="#fff" o={0.2} />
    </g>
  );
}

export const library: RoomTheme = {
  id: "room.library",
  render: (c) =>
    classicScene(c, {
      m: LIBRARY,
      windowKind: "arched",
      curtains: null,
      door: "double",
      lamp: "banker",
      cabinet: "catalogue",
      bookcase: "tall",
      bookcaseRect: { x: 758, y: 34, w: 170, h: 406 },
      shelves: 5,
      back: <HighShelf />,
      chair: <ChairLibrary />,
      front: (
        <>
          <Globe />
          <Ladder />
          <ReadingChair />
        </>
      ),
    }),
};

function ChairLibrary() {
  return (
    <g aria-hidden="true">
      <E cx={470} cy={454} rx={44} ry={6} f="#000" o={0.18} />
      <R x={440} y={392} w={6} h={62} f="#3a2014" />
      <R x={494} y={392} w={6} h={62} f="#3a2014" />
      <P d="M428 408 V362 Q428 346 444 346 H496 Q512 346 512 362 V408 Z" f={LEATHER} />
      {[444, 462, 480, 498].map((x) => (
        <C key={x} cx={x} cy={364} r={1.6} f="#000" o={0.3} />
      ))}
    </g>
  );
}
