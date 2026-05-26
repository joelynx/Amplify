import katex from "katex";

// Convert document-level LaTeX environments into inert sentinel strings so they
// survive HTML escaping in pushText. Swapped back to real HTML tags after the
// rendering pass. The sentinels are ASCII strings that won't ever occur in
// natural LaTeX source.
const MARK_UL_OPEN = "@@AMP_UL_OPEN@@";
const MARK_UL_CLOSE = "@@AMP_UL_CLOSE@@";
const MARK_OL_OPEN = "@@AMP_OL_OPEN@@";
const MARK_OL_CLOSE = "@@AMP_OL_CLOSE@@";
const MARK_LI_OPEN = "@@AMP_LI_OPEN@@";
const MARK_LI_CLOSE = "@@AMP_LI_CLOSE@@";

// Theorem-like text envs: open marker carries the environment name; close is
// a single marker.
const ENV_OPEN = "@@AMP_ENV_OPEN@@";
const ENV_DELIM = "@@AMP_ENV_DELIM@@";
const ENV_CLOSE = "@@AMP_ENV_CLOSE@@";

// Text-mode formatting commands (only applied to TEXT segments, never to
// math segments — math-mode \textbf etc. is handled by KaTeX directly).
const STRONG_OPEN = "@@AMP_STRONG_OPEN@@";
const STRONG_CLOSE = "@@AMP_STRONG_CLOSE@@";
const EM_OPEN = "@@AMP_EM_OPEN@@";
const EM_CLOSE = "@@AMP_EM_CLOSE@@";
const U_OPEN = "@@AMP_U_OPEN@@";
const U_CLOSE = "@@AMP_U_CLOSE@@";
const TT_OPEN = "@@AMP_TT_OPEN@@";
const TT_CLOSE = "@@AMP_TT_CLOSE@@";

// Drop-this commands that LaTeX uses for spacing/typography but have no useful
// HTML equivalent — strip them silently from text chunks.
const STRIP_COMMANDS = ["hfill", "noindent", "newline", "linebreak", "smallskip", "medskip", "bigskip", "vfill", "par"];

// KaTeX natively supports these inside display math — we wrap the whole
// \begin/\end block in $$...$$ so the existing chunker hands it to KaTeX.
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

// Document-level "theorem-like" environments KaTeX can't render. Rendered as
// labelled, left-border blocks.
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

