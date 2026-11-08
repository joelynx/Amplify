/**
 * The Themes page (spec §8.3 / §11).
 *
 * Card per theme: name, description, color-token preview, "Use" button.
 * Active theme renders with a check + filled accent.
 *
 * Selecting a theme calls `applyTheme(id)` which:
 *   1. flips `<html data-theme>` so the CSS overlay takes over,
 *   2. persists `configs.THEME_SELECTED`,
 *   3. plays the `theme_switch` sound (fail-soft).
 *
 * Reward themes unlock with a practice milestone (spaced reviews, fixing old
 * mistakes, honest attempts; app/core/learning.py). Locked cards show the
 * milestone and progress and can still be previewed. The built-in themes and
 * the accessibility toggle are always available.
 *
 * Each preview renders a small question in the theme: text, an equation, an
 * answer box and the correct / wrong feedback, so a theme can be judged by
 * how comfortable it is to study in.
 */

import { useEffect, useState } from "react";
import { Check, Lock, Trophy } from "lucide-react";

import { Button } from "../components/ui/Button";
import { LatexContent } from "../components/browser/LatexContent";
import { Switch } from "../components/ui/Switch";
import { cn } from "../lib/cn";
import { ipc, type ThemeMeta } from "../lib/ipc";
import {
  applyTheme,
  getAccessibilityMode,
  getCurrentTheme,
  isFlavorTheme,
  setAccessibilityMode,
  type ThemeId,
} from "../lib/theme";

/** Preview swatches use the same CSS vars the theme defines. We render a
 * shadow DOM-ish trick by attaching `data-theme={id}` to the swatch container,
 * so each card shows its own palette regardless of which theme is active. */
const SWATCH_TOKENS: readonly { key: string; label: string }[] = [
  { key: "--primary", label: "primary" },
  { key: "--secondary", label: "secondary" },
  { key: "--accent", label: "accent" },
  { key: "--surface", label: "surface" },
  { key: "--text", label: "text" },
];

