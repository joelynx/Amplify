import { type ChangeEvent } from "react";
import { Minus, Plus } from "lucide-react";
import { cn } from "../../lib/cn";

interface NumberInputProps {
  value: number;
  onChange: (n: number) => void;
  min?: number;
  max?: number;
  step?: number;
  className?: string;
  disabled?: boolean;
  ariaLabel?: string;
}

/** Spinbox: native number input flanked by - / + buttons. Clamps to [min, max]. */
export function NumberInput({
  value,
  onChange,
  min = 0,
  max = 200,
  step = 1,
  className,
  disabled,
  ariaLabel,
}: NumberInputProps) {
  const clamp = (n: number) => Math.max(min, Math.min(max, n));

  const handleInput = (e: ChangeEvent<HTMLInputElement>) => {
    const next = Number(e.target.value);
    if (Number.isFinite(next)) onChange(clamp(next));
  };

  return (
    <div
      className={cn(
        "inline-flex h-9 items-stretch overflow-hidden rounded-md border border-border bg-background",
        disabled && "opacity-50",
        className,
      )}
    >
      <button
        type="button"
        className="flex w-8 items-center justify-center text-muted hover:bg-surface disabled:cursor-not-allowed"
        onClick={() => onChange(clamp(value - step))}
        disabled={disabled || value <= min}
        aria-label="decrement"
        tabIndex={-1}
      >
        <Minus className="h-4 w-4" />
      </button>
      <input
        type="number"
        value={value}
        onChange={handleInput}
        min={min}
        max={max}
        step={step}
        disabled={disabled}
        aria-label={ariaLabel}
        className="w-16 bg-transparent text-center text-sm outline-none [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
      />
      <button
        type="button"
        className="flex w-8 items-center justify-center text-muted hover:bg-surface disabled:cursor-not-allowed"
        onClick={() => onChange(clamp(value + step))}
        disabled={disabled || value >= max}
        aria-label="increment"
        tabIndex={-1}
      >
        <Plus className="h-4 w-4" />
      </button>
    </div>
  );
}