function preprocessEnvironments(src: string): string {
  let s = src;

  // Optional [...] argument that follows \begin{env} in many LaTeX packages
  // (e.g. \begin{enumerate}[leftmargin=*]). Consumed so it doesn't leak.
  const OPT_ARG = "(?:\\s*\\[[^\\]]*\\])?";

  // 1) Math envs → wrap in $$...$$ so the chunker hands them to KaTeX.
  for (const env of MATH_ENVS) {
    const envEsc = env.replace(/\*/g, "\\*");
    const re = new RegExp(
      `\\\\begin\\{${envEsc}\\}${OPT_ARG}([\\s\\S]*?)\\\\end\\{${envEsc}\\}`,
      "g"
    );
    s = s.replace(
      re,
      (_, content: string) => `$$\\begin{${env}}${content}\\end{${env}}$$`
    );
  }

  // 2) Theorem-like text envs (including unnumbered starred variants and
  //    \begin{env}[option] forms) → marker pairs with name encoded between delimiters.
  for (const env of TEXT_ENVS) {
    s = s
      .replace(
        new RegExp(`\\\\begin\\{${env}\\*?\\}${OPT_ARG}`, "g"),
        `${ENV_OPEN}${env}${ENV_DELIM}`
      )
      .replace(new RegExp(`\\\\end\\{${env}\\*?\\}`, "g"), ENV_CLOSE);
  }

  // 3) Text-mode formatting commands. Use BALANCED-BRACE parsing so commands
  //    like \textbf{Step 1: $f(x)$.} survive — the inner math will be picked
  //    up by the chunker later, with the surrounding sentinels intact.
  s = wrapBracedCommand(s, "textbf", STRONG_OPEN, STRONG_CLOSE);
  s = wrapBracedCommand(s, "textit", EM_OPEN, EM_CLOSE);
  s = wrapBracedCommand(s, "emph", EM_OPEN, EM_CLOSE);
  s = wrapBracedCommand(s, "underline", U_OPEN, U_CLOSE);
  s = wrapBracedCommand(s, "texttt", TT_OPEN, TT_CLOSE);
  // \text{X} — strip the wrapper, keep the inner content. Inside math mode
  // KaTeX would render it natively; outside math it was leaking visibly.
  s = wrapBracedCommand(s, "text", "", "");
  // \mathrm{X} and \mathit{X} — same treatment as \text outside math mode.
  s = wrapBracedCommand(s, "mathrm", "", "");
  s = wrapBracedCommand(s, "mathit", "", "");

  // Strip pure-spacing commands (no useful HTML equivalent).
  for (const cmd of STRIP_COMMANDS) {
    s = s.replace(new RegExp(`\\\\${cmd}\\b`, "g"), "");
  }

  // 4) Lists. Tolerates \begin{itemize}[opts] / \begin{enumerate}[opts].
  s = s
    .replace(new RegExp(`\\\\begin\\{itemize\\}${OPT_ARG}`, "g"), MARK_UL_OPEN)
    .replace(/\\end\{itemize\}/g, MARK_UL_CLOSE)
    .replace(new RegExp(`\\\\begin\\{enumerate\\}${OPT_ARG}`, "g"), MARK_OL_OPEN)
    .replace(/\\end\{enumerate\}/g, MARK_OL_CLOSE);
  // Braced \item{...} — balanced-brace parser handles nested braces (e.g.
  // \item{Let $\frac{3}{2}$ ...}) that non-greedy regex would mis-truncate.
  s = wrapBracedCommand(s, "item", MARK_LI_OPEN, MARK_LI_CLOSE);
  // Bare \item (no braces) — pseudo-open; postprocess closes it at the next
  // \item or list-end marker via lookahead.
  s = s.replace(/\\item\b/g, MARK_LI_OPEN);
  return s;
  // Note: \\ (LaTeX line break) is NOT preprocessed here — it's legitimate
  // inside math mode (row separator in matrices, align, etc.) and KaTeX
  // handles it natively. Touching it pre-chunker corrupted matrix questions.
}

