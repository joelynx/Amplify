/**
 * Procedural sfx packs: one recipe per cue, built from synth.ts. sfx.soft
 * covers every cue; the other packs give their character to the cues that
 * matter and fall back to sfx.soft for the rest (recipeFor). All melodies
 * are original.
 */

import { DEFAULT_PACK, lookupCue, type Cue, type PackTable } from "./cues";
import { BELL, bell, chord, hz, noise, pulse, run, tone, type Partials, type Voice } from "./synth";

export type Recipe = (v: Voice) => void;
type Pack = Partial<Record<Cue, Recipe>>;

/* ------------------------------------------------------------------ */
/* Soft (default): gentle sine blips                                    */
/* ------------------------------------------------------------------ */

const SOFT: Record<Cue, Recipe> = {
  click: (v) => tone(v, { f: 1250, to: 950, dur: 0.035, peak: 0.16, attack: 0.002 }),
  toggle: (v) => {
    tone(v, { f: 700, dur: 0.05, peak: 0.13 });
    tone(v, { f: 1050, at: 0.045, dur: 0.06, peak: 0.13 });
  },
  nav: (v) => tone(v, { f: 520, to: 640, dur: 0.07, peak: 0.12, attack: 0.006 }),
  correct: (v) => {
    tone(v, { f: hz(79), dur: 0.16, peak: 0.2 });
    tone(v, { f: hz(84), at: 0.09, dur: 0.38, peak: 0.22 });
    tone(v, { f: hz(96), at: 0.09, dur: 0.2, peak: 0.04 });
  },
  partial: (v) => {
    tone(v, { f: hz(76), dur: 0.16, peak: 0.18 });
    tone(v, { f: hz(79), at: 0.1, dur: 0.3, peak: 0.15 });
  },
  wrong: (v) => {
    tone(v, { f: hz(64), dur: 0.18, peak: 0.15, lp: 1200 });
    tone(v, { f: hz(60), at: 0.12, dur: 0.34, peak: 0.13, lp: 1000 });
  },
  combo: (v) => {
    tone(v, { f: hz(84), dur: 0.12, peak: 0.15 });
    tone(v, { f: hz(91), at: 0.05, dur: 0.16, peak: 0.09 });
  },
  hint: (v) => {
    tone(v, { f: 660, to: 990, dur: 0.14, peak: 0.11, attack: 0.01 });
    tone(v, { f: hz(88), at: 0.08, dur: 0.2, peak: 0.06 });
  },
  reveal: (v) => {
    noise(v, { kind: "pink", dur: 0.28, attack: 0.12, peak: 0.05, filter: "bandpass", f: 700, to: 2600, q: 1.2 });
    tone(v, { f: hz(76), at: 0.12, dur: 0.3, peak: 0.11 });
  },
  bookmark: (v) => {
    tone(v, { f: 880, to: 1320, dur: 0.08, peak: 0.12 });
    tone(v, { f: hz(88), at: 0.06, dur: 0.18, peak: 0.08 });
  },
  note: (v) => {
    tone(v, { f: hz(81), dur: 0.08, peak: 0.1 });
    tone(v, { f: hz(86), at: 0.06, dur: 0.14, peak: 0.08 });
  },
  session_start: (v) => run(v, [72, 76, 79], 0.08, { dur: 0.32, peak: 0.15 }),
  session_end: (v) => {
    run(v, [72, 76, 79, 84], 0.09, { dur: 0.35, peak: 0.15 });
    chord(v, [72, 76, 79, 84], { at: 0.38, dur: 1.3, attack: 0.03, peak: 0.06 });
    tone(v, { f: hz(96), at: 0.42, dur: 0.5, peak: 0.04 });
  },
  tick: (v) => tone(v, { f: 1600, dur: 0.03, peak: 0.1, attack: 0.001 }),
  time_up: (v) => {
    tone(v, { f: hz(76), dur: 0.35, peak: 0.15 });
    tone(v, { f: hz(72), at: 0.22, dur: 0.6, peak: 0.15 });
  },
  generate_done: (v) => run(v, [79, 84, 88], 0.07, { dur: 0.3, peak: 0.14 }),
  generate_error: (v) => {
    tone(v, { f: hz(67), dur: 0.2, peak: 0.13, type: "triangle", lp: 1400 });
    tone(v, { f: hz(62), at: 0.15, dur: 0.36, peak: 0.12, type: "triangle", lp: 1200 });
  },
  review_due: (v) => {
    bell(v, hz(84), { dur: 1.4, peak: 0.13 });
    bell(v, hz(91), { at: 0.18, dur: 1.2, peak: 0.07 });
  },
  unlock: (v) => {
    run(v, [84, 88, 91, 96], 0.06, { dur: 0.4, peak: 0.11 });
    noise(v, { at: 0.1, dur: 0.6, attack: 0.2, peak: 0.02, filter: "highpass", f: 6000 });
    bell(v, hz(96), { at: 0.26, dur: 1, peak: 0.06 });
  },
  egg: (v) => {
    run(v, [79, 81, 83, 86, 91], 0.05, { dur: 0.18, peak: 0.11, type: "triangle" });
    run(v, [91, 93, 91, 93, 95], 0.045, { at: 0.3, dur: 0.1, peak: 0.07 });
  },
  theme_switch: (v) => {
    noise(v, { kind: "pink", dur: 0.35, attack: 0.15, peak: 0.05, filter: "bandpass", f: 400, to: 2400, q: 1 });
    tone(v, { f: 500, to: 800, dur: 0.25, peak: 0.07, attack: 0.05 });
  },
};

/* ------------------------------------------------------------------ */
/* Chiptune: pulse and triangle bleeps                                  */
/* ------------------------------------------------------------------ */

