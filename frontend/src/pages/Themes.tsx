/**
 * Themes and Wardrobe (spec §8.3 / §11, Makeover.md §3 and §10).
 *
 * A theme is now a *preset*: a curated value for every appearance slot
 * (palette, chrome, fonts, sounds, wallpaper, …). Presets apply
 * live; the Wardrobe swaps any single slot; Settings holds whimsy, focus,
 * motion and the sound mixer; Colours overrides palette tokens; Saved keeps
 * named loadouts and share codes; Collection lists easter eggs found.
 *
 * Reward presets unlock with a practice milestone (app/core/learning.py);
 * secret presets appear once their easter egg is found. Accessibility
 * options are always available.
 */

import { useState } from "react";

import { CollectionLog } from "../appearance/eggs/CollectionLog";
import { getPref, setPref } from "../appearance/prefs";
import { cn } from "../lib/cn";
import { AppearanceSettingsPanel } from "./themes/AppearanceSettings";
import { PaletteEditor } from "./themes/PaletteEditor";
import { PresetGrid } from "./themes/PresetGrid";
import { SavedLoadouts } from "./themes/SavedLoadouts";
import { SlotBrowser } from "./themes/SlotBrowser";

const TABS = [
  { id: "presets", label: "Presets" },
  { id: "wardrobe", label: "Wardrobe" },
  { id: "settings", label: "Settings" },
  { id: "colours", label: "Colours" },
  { id: "saved", label: "Saved" },
  { id: "collection", label: "Collection" },
] as const;
type Tab = (typeof TABS)[number]["id"];

export default function ThemesPage() {
  const [tab, setTab] = useState<Tab>(() => {
    const t = getPref<string>("themes.tab", "presets");
    return TABS.some((x) => x.id === t) ? (t as Tab) : "presets";
  });
  const choose = (t: Tab) => {
    setTab(t);
    setPref("themes.tab", t);
  };

  return (
    <main className="h-full overflow-y-auto">
      <div className="mx-auto max-w-6xl space-y-5 px-6 py-6">
        <header className="space-y-1">
          <h1 className="text-2xl font-semibold">Themes</h1>
          <p className="text-sm text-muted">
            Pick a preset, then swap any part of it in the Wardrobe. Everything applies live. Three presets are earned by
            practising, and one has to be found.
          </p>
        </header>
        <div role="tablist" aria-label="Themes sections" className="flex flex-wrap gap-1 border-b border-border">
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              role="tab"
              aria-selected={tab === t.id}
              onClick={() => choose(t.id)}
              className={cn(
                "-mb-px border-b-2 px-3 py-2 text-sm",
                tab === t.id ? "border-primary font-medium text-primary" : "border-transparent text-muted hover:text-text",
              )}
            >
              {t.label}
            </button>
          ))}
        </div>
        <div role="tabpanel">
          {tab === "presets" && <PresetGrid />}
          {tab === "wardrobe" && <SlotBrowser />}
          {tab === "settings" && <AppearanceSettingsPanel />}
          {tab === "colours" && <PaletteEditor />}
          {tab === "saved" && <SavedLoadouts />}
          {tab === "collection" && <CollectionLog />}
        </div>
      </div>
    </main>
  );
}
