/**
 * Seasonal and calendar events (Makeover.md §5.17): date rules, the lunar
 * festival table and owner-set club events. Pure, so it is unit-tested;
 * SeasonalLayer decides what to show.
 */

export type EventKind = "math" | "coding" | "culture" | "club";

export interface SeasonEvent {
  id: string;
  name: string;
  message: string;
  kind: EventKind;
  /** Short text mark for the banner (π, τ, 0x100 …). */
  glyph?: string;
  /** The date is an estimate (Eid depends on the moon sighting). */
  approximate?: boolean;
}

/** An owner-set event from configs.CLUB_EVENTS. */
export interface ClubEvent {
  id: string;
  name: string;
  /** "MM-DD" every year, or "YYYY-MM-DD" once. */
  date: string;
  message: string;
}

type Rule =
  | { type: "fixed"; month: number; day: number }
  /** The nth `weekday` (0 = Sunday) of `month`. */
  | { type: "nth-weekday"; month: number; weekday: number; n: number }
  /** Day `day` of the year, counting 1 January as day 1. */
  | { type: "day-of-year"; day: number }
  /** Pre-computed "YYYY-MM-DD" dates (lunar calendars). */
  | { type: "table"; dates: readonly string[] };

interface Entry extends SeasonEvent {
  rule: Rule;
  /** How many days the event lasts from its start date (default 1). */
  days?: number;
}

/**
 * Lunar festivals, 2026–2035. Diwali is the Lakshmi Puja day (Amavasya of
 * Kartika). Eid dates follow the Umm al-Qura pattern and may move by a day
 * with the actual moon sighting, so they are marked approximate. Extend the
 * table before 2036.
 */
export const LUNAR_DATES = {
  diwali: [
    "2026-11-08", "2027-10-29", "2028-10-17", "2029-11-05", "2030-10-26",
    "2031-11-14", "2032-11-02", "2033-10-22", "2034-11-10", "2035-10-30",
  ],
  eidAlFitr: [
    "2026-03-20", "2027-03-09", "2028-02-26", "2029-02-14", "2030-02-04", "2031-01-24",
    "2032-01-14", "2033-01-02", "2033-12-23", "2034-12-12", "2035-12-01",
  ],
  eidAlAdha: [
    "2026-05-27", "2027-05-16", "2028-05-05", "2029-04-24", "2030-04-13",
    "2031-04-02", "2032-03-22", "2033-03-11", "2034-03-01", "2035-02-18",
  ],
} as const;

const fixed = (month: number, day: number): Rule => ({ type: "fixed", month, day });

