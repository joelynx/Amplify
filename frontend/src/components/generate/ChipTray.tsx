/** Single-category chip tray — used for Sources and Types (spec §8.1). */

import { useMemo } from "react";
import { X } from "lucide-react";

import { cn } from "../../lib/cn";
import { Combobox } from "../ui/Combobox";

interface Props {
  available: readonly string[];
  selected: readonly string[];
  onChange: (next: string[]) => void;
  placeholder?: string;
  searchPlaceholder?: string;
  emptyMessage?: string;
  className?: string;
}

export function ChipTray({
  available,
  selected,
  onChange,
  placeholder,
  searchPlaceholder,
  emptyMessage,
  className,
}: Props) {
  const offerings = useMemo(() => available.filter((o) => !selected.includes(o)), [available, selected]);

  const add = (value: string | null) => {
    if (!value) return;
    if (!selected.includes(value)) onChange([...selected, value]);
  };
  const remove = (value: string) => onChange(selected.filter((s) => s !== value));

  return (
    <div className={cn("space-y-3", className)}>
      <Combobox
        options={offerings}
        placeholder={placeholder}
        searchPlaceholder={searchPlaceholder}
        emptyMessage={emptyMessage}
        onSelect={add}
        className="min-w-[14rem]"
      />
      {selected.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {selected.map((value) => (
            <span
              key={value}
              className="inline-flex items-center gap-1.5 rounded-full border border-border bg-background px-3 py-1 text-xs font-medium"
            >
              {value}
              <button
                type="button"
                onClick={() => remove(value)}
                className="inline-flex h-4 w-4 items-center justify-center rounded-full hover:bg-surface"
                aria-label={`remove ${value}`}
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
