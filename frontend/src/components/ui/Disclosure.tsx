import { useId, useState, type ReactNode } from "react";
import { ChevronRight } from "lucide-react";

import { setPref, usePref } from "../../appearance/prefs";
import { cn } from "../../lib/cn";

interface DisclosureProps {
  title: string;
  /** Shown beside the title while closed: what is set inside. */
  summary?: ReactNode;
  /** Remember open / closed across restarts under this UI_PREFS key. */
  prefKey?: string;
  defaultOpen?: boolean;
  className?: string;
  children: ReactNode;
}

/** A card whose body is collapsed until asked for: optional settings that
 * should not sit between the student and the page's main action. */
export function Disclosure({ title, summary, prefKey, defaultOpen = false, className, children }: DisclosureProps) {
  const bodyId = useId();
  const stored = usePref<boolean | null>(prefKey ?? "", null);
  const [local, setLocal] = useState(defaultOpen);
  const open = prefKey ? (stored ?? defaultOpen) : local;

  const toggle = () => {
    if (prefKey) setPref(prefKey, !open);
    else setLocal(!open);
  };

  return (
    <section data-ui="card" className={cn("rounded-lg border border-border bg-surface shadow-sm", className)}>
      <button
        type="button"
        aria-expanded={open}
        aria-controls={bodyId}
        onClick={toggle}
        className="flex w-full items-center gap-2 rounded-lg px-4 py-3 text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-primary"
      >
        <ChevronRight className={cn("h-4 w-4 flex-none text-muted transition-transform", open && "rotate-90")} />
        <span data-ui="card-title" className="text-sm font-semibold uppercase tracking-wide text-muted">
          {title}
        </span>
        {!open && summary && <span className="min-w-0 flex-1 truncate text-right text-sm text-muted">{summary}</span>}
      </button>
      {open && (
        <div id={bodyId} className="px-4 pb-4">
          {children}
        </div>
      )}
    </section>
  );
}