const sq = (v: Voice, m: number, at: number, dur: number, peak: number, duty = 0.25) =>
  tone(v, { f: hz(m), at, dur, peak, wave: pulse(v.ac, duty), attack: 0.002, hold: dur * 0.55, lp: 5000 });
const tri = (v: Voice, m: number, at: number, dur: number, peak: number) =>
  tone(v, { f: hz(m), at, dur, peak, type: "triangle", attack: 0.002, hold: dur * 0.55 });
const sqRun = (v: Voice, notes: number[], step: number, dur: number, peak: number, at = 0, last = dur) =>
  notes.forEach((m, i) => sq(v, m, at + i * step, i === notes.length - 1 ? last : dur, peak));

const CHIPTUNE: Pack = {
  click: (v) => sq(v, 91, 0, 0.03, 0.06, 0.125),
  toggle: (v) => {
    sq(v, 84, 0, 0.035, 0.06);
    sq(v, 91, 0.035, 0.04, 0.06);
  },
  nav: (v) => tri(v, 79, 0, 0.05, 0.08),
  correct: (v) => sqRun(v, [84, 91, 96], 0.055, 0.06, 0.08, 0, 0.22),
  partial: (v) => sqRun(v, [84, 88], 0.07, 0.07, 0.07, 0, 0.18),
  wrong: (v) => tone(v, { f: 330, to: 196, dur: 0.28, type: "triangle", peak: 0.14, hold: 0.1 }),
  combo: (v) => sqRun(v, [88, 91, 96], 0.04, 0.05, 0.07, 0, 0.12),
  hint: (v) => tone(v, { f: 440, to: 1320, glide: 0.1, dur: 0.14, wave: pulse(v.ac, 0.25), peak: 0.06, hold: 0.06, lp: 5000 }),
  reveal: (v) => sqRun(v, [96, 91, 88, 84], 0.045, 0.06, 0.06),
  bookmark: (v) => {
    sq(v, 91, 0, 0.04, 0.06);
    sq(v, 96, 0.045, 0.1, 0.06);
  },
  note: (v) => {
    sq(v, 86, 0, 0.04, 0.05);
    sq(v, 89, 0.05, 0.06, 0.05);
  },
  session_start: (v) => {
    sqRun(v, [72, 76, 79, 84], 0.08, 0.09, 0.07, 0, 0.25);
    tri(v, 48, 0, 0.4, 0.12);
  },
  session_end: (v) => {
    sqRun(v, [67, 72, 76, 79, 84, 88], 0.1, 0.1, 0.07);
    tone(v, { f: hz(91), at: 0.62, dur: 0.55, peak: 0.07, wave: pulse(v.ac, 0.25), hold: 0.3, lp: 5000, vib: { rate: 6, depth: 15 } });
    tri(v, 48, 0, 0.3, 0.12);
    tri(v, 55, 0.3, 0.3, 0.12);
    tri(v, 60, 0.62, 0.6, 0.12);
  },
  tick: (v) => sq(v, 96, 0, 0.02, 0.05, 0.125),
  time_up: (v) => {
    tri(v, 76, 0, 0.16, 0.13);
    tri(v, 72, 0.14, 0.16, 0.13);
    tri(v, 69, 0.28, 0.4, 0.13);
  },
  generate_done: (v) => sqRun(v, [84, 88, 91, 96], 0.05, 0.06, 0.07, 0, 0.2),
  generate_error: (v) => tone(v, { f: hz(55), to: hz(50), type: "triangle", dur: 0.35, peak: 0.14, hold: 0.12 }),
  review_due: (v) => {
    sq(v, 88, 0, 0.1, 0.07);
    sq(v, 93, 0.11, 0.25, 0.07);
    sq(v, 88, 0.3, 0.08, 0.025);
    sq(v, 93, 0.4, 0.2, 0.025);
  },
  unlock: (v) => sqRun(v, [72, 76, 79, 84, 88, 91, 96], 0.035, 0.05, 0.06, 0, 0.3),
  egg: (v) => sqRun(v, [84, 88, 84, 88, 84, 88, 91, 96], 0.05, 0.055, 0.06, 0, 0.25),
  theme_switch: (v) => {
    tone(v, { f: 200, to: 1600, dur: 0.22, wave: pulse(v.ac, 0.25), peak: 0.05, hold: 0.1, lp: 4000 });
    noise(v, { dur: 0.2, peak: 0.03, filter: "highpass", f: 3000 });
  },
};

/* ------------------------------------------------------------------ */
/* Glass: bright chimes and bubbles                                     */
/* ------------------------------------------------------------------ */

const GLASS_PARTIALS: Partials = [
  [1, 1, 1],
  [2, 0.35, 0.6],
  [3, 0.14, 0.4],
  [4.2, 0.06, 0.25],
];
const glass = (v: Voice, m: number, at = 0, dur = 0.9, peak = 0.12) => {
  bell(v, hz(m), { at, dur, peak, partials: GLASS_PARTIALS });
  tone(v, { f: hz(m), detune: 6, at, dur: dur * 0.8, peak: peak * 0.3 });
};
const bubble = (v: Voice, at: number, from: number, to: number, peak: number) =>
  tone(v, { f: from, to, at, dur: 0.07, peak, attack: 0.003 });
const shimmer = (v: Voice, at: number, dur: number, peak = 0.015) =>
  noise(v, { at, dur, attack: dur * 0.35, peak, filter: "highpass", f: 7000 });

