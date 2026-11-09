/**
 * room.pixel-cabin: a log cabin drawn only with crisp rectangles and small
 * character bitmaps (the scene renders with shape-rendering: crispEdges).
 * Same objects and places as the illustrated rooms.
 */

import type { ReactNode } from "react";

import { chartBars, hashString, noteLines, relativeDay, seeded, type Shelf } from "../helpers";
import type { ArtCtx, RoomTheme } from "../model";
import { Books, FLOOR, L, TROPHY_TINT, STICKY, plantLabel } from "../parts";
import { HILLS, SKY, fallStyle, shade } from "../sky";
import { Bitmap, ClubLogo, R, Tx, mix } from "../svg";

const LOG = mix("var(--surface)", 10, "#8b5a33");
const LOG_D = mix("var(--surface)", 6, "#5e3a1f");
const LOG_L = mix("var(--surface)", 10, "#a8703f");
const PLANK = "#5c3a22";
const PLANK_D = "#3f2716";
const PLANK_L = "#74492b";
const FRAME = "#4a2d18";
const IRON = "#2e2e36";
const PAPER = "#f4ecd8";
const INK = "#2a1d12";
const GOLD = "#f2c14e";

const SUN = ["..SSS..", ".SSSSS.", "SSSSSSS", "SSSSSSS", "SSSSSSS", ".SSSSS.", "..SSS.."];
const MOON = ["..MMM..", ".MMM...", "MMM....", "MMM....", "MMM....", ".MMM...", "..MMM.."];
const TREE = [
  "....CCCC....",
  "..CCCCCCCC..",
  ".CCCCCCCCCC.",
  "CCCCCCCCCCCC",
  "CCCCCCCCCCCC",
  ".CCCCCCCCCC.",
  "..CCCCCCCC..",
  ".....TT.....",
  ".....TT.....",
  ".....TT.....",
  "....TTTT....",
];
const BARE = [
  "..W...W..W..",
  "..T...T..T..",
  "...T.T..T...",
  "T...TT.T...T",
  ".T...TT...T.",
  "..TT.TT.TT..",
  "....TTTT....",
  ".....TT.....",
  ".....TT.....",
  ".....TT.....",
  "....TTTT....",
];
const TROPHY = [
  "..YYYYYY..",
  "YYYWYYYYYY",
  "Y.YWYYYY.Y",
  "YYYWYYYYYY",
  "..YYTTYY..",
  "...YYYY...",
  "....YY....",
  "....YY....",
  "...YYYY...",
  "..BBBBBB..",
  "..BTTTTB..",
  "..BBBBBB..",
];
const MUG = [
  "..KKKKKKKKKKK....",
  ".MKKKKKKKKKKKM...",
  ".MMMMMMMMMMMMMHH.",
  ".YYYYYYYYYYYYY.H.",
  ".MMMMMMMMMMMMM.H.",
  ".MMMMMMMMMMMMM.H.",
  ".MMMMMMMMMMMMMHH.",
  ".MMMMMMMMMMMMM...",
  ".MMMMMMMMMMMMM...",
  ".MMMMMMMMMMMMM...",
  "..MMMMMMMMMMM....",
];
const LANTERN = [
  "...MMM...",
  "..M...M..",
  "..MMMMM..",
  ".MMMMMMM.",
  ".MGGGGGM.",
  ".MGFFFGM.",
  ".MGFWFGM.",
  ".MGFFFGM.",
  ".MGGGGGM.",
  ".MMMMMMM.",
  "..MMMMM..",
  "MMMMMMMMM",
];
const POT = [
  "PPSSSSSSSSSSPP",
  "PHHHHHHHHHHHHP",
  "PPPPPPPPPPPPPP",
  ".pppppppppppp.",
  ".pppppppppppp.",
  "..pppppppppp..",
  "..pppppppppp..",
  "..pppppppppp..",
  "...pppppppp...",
  "...pppppppp...",
];
const GROWTH: Record<number, string[]> = {
  0: ["..........w...", "..........w..."],
  1: ["....LL..LL....", ".....LLLL.....", "......SS......", "......SS......"],
  2: [
    "......LL......",
    ".....LLLL.....",
    "...LL.SS.LL...",
    "....LLSSLL....",
    "......SS......",
    "..LL..SS......",
    "...LLLSS..LL..",
    "......SSLLL...",
    "......SS......",
  ],
  3: [
    "......LL......",
    ".....LDDL.....",
    "..LL.LSSL.LL..",
    ".LDDL.SS.LDDL.",
    "..LLLLSSLLLL..",
    "......SS......",
    "LL...LSSL...LL",
    "LDL.LDSSDL.LDL",
    ".LLLL.SS.LLLL.",
    "...LL.SS.LL...",
    "..LDDLSSLDDL..",
    "...LLLSSLLL...",
    "......SS......",
    "....LLSSLL....",
    "...LDDSSDDL...",
    "......SS......",
  ],
};
const FLOWER = [".F.", "FCF", ".F."];
const CAT = [
  "...K.K..........",
  "..KKKKK.........",
  "..KkKkK...KKK...",
  "..KKKKKKKKKKKK..",
  ".KKKKKKKKKKKKKK.",
  ".KKKKKKKKKKKKKKK",
  "..KKKKKKKKKKKK.K",
];

