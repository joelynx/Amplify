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
      className={cn(
        "relative inline-flex h-4 w-4 flex-none items-center justify-center rounded border border-border bg-background",
        state !== "unchecked" && "bg-primary border-primary",
        disabled && "opacity-50",
        className,
      )}
    >
      <input
        ref={ref}
        type="checkbox"
        checked={state === "checked"}
        disabled={disabled}
        className="absolute inset-0 cursor-pointer opacity-0 disabled:cursor-not-allowed"
        {...props}
      />
      {state === "checked" && <Check className="pointer-events-none h-3 w-3 text-white" />}
      {state === "partial" && <Minus className="pointer-events-none h-3 w-3 text-white" />}
    </span>
  ),
);
Checkbox.displayName = "Checkbox";