// Find every \<cmd>{...} occurrence with proper brace-depth tracking, replace
// with sentinel-wrapped content. Handles nested braces inside the argument
// (which non-greedy regex would mis-truncate).
function wrapBracedCommand(
  src: string,
  cmd: string,
  openSentinel: string,
  closeSentinel: string
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
    // Confirm it's a whole command (not e.g. \textbfx where 'x' continues the name).
    const afterCmdIdx = idx + needle.length;
    const afterChar = src[afterCmdIdx] ?? "";
    if (/[A-Za-z]/.test(afterChar)) {
      // Not our command — emit up through this char and keep scanning.
      out.push(src.slice(i, afterCmdIdx + 1));
      i = afterCmdIdx + 1;
      continue;
    }
    // Skip whitespace between command and opening brace.
    let j = afterCmdIdx;
    while (j < src.length && /\s/.test(src[j])) j++;
    if (src[j] !== "{") {
      // No braces — leave the command alone (caller can handle later).
      out.push(src.slice(i, j));
      i = j;
      continue;
    }
    // Balanced-brace scan for the closing brace.
    let depth = 1;
    let k = j + 1;
    while (k < src.length && depth > 0) {
      const c = src[k];
      if (c === "\\") {
        // Skip the escaped char so \{ and \} don't shift depth.
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

// Escape a literal string for use inside a RegExp.
function reEscape(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function postprocessEnvironments(html: string): string {
  let s = html;

  // Theorem-like envs → labelled, left-border block.
  const envBlock = new RegExp(
    `${reEscape(ENV_OPEN)}([a-z]+)${reEscape(ENV_DELIM)}([\\s\\S]*?)${reEscape(ENV_CLOSE)}`,
    "g"
  );
  s = s.replace(envBlock, (_, env: string, content: string) => {
    const label = env.charAt(0).toUpperCase() + env.slice(1) + ".";
    return `<div class="my-3 border-l-4 border-ink-300 pl-3 py-1"><span class="mr-2 font-semibold text-ink-900">${label}</span>${content.trim()}</div>`;
  });

  // Close <li> at the next opener or list end.
  const liBlock = new RegExp(
    `${reEscape(MARK_LI_OPEN)}([\\s\\S]*?)(?=${reEscape(MARK_LI_OPEN)}|${reEscape(MARK_UL_CLOSE)}|${reEscape(MARK_OL_CLOSE)})`,
    "g"
  );
  s = s.replace(liBlock, `<li>$1</li>`);

  s = s
    .replace(new RegExp(reEscape(MARK_UL_OPEN), "g"), `<ul class="list-disc pl-6 my-2 space-y-1">`)
    .replace(new RegExp(reEscape(MARK_UL_CLOSE), "g"), `</ul>`)
    .replace(new RegExp(reEscape(MARK_OL_OPEN), "g"), `<ol class="list-decimal pl-6 my-2 space-y-1">`)
    .replace(new RegExp(reEscape(MARK_OL_CLOSE), "g"), `</ol>`)
    .replace(new RegExp(reEscape(MARK_LI_CLOSE), "g"), `</li>`)
    // Text-mode formatting → real HTML tags.
    .replace(new RegExp(reEscape(STRONG_OPEN), "g"), `<strong>`)
    .replace(new RegExp(reEscape(STRONG_CLOSE), "g"), `</strong>`)
    .replace(new RegExp(reEscape(EM_OPEN), "g"), `<em>`)
    .replace(new RegExp(reEscape(EM_CLOSE), "g"), `</em>`)
    .replace(new RegExp(reEscape(U_OPEN), "g"), `<u>`)
    .replace(new RegExp(reEscape(U_CLOSE), "g"), `</u>`)
    .replace(new RegExp(reEscape(TT_OPEN), "g"), `<code class="rounded bg-ink-100 px-1 py-0.5 text-sm">`)
    .replace(new RegExp(reEscape(TT_CLOSE), "g"), `</code>`);

  // Final safety net: nuke any sentinel that slipped through structural matching
  // (e.g. a bare \item in malformed source with no surrounding \begin{itemize}).
  // Better to drop the marker than show "@@AMP_*@@" to the user.
  s = s.replace(/@@AMP_[A-Z_]+@@/g, "");
  return s;
}

// Render a LaTeX string into safe HTML. Used by the question viewer.
// Mixes inline ($..$) and display ($$..$$ / \[..\]) math; passes prose through.
export function renderLatex(src: string): string {
  if (!src) return "";

  src = preprocessEnvironments(src);

  const parts: string[] = [];
  let i = 0;

  const pushText = (s: string) => {
    const escaped = s
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\n/g, "<br/>");
    parts.push(escaped);
  };

  const render = (math: string, displayMode: boolean) => {
    try {
      parts.push(
        katex.renderToString(math, {
          throwOnError: false,
          displayMode,
          output: "html",
          strict: "ignore",
        })
      );
    } catch {
      parts.push(`<code>${math}</code>`);
    }
  };

  while (i < src.length) {
    if (src[i] === "$" && src[i + 1] === "$") {
      const end = src.indexOf("$$", i + 2);
      if (end !== -1) {
        render(src.slice(i + 2, end), true);
        i = end + 2;
        continue;
      }
    }
    if (src[i] === "\\" && src[i + 1] === "[") {
      const end = src.indexOf("\\]", i + 2);
      if (end !== -1) {
        render(src.slice(i + 2, end), true);
        i = end + 2;
        continue;
      }
    }
    if (src[i] === "$") {
      const end = src.indexOf("$", i + 1);
      if (end !== -1) {
        render(src.slice(i + 1, end), false);
        i = end + 1;
        continue;
      }
    }
    if (src[i] === "\\" && src[i + 1] === "(") {
      const end = src.indexOf("\\)", i + 2);
      if (end !== -1) {
        render(src.slice(i + 2, end), false);
        i = end + 2;
        continue;
      }
    }
    let next = src.length;
    // Search from i+1 to guarantee progress when src[i] is an UNMATCHED delimiter.
    for (const opener of ["$", "\\[", "\\("]) {
      const idx = src.indexOf(opener, i + 1);
      if (idx !== -1 && idx < next) next = idx;
    }
    pushText(src.slice(i, next));
    i = next;
  }

  return postprocessEnvironments(parts.join(""));
}