const LEAF_PAL = { L: mix("var(--success)", 35, "#5aa83c"), D: mix("var(--success)", 25, "#2f6e26"), S: "#3d7a2a", w: "#c9a06c" };

/** Hills as 6-px columns. */
function pixelHills(x: number, y: number, w: number, h: number, base: number, amp: number, phase: number, fill: string, key: string): ReactNode {
  const cols: ReactNode[] = [];
  for (let i = 0; i < w; i += 6) {
    const top = Math.round((base - amp * Math.sin((i / w) * Math.PI * 1.6 + phase)) / 3) * 3;
    cols.push(<R key={`${key}${i}`} x={x + i} y={y + top} w={6} h={h - top} f={fill} />);
  }
  return <g>{cols}</g>;
}

function PixelSky({ c, x, y, w, h }: { c: ArtCtx; x: number; y: number; w: number; h: number }) {
  const g = SKY[c.tod];
  const bands = [g[0], mix(g[0], 50, g[1]), g[1], g[2]];
  const bh = Math.ceil(h / 4);
  const rnd = seeded(hashString(`px${c.tod}${c.season}`));
  const night = c.tod === "night";
  const [far, near] = HILLS[c.season];
  const crown: Record<string, string> = {
    spring: "#8fd16a",
    summer: "#4f9a3f",
    autumn: "#e07a2e",
    winter: "#000",
  };
  const winter = c.season === "winter";
  const n = winter ? 16 : c.season === "summer" ? 0 : 7;
  const particle = winter ? "#ffffff" : c.season === "spring" ? "#f7b6c8" : "#e8b03a";
  return (
    <g>
      {bands.map((b, i) => (
        <R key={i} x={x} y={y + i * bh} w={w} h={bh + 1} f={b} />
      ))}
      {bands.slice(1).map((b, i) =>
        Array.from({ length: Math.ceil(w / 6) }, (_, k) =>
          k % 2 ? null : <R key={`${i}-${k}`} x={x + k * 6} y={y + (i + 1) * bh - 3} w={3} h={3} f={b} />,
        ),
      )}
      {(night || c.tod !== "day") &&
        Array.from({ length: 14 }, (_, i) => (
          <R key={`s${i}`} x={x + Math.floor((rnd() * w) / 3) * 3} y={y + Math.floor((rnd() * h * 0.5) / 3) * 3} w={3} h={3} f="#fffbe8" o={night ? 0.9 : 0.35} cls={i % 3 ? undefined : "rm-twinkle"} />
        ))}
      {night ? (
        <Bitmap x={x + 24} y={y + 18} u={4} rows={MOON} pal={{ M: "#f4f1de" }} />
      ) : (
        <Bitmap
          x={x + (c.tod === "dawn" ? 18 : c.tod === "dusk" ? w - 50 : w - 60)}
          y={y + (c.tod === "day" ? 16 : h * 0.5)}
          u={4}
          rows={SUN}
          pal={{ S: c.tod === "dusk" ? "#ff9b54" : c.tod === "dawn" ? "#ffd59a" : "#fff3b0" }}
        />
      )}
      {pixelHills(x, y, w, h, h * 0.68, h * 0.06, 0.4, shade(far, c.tod), "f")}
      {pixelHills(x, y, w, h, h * 0.84, h * 0.05, 2.2, shade(near, c.tod), "n")}
      <Bitmap
        x={x + w - 60}
        y={y + h - 46}
        u={4}
        rows={winter ? BARE : TREE}
        pal={{ C: shade(crown[c.season], c.tod), T: shade("#6b4a33", c.tod), W: shade("#ffffff", c.tod) }}
      />
      {c.season === "spring" &&
        [
          [10, 8],
          [22, 12],
          [34, 6],
          [16, 18],
          [30, 20],
        ].map(([dx, dy], i) => <R key={`b${i}`} x={x + w - 60 + dx} y={y + h - 46 + dy} w={3} h={3} f={shade("#f6b8cb", c.tod)} />)}
      {Array.from({ length: n }, (_, i) => {
        const px = x + Math.floor((rnd() * w) / 3) * 3;
        const py = y + Math.floor((rnd() * h) / 3) * 3;
        const dur = 7 + rnd() * 6;
        const delay = -rnd() * 13;
        const sq = <R x={0} y={0} w={3} h={3} f={shade(particle, c.tod)} />;
        return c.motion ? (
          <g key={`p${i}`} transform={`translate(${px} ${y - 4})`}>
            <g className="rm-fall" style={fallStyle(dur, delay, h + 8, (rnd() - 0.5) * 18)}>
              {sq}
            </g>
          </g>
        ) : (
          <g key={`p${i}`} transform={`translate(${px} ${py})`}>
            {sq}
          </g>
        );
      })}
    </g>
  );
}

