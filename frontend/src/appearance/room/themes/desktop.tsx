/**
 * room.desktop: an early-2000s style desktop. The objects are desktop icons,
 * the bookshelf is an open window, the noticeboard a sticky-note gadget, the
 * pennant the logo button on the taskbar, trophies sit in the tray. The
 * wallpaper is an original rolling-hills scene that follows the time of day
 * and the season. All art is original; no operating-system artwork.
 */

import type { ReactNode } from "react";

import { abbreviate, clockText, hashString, relativeDay, seeded, type Shelf, type Season } from "../helpers";
import type { ArtCtx, Rect, RoomTheme } from "../model";
import { Books, PlantGrowth, TROPHY_TINT, Trophy, plantLabel } from "../parts";
import { Sky, Weather, shade } from "../sky";
import { C, ClubLogo, E, Ln, P, R, Tx, mix } from "../svg";

const TASK_Y = 504;

const HILL: Record<Season, [string, string, string]> = {
  spring: ["#8ed36b", "#5fb847", "#b8ec92"],
  summer: ["#5cae3c", "#3f9330", "#86cf5f"],
  autumn: ["#d9b04f", "#b9822f", "#ecd07a"],
  winter: ["#f2f6fb", "#d8e3ef", "#ffffff"],
};

const SPOT = {
  door: { x: 18, y: 16, w: 80, h: 84 },
  printer: { x: 18, y: 106, w: 80, h: 84 },
  cabinet: { x: 18, y: 196, w: 80, h: 84 },
  chart: { x: 18, y: 286, w: 80, h: 84 },
  lamp: { x: 104, y: 16, w: 80, h: 84 },
  mug: { x: 104, y: 106, w: 80, h: 84 },
  bookcase: { x: 236, y: 52, w: 420, h: 300 },
  noticeboard: { x: 690, y: 30, w: 200, h: 186 },
  pennant: { x: 0, y: TASK_Y, w: 136, h: 36 },
} as const satisfies Record<string, Rect>;

function Wallpaper({ c }: { c: ArtCtx }) {
  const [back, front, light] = HILL[c.season];
  const rnd = seeded(hashString(`desk${c.season}`));
  return (
    <g aria-hidden="true">
      <Sky c={c} x={0} y={0} w={960} h={TASK_Y} name="desk" land={false} weather={false} body={[0.92, 0.5]} bodySize={0.05} />
      <defs>
        <linearGradient id={c.id("hill")} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" style={{ stopColor: shade(light, c.tod) }} />
          <stop offset="0.35" style={{ stopColor: shade(front, c.tod) }} />
          <stop offset="1" style={{ stopColor: shade(mix(front, 80, "#000"), c.tod) }} />
        </linearGradient>
      </defs>
      <P d="M0 330 C200 250 420 262 620 300 S900 332 960 300 V504 H0 Z" f={shade(back, c.tod)} />
      <P d="M0 424 C240 336 520 352 700 404 S920 452 960 430 V504 H0 Z" style={{ fill: c.url("hill") }} />
      {c.season === "spring" &&
        Array.from({ length: 70 }, (_, i) => (
          <C key={i} cx={rnd() * 960} cy={430 + rnd() * 70} r={1.6} f={shade(i % 2 ? "#fff6a8" : "#f7b6c8", c.tod)} />
        ))}
      {c.season === "autumn" &&
        Array.from({ length: 40 }, (_, i) => (
          <C key={i} cx={rnd() * 960} cy={440 + rnd() * 60} r={2} f={shade(i % 2 ? "#e07a2e" : "#c9452f", c.tod)} />
        ))}
      {c.season === "winter" && <P d="M0 470 C300 440 600 470 960 456 V504 H0 Z" f={shade("#dfe8f3", c.tod)} />}
      <Weather c={c} x={0} y={0} w={960} h={TASK_Y} rnd={rnd} />
    </g>
  );
}

function NightLight({ c }: { c: ArtCtx }) {
  const dark = c.tod === "night" ? 1 : c.tod === "dusk" ? 0.55 : 0;
  if (!dark) return null;
  return (
    <rect
      className="rm-ambient"
      x={0}
      y={0}
      width={960}
      height={TASK_Y}
      style={c.lampOn ? { fill: "#ffb347", opacity: 0.07 * dark } : { fill: "#0a0f2c", opacity: 0.28 * dark }}
    />
  );
}