export const CALENDAR: Entry[] = [
  { id: "e-day", name: "e Day", kind: "math", glyph: "e", rule: fixed(2, 7),
    message: "2.71828…: may your progress compound continuously." },
  { id: "pi-day", name: "Pi Day", kind: "math", glyph: "π", rule: fixed(3, 14),
    message: "3.14159… and counting. Answer something at 3:14." },
  { id: "noether", name: "Emmy Noether's birthday", kind: "math", glyph: "⇄", rule: fixed(3, 23),
    message: "Born 1882. Every symmetry hides a conservation law." },
  { id: "euler", name: "Euler's birthday", kind: "math", glyph: "Σ", rule: fixed(4, 15),
    message: "Born 1707. \"Read Euler, read Euler, he is the master of us all.\" (attributed to Laplace)" },
  { id: "gauss", name: "Gauss's birthday", kind: "math", glyph: "∑", rule: fixed(4, 30),
    message: "Born 1777. Pauca sed matura: few, but ripe." },
  { id: "towel-day", name: "Towel Day", kind: "culture", glyph: "42", rule: fixed(5, 25),
    message: "Don't panic. And know where your towel is." },
  { id: "turing", name: "Alan Turing's birthday", kind: "coding", glyph: "01", rule: fixed(6, 23),
    message: "Born 1912. We can only see a short distance ahead, but we can see plenty there that needs to be done." },
  { id: "tau-day", name: "Tau Day", kind: "math", glyph: "τ", rule: fixed(6, 28),
    message: "τ = 6.28318…: twice the pie." },
  { id: "pi-approximation-day", name: "Pi Approximation Day", kind: "math", glyph: "22/7", rule: fixed(7, 22),
    message: "22/7 = 3.142857…: close enough." },
  { id: "programmers-day", name: "Programmers' Day", kind: "coding", glyph: "0x100", rule: { type: "day-of-year", day: 256 },
    message: "Day 256 of the year. Happy Programmers' Day!" },
  { id: "ada-lovelace-day", name: "Ada Lovelace Day", kind: "coding", glyph: "{ }",
    rule: { type: "nth-weekday", month: 10, weekday: 2, n: 2 },
    message: "Celebrating women in science, technology, engineering and maths, after the author of the first published program." },
  { id: "mole-day", name: "Mole Day", kind: "culture", glyph: "mol", rule: fixed(10, 23),
    message: "6.02 × 10²³ reasons to celebrate chemistry." },
  { id: "halloween", name: "Halloween", kind: "culture", glyph: "∅", rule: fixed(10, 31),
    message: "Beware the undefined." },
  { id: "fibonacci-day", name: "Fibonacci Day", kind: "math", glyph: "φ", rule: fixed(11, 23),
    message: "1, 1, 2, 3, 5, 8, 13, 21…" },
  { id: "uae-national-day", name: "UAE National Day", kind: "culture", glyph: "★", rule: fixed(12, 2),
    message: "Happy Eid Al Etihad!" },
  { id: "grace-hopper", name: "Grace Hopper's birthday", kind: "coding", glyph: "bug", rule: fixed(12, 9),
    message: "Born 1906. \"First actual case of bug being found.\"" },
  { id: "national-mathematics-day", name: "National Mathematics Day", kind: "math", glyph: "1729", rule: fixed(12, 22),
    message: "Srinivasa Ramanujan was born on this day in 1887. Try searching for 1729." },
  { id: "diwali", name: "Diwali", kind: "culture", glyph: "✦", rule: { type: "table", dates: LUNAR_DATES.diwali },
    message: "Happy Diwali! May every lamp make the next proof a little clearer." },
  { id: "eid-al-fitr", name: "Eid al-Fitr", kind: "culture", glyph: "☾", approximate: true, days: 3,
    rule: { type: "table", dates: LUNAR_DATES.eidAlFitr }, message: "Eid Mubarak!" },
  { id: "eid-al-adha", name: "Eid al-Adha", kind: "culture", glyph: "☾", approximate: true, days: 3,
    rule: { type: "table", dates: LUNAR_DATES.eidAlAdha }, message: "Eid al-Adha Mubarak!" },
];

/* ------------------------------------------------------------------ */
/* Date helpers (local calendar days, DST-safe)                         */
/* ------------------------------------------------------------------ */

interface Ymd {
  y: number;
  m: number;
  d: number;
}

function dayNumber({ y, m, d }: Ymd): number {
  return Math.round(Date.UTC(y, m - 1, d) / 86_400_000);
}

function ymdOf(date: Date): Ymd {
  return { y: date.getFullYear(), m: date.getMonth() + 1, d: date.getDate() };
}

function isLeap(y: number): boolean {
  return (y % 4 === 0 && y % 100 !== 0) || y % 400 === 0;
}

function daysInMonth(y: number, m: number): number {
  return [31, isLeap(y) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1];
}

function parseYmd(s: string): Ymd | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s);
  if (!m) return null;
  const v = { y: +m[1], m: +m[2], d: +m[3] };
  return v.m >= 1 && v.m <= 12 && v.d >= 1 && v.d <= daysInMonth(v.y, v.m) ? v : null;
}

/** The nth weekday of a month, e.g. the 2nd Tuesday of October. */
export function nthWeekday(y: number, month: number, weekday: number, n: number): Date {
  const first = new Date(y, month - 1, 1).getDay();
  return new Date(y, month - 1, 1 + ((weekday - first + 7) % 7) + (n - 1) * 7);
}

/** Day `n` of year `y` (1 January is day 1). */
export function dayOfYear(y: number, n: number): Date {
  return new Date(y, 0, n);
}

