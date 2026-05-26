import Link from "next/link";

export function TopicChips({
  topics,
  active,
  preservedParams,
}: {
  topics: string[];
  active: string | null;
  preservedParams?: Record<string, string | undefined>;
}) {
  function hrefFor(topic: string | null): string {
    const params = new URLSearchParams();
    if (topic) params.set("topic", topic);
    for (const [k, v] of Object.entries(preservedParams ?? {})) {
      if (v) params.set(k, v);
    }
    const qs = params.toString();
    return qs ? `/q?${qs}` : "/q";
  }

  return (
    <div className="flex flex-wrap gap-2 text-xs">
      <Link
        href={hrefFor(null)}
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
          href={hrefFor(t)}
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
