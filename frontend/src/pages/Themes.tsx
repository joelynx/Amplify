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
 */

import { useEffect, useState } from "react";
import { Check } from "lucide-react";

import { Button } from "../components/ui/Button";
import { cn } from "../lib/cn";
import { ipc, type ThemeMeta } from "../lib/ipc";
import { applyTheme, getCurrentTheme, type ThemeId } from "../lib/theme";

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

  return (
    <main className="flex-1 overflow-y-auto">
      <div className="mx-auto max-w-4xl space-y-6 px-6 py-6">
        <header>
          <h1 className="text-2xl font-semibold">Themes</h1>
          <p className="text-sm text-muted">
            Default Light + Default Dark + one flavor (Pastel) so far. Switching applies live; no
            restart required.
          </p>
          {error && <p className="mt-2 text-sm text-error">{error}</p>}
        </header>

        <div className="grid gap-4 md:grid-cols-2">
          {themes.map((t) => {
            const isActive = t.id === active;
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
                    </h2>
                    <p className="text-sm text-muted">{t.description}</p>
                  </div>
                  <Button
                    variant={isActive ? "ghost" : "primary"}
                    size="sm"
                    onClick={() => onUse(t.id)}
                    disabled={isActive}
                  >
                    {isActive ? "Active" : "Use"}
                  </Button>
                </header>

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
                  <div className="space-y-1 text-xs">
                    <p style={{ color: "var(--text)" }}>
                      The quick brown fox jumps over the lazy dog
                    </p>
                    <p style={{ color: "var(--muted)" }}>muted helper text · 0.875rem</p>
                    <span
                      className="amplify-tooltip"
                      style={{
                        display: "inline-block",
                        marginTop: "0.25rem",
                        position: "relative",
                      }}
                    >
                      <span className="amp-label">themed tooltip</span>
                      <span className="amp-meta">.amplify-tooltip</span>
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </main>
  );
}
