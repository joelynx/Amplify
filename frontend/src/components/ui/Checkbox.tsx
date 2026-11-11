import { type InputHTMLAttributes, forwardRef } from "react";
import { Check, Minus } from "lucide-react";
import { cn } from "../../lib/cn";

interface CheckboxProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type" | "checked"> {
  /** "checked" | "unchecked" | "partial" — partial renders a dash (tri-state). */
  state?: "checked" | "unchecked" | "partial";
}

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  ({ state = "unchecked", className, disabled, ...props }, ref) => (
    <span
      data-ui="checkbox"
      className={cn(
        "relative inline-flex h-4 w-4 flex-none items-center justify-center rounded border border-border bg-background",
        "focus-within:ring-2 focus-within:ring-primary focus-within:ring-offset-1",
        state !== "unchecked" && "bg-primary border-primary",
        disabled && "opacity-50",
        className,
      )}
    >
      <input
        ref={(el) => {
          // Partial is exposed as the native indeterminate state ("mixed").
          if (el) el.indeterminate = state === "partial";
          if (typeof ref === "function") ref(el);
          else if (ref) ref.current = el;
        }}
        type="checkbox"
        checked={state === "checked"}
        disabled={disabled}
        className="absolute inset-0 cursor-pointer opacity-0 disabled:cursor-not-allowed"
        {...props}
      />
      {state === "checked" && <Check className="pointer-events-none h-3 w-3 text-on-primary" />}
      {state === "partial" && <Minus className="pointer-events-none h-3 w-3 text-on-primary" />}
    </span>
  ),
);
Checkbox.displayName = "Checkbox";