export default function ThemesPage() {
  const [themes, setThemes] = useState<ThemeMeta[]>([]);
  const [active, setActive] = useState<ThemeId>(getCurrentTheme());
  const [a11y, setA11y] = useState<boolean>(getAccessibilityMode());
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    ipc.list_themes().then(setThemes);
  }, []);

  const onUse = async (id: string) => {
    setError(null);
    try {
      await applyTheme(id as ThemeId);
      setActive(id as ThemeId);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const onToggleA11y = async (v: boolean) => {
    await setAccessibilityMode(v);
    setA11y(v);
  };

  const showA11y = isFlavorTheme(active);

  return (
    <main className="h-full overflow-y-auto">
      <div className="mx-auto max-w-4xl space-y-6 px-6 py-6">
        <header className="space-y-3">
          <div>
            <h1 className="text-2xl font-semibold">Themes</h1>
            <p className="text-sm text-muted">
              Two defaults (WCAG AA), seven flavor themes, and three you earn by practising (spaced
              reviews, fixing old mistakes, honest attempts). Switching applies live; no restart required.
            </p>
            {error && <p className="mt-2 text-sm text-error">{error}</p>}
          </div>
          {showA11y && (
            <label className="inline-flex items-center gap-2 rounded-md border border-border bg-surface px-3 py-2 text-sm">
              <Switch checked={a11y} onCheckedChange={onToggleA11y} ariaLabel="Accessibility mode" />
              <span className="font-medium">Accessibility mode</span>
              <span className="text-muted">
                — forces high-contrast text on top of the theme's background art (spec §11.4).
              </span>
            </label>
          )}
        </header>

        <div className="grid gap-4 md:grid-cols-2">
          {themes.map((t) => {
            const isActive = t.id === active;
            const m = t.milestone;
            return (
              <div
                key={t.id}
                className={cn(
                  "rounded-lg border bg-surface p-4 shadow-sm",
                  isActive ? "border-primary ring-2 ring-primary/30" : "border-border",
                )}
              >
                <header className="mb-3 flex items-start justify-between gap-3">
                  <div>
                    <h2 className="flex items-center gap-2 text-lg font-semibold">
                      {t.name}
                      {isActive && <Check className="h-4 w-4 text-primary" />}
                      {t.reward && !t.locked && <Trophy className="h-4 w-4 text-accent" aria-label="Earned" />}
                    </h2>
                    <p className="text-sm text-muted">{t.description}</p>
                  </div>
                  {t.locked ? (
                    <span className="inline-flex items-center gap-1 rounded-md border border-border px-2 py-1 text-xs text-muted">
                      <Lock className="h-3.5 w-3.5" />
                      Locked
                    </span>
                  ) : (
                    <Button
                      variant={isActive ? "ghost" : "primary"}
                      size="sm"
                      onClick={() => onUse(t.id)}
                      disabled={isActive}
                    >
                      {isActive ? "Active" : "Use"}
                    </Button>
                  )}
                </header>

                {t.locked && m && (
                  <div className="mb-3 space-y-1 rounded-md border border-dashed border-border p-2 text-xs">
                    <div className="font-medium">
                      {m.title}: {m.description}
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-border">
                        <div
                          className="h-full rounded-full bg-primary"
                          style={{ width: `${Math.round((m.progress / m.target) * 100)}%` }}
                        />
                      </div>
                      <span className="tabular-nums text-muted">
                        {m.progress} / {m.target}
                      </span>
                    </div>
                  </div>
                )}

                {/* Preview — the swatch container gets data-theme so the
                 * tokens it reads come from THAT theme, regardless of which
                 * theme is currently active globally. */}
                <div
                  data-theme={t.id}
                  className="rounded-md border border-border p-3"
                  style={{ background: "var(--background)", color: "var(--text)" }}
                >
                  <div className="mb-2 flex items-center gap-1">
                    {SWATCH_TOKENS.map((tk) => (
                      <span
                        key={tk.key}
                        className="h-6 w-6 rounded-md border border-border"
                        style={{ background: `var(${tk.key})` }}
                        title={tk.label}
                      />
                    ))}
                  </div>
                  <StudyPreview />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </main>
  );
}

const PREVIEW_QUESTION = String.raw`Find the eigenvalues of $A = \begin{pmatrix} 2 & 1 \\ 1 & 2 \end{pmatrix}$.`;

/** A question as the quiz shows it: statement with an equation, an answer box,
 * and both feedback states. Reads the surrounding theme's tokens. */
function StudyPreview() {
  return (
    <div className="space-y-2 text-sm">
      <LatexContent source={PREVIEW_QUESTION} />
      <div className="flex items-center gap-2">
        <span
          className="flex-1 rounded-md border px-2 py-1 text-xs"
          style={{ borderColor: "var(--border)", background: "var(--surface)", color: "var(--text)" }}
        >
          1, 3
        </span>
        <span
          className="rounded-md px-2 py-1 text-xs font-medium"
          style={{ background: "var(--primary)", color: "var(--background)" }}
        >
          Submit
        </span>
      </div>
      <div className="flex flex-wrap gap-2 text-xs">
        <span className="rounded-md border px-2 py-0.5" style={{ borderColor: "var(--success)", color: "var(--success)" }}>
          ✓ Correct · full credit
        </span>
        <span className="rounded-md border px-2 py-0.5" style={{ borderColor: "var(--error)", color: "var(--error)" }}>
          ✗ Expected 1, 3
        </span>
        <span className="amplify-tooltip" style={{ display: "inline-block", position: "relative" }}>
          <span className="amp-label">hint</span>
        </span>
      </div>
      <p className="text-xs" style={{ color: "var(--muted)" }}>
        muted helper text · 0.875rem
      </p>
    </div>
  );
}
