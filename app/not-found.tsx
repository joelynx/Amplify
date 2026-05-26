import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto max-w-2xl px-6 py-16">
      <h1 className="text-2xl font-semibold tracking-tight">Not found</h1>
      <p className="mt-2 text-sm text-ink-500">
        That page doesn&apos;t exist. Maybe it was a question that&apos;s been
        removed.
      </p>
      <div className="mt-6 flex gap-3">
        <Link
          href="/q"
          className="rounded-md bg-ink-900 px-4 py-2 text-sm font-medium text-white hover:bg-ink-700"
        >
          Browse the bank
        </Link>
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
