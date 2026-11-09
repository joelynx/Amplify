import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { applyBootTheme } from "../apply";
import { LogoSvg, pixelSvg } from "../brand/Logo";
import { LOGOS } from "../brand/logoData";
import { getPref, setPref } from "../prefs";

describe("pixel logo", () => {
  it("puts every zero on the pixel grid, so all six come out the same", () => {
    const [vx, vy, vw, vh] = LOGOS.matrix.viewBox.split(/\s+/).map(Number);
    const w = 110;
    const h = Math.round((w * vh) / vw);
    const doc = new DOMParser().parseFromString(pixelSvg("matrix", w, h, {}), "image/svg+xml");
    const zeros = [...doc.querySelectorAll("g.z use")];
    expect(zeros).toHaveLength(6);
    expect(new Set(zeros.map((u) => u.getAttribute("href"))).size).toBe(1);
    for (const u of zeros) {
      const px = ((Number(u.getAttribute("x")) - vx) * w) / vw;
      const py = ((Number(u.getAttribute("y")) - vy) * h) / vh;
      expect(Math.abs(px - Math.round(px))).toBeLessThan(1e-3);
      expect(Math.abs(py - Math.round(py))).toBeLessThan(1e-3);
    }
  });
});

describe("comic logo", () => {
  it("draws one shadow layer of the inked parts underneath, and no filters", () => {
    const html = renderToStaticMarkup(createElement(LogoSvg, { name: "matrix", variant: "comic" }));
    const doc = new DOMParser().parseFromString(html, "image/svg+xml");
    const shadow = doc.querySelector(".comic-shadow")!;
    expect(shadow).not.toBeNull();
    expect(shadow.previousElementSibling?.tagName).toBe("defs");
    expect(shadow.querySelectorAll(".br").length).toBeGreaterThan(0);
    expect(shadow.querySelectorAll(".d").length).toBe(3);
    expect(shadow.querySelectorAll(".z, .s").length).toBe(0);
    expect(html).not.toContain("filter");
  });

  it("only the comic variant gets a shadow layer", () => {
    const html = renderToStaticMarkup(createElement(LogoSvg, { name: "inline", variant: "original" }));
    expect(html).not.toContain("comic-shadow");
  });
});

describe("prefs", () => {
  it("are read back synchronously after a write", () => {
    expect(getPref("test.key", "fallback")).toBe("fallback");
    setPref("test.key", { a: 1 });
    expect(getPref("test.key", null)).toEqual({ a: 1 });
  });
});

describe("boot theme", () => {
  it("puts the saved palette on <html> before settings load", () => {
    const root = document.documentElement;
    expect(applyBootTheme("#boot-theme=midnight")).toBe(true);
    expect(root.getAttribute("data-theme")).toBe("midnight");
    expect(root.getAttribute("data-dark")).toBe("true");
    applyBootTheme("#boot-theme=default-light");
    expect(root.getAttribute("data-dark")).toBe("false");
  });

  it("ignores an unknown or missing theme and leaves routes alone", () => {
    const root = document.documentElement;
    applyBootTheme("#boot-theme=default-light");
    expect(applyBootTheme("#boot-theme=not-a-theme")).toBe(true);
    expect(applyBootTheme("")).toBe(false);
    expect(applyBootTheme("#/theme-lab")).toBe(false);
    expect(root.getAttribute("data-theme")).toBe("default-light");
  });
});
