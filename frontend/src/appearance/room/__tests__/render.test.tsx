/** Every room theme renders, at every time of day and season, with and without data. */

import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { EMPTY_SCENE, type SceneData } from "../helpers";
import { ITEMS } from "../items";
import { OBJECT_IDS } from "../model";
import { Scene, objectLabels } from "../Scene";
import { THEMES } from "../themes";

const DATA: SceneData = {
  subject: "Maths",
  topics: Array.from({ length: 60 }, (_, i) => ({ topic: `Topic number ${i}`, attempted: i + 1, independent: i % 7 })),
  trophies: [
    { id: "spaced_reviews", title: "Spaced reviewer" },
    { id: "comebacks", title: "Comeback" },
    { id: "honest_attempts", title: "Honest effort" },
  ],
  plantCount: 25,
  due: 4,
  nextDue: "2026-11-10T09:00:00Z",
  notes: ["Eigenvalues", "Series tests", "A very long subtopic name indeed"],
};

const TIMES = [6, 12, 18, 23];
const MONTHS = [0, 3, 6, 9];

describe("room scenes", () => {
  it("has a renderer for every item", () => {
    for (const item of ITEMS) expect(THEMES[item.data?.base as string], item.id).toBeDefined();
  });

  for (const item of ITEMS) {
    it(`${item.id} draws every object as a hotspot`, () => {
      for (const [i, h] of TIMES.entries()) {
        const now = new Date(2026, MONTHS[i], 15, h, 10);
        for (const data of [DATA, EMPTY_SCENE]) {
          const html = renderToStaticMarkup(
            <Scene
              itemId={item.id}
              data={data}
              now={now}
              lampOn={i % 2 === 0}
              motion={i % 2 === 1}
              labels={objectLabels(data.due, true)}
              onActivate={() => {}}
            />,
          );
          for (const id of OBJECT_IDS) expect(html, `${item.id} ${id}`).toContain(`data-object="${id}"`);
          expect(html.match(/role="(button|switch)"/g)?.length).toBe(OBJECT_IDS.length);
        }
      }
    });

    it(`${item.id} renders as a static preview`, () => {
      const html = renderToStaticMarkup(<Scene itemId={item.id} data={DATA} now={new Date(2026, 10, 9, 14)} lampOn motion={false} preview />);
      expect(html).toContain(`data-room="${item.data?.base}"`);
      expect(html).not.toContain("data-object");
      expect(html).not.toContain("foreignObject");
    });
  }
});
