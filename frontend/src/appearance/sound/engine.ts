/**
 * Sound engine (Makeover.md §5.7). Web Audio, created on the first user
 * gesture (autoplay policy). App events become cues (cues.ts) played from
 * the active sfx pack: its audio files when it has them, else the procedural
 * recipes. Levels come from the mixer via channelGain(), read at play time
 * and followed live.
 */

import { on, type AppEvent } from "../events";
import { getItem, resolve } from "../registry";
import { channelGain, useAppearance, type SoundChannel } from "../store";
import type { Item } from "../types";
import { PREVIEW_CUES, PREVIEW_SECONDS, cueGate, cuesFor, fileFor, recipePack, type CueRequest } from "./cues";
import { recipeFor } from "./recipes";

const CHANNELS: SoundChannel[] = ["ui", "feedback", "celebration"];
/** Suspend the context after this long with nothing playing. */
const IDLE_MS = 15_000;
/** A review_due chime that arrives before any gesture waits this long for one. */
const DEFER_MS = 60_000;

let ac: AudioContext | null = null;
const buses = new Map<SoundChannel, GainNode>();
const busLevel = new Map<SoundChannel, number>();
let gestured = false;
let idleTimer: ReturnType<typeof setTimeout> | null = null;
/** Active-pack UI sounds stay quiet until then (performance.now()), during an sfx preview. */
let quietUntil = 0;
let deferred: { req: CueRequest; at: number } | null = null;

/* ------------------------------------------------------------------ */
/* Context and mixer                                                    */
/* ------------------------------------------------------------------ */

function hasGesture(): boolean {
  if (gestured) return true;
  const ua = (navigator as Navigator & { userActivation?: { hasBeenActive: boolean } }).userActivation;
  return !!ua?.hasBeenActive;
}

/** The AudioContext, created lazily once the user has interacted. */
function context(): AudioContext | null {
  if (ac) return ac.state === "closed" ? null : ac;
  if (!hasGesture() || typeof window === "undefined") return null;
  const Ctor = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!Ctor) return null;
  try {
    ac = new Ctor({ latencyHint: "interactive" });
  } catch {
    return null;
  }
  // Master: fixed headroom into a gentle limiter, so stacked cues never clip.
  const master = ac.createGain();
  master.gain.value = 0.9;
  const limiter = ac.createDynamicsCompressor();
  limiter.threshold.value = -10;
  limiter.knee.value = 6;
  limiter.ratio.value = 12;
  limiter.attack.value = 0.003;
  limiter.release.value = 0.2;
  master.connect(limiter);
  limiter.connect(ac.destination);
  for (const ch of CHANNELS) {
    const bus = ac.createGain();
    const g = channelGain(ch);
    bus.gain.value = g;
    busLevel.set(ch, g);
    bus.connect(master);
    buses.set(ch, bus);
  }
  scheduleIdle();
  return ac;
}

/** Make sure the context runs (resume after idle) and push back the idle suspend. */
function wake(c: AudioContext): void {
  if (c.state === "suspended" && !document.hidden) void c.resume().catch(() => {});
  scheduleIdle();
}

function scheduleIdle(): void {
  if (idleTimer) clearTimeout(idleTimer);
  idleTimer = setTimeout(() => {
    idleTimer = null;
    if (ac && ac.state === "running") void ac.suspend().catch(() => {});
  }, IDLE_MS);
}

/** Follow the mixer: channelGain() already folds in master, mute and focus. */
function levels(): void {
  if (!ac) return;
  for (const ch of CHANNELS) {
    const g = channelGain(ch);
    if (busLevel.get(ch) === g) continue;
    busLevel.set(ch, g);
    buses.get(ch)?.gain.setTargetAtTime(g, ac.currentTime, 0.03);
  }
}

/* ------------------------------------------------------------------ */
/* Cues                                                                 */
/* ------------------------------------------------------------------ */

const badFiles = new Set<string>();
const fileCache = new Map<string, HTMLAudioElement>();

function mediaFailed(url: string, err: unknown): void {
  const name = (err as { name?: string } | null)?.name;
  if (name !== "NotAllowedError" && name !== "AbortError") badFiles.add(url);
}

