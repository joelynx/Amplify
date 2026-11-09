/**
 * Theme Lab (Makeover.md §3.4): a workbench for checking a loadout and
 * sourced assets. Every surface on one page in the active loadout, the
 * logos and loaders in every variant, contrast for every palette, which
 * fonts are bundled, and which items came from drop-in packs.
 *
 * Reached from Settings or #/theme-lab; not in the nav.
 */

import { useEffect, useMemo, useState } from "react";

import { Logo, type LogoVariant } from "../appearance/brand/Logo";
import { BootScreen, MatrixLoader, Spinner } from "../appearance/brand/Loader";
import { contrast } from "../appearance/contrast";
import { emit } from "../appearance/events";
import { bundledFamilies } from "../appearance/fonts";
import { allItems, itemsFor, resolve } from "../appearance/registry";
import { ResultsPreview } from "../appearance/results/ResultsScreen";
import { previewSfx } from "../appearance/sound/engine";
import { useAppearance } from "../appearance/store";
import { SLOTS } from "../appearance/types";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Checkbox } from "../components/ui/Checkbox";
import { Input } from "../components/ui/Input";
import { Progress } from "../components/ui/Progress";
import { Switch } from "../components/ui/Switch";
import { StudyPreview } from "./themes/StudyPreview";

const VARIANTS: LogoVariant[] = ["original", "tinted", "mono", "pixel", "terminal", "comic", "glossy", "chalk", "neon", "blueprint"];

function fontFamilies(stack: string): string[] {
  return stack.split(",").map((f) => f.trim().replace(/^"|"$/g, "")).filter((f) => !/^(system-ui|sans-serif|serif|monospace|cursive|ui-monospace)$/.test(f));
}

/** Contrast of every palette, measured on hidden scoped elements. */
function usePaletteReport() {
  const [rows, setRows] = useState<{ id: string; name: string; text: number | null; muted: number | null; button: number | null }[]>([]);
  useEffect(() => {
    const host = document.createElement("div");
    host.style.cssText = "position:absolute;left:-9999px;top:0";
    document.body.appendChild(host);
    const out = itemsFor("palette").map((p) => {
      const el = document.createElement("div");
      el.setAttribute("data-theme", String(p.data?.theme));
      host.appendChild(el);
      const cs = getComputedStyle(el);
      const t = (k: string) => cs.getPropertyValue(k).trim();
      return {
        id: p.id,
        name: p.name,
        text: contrast(t("--text"), t("--background")),
        muted: contrast(t("--muted"), t("--background")),
        button: contrast(t("--on-primary") || "#ffffff", t("--primary")),
      };
    });
    host.remove();
    setRows(out);
  }, []);
  return rows;
}