const GLASS: Pack = {
  click: (v) => {
    tone(v, { f: hz(100), dur: 0.05, peak: 0.07 });
    tone(v, { f: hz(107), dur: 0.03, peak: 0.02 });
  },
  toggle: (v) => {
    glass(v, 95, 0, 0.18, 0.07);
    glass(v, 100, 0.05, 0.2, 0.06);
  },
  nav: (v) => tone(v, { f: hz(95), dur: 0.1, peak: 0.05, attack: 0.01 }),
  correct: (v) => {
    glass(v, 88, 0, 0.9, 0.12);
    glass(v, 95, 0.08, 1.1, 0.12);
  },
  partial: (v) => {
    glass(v, 85, 0, 0.7, 0.1);
    glass(v, 88, 0.09, 0.8, 0.08);
  },
  wrong: (v) => {
    tone(v, { f: hz(76), dur: 0.3, peak: 0.12, lp: 1500 });
    tone(v, { f: hz(71), at: 0.12, dur: 0.45, peak: 0.1, lp: 1200 });
  },
  combo: (v) => glass(v, 95, 0, 0.5, 0.09),
  hint: (v) => {
    bubble(v, 0, 500, 1300, 0.1);
    bubble(v, 0.06, 700, 1700, 0.07);
  },
  reveal: (v) => [88, 92, 95].forEach((m, i) => glass(v, m, i * 0.07, 0.6, 0.08)),
  bookmark: (v) => bubble(v, 0, 600, 1500, 0.1),
  note: (v) => glass(v, 100, 0, 0.4, 0.06),
  session_start: (v) => [76, 83, 88].forEach((m, i) => glass(v, m, i * 0.1, 0.8, 0.09)),
  session_end: (v) => {
    [88, 92, 95, 100].forEach((m, i) => glass(v, m, i * 0.08, 1.2, 0.09));
    [76, 83, 88].forEach((m) => glass(v, m, 0.4, 1.6, 0.05));
    shimmer(v, 0.3, 1);
  },
  tick: (v) => tone(v, { f: hz(100), dur: 0.03, peak: 0.06 }),
  review_due: (v) => {
    glass(v, 88, 0, 1.4, 0.1);
    glass(v, 92, 0.12, 1.4, 0.07);
    glass(v, 95, 0.24, 1.6, 0.07);
  },
  unlock: (v) => {
    [88, 92, 95, 100, 104].forEach((m, i) => glass(v, m, i * 0.06, 0.9, 0.08));
    shimmer(v, 0.1, 0.9);
  },
  egg: (v) => {
    const pops: [number, number, number][] = [[0, 500, 1200], [0.08, 650, 1500], [0.15, 550, 1400], [0.24, 800, 1900], [0.3, 700, 1700]];
    for (const [at, a, b] of pops) bubble(v, at, a, b, 0.09);
  },
  theme_switch: (v) => {
    noise(v, { kind: "pink", dur: 0.4, attack: 0.18, peak: 0.04, filter: "bandpass", f: 600, to: 3000, q: 1 });
    glass(v, 95, 0.2, 0.6, 0.06);
  },
};

/* ------------------------------------------------------------------ */
/* Marimba: soft wooden mallets (F major pentatonic)                    */
/* ------------------------------------------------------------------ */

const mallet = (v: Voice, m: number, at = 0, peak = 0.2) => {
  const f = hz(m);
  const dur = Math.max(0.25, Math.min(0.7, 260 / f));
  tone(v, { f, at, dur, peak, attack: 0.002 });
  tone(v, { f: f * 3.93, at, dur: dur * 0.18, peak: peak * 0.25, attack: 0.001 });
  tone(v, { f: f * 9.2, at, dur: 0.03, peak: peak * 0.06, attack: 0.001 });
  noise(v, { at, dur: 0.012, peak: peak * 0.3, filter: "lowpass", f: 2500, attack: 0.001 });
};
const malletRun = (v: Voice, notes: number[], step: number, peak: number, at = 0) =>
  notes.forEach((m, i) => mallet(v, m, at + i * step, peak));

const MARIMBA: Pack = {
  click: (v) => mallet(v, 96, 0, 0.1),
  toggle: (v) => {
    mallet(v, 89, 0, 0.11);
    mallet(v, 93, 0.05, 0.1);
  },
  nav: (v) => mallet(v, 84, 0, 0.08),
  correct: (v) => malletRun(v, [81, 84, 89], 0.09, 0.19),
  partial: (v) => {
    mallet(v, 79, 0, 0.17);
    mallet(v, 81, 0.11, 0.14);
  },
  wrong: (v) => {
    mallet(v, 69, 0, 0.15);
    mallet(v, 65, 0.14, 0.14);
  },
  combo: (v) => mallet(v, 89, 0, 0.16),
  hint: (v) => {
    mallet(v, 88, 0, 0.12);
    mallet(v, 93, 0.07, 0.1);
  },
  reveal: (v) => malletRun(v, [77, 81, 84], 0.06, 0.12),
  bookmark: (v) => {
    mallet(v, 91, 0, 0.13);
    mallet(v, 96, 0.06, 0.1);
  },
  note: (v) => mallet(v, 93, 0, 0.11),
  session_start: (v) => malletRun(v, [77, 81, 84], 0.1, 0.17),
  session_end: (v) => {
    malletRun(v, [77, 81, 84, 89], 0.09, 0.16);
    malletRun(v, [65, 72, 77, 81], 0.03, 0.1, 0.45);
    malletRun(v, [89, 89, 89], 0.07, 0.07, 0.6);
  },
  tick: (v) => mallet(v, 96, 0, 0.09),
  time_up: (v) => {
    mallet(v, 84, 0, 0.16);
    mallet(v, 77, 0.18, 0.16);
  },
  generate_done: (v) => malletRun(v, [84, 89, 93], 0.07, 0.15),
  generate_error: (v) => {
    mallet(v, 67, 0, 0.14);
    mallet(v, 62, 0.15, 0.13);
  },
  review_due: (v) => malletRun(v, [84, 89, 93], 0.12, 0.14),
  unlock: (v) => malletRun(v, [77, 81, 84, 89, 93, 96], 0.05, 0.13),
  egg: (v) => malletRun(v, [84, 86, 89, 86, 89, 93, 96], 0.06, 0.12),
  theme_switch: (v) => malletRun(v, [72, 77, 81, 84], 0.035, 0.1),
};

