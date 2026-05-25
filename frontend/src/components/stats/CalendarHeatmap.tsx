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

  useEffect(() => {
    const svgEl = svgRef.current;
    const tooltipEl = tooltipRef.current;
    if (!svgEl || !tooltipEl) return;
    const svg = d3.select(svgEl);
    svg.selectAll("*").remove();
    const tooltip = d3.select(tooltipEl);

    const max = Math.max(0, ...Object.values(data));
    const color = d3
      .scaleSequential<string>()
      .domain([0, Math.max(1, max)])
      .interpolator((t) => d3.interpolate("var(--surface)", "var(--primary)")(t) as string);

    if (mode === "year") {
      renderYear(svg, tooltip, data, year, color);
    } else {
      renderMonth(svg, tooltip, data, year, month, color);
    }
  }, [data, year, month, mode]);

  return (
    <>
      <svg ref={svgRef} className="w-full" />
      <div
        ref={tooltipRef}
        className="amplify-tooltip fixed"
        style={{ display: "none", left: 0, top: 0 }}
      />
    </>
  );
}

type Color = (n: number) => string;
type Sel = d3.Selection<SVGSVGElement, unknown, null, undefined>;
type TipSel = d3.Selection<HTMLDivElement, unknown, null, undefined>;

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
            `<div class="amp-meta">${count.toLocaleString()} PSet${count === 1 ? "" : "s"}</div>`,
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

function renderYear(svg: Sel, tooltip: TipSel, data: Record<string, number>, year: number, color: Color) {
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
    .attr("fill", (d) => color(data[isoDate(d)] ?? 0))
    .attr("stroke", "var(--border)")
    .attr("stroke-width", 0.5);
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
  color: Color,
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
    .attr("fill", (d) => color(data[isoDate(d)] ?? 0))
    .attr("stroke", "var(--border)")
    .attr("stroke-width", 0.5);
  attachHover(rect, tooltip, data);

  cells
    .append("text")
    .attr("x", 5)
    .attr("y", 13)
    .attr("fill", (d) => {
      const count = data[isoDate(d)] ?? 0;
      // Use a brighter color on filled cells; mute on empties.
      return count > 0 ? "var(--background)" : "var(--muted)";
    })
    .attr("font-size", "10px")
    .attr("font-weight", "600")
    .text((d) => d.getDate());

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
