/**
 * Room theme renderers by id. An item may name another renderer through
 * `data.base` (for drop-in packs that reuse a built-in room with their own
 * wall picture); unknown ids fall back to the study.
 */

import type { RoomTheme } from "../model";
import { desktop } from "./desktop";
import { dorm } from "./dorm";
import { greenhouse } from "./greenhouse";
import { observatory } from "./observatory";
import { pixelCabin } from "./pixel";
import { library, study } from "./study";

export const THEMES: Record<string, RoomTheme> = Object.fromEntries(
  [study, library, observatory, pixelCabin, desktop, greenhouse, dorm].map((t) => [t.id, t]),
);

export function roomTheme(id: string | undefined): RoomTheme {
  return (id && THEMES[id]) || study;
}
