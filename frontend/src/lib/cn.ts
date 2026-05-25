import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** clsx + tailwind-merge — the standard helper for conditional classes. */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
