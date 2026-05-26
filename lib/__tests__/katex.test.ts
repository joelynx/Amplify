import { describe, expect, it } from "vitest";
import { renderLatex } from "../katex";

describe("renderLatex", () => {
  it("returns empty string for empty input", () => {
    expect(renderLatex("")).toBe("");
  });

  it("escapes HTML in plain text", () => {
    const out = renderLatex("hello <script>");
    expect(out).toContain("&lt;script&gt;");
  });

  it("renders inline math $..$", () => {
    const out = renderLatex("the value $x = 1$ holds");
    expect(out).toContain("katex"); // KaTeX adds class names
    expect(out).toContain("the value ");
    expect(out).toContain(" holds");
  });

  it("renders display math $$..$$", () => {
    const out = renderLatex("$$\\int_0^1 x\\, dx$$");
    expect(out).toContain("katex-display");
  });

  it("renders display math \\[..\\]", () => {
    const out = renderLatex("\\[x^2 + y^2 = r^2\\]");
    expect(out).toContain("katex-display");
  });

  it("renders inline math \\(..\\)", () => {
    const out = renderLatex("the point \\(p\\) is");
    expect(out).toContain("katex");
    expect(out).not.toContain("katex-display");
  });

  it("preserves newlines as <br/>", () => {
    const out = renderLatex("line one\nline two");
    expect(out).toContain("<br/>");
  });

  it("falls back gracefully on malformed math", () => {
    // KaTeX with throwOnError: false renders error markup, doesn't throw.
    expect(() => renderLatex("$\\frac$")).not.toThrow();
  });

  it("handles mixed inline + display", () => {
    const out = renderLatex(
      "We claim $a = b$. Therefore:\n$$a^2 = b^2$$"
    );
    expect(out).toContain("katex-display");
    expect(out).toContain("katex"); // inline match too
  });
});
