/**
 * Collection log (Makeover.md §6): every easter egg in the catalogue, found
 * ones with their reward, the rest as "???" with a vague hint.
 */

import { useAppearance } from "../store";
import { EGGS, rewardLabel, type EggDef } from "./catalogue";

const GROUPS: { id: EggDef["group"]; label: string }[] = [
  { id: "global", label: "Around the app" },
  { id: "search", label: "In the Browser search" },
];

export function CollectionLog({ className = "" }: { className?: string }) {
  const secrets = useAppearance((s) => s.secrets);
  const enabled = useAppearance((s) => s.settings.eggs);
  const found = EGGS.filter((e) => secrets.has(e.id)).length;

  return (
    <section className={`space-y-4 ${className}`} aria-labelledby="amp-collection-log">
      <header className="flex items-baseline justify-between gap-3">
        <h3 id="amp-collection-log" className="text-base font-semibold text-text">
          Collection log
        </h3>
        <span className="text-sm text-muted">
          {found} / {EGGS.length} found
        </span>
      </header>
      {!enabled && <p className="text-sm text-muted">Easter eggs are turned off, so nothing new will be found.</p>}
      {GROUPS.map((g) => (
        <div key={g.id} className="space-y-2">
          <h4 className="text-xs font-medium uppercase tracking-wide text-muted">{g.label}</h4>
          <ul className="grid gap-2 sm:grid-cols-2">
            {EGGS.filter((e) => e.group === g.id).map((e) => {
              const got = secrets.has(e.id);
              return (
                <li
                  key={e.id}
                  className={
                    "rounded-md border px-3 py-2 text-sm " +
                    (got ? "border-border bg-surface text-text" : "border-dashed border-border text-muted")
                  }
                >
                  {got ? (
                    <>
                      <div className="font-medium">{e.title}</div>
                      <div className="text-xs text-muted">{rewardLabel(e.reward)}</div>
                    </>
                  ) : (
                    <>
                      <div className="font-mono font-medium" aria-label="Not found yet">
                        ???
                      </div>
                      <div className="text-xs italic">{e.hint}</div>
                    </>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </section>
  );
}
