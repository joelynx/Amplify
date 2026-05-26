"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ChevronRight, Search, X } from "lucide-react";
import { getAnonKey } from "@/lib/anon";
import { Checkbox } from "@/components/ui/Checkbox";
import { cn } from "@/lib/cn";
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
  const searchParams = useSearchParams();
  const [selectedSubtopics, setSelectedSubtopics] = useState<Set<string>>(
    () => {
      // Pre-fill from ?subs=topic||branch||sub,topic||branch||sub,...
      const raw = searchParams?.get("subs");
      if (!raw) return new Set();
      const items = raw
        .split(",")
        .map((s) => s.trim())
        .filter((s) => s.includes("||"));
      return new Set(items);
    }
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

      {/* Topics — 3-level CheckableTree adapted from Joel's spec. Single
       *  scrollable column with chevron + tri-state checkbox per row. */}
      <section>
        <div className="mb-3 flex items-center gap-2">
          <div className="flex h-9 flex-1 items-center gap-2 rounded-md border border-ink-200 bg-white px-3">
            <Search className="h-4 w-4 text-ink-400" />
            <input
              type="text"
              value={treeSearch}
              onChange={(e) => setTreeSearch(e.target.value)}
              placeholder="Filter topics…"
              className="flex-1 bg-transparent text-sm outline-none"
            />
            {treeSearch && (
              <button
                type="button"
                onClick={() => setTreeSearch("")}
                aria-label="Clear search"
                className="text-ink-400 hover:text-ink-900"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
          <button
            type="button"
            onClick={() => {
              setCollapsedTopics(new Set(topics));
              setCollapsedBranches(new Set());
            }}
            className="rounded-md border border-ink-200 px-3 py-1.5 text-xs hover:bg-ink-50"
          >
            Collapse
          </button>
        </div>

        <div className="max-h-96 overflow-y-auto rounded-md border border-ink-200 bg-white py-1">
          {topics.filter(topicHasMatch).length === 0 && (
            <p className="px-4 py-6 text-sm text-ink-500">
              {treeQuery ? "No topics match." : "No taxonomy data."}
            </p>
          )}
          {topics.filter(topicHasMatch).map((topic) => {
            const tSt = topicState(topic);
            const tOpen = treeQuery !== "" || !collapsedTopics.has(topic);
            return (
              <div key={topic} className="px-1">
                <TreeRow
                  indent={0}
                  state={tSt === "indeterminate" ? "partial" : tSt === "empty" ? "unchecked" : "checked"}
                  expanded={tOpen}
                  onToggleExpand={() => toggleTopicCollapse(topic)}
                  onToggleCheck={() => toggleTopic(topic)}
                  label={topic}
                  bold
                />
                {tOpen &&
                  Object.entries(tree[topic])
                    .sort(([a], [b]) => a.localeCompare(b))
                    .filter(([branch]) => branchHasMatch(topic, branch))
                    .map(([branch, subs]) => {
                      const bSt = branchState(topic, branch);
                      const bKey = `${topic}||${branch}`;
                      const bOpen =
                        treeQuery !== "" || !collapsedBranches.has(bKey);
                      return (
                        <div key={branch}>
                          <TreeRow
                            indent={1}
                            state={bSt === "indeterminate" ? "partial" : bSt === "empty" ? "unchecked" : "checked"}
                            expanded={bOpen}
                            onToggleExpand={() =>
                              toggleBranchCollapse(topic, branch)
                            }
                            onToggleCheck={() => toggleBranch(topic, branch)}
                            label={branch}
                          />
                          {bOpen &&
                            subs.filter(subtopicMatches).map((s) => {
                              const key = subtopicKey(topic, branch, s);
                              const isOn = selectedSubtopics.has(key);
                              return (
                                <TreeRow
                                  key={s}
                                  indent={2}
                                  state={isOn ? "checked" : "unchecked"}
                                  onToggleCheck={() => {
                                    toggleSubtopic(key);
                                    setCount(null);
                                  }}
                                  label={s}
                                />
                              );
                            })}
                        </div>
                      );
                    })}
              </div>
            );
          })}
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

      {/* Tags — combobox add + selected-only chip tray. */}
      {tags.length > 0 && (
        <section>
          <h2 className="mb-2 text-sm font-medium text-ink-700">Tags</h2>

          {/* Combobox: type to filter unselected tags; results in a dropdown. */}
          <TagCombobox
            available={tags.filter((t) => !tagStates.has(t))}
            query={tagSearch}
            setQuery={setTagSearch}
            onPick={(t) => {
              setTagStates((prev) => {
                const next = new Map(prev);
                next.set(t, "compulsory");
                return next;
              });
              setTagSearch("");
              setCount(null);
            }}
          />

          {/* Selected chips — only the ones the user has actually picked. */}
          {tagStates.size > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {[...tagStates.entries()].map(([t, state]) => {
                const cls =
                  state === "compulsory"
                    ? "border-brand-600 bg-brand-50 text-brand-700"
                    : "border-red-500 bg-red-50 text-red-700 line-through";
                const prefix = state === "compulsory" ? "+ " : "− ";
                return (
                  <span
                    key={t}
                    className={cn(
                      "inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs",
                      cls
                    )}
                  >
                    <button
                      type="button"
                      onClick={() => cycleTag(t)}
                      className="font-medium"
                      title="Click to cycle compulsory ↔ excluded"
                    >
                      {prefix}
                      {t}
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setTagStates((prev) => {
                          const next = new Map(prev);
                          next.delete(t);
                          return next;
                        });
                        setCount(null);
                      }}
                      aria-label={`remove ${t}`}
                      className="inline-flex h-4 w-4 items-center justify-center rounded-full hover:bg-black/10"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                );
              })}
            </div>
          )}
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
          {submitting
            ? mode === "diverse"
              ? "Picking diverse set with DPP…"
              : "Picking your questions…"
            : "Start practice"}
        </button>
      </div>
    </form>
  );
}

