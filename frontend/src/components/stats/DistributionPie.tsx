/**
 * D3 pie chart with the custom .amplify-tooltip on hover (spec §9.3).
 *
 * The tooltip is *not* D3's default — it's a DOM node we position by mouse
 * coordinates and style via the `.amplify-tooltip` class (overridden per
 * theme in Step 12).
 */

import { useEffect, useRef } from "react";
import * as d3 from "d3";

import type { DistributionDatum } from "../../lib/ipc";

interface Props {
  data: readonly DistributionDatum[];
  /** Optional fixed palette; defaults to d3.schemeTableau10. */
  palette?: readonly string[];
  size?: number;
}

export function DistributionPie({
  data,
  palette = d3.schemeTableau10,
  size = 360,
}: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const w = size;
    const h = size;
    const r = Math.min(w, h) / 2 - 10;
    const total = data.reduce((s, d) => s + d.count, 0);
    if (total === 0) return;

    svg.attr("viewBox", `0 0 ${w} ${h}`).attr("role", "img");
    const g = svg.append("g").attr("transform", `translate(${w / 2}, ${h / 2})`);

    const pie = d3
      .pie<DistributionDatum>()
      .value((d) => d.count)
      .sort(null);

    const arc = d3
      .arc<d3.PieArcDatum<DistributionDatum>>()
      .innerRadius(r * 0.55)
      .outerRadius(r);

    const tooltip = d3.select(tooltipRef.current);

    g.selectAll<SVGPathElement, d3.PieArcDatum<DistributionDatum>>("path")
      .data(pie([...data]))
      .join("path")
      .attr("d", (d) => arc(d) ?? "")
      .attr("fill", (_, i) => palette[i % palette.length])
      .attr("stroke", "var(--background)")
      .attr("stroke-width", 2)
      .attr("opacity", 0.92)
      .on("mouseenter", function (_, d) {
        d3.select(this).attr("opacity", 1).attr("stroke-width", 3);
        const pct = ((d.data.count / total) * 100).toFixed(1);
        tooltip
          .style("display", "block")
          .html(
            `<div class="amp-label">${escapeHtml(d.data.label)}</div>` +
              `<div class="amp-meta">${d.data.count.toLocaleString()} · ${pct}%</div>`,
          );
      })
      .on("mousemove", function (event: MouseEvent) {
        tooltip
          .style("left", `${event.clientX + 12}px`)
          .style("top", `${event.clientY + 12}px`);
      })
      .on("mouseleave", function () {
        d3.select(this).attr("opacity", 0.92).attr("stroke-width", 2);
        tooltip.style("display", "none");
      });

    // Center label: total
    g.append("text")
      .attr("text-anchor", "middle")
      .attr("dy", "-0.15em")
      .attr("fill", "var(--text)")
      .style("font-size", "1.6rem")
      .style("font-weight", "600")
      .text(total.toLocaleString());
    g.append("text")
      .attr("text-anchor", "middle")
      .attr("dy", "1.1em")
      .attr("fill", "var(--muted)")
      .style("font-size", "0.75rem")
      .style("letter-spacing", "0.05em")
      .style("text-transform", "uppercase")
      .text("total");
  }, [data, palette, size]);

  return (
    <div className="flex flex-col items-center gap-4 md:flex-row md:items-start">
      <svg ref={svgRef} className="w-full max-w-[360px]" />
      <Legend data={data} palette={palette} />
      <div
        ref={tooltipRef}
        className="amplify-tooltip fixed"
        style={{ display: "none", left: 0, top: 0 }}
      />
    </div>
  );
}

function Legend({
  data,
  palette,
}: {
  data: readonly DistributionDatum[];
  palette: readonly string[];
}) {
  const total = data.reduce((s, d) => s + d.count, 0);
  return (
    <ul className="flex-1 space-y-1 text-sm">
      {data.map((d, i) => {
        const pct = total > 0 ? ((d.count / total) * 100).toFixed(1) : "0";
        return (
          <li key={d.label} className="flex items-center gap-2">
            <span
              className="inline-block h-3 w-3 flex-none rounded-sm"
              style={{ backgroundColor: palette[i % palette.length] }}
            />
            <span className="flex-1 truncate">{d.label}</span>
            <span className="tabular-nums text-muted">
              {d.count.toLocaleString()} · {pct}%
            </span>
          </li>
        );
      })}
    </ul>
  );
}

function escapeHtml(s: string): string {
  return s
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