/** Play a pack's own file through an <audio> element (fetching file:// URLs fails in WebView2). */
function playFile(url: string, volume: number, rate: number, delayS: number, fallback: () => void): void {
  const go = () => {
    let el = fileCache.get(url);
    if (!el || !el.paused) {
      el = new Audio(url);
      el.preload = "auto";
      if (!fileCache.has(url)) fileCache.set(url, el);
    }
    el.volume = Math.max(0, Math.min(1, volume));
    el.playbackRate = rate;
    (el as HTMLAudioElement & { preservesPitch?: boolean }).preservesPitch = false;
    el.currentTime = 0;
    el.play().catch((err: unknown) => {
      mediaFailed(url, err);
      fallback();
    });
  };
  if (delayS > 0) setTimeout(go, delayS * 1000);
  else go();
}

function play(req: CueRequest, item: Item | undefined, extraDelay = 0): void {
  const level = channelGain(req.channel);
  if (level <= 0 || typeof document === "undefined" || document.hidden) return;
  const c = context();
  if (!c) {
    if (req.cue === "review_due") deferred = { req, at: performance.now() };
    return;
  }
  const bus = buses.get(req.channel);
  if (!bus) return;
  wake(c);
  levels();
  const pitch = 2 ** ((req.semitones ?? 0) / 12);
  const gain = req.gain ?? 1;
  const delay = (req.delay ?? 0) + extraDelay;
  const recipe = recipeFor(recipePack(item), req.cue);
  const synth = (afterS: number) => {
    try {
      recipe({ ac: c, out: bus, t: c.currentTime + afterS + 0.005, pitch, gain });
    } catch (err) {
      console.warn("sound recipe failed", req.cue, err);
    }
  };
  const url = fileFor(item?.data?.files, req.cue);
  if (url && !badFiles.has(url)) playFile(url, level * gain, pitch, delay, () => synth(0));
  else synth(delay);
}

function activePack(): Item | undefined {
  return resolve(useAppearance.getState().loadout, "sfx");
}

/* ------------------------------------------------------------------ */
/* Public API                                                           */
/* ------------------------------------------------------------------ */

let installed: (() => void) | null = null;

/** Start listening to app events and following the loadout. Returns the uninstall function. */
export function installSound(): () => void {
  if (installed) return installed;
  const gate = cueGate();

  const onEvent = (e: AppEvent) => {
    const reqs = cuesFor(e);
    if (!reqs.length) return;
    const item = activePack();
    const now = performance.now();
    for (const r of reqs) {
      if (r.channel === "ui" && now < quietUntil) continue;
      if (channelGain(r.channel) <= 0 || !gate(r.cue, now)) continue;
      play(r, item);
    }
  };

  const onGesture = () => {
    gestured = true;
    if (!context()) return;
    if (deferred) {
      const d = deferred;
      deferred = null;
      if (performance.now() - d.at < DEFER_MS) play(d.req, activePack(), 0.15);
    }
  };

  const onVisibility = () => {
    if (document.hidden && ac?.state === "running") void ac.suspend().catch(() => {});
  };

  const offEvents = on("*", onEvent);
  const offStore = useAppearance.subscribe(levels);
  window.addEventListener("pointerdown", onGesture, true);
  window.addEventListener("keydown", onGesture, true);
  document.addEventListener("visibilitychange", onVisibility);

  const uninstall = () => {
    offEvents();
    offStore();
    window.removeEventListener("pointerdown", onGesture, true);
    window.removeEventListener("keydown", onGesture, true);
    document.removeEventListener("visibilitychange", onVisibility);
    scheduleIdle();
    installed = null;
  };
  installed = uninstall;
  return uninstall;
}

/** Play a short tour of an sfx pack (click, correct, partial, wrong, session end) at the user's volumes. */
export function previewSfx(itemId: string): void {
  const item = getItem(itemId);
  if (!item || item.slot !== "sfx") return;
  quietUntil = performance.now() + PREVIEW_SECONDS * 1000;
  for (const r of PREVIEW_CUES) play(r, item);
}
