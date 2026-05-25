import { useEffect, useMemo, useRef, useState } from "react";
import { ChevronDown, Search, X } from "lucide-react";
import { cn } from "../../lib/cn";

interface ComboboxProps {
  options: readonly string[];
  value?: string | null;
  /** Called when the user picks an option (or null when clearable + cleared). */
  onSelect: (value: string | null) => void;
  placeholder?: string;
  searchPlaceholder?: string;
  emptyMessage?: string;
  /** Shown as the first row above the filtered options — useful for "(Any subject)" sentinels. */
  sentinel?: string;
  /** Allow the user to clear the selection with an X button. */
  clearable?: boolean;
  disabled?: boolean;
  className?: string;
}

/**
 * Searchable combobox. Single-select. Keyboard: arrow keys move highlight,
 * Enter selects, Escape closes. Click outside closes.
 *
 * Deliberately hand-rolled rather than pulled from an a11y library — the spec's
 * UI surface is tightly tailored (sentinels, themed tooltip, etc.) and avoiding
 * a heavy dep keeps the bundle small.
 */
export function Combobox({
  options,
  value,
  onSelect,
  placeholder = "Select…",
  searchPlaceholder = "Search…",
  emptyMessage = "No matches",
  sentinel,
  clearable,
  disabled,
  className,
}: ComboboxProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [highlight, setHighlight] = useState(0);
  const rootRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const filtered = useMemo(() => {
    if (!query) return options;
    const q = query.toLowerCase();
    return options.filter((o) => o.toLowerCase().includes(q));
  }, [options, query]);

  const rows = useMemo(() => {
    return sentinel ? [sentinel, ...filtered] : [...filtered];
  }, [filtered, sentinel]);

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false);
    };
    window.addEventListener("mousedown", handler);
    return () => window.removeEventListener("mousedown", handler);
  }, [open]);

  useEffect(() => {
    if (open) {
      setHighlight(0);
      // focus search field next tick after popup renders
      setTimeout(() => inputRef.current?.focus(), 0);
    } else {
      setQuery("");
    }
  }, [open]);

  const choose = (label: string) => {
    if (sentinel && label === sentinel) {
      onSelect(null);
    } else {
      onSelect(label);
    }
    setOpen(false);
  };

  return (
    <div ref={rootRef} className={cn("relative inline-block", className)}>
      <button
        type="button"
        disabled={disabled}
        onClick={() => !disabled && setOpen((o) => !o)}
        className={cn(
          "flex h-9 w-full items-center justify-between gap-2 rounded-md border border-border bg-background px-3 text-left text-sm",
          "hover:bg-surface disabled:cursor-not-allowed disabled:opacity-50",
          "focus:outline-none focus-visible:ring-2 focus-visible:ring-primary",
        )}
      >
        <span className={cn(!value && "text-muted")}>{value || placeholder}</span>
        <span className="flex items-center gap-1">
          {clearable && value && (
            <X
              className="h-4 w-4 text-muted hover:text-text"
              role="button"
              onClick={(e) => {
                e.stopPropagation();
                onSelect(null);
              }}
            />
          )}
          <ChevronDown className="h-4 w-4 text-muted" />
        </span>
      </button>

      {open && (
        <div className="absolute z-30 mt-1 w-full min-w-[14rem] rounded-md border border-border bg-background shadow-lg">
          <div className="flex items-center gap-2 border-b border-border px-2">
            <Search className="h-4 w-4 text-muted" />
            <input
              ref={inputRef}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={searchPlaceholder}
              className="h-8 flex-1 bg-transparent text-sm outline-none"
              onKeyDown={(e) => {
                if (e.key === "ArrowDown") {
                  e.preventDefault();
                  setHighlight((h) => Math.min(rows.length - 1, h + 1));
                } else if (e.key === "ArrowUp") {
                  e.preventDefault();
                  setHighlight((h) => Math.max(0, h - 1));
                } else if (e.key === "Enter") {
                  e.preventDefault();
                  if (rows[highlight] !== undefined) choose(rows[highlight]);
                } else if (e.key === "Escape") {
                  setOpen(false);
                }
              }}
            />
          </div>
          <ul className="max-h-64 overflow-y-auto py-1">
            {rows.length === 0 && (
              <li className="px-3 py-2 text-sm text-muted">{emptyMessage}</li>
            )}
            {rows.map((label, i) => {
              const isSentinel = sentinel && label === sentinel;
              const isHi = i === highlight;
              return (
                <li
                  key={label}
                  className={cn(
                    "cursor-pointer px-3 py-1.5 text-sm",
                    isHi && "bg-surface",
                    isSentinel && "text-muted italic",
                    value === label && !isSentinel && "font-semibold",
                  )}
                  onMouseEnter={() => setHighlight(i)}
                  onMouseDown={(e) => {
                    e.preventDefault();
                    choose(label);
                  }}
                >
                  {label}
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