/** Combobox tag-picker — search input + dropdown of unselected tags. */
function TagCombobox({
  available,
  query,
  setQuery,
  onPick,
}: {
  available: string[];
  query: string;
  setQuery: (v: string) => void;
  onPick: (t: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const q = query.trim().toLowerCase();
  const matches = q
    ? available.filter((t) => t.toLowerCase().includes(q)).slice(0, 40)
    : available.slice(0, 40);

  return (
    <div className="relative">
      <div className="flex h-9 items-center gap-2 rounded-md border border-ink-200 bg-white px-3">
        <Search className="h-4 w-4 text-ink-400" />
        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 150)}
          placeholder={
            available.length === 0
              ? "All tags added"
              : "Add a tag — type to filter"
          }
          disabled={available.length === 0}
          className="flex-1 bg-transparent text-sm outline-none disabled:text-ink-400"
        />
        {query && (
          <button
            type="button"
            onClick={() => setQuery("")}
            aria-label="Clear"
            className="text-ink-400 hover:text-ink-900"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {open && matches.length > 0 && (
        <div className="absolute z-20 mt-1 max-h-60 w-full overflow-y-auto rounded-md border border-ink-200 bg-white py-1 shadow-lg">
          {matches.map((t) => (
            <button
              key={t}
              type="button"
              onMouseDown={(e) => {
                // mousedown beats the input's blur so the click registers
                e.preventDefault();
                onPick(t);
              }}
              className="block w-full px-3 py-1.5 text-left text-sm hover:bg-ink-50"
            >
              {t}
            </button>
          ))}
        </div>
      )}
      {open && q && matches.length === 0 && (
        <div className="absolute z-20 mt-1 w-full rounded-md border border-ink-200 bg-white px-3 py-2 text-sm text-ink-500 shadow-lg">
          No tags match.
        </div>
      )}
    </div>
  );
}

/** Indented tree row — chevron + tri-state checkbox + label.
 *  Indent 0 = topic (bold), 1 = branch, 2 = subtopic (no chevron). */
function TreeRow({
  indent,
  state,
  expanded,
  onToggleExpand,
  onToggleCheck,
  label,
  bold,
}: {
  indent: 0 | 1 | 2;
  state: "checked" | "unchecked" | "partial";
  expanded?: boolean;
  onToggleExpand?: () => void;
  onToggleCheck: () => void;
  label: string;
  bold?: boolean;
}) {
  const indentClass = ["pl-2", "pl-7", "pl-12"][indent];
  return (
    <div
      className={cn(
        "flex items-center gap-2 rounded px-2 py-1 hover:bg-ink-50",
        indentClass
      )}
    >
      {onToggleExpand ? (
        <button
          type="button"
          onClick={onToggleExpand}
          className="flex h-4 w-4 flex-none items-center justify-center text-ink-400"
          aria-label={expanded ? "collapse" : "expand"}
        >
          <ChevronRight
            className={cn(
              "h-3 w-3 transition-transform",
              expanded && "rotate-90"
            )}
          />
        </button>
      ) : (
        <span className="h-4 w-4 flex-none" />
      )}
      <Checkbox state={state} onChange={onToggleCheck} aria-label={label} />
      <span
        className={cn(
          "flex-1 cursor-pointer truncate text-sm",
          bold && "font-medium"
        )}
        onClick={onToggleCheck}
      >
        {label}
      </span>
    </div>
  );
}
