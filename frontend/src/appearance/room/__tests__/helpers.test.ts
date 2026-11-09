/** Pure helpers of the study room: time, season, plant, books, text. */

import { describe, expect, it } from "vitest";

import type { LearningStats, Milestone, ReviewSummary } from "../../../lib/ipc";
import {
  abbreviate,
  bookWidth,
  chartBars,
  clockHands,
  clockText,
  dayPart,
  daysUntil,
  examCountdown,
  greeting,
  hashString,
  layoutBooks,
  noteLines,
  plantStage,
  relativeDay,
  reviewsToNextStage,
  season,
  seeded,
  timeOfDay,
  toSceneData,
  type Shelf,
  type TopicBook,
} from "../helpers";

const at = (h: number, m = 0, month = 10, day = 9) => new Date(2026, month, day, h, m);

describe("timeOfDay", () => {
  it("splits the day at 5, 8, 17 and 20", () => {
    expect(timeOfDay(at(4, 59))).toBe("night");
    expect(timeOfDay(at(5))).toBe("dawn");
    expect(timeOfDay(at(7, 59))).toBe("dawn");
    expect(timeOfDay(at(8))).toBe("day");
    expect(timeOfDay(at(16, 59))).toBe("day");
    expect(timeOfDay(at(17))).toBe("dusk");
    expect(timeOfDay(at(19, 59))).toBe("dusk");
    expect(timeOfDay(at(20))).toBe("night");
    expect(timeOfDay(at(0))).toBe("night");
  });
});

describe("season", () => {
  it("uses meteorological seasons", () => {
    const months = Array.from({ length: 12 }, (_, m) => season(new Date(2026, m, 15)));
    expect(months).toEqual([
      "winter", "winter", "spring", "spring", "spring", "summer",
      "summer", "summer", "autumn", "autumn", "autumn", "winter",
    ]);
  });
});

describe("greeting", () => {
  it("picks the part of the day", () => {
    expect(dayPart(at(6))).toBe("morning");
    expect(dayPart(at(12))).toBe("afternoon");
    expect(dayPart(at(18))).toBe("evening");
    expect(dayPart(at(23))).toBe("night");
    expect(dayPart(at(3))).toBe("night");
  });

  it("adds the name when there is one", () => {
    expect(greeting(at(19), "Joel")).toBe("Good evening, Joel");
    expect(greeting(at(19), "  ")).toBe("Good evening");
    expect(greeting(at(9), "")).toBe("Good morning");
  });
});

describe("exam countdown", () => {
  const now = at(22, 30);
  it("counts calendar days", () => {
    expect(daysUntil("2026-11-21", now)).toBe(12);
    expect(daysUntil("2026-11-09", now)).toBe(0);
    expect(daysUntil("2026-11-01", now)).toBe(-8);
    expect(daysUntil("not a date", now)).toBeNull();
  });

  it("formats the line, hiding past or unset exams", () => {
    expect(examCountdown({ label: "Finals", date: "2026-11-21" }, now)).toBe("12 days to Finals");
    expect(examCountdown({ label: "Finals", date: "2026-11-10" }, now)).toBe("1 day to Finals");
    expect(examCountdown({ label: "finals", date: "2026-11-09" }, now)).toBe("Finals is today");
    expect(examCountdown({ label: "", date: "2026-11-12" }, now)).toBe("3 days to the exam");
    expect(examCountdown({ label: "Finals", date: "2026-11-01" }, now)).toBeNull();
    expect(examCountdown({ label: "Finals", date: null }, now)).toBeNull();
  });
});