function Walls() {
  const logs: ReactNode[] = [];
  for (let y = 0; y < FLOOR - 8; y += 30) {
    logs.push(
      <g key={y}>
        <R x={0} y={y} w={960} h={24} f={LOG} />
        <R x={0} y={y + 3} w={960} h={3} f={LOG_L} />
        <R x={0} y={y + 24} w={960} h={6} f={LOG_D} />
      </g>,
    );
  }
  const rnd = seeded(5);
  return (
    <g aria-hidden="true">
      {logs}
      {Array.from({ length: 22 }, (_, i) => (
        <R key={i} x={Math.floor((rnd() * 950) / 3) * 3} y={Math.floor(rnd() * 14) * 30 + 12} w={6} h={3} f={LOG_D} />
      ))}
      <R x={0} y={FLOOR - 8} w={960} h={8} f={PLANK_D} />
      {Array.from({ length: 5 }, (_, j) => (
        <g key={j}>
          <R x={0} y={FLOOR + j * 20} w={960} h={18} f={j % 2 ? PLANK : PLANK_L} />
          <R x={0} y={FLOOR + j * 20 + 18} w={960} h={2} f={PLANK_D} />
          {Array.from({ length: 6 }, (_, i) => (
            <R key={i} x={((i * 168 + j * 72) % 960) + 30} y={FLOOR + j * 20} w={3} h={18} f={PLANK_D} />
          ))}
        </g>
      ))}
    </g>
  );
}