export default function ThemeLabPage() {
  const loadout = useAppearance((s) => s.loadout);
  const [switchOn, setSwitchOn] = useState(true);
  const [boot, setBoot] = useState(0);
  const palettes = usePaletteReport();
  const bundled = useMemo(() => bundledFamilies(), []);
  const wanted = useMemo(() => {
    const fams = new Set<string>();
    for (const t of itemsFor("typography")) {
      for (const k of ["body", "heading", "mono"]) fontFamilies(String(t.data?.[k] ?? "")).forEach((f) => fams.add(f));
    }
    return [...fams].sort();
  }, []);
  const packs = allItems().filter((i) => i.tags?.includes("pack"));
  const fmt = (r: number | null, min: number) => (r === null ? <span className="text-muted">n/a</span> : <span className={r < min ? "font-semibold text-error" : ""}>{r.toFixed(1)}</span>);

  return (
    <main className="h-full overflow-y-auto">
      {boot > 0 && (
        <div className="fixed inset-0 z-50 bg-background">
          <BootScreen key={boot} message="Connecting…" onDone={() => setBoot(0)} />
        </div>
      )}
      <div className="mx-auto max-w-6xl space-y-5 px-6 py-6">
        <header>
          <h1 className="text-2xl font-semibold">Theme Lab</h1>
          <p className="text-sm text-muted">
            Everything in the active loadout at once. Drop packs into <code>frontend/packs/&lt;id&gt;/</code> and fonts into{" "}
            <code>frontend/fonts/&lt;Family&gt;/</code>, rebuild (or run the dev server), and check them here.
          </p>
        </header>

        <Card title="Active loadout">
          <div className="grid gap-x-6 gap-y-1 text-xs sm:grid-cols-2 lg:grid-cols-4">
            {SLOTS.map((s) => (
              <div key={s} className="flex justify-between gap-2">
                <span className="text-muted">{s}</span>
                <span className="truncate font-medium">{resolve(loadout, s)?.name ?? "—"}</span>
              </div>
            ))}
          </div>
        </Card>

        <div className="grid gap-4 lg:grid-cols-2">
          <Card title="Controls">
            <div className="flex flex-wrap gap-2">
              <Button variant="primary">Primary</Button>
              <Button variant="secondary">Secondary</Button>
              <Button variant="outline">Outline</Button>
              <Button variant="ghost">Ghost</Button>
              <Button variant="primary" disabled>
                <Spinner className="h-4 w-4" /> Busy
              </Button>
            </div>
            <div className="mt-3 flex items-center gap-3">
              <Input placeholder="An input" className="max-w-xs" />
              <Switch checked={switchOn} onCheckedChange={setSwitchOn} ariaLabel="Sample switch" />
              <Checkbox state="checked" readOnly />
            </div>
            <div className="mt-3 space-y-2">
              <Progress value={0.62} />
              <span className="amplify-tooltip inline-block">
                <span className="amp-label">Tooltip</span> <span className="amp-meta">12 · 34%</span>
              </span>
            </div>
          </Card>
          <Card title="Question paper">
            <div data-ui="question">
              <StudyPreview />
            </div>
          </Card>
        </div>

        <Card title="Loaders">
          <div className="flex flex-wrap items-end gap-6">
            {(["sweep", "reduce"] as const).map((k) => (
              <div key={k} className="text-center text-xs text-muted">
                <MatrixLoader kind={k} className="mx-auto block w-32" />
                {k}
              </div>
            ))}
            <div className="text-center text-xs text-muted">
              <Spinner className="mx-auto block h-6 w-6" />
              φ coin
            </div>
            <div className="text-center text-xs text-muted">
              <Button size="sm" variant="primary" onClick={() => setBoot((n) => n + 1)}>
                Replay boot
              </Button>
            </div>
          </div>
        </Card>

        <Card title="Logos">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {VARIANTS.map((v) => (
              <div key={v} className="space-y-2 rounded-md border border-border p-3 text-xs">
                <div className="font-medium">{v}</div>
                <Logo name="matrix" variant={v} style={{ width: 150 }} />
                <Logo name="inline" variant={v} style={{ width: 120 }} />
                <Logo name="coding" variant={v} style={{ width: 130 }} />
              </div>
            ))}
          </div>
        </Card>

        <div className="grid gap-4 lg:grid-cols-2">
          <Card title="Sounds">
            <div className="flex flex-wrap gap-2">
              <Button size="sm" onClick={() => previewSfx(loadout.sfx)}>Sound pack demo</Button>
              <Button size="sm" onClick={() => emit({ type: "answer", outcome: "correct", unaided: true, combo: 3, selfAssessed: false })}>
                Fake: correct ×3
              </Button>
              <Button size="sm" onClick={() => emit({ type: "answer", outcome: "wrong", unaided: true, combo: 0, selfAssessed: false })}>
                Fake: wrong
              </Button>
              <Button size="sm" onClick={() => emit({ type: "review_due", count: 3 })}>Fake: reviews due</Button>
            </div>
          </Card>
          <Card title="Results screen">
            <ResultsPreview itemId={loadout.results} />
          </Card>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <Card title="Palette contrast">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-left text-muted">
                  <th className="py-1">Palette</th>
                  <th>Text (4.5)</th>
                  <th>Muted (4.5)</th>
                  <th>Button (3)</th>
                </tr>
              </thead>
              <tbody>
                {palettes.map((p) => (
                  <tr key={p.id} className="border-t border-border">
                    <td className="py-1">{p.name}</td>
                    <td>{fmt(p.text, 4.5)}</td>
                    <td>{fmt(p.muted, 4.5)}</td>
                    <td>{fmt(p.button, 3)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
          <Card title="Fonts">
            <p className="mb-2 text-xs text-muted">Families the typography items ask for. Missing ones fall back to the next font in the stack.</p>
            <ul className="grid grid-cols-2 gap-x-4 text-xs">
              {wanted.map((f) => (
                <li key={f} className="flex justify-between gap-2 py-0.5">
                  <span style={{ fontFamily: `"${f}"` }}>{f}</span>
                  <span className={bundled.has(f) ? "text-success" : "text-muted"}>{bundled.has(f) ? "bundled" : "missing"}</span>
                </li>
              ))}
            </ul>
            <div className="mt-4 text-sm font-medium">Packs</div>
            {packs.length === 0 ? (
              <p className="text-xs text-muted">No drop-in packs found in frontend/packs/.</p>
            ) : (
              <ul className="text-xs">
                {packs.map((p) => (
                  <li key={p.id}>
                    {p.slot}: {p.name} <span className="text-muted">({p.id})</span>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>
      </div>
    </main>
  );
}
