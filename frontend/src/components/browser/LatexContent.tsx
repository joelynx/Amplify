/**
 * Render prose with embedded LaTeX math, KaTeX-flavored.
 *
 * Ported from the `karth/web-mvp` branch's `lib/katex.ts`. Two-phase:
 *
 *   1. `preprocessEnvironments` rewrites document-level LaTeX constructs the
 *      KaTeX inline parser can't handle:
 *        - `\begin{align|equation|gather|multline}` → wrap in `$$…$$`
 *          (KaTeX handles them inside display math)
 *        - `\begin{proof|theorem|lemma|definition|example|remark|corollary|
 *           claim|exercise|solution|proposition|quote}` → sentinel-marked
 *          labeled block, rendered as a left-border note after KaTeX runs
 *        - `\begin{itemize|enumerate}` + `\item` → sentinel-marked HTML lists
 *        - text-mode `\textbf` / `\textit` / `\emph` / `\underline` / `\texttt`
 *          → sentinel-marked HTML tags (balanced-brace argument parser so
 *          nested braces survive)
 *        - strip pure-spacing commands (`\hfill`, `\noindent`, `\smallskip`,
 *          `\medskip`, `\bigskip`, `\vfill`, `\par`, `\newline`, `\linebreak`)
 *   2. chunker walks the result, sending `$…$` / `$$…$$` / `\(…\)` / `\[…\]`
 *      regions through KaTeX, HTML-escaping the prose in between.
 *   3. `postprocessEnvironments` swaps sentinels for real HTML.
 *
 * Sentinels are ASCII strings that never occur in natural LaTeX source, so
 * they survive HTML escaping unmolested. The escape rule means we can pass
 * the final HTML straight to `dangerouslySetInnerHTML` — only KaTeX-emitted
 * markup and a fixed set of structural tags ever land in the output.
 */

import { useMemo, useState, useEffect, useRef } from "react";
import katex from "katex";
import "katex/dist/katex.min.css";

import { cn } from "../../lib/cn";
import { ipc } from "../../lib/ipc";

interface Props {
  source: string;
  className?: string;
}

// --- Sentinels ----------------------------------------------------------
const MARK_UL_OPEN = "@@AMP_UL_OPEN@@";
const MARK_UL_CLOSE = "@@AMP_UL_CLOSE@@";
const MARK_OL_OPEN = "@@AMP_OL_OPEN@@";
const MARK_OL_CLOSE = "@@AMP_OL_CLOSE@@";
const MARK_LI_OPEN = "@@AMP_LI_OPEN@@";
const MARK_LI_CLOSE = "@@AMP_LI_CLOSE@@";

const ENV_OPEN = "@@AMP_ENV_OPEN@@";
const ENV_DELIM = "@@AMP_ENV_DELIM@@";
const ENV_CLOSE = "@@AMP_ENV_CLOSE@@";

const STRONG_OPEN = "@@AMP_STRONG_OPEN@@";
const STRONG_CLOSE = "@@AMP_STRONG_CLOSE@@";
const EM_OPEN = "@@AMP_EM_OPEN@@";
const EM_CLOSE = "@@AMP_EM_CLOSE@@";
const U_OPEN = "@@AMP_U_OPEN@@";
const U_CLOSE = "@@AMP_U_CLOSE@@";
const TT_OPEN = "@@AMP_TT_OPEN@@";
const TT_CLOSE = "@@AMP_TT_CLOSE@@";

const IMG_SENTINEL_PREFIX = "@@AMP_IMG@@";
const IMG_SENTINEL_SUFFIX = "@@/AMP_IMG@@";

const STRIP_COMMANDS = [
  "hfill",
  "noindent",
  "newline",
  "linebreak",
  "smallskip",
  "medskip",
  "bigskip",
  "vfill",
  "par",
];

const MATH_ENVS = [
  "align",
  "align*",
  "equation",
  "equation*",
  "gather",
  "gather*",
  "multline",
  "multline*",
];

const TEXT_ENVS = [
  "proof",
  "theorem",
  "lemma",
  "definition",
  "example",
  "remark",
  "corollary",
  "claim",
  "exercise",
  "solution",
  "proposition",
  "quote",
];

// --- Image extraction ---------------------------------------------------

