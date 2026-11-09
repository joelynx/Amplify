/** Every room id a preset names exists, and every room item has a renderer. */

import { describe, expect, it } from "vitest";

import { PRESETS } from "../../presets";
import { ITEMS } from "../items";

describe("room items", () => {
  const ids = new Set(ITEMS.map((i) => i.id));

  it("cover every room used by a preset", () => {
    const used = PRESETS.map((p) => p.slots.room).filter((r): r is string => !!r);
    expect(used.length).toBeGreaterThan(0);
    for (const id of used) expect(ids.has(id), id).toBe(true);
  });

  it("include the slot default and the seven themes", () => {
    for (const id of ["room.study", "room.library", "room.observatory", "room.pixel-cabin", "room.desktop", "room.greenhouse", "room.dorm"]) {
      expect(ids.has(id), id).toBe(true);
    }
  });

  it("are well formed", () => {
    expect(ids.size).toBe(ITEMS.length);
    for (const it of ITEMS) {
      expect(it.slot).toBe("room");
      expect(it.id.startsWith("room.")).toBe(true);
      expect(typeof it.data?.base).toBe("string");
    }
  });
});
