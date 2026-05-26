"use client";

/**
 * D3 bar chart of `{multiplicity: count}` (spec §8.4, §9.1).
 *
 * Each bar represents the number of questions seen `k` times, for each `k`
 * from 1..max. Themed tooltip on hover uses the `.amplify-tooltip` class.
 */

import { useEffect, useRef } from "react";
import * as d3 from "d3";

interface Props {
  /** Server response: { multiplicity: count }. */
  data: Record<number, number>;
  height?: number;
}

export function MultiplicityHistogram({ data, height = 220 }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!svgRef.current) return;
    const entries = Object.entries(data)
      .map(([k, v]) => ({ k: Number(k), v }))
      .sort((a, b) => a.k - b.k);
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();
    if (entries.length === 0) return;

    // Ensure a contiguous integer x-axis from 1..max so gaps are visible.
    const max = entries[entries.length - 1].k;
    const filled = Array.from({ length: max }, (_, i) => ({
      k: i + 1,
      v: data[i + 1] ?? 0,
    }));

    const width = svgRef.current.clientWidth || 600;
    const margin = { top: 12, right: 12, bottom: 32, left: 36 };
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;

    svg.attr("viewBox", `0 0 ${width} ${height}`);

    const g = svg.append("g").attr("transform", `translate(${margin.left}, ${margin.top})`);

    const x = d3
      .scaleBand<number>()
      .domain(filled.map((d) => d.k))
      .range([0, innerW])
      .padding(0.18);
    const y = d3
      .scaleLinear()
      .domain([0, d3.max(filled, (d) => d.v) || 1])
      .nice()
      .range([innerH, 0]);

    g.append("g")
      .attr("transform", `translate(0, ${innerH})`)
      .call(d3.axisBottom(x).tickFormat((d) => `${d}×`))
      .call((sel) => sel.selectAll("text").attr("fill", "var(--muted)"))
      .call((sel) => sel.selectAll("path,line").attr("stroke", "var(--border)"));
    g.append("g")
      .call(d3.axisLeft(y).ticks(5).tickFormat(d3.format("d")))
      .call((sel) => sel.selectAll("text").attr("fill", "var(--muted)"))
      .call((sel) => sel.selectAll("path,line").attr("stroke", "var(--border)"));

    const tooltip = d3.select(tooltipRef.current);

    g.selectAll<SVGRectElement, (typeof filled)[number]>("rect")
      .data(filled)
      .join("rect")
      .attr("x", (d) => x(d.k) ?? 0)
      .attr("y", (d) => y(d.v))
      .attr("width", x.bandwidth())
      .attr("height", (d) => innerH - y(d.v))
      .attr("fill", "var(--primary)")
      .attr("opacity", 0.85)
      .on("mouseenter", function (_e, d) {
        d3.select(this).attr("opacity", 1);
        tooltip
          .style("display", "block")
          .html(
            `<div class="amp-label">${d.k}× multiplicity</div>` +
              `<div class="amp-meta">${d.v.toLocaleString()} question${d.v === 1 ? "" : "s"}</div>`,
          );
      })
      .on("mousemove", function (event: MouseEvent) {
        tooltip
          .style("left", `${event.clientX + 12}px`)
          .style("top", `${event.clientY + 12}px`);
      })
      .on("mouseleave", function () {
        d3.select(this).attr("opacity", 0.85);
        tooltip.style("display", "none");
      });
  }, [data, height]);

  return (
    <>
      <svg ref={svgRef} className="w-full" style={{ height }} />
      <div
        ref={tooltipRef}
        className="amplify-tooltip fixed"
        style={{ display: "none", left: 0, top: 0 }}
      />
    </>
  );
}