function Window({ c }: { c: ArtCtx }) {
  const { x, y, w, h } = L.window;
  const label = `Window: ${c.tod} in ${c.season}`;
  const check = mix("var(--primary)", 80, "#7a1f1f");
  const curtain = (cx: number) => (
    <g>
      <R x={cx} y={y - 12} w={30} h={h + 30} f={check} />
      {Array.from({ length: Math.ceil((h + 30) / 6) }, (_, j) =>
        Array.from({ length: 5 }, (_, i) =>
          (i + j) % 2 ? null : <R key={`${i}-${j}`} x={cx + i * 6} y={y - 12 + j * 6} w={6} h={6} f="#ffffff" o={0.35} />,
        ),
      )}
    </g>
  );
  return (
    <g role="img" aria-label={label}>
      <title>{label}</title>
      <defs>
        <clipPath id={c.id("pxwin")}>
          <rect x={x + 12} y={y + 12} width={w - 24} height={h - 24} />
        </clipPath>
      </defs>
      <g clipPath={c.url("pxwin")}>
        <PixelSky c={c} x={x + 12} y={y + 12} w={w - 24} h={h - 24} />
      </g>
      <R x={x} y={y} w={w} h={12} f={FRAME} />
      <R x={x} y={y + h - 12} w={w} h={12} f={FRAME} />
      <R x={x} y={y} w={12} h={h} f={FRAME} />
      <R x={x + w - 12} y={y} w={12} h={h} f={FRAME} />
      <R x={x + w / 2 - 3} y={y} w={6} h={h} f={FRAME} />
      <R x={x} y={y + h / 2 - 3} w={w} h={6} f={FRAME} />
      <R x={x - 12} y={y + h} w={w + 24} h={9} f={PLANK_L} />
      <R x={x - 12} y={y + h + 9} w={w + 24} h={3} f={PLANK_D} />
      <R x={x - 36} y={y - 18} w={w + 72} h={6} f={IRON} />
      {curtain(x - 30)}
      {curtain(x + w)}
    </g>
  );
}

function Door() {
  const { x, y, w, h } = L.door;
  return (
    <g>
      <R x={x - 9} y={y - 9} w={w + 18} h={h + 9} f={FRAME} />
      {Array.from({ length: 5 }, (_, i) => (
        <g key={i}>
          <R x={x + i * 26} y={y} w={24} h={h} f={i % 2 ? PLANK : PLANK_L} />
          <R x={x + i * 26 + 24} y={y} w={2} h={h} f={PLANK_D} />
        </g>
      ))}
      {[0.18, 0.78].map((f) => (
        <g key={f}>
          <R x={x} y={y + h * f} w={w} h={9} f={IRON} />
          <R x={x + 6} y={y + h * f + 3} w={3} h={3} f="#6b6b78" />
          <R x={x + w - 9} y={y + h * f + 3} w={3} h={3} f="#6b6b78" />
        </g>
      ))}
      <R x={x + w - 24} y={y + h * 0.5} w={12} h={6} f={IRON} />
      <R x={x + w - 18} y={y + h * 0.5 + 6} w={3} h={12} f={IRON} />
      <R x={x + w / 2 - 24} y={y + h * 0.36} w={48} h={15} f={GOLD} />
      <R x={x + w / 2 - 24} y={y + h * 0.36 + 12} w={48} h={3} f="#b8861f" />
      <Tx x={x + w / 2} y={y + h * 0.36 + 10} size={8} f={INK} anchor="middle" weight={700} ls={1.5}>
        QUIZ
      </Tx>
    </g>
  );
}

function Pennant({ c }: { c: ArtCtx }) {
  const { x, y, w, h } = L.pennant;
  const fill = mix("var(--surface)", 88, "var(--primary)");
  const rows: ReactNode[] = [];
  const steps = Math.floor((h - 12) / 6);
  for (let i = 0; i < steps; i++) {
    const dist = Math.abs(i - (steps - 1) / 2) / ((steps - 1) / 2);
    const len = Math.round(((w - 16) * (1 - dist)) / 6) * 6 + 6;
    rows.push(<R key={i} x={x + 12} y={y + 6 + i * 6} w={len} h={6} f={fill} />);
  }
  return (
    <g>
      <R x={x + 6} y={y} w={6} h={6} f={IRON} />
      {rows}
      <R x={x} y={y + 6} w={12} h={steps * 6} f="var(--primary)" />
      <ClubLogo name="inline" x={x + 18} y={y + h / 2 - 9} w={66} h={18} preview={c.preview} />
    </g>
  );
}

