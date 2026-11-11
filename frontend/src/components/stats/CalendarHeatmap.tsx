/**
 * Custom calendar heatmap (spec §8.4, §11.4 / dev cycle Step 14 explicit:
 * "NOT react-calendar-heatmap").
 *
 * Two layouts:
 *   - `year`:  53 weeks × 7 days, tiny cells, month labels along the top.
 *   - `month`: 6 weeks × 7 days, larger cells with the day-of-month number.
 *
 * Color intensity interpolates between `--surface` (no activity) and
 * `--primary` (max activity).
 */

import { useEffect, useRef } from "react";
import * as d3 from "d3";

import { resolve } from "../../appearance/registry";
import { useAppearance } from "../../appearance/store";

interface Props {
  /** {YYYY-MM-DD: count}. Days not in the map default to 0. */
  data: Record<string, number>;
  year: number;
  /** 0-11. Required when `mode === "month"`. */
  month?: number;
  mode?: "year" | "month";
}

function dateRangeForYear(year: number): Date[] {
  const out: Date[] = [];
  const d = new Date(year, 0, 1);
  while (d.getFullYear() === year) {
    out.push(new Date(d));
    d.setDate(d.getDate() + 1);
  }
  return out;
}

function dateRangeForMonth(year: number, month: number): Date[] {
  const out: Date[] = [];
  const d = new Date(year, month, 1);
  while (d.getMonth() === month && d.getFullYear() === year) {
    out.push(new Date(d));
    d.setDate(d.getDate() + 1);
  }
  return out;
}

function isoDate(d: Date): string {
  const y = d.getFullYear();
  const m = `${d.getMonth() + 1}`.padStart(2, "0");
  const day = `${d.getDate()}`.padStart(2, "0");
  return `${y}-${m}-${day}`;
}

const DAY_LABELS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

export function CalendarHeatmap({ data, year, month = 0, mode = "year" }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  // Redraw when the chart skin changes (cell shapes are drawn here, not in CSS).
  const skin = useAppearance((st) => st.loadout.charts);

  useEffect(() => {
    const svgEl = svgRef.current;
    const tooltipEl = tooltipRef.current;
    if (!svgEl || !tooltipEl) return;
    const svg = d3.select(svgEl);
    svg.selectAll("*").remove();
    const tooltip = d3.select(tooltipEl);

    const max = Math.max(0, ...Object.values(data));

    if (mode === "year") {
      renderYear(svg, tooltip, data, year, max);
    } else {
      renderMonth(svg, tooltip, data, year, month, max);
    }
  }, [data, year, month, mode, skin]);

  return (
    <>
      <svg ref={svgRef} data-ui="chart" className="w-full" />
      <div
        ref={tooltipRef}
        className="amplify-tooltip fixed"
        style={{ display: "none", left: 0, top: 0 }}
      />
    </>
  );
}

type Sel = d3.Selection<SVGSVGElement, unknown, null, undefined>;
type TipSel = d3.Selection<HTMLDivElement, unknown, null, undefined>;

/** Cell color: neutral surface when empty, `--primary` with opacity scaled by
 * value/max otherwise. CSS-variable interpolation isn't a thing D3 can do
 * natively, and resolving via getComputedStyle would re-introduce theme-lag
 * — opacity on a primary fill produces the right "light → dark" gradient in
 * every theme automatically. */
function fillFor(v: number): string {
  return v <= 0 ? "var(--surface)" : "var(--primary)";
}
function opacityFor(v: number, max: number): number {
  if (v <= 0) return 1; // surface is already opaque
  if (max <= 0) return 1;
  // Scale 25% → 100% so even 1× cells are visibly distinct from empty,
  // and the max cell is fully saturated.
  return 0.25 + 0.75 * (v / max);
}

/* ---- chart skin (appearance "charts" slot): cell shape and colour ---- */

function cellSkin(): { cell: string; green: boolean } {
  const d = resolve(useAppearance.getState().loadout, "charts")?.data;
  return { cell: String(d?.cell ?? "square"), green: Boolean(d?.green) };
}

function starPath(size: number): string {
  const c = size / 2;
  const pts: string[] = [];
  for (let i = 0; i < 10; i++) {
    const r = i % 2 === 0 ? size * 0.5 : size * 0.21;
    const a = -Math.PI / 2 + (i * Math.PI) / 5;
    pts.push(`${(c + r * Math.cos(a)).toFixed(2)},${(c + r * Math.sin(a)).toFixed(2)}`);
  }
  return `M${pts.join("L")}Z`;
}

