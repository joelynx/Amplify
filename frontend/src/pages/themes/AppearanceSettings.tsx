/**
 * Appearance settings: how much whimsy, focus mode, motion, the sound mixer,
 * Home, seasonal events, easter eggs, personal touches and the day/night
 * switch. Accessibility options are always available.
 */

import { type ReactNode, useEffect, useState } from "react";

import { useAppearance } from "../../appearance/store";
import type { AppearanceSettings, Volumes, Whimsy } from "../../appearance/types";
import { Card } from "../../components/ui/Card";
import { Input } from "../../components/ui/Input";
import { Switch } from "../../components/ui/Switch";
import { cn } from "../../lib/cn";
import { getAccessibilityMode, setAccessibilityMode } from "../../lib/theme";

function Segmented<T extends string>({ value, options, onChange, label }: {
  value: T;
  options: { id: T; label: string }[];
  onChange: (v: T) => void;
  label: string;
}) {
  return (
    <div role="radiogroup" aria-label={label} className="inline-flex overflow-hidden rounded-md border border-border">
      {options.map((o) => (
        <button
          key={o.id}
          type="button"
          role="radio"
          aria-checked={value === o.id}
          onClick={() => onChange(o.id)}
          className={cn("px-3 py-1.5 text-sm", value === o.id ? "bg-primary text-on-primary" : "bg-background hover:bg-surface")}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

function Row({ title, hint, children }: { title: string; hint?: string; children: ReactNode }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 py-2">
      <div className="min-w-0">
        <div className="text-sm font-medium">{title}</div>
        {hint && <div className="text-xs text-muted">{hint}</div>}
      </div>
      <div className="flex items-center gap-2">{children}</div>
    </div>
  );
}

const CHANNELS: { key: keyof Volumes; label: string }[] = [
  { key: "master", label: "Master" },
  { key: "ui", label: "Clicks and UI" },
  { key: "feedback", label: "Answer feedback" },
  { key: "celebration", label: "Session ends and unlocks" },
];

export function AppearanceSettingsPanel() {
  const settings = useAppearance((s) => s.settings);
  const saved = useAppearance((s) => s.saved);
  const set = useAppearance((s) => s.setSettings);
  const [a11y, setA11y] = useState(getAccessibilityMode());
  const patch = (p: Partial<AppearanceSettings>) => set(p);

  useEffect(() => setA11y(getAccessibilityMode()), []);

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card title="Whimsy and focus">
        <Row title="Whimsy" hint="How much decoration: room and results animations, wallpaper strength, easter-egg effects.">
          <Segmented<Whimsy>
            label="Whimsy"
            value={settings.whimsy}
            onChange={(whimsy) => patch({ whimsy })}
            options={[{ id: "off", label: "Off" }, { id: "subtle", label: "Subtle" }, { id: "full", label: "Full" }]}
          />
        </Row>
        <Row title="Focus mode" hint="Hides the wallpaper and turns off decorative animation. Also in the nav bar.">
          <Switch checked={settings.focus} onCheckedChange={(focus) => patch({ focus })} ariaLabel="Focus mode" />
        </Row>
        <Row title="Focus during timed quizzes" hint="Turns focus on by itself while a timer runs.">
          <Switch checked={settings.focusInTimed} onCheckedChange={(focusInTimed) => patch({ focusInTimed })} ariaLabel="Focus during timed quizzes" />
        </Row>
        <Row title="Reduced motion" hint="System follows your Windows setting.">
          <Segmented
            label="Reduced motion"
            value={settings.reducedMotion}
            onChange={(reducedMotion) => patch({ reducedMotion })}
            options={[{ id: "system", label: "System" }, { id: "on", label: "On" }, { id: "off", label: "Off" }]}
          />
        </Row>
      </Card>

      <Card title="Sound">
        <Row title="Mute everything">
          <Switch checked={settings.muted} onCheckedChange={(muted) => patch({ muted })} ariaLabel="Mute" />
        </Row>
        {CHANNELS.map((c) => (
          <Row key={c.key} title={c.label}>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={settings.volumes[c.key]}
              disabled={settings.muted}
              onChange={(e) => patch({ volumes: { ...settings.volumes, [c.key]: Number(e.target.value) } })}
              className="w-40 accent-[var(--primary)]"
              aria-label={`${c.label} volume`}
            />
            <span className="w-9 text-right text-xs tabular-nums text-muted">{Math.round(settings.volumes[c.key] * 100)}%</span>
          </Row>
        ))}
      </Card>

      <Card title="Home and events">
        <Row title="Study room on Home" hint="An illustrated room you navigate from. Off shows the plain layout.">
          <Switch checked={settings.room} onCheckedChange={(room) => patch({ room })} ariaLabel="Study room on Home" />
        </Row>
        <Row title="Seasonal events" hint="Pi Day, Ada Lovelace Day, club events and more.">
          <Switch checked={settings.seasonal} onCheckedChange={(seasonal) => patch({ seasonal })} ariaLabel="Seasonal events" />
        </Row>
        <Row title="Easter eggs">
          <Switch checked={settings.eggs} onCheckedChange={(eggs) => patch({ eggs })} ariaLabel="Easter eggs" />
        </Row>
      </Card>

      <Card title="Personal">
        <Row title="Your name" hint="For the greeting on Home. Stays on this computer.">
          <Input value={settings.greetingName} onChange={(e) => patch({ greetingName: e.target.value.slice(0, 40) })} className="w-48" />
        </Row>
        <Row title="Exam countdown" hint="Shown on Home.">
          <Input
            placeholder="Label, e.g. Midsems"
            value={settings.exam.label}
            onChange={(e) => patch({ exam: { ...settings.exam, label: e.target.value.slice(0, 40) } })}
            className="w-40"
          />
          <Input
            type="date"
            value={settings.exam.date ?? ""}
            onChange={(e) => patch({ exam: { ...settings.exam, date: e.target.value || null } })}
            className="w-40"
          />
        </Row>
      </Card>

      <Card title="Day and night">
        <Row title="Switch loadout at night" hint="Uses one of your saved loadouts between the hours below.">
          <Switch
            checked={settings.dayNight.enabled}
            disabled={saved.length === 0}
            onCheckedChange={(enabled) => patch({ dayNight: { ...settings.dayNight, enabled } })}
            ariaLabel="Switch loadout at night"
          />
        </Row>
        <Row title="Night loadout">
          <select
            className="h-9 rounded-md border border-border bg-background px-2 text-sm"
            value={settings.dayNight.night ?? ""}
            onChange={(e) => patch({ dayNight: { ...settings.dayNight, night: e.target.value || null } })}
          >
            <option value="">{saved.length ? "Choose…" : "Save a loadout first"}</option>
            {saved.map((s) => (
              <option key={s.name} value={s.name}>
                {s.name}
              </option>
            ))}
          </select>
        </Row>
        <Row title="Night hours">
          <input type="number" min={0} max={23} value={settings.dayNight.from} onChange={(e) => patch({ dayNight: { ...settings.dayNight, from: Number(e.target.value) } })} className="h-9 w-16 rounded-md border border-border bg-background px-2 text-sm" aria-label="Night starts" />
          <span className="text-sm text-muted">to</span>
          <input type="number" min={0} max={23} value={settings.dayNight.to} onChange={(e) => patch({ dayNight: { ...settings.dayNight, to: Number(e.target.value) } })} className="h-9 w-16 rounded-md border border-border bg-background px-2 text-sm" aria-label="Night ends" />
        </Row>
      </Card>

      <Card title="Accessibility">
        <Row title="High-contrast text" hint="Forces maximum-contrast text over any palette and wallpaper.">
          <Switch
            checked={a11y}
            onCheckedChange={(v) => {
              void setAccessibilityMode(v);
              setA11y(v);
            }}
            ariaLabel="High-contrast text"
          />
        </Row>
        <p className="text-xs text-muted">
          Reduced motion is above. Both are always free.
        </p>
      </Card>
    </div>
  );
}