/* ------------------------------------------------------------------ */
/* Keys: mechanical key clacks, typewriter bell                         */
/* ------------------------------------------------------------------ */

const clack = (v: Voice, at = 0, peak = 0.2, bright = 1) => {
  noise(v, { at, dur: 0.018, peak, filter: "bandpass", f: 2800 * bright, q: 1.4, attack: 0.001 });
  noise(v, { kind: "brown", at: at + 0.002, dur: 0.035, peak: peak * 0.8, filter: "lowpass", f: 700, attack: 0.001 });
  tone(v, { f: 190 * bright, to: 110, at, dur: 0.04, peak: peak * 0.5, attack: 0.001 });
};
const TYPEWRITER_BELL: Partials = [
  [1, 1, 1],
  [2.01, 0.25, 0.5],
  [3.02, 0.1, 0.3],
  [4.6, 0.08, 0.2],
];
const ding = (v: Voice, at = 0, peak = 0.13, f = 1975) => bell(v, f, { at, dur: 1.1, peak, partials: TYPEWRITER_BELL });
const GAPS = [0.07, 0.055, 0.09, 0.06, 0.075, 0.05, 0.085, 0.065];
const typing = (v: Voice, n: number, at = 0, peak = 0.12) => {
  let t = at;
  for (let i = 0; i < n; i++) {
    clack(v, t, peak * (i % 3 === 1 ? 0.8 : 1), i % 2 ? 1.12 : 0.95);
    t += GAPS[i % GAPS.length];
  }
};
const ratchet = (v: Voice, at = 0, n = 12, step = 0.014, peak = 0.06) => {
  for (let i = 0; i < n; i++) noise(v, { at: at + i * step, dur: 0.006, peak, filter: "highpass", f: 3000 });
};
const thud = (v: Voice, at = 0, peak = 0.16) => {
  noise(v, { kind: "brown", at, dur: 0.12, peak, filter: "lowpass", f: 380, attack: 0.004 });
  tone(v, { f: 120, to: 80, at, dur: 0.14, peak: peak * 0.7 });
};

const KEYS: Pack = {
  click: (v) => clack(v, 0, 0.16),
  toggle: (v) => {
    clack(v, 0, 0.15);
    clack(v, 0.07, 0.08, 1.3);
  },
  nav: (v) => clack(v, 0, 0.08, 0.8),
  correct: (v) => {
    clack(v, 0, 0.1);
    ding(v, 0.03, 0.13);
  },
  partial: (v) => {
    clack(v, 0, 0.12);
    ding(v, 0.03, 0.07, 1480);
  },
  wrong: (v) => thud(v, 0, 0.15),
  combo: (v) => {
    clack(v, 0, 0.08);
    ding(v, 0.02, 0.07, 2349);
  },
  hint: (v) => {
    clack(v, 0, 0.1, 1.2);
    clack(v, 0.06, 0.1, 1.1);
  },
  reveal: (v) => typing(v, 5, 0, 0.1),
  bookmark: (v) => {
    clack(v, 0, 0.12, 0.9);
    clack(v, 0.05, 0.12, 1.2);
  },
  note: (v) => typing(v, 3, 0, 0.1),
  session_start: (v) => {
    ratchet(v, 0, 12);
    thud(v, 0.2, 0.12);
  },
  session_end: (v) => {
    typing(v, 4, 0, 0.1);
    ding(v, 0.35, 0.13);
    ding(v, 0.55, 0.1, 2349);
  },
  tick: (v) => clack(v, 0, 0.07, 1.2),
  time_up: (v) => {
    ding(v, 0, 0.13, 1480);
    ding(v, 0.25, 0.11, 1175);
  },
  generate_done: (v) => {
    typing(v, 6, 0, 0.09);
    ding(v, 0.45, 0.12);
  },
  generate_error: (v) => {
    thud(v, 0, 0.14);
    thud(v, 0.15, 0.12);
  },
  review_due: (v) => ding(v, 0, 0.12),
  unlock: (v) => {
    ratchet(v, 0, 10);
    ding(v, 0.15, 0.12);
    ding(v, 0.3, 0.1, 2637);
  },
  egg: (v) => {
    typing(v, 8, 0, 0.09);
    ding(v, 0.55, 0.12);
  },
  theme_switch: (v) => ratchet(v, 0, 14, 0.012, 0.05),
};

/* ------------------------------------------------------------------ */
/* Paper: pencil scratch, page turn, chalk tap                          */
/* ------------------------------------------------------------------ */

const scratch = (v: Voice, at: number, dur: number, peak = 0.06, f = 4200) =>
  noise(v, { at, dur, peak, filter: "bandpass", f, to: f * 1.15, q: 1.8, attack: dur * 0.3 });
const pageTurn = (v: Voice, at = 0, peak = 0.1) => {
  noise(v, { kind: "pink", at, dur: 0.32, attack: 0.14, peak, filter: "bandpass", f: 1200, to: 3800, q: 0.8 });
  noise(v, { kind: "brown", at: at + 0.24, dur: 0.1, peak: peak * 0.8, filter: "lowpass", f: 600 });
};
const chalk = (v: Voice, at = 0, peak = 0.13) => {
  noise(v, { at, dur: 0.02, peak, filter: "bandpass", f: 2600, q: 2.5, attack: 0.001 });
  tone(v, { f: 880, at, dur: 0.02, peak: peak * 0.35, attack: 0.001 });
};
const pencilTap = (v: Voice, at = 0, peak = 0.13) => {
  tone(v, { f: 620, to: 520, at, dur: 0.03, peak: peak * 0.6, attack: 0.001 });
  noise(v, { at, dur: 0.015, peak: peak * 0.5, filter: "bandpass", f: 1800, q: 1.2 });
};
const softNote = (v: Voice, m: number, at = 0, peak = 0.07, dur = 0.35) =>
  tone(v, { f: hz(m), at, dur, peak, type: "triangle", lp: 2000 });