function flowerPath(size: number): string {
  const c = size / 2;
  const r = size * 0.2;
  let d = "";
  for (let i = 0; i < 5; i++) {
    const a = -Math.PI / 2 + (i * 2 * Math.PI) / 5;
    const x = c + size * 0.24 * Math.cos(a);
    const y = c + size * 0.24 * Math.sin(a);
    d += `M${x - r},${y}a${r},${r} 0 1,0 ${2 * r},0a${r},${r} 0 1,0 ${-2 * r},0`;
  }
  return d + `M${c - r * 0.8},${c}a${r * 0.8},${r * 0.8} 0 1,0 ${r * 1.6},0a${r * 0.8},${r * 0.8} 0 1,0 ${-r * 1.6},0`;
}

/**
 * Restyle day cells for the active chart skin. Stars and flowers are drawn
 * in a layer under the (now transparent) rects, which stay as hover targets.
 */
function applyCellSkin(
  rect: d3.Selection<SVGRectElement, Date, SVGGElement, unknown>,
  size: number,
  value: (d: Date) => number,
  max: number,
) {
  const { cell, green } = cellSkin();
  if (green) rect.attr("fill", (d) => (value(d) > 0 ? "#2ea043" : "var(--surface)"));
  if (cell === "round") rect.attr("rx", size / 2);
  if (cell === "pixel") rect.attr("rx", 0);
  if (cell !== "star" && cell !== "flower") return;
  const shape = cell === "star" ? starPath(size) : flowerPath(size);
  const fill = cell === "star" ? "var(--accent)" : "var(--primary)";
  rect.each(function (d) {
    const r = d3.select(this);
    const parent = d3.select(this.parentNode as SVGGElement);
    const v = value(d);
    parent
      .insert("path", () => this)
      .attr("d", v > 0 ? shape : `M${size / 2 - 1},${size / 2}a1,1 0 1,0 2,0a1,1 0 1,0 -2,0`)
      .attr("transform", `translate(${r.attr("x") ?? 0}, ${r.attr("y") ?? 0})`)
      .attr("fill", v > 0 ? fill : "var(--muted)")
      .attr("opacity", v > 0 ? opacityFor(v, max) : 0.5)
      .attr("pointer-events", "none");
  });
  rect.attr("fill", "transparent").attr("opacity", 1).attr("stroke-opacity", 0);
}

function attachHover(
  rect: d3.Selection<SVGRectElement, Date, SVGGElement, unknown>,
  tooltip: TipSel,
  data: Record<string, number>,
) {
  rect
    .on("mouseenter", function (_e, d) {
      const iso = isoDate(d);
      const count = data[iso] ?? 0;
      d3.select(this).attr("stroke", "var(--text)").attr("stroke-width", 1);
      tooltip
        .style("display", "block")
        .html(
          `<div class="amp-label">${iso}</div>` +
            `<div class="amp-meta">${count.toLocaleString()} paper${count === 1 ? "" : "s"}</div>`,
        );
    })
    .on("mousemove", function (event: MouseEvent) {
      tooltip
        .style("left", `${event.clientX + 12}px`)
        .style("top", `${event.clientY + 12}px`);
    })
    .on("mouseleave", function () {
      d3.select(this).attr("stroke", "var(--border)").attr("stroke-width", 0.5);
      tooltip.style("display", "none");
    });
}

