import { type ReactNode, useState } from "react";
import { cn } from "../../lib/cn";

interface TooltipProps {
  content: ReactNode | null | undefined;
  children: ReactNode;
  className?: string;
}

/** Lightweight hover/focus tooltip. Renders nothing if `content` is null.
 * The bubble sits above the trigger (spec §8.1 "validation tooltips appear
 * above the offending control"). */
export function Tooltip({ content, children, className }: TooltipProps) {
  const [open, setOpen] = useState(false);
  const show = open && content != null && content !== "";
  return (
    <span
      className="relative inline-flex"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onFocus={() => setOpen(true)}
      onBlur={() => setOpen(false)}
    >
      {children}
      {show && (
        <span
          role="tooltip"
          className={cn(
            "amplify-tooltip pointer-events-none absolute left-1/2 bottom-full mb-2 -translate-x-1/2",
            "whitespace-nowrap rounded-md bg-text px-2 py-1 text-xs font-medium text-background shadow-lg",
            className,
          )}
        >
          {content}
        </span>
      )}
    </span>
  );
}
