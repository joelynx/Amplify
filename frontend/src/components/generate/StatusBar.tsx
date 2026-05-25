import { Loader2 } from "lucide-react";
import { cn } from "../../lib/cn";

interface Props {
  count: number | null;
  loading: boolean;
  error?: string | null;
}

/** Bottom status line — live "N questions match" message (spec §7.5 / §8.1). */
export function StatusBar({ count, loading, error }: Props) {
  return (
    <div
      className={cn(
        "flex h-8 items-center gap-2 border-t border-border bg-surface px-4 text-xs",
        error && "text-error",
      )}
    >
      {loading && <Loader2 className="h-3 w-3 animate-spin text-muted" />}
      {error ? (
        <span>{error}</span>
      ) : count === null ? (
        <span className="text-muted">Compose your filters above…</span>
      ) : (
        <span>
          <span className="font-semibold">{count.toLocaleString()}</span> question{count === 1 ? "" : "s"} match your current filters
        </span>
      )}
    </div>
  );
}