function Noticeboard({ c }: { c: ArtCtx }) {
  const { x, y, w, h } = L.noticeboard;
  const { due, nextDue, notes } = c.data;
  const rnd = seeded(9);
  const next = relativeDay(nextDue, c.now);
  const head = due === null ? "-" : due > 0 ? String(due) : "OK";
  const sub = due === null ? "reviews" : due > 0 ? (due === 1 ? "review due" : "reviews due") : "all caught up";
  const slots = [
    [x + 90, y + 12],
    [x + 126, y + 18],
    [x + 96, y + 60],
  ] as const;
  return (
    <g>
      <R x={x} y={y} w={w} h={h} f={PLANK_D} />
      <R x={x + 9} y={y + 9} w={w - 18} h={h - 18} f="#b98a5a" />
      {Array.from({ length: 36 }, (_, i) => (
        <R key={i} x={x + 9 + Math.floor((rnd() * (w - 21)) / 3) * 3} y={y + 9 + Math.floor((rnd() * (h - 21)) / 3) * 3} w={3} h={3} f="#8f6640" />
      ))}
      <R x={x + 15} y={y + 15} w={66} h={54} f={PAPER} />
      <R x={x + 15} y={y + 15} w={66} h={9} f="var(--primary)" />
      <Tx x={x + 48} y={y + 22} size={6.5} f="#fff" anchor="middle" weight={700} ls={1}>
        TODAY
      </Tx>
      <Tx x={x + 48} y={y + 47} size={18} f="var(--primary)" anchor="middle" weight={700}>
        {head}
      </Tx>
      <Tx x={x + 48} y={y + 57} size={6.5} f={INK} anchor="middle">
        {sub}
      </Tx>
      {next && (due ?? 0) === 0 && (
        <Tx x={x + 48} y={y + 65} size={5.5} f={INK} anchor="middle" o={0.75}>
          next: {next}
        </Tx>
      )}
      {notes.slice(0, 3).map((n, i) => {
        const [nx, ny] = slots[i];
        return (
          <g key={i}>
            <R x={nx + 3} y={ny + 3} w={33} h={33} f="#000" o={0.2} />
            <R x={nx} y={ny} w={33} h={33} f={STICKY[i % STICKY.length]} />
            <R x={nx + 15} y={ny} w={3} h={3} f="var(--primary)" />
            {noteLines(n, 8, 3).map((l, k) => (
              <Tx key={k} x={nx + 16.5} y={ny + 13 + k * 8} size={6.4} f={INK} anchor="middle">
                {l}
              </Tx>
            ))}
          </g>
        );
      })}
      <R x={x + 21} y={y + 78} w={39} h={27} f="#e8f0ff" />
      {[0, 1, 2].map((i) => (
        <R key={i} x={x + 24} y={y + 84 + i * 6} w={24 + (i % 2) * 9} h={3} f="var(--primary)" o={0.6} />
      ))}
    </g>
  );
}

function Chart({ c }: { c: ArtCtx }) {
  const { x, y, w, h } = L.chart;
  const bars = c.data.topics.length ? chartBars(c.data.topics) : [0.35, 0.55, 0.45, 0.8, 0.65].map((v) => ({ value: v, share: 0.6 }));
  const ax = x + 21;
  const ay = y + h - 18;
  const bw = 15;
  return (
    <g>
      <R x={x} y={y} w={w} h={h} f={FRAME} />
      <R x={x + 9} y={y + 9} w={w - 18} h={h - 18} f={PAPER} />
      <R x={ax - 3} y={y + 15} w={3} h={ay - y - 15} f={INK} />
      <R x={ax - 3} y={ay} w={w - 36} h={3} f={INK} />
      {bars.map((b, i) => {
        const bh = Math.round((b.value * (h - 42)) / 3) * 3;
        const ih = Math.round((bh * b.share) / 3) * 3;
        const bx = ax + 3 + i * (bw + 3);
        return (
          <g key={i}>
            <R x={bx} y={ay - bh} w={bw} h={bh} f={mix("var(--primary)", 35, PAPER)} />
            <R x={bx} y={ay - ih} w={bw} h={ih} f="var(--primary)" />
            <R x={bx + 6} y={ay - bh - 6} w={3} h={3} f="var(--accent)" />
          </g>
        );
      })}
    </g>
  );
}

