/**
 * Pure helpers for the TagTray's Compulsory / Exclude toggle state.
 *
 * Spec §8.1 cascade rules:
 *   - Adding a chip while Exclude is on forces Compulsory on. Equivalently:
 *     turning Exclude on flips Compulsory on too.
 *   - Turning Compulsory off while Exclude is on also turns Exclude off.
 *
 * Truth table for the chip category at add time (after the cascades have
 * already normalized the toggle state):
 *
 *   compulsory | exclude | category
 *   --------------------------------
 *   false      | false   | "optional"
 *   true       | false   | "compulsory"
 *   true       | true    | "excluded"
 *   false      | true    | unreachable — cascadeOnExcludeChange normalizes to (true, true)
 */

import type { TagCategory } from "../../state/generate";

export interface ToggleState {
  compulsory: boolean;
  exclude: boolean;
}

export function categoryFromToggles(state: ToggleState): TagCategory {
  if (state.exclude) return "excluded";
  if (state.compulsory) return "compulsory";
  return "optional";
}

/** New state after the user changes the Compulsory toggle. */
export function cascadeOnCompulsoryChange(prev: ToggleState, next: boolean): ToggleState {
  // Turning Compulsory off while Exclude is on also turns Exclude off (§8.1).
  if (!next && prev.exclude) return { compulsory: false, exclude: false };
  return { ...prev, compulsory: next };
}

/** New state after the user changes the Exclude toggle. */
export function cascadeOnExcludeChange(prev: ToggleState, next: boolean): ToggleState {
  // Turning Exclude on forces Compulsory on (§8.1).
  if (next) return { compulsory: true, exclude: true };
  return { ...prev, exclude: false };
}
