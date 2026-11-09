/**
 * Web Audio building blocks for the procedural sounds: shared noise buffers
 * and pulse waves (made once per context), enveloped tones, filtered noise
 * bursts and additive bells. Every one-shot disconnects its nodes when its
 * source ends, so nothing accumulates over a long session.
 */

/** Where and how one cue plays. */
export interface Voice {
  ac: AudioContext;
  out: AudioNode;
  /** Start time in AudioContext seconds. */
  t: number;
  /** Frequency multiplier (combo pitch). */
  pitch: number;
  /** Gain multiplier for the whole cue. */
  gain: number;
}

export type NoiseKind = "white" | "pink" | "brown";

/** MIDI note number to Hz (69 = A4 = 440 Hz). */
export const hz = (midi: number): number => 440 * 2 ** ((midi - 69) / 12);

export const rnd = (a: number, b: number): number => a + Math.random() * (b - a);

/* ------------------------------------------------------------------ */
/* Shared buffers                                                       */
/* ------------------------------------------------------------------ */

export const NOISE_SECONDS = 6;
const NOISE_RMS = 0.3;
const noiseCache = new WeakMap<BaseAudioContext, Map<NoiseKind, AudioBuffer>>();

function generate(kind: NoiseKind, n: number): Float32Array {
  const out = new Float32Array(n);
  if (kind === "white") {
    for (let i = 0; i < n; i++) out[i] = Math.random() * 2 - 1;
  } else if (kind === "pink") {
    // Paul Kellet's refined pink filter.
    let b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0, b6 = 0;
    for (let i = 0; i < n; i++) {
      const w = Math.random() * 2 - 1;
      b0 = 0.99886 * b0 + w * 0.0555179;
      b1 = 0.99332 * b1 + w * 0.0750759;
      b2 = 0.969 * b2 + w * 0.153852;
      b3 = 0.8665 * b3 + w * 0.3104856;
      b4 = 0.55 * b4 + w * 0.5329522;
      b5 = -0.7616 * b5 - w * 0.016898;
      out[i] = b0 + b1 + b2 + b3 + b4 + b5 + b6 + w * 0.5362;
      b6 = w * 0.115926;
    }
  } else {
    let last = 0;
    for (let i = 0; i < n; i++) {
      last = (last + 0.02 * (Math.random() * 2 - 1)) / 1.02;
      out[i] = last;
    }
  }
  return out;
}

/** A looping mono noise buffer, made once per context and kind. */
export function noiseBuffer(ac: BaseAudioContext, kind: NoiseKind): AudioBuffer {
  let byKind = noiseCache.get(ac);
  if (!byKind) {
    byKind = new Map();
    noiseCache.set(ac, byKind);
  }
  const hit = byKind.get(kind);
  if (hit) return hit;
  const len = Math.floor(ac.sampleRate * NOISE_SECONDS);
  const fade = Math.floor(ac.sampleRate * 0.05);
  const raw = generate(kind, len + fade);
  const buf = ac.createBuffer(1, len, ac.sampleRate);
  const d = buf.getChannelData(0);
  d.set(raw.subarray(0, len));
  // Blend the overhang into the head so the loop point has no seam.
  for (let i = 0; i < fade; i++) {
    const k = i / fade;
    d[i] = raw[i] * k + raw[len + i] * (1 - k);
  }
  let mean = 0;
  for (let i = 0; i < len; i++) mean += d[i];
  mean /= len;
  let sq = 0;
  for (let i = 0; i < len; i++) {
    d[i] -= mean;
    sq += d[i] * d[i];
  }
  const scale = NOISE_RMS / Math.max(1e-9, Math.sqrt(sq / len));
  for (let i = 0; i < len; i++) d[i] *= scale;
  byKind.set(kind, buf);
  return buf;
}

const waveCache = new WeakMap<BaseAudioContext, Map<number, PeriodicWave>>();