function Trophies({ c }: { c: ArtCtx }) {
  const { x, y, w, h } = L.trophies;
  const base = y + h - 9;
  const list = c.data.trophies.slice(0, 5);
  const label = list.length ? `Trophies: ${list.map((t) => t.title).join(", ")}` : "Trophy shelf: no milestones yet";
  const start = x + w / 2 - (list.length * 27) / 2;
  return (
    <g role="img" aria-label={label}>
      <title>{label}</title>
      <R x={x} y={base} w={w} h={9} f={PLANK_L} />
      <R x={x} y={base + 9} w={w} h={3} f={PLANK_D} />
      <R x={x + 12} y={base + 12} w={6} h={9} f={PLANK_D} />
      <R x={x + w - 18} y={base + 12} w={6} h={9} f={PLANK_D} />
      {list.map((t, i) => (
        <g key={t.id}>
          <title>{t.title}</title>
          <Bitmap x={start + i * 27 + 1} y={base - 36} u={3} rows={TROPHY} pal={{ Y: GOLD, W: "#fff4c2", B: "#5b3b22", T: TROPHY_TINT[t.id] ?? "var(--primary)" }} />
        </g>
      ))}
    </g>
  );
}

function Bookcase({ c }: { c: ArtCtx }) {
  const { x, y, w, h } = L.bookcase;
  const n = 4;
  const top = y + 12;
  const comp = (h - 24 - (n - 1) * 9) / n;
  const shelves: Shelf[] = Array.from({ length: n }, (_, i) => ({ x: x + 12, base: top + comp * (i + 1) + 9 * i, width: w - 24, height: comp - 6 }));
  return (
    <g>
      <title>{c.data.topics.length ? `${c.data.topics.length} topics practised` : "No topics practised yet"}</title>
      <R x={x} y={y} w={w} h={h} f={FRAME} />
      <R x={x + 9} y={top} w={w - 18} h={h - 24} f={PLANK_D} />
      {shelves.slice(0, -1).map((s, i) => (
        <R key={i} x={x + 6} y={s.base} w={w - 12} h={9} f={PLANK_L} />
      ))}
      <R x={x - 6} y={y - 3} w={w + 12} h={12} f={PLANK_L} />
      <R x={x - 3} y={y + h - 12} w={w + 6} h={12} f={PLANK_L} />
      <Books c={c} shelves={shelves} />
    </g>
  );
}

function Desk() {
  const { x, y, w, h } = L.desk;
  return (
    <g aria-hidden="true">
      <R x={x + 6} y={FLOOR} w={w - 12} h={6} f="#000" o={0.25} />
      <R x={x + 9} y={y + 12} w={15} h={h - 12} f={PLANK_D} />
      <R x={x + w - 24} y={y + 12} w={15} h={h - 12} f={PLANK_D} />
      <R x={x + 6} y={y + 12} w={w - 12} h={24} f={PLANK} />
      <R x={x + w / 2 - 60} y={y + 18} w={120} h={12} f={PLANK_L} />
      <R x={x + w / 2 - 6} y={y + 21} w={12} h={6} f={GOLD} />
      <R x={x - 9} y={y} w={w + 18} h={12} f={PLANK_L} />
      <R x={x - 9} y={y + 9} w={w + 18} h={3} f={PLANK_D} />
    </g>
  );
}