const PAPER: Pack = {
  click: (v) => pencilTap(v, 0, 0.13),
  toggle: (v) => {
    pencilTap(v, 0, 0.12);
    pencilTap(v, 0.06, 0.1);
  },
  nav: (v) => noise(v, { kind: "pink", dur: 0.16, attack: 0.06, peak: 0.04, filter: "bandpass", f: 1500, to: 3000, q: 1 }),
  correct: (v) => {
    scratch(v, 0, 0.05, 0.06);
    scratch(v, 0.07, 0.12, 0.08, 4600);
    softNote(v, 84, 0.1, 0.07);
  },
  partial: (v) => {
    scratch(v, 0, 0.1, 0.06);
    softNote(v, 79, 0.08, 0.06);
  },
  wrong: (v) => {
    noise(v, { kind: "pink", dur: 0.22, attack: 0.06, peak: 0.05, filter: "bandpass", f: 900, q: 0.9 });
    noise(v, { kind: "pink", at: 0.2, dur: 0.12, attack: 0.04, peak: 0.04, filter: "bandpass", f: 850, q: 0.9 });
    softNote(v, 64, 0.1, 0.06, 0.3);
  },
  combo: (v) => {
    chalk(v, 0, 0.12);
    softNote(v, 88, 0.02, 0.05, 0.2);
  },
  hint: (v) => {
    pencilTap(v, 0, 0.12);
    pencilTap(v, 0.09, 0.12);
  },
  reveal: (v) => pageTurn(v, 0, 0.09),
  bookmark: (v) => {
    noise(v, { dur: 0.08, peak: 0.06, filter: "bandpass", f: 3000, q: 0.7 });
    noise(v, { at: 0.06, dur: 0.06, peak: 0.05, filter: "bandpass", f: 3400, q: 0.7 });
  },
  note: (v) => {
    scratch(v, 0, 0.07, 0.05);
    scratch(v, 0.09, 0.06, 0.05, 3800);
    scratch(v, 0.17, 0.09, 0.05, 4400);
  },
  session_start: (v) => pageTurn(v, 0, 0.1),
  session_end: (v) => {
    pageTurn(v, 0, 0.1);
    scratch(v, 0.4, 0.05, 0.06);
    scratch(v, 0.47, 0.14, 0.08, 4600);
    chord(v, [72, 76, 79], { at: 0.6, dur: 1, peak: 0.045, type: "triangle", lp: 2000, attack: 0.02 });
  },
  tick: (v) => chalk(v, 0, 0.08),
  time_up: (v) => {
    chalk(v, 0, 0.12);
    chalk(v, 0.12, 0.12);
    softNote(v, 72, 0.2, 0.07, 0.5);
  },
  generate_done: (v) => {
    pageTurn(v, 0, 0.08);
    softNote(v, 79, 0.3, 0.06);
    softNote(v, 84, 0.4, 0.06, 0.5);
  },
  theme_switch: (v) => pageTurn(v, 0, 0.08),
};

/* ------------------------------------------------------------------ */
/* Pop: comic whoosh, pop, boing                                        */
/* ------------------------------------------------------------------ */

const pop = (v: Voice, at = 0, peak = 0.18, f = 1100) => {
  tone(v, { f, to: f * 0.28, glide: 0.035, at, dur: 0.05, peak, attack: 0.001 });
  noise(v, { at, dur: 0.008, peak: peak * 0.4, filter: "highpass", f: 2500 });
};
const whoosh = (v: Voice, at = 0, dur = 0.35, peak = 0.08, up = true) =>
  noise(v, { kind: "pink", at, dur, attack: dur * 0.55, peak, filter: "bandpass", f: up ? 350 : 2600, to: up ? 2600 : 350, q: 1.6 });
const boing = (v: Voice, at = 0, peak = 0.13, f = 190) =>
  tone(v, { f, to: f * 1.9, glide: 0.12, at, dur: 0.45, peak, vib: { rate: 13, depth: 60 } });
const bloop = (v: Voice, at: number, from: number, to: number, peak: number) =>
  tone(v, { f: from, to, at, dur: 0.12, peak, attack: 0.004 });

