/**
 * Results screens: every style shows the same honest numbers, the newspaper
 * headline reads the numbers right, the time formats hold, and every results
 * id a preset names exists.
 */

import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { SessionSummary } from "../../events";
import { PRESETS } from "../../presets";
import { ITEMS } from "../items";
import { RESULT_STYLES, ResultsCard, ResultsPreview } from "../ResultsScreen";
import { SAMPLE, clock, hms, longTime, words } from "../shared";
import { headline } from "../styles/Newspaper";

/** Distinct two-digit numbers, so each one can be found in the markup. */
const ODD: SessionSummary = {
  mode: "quiz",
  answered: 61,
  unaided: 23,
  assisted: 19,
  partial: 11,
  missed: 18,
  toReview: 37,
  elapsedMs: 12 * 60_000 + 34_000,
};

const text = (html: string) => html.replace(/<[^>]+>/g, " ").replace(/&#x27;|&#39;/g, "'").replace(/\s+/g, " ");

describe("styles", () => {
  it("has a renderer for every item and an item for every renderer", () => {
    expect(ITEMS.map((i) => i.data?.style).sort()).toEqual(Object.keys(RESULT_STYLES).sort());
  });

  it.each(ITEMS.map((i) => i.id))("%s shows every number", (id) => {
    const out = text(renderToStaticMarkup(<ResultsCard itemId={id} summary={ODD} onClose={() => {}} />));
    for (const n of [61, 23, 19, 11, 18, 37]) expect(out, `${id} → ${n}`).toContain(String(n));
    expect(out, `${id} → time`).toContain("12:34");
  });

  it.each(ITEMS.map((i) => i.id))("%s renders a preview without a close button", (id) => {
    const html = renderToStaticMarkup(<ResultsPreview itemId={id} />);
    expect(html.length).toBeGreaterThan(200);
    expect(html).not.toMatch(/>(Done|Continue|Finish|\[ close \])</);
  });

  it("falls back to the report card for unknown ids", () => {
    const out = text(renderToStaticMarkup(<ResultsCard itemId="results.nope" summary={SAMPLE} />));
    expect(out).toContain("solved unaided");
  });
});

describe("newspaper headline", () => {
  it("spells small numbers and names the unaided count", () => {
    expect(headline(SAMPLE)).toBe("STUDENT SOLVES SEVEN UNAIDED");
    expect(headline({ ...SAMPLE, unaided: 12, answered: 20 }, "Ada")).toBe("ADA SOLVES 12 UNAIDED");
  });

  it("covers perfect, assisted-only, partial-only, all-missed and empty sessions kindly", () => {
    expect(headline({ ...SAMPLE, answered: 4, unaided: 4 })).toBe("STUDENT SOLVES ALL FOUR UNAIDED");
    expect(headline({ ...SAMPLE, answered: 1, unaided: 1 })).toBe("STUDENT SOLVES IT UNAIDED");
    expect(headline({ ...SAMPLE, unaided: 0, assisted: 2 })).toBe("STUDENT CRACKS TWO WITH HELP");
    expect(headline({ ...SAMPLE, unaided: 0, assisted: 0, partial: 3 })).toBe("STUDENT MAKES HEADWAY ON THREE");
    expect(headline({ ...SAMPLE, answered: 5, unaided: 0, assisted: 0, partial: 0, missed: 5 })).toBe(
      "STUDENT TAKES ON FIVE TOUGH QUESTIONS",
    );
    expect(headline({ ...SAMPLE, answered: 0, unaided: 0 })).toBe("QUIET DAY AT THE DESK");
  });
});

describe("formatting", () => {
  it("formats elapsed time", () => {
    expect(clock(754_000)).toBe("12:34");
    expect(clock(3_723_000)).toBe("1:02:03");
    expect(hms(754_000)).toBe("00:12:34");
    expect(longTime(754_000)).toBe("12 minutes 34 seconds");
    expect(longTime(60_000)).toBe("1 minute");
    expect(longTime(45_000)).toBe("45 seconds");
    expect(longTime(3_660_000)).toBe("1 hour 1 minute");
  });

  it("spells numbers below ten", () => {
    expect(words(0)).toBe("zero");
    expect(words(9)).toBe("nine");
    expect(words(10)).toBe("10");
  });
});

describe("items", () => {
  it("are all in the results slot", () => {
    for (const it of ITEMS) expect(it.slot).toBe("results");
  });

  it("provide every results style a preset names", () => {
    const ids = new Set(ITEMS.map((i) => i.id));
    for (const p of PRESETS) if (p.slots.results) expect(ids, `${p.id} → ${p.slots.results}`).toContain(p.slots.results);
  });
});
