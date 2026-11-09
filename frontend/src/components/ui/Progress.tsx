import { cn } from "../../lib/cn";

interface ProgressProps {
  /** 0–1. */
  value: number;
  className?: string;
  /** Bar colour class; defaults to the primary colour. */
  barClassName?: string;
  label?: string;
}

/** A progress bar the chrome slot can skin (data-ui="progress" / "progress-bar"). */
export function Progress({ value, className, barClassName, label }: ProgressProps) {
  const pct = Math.round(Math.max(0, Math.min(1, value)) * 100);
  return (
    <div
      data-ui="progress"
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={pct}
      aria-label={label}
      className={cn("h-1.5 w-full overflow-hidden rounded-full bg-border", className)}
    >
      <div data-ui="progress-bar" className={cn("h-full rounded-full bg-primary", barClassName)} style={{ width: `${pct}%` }} />
    </div>
  );
}
