/**
 * room.dorm: a soft painted wall, fairy lights, maths posters, a bed in the
 * foreground and a beanbag.
 */

import type { ArtCtx, RoomTheme } from "../model";
import { C, E, P, R, Tx, mix } from "../svg";
import { Wall, type Mat } from "../parts";
import { classicScene } from "./classic";

const DORM: Mat = {
  wall: mix("var(--surface)", 55, "#dfe6f3"),
  wallLow: mix("var(--surface)", 55, "#dfe6f3"),
  rail: "#ffffff",
  floor: mix("var(--primary)", 16, "#8d8aa6"),
  floorLine: "#6f6c8a",
  wood: "#d8b98a",
  woodDark: "#b8946a",
  woodLight: "#e9d2a8",
  trim: "#f4f1ea",
  metal: "#b0b4bf",
  paper: "#ffffff",
  cork: "#c9a27a",
  ink: "#2b2b3a",
  pot: mix("var(--accent)", 45, "#e8e0f0"),
  rug: mix("var(--accent)", 35, "#f2e9f7"),
  rugEdge: "#ffffff",
  shade: mix("var(--accent)", 70, "#444"),
};

const BULBS = ["#ffd166", "var(--primary)", "var(--accent)", "#ff9ecb", "#9be7ff"];

function FairyLights({ c }: { c: ArtCtx }) {
  const spans = 5;
  const sw = 960 / spans;
  const y0 = 16;
  const sag = 26;
  const bright = c.tod === "night" || c.tod === "dusk" ? 0.55 : 0.3;
  const bulbs: { x: number; y: number; i: number }[] = [];
  for (let s = 0; s < spans; s++) {
    for (let k = 1; k <= 6; k++) {
      const t = k / 7;
      const x = s * sw + sw * t;
      const y = y0 + 2 * (1 - t) * t * (2 * sag);
      bulbs.push({ x, y, i: bulbs.length });
    }
  }
  return (
    <g>
      <path
        d={Array.from({ length: spans }, (_, s) => `M${s * sw} ${y0} Q${s * sw + sw / 2} ${y0 + 2 * sag} ${(s + 1) * sw} ${y0}`).join(" ")}
        style={{ fill: "none", stroke: "#4a4a4a", strokeWidth: 1, opacity: 0.6 }}
      />
      {bulbs.map((b) => (
        <g key={b.i} className="rm-twinkle" style={{ animationDelay: `${-(b.i % 7) * 0.45}s`, animationDuration: `${2.6 + (b.i % 3) * 0.5}s` }}>
          <C cx={b.x} cy={b.y + 4} r={8} f={BULBS[b.i % BULBS.length]} o={bright * 0.5} />
          <E cx={b.x} cy={b.y + 4} rx={2.6} ry={3.6} f={BULBS[b.i % BULBS.length]} />
          <R x={b.x - 1.5} y={b.y - 1} w={3} h={2.5} f="#4a4a4a" />
        </g>
      ))}
    </g>
  );
}

function Posters() {
  return (
    <g>
      <g transform="rotate(-2 238 64)">
        <R x={206} y={42} w={66} h={44} f="#000" o={0.12} t="translate(2 2)" />
        <R x={206} y={42} w={66} h={44} f={mix("var(--primary)", 70, "#1f2340")} />
        <Tx x={239} y={70} size={13} f="#fff" anchor="middle" weight={700}>
          e
          <tspan dy={-6} fontSize={8}>
            iπ
          </tspan>
          <tspan dy={6}>+1=0</tspan>
        </Tx>
        <C cx={210} cy={45} r={1.8} f="#c0c0c0" />
        <C cx={268} cy={45} r={1.8} f="#c0c0c0" />
      </g>
      <g transform="rotate(3 312 66)">
        <R x={284} y={46} w={56} h={40} f={mix("var(--accent)", 55, "#ffb38a")} />
        <C cx={322} cy={62} r={8} f="#fff3c4" />
        <P d="M284 86 L304 62 L316 74 L328 60 L340 72 V86 Z" f="#3d3b5c" />
        <P d="M284 86 L296 76 L308 86 Z" f="#2b2a44" />
      </g>
    </g>
  );
}

function Bed() {
  const duvet = mix("var(--primary)", 45, "#e9e4f4");
  return (
    <g>
      <E cx={80} cy={538} rx={120} ry={8} f="#000" o={0.22} />
      <R x={-16} y={372} w={22} h={168} rx={4} f={DORM.woodDark} />
      <R x={-10} y={500} w={196} h={22} rx={3} f={DORM.wood} />
      <R x={-4} y={520} w={10} h={20} f={DORM.woodDark} />
      <R x={168} y={520} w={10} h={20} f={DORM.woodDark} />
      <R x={-6} y={462} w={188} h={40} rx={8} f="#f7f5fb" />
      <R x={4} y={430} w={64} h={34} rx={14} f="#ffffff" s="#d9d4e8" sw={1} />
      <P d="M40 452 Q100 438 186 448 L192 512 Q120 520 36 506 Z" f={duvet} />
      {[60, 92, 124, 156].map((x) => (
        <C key={x} cx={x} cy={472 + (x % 3) * 6} r={3} f="#fff" o={0.5} />
      ))}
      <P d="M40 452 Q100 438 186 448" f="none" s="#fff" sw={2} o={0.4} />
    </g>
  );
}

function Beanbag() {
  const col = mix("var(--accent)", 50, "#4a4a5a");
  return (
    <g>
      <E cx={628} cy={536} rx={78} ry={8} f="#000" o={0.22} />
      <P d="M552 540 C540 500 566 462 622 458 C680 454 712 494 702 540 Z" f={col} />
      <P d="M576 488 C596 470 640 466 668 482" f="none" s="#fff" sw={3} o={0.15} />
      <P d="M600 540 C604 512 620 494 640 488" f="none" s="#000" sw={1.5} o={0.15} />
      <R x={640} y={482} w={34} h={24} rx={8} f={mix("var(--primary)", 60, "#fff")} t="rotate(12 657 494)" />
    </g>
  );
}

export const dorm: RoomTheme = {
  id: "room.dorm",
  render: (c) =>
    classicScene(c, {
      m: DORM,
      wall: <Wall c={c} m={DORM} wainscot={false} stripes={false} />,
      floor: "carpet",
      curtains: mix("var(--accent)", 40, "#ffffff"),
      back: (
        <>
          <Posters />
          <FairyLights c={c} />
        </>
      ),
      door: "flat",
      bookcase: "cubes",
      cabinet: "tower",
      cabinetBody: "#f4f1ea",
      rug: (
        <g aria-hidden="true">
          <E cx={470} cy={490} rx={170} ry={28} f={DORM.rug} />
          <E cx={470} cy={490} rx={150} ry={22} f="none" s="#fff" sw={2} o={0.5} />
        </g>
      ),
      front: (
        <>
          <Bed />
          <Beanbag />
        </>
      ),
    }),
};