function extractImageNames(src: string): string[] {
  const re = /\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}/g;
  const names: string[] = [];
  let m: RegExpExecArray | null;
  while ((m = re.exec(src)) !== null) {
    const name = m[1].trim();
    if (name && !names.includes(name)) names.push(name);
  }
  return names;
}

// --- Preprocess ---------------------------------------------------------

function preprocessEnvironments(src: string): string {
  let s = src;

  // 0) Images: \includegraphics[opts]{name} → sentinel-wrapped filename.
  s = s.replace(
    /\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}/g,
    (_m, name: string) => `${IMG_SENTINEL_PREFIX}${name.trim()}${IMG_SENTINEL_SUFFIX}`,
  );
  // Optional [...] arg that follows \begin{env} (e.g. \begin{enumerate}[label=…]).
  const OPT_ARG = "(?:\\s*\\[[^\\]]*\\])?";

  // 1) Math envs → wrap in $$…$$ so the chunker hands them to KaTeX.
  for (const env of MATH_ENVS) {
    const envEsc = env.replace(/\*/g, "\\*");
    const re = new RegExp(
      `\\\\begin\\{${envEsc}\\}${OPT_ARG}([\\s\\S]*?)\\\\end\\{${envEsc}\\}`,
      "g",
    );
    s = s.replace(re, (_m, content: string) => `$$\\begin{${env}}${content}\\end{${env}}$$`);
  }

  // 2) Theorem-like envs (including starred variants like \begin{theorem*}).
  for (const env of TEXT_ENVS) {
    s = s
      .replace(
        new RegExp(`\\\\begin\\{${env}\\*?\\}${OPT_ARG}`, "g"),
        `${ENV_OPEN}${env}${ENV_DELIM}`,
      )
      .replace(new RegExp(`\\\\end\\{${env}\\*?\\}`, "g"), ENV_CLOSE);
  }

  // 3) Text-mode formatting (balanced-brace parser).
  s = wrapBracedCommand(s, "textbf", STRONG_OPEN, STRONG_CLOSE);
  s = wrapBracedCommand(s, "textit", EM_OPEN, EM_CLOSE);
  s = wrapBracedCommand(s, "emph", EM_OPEN, EM_CLOSE);
  s = wrapBracedCommand(s, "underline", U_OPEN, U_CLOSE);
  s = wrapBracedCommand(s, "texttt", TT_OPEN, TT_CLOSE);

  for (const cmd of STRIP_COMMANDS) {
    s = s.replace(new RegExp(`\\\\${cmd}\\b`, "g"), "");
  }

  // 4) Lists. \begin{itemize|enumerate}[opts] → sentinel pair.
  s = s
    .replace(new RegExp(`\\\\begin\\{itemize\\}${OPT_ARG}`, "g"), MARK_UL_OPEN)
    .replace(/\\end\{itemize\}/g, MARK_UL_CLOSE)
    .replace(new RegExp(`\\\\begin\\{enumerate\\}${OPT_ARG}`, "g"), MARK_OL_OPEN)
    .replace(/\\end\{enumerate\}/g, MARK_OL_CLOSE);
  // Braced \item{…} (handle nested braces).
  s = wrapBracedCommand(s, "item", MARK_LI_OPEN, MARK_LI_CLOSE);
  // Bare \item with no braces — pseudo-open; closed in postprocess.
  s = s.replace(/\\item\b/g, MARK_LI_OPEN);

  // NOTE: \\ (LaTeX line-break) is *not* preprocessed — it's a legitimate
  // row separator inside matrix/align math, and KaTeX handles it natively.
  return s;
}

/** Scan `src` for `\<cmd>{…}` with proper brace depth (handles nested `{}`)
 * and wrap each occurrence with `openSentinel`/`closeSentinel`. */
