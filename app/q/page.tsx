import Link from "next/link";
import { getServerSupabase } from "@/lib/supabase/server";
import { LatexBlock } from "@/components/latex-block";
import { TopicChips } from "./topic-chips";

const PAGE_SIZE = 20;

function sourceHref(
  source: string | null,
  topic: string | undefined,
  type: string | undefined
): string {
  const params = new URLSearchParams();
  if (source) params.set("source", source);
  if (topic) params.set("topic", topic);
  if (type) params.set("type", type);
  const qs = params.toString();
  return qs ? `/q?${qs}` : "/q";
}

type SearchParams = Promise<{
  topic?: string;
  type?: string;
  source?: string;
  page?: string;
}>;

export default async function BrowsePage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const sp = await searchParams;
  const page = Math.max(1, Number.parseInt(sp.page ?? "1", 10) || 1);
  const offset = (page - 1) * PAGE_SIZE;

  const supabase = await getServerSupabase();

  let q = supabase
    .from("questions")
    .select("id, topic, branch, subtopic, latexcode, type, source", {
      count: "exact",
    })
    .order("id");

  if (sp.topic) q = q.eq("topic", sp.topic);
  if (sp.type) q = q.eq("type", sp.type);
  if (sp.source) q = q.eq("source", sp.source);

  const { data: rows, count } = await q.range(
    offset,
    offset + PAGE_SIZE - 1
  );

  // For the topic chip strip + source filter.
  const { data: allMeta } = await supabase
    .from("questions")
    .select("topic, source");
  const topicSet = new Set((allMeta ?? []).map((t) => t.topic as string));
  const topics = [...topicSet].sort();
  const sourceSet = new Set(
    (allMeta ?? [])
      .map((t) => t.source as string | null)
      .filter((s): s is string => !!s)
  );
  const sources = [...sourceSet].sort();

  const totalPages = Math.max(1, Math.ceil((count ?? 0) / PAGE_SIZE));

  const baseParams = new URLSearchParams();
  if (sp.topic) baseParams.set("topic", sp.topic);
  if (sp.type) baseParams.set("type", sp.type);
  if (sp.source) baseParams.set("source", sp.source);
  const pageHref = (p: number) => {
    const params = new URLSearchParams(baseParams);
    params.set("page", p.toString());
    return `/q?${params.toString()}`;
  };

  return (
    <main className="mx-auto max-w-4xl px-6 py-10">
      <div className="mb-6 flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">
            Browse the bank
          </h1>
          <p className="mt-1 text-sm text-ink-500">
            {count ?? 0} curated questions. Every one is a permalink.
          </p>
        </div>
      </div>

      <TopicChips
        topics={topics}
        active={sp.topic ?? null}
        preservedParams={{ source: sp.source, type: sp.type }}
      />

      {sources.length > 0 && (
        <div className="mt-3">
          <div className="mb-1 text-xs font-medium uppercase tracking-wider text-ink-500">
            Source
          </div>
          <div className="flex flex-wrap gap-1.5">
            <Link
              href={sourceHref(null, sp.topic, sp.type)}
              className={
                "rounded-full border px-2.5 py-1 text-xs " +
                (!sp.source
                  ? "border-ink-900 bg-ink-900 text-white"
                  : "border-ink-200 text-ink-700 hover:border-ink-400")
              }
            >
              All
            </Link>
            {sources.slice(0, 24).map((s) => (
              <Link
                key={s}
                href={sourceHref(s, sp.topic, sp.type)}
                className={
                  "rounded-full border px-2.5 py-1 text-xs " +
                  (sp.source === s
                    ? "border-ink-900 bg-ink-900 text-white"
                    : "border-ink-200 text-ink-700 hover:border-ink-400")
                }
              >
                {s.startsWith("user:") ? `from ${s.slice(5).split("@")[0]}` : s}
              </Link>
            ))}
          </div>
        </div>
      )}

      <ul className="mt-6 flex flex-col gap-3">
        {(rows ?? []).map((r) => (
          <li
            key={r.id}
            className="rounded-md border border-ink-200 p-4 hover:border-ink-400"
          >
            <Link href={`/q/${r.id}`} className="block">
              <div className="mb-1 flex flex-wrap items-center gap-2 text-xs text-ink-500">
                <span className="rounded-full bg-ink-100 px-2 py-0.5 text-ink-700">
                  {r.topic}
                </span>
                <span>›</span>
                <span>{r.branch}</span>
                <span>›</span>
                <span>{r.subtopic}</span>
                <span className="ml-auto">{r.source}</span>
              </div>
              <div className="line-clamp-2 text-sm">
                <LatexBlock src={r.latexcode} />
              </div>
            </Link>
          </li>
        ))}
        {(rows ?? []).length === 0 && (
          <li className="rounded-md border border-ink-200 bg-ink-50 p-6 text-sm text-ink-500">
            No questions match the current filters.
          </li>
        )}
      </ul>

      {/* Pagination */}
      {totalPages > 1 && (
        <nav className="mt-8 flex items-center justify-between text-sm">
          {page > 1 ? (
            <Link
              href={pageHref(page - 1)}
              className="rounded-md border border-ink-200 px-3 py-1 hover:bg-ink-50"
            >
              ← Prev
            </Link>
          ) : (
            <span />
          )}
          <span className="text-ink-500">
            Page {page} of {totalPages}
          </span>
          {page < totalPages ? (
            <Link
              href={pageHref(page + 1)}
              className="rounded-md border border-ink-200 px-3 py-1 hover:bg-ink-50"
            >
              Next →
            </Link>
          ) : (
            <span />
          )}
        </nav>
      )}
    </main>
  );
}