/** A desktop icon: 48-px art and a shadowed label. */
function Icon({ r, label, children }: { r: Rect; label: string; children: ReactNode }) {
  const cx = r.x + r.w / 2;
  return (
    <g>
      <g transform={`translate(${cx - 24} ${r.y + 4})`}>{children}</g>
      <Tx x={cx + 1} y={r.y + 69} size={11} f="#000" anchor="middle" o={0.7}>
        {label}
      </Tx>
      <Tx x={cx} y={r.y + 68} size={11} f="#fff" anchor="middle">
        {label}
      </Tx>
    </g>
  );
}

const DoorArt = () => (
  <g>
    <R x={8} y={2} w={32} h={44} rx={2} f="#6b3f22" />
    <R x={11} y={5} w={26} h={41} f="#b5783f" />
    <R x={14} y={9} w={20} h={14} rx={1} f="#000" o={0.12} />
    <R x={14} y={27} w={20} h={15} rx={1} f="#000" o={0.12} />
    <C cx={33} cy={26} r={2} f="#f2c14e" />
    <P d="M37 5 L44 9 V46 L37 46 Z" f="#4a2a15" o={0.6} />
  </g>
);

const PrinterArt = () => (
  <g>
    <R x={14} y={4} w={20} h={14} f="#fff" s="#8a8a8a" sw={0.6} />
    <R x={4} y={15} w={40} h={20} rx={4} f="#d6dae0" s="#7a7f88" sw={0.8} />
    <R x={10} y={26} w={28} h={3} f="#444" />
    <R x={12} y={28} w={24} h={16} f="#fff" s="#8a8a8a" sw={0.6} />
    <Ln x1={15} y1={34} x2={33} y2={34} s="#888" sw={1} />
    <Ln x1={15} y1={38} x2={28} y2={38} s="#888" sw={1} />
    <C cx={39} cy={20} r={1.8} f="#3fbf5f" />
  </g>
);

const CabinetArt = () => (
  <g>
    <R x={10} y={3} w={28} h={43} rx={2} f="#c9bfa8" s="#7f7564" sw={0.8} />
    {[0, 1, 2].map((i) => (
      <g key={i}>
        <R x={13} y={6 + i * 13.5} w={22} h={11} rx={1} f="#e2d9c3" s="#7f7564" sw={0.6} />
        <R x={19} y={10 + i * 13.5} w={10} h={3} rx={1.5} f="#7f7564" />
      </g>
    ))}
  </g>
);

function ChartArt({ c }: { c: ArtCtx }) {
  const vals = c.data.topics.length ? c.data.topics.slice(0, 4).map((_, i) => 0.4 + ((i * 37) % 50) / 100) : [0.4, 0.65, 0.5, 0.85];
  return (
    <g>
      <R x={6} y={6} w={36} h={36} rx={2} f="#fff" s="#8a8a8a" sw={0.8} />
      {vals.map((v, i) => (
        <R key={i} x={11 + i * 8} y={38 - v * 26} w={6} h={v * 26} f="var(--primary)" />
      ))}
      <P d="M10 30 L18 24 L26 27 L38 12" f="none" s="var(--accent)" sw={1.8} />
    </g>
  );
}

function BulbArt({ on }: { on: boolean }) {
  return (
    <g>
      {on &&
        Array.from({ length: 8 }, (_, i) => {
          const a = (i / 8) * Math.PI * 2;
          return <Ln key={i} x1={24 + Math.cos(a) * 16} y1={19 + Math.sin(a) * 16} x2={24 + Math.cos(a) * 21} y2={19 + Math.sin(a) * 21} s="#ffd84a" sw={2} />;
        })}
      <C cx={24} cy={19} r={12} f={on ? "#ffe066" : "#d9d9d9"} s={on ? "#e0a800" : "#999"} sw={1} />
      <P d="M19 19 q5 6 10 0" f="none" s={on ? "#c98a00" : "#888"} sw={1} />
      <R x={18} y={30} w={12} h={10} rx={2} f="#9aa0a8" />
      <Ln x1={18} y1={33} x2={30} y2={33} s="#6b7078" sw={1} />
      <Ln x1={18} y1={36} x2={30} y2={36} s="#6b7078" sw={1} />
      <C cx={20} cy={14} r={3} f="#fff" o={0.6} />
    </g>
  );
}

