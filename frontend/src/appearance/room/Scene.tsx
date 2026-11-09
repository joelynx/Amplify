/**
 * The room as one SVG (viewBox 960×540): resolves the room item to a theme
 * renderer, builds the drawing context (time, season, data, lamp, motion),
 * wraps clickable objects as keyboard-accessible hotspots, and draws the
 * hover/focus ring and label on top of everything.
 */

import { useId, useState, type Dispatch, type ReactNode, type SetStateAction } from "react";

import { getItem } from "../registry";
import { plantStage, season, timeOfDay, type SceneData } from "./helpers";
import type { ArtCtx, ObjectId, Rect } from "./model";
import { roomTheme } from "./themes";
import "./room.css";

export interface ObjectLabel {
  /** Shown in the hover label. */
  short: string;
  /** Accessible name. */
  long: string;
}

export function objectLabels(due: number | null, lampOn: boolean): Record<ObjectId, ObjectLabel> {
  const n = due ?? 0;
  return {
    door: { short: "Quiz", long: "Door: start a quiz" },
    printer: { short: "Generate a problem set", long: "Printer: generate a problem set" },
    cabinet: { short: "History", long: "Filing cabinet: your history" },
    chart: { short: "Stats", long: "Chart: your stats" },
    bookcase: { short: "Browse questions", long: "Bookcase: browse questions" },
    noticeboard:
      n > 0
        ? { short: `Start review · ${n} due`, long: `Noticeboard: ${n} review${n === 1 ? "" : "s"} due, start a review` }
        : { short: "Quiz", long: due === 0 ? "Noticeboard: nothing due for review, open Quiz" : "Noticeboard: open Quiz" },
    lamp: { short: lampOn ? "Lamp off" : "Lamp on", long: "Desk lamp" },
    pennant: { short: "About the clubs", long: "Mathematics Club pennant: about Amplify and the clubs" },
    mug: { short: "About the clubs", long: "Coding Club mug: about Amplify and the clubs" },
  };
}

type Active = { id: ObjectId; focus: boolean } | null;

function focusVisible(el: Element): boolean {
  try {
    return el.matches(":focus-visible");
  } catch {
    return true;
  }
}

function Hotspot({
  id,
  rect,
  label,
  checked,
  onActivate,
  setActive,
  children,
}: {
  id: ObjectId;
  rect: Rect;
  label: string;
  checked?: boolean;
  onActivate: (id: ObjectId) => void;
  setActive: Dispatch<SetStateAction<Active>>;
  children: ReactNode;
}) {
  return (
    <g
      className="rm-hs"
      role={checked === undefined ? "button" : "switch"}
      aria-checked={checked}
      aria-label={label}
      tabIndex={0}
      data-object={id}
      onClick={() => onActivate(id)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onActivate(id);
        }
      }}
      onMouseEnter={() => setActive((a) => (a?.focus ? a : { id, focus: false }))}
      onMouseLeave={() => setActive((a) => (a && a.id === id && !a.focus ? null : a))}
      onFocus={(e) => setActive({ id, focus: focusVisible(e.currentTarget) })}
      onBlur={() => setActive((a) => (a && a.id === id ? null : a))}
    >
      <rect className="rm-hit" x={rect.x} y={rect.y} width={rect.w} height={rect.h} />
      <g className="rm-art">{children}</g>
    </g>
  );
}

function Callout({ rect, text, focus }: { rect: Rect; text: string; focus: boolean }) {
  const pad = 5;
  const w = Math.max(44, text.length * 6.9 + 22);
  const h = 24;
  const tx = Math.min(960 - w - 6, Math.max(6, rect.x + rect.w / 2 - w / 2));
  let ty = rect.y - h - 10;
  if (ty < 4) ty = rect.y + rect.h + 10;
  if (ty + h > 536) ty = rect.y + 6;
  const ring = { x: rect.x - pad, y: rect.y - pad, width: rect.w + pad * 2, height: rect.h + pad * 2, rx: 8 };
  return (
    <g className="rm-callout" aria-hidden="true">
      {focus && <rect className="rm-ring-halo" {...ring} />}
      <rect className={focus ? "rm-ring rm-ring-focus" : "rm-ring"} {...ring} />
      <rect className="rm-tip-bg" x={tx} y={ty} width={w} height={h} rx={6} />
      <text className="rm-tip-text" x={tx + w / 2} y={ty + 16} textAnchor="middle">
        {text}
      </text>
    </g>
  );
}

export interface SceneProps {
  itemId: string;
  data: SceneData;
  now: Date;
  lampOn: boolean;
  motion: boolean;
  /** Static thumbnail: no hotspots, no logos. */
  preview?: boolean;
  paused?: boolean;
  labels?: Record<ObjectId, ObjectLabel>;
  onActivate?: (id: ObjectId) => void;
  className?: string;
  title?: string;
}

export function Scene({ itemId, data, now, lampOn, motion, preview = false, paused, labels, onActivate, className, title }: SceneProps) {
  const uid = `rm${useId().replace(/[^a-zA-Z0-9_-]/g, "")}`;
  const [active, setActive] = useState<Active>(null);
  const item = getItem(itemId);
  const base = typeof item?.data?.base === "string" ? item.data.base : itemId;
  const theme = roomTheme(base);
  const backdrop = typeof item?.data?.backdrop === "string" ? item.data.backdrop : null;
  const interactive = !preview && !!onActivate && !!labels;

  // Filled while the theme renders (hs is called synchronously from render).
  const rects: Partial<Record<ObjectId, Rect>> = {};
  const c: ArtCtx = {
    id: (n) => `${uid}-${n}`,
    url: (n) => `url(#${uid}-${n})`,
    now,
    tod: timeOfDay(now),
    season: season(now),
    lampOn,
    motion,
    preview,
    data,
    plant: plantStage(data.plantCount),
    backdrop,
    hs: (id, rect, art) => {
      rects[id] = rect;
      if (!interactive || !labels || !onActivate) return art;
      return (
        <Hotspot
          id={id}
          rect={rect}
          label={labels[id].long}
          checked={id === "lamp" ? lampOn : undefined}
          onActivate={onActivate}
          setActive={setActive}
        >
          {art}
        </Hotspot>
      );
    },
  };
  const body = theme.render(c);
  const spot = active ? rects[active.id] : undefined;

  return (
    <svg
      viewBox="0 0 960 540"
      className={["amp-room-svg", motion ? "rm-motion" : "", paused ? "rm-paused" : "", className ?? ""].join(" ")}
      role={interactive ? "group" : "img"}
      aria-label={title ?? `${item?.name ?? "Study"} room`}
      shapeRendering={theme.pixel ? "crispEdges" : undefined}
      data-room={theme.id}
      preserveAspectRatio="xMidYMid meet"
    >
      {body}
      {interactive && labels && active && spot && <Callout rect={spot} text={labels[active.id].short} focus={active.focus} />}
    </svg>
  );
}
