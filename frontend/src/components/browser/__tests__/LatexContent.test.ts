/** Golden-ish tests for renderLatex(). We don't pin the full HTML (KaTeX
 * markup is verbose); instead we check structural invariants: math segments
 * become KaTeX nodes, environments produce labeled blocks, sentinels never
 * leak into the output. */

import { describe, expect, it } from "vitest";
import { renderLatex } from "../LatexContent";

describe("renderLatex — basics", () => {
  it("empty input → empty string", () => {
    expect(renderLatex("")).toBe("");
  });

  it("prose without math is HTML-escaped", () => {
    const html = renderLatex("a < b & c > d");
    expect(html).toContain("a &lt; b &amp; c &gt; d");
  });

  it("inline math renders to katex HTML", () => {
    const html = renderLatex("area is $\\pi r^2$");
    expect(html).toContain("katex");
    expect(html).toContain("area is");
  });

  it("display math renders to katex display mode", () => {
    const html = renderLatex("Identity: $$x = y$$");
    expect(html).toContain("katex-display");
  });

  it("\\[ \\] display math is recognized too", () => {
    const html = renderLatex("\\[ x = 1 \\]");
    expect(html).toContain("katex-display");
  });

  it("\\( \\) inline math is recognized", () => {
    const html = renderLatex("Define \\( f \\) as");
    expect(html).toContain("katex");
    expect(html).not.toContain("katex-display");
  });

  it("unmatched lone $ doesn't enter math mode (no infinite loop)", () => {
    const html = renderLatex("price is $10 only");
    expect(html).toBeTypeOf("string");
    expect(html).toContain("price is");
  });
});

describe("renderLatex — text-mode formatting", () => {
  it("\\textbf wraps to <strong>", () => {
    const html = renderLatex("Hello \\textbf{world}");
    expect(html).toContain("<strong>world</strong>");
  });

  it("\\emph wraps to <em>", () => {
    const html = renderLatex("Stress on \\emph{this}");
    expect(html).toContain("<em>this</em>");
  });

  it("\\textit wraps to <em>", () => {
    expect(renderLatex("\\textit{italic}")).toContain("<em>italic</em>");
  });

  it("\\underline wraps to <u>", () => {
    expect(renderLatex("\\underline{u}")).toContain("<u>u</u>");
  });

  it("\\texttt wraps to <code> with surface background", () => {
    expect(renderLatex("\\texttt{mono}")).toContain("<code");
  });

  it("nested braces inside \\textbf survive (balanced-brace parser)", () => {
    const html = renderLatex("\\textbf{Step 1: $f(x) = \\{0,1\\}$}");
    // The strong should wrap the whole argument; the math inside still renders.
    expect(html).toMatch(/<strong>[\s\S]*katex[\s\S]*<\/strong>/);
  });

  it("strips pure-spacing commands like \\hfill and \\noindent", () => {
    const html = renderLatex("Before \\hfill after \\noindent fin");
    expect(html).not.toContain("hfill");
    expect(html).not.toContain("noindent");
  });
});

describe("renderLatex — environments", () => {
  it("\\begin{proof} … \\end{proof} renders a labeled block", () => {
    const html = renderLatex("\\begin{proof}Because $x = y$.\\end{proof}");
    expect(html).toContain("Proof.");
    expect(html).toMatch(/border-l-4/);
  });

  it("starred theorem variant works too", () => {
    const html = renderLatex("\\begin{theorem*}Limits are unique.\\end{theorem*}");
    expect(html).toContain("Theorem.");
  });

  it("\\begin{align} is wrapped for KaTeX display math", () => {
    const html = renderLatex("\\begin{align}x &= 1\\\\y &= 2\\end{align}");
    // KaTeX renders the align as display math; verify a katex node appears.
    expect(html).toContain("katex");
  });

  it("\\begin{itemize} \\item ... renders as <ul><li>", () => {
    const html = renderLatex("\\begin{itemize}\\item first\\item second\\end{itemize}");
    expect(html).toContain("<ul");
    expect(html).toMatch(/<li>\s*first/);
    expect(html).toMatch(/<li>\s*second/);
  });

  it("\\begin{enumerate} → <ol>", () => {
    const html = renderLatex("\\begin{enumerate}\\item a\\item b\\end{enumerate}");
    expect(html).toContain("<ol");
  });

  it("\\begin{enumerate}[label=\\alph*] (optional arg) is consumed cleanly", () => {
    const html = renderLatex("\\begin{enumerate}[label=\\alph*]\\item a\\end{enumerate}");
    expect(html).toContain("<ol");
    expect(html).not.toContain("[label");
  });
});

describe("renderLatex — sentinels never leak", () => {
  it("sentinel markers don't appear in any output", () => {
    const samples = [
      "\\begin{itemize}\\item x\\end{itemize}",
      "\\textbf{bold} \\emph{em} \\underline{u}",
      "\\begin{proof}qed\\end{proof}",
      "plain text",
      "$x^2$",
    ];
    for (const s of samples) {
      const html = renderLatex(s);
      expect(html).not.toMatch(/@@AMP_/);
    }
  });

  it("malformed source: stray \\item with no surrounding list still doesn't leak sentinel", () => {
    const html = renderLatex("\\item orphan");
    expect(html).not.toMatch(/@@AMP_/);
  });
});