function wrapBracedCommand(
  src: string,
  cmd: string,
  openSentinel: string,
  closeSentinel: string,
): string {
  const needle = `\\${cmd}`;
  const out: string[] = [];
  let i = 0;
  while (i < src.length) {
    const idx = src.indexOf(needle, i);
    if (idx === -1) {
      out.push(src.slice(i));
      break;
    }
    const afterCmdIdx = idx + needle.length;
    const afterChar = src[afterCmdIdx] ?? "";
    if (/[A-Za-z]/.test(afterChar)) {
      // Not actually \cmd — it's \cmdX where X continues the name.
      out.push(src.slice(i, afterCmdIdx + 1));
      i = afterCmdIdx + 1;
      continue;
    }
    let j = afterCmdIdx;
    while (j < src.length && /\s/.test(src[j])) j++;
    if (src[j] !== "{") {
      out.push(src.slice(i, j));
      i = j;
      continue;
    }
    let depth = 1;
    let k = j + 1;
    while (k < src.length && depth > 0) {
      const c = src[k];
      if (c === "\\") {
        k += 2;
        continue;
      }
      if (c === "{") depth++;
      else if (c === "}") depth--;
      if (depth > 0) k++;
    }
    if (depth !== 0) {
      // Unbalanced — give up on this occurrence.
      out.push(src.slice(i, j + 1));
      i = j + 1;
      continue;
    }
    out.push(src.slice(i, idx));
    out.push(openSentinel);
    out.push(src.slice(j + 1, k));
    out.push(closeSentinel);
    i = k + 1;
  }
  return out.join("");
}

function reEscape(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

// --- Postprocess --------------------------------------------------------

function postprocessEnvironments(html: string): string {
  let s = html;

  // Images: replace sentinel with <img> placeholder. The `data-img` attr is
  // used for resolution; the src is set by the component after IPC resolves.
  const imgRe = new RegExp(
    `${reEscape(IMG_SENTINEL_PREFIX)}([\\s\\S]*?)${reEscape(IMG_SENTINEL_SUFFIX)}`,
    "g",
  );
  s = s.replace(imgRe, (_m, name: string) => {
    const trimmed = name.trim();
    return (
      `<span class="amp-img-placeholder" data-img="${trimmed}">` +
      `<span class="text-muted text-xs">[Loading image…]</span></span>`
    );
  });

  // Theorem-like envs → labeled left-border block. Capitalize the name.
  const envBlock = new RegExp(
    `${reEscape(ENV_OPEN)}([a-z]+)${reEscape(ENV_DELIM)}([\\s\\S]*?)${reEscape(ENV_CLOSE)}`,
    "g",
  );
  s = s.replace(envBlock, (_m, env: string, content: string) => {
    const label = env.charAt(0).toUpperCase() + env.slice(1) + ".";
    return (
      `<div class="my-3 border-l-4 border-border pl-3 py-1">` +
      `<span class="mr-2 font-semibold text-text">${label}</span>${content.trim()}</div>`
    );
  });

  // Close <li> at the next opener or list end (bare \item ran without braces).
  const liBlock = new RegExp(
    `${reEscape(MARK_LI_OPEN)}([\\s\\S]*?)(?=${reEscape(MARK_LI_OPEN)}|${reEscape(MARK_UL_CLOSE)}|${reEscape(MARK_OL_CLOSE)})`,
    "g",
  );
  s = s.replace(liBlock, `<li>$1</li>`);

  s = s
    .replace(new RegExp(reEscape(MARK_UL_OPEN), "g"), `<ul class="list-disc pl-6 my-2 space-y-1">`)
    .replace(new RegExp(reEscape(MARK_UL_CLOSE), "g"), `</ul>`)
    .replace(new RegExp(reEscape(MARK_OL_OPEN), "g"), `<ol class="list-decimal pl-6 my-2 space-y-1">`)
    .replace(new RegExp(reEscape(MARK_OL_CLOSE), "g"), `</ol>`)
    .replace(new RegExp(reEscape(MARK_LI_CLOSE), "g"), `</li>`)
    .replace(new RegExp(reEscape(STRONG_OPEN), "g"), `<strong>`)
    .replace(new RegExp(reEscape(STRONG_CLOSE), "g"), `</strong>`)
    .replace(new RegExp(reEscape(EM_OPEN), "g"), `<em>`)
    .replace(new RegExp(reEscape(EM_CLOSE), "g"), `</em>`)
    .replace(new RegExp(reEscape(U_OPEN), "g"), `<u>`)
    .replace(new RegExp(reEscape(U_CLOSE), "g"), `</u>`)
    .replace(
      new RegExp(reEscape(TT_OPEN), "g"),
      `<code class="rounded bg-surface px-1 py-0.5 text-sm">`,
    )
    .replace(new RegExp(reEscape(TT_CLOSE), "g"), `</code>`);

  // Final safety net: nuke any sentinel that slipped through (malformed source).
  s = s.replace(/@@AMP_[A-Z_]+@@/g, "");
  return s;
}

// --- Chunk + render -----------------------------------------------------

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
      throwOnError: false,
      displayMode: display,
      output: "html",
      strict: "ignore",
    });
  } catch {
    return `<code>${escapeHtml(expr)}</code>`;
  }
}

