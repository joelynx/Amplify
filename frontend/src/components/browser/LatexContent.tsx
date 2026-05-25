/**
 * Render prose with embedded LaTeX math, KaTeX-flavored.
 *
 * The seed bank's question/solution/outline strings mix free-form text with
 * `$…$` / `$$…$$` / `\(…\)` / `\[…\]` math. We split on those delimiters,
 * pass the math through KaTeX, and HTML-escape the prose. Each chunk is
 * inserted via `dangerouslySetInnerHTML` — safe because KaTeX produces
 * sanitized output and the prose path explicitly escapes.
 */

import { useMemo } from "react";
import katex from "katex";
import "katex/dist/katex.min.css";

import { cn } from "../../lib/cn";

interface Props {
  source: string;
  className?: string;
}

interface Chunk {
  kind: "text" | "math";
  text: string;
  display: boolean;
}

const MATH_RE = /(\$\$[\s\S]+?\$\$|\\\[[\s\S]+?\\\]|\\\([\s\S]+?\\\)|\$[^$\n]+\$)/g;

function splitChunks(s: string): Chunk[] {
  const out: Chunk[] = [];
  let last = 0;
  s.replace(MATH_RE, (match, _0, offset) => {
    if (offset > last) {
      out.push({ kind: "text", text: s.slice(last, offset), display: false });
    }
    let inner: string;
    let display: boolean;
    if (match.startsWith("$$")) {
      inner = match.slice(2, -2);
      display = true;
    } else if (match.startsWith("\\[")) {
      inner = match.slice(2, -2);
      display = true;
    } else if (match.startsWith("\\(")) {
      inner = match.slice(2, -2);
      display = false;
    } else {
      inner = match.slice(1, -1);
      display = false;
    }
    out.push({ kind: "math", text: inner, display });
    last = offset + match.length;
    return match;
  });
  if (last < s.length) out.push({ kind: "text", text: s.slice(last), display: false });
  return out;
}

function escapeHtml(s: string): string {
  return s
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll("\n", "<br/>");
}

function renderMath(expr: string, display: boolean): string {
  try {
    return katex.renderToString(expr, {
      displayMode: display,
      throwOnError: false,
      strict: "ignore",
    });
  } catch {
    return escapeHtml(`$${expr}$`);
  }
}

export function LatexContent({ source, className }: Props) {
  const html = useMemo(() => {
    if (!source) return "";
    const chunks = splitChunks(source);
    return chunks
      .map((c) =>
        c.kind === "math" ? renderMath(c.text, c.display) : escapeHtml(c.text),
      )
      .join("");
  }, [source]);
  return (
    <div
      className={cn("text-sm leading-relaxed", className)}
      // eslint-disable-next-line react/no-danger
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
