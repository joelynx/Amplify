/**
 * Tag tray (spec §8.1, §7.2):
 *   - Searchable combobox adds chips into a flow-layout tray.
 *   - A rule selector (Must include / Match any / Exclude) sets the category at add time.
 *   - Each chip names its rule; colors: compulsory blue, optional grey, excluded red.
 *
 * Each chip stays in its category until removed. Clicking the × removes it.
 */

import { useMemo, useState } from "react";
import { X } from "lucide-react";

import { cn } from "../../lib/cn";
import { useGenerateStore, type TagCategory } from "../../state/generate";
import { Combobox } from "../ui/Combobox";

const RULES: readonly { id: TagCategory; label: string; hint: string }[] = [
  { id: "compulsory", label: "Must include", hint: "Every question has this tag." },
  { id: "optional", label: "Match any", hint: "Every question has at least one of these tags." },
  { id: "excluded", label: "Exclude", hint: "No question has this tag." },
];
const RULE_LABEL = Object.fromEntries(RULES.map((r) => [r.id, r.label])) as Record<TagCategory, string>;

interface Props {
  available: readonly string[];
}

const chipStyle: Record<TagCategory, string> = {
  compulsory: "bg-primary/10 text-primary border-primary/30",
  optional: "bg-muted/15 text-text border-border",
  excluded: "bg-error/10 text-error border-error/30",
};

export function TagTray({ available }: Props) {
  const tags = useGenerateStore((s) => s.tags);
  const addTag = useGenerateStore((s) => s.addTag);
  const removeTag = useGenerateStore((s) => s.removeTag);

  // The rule the next added tag gets.
  const [rule, setRule] = useState<TagCategory>("optional");

  // The combobox lists tags that aren't already in any category.
  const allInUse = useMemo(
    () => new Set([...tags.compulsory, ...tags.optional, ...tags.excluded]),
    [tags],
  );
  const offerings = useMemo(
    () => available.filter((t) => !allInUse.has(t)),
    [available, allInUse],
  );

  const handlePick = (tag: string | null) => {
    if (!tag) return;
    addTag(tag, rule);
  };

  const allChips: Array<{ tag: string; category: TagCategory }> = [
    ...tags.compulsory.map((t) => ({ tag: t, category: "compulsory" as const })),
    ...tags.optional.map((t) => ({ tag: t, category: "optional" as const })),
    ...tags.excluded.map((t) => ({ tag: t, category: "excluded" as const })),
  ];

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-3">
        <Combobox
          options={offerings}
          placeholder="Add a tag…"
          searchPlaceholder="Search tags"
          emptyMessage={available.length === 0 ? "No tags match the current filters" : "All matching tags added"}
          onSelect={handlePick}
          className="min-w-[14rem]"
        />
        <div role="group" aria-label="Rule for the next tag" className="inline-flex overflow-hidden rounded-md border border-border">
          {RULES.map((r) => (
            <button
              key={r.id}
              type="button"
              aria-pressed={rule === r.id}
              title={r.hint}
              onClick={() => setRule(r.id)}
              className={cn(
                "px-3 py-1.5 text-xs font-medium transition",
                rule === r.id ? "bg-primary text-on-primary" : "bg-surface text-text hover:bg-primary/10",
              )}
            >
              {r.label}
            </button>
          ))}
        </div>
        <span className="text-xs text-muted">{RULES.find((r) => r.id === rule)?.hint}</span>
      </div>

      {allChips.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {allChips.map(({ tag, category }) => (
            <span
              key={tag}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium",
                chipStyle[category],
              )}
            >
              <span className="font-normal opacity-80">{RULE_LABEL[category]}:</span>
              {tag}
              <button
                type="button"
                onClick={() => removeTag(tag)}
                className="inline-flex h-4 w-4 items-center justify-center rounded-full hover:bg-black/10"
                aria-label={`remove ${tag}`}
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
