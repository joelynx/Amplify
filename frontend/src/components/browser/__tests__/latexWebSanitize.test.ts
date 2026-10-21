/** The web sanitizer (latexWebSanitize.ts) runs inside renderLatex(): PDF-only
 * LaTeX must come out as plain text or HTML, never as raw commands or stray
 * braces, while math is still handed to KaTeX unchanged. */

import { describe, expect, it } from "vitest";
import { renderLatex } from "../LatexContent";

/** Remove every <span class="katex…"> block (nested spans inside), the way
 * pipeline/scripts/check_web.mjs does, so only prose is left. */
function stripKatex(html: string): string {
  let out = "";
  let i = 0;
  const openRe = /<span class="katex(?:-display)?"/g;
  while (i < html.length) {
    openRe.lastIndex = i;
    const m = openRe.exec(html);
    if (!m) {
      out += html.slice(i);
      break;
    }
    out += html.slice(i, m.index);
    let depth = 0;
    let end = html.length;
    const tagRe = /<\/?span\b[^>]*>/g;
    tagRe.lastIndex = m.index;
    let t: RegExpExecArray | null;
    while ((t = tagRe.exec(html)) !== null) {
      if (t[0].startsWith("</")) depth -= 1;
      else if (!t[0].endsWith("/>")) depth += 1;
      if (depth === 0) {
        end = t.index + t[0].length;
        break;
      }
    }
    out += " ";
    i = end;
  }
  return out;
}

/** Nothing outside KaTeX markup may look like a LaTeX command or a brace. */
function expectNoRaw(html: string): void {
  const rest = stripKatex(html.replace(/<span class="katex-error"[^>]*>[\s\S]*?<\/span>/g, " ")).replace(
    /<[^>]+>/g,
    " ",
  );
  expect(rest).not.toMatch(/\\[A-Za-z]|\\\\|[{}]/);
}