describe("relative days and clock", () => {
  const now = at(10);
  it("says today, tomorrow, in n days", () => {
    expect(relativeDay(new Date(2026, 10, 9, 23).toISOString(), now)).toBe("today");
    expect(relativeDay(new Date(2026, 10, 10, 1).toISOString(), now)).toBe("tomorrow");
    expect(relativeDay(new Date(2026, 10, 13, 9).toISOString(), now)).toBe("in 4 days");
    expect(relativeDay(new Date(2026, 10, 7, 9).toISOString(), now)).toBe("2 days ago");
    expect(relativeDay(null, now)).toBeNull();
    expect(relativeDay("garbage", now)).toBeNull();
  });

  it("formats the clock and hand angles", () => {
    expect(clockText(at(7, 5))).toBe("07:05");
    expect(clockHands(at(3, 0))).toEqual({ hour: 90, minute: 0 });
    expect(clockHands(at(15, 30))).toEqual({ hour: 105, minute: 180 });
  });
});

describe("plantStage", () => {
  it("grows at 0/1/3/8/20 and never goes back", () => {
    expect([0, 1, 2, 3, 7, 8, 19, 20, 500].map(plantStage)).toEqual([0, 1, 1, 2, 2, 3, 3, 4, 4]);
    expect(plantStage(-4)).toBe(0);
    expect(plantStage(Number.NaN)).toBe(0);
  });

  it("says how many reviews until the next stage", () => {
    expect(reviewsToNextStage(0)).toBe(1);
    expect(reviewsToNextStage(4)).toBe(4);
    expect(reviewsToNextStage(25)).toBeNull();
  });
});

describe("abbreviate and noteLines", () => {
  it("keeps short titles and shortens long ones", () => {
    expect(abbreviate("Calculus", 10)).toBe("Calculus");
    expect(abbreviate("Linear Algebra", 9)).toBe("Lin. Alg.");
    expect(abbreviate("Theory of Linear Algebra and Matrices", 6)).toBe("TLAM");
    expect(abbreviate("Thermodynamics", 8)).toBe("Thermo.");
    expect(abbreviate("Anything", 0)).toBe("");
    for (const t of ["Ordinary Differential Equations", "Probability", "A B C D E F G"]) {
      for (let n = 1; n < 20; n++) expect(abbreviate(t, n).length).toBeLessThanOrEqual(n);
    }
  });

  it("wraps notes into short lines", () => {
    expect(noteLines("Series tests", 8)).toEqual(["Series", "tests"]);
    expect(noteLines("Bayes", 8)).toEqual(["Bayes"]);
    const lines = noteLines("Ordinary differential equations of order two", 8, 2);
    expect(lines).toHaveLength(2);
    expect(lines[1].endsWith("…")).toBe(true);
    for (const l of lines) expect(l.length).toBeLessThanOrEqual(9);
  });
});

describe("layoutBooks", () => {
  const shelves: Shelf[] = [
    { x: 10, base: 100, width: 100, height: 80 },
    { x: 10, base: 200, width: 100, height: 80 },
  ];
  const t = (topic: string, attempted: number, independent: number): TopicBook => ({ topic, attempted, independent });

  it("thickens books with independent solves", () => {
    expect(bookWidth(0)).toBe(9);
    expect(bookWidth(4)).toBe(15);
    expect(bookWidth(10_000)).toBe(30);
    expect(bookWidth(1)).toBeGreaterThan(bookWidth(0));
  });

  it("places practised topics alphabetically within the shelves", () => {
    const { books, overflow } = layoutBooks([t("b", 3, 1), t("a", 2, 0), t("never", 0, 0)], shelves);
    expect(overflow).toBe(0);
    expect(books.map((b) => b.topic)).toEqual(["a", "b"]);
    for (const b of books) {
      const s = shelves[b.shelf];
      expect(b.x).toBeGreaterThanOrEqual(s.x);
      expect(b.x + b.w).toBeLessThanOrEqual(s.x + s.width);
      expect(b.y + b.h).toBe(s.base);
      expect(b.h).toBeLessThanOrEqual(s.height);
    }
    expect(books[1].x).toBeGreaterThan(books[0].x);
  });

  it("wraps to the next shelf and keeps the most practised when full", () => {
    const many = Array.from({ length: 30 }, (_, i) => t(`topic ${String(i).padStart(2, "0")}`, i + 1, 9));
    const { books, overflow } = layoutBooks(many, shelves);
    expect(books.length + overflow).toBe(30);
    expect(overflow).toBeGreaterThan(0);
    expect(new Set(books.map((b) => b.shelf))).toEqual(new Set([0, 1]));
    const kept = new Set(books.map((b) => b.topic));
    expect(kept.has("topic 29")).toBe(true);
    expect(kept.has("topic 00")).toBe(false);
  });

  it("labels only spines wide enough and keeps colours stable", () => {
    const { books } = layoutBooks([t("Linear Algebra", 5, 25), t("Thin", 5, 0)], shelves);
    const wide = books.find((b) => b.topic === "Linear Algebra")!;
    const thin = books.find((b) => b.topic === "Thin")!;
    expect(wide.label.length).toBeGreaterThan(0);
    expect(thin.label).toBe("");
    const again = layoutBooks([t("Linear Algebra", 1, 25)], shelves, { colors: 8 }).books[0];
    expect(again.color).toBe(wide.color);
  });

  it("handles no shelves or no topics", () => {
    expect(layoutBooks([t("a", 1, 1)], [])).toEqual({ books: [], overflow: 1 });
    expect(layoutBooks([], shelves)).toEqual({ books: [], overflow: 0 });
  });
});

