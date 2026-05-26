import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** clsx + tailwind-merge — the standard helper for conditional classes.
 * Ported from joelynx/Amplify@a1897a7 frontend/src/lib/cn.ts. */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
