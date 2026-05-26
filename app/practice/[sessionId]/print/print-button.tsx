"use client";

export function PrintButton() {
  return (
    <button
      onClick={() => window.print()}
      className="rounded-md bg-ink-900 px-4 py-2 text-sm font-medium text-white hover:bg-ink-700"
    >
      Print / Save as PDF
    </button>
  );
}