function renderYear(svg: Sel, tooltip: TipSel, data: Record<string, number>, year: number, max: number) {
  const days = dateRangeForYear(year);
  const cell = 12;
  const gap = 2;
  const cellPitch = cell + gap;
  const margin = { top: 18, right: 12, bottom: 8, left: 28 };
  const innerW = 53 * cellPitch;
  const innerH = 7 * cellPitch;
  const width = innerW + margin.left + margin.right;
  const height = innerH + margin.top + margin.bottom;

  svg.attr("viewBox", `0 0 ${width} ${height}`).attr("height", height);
  const g = svg.append("g").attr("transform", `translate(${margin.left}, ${margin.top})`);

  g.selectAll("text.day")
    .data([1, 3, 5])
    .join("text")
    .attr("class", "day")
    .attr("x", -8)
    .attr("y", (d) => d * cellPitch + cell - 2)
    .attr("text-anchor", "end")
    .attr("fill", "var(--muted)")
    .attr("font-size", "10px")
    .text((d) => ["", "Mon", "", "Wed", "", "Fri", ""][d]);

  const rect = g
    .selectAll<SVGRectElement, Date>("rect.day")
    .data(days)
    .join("rect")
    .attr("class", "day")
    .attr("x", (d) => d3.timeWeek.count(d3.timeYear(d), d) * cellPitch)
    .attr("y", (d) => d.getDay() * cellPitch)
    .attr("width", cell)
    .attr("height", cell)
    .attr("rx", 2)
    .attr("fill", (d) => fillFor(data[isoDate(d)] ?? 0))
    .attr("opacity", (d) => opacityFor(data[isoDate(d)] ?? 0, max))
    .attr("stroke", "var(--border)")
    .attr("stroke-width", 0.5);
  applyCellSkin(rect, cell, (d) => data[isoDate(d)] ?? 0, max);
  attachHover(rect, tooltip, data);

  const monthStarts = d3.timeMonths(new Date(year, 0, 1), new Date(year + 1, 0, 1));
  g.selectAll("text.month")
    .data(monthStarts)
    .join("text")
    .attr("class", "month")
    .attr("x", (d) => d3.timeWeek.count(d3.timeYear(d), d) * cellPitch)
    .attr("y", -6)
    .attr("fill", "var(--muted)")
    .attr("font-size", "10px")
    .text((d) => d3.timeFormat("%b")(d));
}

function renderMonth(
  svg: Sel,
  tooltip: TipSel,
  data: Record<string, number>,
  year: number,
  month: number,
  max: number,
) {
  const days = dateRangeForMonth(year, month);
  if (days.length === 0) return;

  const cell = 44;
  const gap = 6;
  const cellPitch = cell + gap;
  const margin = { top: 28, right: 12, bottom: 12, left: 12 };
  const innerW = 7 * cellPitch;
  const innerH = 6 * cellPitch;
  const width = innerW + margin.left + margin.right;
  const height = innerH + margin.top + margin.bottom;

  svg.attr("viewBox", `0 0 ${width} ${height}`).attr("height", height);
  const g = svg.append("g").attr("transform", `translate(${margin.left}, ${margin.top})`);

  // Day-of-week labels along the top.
  g.selectAll("text.dow")
    .data(DAY_LABELS)
    .join("text")
    .attr("class", "dow")
    .attr("x", (_d, i) => i * cellPitch + cell / 2)
    .attr("y", -10)
    .attr("text-anchor", "middle")
    .attr("fill", "var(--muted)")
    .attr("font-size", "10px")
    .text((d) => d);

  const firstDow = days[0].getDay();

  const cells = g
    .selectAll<SVGGElement, Date>("g.cell")
    .data(days)
    .join("g")
    .attr("class", "cell")
    .attr(
      "transform",
      (_d, i) => {
        const offset = i + firstDow;
        const col = offset % 7;
        const row = Math.floor(offset / 7);
        return `translate(${col * cellPitch}, ${row * cellPitch})`;
      },
    );

  const rect = cells
    .append("rect")
    .attr("width", cell)
    .attr("height", cell)
    .attr("rx", 6)
    .attr("fill", (d) => fillFor(data[isoDate(d)] ?? 0))
    .attr("opacity", (d) => opacityFor(data[isoDate(d)] ?? 0, max))
    .attr("stroke", "var(--border)")
    .attr("stroke-width", 0.5);
  applyCellSkin(rect, cell, (d) => data[isoDate(d)] ?? 0, max);
  attachHover(rect, tooltip, data);

  // Day-of-month number. Filled cells get a high-contrast label; empty cells
  // stay muted so the eye picks out activity.
  cells
    .append("text")
    .attr("x", 5)
    .attr("y", 13)
    .attr("fill", (d) => ((data[isoDate(d)] ?? 0) > 0 ? "var(--background)" : "var(--muted)"))
    .attr("font-size", "10px")
    .attr("font-weight", "600")
    .text((d) => d.getDate());

  // Big count overlay on active days only.
  cells
    .filter((d) => (data[isoDate(d)] ?? 0) > 0)
    .append("text")
    .attr("x", cell / 2)
    .attr("y", cell - 8)
    .attr("text-anchor", "middle")
    .attr("fill", "var(--background)")
    .attr("font-size", "14px")
    .attr("font-weight", "700")
    .text((d) => (data[isoDate(d)] ?? 0).toLocaleString());
}