const POP: Pack = {
  click: (v) => pop(v, 0, 0.13, 1000),
  toggle: (v) => {
    pop(v, 0, 0.11, 900);
    pop(v, 0.06, 0.11, 1300);
  },
  nav: (v) => whoosh(v, 0, 0.18, 0.035),
  correct: (v) => {
    pop(v, 0, 0.11);
    bloop(v, 0.04, 500, 1000, 0.13);
    tone(v, { f: hz(88), at: 0.12, dur: 0.25, peak: 0.07 });
  },
  partial: (v) => {
    bloop(v, 0, 500, 750, 0.11);
    pop(v, 0.1, 0.08);
  },
  wrong: (v) => tone(v, { f: 700, to: 330, dur: 0.38, peak: 0.09, vib: { rate: 5, depth: 20 }, attack: 0.02 }),
  combo: (v) => pop(v, 0, 0.12, 1300),
  hint: (v) => bloop(v, 0, 400, 1100, 0.11),
  reveal: (v) => whoosh(v, 0, 0.3, 0.08),
  bookmark: (v) => pop(v, 0, 0.13, 1200),
  note: (v) => {
    pop(v, 0, 0.1, 900);
    pop(v, 0.07, 0.08, 1200);
  },
  session_start: (v) => {
    whoosh(v, 0, 0.3, 0.07);
    pop(v, 0.28, 0.13);
  },
  session_end: (v) => {
    whoosh(v, 0, 0.32, 0.07);
    pop(v, 0.3, 0.12, 1000);
    pop(v, 0.4, 0.12, 1300);
    pop(v, 0.5, 0.12, 1600);
    boing(v, 0.62, 0.11);
  },
  tick: (v) => pop(v, 0, 0.07, 1500),
  time_up: (v) => boing(v, 0, 0.12, 160),
  generate_done: (v) => {
    pop(v, 0, 0.11, 1000);
    pop(v, 0.08, 0.11, 1250);
    pop(v, 0.16, 0.11, 1500);
  },
  generate_error: (v) => tone(v, { f: 520, to: 260, dur: 0.3, peak: 0.09, vib: { rate: 5, depth: 20 }, attack: 0.02 }),
  review_due: (v) => {
    bloop(v, 0, 450, 900, 0.11);
    pop(v, 0.14, 0.1, 1400);
  },
  unlock: (v) => {
    whoosh(v, 0, 0.3, 0.07);
    [1000, 1250, 1500, 1800].forEach((f, i) => pop(v, 0.25 + i * 0.07, 0.11, f));
  },
  egg: (v) => {
    boing(v, 0, 0.12);
    boing(v, 0.35, 0.1, 240);
  },
  theme_switch: (v) => whoosh(v, 0, 0.35, 0.08),
};

/* ------------------------------------------------------------------ */
/* Desktop 2001: soft pads and chimes (an original set)                 */
/* ------------------------------------------------------------------ */

const pad = (v: Voice, notes: number[], at = 0, dur = 1, peak = 0.03, attack = 0.08) => {
  for (const m of notes) {
    for (const detune of [-7, 7]) {
      tone(v, { f: hz(m), at, dur, peak, type: "sawtooth", detune, attack, hold: dur * 0.35, lp: 1600 });
    }
  }
};
const CHIME: Partials = [
  [1, 1, 1],
  [2, 0.3, 0.5],
  [3, 0.1, 0.3],
];
const chime = (v: Voice, m: number, at = 0, peak = 0.1, dur = 0.9) => bell(v, hz(m), { at, dur, peak, partials: CHIME });

const DESKTOP: Pack = {
  click: (v) => tone(v, { f: 1400, dur: 0.03, peak: 0.1, type: "triangle", lp: 3000 }),
  toggle: (v) => {
    tone(v, { f: hz(81), dur: 0.07, peak: 0.1 });
    tone(v, { f: hz(88), at: 0.05, dur: 0.1, peak: 0.1 });
  },
  nav: (v) => tone(v, { f: 300, to: 420, dur: 0.09, peak: 0.1, attack: 0.01 }),
  correct: (v) => {
    pad(v, [65, 69, 72, 76], 0, 0.7, 0.025, 0.02);
    chime(v, 84, 0, 0.1);
    chime(v, 91, 0.1, 0.1);
  },
  partial: (v) => {
    pad(v, [62, 69, 72, 76], 0, 0.6, 0.022);
    chime(v, 81, 0, 0.08);
  },
  wrong: (v) => {
    pad(v, [60, 67], 0, 0.6, 0.02);
    chime(v, 72, 0, 0.08, 0.6);
    chime(v, 67, 0.14, 0.08, 0.7);
  },
  combo: (v) => chime(v, 91, 0, 0.09, 0.6),
  hint: (v) => {
    tone(v, { f: 500, to: 900, dur: 0.15, peak: 0.07, attack: 0.02 });
    chime(v, 88, 0.1, 0.06);
  },
  reveal: (v) => {
    pad(v, [67, 74, 79], 0, 0.5, 0.02, 0.1);
    chime(v, 86, 0.06, 0.07);
  },
  bookmark: (v) => {
    chime(v, 86, 0, 0.08, 0.5);
    chime(v, 91, 0.07, 0.06, 0.5);
  },
  note: (v) => chime(v, 88, 0, 0.07, 0.4),
  session_start: (v) => {
    pad(v, [62, 69, 76, 78], 0, 1.4, 0.025, 0.25);
    [74, 81, 88].forEach((m, i) => chime(v, m, 0.1 + i * 0.14, 0.08, 1));
  },
  session_end: (v) => {
    pad(v, [67, 71, 74, 78], 0, 0.8, 0.025, 0.1);
    pad(v, [62, 69, 74, 76, 78], 0.7, 1.6, 0.022, 0.1);
    ([[86, 0], [83, 0.18], [88, 0.45], [90, 0.75]] as const).forEach(([m, at]) => chime(v, m, at, 0.08, 1.1));
  },
  tick: (v) => tone(v, { f: 1200, dur: 0.025, peak: 0.08, type: "triangle", lp: 2500 }),
  time_up: (v) => {
    chime(v, 79, 0, 0.1, 1);
    chime(v, 74, 0.3, 0.1, 1.2);
    pad(v, [62, 69], 0.3, 1, 0.018);
  },
  generate_done: (v) => {
    pad(v, [67, 71, 74], 0, 0.8, 0.02);
    [79, 83, 86].forEach((m, i) => chime(v, m, i * 0.1, 0.08));
  },
  generate_error: (v) => {
    pad(v, [52, 59], 0, 0.9, 0.02);
    chime(v, 69, 0, 0.09, 0.7);
    chime(v, 64, 0.2, 0.09, 0.9);
  },
  review_due: (v) => {
    pad(v, [60, 67, 76], 0, 1.2, 0.018, 0.2);
    chime(v, 84, 0, 0.1, 1.1);
    chime(v, 88, 0.15, 0.08, 1.2);
  },
  unlock: (v) => {
    pad(v, [65, 72, 76, 79], 0, 1.2, 0.025, 0.1);
    [84, 88, 91, 96].forEach((m, i) => chime(v, m, i * 0.08, 0.08));
  },
  egg: (v) => [86, 90, 93, 98].forEach((m, i) => chime(v, m, i * 0.07, 0.08, 0.7)),
  theme_switch: (v) => {
    pad(v, [62, 69, 74], 0, 0.6, 0.02, 0.2);
    noise(v, { kind: "pink", dur: 0.4, attack: 0.2, peak: 0.03, filter: "bandpass", f: 500, to: 2000, q: 1 });
  },
};

