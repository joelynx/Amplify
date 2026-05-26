"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { getAnonKey } from "@/lib/anon";
import type { PracticeFilters, QuestionType } from "@/lib/db/types";

type Tree = Record<string, Record<string, string[]>>;
type Mode = "random" | "diverse";
type TagState = "none" | "compulsory" | "excluded";

export function PracticeFilterForm({
  tree,
  types,
  sources,
  tags,
}: {
  tree: Tree;
  types: string[];
  sources: string[];
  tags: string[];
}) {
  const router = useRouter();
  const [selectedSubtopics, setSelectedSubtopics] = useState<Set<string>>(
    new Set()
  );
  const [selectedTypes, setSelectedTypes] = useState<Set<string>>(new Set());
  const [selectedSources, setSelectedSources] = useState<Set<string>>(new Set());
  const [tagStates, setTagStates] = useState<Map<string, TagState>>(new Map());
  const [tagSearch, setTagSearch] = useState("");
  const [treeSearch, setTreeSearch] = useState("");
  const [collapsedTopics, setCollapsedTopics] = useState<Set<string>>(new Set());
  const [collapsedBranches, setCollapsedBranches] = useState<Set<string>>(
    new Set()
  );
  const [n, setN] = useState(10);
  const [mode, setMode] = useState<Mode>("diverse");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string>("");
  const [count, setCount] = useState<number | null>(null);
  const [countLoading, setCountLoading] = useState(false);

  const topics = useMemo(() => Object.keys(tree).sort(), [tree]);

  const subtopicKey = (topic: string, branch: string, sub: string) =>
    `${topic}||${branch}||${sub}`;

  const toggleSubtopic = (key: string) => {
    setSelectedSubtopics((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const toggle = <T extends string>(
    set: Set<T>,
    setter: (s: Set<T>) => void,
    v: T
  ) => {
    const next = new Set(set);
    if (next.has(v)) next.delete(v);
    else next.add(v);
    setter(next);
  };

  function buildFilters(): PracticeFilters {
    const subs: string[] = [];
    const branches = new Set<string>();
    const tops = new Set<string>();
    for (const k of selectedSubtopics) {
      const [t, b, s] = k.split("||");
      tops.add(t);
      branches.add(b);
      subs.push(s);
    }
    const compulsory: string[] = [];
    const excluded: string[] = [];
    for (const [t, state] of tagStates) {
      if (state === "compulsory") compulsory.push(t);
      else if (state === "excluded") excluded.push(t);
    }
    return {
      topics: [...tops],
      branches: [...branches],
      subtopics: subs,
      types: [...selectedTypes] as QuestionType[],
      sources: [...selectedSources],
      in_syllabus_only: true,
      ...(compulsory.length > 0 || excluded.length > 0
        ? { tags: { compulsory, excluded } }
        : {}),
    };
  }

  function cycleTag(t: string) {
    setTagStates((prev) => {
      const next = new Map(prev);
      const cur = next.get(t) ?? "none";
      const ord: TagState[] = ["none", "compulsory", "excluded"];
      next.set(t, ord[(ord.indexOf(cur) + 1) % 3]);
      if (next.get(t) === "none") next.delete(t);
      return next;
    });
    setCount(null);
  }

  const filteredTags = useMemo(() => {
    if (!tagSearch.trim()) return tags;
    const q = tagSearch.toLowerCase();
    return tags.filter((t) => t.toLowerCase().includes(q));
  }, [tags, tagSearch]);

  // ────────────────────────────────────────────────────────────────────────
  // CheckableTree: tri-state checkboxes, cascade, search.
  // ────────────────────────────────────────────────────────────────────────

  type TriState = "empty" | "checked" | "indeterminate";

  const branchSubs = (topic: string, branch: string) => tree[topic][branch];

  const branchState = (topic: string, branch: string): TriState => {
    const subs = branchSubs(topic, branch);
    let count = 0;
    for (const s of subs) {
      if (selectedSubtopics.has(subtopicKey(topic, branch, s))) count++;
    }
    if (count === 0) return "empty";
    if (count === subs.length) return "checked";
    return "indeterminate";
  };

  const topicState = (topic: string): TriState => {
    const branches = Object.keys(tree[topic]);
    let allChecked = true;
    let anyChecked = false;
    for (const b of branches) {
      const st = branchState(topic, b);
      if (st !== "empty") anyChecked = true;
      if (st !== "checked") allChecked = false;
    }
    if (!anyChecked) return "empty";
    if (allChecked) return "checked";
    return "indeterminate";
  };

  const setBranchAll = (topic: string, branch: string, on: boolean) => {
    setSelectedSubtopics((prev) => {
      const next = new Set(prev);
      for (const s of branchSubs(topic, branch)) {
        const k = subtopicKey(topic, branch, s);
        if (on) next.add(k);
        else next.delete(k);
      }
      return next;
    });
    setCount(null);
  };

  const setTopicAll = (topic: string, on: boolean) => {
    setSelectedSubtopics((prev) => {
      const next = new Set(prev);
      for (const b of Object.keys(tree[topic])) {
        for (const s of branchSubs(topic, b)) {
          const k = subtopicKey(topic, b, s);
          if (on) next.add(k);
          else next.delete(k);
        }
      }
      return next;
    });
    setCount(null);
  };

  const toggleTopic = (topic: string) => {
    const st = topicState(topic);
    setTopicAll(topic, st !== "checked");
  };

  const toggleBranch = (topic: string, branch: string) => {
    const st = branchState(topic, branch);
    setBranchAll(topic, branch, st !== "checked");
  };

  const toggleTopicCollapse = (topic: string) => {
    setCollapsedTopics((prev) => {
      const next = new Set(prev);
      if (next.has(topic)) next.delete(topic);
      else next.add(topic);
      return next;
    });
  };

  const toggleBranchCollapse = (topic: string, branch: string) => {
    const k = `${topic}||${branch}`;
    setCollapsedBranches((prev) => {
      const next = new Set(prev);
      if (next.has(k)) next.delete(k);
      else next.add(k);
      return next;
    });
  };

  // Search-filtered visibility: hide nodes whose entire subtree has no match.
  const treeQuery = treeSearch.trim().toLowerCase();
  const subtopicMatches = (s: string) =>
    treeQuery === "" || s.toLowerCase().includes(treeQuery);
  const branchHasMatch = (topic: string, branch: string) =>
    treeQuery === "" ||
    branch.toLowerCase().includes(treeQuery) ||
    branchSubs(topic, branch).some(subtopicMatches);
  const topicHasMatch = (topic: string) =>
    treeQuery === "" ||
    topic.toLowerCase().includes(treeQuery) ||
    Object.keys(tree[topic]).some((b) => branchHasMatch(topic, b));

  // Debounced live counter — fires whenever any filter changes (~150ms idle).
  // Aborts in-flight fetches when filters change again to avoid races.
  useEffect(() => {
    const filtersNow = buildFilters();
    const handle = setTimeout(async () => {
      setCountLoading(true);
      try {
        const res = await fetch("/api/questions/count", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ filters: filtersNow }),
        });
        const json = await res.json();
        setCount(json.count ?? 0);
      } catch {
        setCount(null);
      } finally {
        setCountLoading(false);
      }
    }, 150);
    return () => clearTimeout(handle);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedSubtopics, selectedTypes, selectedSources, tagStates]);

  async function handleStart(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (selectedSubtopics.size === 0) {
      setError("Select at least one subtopic.");
      return;
    }

    setSubmitting(true);
    try {
      const res = await fetch("/api/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          filters: buildFilters(),
          n_target: n,
          anon_key: getAnonKey(),
          mode,
        }),
      });
      if (!res.ok) {
        const j = await res.json().catch(() => ({}));
        throw new Error(j.error || `HTTP ${res.status}`);
      }
      const json = await res.json();
      router.push(`/practice/${json.session_id}`);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleStart} className="flex flex-col gap-8">
      {/* Generation mode — segmented control */}
      <section>
        <h2 className="mb-3 text-sm font-medium text-ink-700">
          Generation mode
        </h2>
        <div className="inline-flex overflow-hidden rounded-md border border-ink-200">
          {(["random", "diverse"] as const).map((m) => (
            <button
              type="button"
              key={m}
              onClick={() => setMode(m)}
              className={
                "px-4 py-1.5 text-xs font-medium transition " +
                (mode === m
                  ? "bg-ink-900 text-white"
                  : "bg-white text-ink-700 hover:bg-ink-50")
              }
            >
              {m === "random" ? "Random" : "Diverse"}
            </button>
          ))}
        </div>
        <p className="mt-2 max-w-prose text-xs text-ink-500">
          {mode === "random"
            ? "Uniform random over your filters."
            : "Picks a set with maximum coverage across the concept space, not just the topic match. Uses a determinantal point process on the question embeddings."}
        </p>
      </section>

      {/* Taxonomy CheckableTree: tri-state checkboxes, cascade up/down, search. */}
      <section>
        <div className="mb-3 flex items-center justify-between gap-2">
          <h2 className="text-sm font-medium text-ink-700">Topics</h2>
          <div className="flex items-center gap-2">
            <input
              type="text"
              placeholder="Search topics…"
              value={treeSearch}
              onChange={(e) => setTreeSearch(e.target.value)}
              className="w-56 rounded-md border border-ink-200 px-2 py-1 text-xs"
            />
            {treeSearch && (
              <button
                type="button"
                onClick={() => setTreeSearch("")}
                className="text-xs text-ink-500 underline hover:text-ink-900"
              >
                clear
              </button>
            )}
            <button
              type="button"
              onClick={() => {
                setCollapsedTopics(new Set(topics));
                setCollapsedBranches(new Set());
              }}
              className="text-xs text-ink-500 underline hover:text-ink-900"
            >
              collapse all
            </button>
          </div>
        </div>

        <div className="space-y-2">
          {topics.filter(topicHasMatch).map((topic) => {
            const tSt = topicState(topic);
            const tCollapsed = collapsedTopics.has(topic) && !treeQuery;
            return (
              <div key={topic} className="rounded-md border border-ink-200">
                <div className="flex items-center gap-2 px-3 py-2">
                  <TriCheckbox state={tSt} onClick={() => toggleTopic(topic)} />
                  <button
                    type="button"
                    onClick={() => toggleTopicCollapse(topic)}
                    className="flex-1 text-left text-sm font-medium hover:text-ink-700"
                  >
                    <span className="mr-1 text-ink-400">
                      {tCollapsed ? "▸" : "▾"}
                    </span>
                    {topic}
                  </button>
                </div>

                {!tCollapsed && (
                  <div className="space-y-1 border-t border-ink-100 px-3 py-2 pl-8">
                    {Object.entries(tree[topic])
                      .sort(([a], [b]) => a.localeCompare(b))
                      .filter(([branch]) => branchHasMatch(topic, branch))
                      .map(([branch, subs]) => {
                        const bSt = branchState(topic, branch);
                        const bKey = `${topic}||${branch}`;
                        const bCollapsed =
                          collapsedBranches.has(bKey) && !treeQuery;
                        return (
                          <div key={branch}>
                            <div className="flex items-center gap-2">
                              <TriCheckbox
                                state={bSt}
                                onClick={() => toggleBranch(topic, branch)}
                              />
                              <button
                                type="button"
                                onClick={() =>
                                  toggleBranchCollapse(topic, branch)
                                }
                                className="flex-1 text-left text-xs uppercase tracking-wide text-ink-500 hover:text-ink-700"
                              >
                                <span className="mr-1 text-ink-400">
                                  {bCollapsed ? "▸" : "▾"}
                                </span>
                                {branch}
                              </button>
                            </div>
                            {!bCollapsed && (
                              <div className="ml-7 mt-1 flex flex-wrap gap-1.5">
                                {subs.filter(subtopicMatches).map((s) => {
                                  const key = subtopicKey(topic, branch, s);
                                  const active = selectedSubtopics.has(key);
                                  return (
                                    <button
                                      type="button"
                                      key={key}
                                      onClick={() => {
                                        toggleSubtopic(key);
                                        setCount(null);
                                      }}
                                      className={
                                        "rounded-full border px-2.5 py-1 text-xs transition " +
                                        (active
                                          ? "border-ink-900 bg-ink-900 text-white"
                                          : "border-ink-200 text-ink-700 hover:border-ink-400")
                                      }
                                    >
                                      {s}
                                    </button>
                                  );
                                })}
                              </div>
                            )}
                          </div>
                        );
                      })}
                  </div>
                )}
              </div>
            );
          })}
          {topics.filter(topicHasMatch).length === 0 && (
            <p className="text-sm text-ink-500">No topics match the search.</p>
          )}
        </div>
      </section>

      {/* Types */}
      {types.length > 0 && (
        <section>
          <h2 className="mb-2 text-sm font-medium text-ink-700">
            Question type
          </h2>
          <div className="flex flex-wrap gap-1.5">
            {types.map((t) => (
              <button
                type="button"
                key={t}
                onClick={() => {
                  toggle(selectedTypes, setSelectedTypes, t);
                  setCount(null);
                }}
                className={
                  "rounded-full border px-2.5 py-1 text-xs transition " +
                  (selectedTypes.has(t)
                    ? "border-ink-900 bg-ink-900 text-white"
                    : "border-ink-200 text-ink-700 hover:border-ink-400")
                }
              >
                {t}
              </button>
            ))}
          </div>
        </section>
      )}

      {/* Tags — 3-state chips (none / compulsory / excluded) */}
      {tags.length > 0 && (
        <section>
          <div className="mb-2 flex items-center justify-between gap-2">
            <h2 className="text-sm font-medium text-ink-700">Tags</h2>
            <input
              type="text"
              placeholder="Search tags…"
              value={tagSearch}
              onChange={(e) => setTagSearch(e.target.value)}
              className="w-48 rounded-md border border-ink-200 px-2 py-1 text-xs"
            />
          </div>
          <p className="mb-2 text-xs text-ink-500">
            Click once for <span className="text-brand-700 font-medium">must have</span> (blue), again for{" "}
            <span className="text-red-700 font-medium">must not have</span> (red), third click clears.
          </p>
          <div className="flex flex-wrap gap-1.5">
            {filteredTags.map((t) => {
              const state = tagStates.get(t) ?? "none";
              const cls =
                state === "compulsory"
                  ? "border-brand-600 bg-brand-50 text-brand-700"
                  : state === "excluded"
                    ? "border-red-500 bg-red-50 text-red-700 line-through"
                    : "border-ink-200 text-ink-700 hover:border-ink-400";
              const prefix =
                state === "compulsory" ? "+ " : state === "excluded" ? "− " : "";
              return (
                <button
                  type="button"
                  key={t}
                  onClick={() => cycleTag(t)}
                  className={`rounded-full border px-2.5 py-1 text-xs transition ${cls}`}
                >
                  {prefix}
                  {t}
                </button>
              );
            })}
            {filteredTags.length === 0 && (
              <span className="text-xs text-ink-400">No tags match.</span>
            )}
          </div>
        </section>
      )}

      {/* Sources */}
      {sources.length > 0 && (
        <section>
          <h2 className="mb-2 text-sm font-medium text-ink-700">Source</h2>
          <div className="flex flex-wrap gap-1.5">
            {sources.map((s) => (
              <button
                type="button"
                key={s}
                onClick={() => {
                  toggle(selectedSources, setSelectedSources, s);
                  setCount(null);
                }}
                className={
                  "rounded-full border px-2.5 py-1 text-xs transition " +
                  (selectedSources.has(s)
                    ? "border-ink-900 bg-ink-900 text-white"
                    : "border-ink-200 text-ink-700 hover:border-ink-400")
                }
              >
                {s}
              </button>
            ))}
          </div>
        </section>
      )}

      {/* Count + n_target */}
      <section className="flex flex-wrap items-center gap-4">
        <label className="text-sm">
          <span className="mr-2 text-ink-700">Questions in session</span>
          <input
            type="number"
            min={1}
            max={50}
            value={n}
            onChange={(e) => setN(Number.parseInt(e.target.value, 10) || 10)}
            className="w-20 rounded-md border border-ink-200 px-2 py-1 text-sm"
          />
        </label>
        <span
          className={
            "text-xs " +
            (countLoading ? "text-ink-400" : count === 0 ? "text-red-600" : "text-ink-700")
          }
        >
          {countLoading
            ? "counting…"
            : count !== null
              ? `${count.toLocaleString()} questions match your filters`
              : "—"}
        </span>
      </section>

      {/* Action */}
      <div className="flex flex-col gap-2">
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          type="submit"
          disabled={submitting}
          className="self-start rounded-md bg-ink-900 px-6 py-3 text-sm font-medium text-white hover:bg-ink-700 disabled:opacity-50"
        >
          {submitting ? "Starting..." : "Start practice"}
        </button>
      </div>
    </form>
  );
}

function TriCheckbox({
  state,
  onClick,
}: {
  state: "empty" | "checked" | "indeterminate";
  onClick: () => void;
}) {
  const fill =
    state === "checked"
      ? "bg-ink-900 border-ink-900 text-white"
      : state === "indeterminate"
        ? "bg-ink-200 border-ink-400 text-ink-900"
        : "border-ink-300 hover:border-ink-500";
  const glyph =
    state === "checked" ? "✓" : state === "indeterminate" ? "−" : "";
  return (
    <button
      type="button"
      onClick={onClick}
      aria-checked={state === "checked"}
      role="checkbox"
      className={`inline-flex size-4 shrink-0 items-center justify-center rounded border text-[10px] leading-none transition ${fill}`}
    >
      {glyph}
    </button>
  );
}
