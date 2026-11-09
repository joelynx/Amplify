/**
 * Recording a found egg: adds the secret to the store and emits an `egg`
 * event the first time. Waits for the store to load, so an early find can
 * never overwrite configs.EASTER_EGGS with a one-item list.
 */

import { emit } from "../events";
import { useAppearance } from "../store";

/** Run `fn` once the appearance store has loaded the saved secrets. */
export function whenReady(fn: () => void): void {
  if (useAppearance.getState().ready) {
    fn();
    return;
  }
  const unsub = useAppearance.subscribe((s) => {
    if (!s.ready) return;
    unsub();
    fn();
  });
}

/** Mark egg `id` as found. No-op when eggs are off or it was already found. */
export function findEgg(id: string): void {
  whenReady(() => {
    const st = useAppearance.getState();
    if (!st.settings.eggs || st.secrets.has(id)) return;
    st.addSecret(id);
    emit({ type: "egg", id });
  });
}

export function eggFound(id: string): boolean {
  return useAppearance.getState().secrets.has(id);
}
