"use client";

/**
 * Custom calendar heatmap (spec §8.4, §11.4 / dev cycle Step 14 explicit:
 * "NOT react-calendar-heatmap").
 *
 * Layout: weeks as columns, days as rows. Sunday-anchored (week starts Sunday).
 * Color intensity uses a perceptually uniform interpolation between
 * `--surface` (no activity) and `--primary` (max activity).
 */

import { useEffect, useRef } from "react";
import * as d3 from "d3";

interface Props {
  /** {YYYY-MM-DD: count}. Days not in the map default to 0. */
  data: Record<string, number>;
  year: number;
}

function dateRangeForYear(year: number): Date[] {
  const start = new Date(year, 0, 1);
  const end = new Date(year, 11, 31);
  const out: Date[] = [];
  const d = new Date(start);
  while (d <= end) {
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

export function CalendarHeatmap({ data, year }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const days = dateRangeForYear(year);
    const max = Math.max(0, ...Object.values(data));
    const color = d3
      .scaleSequential<string>()
      .domain([0, Math.max(1, max)])
      .interpolator((t) => d3.interpolate("var(--surface)", "var(--primary)")(t) as string);

    const cell = 12;
    const gap = 2;
    const cellPitch = cell + gap;
    const margin = { top: 18, right: 12, bottom: 8, left: 28 };
    // 53 weeks max per year × 7 days; plus space for month labels at top.
    const cols = 53;
    const rows = 7;
    const innerW = cols * cellPitch;
    const innerH = rows * cellPitch;
    const width = innerW + margin.left + margin.right;
    const height = innerH + margin.top + margin.bottom;

    svg.attr("viewBox", `0 0 ${width} ${height}`).attr("height", height);

    const g = svg.append("g").attr("transform", `translate(${margin.left}, ${margin.top})`);

    // Day labels on the left (Sun, Tue, Thu).
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

    const tooltip = d3.select(tooltipRef.current);

    // Cells
    g.selectAll<SVGRectElement, Date>("rect.day")
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
      .attr("stroke-width", 0.5)
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

    // Month labels along the top — placed at the first week column containing
    // the 1st of each month.
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
  }, [data, year]);

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
