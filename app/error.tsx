"use client";

import Link from "next/link";
import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("App error:", error);
  }, [error]);

  return (
    <main className="mx-auto max-w-2xl px-6 py-16">
      <h1 className="text-2xl font-semibold tracking-tight">Something broke</h1>
      <p className="mt-2 text-sm text-ink-500">
        We logged it. If you&apos;re a developer, check the browser console for
        details.
      </p>
      {error.digest && (
        <p className="mt-1 font-mono text-xs text-ink-400">
          ref: {error.digest}
        </p>
      )}
      <div className="mt-6 flex gap-3">
        <button
          onClick={reset}
          className="rounded-md bg-ink-900 px-4 py-2 text-sm font-medium text-white hover:bg-ink-700"
        >
          Try again
        </button>
        <Link
          href="/"
          className="rounded-md border border-ink-200 px-4 py-2 text-sm font-medium hover:bg-ink-50"
        >
          Home
        </Link>
      </div>
    </main>
  );
}
