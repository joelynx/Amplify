import { useEffect, useState } from "react";

import { cn } from "../../lib/cn";

interface Props {
  /** UTC ms timestamp when the timer expires. null disables the countdown. */
  deadlineMs: number | null;
  onExpire?: () => void;
  className?: string;
}

function fmt(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  const pad = (n: number) => n.toString().padStart(2, "0");
  return h > 0 ? `${h}:${pad(m)}:${pad(sec)}` : `${m}:${pad(sec)}`;
}

export function QuizCountdown({ deadlineMs, onExpire, className }: Props) {
  const [remaining, setRemaining] = useState<number>(() =>
    deadlineMs == null ? 0 : Math.max(0, deadlineMs - Date.now()),
  );

  useEffect(() => {
    if (deadlineMs == null) return;
    const id = window.setInterval(() => {
      const r = deadlineMs - Date.now();
      setRemaining(r);
      if (r <= 0) {
        window.clearInterval(id);
        onExpire?.();
      }
    }, 500);
    return () => window.clearInterval(id);
  }, [deadlineMs, onExpire]);

  if (deadlineMs == null) return null;
  const expired = remaining <= 0;
  const lowTime = remaining > 0 && remaining < 60_000;
  return (
    <span
      className={cn(
        "rounded-md border border-border bg-background px-3 py-1 font-mono tabular-nums text-sm",
        lowTime && "border-warning text-warning",
        expired && "border-error text-error",
        className,
      )}
    >
      {fmt(remaining / 1000)}
    </span>
  );
}