/** Start dates of a rule that could cover year `y`. */
function starts(rule: Rule, y: number): Ymd[] {
  switch (rule.type) {
    case "fixed":
      return rule.day <= daysInMonth(y, rule.month) ? [{ y, m: rule.month, d: rule.day }] : [];
    case "nth-weekday":
      return [ymdOf(nthWeekday(y, rule.month, rule.weekday, rule.n))];
    case "day-of-year":
      return [ymdOf(dayOfYear(y, rule.day))];
    case "table":
      return rule.dates.map(parseYmd).filter((v): v is Ymd => v !== null && (v.y === y || v.y === y - 1));
  }
}

function occurs(rule: Rule, days: number, date: Date): boolean {
  const today = ymdOf(date);
  const n = dayNumber(today);
  const years = rule.type === "table" ? [today.y] : days > 1 ? [today.y, today.y - 1] : [today.y];
  return years.some((y) =>
    starts(rule, y).some((s) => {
      const off = n - dayNumber(s);
      return off >= 0 && off < days;
    }),
  );
}

/* ------------------------------------------------------------------ */
/* Club events                                                          */
/* ------------------------------------------------------------------ */

function clubRule(date: string): { once: Ymd } | { yearly: { m: number; d: number } } | null {
  const s = date.trim();
  const full = parseYmd(s);
  if (full) return { once: full };
  const m = /^(\d{2})-(\d{2})$/.exec(s);
  if (!m) return null;
  const mm = +m[1];
  const dd = +m[2];
  // A leap year, so 02-29 is accepted (it then shows only in leap years).
  return mm >= 1 && mm <= 12 && dd >= 1 && dd <= daysInMonth(2024, mm) ? { yearly: { m: mm, d: dd } } : null;
}

/**
 * Validate configs.CLUB_EVENTS: an array (or its JSON string) of
 * { id, name, date: "MM-DD" | "YYYY-MM-DD", message }. Malformed entries are
 * dropped; ids are slugged so they are safe in attributes and storage keys.
 */
export function parseClubEvents(raw: unknown): ClubEvent[] {
  let v = raw;
  if (typeof v === "string") {
    try {
      v = JSON.parse(v);
    } catch {
      return [];
    }
  }
  if (!Array.isArray(v)) return [];
  const out: ClubEvent[] = [];
  for (const e of v) {
    if (!e || typeof e !== "object") continue;
    const { id, name, date, message } = e as Record<string, unknown>;
    if (typeof id !== "string" || typeof name !== "string" || typeof date !== "string") continue;
    const slug = id.trim().toLowerCase().replace(/[^a-z0-9_-]+/g, "-").replace(/^-+|-+$/g, "");
    if (!slug || !name.trim() || !clubRule(date)) continue;
    out.push({ id: slug, name: name.trim(), date: date.trim(), message: typeof message === "string" ? message.trim() : "" });
  }
  return out;
}

function clubOccurs(ev: ClubEvent, date: Date): boolean {
  const r = clubRule(ev.date);
  if (!r) return false;
  const t = ymdOf(date);
  if ("once" in r) return r.once.y === t.y && r.once.m === t.m && r.once.d === t.d;
  return r.yearly.m === t.m && r.yearly.d === t.d;
}

/* ------------------------------------------------------------------ */

/**
 * Events running on `date` (local time): club events first, then the
 * built-in calendar in table order (lunar festivals last).
 */
export function activeEvents(date: Date, clubEvents: ClubEvent[] = []): SeasonEvent[] {
  const out: SeasonEvent[] = [];
  const seen = new Set<string>();
  for (const ev of parseClubEvents(clubEvents)) {
    if (seen.has(ev.id) || !clubOccurs(ev, date)) continue;
    seen.add(ev.id);
    out.push({ id: ev.id, name: ev.name, message: ev.message, kind: "club" });
  }
  for (const { rule, days, ...ev } of CALENDAR) {
    if (seen.has(ev.id) || !occurs(rule, days ?? 1, date)) continue;
    seen.add(ev.id);
    out.push(ev);
  }
  return out;
}
