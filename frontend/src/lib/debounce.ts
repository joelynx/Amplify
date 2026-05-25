import { useEffect, useState } from "react";

/** Returns `value` debounced by `delayMs`. Useful for live-count queries that
 * should wait for typing to settle (spec §7.5 / Step 4: ~150ms on filter changes). */
export function useDebounced<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = window.setTimeout(() => setDebounced(value), delayMs);
    return () => window.clearTimeout(id);
  }, [value, delayMs]);
  return debounced;
}