function Lantern({ c }: { c: ArtCtx }) {
  const x = L.lamp.x + 30;
  const y = L.lamp.y + 58;
  const on = c.lampOn;
  return (
    <g>
      {on && (
        <g className="rm-glow">
          {[48, 36, 24].map((r, i) => (
            <R key={r} x={x + 18 - r} y={y + 22 - r} w={r * 2} h={r * 2} f="#ffd98a" o={0.08 + i * 0.05} />
          ))}
        </g>
      )}
      <Bitmap x={x} y={y} u={4} rows={LANTERN} pal={{ M: IRON, G: on ? "#ffe9a8" : "#9fb8c0", F: on ? "#ff9f1c" : "#9fb8c0", W: on ? "#fff6c9" : "#9fb8c0" }} />
    </g>
  );
}

function Mug({ c }: { c: ArtCtx }) {
  const x = L.mug.x + 6;
  const y = L.mug.y + L.mug.h - 33;
  return (
    <g>
      {[0, 1].map((i) => (
        <g key={i} className="rm-steam" style={{ animationDelay: `${i * -1.8}s` }}>
          <R x={x + 12 + i * 15} y={y - 9} w={3} h={3} f="var(--muted)" />
          <R x={x + 15 + i * 15} y={y - 15} w={3} h={3} f="var(--muted)" />
          <R x={x + 12 + i * 15} y={y - 21} w={3} h={3} f="var(--muted)" />
        </g>
      ))}
      <Bitmap x={x} y={y} u={3} rows={MUG} pal={{ K: "#5b3a29", M: mix("var(--surface)", 90, "var(--text)"), H: mix("var(--surface)", 75, "var(--text)"), Y: "#ffd60a" }} />
      <ClubLogo name="coding" x={x + 5} y={y + 13} w={33} h={12} preview={c.preview} />
    </g>
  );
}

function Printer() {
  const { x, y, h } = L.printer;
  const body = mix("var(--surface)", 65, "#c9ced6");
  return (
    <g>
      <R x={x + 27} y={y} w={63} h={24} f={PAPER} />
      {[0, 1, 2].map((i) => (
        <R key={i} x={x + 33} y={y + 6 + i * 6} w={45 - i * 9} h={2} f={INK} o={0.35} />
      ))}
      <R x={x + 3} y={y + 18} w={114} h={39} f={body} />
      <R x={x + 3} y={y + 18} w={114} h={9} f="#000" o={0.12} />
      <R x={x + 18} y={y + 39} w={84} h={6} f={IRON} />
      <R x={x + 24} y={y + 42} w={72} h={h - 42} f={PAPER} />
      <R x={x + 30} y={y + 48} w={6} h={9} f="var(--primary)" />
      <R x={x + 42} y={y + 49} w={42} h={2} f={INK} o={0.4} />
      <R x={x + 42} y={y + 54} w={30} h={2} f={INK} o={0.4} />
      <R x={x + 102} y={y + 24} w={6} h={6} f="var(--success)" />
    </g>
  );
}

function Cabinet() {
  const { x, y, w, h } = L.cabinet;
  const dh = (h - 18) / 3;
  return (
    <g>
      <R x={x} y={y + 6} w={w} h={h - 6} f={PLANK} />
      <R x={x - 3} y={y} w={w + 6} h={9} f={PLANK_D} />
      {[0, 1, 2].map((j) => {
        const dy = y + 12 + j * dh;
        return (
          <g key={j}>
            <R x={x + 6} y={dy + 3} w={w - 12} h={dh - 6} f={PLANK_L} />
            <R x={x + w / 2 - 12} y={dy + dh / 2 + 6} w={24} h={6} f={GOLD} />
            <R x={x + w / 2 - 18} y={dy + 9} w={36} h={9} f={PAPER} />
            {j === 0 && (
              <Tx x={x + w / 2} y={dy + 16} size={5} f={INK} anchor="middle" weight={700} ls={0.4}>
                HISTORY
              </Tx>
            )}
          </g>
        );
      })}
    </g>
  );
}