/** A band-limited pulse wave with the given duty cycle (0.125, 0.25, 0.5). */
export function pulse(ac: BaseAudioContext, duty: number): PeriodicWave {
  let byDuty = waveCache.get(ac);
  if (!byDuty) {
    byDuty = new Map();
    waveCache.set(ac, byDuty);
  }
  const hit = byDuty.get(duty);
  if (hit) return hit;
  const n = 32;
  const real = new Float32Array(n);
  const imag = new Float32Array(n);
  for (let k = 1; k < n; k++) {
    real[k] = Math.sin(2 * Math.PI * k * duty) / (Math.PI * k);
    imag[k] = (1 - Math.cos(2 * Math.PI * k * duty)) / (Math.PI * k);
  }
  const wave = ac.createPeriodicWave(real, imag);
  byDuty.set(duty, wave);
  return wave;
}

/* ------------------------------------------------------------------ */
/* One-shots                                                            */
/* ------------------------------------------------------------------ */

/** Attack, optional hold at the peak, then an exponential decay to silence by t0 + dur. */
function shape(p: AudioParam, t0: number, attack: number, hold: number, dur: number, peak: number): void {
  const a = Math.max(0.001, attack);
  const end = t0 + Math.max(a + hold + 0.005, dur);
  p.setValueAtTime(0, t0);
  p.linearRampToValueAtTime(peak, t0 + a);
  if (hold > 0) p.setValueAtTime(peak, t0 + a + hold);
  p.exponentialRampToValueAtTime(0.0001, end);
  p.setValueAtTime(0, end + 0.001);
}

/** Connect `from` to the voice output, through a stereo panner when asked. */
function toOut(v: Voice, from: AudioNode, pan: number | undefined, nodes: AudioNode[]): void {
  if (pan !== undefined && pan !== 0 && typeof v.ac.createStereoPanner === "function") {
    const p = v.ac.createStereoPanner();
    p.pan.value = Math.max(-1, Math.min(1, pan));
    from.connect(p);
    p.connect(v.out);
    nodes.push(p);
  } else {
    from.connect(v.out);
  }
}

function filters(ac: AudioContext, from: AudioNode, lp: number | undefined, hp: number | undefined, nodes: AudioNode[]): AudioNode {
  let tail = from;
  for (const [type, f] of [["lowpass", lp], ["highpass", hp]] as const) {
    if (!f) continue;
    const bq = ac.createBiquadFilter();
    bq.type = type;
    bq.frequency.value = Math.min(f, ac.sampleRate / 2 - 100);
    tail.connect(bq);
    nodes.push(bq);
    tail = bq;
  }
  return tail;
}

function cleanup(src: AudioScheduledSourceNode, nodes: AudioNode[]): void {
  src.onended = () => {
    for (const n of nodes) n.disconnect();
  };
}

export interface ToneOpts {
  /** Hz, before the voice's pitch multiplier. */
  f: number;
  /** Seconds after the voice start. */
  at?: number;
  /** Total length including the decay. */
  dur: number;
  type?: OscillatorType;
  wave?: PeriodicWave;
  attack?: number;
  /** Seconds held at the peak before decaying. */
  hold?: number;
  peak?: number;
  /** Glide to this frequency over `glide` seconds (default: the whole note). */
  to?: number;
  glide?: number;
  /** Cents. */
  detune?: number;
  /** Vibrato: rate in Hz, depth in cents. */
  vib?: { rate: number; depth: number };
  lp?: number;
  hp?: number;
  pan?: number;
}

export function tone(v: Voice, o: ToneOpts): void {
  const { ac } = v;
  const nyquist = ac.sampleRate / 2;
  const f = o.f * v.pitch;
  if (f <= 0 || f > nyquist * 0.9) return;
  const t0 = v.t + (o.at ?? 0);
  const stopAt = t0 + o.dur + 0.05;
  const osc = ac.createOscillator();
  if (o.wave) osc.setPeriodicWave(o.wave);
  else osc.type = o.type ?? "sine";
  osc.frequency.setValueAtTime(f, t0);
  if (o.to) osc.frequency.exponentialRampToValueAtTime(Math.min(o.to * v.pitch, nyquist * 0.9), t0 + (o.glide ?? o.dur));
  if (o.detune) osc.detune.value = o.detune;
  const nodes: AudioNode[] = [osc];
  if (o.vib) {
    const lfo = ac.createOscillator();
    lfo.frequency.value = o.vib.rate;
    const depth = ac.createGain();
    depth.gain.value = o.vib.depth;
    lfo.connect(depth);
    depth.connect(osc.detune);
    lfo.start(t0);
    lfo.stop(stopAt);
    nodes.push(lfo, depth);
  }
  const env = ac.createGain();
  shape(env.gain, t0, o.attack ?? 0.004, o.hold ?? 0, o.dur, (o.peak ?? 0.3) * v.gain);
  filters(ac, osc, o.lp, o.hp, nodes).connect(env);
  nodes.push(env);
  toOut(v, env, o.pan, nodes);
  osc.start(t0);
  osc.stop(stopAt);
  cleanup(osc, nodes);
}

