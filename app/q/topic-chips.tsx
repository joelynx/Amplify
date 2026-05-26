import Link from "next/link";

export function TopicChips({
  topics,
  active,
}: {
  topics: string[];
  active: string | null;
}) {
  return (
    <div className="flex flex-wrap gap-2 text-xs">
      <Link
        href="/q"
        className={
          "rounded-full border px-2.5 py-1 " +
          (active === null
            ? "border-ink-900 bg-ink-900 text-white"
            : "border-ink-200 hover:bg-ink-50")
        }
      >
        All
      </Link>
      {topics.map((t) => (
        <Link
          key={t}
          href={`/q?topic=${encodeURIComponent(t)}`}
          className={
            "rounded-full border px-2.5 py-1 " +
            (active === t
              ? "border-ink-900 bg-ink-900 text-white"
              : "border-ink-200 hover:bg-ink-50")
          }
        >
          {t}
        </Link>
      ))}
    </div>
  );
}
