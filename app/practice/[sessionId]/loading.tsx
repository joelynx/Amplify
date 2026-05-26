export default function Loading() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <div className="flex flex-col gap-6">
        <div className="h-3 w-24 animate-pulse rounded bg-ink-100" />
        <div className="space-y-3">
          <div className="h-6 w-full animate-pulse rounded bg-ink-100" />
          <div className="h-6 w-5/6 animate-pulse rounded bg-ink-100" />
          <div className="h-6 w-2/3 animate-pulse rounded bg-ink-100" />
        </div>
        <div className="h-10 w-40 animate-pulse rounded bg-ink-100" />
      </div>
    </main>
  );
}