export interface NoiseOpts {
  kind?: NoiseKind;
  at?: number;
  dur: number;
  attack?: number;
  hold?: number;
  peak?: number;
  /** Main filter; its frequency follows the voice pitch. */
  filter?: BiquadFilterType;
  f?: number;
  q?: number;
  /** Sweep the main filter to this frequency over the burst. */
  to?: number;
  pan?: number;
}

/**
 * A filtered noise burst. Narrow band-passes on white and pink noise are
 * compensated so `peak` lands near the level of a tone with the same peak.
 */
export function noise(v: Voice, o: NoiseOpts): void {
  const { ac } = v;
  const kind = o.kind ?? "white";
  const t0 = v.t + (o.at ?? 0);
  const src = ac.createBufferSource();
  src.buffer = noiseBuffer(ac, kind);
  src.loop = true;
  const nodes: AudioNode[] = [src];
  let tail: AudioNode = src;
  let comp = 1;
  if (o.filter) {
    const nyquist = ac.sampleRate / 2 - 100;
    const f = Math.min((o.f ?? 1000) * v.pitch, nyquist);
    const q = o.q ?? 1;
    const bq = ac.createBiquadFilter();
    bq.type = o.filter;
    bq.frequency.setValueAtTime(f, t0);
    if (o.to) bq.frequency.exponentialRampToValueAtTime(Math.min(o.to * v.pitch, nyquist), t0 + o.dur);
    bq.Q.value = q;
    src.connect(bq);
    nodes.push(bq);
    tail = bq;
    if (o.filter === "bandpass") {
      const share = kind === "white" ? f / q / nyquist : kind === "pink" ? 0.144 / q : 1;
      comp = Math.max(1, Math.min(6, 1 / Math.sqrt(share)));
    }
  }
  const env = ac.createGain();
  shape(env.gain, t0, o.attack ?? 0.002, o.hold ?? 0, o.dur, (o.peak ?? 0.2) * v.gain * comp);
  tail.connect(env);
  nodes.push(env);
  toOut(v, env, o.pan, nodes);
  src.start(t0, Math.random() * (NOISE_SECONDS - 1));
  src.stop(t0 + o.dur + 0.03);
  cleanup(src, nodes);
}

/** Partials as [frequency ratio, relative amplitude, relative decay]. */
export type Partials = [ratio: number, amp: number, decay: number][];

/** Inharmonic struck-bell partials. */
export const BELL: Partials = [
  [1, 1, 1],
  [2.76, 0.4, 0.45],
  [5.4, 0.2, 0.25],
  [8.93, 0.08, 0.15],
];

export interface BellOpts {
  at?: number;
  dur?: number;
  peak?: number;
  partials?: Partials;
  pan?: number;
}

/** An additive bell or chime: one decaying sine per partial. */
export function bell(v: Voice, f: number, o: BellOpts = {}): void {
  const dur = o.dur ?? 1;
  const peak = o.peak ?? 0.15;
  for (const [ratio, amp, decay] of o.partials ?? BELL) {
    tone(v, { f: f * ratio, at: o.at, dur: Math.max(0.03, dur * decay), peak: peak * amp, attack: 0.002, pan: o.pan });
  }
}

/** Play `notes` (MIDI) one after another, `step` seconds apart. */
export function run(v: Voice, notes: number[], step: number, o: Omit<ToneOpts, "f"> = { dur: 0.2 }): void {
  notes.forEach((m, i) => tone(v, { ...o, f: hz(m), at: (o.at ?? 0) + i * step }));
}

/** Play `notes` (MIDI) together. */
export function chord(v: Voice, notes: number[], o: Omit<ToneOpts, "f"> = { dur: 0.6 }): void {
  for (const m of notes) tone(v, { ...o, f: hz(m) });
}
