/**
 * Pure detectors behind the global easter eggs (Makeover.md §6): key
 * sequences, click bursts, clock times, note endings and the bouncing
 * screensaver's physics. No DOM and no store, so they are unit-tested.
 */

export const KONAMI = [
  "arrowup", "arrowup", "arrowdown", "arrowdown",
  "arrowleft", "arrowright", "arrowleft", "arrowright",
  "b", "a",
] as const;

/**
 * Feed keys one at a time; returns true on the key that completes `seq`.
 * Keys are compared case-insensitively. Keeps only the last `seq.length`
 * keys, so overlapping starts (↑↑↑↓↓…) still match.
 */
export function createSequenceDetector(seq: readonly string[]): (key: string) => boolean {
  const want = seq.map((k) => k.toLowerCase());
  let buf: string[] = [];
  return (key) => {
    buf.push(key.toLowerCase());
    if (buf.length > want.length) buf = buf.slice(-want.length);
    if (buf.length === want.length && buf.every((k, i) => k === want[i])) {
      buf = [];
      return true;
    }
    return false;
  };
}

export function createKonamiDetector(): (key: string) => boolean {
  return createSequenceDetector(KONAMI);
}

/**
 * Detects a word typed anywhere. Only printable single-character keys count;
 * modifiers and navigation keys are ignored rather than resetting the buffer.
 */
export function createWordDetector(word: string): (key: string) => boolean {
  const detect = createSequenceDetector([...word.toLowerCase()]);
  return (key) => key.length === 1 && detect(key);
}

/**
 * True on the event that makes `n` events within `windowMs`. The count then
 * restarts. `t` is a timestamp in ms. `count()` reports the current run.
 */
export function createBurstCounter(n: number, windowMs: number) {
  let times: number[] = [];
  return {
    hit(t: number): boolean {
      times = times.filter((x) => t - x < windowMs);
      times.push(t);
      if (times.length >= n) {
        times = [];
        return true;
      }
      return false;
    },
    count(): number {
      return times.length;
    },
  };
}

/** Clock eggs for an answer at local time `d`. */
export function timeEgg(d: Date): "pi-time" | "leet" | null {
  const h = d.getHours();
  const m = d.getMinutes();
  if ((h === 3 || h === 15) && m === 14) return "pi-time";
  if (h === 13 && m === 37) return "leet";
  return null;
}

/** A self-explanation that ends the way a proof should: "QED", "Q.E.D." or "∎". */
export function endsWithQed(text: string): boolean {
  const t = text.trim();
  return t.endsWith("∎") || /(?:^|[^\p{L}\p{N}])(?:qed|q\.e\.d\.?)$/iu.test(t);
}

/** Fermat's margin: the note is full. */
export function fillsMargin(text: string, limit: number): boolean {
  return limit > 0 && text.length >= limit;
}

/** "After 2 am": 02:00 to 04:59 local. */
export function isLateNight(d: Date): boolean {
  const h = d.getHours();
  return h >= 2 && h < 5;
}

/* ------------------------------------------------------------------ */
/* Screensaver physics                                                  */
/* ------------------------------------------------------------------ */

export interface Bouncer {
  x: number;
  y: number;
  /** Velocity in px/s. */
  vx: number;
  vy: number;
}

export interface BounceStep {
  next: Bouncer;
  hitX: boolean;
  hitY: boolean;
  /** Both walls at once, within `tol` px: the famous corner hit. */
  corner: boolean;
}

/**
 * Advance a box of size w×h inside W×H by `dt` seconds, reflecting off the
 * walls. A corner counts when one axis hits a wall while the other is within
 * `tol` px of a wall.
 */
export function stepBounce(b: Bouncer, dt: number, w: number, h: number, W: number, H: number, tol = 3): BounceStep {
  const maxX = Math.max(0, W - w);
  const maxY = Math.max(0, H - h);
  let { x, y, vx, vy } = b;
  x += vx * dt;
  y += vy * dt;
  let hitX = false;
  let hitY = false;
  if (x <= 0) {
    x = -x;
    vx = Math.abs(vx);
    hitX = true;
  } else if (x >= maxX) {
    x = 2 * maxX - x;
    vx = -Math.abs(vx);
    hitX = true;
  }
  if (y <= 0) {
    y = -y;
    vy = Math.abs(vy);
    hitY = true;
  } else if (y >= maxY) {
    y = 2 * maxY - y;
    vy = -Math.abs(vy);
    hitY = true;
  }
  x = Math.min(Math.max(x, 0), maxX);
  y = Math.min(Math.max(y, 0), maxY);
  const nearX = x <= tol || x >= maxX - tol;
  const nearY = y <= tol || y >= maxY - tol;
  const corner = (hitX && nearY) || (hitY && nearX);
  return { next: { x, y, vx, vy }, hitX, hitY, corner };
}
