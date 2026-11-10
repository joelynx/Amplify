/**
 * Preset cards. Each card renders its own palette (the palette overlays also
 * match a scoped `[data-theme]`), the logo in the preset's variant and a
 * small study preview. Reward presets show their milestone until earned;
 * secret presets appear once found.
 */

import { type CSSProperties, useEffect, useState } from "react";
import { Check, Lock, Trophy } from "lucide-react";

import { Logo, autoLogoVariant, type LogoVariant } from "../../appearance/brand/Logo";
import { getPreset } from "../../appearance/presets";
import { getItem, normalizeLoadout } from "../../appearance/registry";
import { useAppearance, visiblePresets } from "../../appearance/store";
import { SLOTS, type SlotId } from "../../appearance/types";
import { emit } from "../../appearance/events";
import { Button } from "../../components/ui/Button";
import { Progress } from "../../components/ui/Progress";
import { cn } from "../../lib/cn";
import { ipc, type ThemeMeta } from "../../lib/ipc";
import { StudyPreview } from "./StudyPreview";

const KEEP_CHOICES: { slot: SlotId; label: string }[] = [
  { slot: "sfx", label: "sounds" },
  { slot: "typography", label: "fonts" },
  { slot: "wallpaper", label: "wallpaper" },
  { slot: "cursor", label: "cursor" },
];

function presetLogoVariant(presetId: string, theme: string): LogoVariant {
  const logo = getPreset(presetId)?.slots.logo;
  const v = logo ? logo.slice(5) : "auto";
  if (v !== "auto") return v as LogoVariant;
  return autoLogoVariant(theme);
}

export function PresetGrid() {
  const st = useAppearance();
  const [themes, setThemes] = useState<ThemeMeta[]>([]);
  const [keep, setKeep] = useState<SlotId[]>([]);

  useEffect(() => {
    ipc.list_themes().then(setThemes).catch(() => undefined);
  }, []);
  const meta = new Map(themes.map((t) => [t.id, t]));

  const apply = (id: string) => {
    st.applyPreset(id, keep);
    emit({ type: "theme_switch" });
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm">
        <span className="text-muted">When applying a preset, keep my</span>
        {KEEP_CHOICES.map((k) => (
          <label key={k.slot} className="inline-flex items-center gap-1.5">
            <input
              type="checkbox"
              checked={keep.includes(k.slot)}
              onChange={(e) => setKeep((cur) => (e.target.checked ? [...cur, k.slot] : cur.filter((s) => s !== k.slot)))}
            />
            {k.label}
          </label>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {visiblePresets(st).map((p) => {
          const loadout = normalizeLoadout({ ...p.slots });
          const theme = (getItem(loadout.palette)?.data?.theme as string) ?? "default-light";
          // The preset's own fonts, not the palette CSS fallback stack.
          const type = getItem(loadout.typography)?.data as { body?: string; heading?: string; mono?: string; variation?: string } | undefined;
          const fonts = {
            "--font-family": type?.body,
            "--font-heading": type?.heading,
            "--font-mono": type?.mono,
            fontVariationSettings: type?.variation ?? "normal",
          } as CSSProperties;
          const m = meta.get(p.id);
          const locked = st.locked.has(p.id);
          const active = st.preset === p.id;
          const differs = SLOTS.filter((s) => p.slots[s] && st.loadout[s] !== p.slots[s]).length;
          return (
            <div
              key={p.id}
              data-theme={theme}
              className={cn(
                "flex flex-col overflow-hidden rounded-lg border shadow-sm",
                active ? "border-primary ring-2 ring-primary/40" : "border-border",
              )}
              style={{ ...fonts, background: "var(--background)", color: "var(--text)", fontFamily: "var(--font-family)" }}
            >
              <div className="flex items-center justify-center px-4 pt-4" style={{ minHeight: 92 }}>
                <Logo name="matrix" variant={presetLogoVariant(p.id, theme)} style={{ width: 150 }} />
              </div>
              <div className="m-3 rounded-md border p-3" style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
                <StudyPreview />
              </div>
              <div className="mt-auto flex items-start justify-between gap-3 border-t px-4 py-3" style={{ borderColor: "var(--border)" }}>
                <div className="min-w-0">
                  <h3 className="flex items-center gap-1.5 font-semibold">
                    {p.name}
                    {active && <Check className="h-4 w-4" style={{ color: "var(--primary)" }} />}
                    {p.reward && !locked && <Trophy className="h-4 w-4" style={{ color: "var(--accent)" }} aria-label="Earned" />}
                  </h3>
                  <p className="text-xs" style={{ color: "var(--muted)" }}>
                    {p.description}
                  </p>
                </div>
                {locked ? (
                  <span className="inline-flex shrink-0 items-center gap-1 rounded-md border px-2 py-1 text-xs" style={{ borderColor: "var(--border)", color: "var(--muted)" }}>
                    <Lock className="h-3.5 w-3.5" /> Locked
                  </span>
                ) : (
                  <Button size="sm" variant={active ? "ghost" : "primary"} disabled={active && differs === 0} onClick={() => apply(p.id)}>
                    {active ? (differs ? "Reset" : "Active") : "Apply"}
                  </Button>
                )}
              </div>
              {locked && m?.milestone && (
                <div className="space-y-1 px-4 pb-3 text-xs" style={{ color: "var(--muted)" }}>
                  <div className="font-medium" style={{ color: "var(--text)" }}>
                    {m.milestone.title}: {m.milestone.description}
                  </div>
                  <div className="flex items-center gap-2">
                    <Progress value={m.milestone.progress / Math.max(1, m.milestone.target)} />
                    <span className="tabular-nums">
                      {m.milestone.progress} / {m.milestone.target}
                    </span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
