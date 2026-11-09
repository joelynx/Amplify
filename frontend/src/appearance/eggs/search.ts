/**
 * Browser search eggs (Makeover.md §6). The real search still runs; the page
 * shows the returned card above the results. Finding one records the secret
 * `search-<id>`; "do a barrel roll" also spins the app. Call it once per
 * query change (an effect or memo keyed on the query); side effects run
 * after the current render and the roll only fires when the query changes.
 */

import { barrelRoll } from "./barrelRoll";
import { findEgg } from "./found";
import { matchSearchEgg, normalizeQuery } from "./searchMatch";
import { motionReduced, useAppearance } from "../store";

export interface SearchEgg {
  id: string;
  title: string;
  body: string;
}

export { barrelRoll } from "./barrelRoll";
export { matchSearchEgg, normalizeQuery } from "./searchMatch";

let lastQuery = "";

export function searchEgg(query: string): SearchEgg | null {
  if (!useAppearance.getState().settings.eggs) return null;
  const q = normalizeQuery(query);
  const changed = q !== lastQuery;
  lastQuery = q;
  const egg = matchSearchEgg(query);
  if (!egg) return null;
  queueMicrotask(() => {
    findEgg(`search-${egg.id}`);
    if (egg.id === "barrel-roll" && changed) barrelRoll();
  });
  if (egg.id === "barrel-roll" && motionReduced()) {
    return { ...egg, body: "Consider it rolled. (Reduced motion is on, so the page stays put.)" };
  }
  return egg;
}
