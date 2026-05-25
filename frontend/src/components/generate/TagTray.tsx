/**
 * Tag tray (spec §8.1, §7.2):
 *   - Searchable combobox adds chips into a flow-layout tray.
 *   - Two header toggles **Compulsory?** and **Exclude** drive the category at add time.
 *   - Cascade rules (spec §8.1):
 *       * Adding while Exclude is on forces Compulsory on.
 *       * Turning Compulsory off while Exclude is on also turns Exclude off.
 *   - Chip colors: compulsory blue, optional grey, excluded red.
 *
 * Each chip stays in its category until removed. Clicking the × removes it.
 */

import { useMemo, useState } from "react";
import { X } from "lucide-react";

import { cn } from "../../lib/cn";
import { useGenerateStore, type TagCategory } from "../../state/generate";
import { Combobox } from "../ui/Combobox";
import { Switch } from "../ui/Switch";

interface Props {
  available: readonly string[];
}

function categoryFromToggles(compulsory: boolean, exclude: boolean): TagCategory {
  if (exclude) return "excluded";
  if (compulsory) return "compulsory";
  return "optional";
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

  const [compulsoryOn, setCompulsoryOn] = useState(false);
  const [excludeOn, setExcludeOn] = useState(false);

  const handleCompulsoryChange = (v: boolean) => {
    setCompulsoryOn(v);
    // Spec: turning Compulsory off while Exclude is on also turns Exclude off.
    if (!v && excludeOn) setExcludeOn(false);
  };
  const handleExcludeChange = (v: boolean) => {
    setExcludeOn(v);
    // Spec: adding a chip while Exclude is on forces Compulsory on. Keep the
    // toggles in sync proactively too — clicking Exclude on flips Compulsory on.
    if (v) setCompulsoryOn(true);
  };

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
    const category = categoryFromToggles(compulsoryOn, excludeOn);
    addTag(tag, category);
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
        <ToggleRow
          label="Compulsory?"
          checked={compulsoryOn}
          onChange={handleCompulsoryChange}
        />
        <ToggleRow label="Exclude" checked={excludeOn} onChange={handleExcludeChange} />
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

function ToggleRow({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <label className="inline-flex cursor-pointer items-center gap-2 text-sm">
      <Switch checked={checked} onCheckedChange={onChange} ariaLabel={label} />
      <span>{label}</span>
    </label>
  );
}