function Plant({ c }: { c: ArtCtx }) {
  const cx = L.plant.x + L.plant.w / 2;
  const potX = cx - 28;
  const potY = FLOOR - 40;
  const rows = GROWTH[Math.min(3, c.plant)];
  const label = plantLabel(c);
  return (
    <g role="img" aria-label={label}>
      <title>{label}</title>
      <g className="rm-sway">
        <Bitmap x={potX} y={potY - rows.length * 4} u={4} rows={rows} pal={LEAF_PAL} />
        {c.plant >= 4 &&
          [
            [6, -66],
            [0, -42],
            [11, -42],
            [2, -18],
          ].map(([gx, gy], i) => (
            <Bitmap key={i} x={potX + gx * 4 - 2} y={potY + gy} u={4} rows={FLOWER} pal={{ F: mix("var(--accent)", 55, "#f49ac1"), C: "#ffd166" }} />
          ))}
      </g>
      <Bitmap x={potX} y={potY} u={4} rows={POT} pal={{ P: "#c0653f", H: "#d98a64", p: "#a5502f", S: "#4a3426" }} />
    </g>
  );
}

function Rug() {
  const x = 312;
  const y = 468;
  const w = 324;
  const h = 48;
  const diamonds: ReactNode[] = [];
  for (let i = 0; i < 9; i++) {
    const cx = x + 36 + i * 32;
    diamonds.push(
      <g key={i}>
        <R x={cx - 3} y={y + 15} w={6} h={3} f="var(--primary)" />
        <R x={cx - 6} y={y + 18} w={12} h={3} f="var(--primary)" />
        <R x={cx - 9} y={y + 21} w={18} h={6} f="var(--primary)" />
        <R x={cx - 6} y={y + 27} w={12} h={3} f="var(--primary)" />
        <R x={cx - 3} y={y + 30} w={6} h={3} f="var(--primary)" />
      </g>,
    );
  }
  return (
    <g aria-hidden="true">
      <R x={x + 6} y={y + h} w={w} h={6} f="#000" o={0.25} />
      <R x={x} y={y} w={w} h={h} f="var(--primary)" />
      <R x={x + 6} y={y + 6} w={w - 12} h={h - 12} f={mix("var(--accent)", 60, "#f4ecd8")} />
      <R x={x + 12} y={y + 12} w={w - 24} h={h - 24} f={mix("var(--primary)", 25, "#f4ecd8")} />
      {diamonds}
      {Array.from({ length: 8 }, (_, i) => (
        <g key={i}>
          <R x={x - 6} y={y + 3 + i * 6} w={6} h={3} f="#f4ecd8" />
          <R x={x + w} y={y + 3 + i * 6} w={6} h={3} f="#f4ecd8" />
        </g>
      ))}
    </g>
  );
}

export const pixelCabin: RoomTheme = {
  id: "room.pixel-cabin",
  pixel: true,
  render: (c) => (
    <>
      <Walls />
      <Window c={c} />
      {c.hs("pennant", L.pennant, <Pennant c={c} />)}
      {c.hs("noticeboard", L.noticeboard, <Noticeboard c={c} />)}
      {c.hs("chart", L.chart, <Chart c={c} />)}
      <Trophies c={c} />
      {c.hs("bookcase", L.bookcase, <Bookcase c={c} />)}
      {c.hs("door", L.door, <Door />)}
      <Rug />
      <Bitmap x={566} y={484} u={3} rows={CAT} pal={{ K: "#d98a3a", k: "#7a4a1f" }} />
      <Desk />
      {c.hs("lamp", L.lamp, <Lantern c={c} />)}
      {c.hs("mug", L.mug, <Mug c={c} />)}
      {c.hs("printer", L.printer, <Printer />)}
      {c.hs("cabinet", L.cabinet, <Cabinet />)}
      <Plant c={c} />
      <PixelDim c={c} />
    </>
  ),
};

function PixelDim({ c }: { c: ArtCtx }) {
  const dark = c.tod === "night" ? 1 : c.tod === "dusk" ? 0.55 : c.tod === "dawn" ? 0.25 : 0;
  if (!dark) return null;
  return (
    <g className="rm-ambient" aria-hidden="true">
      <rect x={0} y={0} width={960} height={540} style={{ fill: "#0a0f2c", opacity: (c.lampOn ? 0.16 : 0.3) * dark }} />
    </g>
  );
}
