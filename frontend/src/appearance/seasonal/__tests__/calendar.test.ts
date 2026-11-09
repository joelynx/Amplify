import { describe, expect, it } from "vitest";

import { CALENDAR, activeEvents, nthWeekday, parseClubEvents, type ClubEvent } from "../calendar";

const on = (y: number, m: number, d: number, club: ClubEvent[] = []) =>
  activeEvents(new Date(y, m - 1, d, 12), club).map((e) => e.id);

describe("fixed dates", () => {
  it("finds Pi Day on 14 March only", () => {
    expect(on(2026, 3, 14)).toContain("pi-day");
    expect(on(2031, 3, 14)).toContain("pi-day");
    expect(on(2026, 3, 13)).not.toContain("pi-day");
    expect(on(2026, 3, 15)).not.toContain("pi-day");
  });

  it("is quiet on an ordinary day", () => {
    expect(on(2026, 1, 15)).toEqual([]);
  });

  it("knows the other anniversaries", () => {
    expect(on(2026, 12, 22)).toContain("national-mathematics-day");
    expect(on(2026, 12, 2)).toContain("uae-national-day");
    expect(on(2026, 6, 28)).toContain("tau-day");
  });
});

describe("Programmers' Day (256th day)", () => {
  it("is 13 September in a common year", () => {
    expect(on(2026, 9, 13)).toContain("programmers-day");
    expect(on(2026, 9, 12)).not.toContain("programmers-day");
    expect(on(2027, 9, 13)).toContain("programmers-day");
  });

  it("is 12 September in a leap year", () => {
    expect(on(2028, 9, 12)).toContain("programmers-day");
    expect(on(2028, 9, 13)).not.toContain("programmers-day");
    expect(on(2024, 9, 12)).toContain("programmers-day");
  });
});

describe("Ada Lovelace Day (2nd Tuesday of October)", () => {
  it.each([
    [2024, 8],
    [2025, 14],
    [2026, 13],
    [2027, 12],
    [2028, 10],
    [2030, 8],
  ])("%i: the 2nd Tuesday is %i October", (y, d) => {
    expect(nthWeekday(y, 10, 2, 2).getDate()).toBe(d);
    expect(on(y, 10, d)).toContain("ada-lovelace-day");
    expect(on(y, 10, d - 7)).not.toContain("ada-lovelace-day");
    expect(on(y, 10, d + 7)).not.toContain("ada-lovelace-day");
  });
});

describe("lunar festivals", () => {
  it("has Diwali on 8 November 2026", () => {
    expect(on(2026, 11, 8)).toContain("diwali");
    expect(on(2026, 11, 9)).not.toContain("diwali");
  });

  it("runs Eid for three days and marks it approximate", () => {
    expect(on(2026, 3, 19)).not.toContain("eid-al-fitr");
    for (const d of [20, 21, 22]) expect(on(2026, 3, d)).toContain("eid-al-fitr");
    expect(on(2026, 3, 23)).not.toContain("eid-al-fitr");
    const eid = activeEvents(new Date(2026, 4, 27, 12)).find((e) => e.id === "eid-al-adha");
    expect(eid?.approximate).toBe(true);
  });

  it("covers both Eid al-Fitr dates in 2033, across the new year", () => {
    expect(on(2033, 1, 2)).toContain("eid-al-fitr");
    expect(on(2033, 12, 23)).toContain("eid-al-fitr");
    expect(on(2034, 1, 1)).not.toContain("eid-al-fitr");
    expect(on(2033, 12, 25)).toContain("eid-al-fitr");
  });

  it("has every lunar table entry from 2026 to 2035", () => {
    for (const e of CALENDAR) {
      if (e.rule.type !== "table") continue;
      const years = new Set(e.rule.dates.map((d) => Number(d.slice(0, 4))));
      for (let y = 2026; y <= 2035; y++) expect(years.has(y)).toBe(true);
    }
  });
});

describe("club events", () => {
  const raw = [
    { id: "Integration Bee", name: "Integration Bee", date: "03-05", message: "Bring your best substitutions." },
    { id: "anniversary", name: "Club anniversary", date: "2026-09-01", message: "Five years of the club." },
    { id: "leap", name: "Leap day social", date: "02-29", message: "" },
    { id: "bad-month", name: "Nope", date: "13-01", message: "" },
    { id: "bad-day", name: "Nope", date: "2026-02-30", message: "" },
    { id: "no-name", date: "04-01", message: "" },
    { name: "No id", date: "04-01", message: "" },
    "not an object",
    null,
  ];

  it("keeps valid entries and drops malformed ones", () => {
    const parsed = parseClubEvents(raw);
    expect(parsed.map((e) => e.id)).toEqual(["integration-bee", "anniversary", "leap"]);
  });

  it("accepts a JSON string and ignores junk", () => {
    expect(parseClubEvents(JSON.stringify(raw.slice(0, 1)))).toHaveLength(1);
    expect(parseClubEvents("{oops")).toEqual([]);
    expect(parseClubEvents(null)).toEqual([]);
    expect(parseClubEvents({ id: "x" })).toEqual([]);
    expect(parseClubEvents(undefined)).toEqual([]);
  });

  it("shows yearly and one-off events on their days, club events first", () => {
    const club = parseClubEvents(raw);
    expect(on(2027, 3, 5, club)).toEqual(["integration-bee"]);
    expect(on(2026, 9, 1, club)).toEqual(["anniversary"]);
    expect(on(2027, 9, 1, club)).toEqual([]);
    expect(on(2028, 2, 29, club)).toEqual(["leap"]);
    expect(on(2026, 3, 14, [...club, { id: "pi", name: "Club Pi Day", date: "03-14", message: "" }])).toEqual([
      "pi",
      "pi-day",
    ]);
  });

  it("validates club events passed straight to activeEvents", () => {
    const junk = [{ id: "x", name: "X", date: "99-99", message: "" }] as ClubEvent[];
    expect(on(2026, 1, 15, junk)).toEqual([]);
  });
});
