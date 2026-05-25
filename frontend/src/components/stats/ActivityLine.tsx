/**
 * Two-line chart: papers + questions per day (spec §8.4).
 *
 * Single y-axis (papers and questions both fit one count axis since they're
 * comparable orders of magnitude in practice). Themed tooltip on the nearest
 * day to the cursor.
 */

import { useEffect, useRef } from "react";
import * as d3 from "d3";

import type { ActivityDatum } from "../../lib/ipc";

interface Props {
  data: readonly ActivityDatum[];
  height?: number;
}

export function ActivityLine({ data, height = 220 }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();
    if (data.length === 0) return;

    const parsed = data.map((d) => ({
      date: new Date(d.date),
      papers: d.papers,
      questions: d.questions,
    }));

    const width = svgRef.current.clientWidth || 600;
    const margin = { top: 12, right: 12, bottom: 32, left: 36 };
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;

    svg.attr("viewBox", `0 0 ${width} ${height}`);
    const g = svg.append("g").attr("transform", `translate(${margin.left}, ${margin.top})`);

    const x = d3
      .scaleTime()
      .domain(d3.extent(parsed, (d) => d.date) as [Date, Date])
      .range([0, innerW]);
    const yMax = Math.max(
      d3.max(parsed, (d) => d.papers) ?? 0,
      d3.max(parsed, (d) => d.questions) ?? 0,
    );
    const y = d3
      .scaleLinear()
      .domain([0, Math.max(1, yMax)])
      .nice()
      .range([innerH, 0]);

    const linePapers = d3
      .line<(typeof parsed)[number]>()
      .x((d) => x(d.date))
      .y((d) => y(d.papers));
    const lineQuestions = d3
      .line<(typeof parsed)[number]>()
      .x((d) => x(d.date))
      .y((d) => y(d.questions));

    g.append("g")
      .attr("transform", `translate(0, ${innerH})`)
      .call(d3.axisBottom(x).ticks(6).tickFormat(d3.timeFormat("%b %d") as never))
      .call((s) => s.selectAll("text").attr("fill", "var(--muted)"))
      .call((s) => s.selectAll("path,line").attr("stroke", "var(--border)"));
    g.append("g")
      .call(d3.axisLeft(y).ticks(5).tickFormat(d3.format("d")))
      .call((s) => s.selectAll("text").attr("fill", "var(--muted)"))
      .call((s) => s.selectAll("path,line").attr("stroke", "var(--border)"));

    g.append("path")
      .datum(parsed)
      .attr("fill", "none")
      .attr("stroke", "var(--secondary)")
      .attr("stroke-width", 2)
      .attr("d", lineQuestions);
    g.append("path")
      .datum(parsed)
      .attr("fill", "none")
      .attr("stroke", "var(--primary)")
      .attr("stroke-width", 2)
      .attr("d", linePapers);

    // Hover dots — questions
    g.selectAll<SVGCircleElement, (typeof parsed)[number]>("circle.q")
      .data(parsed)
      .join("circle")
      .attr("class", "q")
      .attr("cx", (d) => x(d.date))
      .attr("cy", (d) => y(d.questions))
      .attr("r", 3)
      .attr("fill", "var(--secondary)");
    g.selectAll<SVGCircleElement, (typeof parsed)[number]>("circle.p")
      .data(parsed)
      .join("circle")
      .attr("class", "p")
      .attr("cx", (d) => x(d.date))
      .attr("cy", (d) => y(d.papers))
      .attr("r", 3)
      .attr("fill", "var(--primary)");

    const tooltip = d3.select(tooltipRef.current);
    const overlay = g
      .append("rect")
      .attr("width", innerW)
      .attr("height", innerH)
      .attr("fill", "transparent")
      .style("cursor", "crosshair");
    const bisect = d3.bisector<(typeof parsed)[number], Date>((d) => d.date).center;
    overlay
      .on("mousemove", function (event: MouseEvent) {
        const [mx] = d3.pointer(event, this);
        const d = parsed[bisect(parsed, x.invert(mx))];
        if (!d) return;
        tooltip
          .style("display", "block")
          .style("left", `${event.clientX + 12}px`)
          .style("top", `${event.clientY + 12}px`)
          .html(
            `<div class="amp-label">${d3.timeFormat("%Y-%m-%d")(d.date)}</div>` +
              `<div class="amp-meta">${d.papers} paper${d.papers === 1 ? "" : "s"} · ` +
              `${d.questions} question${d.questions === 1 ? "" : "s"}</div>`,
          );
      })
      .on("mouseleave", () => tooltip.style("display", "none"));

    // Legend
    const legend = g.append("g").attr("transform", `translate(${innerW - 140}, 4)`);
    [
      { label: "Papers", color: "var(--primary)" },
      { label: "Questions", color: "var(--secondary)" },
    ].forEach((row, i) => {
      const grow = legend.append("g").attr("transform", `translate(0, ${i * 14})`);
      grow.append("rect").attr("width", 12).attr("height", 3).attr("y", 5).attr("fill", row.color);
      grow
        .append("text")
        .attr("x", 18)
        .attr("y", 9)
        .attr("fill", "var(--muted)")
        .attr("font-size", "11px")
        .text(row.label);
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
