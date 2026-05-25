import { type ButtonHTMLAttributes, forwardRef } from "react";
import { cn } from "../../lib/cn";

type Variant = "primary" | "secondary" | "ghost" | "outline";
type Size = "sm" | "md";

const variants: Record<Variant, string> = {
  primary:
    "bg-primary text-white hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed",
  secondary:
    "bg-secondary text-white hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed",
  ghost:
    "bg-transparent hover:bg-surface text-text disabled:opacity-50 disabled:cursor-not-allowed",
  outline:
    "bg-transparent text-text border border-border hover:bg-surface disabled:opacity-50 disabled:cursor-not-allowed",
};

const sizes: Record<Size, string> = {
  sm: "h-8 px-3 text-sm",
  md: "h-10 px-4 text-sm",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "outline", size = "md", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary",
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    />
  ),
);
Button.displayName = "Button";