/** Public: render LaTeX/prose source to sanitized HTML string. Exported so
 * unit tests can exercise it without React. */
export function renderLatex(src: string): string {
  if (!src) return "";
  const preprocessed = preprocessEnvironments(src);
  const parts: string[] = [];
  let i = 0;

  while (i < preprocessed.length) {
    if (preprocessed[i] === "$" && preprocessed[i + 1] === "$") {
      const end = preprocessed.indexOf("$$", i + 2);
      if (end !== -1) {
        parts.push(renderMath(preprocessed.slice(i + 2, end), true));
        i = end + 2;
        continue;
      }
    }
    if (preprocessed[i] === "\\" && preprocessed[i + 1] === "[") {
      const end = preprocessed.indexOf("\\]", i + 2);
      if (end !== -1) {
        parts.push(renderMath(preprocessed.slice(i + 2, end), true));
        i = end + 2;
        continue;
      }
    }
    if (preprocessed[i] === "$") {
      const end = preprocessed.indexOf("$", i + 1);
      if (end !== -1) {
        parts.push(renderMath(preprocessed.slice(i + 1, end), false));
        i = end + 1;
        continue;
      }
    }
    if (preprocessed[i] === "\\" && preprocessed[i + 1] === "(") {
      const end = preprocessed.indexOf("\\)", i + 2);
      if (end !== -1) {
        parts.push(renderMath(preprocessed.slice(i + 2, end), false));
        i = end + 2;
        continue;
      }
    }
    // Walk to the next potential math opener. Search from i+1 so unmatched
    // delimiters can't trap us in an infinite loop.
    let next = preprocessed.length;
    for (const opener of ["$", "\\[", "\\("]) {
      const idx = preprocessed.indexOf(opener, i + 1);
      if (idx !== -1 && idx < next) next = idx;
    }
    parts.push(escapeHtml(preprocessed.slice(i, next)));
    i = next;
  }

  return postprocessEnvironments(parts.join(""));
}

export function LatexContent({ source, className }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [imageMap, setImageMap] = useState<Record<string, string>>({});

  // Extract unique image filenames from source.
  const imageNames = useMemo(() => extractImageNames(source), [source]);

  // Fetch image data URLs via IPC.
  useEffect(() => {
    if (imageNames.length === 0) {
      setImageMap({});
      return;
    }
    let cancelled = false;
    ipc.resolve_images(imageNames).then((map) => {
      if (!cancelled) setImageMap(map);
    }).catch(() => {
      // IPC unavailable (e.g. browser preview); silently degrade.
    });
    return () => { cancelled = true; };
  }, [imageNames]);

  const html = useMemo(() => renderLatex(source), [source]);

  // After render, replace placeholder spans with resolved <img> tags.
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const placeholders = el.querySelectorAll<HTMLSpanElement>(".amp-img-placeholder");
    placeholders.forEach((span) => {
      const name = span.getAttribute("data-img");
      if (!name) return;
      const dataUrl = imageMap[name];
      if (dataUrl) {
        const img = document.createElement("img");
        img.src = dataUrl;
        img.alt = name;
        img.className = "my-2 max-w-full rounded";
        img.style.maxHeight = "400px";
        span.replaceWith(img);
      } else if (Object.keys(imageMap).length > 0 || imageNames.length === 0) {
        // Images were fetched but this one wasn't found — show a subtle missing indicator.
        span.innerHTML = `<span class="inline-flex items-center gap-1 rounded border border-border px-2 py-1 text-xs text-muted"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" /><circle cx="8.5" cy="8.5" r="1.5" /><path d="m21 15-5-5L5 21" /></svg>${name}</span>`;
      }
    });
  }, [html, imageMap, imageNames]);

  return (
    <div
      ref={containerRef}
      className={cn("text-sm leading-relaxed", className)}
      // eslint-disable-next-line react/no-danger
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
