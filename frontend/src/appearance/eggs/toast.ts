/**
 * The easter-egg toast queue. EasterEggs renders it bottom centre; while
 * focus mode is on, toasts wait in the queue and appear once it ends.
 */

import { create } from "zustand";

export interface EggToast {
  id: number;
  text: string;
  /** "duck" draws the rubber duck; any other string is shown as a glyph. */
  icon?: string;
  /** A toast with the same key replaces the previous one. */
  key?: string;
}

const MAX_QUEUE = 6;

export const useEggToasts = create<{ items: EggToast[] }>(() => ({ items: [] }));

let seq = 0;

export function showToast(text: string, opts: { icon?: string; key?: string } = {}): void {
  const items = useEggToasts.getState().items;
  const kept = opts.key ? items.filter((t) => t.key !== opts.key) : items;
  const toast: EggToast = { id: ++seq, text, icon: opts.icon, key: opts.key };
  useEggToasts.setState({ items: [...kept, toast].slice(-MAX_QUEUE) });
}

export function dismissToast(id: number): void {
  useEggToasts.setState({ items: useEggToasts.getState().items.filter((t) => t.id !== id) });
}
