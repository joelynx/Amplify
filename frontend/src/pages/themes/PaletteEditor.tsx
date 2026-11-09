/**
 * Token overrides on top of the active palette (spec §11.3): change any
 * colour without leaving the theme. Contrast is checked live against WCAG;
 * failing pairs are flagged, and Reset puts the palette's own value back.
 */

import { useEffect, useState } from "react";
import { AlertTriangle, Check, RotateCcw } from "lucide-react";

import { paletteChecks, parseColor, type ContrastCheck } from "../../appearance/contrast";
import { useAppearance } from "../../appearance/store";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";

const TOKENS: { key: string; label: string }[] = [
  { key: "--background", label: "Background" },
  { key: "--surface", label: "Surface (cards)" },
  { key: "--text", label: "Text" },
  { key: "--muted", label: "Muted text" },
  { key: "--border", label: "Borders" },
  { key: "--primary", label: "Primary" },
  { key: "--secondary", label: "Secondary" },
  { key: "--accent", label: "Accent" },
  { key: "--success", label: "Success" },
  { key: "--warning", label: "Warning" },
  { key: "--error", label: "Error" },
];

function toHex(value: string): string {
  const c = parseColor(value);
  if (!c) return "#000000";
  return "#" + c.map((n) => Math.round(n).toString(16).padStart(2, "0")).join("");
}

export function PaletteEditor() {
  const tokens = useAppearance((s) => s.settings.tokens);
  const loadout = useAppearance((s) => s.loadout);
  const set = useAppearance((s) => s.setSettings);
  const [computed, setComputed] = useState<Record<string, string>>({});
  const [checks, setChecks] = useState<ContrastCheck[]>([]);

  useEffect(() => {
    const id = requestAnimationFrame(() => {
      const cs = getComputedStyle(document.documentElement);
      setComputed(Object.fromEntries(TOKENS.map((t) => [t.key, cs.getPropertyValue(t.key).trim()])));
      setChecks(paletteChecks());
    });
    return () => cancelAnimationFrame(id);
  }, [tokens, loadout.palette]);

  const change = (key: string, value: string | null) => {
    const next = { ...tokens };
    if (value === null) delete next[key];
    else next[key] = value;
    set({ tokens: next });
  };

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_20rem]">
      <Card
        title="Colours"
        actions={
          Object.keys(tokens).length > 0 && (
            <Button size="sm" variant="ghost" onClick={() => set({ tokens: {} })}>
              <RotateCcw className="h-4 w-4" /> Reset all
            </Button>
          )
        }
      >
        <p className="mb-3 text-xs text-muted">
          Overrides apply on top of whichever palette is active, and stay when you switch presets.
        </p>
        <ul className="divide-y divide-border">
          {TOKENS.map((t) => {
            const overridden = t.key in tokens;
            const value = tokens[t.key] ?? computed[t.key] ?? "";
            const gradient = !parseColor(value);
            return (
              <li key={t.key} className="flex items-center gap-3 py-2 text-sm">
                <input
                  type="color"
                  value={toHex(value)}
                  disabled={gradient && !overridden}
                  onChange={(e) => change(t.key, e.target.value)}
                  className="h-8 w-10 cursor-pointer rounded border border-border bg-transparent"
                  aria-label={t.label}
                />
                <span className="flex-1">{t.label}</span>
                <code className="text-xs text-muted">{gradient ? "gradient" : toHex(value)}</code>
                {overridden && (
                  <button type="button" className="text-xs text-primary hover:underline" onClick={() => change(t.key, null)}>
                    Reset
                  </button>
                )}
              </li>
            );
          })}
        </ul>
      </Card>
      <Card title="Contrast">
        <ul className="space-y-2 text-sm">
          {checks.map((c) => {
            const ok = c.ratio === null || c.ratio >= c.min;
            return (
              <li key={c.label} className="flex items-center gap-2">
                {ok ? <Check className="h-4 w-4 text-success" /> : <AlertTriangle className="h-4 w-4 text-warning" />}
                <span className="flex-1">{c.label}</span>
                <span className="tabular-nums text-xs text-muted">
                  {c.ratio === null ? "n/a" : `${c.ratio.toFixed(1)} : 1`} (min {c.min})
                </span>
              </li>
            );
          })}
        </ul>
        <p className="mt-3 text-xs text-muted">
          WCAG AA asks for 4.5 : 1 for body text and 3 : 1 for large text and buttons.
        </p>
      </Card>
    </div>
  );
}