describe("renderLatex - PDF-only constructs are rewritten for the web view", () => {
  it("figure scaffolding: image placeholder stays, caption becomes a caption block", () => {
    const src = String.raw`\begin{figure}[h]\begin{center}\includegraphics[alt={},max width=0.5\textwidth]{abc}\captionsetup{labelformat=empty}\caption{Fig. E6.1}\end{center}\end{figure}`;
    const html = renderLatex(src);
    expect(html).toContain('data-img="abc"');
    expect(html).toMatch(/italic[^>]*>Fig\. E6\.1</);
    expect(html).toContain("text-center");
    expectNoRaw(html);
  });

  it("tabular inside display math becomes an HTML table", () => {
    const src = String.raw`\[\begin{tabular}{|c|c|} \hline $x$ & $y$ \\ \hline 1 & 2 \\ \hline \end{tabular}\]`;
    const html = renderLatex(src);
    expect(html).toContain("<table");
    expect(html.match(/<tr>/g)?.length).toBe(2);
    expect(html.match(/<td /g)?.length).toBe(4);
    expect(html).not.toContain("katex-error");
    expectNoRaw(html);
  });

  it("multicolumn gives a colspan cell; multirow keeps its text", () => {
    const src = String.raw`\begin{center}\begin{tabular}{ccc}\multicolumn{2}{c}{Head} & \multirow{2}{*}{R} \\ a & b & c\end{tabular}\end{center}`;
    const html = renderLatex(src);
    expect(html).toContain('colspan="2"');
    expect(html).toContain(">Head<");
    expect(html).toContain(">R<");
    expectNoRaw(html);
  });

  it("sectioning: \\paragraph is a bold run-in heading, \\subsection* a heading block", () => {
    const html = renderLatex("\\paragraph{Analysis:} text\n\\subsection*{(c) Part} more");
    expect(html).toContain("<strong>Analysis:</strong> text");
    expect(html).toMatch(/font-semibold[^>]*>\(c\) Part</);
    expectNoRaw(html);
  });

  it("\\vspace vanishes; \\\\ in prose is a line break but stays a row separator inside math", () => {
    const html = renderLatex(String.raw`a\vspace{0.5em} b \\ c $\begin{pmatrix}1\\2\end{pmatrix}$`);
    expect(html).not.toContain("vspace");
    expect(html).toContain("b <br/>");
    expect(html).toContain("katex");
    expect(html).not.toContain("katex-error");
    expectNoRaw(html);
  });

  it("\\\\[2mm] drops its length and does not open display math", () => {
    const html = renderLatex(String.raw`first \\[2mm] second \[ x = 1 \]`);
    expect(html).toContain("first <br/>");
    expect(html).toContain("second");
    expect(html).not.toContain("2mm");
    expect(html).toContain("katex-display");
    expectNoRaw(html);
  });

  it("footnotetext keeps its math and text", () => {
    const html = renderLatex(String.raw`\footnotetext{\({ }^{1}\) See the text.}`);
    expect(html).toContain("katex");
    expect(html).toContain("See the text.");
    expectNoRaw(html);
  });

  it("text symbols and escapes", () => {
    const html = renderLatex(String.raw`\textsubscript{2} \textsuperscript{3} \AA \qed \textbackslash 5\% \$ \{x\} \'e \ldots`);
    expect(html).toContain("<sub>2</sub>");
    expect(html).toContain("<sup>3</sup>");
    expect(html).toContain("Å");
    expect(html).toContain("∎");
    expect(html).toContain("&#92;");
    expect(html).toContain("5%");
    expect(html).toContain("&#36;");
    expect(html).toContain("&#123;x&#125;");
    expect(html).toContain("é");
    expect(html).toContain("…");
    expectNoRaw(html);
  });

  it("TikZ pictures become a placeholder", () => {
    const html = renderLatex(String.raw`\begin{center}\begin{tikzpicture}\draw (0,0) -- (1,1);\end{tikzpicture}\end{center}`);
    expect(html).toContain("open the PDF view");
    expect(html).not.toContain("\\draw");
    expect(html).not.toContain("(0,0)");
    expectNoRaw(html);
  });

  it("bare brace groups: {\\bf x} is strong, {\\em y} is em, {z} is unwrapped", () => {
    const html = renderLatex(String.raw`{\bf Bold} and {\em it} and {plain}`);
    expect(html).toContain("<strong>Bold</strong>");
    expect(html).toContain("<em>it</em>");
    expect(html).toContain("plain");
    expectNoRaw(html);
  });

  it("a brace group that spans math closes in the right place", () => {
    const html = renderLatex(String.raw`{\bf a $x$ b} c`);
    expect(html).toMatch(/<strong>a [\s\S]*katex[\s\S]* b<\/strong> c/);
    expectNoRaw(html);
  });

  it("description lists: \\item[label] renders a bold label", () => {
    const html = renderLatex(String.raw`\begin{description}\item[Case 1] first\item[Case 2] second\end{description}`);
    expect(html).toContain("<ul");
    expect(html).toContain("<strong>Case 1</strong> first");
    expectNoRaw(html);
  });

  it("math-only commands in prose are wrapped for KaTeX", () => {
    const html = renderLatex(String.raw`so 2\cdot 3 and \frac{1}{2} and \alpha^2 work`);
    expect(html).not.toContain("katex-error");
    expect((html.match(/class="katex"/g) ?? []).length).toBe(3);
    expectNoRaw(html);
  });

  it("\\href and \\url keep the link text and address", () => {
    const html = renderLatex(String.raw`see \href{http://x.y/~u}{the page} or \url{http://a.b/c_d}`);
    expect(html).toContain("the page");
    expect(html).toContain("http://x.y/~u");
    expect(html).toContain("http://a.b/c_d");
    expectNoRaw(html);
  });

  it("comments are dropped but percentages are kept", () => {
    const html = renderLatex("text % hidden note\nnext and 50% of all");
    expect(html).not.toContain("hidden");
    expect(html).toContain("next and 50% of all");
  });

  it("verbatim becomes <pre> and protects $ and backslashes", () => {
    const html = renderLatex("\\begin{verbatim}\nx $ y \\z {w}\n\\end{verbatim}");
    expect(html).toContain("<pre");
    expect(html).toContain("x &#36; y &#92;z &#123;w&#125;");
    expectNoRaw(html);
  });

  it("unknown commands drop the command and keep the argument; lost JSON escapes keep their word", () => {
    const html = renderLatex(String.raw`\mystyle{kept} \nTherefore yes`);
    expect(html).toContain("kept");
    expect(html).not.toContain("mystyle");
    expect(html).toContain("Therefore yes");
    expectNoRaw(html);
  });

  it("eqnarray in prose is rendered by KaTeX as align", () => {
    const html = renderLatex(String.raw`\begin{eqnarray*} a &=& b \\ c &=& d \end{eqnarray*}`);
    expect(html).toContain("katex-display");
    expect(html).not.toContain("katex-error");
    expectNoRaw(html);
  });

  it("an align already inside $…$ or \\[…\\] keeps exactly one display pair", () => {
    for (const src of [
      String.raw`$\begin{align*} a &= b \\ c &= d \end{align*}$`,
      String.raw`\[ \begin{align*} a &= b \\ c &= d \end{align*} \]`,
      String.raw`$$\begin{equation*} a = b \end{equation*}$$`,
    ]) {
      const html = renderLatex(src);
      expect(html).toContain("katex-display");
      expect(html).not.toContain("katex-error");
      expect(html).not.toContain("&#36;");
    }
  });

  it("neighbouring display blocks keep their own delimiters", () => {
    const cases = [
      "$$\\begin{align*} a &= 1 \\end{align*}$$\n$$\\begin{align*} b &= 2 \\end{align*}$$",
      "\\[\\begin{array}{c} 1 \\end{array}\\]\n\\begin{align*} a &= b \\end{align*}\n\\[ 2 = 2 \\]",
      "$x$\n\\[ y = 1 \\]\n$z$",
      "\\begin{align*} a &= 1 \\end{align*}\n\\begin{align*} b &= 2 \\end{align*}",
    ];
    for (const src of cases) {
      const html = renderLatex(src);
      expect(html, src).not.toContain("katex-error");
      expect(html, src).not.toContain("&#36;");
      expect((html.match(/class="katex"/g) ?? []).length, src).toBeGreaterThanOrEqual(2);
    }
  });

  it("a stray $ inside \\[…\\] is dropped instead of breaking the formula", () => {
    const html = renderLatex(String.raw`\[$f(t) = f(14-t)\]`);
    expect(html).toContain("katex-display");
    expect(html).not.toContain("katex-error");
  });

  it("\\underline and \\textbf inside math are left to KaTeX", () => {
    const html = renderLatex(String.raw`$\underline{\int_0^1 f}$ and $\textbf{v}$`);
    expect(html).not.toContain("katex-error");
    expect(html).not.toMatch(/@@\/?AMP_/);
  });

  it("source quirks KaTeX rejects are rewritten inside math", () => {
    const cases: [string, string[]][] = [
      [String.raw`wins $\$ 1$ with`, ["katex"]],
      [String.raw`so $ \[ x = 1 \] $ holds`, ["katex-display"]],
      [String.raw`\[\text { t_cash_flow }=1\]`, ["katex-display"]],
      [String.raw`\[\begin{align*} a &= b \quad \text{(since $W \in S$, $W^T = -W$)} \end{align*}\]`, ["katex-display"]],
      [String.raw`\[\begin{array}[b]{c@{\hspace{8em}}c} 1 & 2 \end{array}\]`, ["katex-display"]],
      [String.raw`\[\left\{\begin{align*} a &= b \\ c &= d \end{align*}\right.\]`, ["katex-display"]],
      [String.raw`\begin{multline*} a \\ b \end{multline*}`, ["katex-display"]],
      [String.raw`\[ x = \begin{tabular}{|c|} \hline 1 \\ \hline \end{tabular} \]`, ["katex-display"]],
    ];
    for (const [src, expectations] of cases) {
      const html = renderLatex(src);
      expect(html, src).not.toContain("katex-error");
      for (const e of expectations) expect(html, src).toContain(e);
      expect(html, src).not.toMatch(/@@\/?AMP_/);
    }
    // The escaped dollar is still shown as a dollar sign in prose.
    expect(renderLatex(String.raw`costs \$5`)).toContain("costs &#36;5");
  });

  it("\\label inside align is removed before KaTeX sees it", () => {
    const html = renderLatex(String.raw`\begin{align} x &= 1 \label{eq:one} \end{align}`);
    expect(html).not.toContain("katex-error");
  });

  it("existing text formatting still works through the sanitizer", () => {
    const html = renderLatex(String.raw`\textbf{Step 1: $f(x) = \{0,1\}$} and \emph{this} and \texttt{mono}`);
    expect(html).toMatch(/<strong>[\s\S]*katex[\s\S]*<\/strong>/);
    expect(html).toContain("<em>this</em>");
    expect(html).toContain("<code");
    expectNoRaw(html);
  });

  it("malformed input never leaks sentinels or throws", () => {
    const samples = [
      String.raw`\section{A \textbf{b} $c$}`,
      String.raw`\caption{x}`,
      String.raw`\begin{tabular}{c} a \end{tabular}`,
      String.raw`\begin{center} x`,
      String.raw`\end{center}`,
      String.raw`{\bf unclosed`,
      String.raw`\begin{tikzpicture} no end`,
      String.raw`\verb|a$b|`,
      String.raw`\multicolumn{2}{c}{x} \hline \cline{1-2}`,
      String.raw`\newcommand{\R}{\mathbb{R}} \def\x{1} text`,
      String.raw`}}} {{{`,
      "\\",
    ];
    for (const s of samples) {
      const html = renderLatex(s);
      expect(html).not.toMatch(/@@\/?AMP_/);
    }
  });
});