function MugArt({ c }: { c: ArtCtx }) {
  return (
    <g>
      <P d="M14 8 c-3 -4 3 -6 0 -9 M22 8 c-3 -4 3 -6 0 -9" f="none" s="#fff" sw={1.4} o={0.7} cls="rm-steam" />
      <P d="M36 18 c9 0 9 14 0 14" f="none" s="#f4f1ea" sw={4} />
      <R x={8} y={12} w={28} h={32} rx={3} f="#f4f1ea" s="#7a7f88" sw={0.8} />
      <E cx={22} cy={12} rx={14} ry={2.5} f="#5b3a29" />
      <R x={8} y={16} w={28} h={2.5} f="#ffd60a" />
      <ClubLogo name="coding" x={10} y={24} w={24} h={8} preview={c.preview} color="#111" />
    </g>
  );
}

function TitleBar({ c, x, y, w, title, sub, idName }: { c: ArtCtx; x: number; y: number; w: number; title: string; sub?: string; idName: string }) {
  return (
    <g>
      <defs>
        <linearGradient id={c.id(idName)} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" style={{ stopColor: "color-mix(in srgb, var(--primary) 70%, #fff)" }} />
          <stop offset="0.45" style={{ stopColor: "var(--primary)" }} />
          <stop offset="1" style={{ stopColor: "color-mix(in srgb, var(--primary) 75%, #000)" }} />
        </linearGradient>
      </defs>
      <P d={`M${x} ${y + 28} V${y + 8} Q${x} ${y} ${x + 8} ${y} H${x + w - 8} Q${x + w} ${y} ${x + w} ${y + 8} V${y + 28} Z`} style={{ fill: c.url(idName) }} />
      <R x={x + 8} y={y + 7} w={14} h={14} rx={2} f="#fff" o={0.85} />
      <R x={x + 11} y={y + 9} w={3} h={10} f="var(--primary)" />
      <R x={x + 15} y={y + 10} w={3} h={9} f="var(--accent)" />
      <Tx x={x + 28} y={y + 18.5} size={12} f="#fff" weight={700}>
        {title}
        {sub ? <tspan style={{ fontWeight: 400, opacity: 0.85 }}>{`  ${sub}`}</tspan> : null}
      </Tx>
      {[0, 1, 2].map((i) => {
        const bx = x + w - 66 + i * 21;
        return (
          <g key={i}>
            <R x={bx} y={y + 5} w={18} h={18} rx={3} f="#fff" o={i === 2 ? 0.35 : 0.22} s="#fff" sw={0.8} />
            {i === 0 && <Ln x1={bx + 5} y1={y + 17} x2={bx + 13} y2={y + 17} s="#fff" sw={2} />}
            {i === 1 && <R x={bx + 5} y={y + 9} w={8} h={8} f="none" s="#fff" sw={1.6} />}
            {i === 2 && (
              <P d={`M${bx + 5.5} ${y + 10.5} l7 7 M${bx + 12.5} ${y + 10.5} l-7 7`} f="none" s="#fff" sw={2} />
            )}
          </g>
        );
      })}
    </g>
  );
}

function ShelfWindow({ c }: { c: ArtCtx }) {
  const { x, y, w, h } = SPOT.bookcase;
  const n = c.data.topics.length;
  const solved = c.data.topics.reduce((s, t) => s + t.independent, 0);
  const inner = { x: x + 16, y: y + 40, w: w - 32, h: h - 74 };
  const comp = (inner.h - 12) / 3;
  const shelves: Shelf[] = [0, 1, 2].map((i) => ({ x: inner.x + 8, base: inner.y + 6 + comp * (i + 1) - 4, width: inner.w - 16, height: comp - 10 }));
  return (
    <g>
      <R x={x + 5} y={y + 7} w={w} h={h} rx={8} f="#000" o={0.25} />
      <R x={x} y={y} w={w} h={h} rx={8} f="var(--primary)" />
      <R x={x + 4} y={y + 28} w={w - 8} h={h - 32} f="var(--surface)" />
      <TitleBar c={c} x={x} y={y} w={w} title="Bookshelf" sub={n ? `${n} topic${n === 1 ? "" : "s"}` : undefined} idName="tb1" />
      <R x={inner.x} y={inner.y} w={inner.w} h={inner.h} rx={3} f="#9a6a3e" />
      <R x={inner.x + 6} y={inner.y + 6} w={inner.w - 12} h={inner.h - 12} f="#6e4526" />
      {shelves.map((s, i) => (
        <R key={i} x={inner.x + 4} y={s.base} w={inner.w - 8} h={6} f="#b07a4c" />
      ))}
      <Books c={c} shelves={shelves} />
      <R x={x + 4} y={y + h - 24} w={w - 8} h={20} f="color-mix(in srgb, var(--surface) 88%, var(--text))" />
      <Tx x={x + 12} y={y + h - 10} size={10} f="var(--text)" o={0.8}>
        {n ? `${n} topic${n === 1 ? "" : "s"} practised · ${solved} solved on your own` : "Practise a topic to put its book on the shelf"}
      </Tx>
    </g>
  );
}

function StickyGadget({ c }: { c: ArtCtx }) {
  const { x, y, w, h } = SPOT.noticeboard;
  const { due, nextDue, notes, subject } = c.data;
  const next = relativeDay(nextDue, c.now);
  return (
    <g>
      <R x={x + 4} y={y + 6} w={w} h={h} rx={4} f="#000" o={0.25} />
      <R x={x} y={y} w={w} h={h} rx={4} f="#fde68a" />
      <R x={x} y={y} w={w} h={20} rx={4} f="#fcd34d" />
      <R x={x} y={y + 14} w={w} h={6} f="#fcd34d" />
      <Tx x={x + 10} y={y + 14} size={10} f="#5b4a12" weight={700}>
        {`Today${subject ? ` · ${abbreviate(subject, 18)}` : ""}`}
      </Tx>
      <Tx x={x + w - 12} y={y + 14} size={11} f="#5b4a12" anchor="end">
        ×
      </Tx>
      <Tx x={x + 14} y={y + 62} size={34} f="#5b4a12" weight={700}>
        {due === null ? "—" : due > 0 ? String(due) : "✓"}
      </Tx>
      <Tx x={x + 14} y={y + 80} size={11} f="#5b4a12">
        {due === null ? "reviews" : due > 0 ? (due === 1 ? "review due" : "reviews due") : "all caught up"}
      </Tx>
      {notes.slice(0, 3).map((n, i) => (
        <Tx key={i} x={x + 14} y={y + 104 + i * 16} size={11} f="#3b3326">
          {`• ${abbreviate(n, 26)}`}
        </Tx>
      ))}
      {next && (due ?? 0) === 0 && (
        <Tx x={x + 14} y={y + h - 14} size={10} f="#5b4a12" o={0.8}>
          {`next review ${next}`}
        </Tx>
      )}
      <P d={`M${x + w - 18} ${y + h} L${x + w} ${y + h - 18} V${y + h - 4} Q${x + w} ${y + h} ${x + w - 4} ${y + h} Z`} f="#e9c95a" />
    </g>
  );
}

function PlantGadget({ c }: { c: ArtCtx }) {
  const x = 716;
  const y = 296;
  const w = 124;
  const h = 176;
  const label = plantLabel(c);
  const n = c.data.plantCount;
  return (
    <g role="img" aria-label={label}>
      <title>{label}</title>
      <R x={x} y={y} w={w} h={h} rx={12} f="#fff" o={0.22} />
      <R x={x} y={y} w={w} h={h} rx={12} f="none" s="#fff" sw={1.2} o={0.6} />
      <PlantGrowth stage={c.plant} x={x + w / 2} y={y + h - 54} s={0.85} />
      <P d={`M${x + w / 2 - 22} ${y + h - 52} l5 30 h34 l5 -30 Z`} f="#c0653f" />
      <R x={x + w / 2 - 25} y={y + h - 56} w={50} h={7} rx={2} f="#d0754f" />
      <Tx x={x + w / 2 + 1} y={y + h - 9} size={10} f="#000" anchor="middle" o={0.6}>
        {`${n} spaced review${n === 1 ? "" : "s"}`}
      </Tx>
      <Tx x={x + w / 2} y={y + h - 10} size={10} f="#fff" anchor="middle">
        {`${n} spaced review${n === 1 ? "" : "s"}`}
      </Tx>
    </g>
  );
}

function StartButton({ c }: { c: ArtCtx }) {
  const { x, y, w, h } = SPOT.pennant;
  return (
    <g>
      <defs>
        <linearGradient id={c.id("start")} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" style={{ stopColor: "color-mix(in srgb, var(--accent) 65%, #fff)" }} />
          <stop offset="0.5" style={{ stopColor: "var(--accent)" }} />
          <stop offset="1" style={{ stopColor: "color-mix(in srgb, var(--accent) 70%, #000)" }} />
        </linearGradient>
      </defs>
      <P d={`M${x} ${y} H${x + w - 18} Q${x + w} ${y} ${x + w} ${y + h / 2} Q${x + w} ${y + h} ${x + w - 18} ${y + h} H${x} Z`} style={{ fill: c.url("start") }} />
      <R x={x + 10} y={y + 6} w={108} h={24} rx={12} f="var(--surface)" />
      <ClubLogo name="inline" x={x + 20} y={y + 9} w={88} h={18} preview={c.preview} />
    </g>
  );
}

function Taskbar({ c }: { c: ArtCtx }) {
  const list = c.data.trophies.slice(0, 5);
  return (
    <g>
      <defs>
        <linearGradient id={c.id("task")} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" style={{ stopColor: "color-mix(in srgb, var(--primary) 70%, #fff)" }} />
          <stop offset="0.2" style={{ stopColor: "var(--primary)" }} />
          <stop offset="1" style={{ stopColor: "color-mix(in srgb, var(--primary) 70%, #000)" }} />
        </linearGradient>
      </defs>
      <rect x={0} y={TASK_Y} width={960} height={36} style={{ fill: c.url("task") }} />
      <R x={0} y={TASK_Y} w={960} h={1.5} f="#fff" o={0.4} />
      <g aria-hidden="true">
        {["Bookshelf", "Today"].map((t, i) => (
          <g key={t}>
            <R x={150 + i * 146} y={TASK_Y + 5} w={138} h={26} rx={4} f="#fff" o={i === 0 ? 0.28 : 0.14} />
            <Tx x={164 + i * 146} y={TASK_Y + 22} size={11} f="#fff">
              {t}
            </Tx>
          </g>
        ))}
      </g>
      <R x={770} y={TASK_Y} w={190} h={36} f="#000" o={0.18} />
      <R x={770} y={TASK_Y} w={1.5} h={36} f="#fff" o={0.3} />
      <g role="img" aria-label={list.length ? `Trophies: ${list.map((t) => t.title).join(", ")}` : "No trophies yet"}>
        {list.map((t, i) => (
          <g key={t.id}>
            <title>{t.title}</title>
            <Trophy x={790 + i * 20} base={TASK_Y + 30} tint={TROPHY_TINT[t.id] ?? "var(--primary)"} s={0.62} />
          </g>
        ))}
      </g>
      <Tx x={944} y={TASK_Y + 23} size={13} f="#fff" anchor="end">
        {clockText(c.now)}
      </Tx>
    </g>
  );
}

export const desktop: RoomTheme = {
  id: "room.desktop",
  render: (c) => (
    <>
      <Wallpaper c={c} />
      <NightLight c={c} />
      {c.hs("door", SPOT.door, <Icon r={SPOT.door} label="Quiz"><DoorArt /></Icon>)}
      {c.hs("printer", SPOT.printer, <Icon r={SPOT.printer} label="Generate"><PrinterArt /></Icon>)}
      {c.hs("cabinet", SPOT.cabinet, <Icon r={SPOT.cabinet} label="History"><CabinetArt /></Icon>)}
      {c.hs("chart", SPOT.chart, <Icon r={SPOT.chart} label="Stats"><ChartArt c={c} /></Icon>)}
      {c.hs("lamp", SPOT.lamp, <Icon r={SPOT.lamp} label="Night light"><BulbArt on={c.lampOn} /></Icon>)}
      {c.hs("mug", SPOT.mug, <Icon r={SPOT.mug} label="Coding Club"><MugArt c={c} /></Icon>)}
      <PlantGadget c={c} />
      {c.hs("bookcase", SPOT.bookcase, <ShelfWindow c={c} />)}
      {c.hs("noticeboard", SPOT.noticeboard, <StickyGadget c={c} />)}
      <Taskbar c={c} />
      {c.hs("pennant", SPOT.pennant, <StartButton c={c} />)}
    </>
  ),
};
