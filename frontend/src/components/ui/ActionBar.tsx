import { type ReactNode } from "react";
import { AlertCircle } from "lucide-react";

import { Spinner } from "../../appearance/brand/Loader";

interface ActionBarProps {
  /** What the action will use: selection, counts. */
  summary: ReactNode;
  /** Why the main action is unavailable, or a warning about its result. */
  note?: string | null;
  loading?: boolean;
  /** The buttons; the main action goes last. */
  children: ReactNode;
}

/** The page's main action, pinned under the scrolling form so it is always in
 * reach, with a summary of what it will act on. */
export function ActionBar({ summary, note, loading, children }: ActionBarProps) {
  return (
    <div
      data-ui="action-bar"
      className="flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-border bg-surface px-6 py-2.5"
    >
      <div className="min-w-0 flex-1 text-sm">
        <div className="flex items-center gap-2">
          {loading && <Spinner className="h-3 w-3 flex-none text-muted" />}
          <span className="truncate">{summary}</span>
        </div>
        {note && (
          <div role="status" className="mt-0.5 flex items-center gap-1.5 text-xs font-medium text-text">
            <AlertCircle className="h-3.5 w-3.5 flex-none text-warning" aria-hidden="true" />
            {note}
          </div>
        )}
      </div>
      <div className="flex flex-wrap items-center gap-2">{children}</div>
    </div>
  );
}