/* ------------------------------------------------------------------ */
/* Material: short clean taps                                           */
/* ------------------------------------------------------------------ */

const tap = (v: Voice, at = 0, f = 1800, peak = 0.13) => {
  tone(v, { f, at, dur: 0.018, peak, attack: 0.001 });
  noise(v, { at, dur: 0.006, peak: peak * 0.35, filter: "highpass", f: 3500 });
};

const MATERIAL: Pack = {
  click: (v) => tap(v),
  toggle: (v) => {
    tap(v, 0, 1400, 0.11);
    tap(v, 0.05, 2000, 0.1);
  },
  nav: (v) => tap(v, 0, 1200, 0.07),
  correct: (v) => {
    tone(v, { f: hz(84), dur: 0.09, peak: 0.15 });
    tone(v, { f: hz(91), at: 0.07, dur: 0.14, peak: 0.15 });
  },
  partial: (v) => {
    tone(v, { f: hz(84), dur: 0.09, peak: 0.13 });
    tone(v, { f: hz(86), at: 0.07, dur: 0.12, peak: 0.11 });
  },
  wrong: (v) => {
    tone(v, { f: hz(72), dur: 0.09, peak: 0.12 });
    tone(v, { f: hz(67), at: 0.08, dur: 0.16, peak: 0.11 });
  },
  combo: (v) => tap(v, 0, hz(96), 0.12),
  hint: (v) => {
    tap(v, 0, 1600, 0.1);
    tap(v, 0.05, 2100, 0.08);
  },
  bookmark: (v) => {
    tap(v, 0, 1900, 0.12);
    tap(v, 0.04, 2400, 0.08);
  },
  note: (v) => tap(v, 0, 2200, 0.1),
  tick: (v) => tap(v, 0, 2400, 0.08),
  session_start: (v) => run(v, [79, 84, 91], 0.06, { dur: 0.1, peak: 0.12 }),
  session_end: (v) => {
    run(v, [79, 84, 88, 91], 0.07, { dur: 0.14, peak: 0.12 });
    chord(v, [84, 91, 96], { at: 0.3, dur: 0.5, peak: 0.05 });
  },
  theme_switch: (v) => {
    tap(v, 0, 1200);
    tap(v, 0.04, 1600);
    tap(v, 0.08, 2000);
  },
};

/* ------------------------------------------------------------------ */
/* Chimes: celestial bells with a soft echo (D major, high)             */
/* ------------------------------------------------------------------ */

const cbell = (v: Voice, m: number, at = 0, peak = 0.1, dur = 1.6) => {
  bell(v, hz(m), { at, dur, peak, partials: BELL });
  bell(v, hz(m), { at: at + 0.19, dur: dur * 0.8, peak: peak * 0.28, pan: 0.4, partials: BELL.slice(0, 2) });
};
const cbellRun = (v: Voice, notes: number[], step: number, peak: number, at = 0, dur = 1.6) =>
  notes.forEach((m, i) => cbell(v, m, at + i * step, peak, dur));

const CHIMES: Pack = {
  click: (v) => {
    tone(v, { f: hz(98), dur: 0.12, peak: 0.05 });
    tone(v, { f: hz(98) * 2.76, dur: 0.05, peak: 0.012 });
  },
  toggle: (v) => {
    tone(v, { f: hz(93), dur: 0.15, peak: 0.05 });
    tone(v, { f: hz(98), at: 0.05, dur: 0.18, peak: 0.05 });
  },
  nav: (v) => tone(v, { f: hz(93), dur: 0.2, peak: 0.04, attack: 0.02 }),
  correct: (v) => {
    cbell(v, 86, 0, 0.1);
    cbell(v, 93, 0.1, 0.09);
  },
  partial: (v) => {
    cbell(v, 86, 0, 0.09, 1.2);
    tone(v, { f: hz(88), at: 0.1, dur: 0.4, peak: 0.04 });
  },
  wrong: (v) => {
    tone(v, { f: hz(74), dur: 0.5, peak: 0.1 });
    tone(v, { f: hz(69), at: 0.15, dur: 0.7, peak: 0.09 });
    tone(v, { f: hz(81), at: 0.15, dur: 0.3, peak: 0.02 });
  },
  combo: (v) => cbell(v, 93, 0, 0.08, 1),
  hint: (v) => {
    tone(v, { f: hz(98), dur: 0.3, peak: 0.05 });
    tone(v, { f: hz(105), at: 0.08, dur: 0.3, peak: 0.04 });
  },
  reveal: (v) => cbellRun(v, [86, 90, 93], 0.09, 0.07),
  bookmark: (v) => cbell(v, 98, 0, 0.06, 0.8),
  note: (v) => cbell(v, 95, 0, 0.05, 0.7),
  session_start: (v) => cbellRun(v, [86, 90, 93], 0.12, 0.08),
  session_end: (v) => {
    cbellRun(v, [86, 88, 90, 93, 95, 98], 0.09, 0.07);
    shimmer(v, 0.2, 1.2, 0.012);
  },
  tick: (v) => tone(v, { f: hz(98), dur: 0.06, peak: 0.05 }),
  time_up: (v) => {
    cbell(v, 81, 0, 0.09, 1.4);
    cbell(v, 74, 0.3, 0.09, 1.8);
  },
  generate_done: (v) => cbellRun(v, [86, 93, 98], 0.1, 0.07),
  review_due: (v) => {
    cbell(v, 86, 0, 0.09);
    cbell(v, 93, 0.16, 0.07);
  },
  unlock: (v) => {
    cbellRun(v, [86, 90, 93, 98, 102], 0.07, 0.07, 0, 1.4);
    shimmer(v, 0.1, 1.2, 0.012);
  },
  egg: (v) => cbellRun(v, [93, 98, 95, 100, 98, 105], 0.08, 0.06, 0, 1),
  theme_switch: (v) => {
    shimmer(v, 0, 0.6, 0.012);
    cbell(v, 93, 0.1, 0.06, 1);
  },
};

