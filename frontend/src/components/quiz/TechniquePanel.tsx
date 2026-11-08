/**
 * Mixed review: pick two or more techniques you have already practised; the
 * session splits its questions across them and orders them so neighbouring
 * questions usually need different techniques. The technique stays hidden
 * until each question is answered, so choosing the method is part of the work.
 */

import { useEffect, useMemo, useState } from "react";

import { cn } from "../../lib/cn";
import { ipc, type ConceptRef, type StudiedTechnique } from "../../lib/ipc";

interface Props {
  subject: string | null;
  selected: ConceptRef[];
  onChange: (concepts: ConceptRef[]) => void;
}

export function TechniquePanel({ subject, selected, onChange }: Props) {
  const [rows, setRows] = useState<StudiedTechnique[] | null>(null);
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    let cancelled = false;
    ipc.get_studied_techniques(subject).then((r) => {
      if (!cancelled) setRows(r);
    });
    return () => {
      cancelled = true;
    };
  }, [subject]);

  const practised = useMemo(() => (rows ?? []).filter((r) => r.practised > 0), [rows]);
  const fewPractised = practised.length < 2;
  const shown = showAll || fewPractised ? (rows ?? []) : practised;
  const picked = new Set(selected.map((c) => c.label));

  const toggle = (tag: string) => {
    if (picked.has(tag)) onChange(selected.filter((c) => c.label !== tag));
    else onChange([...selected, { kind: "tag", label: tag }]);
  };

  if (!rows) return <p className="text-sm text-muted">Loading techniques…</p>;

  return (
    <div className="space-y-3">
      <p className="text-xs text-muted">
        {fewPractised
          ? "You have practised fewer than two techniques in this subject so far, so every technique is listed."
          : "Techniques from questions you have answered. Pick at least two."}
      </p>
      <ul className="flex max-h-72 flex-wrap gap-2 overflow-y-auto">
        {shown.map((r) => {
          const on = picked.has(r.tag);
          return (
            <li key={r.tag}>
              <button
                type="button"
                onClick={() => toggle(r.tag)}
                aria-pressed={on}
                className={cn(
                  "rounded-full border px-3 py-1 text-sm transition-colors",
                  on ? "border-primary bg-primary/10 text-primary" : "border-border bg-background hover:border-primary/50",
                )}
                title={`${r.available} questions carry this technique`}
              >
                {r.tag}
                <span className="ml-1 text-xs text-muted">
                  {r.practised > 0 ? `${r.practised} done` : `${r.available}`}
                </span>
              </button>
            </li>
          );
        })}
      </ul>
      {!fewPractised && (
        <button type="button" className="text-xs text-primary hover:underline" onClick={() => setShowAll((v) => !v)}>
          {showAll ? "Only techniques I have practised" : "Show every technique"}
        </button>
      )}
      <p className="text-xs text-muted">
        {selected.length} selected{selected.length === 1 ? " — pick one more" : ""}. Reused questions are allowed in a
        mixed review.
      </p>
    </div>
  );
}
