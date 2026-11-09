/**
 * The illustrated room layout shared by study, library, observatory,
 * greenhouse and dorm: the same objects in the same places, in the theme's
 * materials, with theme decor slotted in behind and in front. Also the
 * ambient light (lamp glow, evening dimming).
 */

import type { ReactNode } from "react";

import type { ArtCtx, Rect } from "../model";
import {
  Bookcase,
  Cabinet,
  ChairBack,
  Desk,
  Door,
  Floor,
  L,
  Lamp,
  Mug,
  Notebook,
  Noticeboard,
  Pennant,
  Plant,
  Printer,
  Rug,
  TrophyShelf,
  Wall,
  WallChart,
  WindowFrame,
  lampHead,
  type BoardKind,
  type BookcaseKind,
  type CabinetKind,
  type ChartKind,
  type DeskKind,
  type DoorKind,
  type FloorKind,
  type LampKind,
  type Mat,
  type WindowKind,
} from "../parts";

export interface ClassicOpts {
  m: Mat;
  /** Replaces the default wall (wallpaper, wainscot, skirting). */
  wall?: ReactNode;
  floor?: FloorKind;
  /** Decor on the wall, behind every object. */
  back?: ReactNode;
  /** Replaces the window; null for none. */
  window?: ReactNode | null;
  windowKind?: WindowKind;
  curtains?: string | null;
  door?: DoorKind;
  board?: BoardKind;
  chart?: ChartKind;
  bookcase?: BookcaseKind;
  bookcaseRect?: Rect;
  shelves?: number;
  desk?: DeskKind;
  lamp?: LampKind;
  cabinet?: CabinetKind;
  cabinetBody?: string;
  /** Behind the desk, in front of the wall objects (telescope, ladder). */
  mid?: ReactNode;
  /** On the desk instead of the notebook. */
  deskTop?: ReactNode;
  /** Foreground (armchair, bed, beanbag). Never catches clicks. */
  front?: ReactNode;
  rug?: ReactNode | false;
  chair?: ReactNode | false;
}

export function Ambient({ c, at }: { c: ArtCtx; at: { x: number; y: number } }) {
  const dark = c.tod === "night" ? 1 : c.tod === "dusk" ? 0.55 : c.tod === "dawn" ? 0.25 : 0;
  return (
    <g className="rm-ambient" aria-hidden="true">
      <defs>
        <radialGradient id={c.id("pool")} cx={at.x} cy={at.y + 60} r={420} gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#0a0f2c" stopOpacity="0" />
          <stop offset="0.3" stopColor="#0a0f2c" stopOpacity={0.06 * dark} />
          <stop offset="1" stopColor="#0a0f2c" stopOpacity={0.3 * dark} />
        </radialGradient>
        <radialGradient id={c.id("glow")} cx={at.x} cy={at.y} r={170} gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#ffd98a" stopOpacity="0.55" />
          <stop offset="1" stopColor="#ffd98a" stopOpacity="0" />
        </radialGradient>
      </defs>
      {dark > 0 &&
        (c.lampOn ? (
          <rect x={0} y={0} width={960} height={540} style={{ fill: c.url("pool") }} />
        ) : (
          <rect x={0} y={0} width={960} height={540} style={{ fill: "#0a0f2c", opacity: 0.3 * dark }} />
        ))}
      {c.lampOn && (
        <g className="rm-glow">
          <circle cx={at.x} cy={at.y} r={170} style={{ fill: c.url("glow"), opacity: 0.3 + 0.5 * dark }} />
        </g>
      )}
    </g>
  );
}

export function classicScene(c: ArtCtx, o: ClassicOpts): ReactNode {
  const m = o.m;
  const lamp = o.lamp ?? "angle";
  const bookcase = o.bookcaseRect ?? L.bookcase;
  return (
    <>
      {o.wall ?? <Wall c={c} m={m} />}
      <Floor c={c} m={m} kind={o.floor} />
      {o.back && (
        <g className="rm-deco" aria-hidden="true">
          {o.back}
        </g>
      )}
      {o.window !== undefined ? o.window : <WindowFrame c={c} m={m} kind={o.windowKind} curtains={o.curtains} />}
      {c.hs("pennant", L.pennant, <Pennant c={c} />)}
      {c.hs("noticeboard", L.noticeboard, <Noticeboard c={c} m={m} kind={o.board} />)}
      {c.hs("chart", L.chart, <WallChart c={c} m={m} kind={o.chart} />)}
      <TrophyShelf c={c} m={m} />
      {c.hs("bookcase", bookcase, <Bookcase c={c} m={m} r={bookcase} kind={o.bookcase} shelves={o.shelves} />)}
      {c.hs("door", L.door, <Door m={m} kind={o.door} />)}
      {o.rug === false ? null : (o.rug ?? <Rug m={m} />)}
      {o.mid && (
        <g className="rm-deco" aria-hidden="true">
          {o.mid}
        </g>
      )}
      <Desk m={m} kind={o.desk} />
      {o.chair === false ? null : (o.chair ?? <ChairBack m={m} />)}
      {o.deskTop ?? <Notebook m={m} />}
      {c.hs("lamp", L.lamp, <Lamp c={c} m={m} kind={lamp} />)}
      {c.hs("mug", L.mug, <Mug c={c} />)}
      {c.hs("printer", L.printer, <Printer m={m} />)}
      {c.hs("cabinet", L.cabinet, <Cabinet m={m} kind={o.cabinet} body={o.cabinetBody} />)}
      <Plant c={c} m={m} />
      {o.front && (
        <g className="rm-deco" aria-hidden="true">
          {o.front}
        </g>
      )}
      <Ambient c={c} at={lampHead(lamp)} />
    </>
  );
}