/* ------------------------------------------------------------------ */
/* Warm: woody thunks, crackly warm tones                               */
/* ------------------------------------------------------------------ */

const thunk = (v: Voice, at = 0, f = 180, peak = 0.18) => {
  tone(v, { f: f * 2, to: f, glide: 0.05, at, dur: 0.16, peak, attack: 0.002, lp: 900 });
  noise(v, { kind: "brown", at, dur: 0.05, peak: peak * 0.6, filter: "lowpass", f: 500 });
};
const crackle = (v: Voice, at = 0, n = 4, peak = 0.04) => {
  for (let i = 0; i < n; i++) {
    noise(v, { at: at + i * 0.037 + (i % 2) * 0.013, dur: 0.006, peak: peak * (i % 3 ? 0.6 : 1), filter: "highpass", f: 2400 });
  }
};
const warm = (v: Voice, m: number, at = 0, dur = 0.5, peak = 0.11) => {
  tone(v, { f: hz(m), at, dur, peak, type: "triangle", lp: 1500, attack: 0.01 });
  tone(v, { f: hz(m - 12), at, dur, peak: peak * 0.5, lp: 800, attack: 0.01 });
};

const WARM: Pack = {
  click: (v) => thunk(v, 0, 220, 0.14),
  toggle: (v) => {
    thunk(v, 0, 200, 0.12);
    thunk(v, 0.06, 260, 0.1);
  },
  nav: (v) => thunk(v, 0, 160, 0.09),
  correct: (v) => {
    warm(v, 72, 0, 0.35);
    warm(v, 79, 0.1, 0.6);
    crackle(v, 0.12, 3);
  },
  partial: (v) => {
    warm(v, 72, 0, 0.35, 0.1);
    warm(v, 74, 0.1, 0.45, 0.09);
  },
  wrong: (v) => {
    thunk(v, 0, 140, 0.13);
    warm(v, 60, 0.05, 0.5, 0.08);
  },
  combo: (v) => {
    warm(v, 79, 0, 0.3, 0.1);
    crackle(v, 0, 2, 0.03);
  },
  hint: (v) => {
    thunk(v, 0, 300, 0.1);
    warm(v, 84, 0.05, 0.3, 0.06);
  },
  reveal: (v) => [72, 76, 79].forEach((m, i) => warm(v, m, i * 0.07, 0.4, 0.08)),
  bookmark: (v) => {
    thunk(v, 0, 240, 0.13);
    thunk(v, 0.05, 320, 0.09);
  },
  note: (v) => {
    thunk(v, 0, 280, 0.11);
    crackle(v, 0.02, 2, 0.025);
  },
  session_start: (v) => {
    thunk(v, 0, 150, 0.13);
    [67, 72, 76].forEach((m, i) => warm(v, m, 0.05 + i * 0.09, 0.5, 0.09));
  },
  session_end: (v) => {
    [72, 76, 79, 84].forEach((m, i) => warm(v, m, i * 0.09, 0.5, 0.09));
    [60, 67, 72, 76].forEach((m) => warm(v, m, 0.36, 1.4, 0.05));
    crackle(v, 0.2, 8, 0.04);
  },
  tick: (v) => thunk(v, 0, 260, 0.08),
  time_up: (v) => {
    warm(v, 72, 0, 0.5);
    warm(v, 67, 0.25, 0.8);
  },
  generate_done: (v) => [72, 79, 84].forEach((m, i) => warm(v, m, i * 0.08, 0.45, 0.09)),
  generate_error: (v) => {
    thunk(v, 0, 150, 0.13);
    thunk(v, 0.15, 120, 0.12);
  },
  review_due: (v) => {
    warm(v, 79, 0, 0.6, 0.1);
    warm(v, 84, 0.15, 0.8, 0.08);
  },
  unlock: (v) => {
    [72, 76, 79, 84, 88].forEach((m, i) => warm(v, m, i * 0.06, 0.5, 0.08));
    crackle(v, 0.1, 6, 0.04);
  },
  egg: (v) => [200, 260, 200, 320].forEach((f, i) => thunk(v, i * 0.09, f, 0.11)),
  theme_switch: (v) => {
    crackle(v, 0, 6, 0.035);
    warm(v, 72, 0.05, 0.5, 0.07);
  },
};

/* ------------------------------------------------------------------ */

export const PACKS: PackTable<Recipe> = {
  [DEFAULT_PACK]: SOFT,
  "sfx.chiptune": CHIPTUNE,
  "sfx.glass": GLASS,
  "sfx.marimba": MARIMBA,
  "sfx.keys": KEYS,
  "sfx.paper": PAPER,
  "sfx.pop": POP,
  "sfx.desktop": DESKTOP,
  "sfx.material": MATERIAL,
  "sfx.chimes": CHIMES,
  "sfx.warm": WARM,
};

/** The recipe for a cue in a pack, falling back to sfx.soft (also for unknown packs). */
export function recipeFor(packId: string, cue: Cue): Recipe {
  return lookupCue(PACKS, packId, cue) ?? SOFT[cue];
}
