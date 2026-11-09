/**
 * A minimal stand-in for the Web Audio API (jsdom has none). It records every
 * node, rejects the values real Web Audio rejects (non-finite numbers,
 * exponential ramps to zero or below), and lets tests end sources so they can
 * check that every node was disconnected afterwards.
 */

function finite(...xs: number[]): void {
  for (const x of xs) if (!Number.isFinite(x)) throw new TypeError(`non-finite value ${x}`);
}

export class FakeParam {
  value: number;
  constructor(value = 0) {
    this.value = value;
  }
  setValueAtTime(v: number, t: number) {
    finite(v, t);
    this.value = v;
    return this;
  }
  linearRampToValueAtTime(v: number, t: number) {
    finite(v, t);
    return this;
  }
  exponentialRampToValueAtTime(v: number, t: number) {
    finite(v, t);
    if (v <= 0) throw new RangeError("exponential ramp target must be positive");
    return this;
  }
  setTargetAtTime(v: number, t: number, c: number) {
    finite(v, t, c);
    return this;
  }
  cancelScheduledValues(t: number) {
    finite(t);
    return this;
  }
  cancelAndHoldAtTime(t: number) {
    finite(t);
    return this;
  }
}

export class FakeNode {
  readonly ctx: FakeContext;
  outputs = new Set<unknown>();
  constructor(ctx: FakeContext) {
    this.ctx = ctx;
    ctx.nodes.push(this);
  }
  connect<T>(target: T): T {
    if (!target) throw new TypeError("connect to nothing");
    this.outputs.add(target);
    return target;
  }
  disconnect() {
    this.outputs.clear();
  }
}

class FakeSource extends FakeNode {
  onended: (() => void) | null = null;
  started = false;
  stopped = false;
  constructor(ctx: FakeContext) {
    super(ctx);
    ctx.sources.push(this);
  }
  start(t = 0, offset = 0) {
    finite(t, offset);
    if (this.started) throw new Error("started twice");
    this.started = true;
  }
  stop(t = 0) {
    finite(t);
    if (!this.started) throw new Error("stop before start");
    this.stopped = true;
  }
}

class FakeOscillator extends FakeSource {
  type = "sine";
  frequency = new FakeParam(440);
  detune = new FakeParam(0);
  setPeriodicWave() {}
}

class FakeBufferSource extends FakeSource {
  buffer: unknown = null;
  loop = false;
}

class FakeGain extends FakeNode {
  gain = new FakeParam(1);
}

class FakeFilter extends FakeNode {
  type = "lowpass";
  frequency = new FakeParam(350);
  Q = new FakeParam(1);
}

class FakePanner extends FakeNode {
  pan = new FakeParam(0);
}

class FakeDelay extends FakeNode {
  delayTime = new FakeParam(0);
}

export class FakeContext {
  sampleRate = 48000;
  currentTime = 0;
  state = "running";
  nodes: FakeNode[] = [];
  sources: FakeSource[] = [];
  destination: FakeNode;
  constructor() {
    this.destination = new FakeNode(this);
  }
  createOscillator() {
    return new FakeOscillator(this);
  }
  createBufferSource() {
    return new FakeBufferSource(this);
  }
  createGain() {
    return new FakeGain(this);
  }
  createBiquadFilter() {
    return new FakeFilter(this);
  }
  createStereoPanner() {
    return new FakePanner(this);
  }
  createDelay() {
    return new FakeDelay(this);
  }
  createPeriodicWave(real: Float32Array, imag: Float32Array) {
    for (const x of [...real, ...imag]) finite(x);
    return {};
  }
  createBuffer(_channels: number, length: number, sampleRate: number) {
    const data = new Float32Array(length);
    return { duration: length / sampleRate, getChannelData: () => data };
  }
  /** Fire onended on every source that was started (as the audio thread would once they stop). */
  endAll() {
    for (const s of this.sources) if (s.started) s.onended?.();
  }
  /** Nodes other than `except` that still have outputs. */
  connected(except: FakeNode[] = []): FakeNode[] {
    return this.nodes.filter((n) => !except.includes(n) && n.outputs.size > 0);
  }
}

/** The fake, typed as the real thing for code under test. */
export function fakeAudio(): { fake: FakeContext; ac: AudioContext; out: AudioNode; outNode: FakeNode } {
  const fake = new FakeContext();
  const outNode = new FakeGain(fake);
  outNode.connect(fake.destination);
  return { fake, ac: fake as unknown as AudioContext, out: outNode as unknown as AudioNode, outNode };
}