describe("hash and seeded random", () => {
  it("is deterministic", () => {
    expect(hashString("abc")).toBe(hashString("abc"));
    expect(hashString("abc")).not.toBe(hashString("abd"));
    const a = seeded(42);
    const b = seeded(42);
    const xs = [a(), a(), a()];
    expect([b(), b(), b()]).toEqual(xs);
    for (const x of xs) expect(x >= 0 && x < 1).toBe(true);
  });
});

describe("toSceneData", () => {
  it("survives a missing bridge", () => {
    const d = toSceneData(null, null, null, null);
    expect(d.due).toBeNull();
    expect(d.topics).toEqual([]);
    expect(d.trophies).toEqual([]);
    expect(d.plantCount).toBe(0);
  });

  it("maps topics, trophies, plant and notes", () => {
    const stats = {
      delayed: { n: 11, independent: 4 },
      topics: [
        { topic: "Calculus", attempted: 4, independent: 2 },
        { topic: "Unseen", attempted: 0, independent: 0 },
      ],
    } as unknown as LearningStats;
    const reviews = {
      counts: { due: 2, mistakes: 0, assisted: 0, bookmarked: 0 },
      next_due: "2026-11-10T09:00:00Z",
      tracked: 5,
      retired: 0,
      lists: {
        due: [
          { question_id: 1, topic: "Calculus", subtopic: "Series" },
          { question_id: 2, topic: "Calculus", subtopic: "Series" },
          { question_id: 3, topic: "Algebra" },
        ],
        mistakes: [],
        assisted: [],
        bookmarked: [],
      },
    } as unknown as ReviewSummary;
    const milestones: Milestone[] = [
      { id: "spaced_reviews", title: "Spaced reviewer", description: "", target: 5, progress: 5, unlocked: true, theme_id: "sage" },
      { id: "comebacks", title: "Comeback", description: "", target: 3, progress: 1, unlocked: false, theme_id: "ember" },
    ];
    const d = toSceneData("Maths", stats, reviews, milestones);
    expect(d.subject).toBe("Maths");
    expect(d.topics).toEqual([{ topic: "Calculus", attempted: 4, independent: 2 }]);
    expect(d.trophies).toEqual([{ id: "spaced_reviews", title: "Spaced reviewer" }]);
    expect(d.plantCount).toBe(11);
    expect(d.due).toBe(2);
    expect(d.notes).toEqual(["Series", "Algebra"]);
  });

  it("builds chart bars from the most practised topics", () => {
    const bars = chartBars([
      { topic: "a", attempted: 10, independent: 5 },
      { topic: "b", attempted: 5, independent: 5 },
    ]);
    expect(bars).toEqual([
      { value: 1, share: 0.5 },
      { value: 0.5, share: 1 },
    ]);
  });
});
