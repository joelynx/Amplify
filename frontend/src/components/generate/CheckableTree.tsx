/**
 * 3-level CheckableTree (Topic → Branch → Subtopic) per spec §8.1.
 *
 * State (live in the generate store) is a flat Set of leaf keys. Topic and
 * branch states are *derived* from leaf membership:
 *   - 0 leaves selected → "unchecked"
 *   - all leaves selected → "checked"
 *   - some leaves selected → "partial"
 *
 * Toggle semantics:
 *   - Click leaf: toggle that leaf only.
 *   - Click branch: select/deselect all of its subtopics in one shot.
 *   - Click topic: cascade across every subtopic under every branch.
 *
 * Search filters which leaves are *visible* but never mutates the selection
 * (spec: "filters visible leaves *without* changing selection state").
 */

import { useMemo, useState } from "react";
import { ChevronRight, Search, X } from "lucide-react";

import type { ConceptTree } from "../../lib/ipc";
import { cn } from "../../lib/cn";
import { leafKey, useGenerateStore } from "../../state/generate";
import { Checkbox } from "../ui/Checkbox";
import { Button } from "../ui/Button";

interface Props {
  tree: ConceptTree;
}

type TriState = "checked" | "unchecked" | "partial";

function deriveState(selected: Set<string>, allLeaves: string[]): TriState {
  if (allLeaves.length === 0) return "unchecked";
  let any = false;
  let all = true;
  for (const k of allLeaves) {
    if (selected.has(k)) any = true;
    else all = false;
    if (any && !all) return "partial";
  }
  return all ? "checked" : "unchecked";
}

export function CheckableTree({ tree }: Props) {
  const selected = useGenerateStore((s) => s.selectedLeaves);
  const toggleLeaf = useGenerateStore((s) => s.toggleLeaf);
  const setLeavesBulk = useGenerateStore((s) => s.setLeavesBulk);

  const [query, setQuery] = useState("");
  const [expandedTopics, setExpandedTopics] = useState<Set<string>>(new Set());
  const [expandedBranches, setExpandedBranches] = useState<Set<string>>(new Set());

  // When a query is active, auto-expand every topic + branch that contains a
  // matching leaf. The map view is much more useful that way.
  const queryLower = query.trim().toLowerCase();
  const matchesLeaf = (subtopic: string) => !queryLower || subtopic.toLowerCase().includes(queryLower);

  const visibleTree = useMemo(() => {
    if (!queryLower) return tree;
    const out: ConceptTree = {};
    for (const [topic, branches] of Object.entries(tree)) {
      for (const [branch, subs] of Object.entries(branches)) {
        const kept = subs.filter(matchesLeaf);
        if (kept.length > 0) {
          out[topic] ??= {};
          out[topic][branch] = kept;
        }
      }
    }
    return out;
  }, [tree, queryLower]);

  const topicEntries = Object.entries(visibleTree);

  const allLeavesForBranch = (topic: string, branch: string): string[] =>
    (tree[topic]?.[branch] ?? []).map((s) => leafKey(topic, branch, s));

  const allLeavesForTopic = (topic: string): string[] => {
    const branches = tree[topic] ?? {};
    return Object.entries(branches).flatMap(([b, subs]) => subs.map((s) => leafKey(topic, b, s)));
  };

  const toggleTopic = (topic: string) => {
    const leaves = allLeavesForTopic(topic);
    const state = deriveState(selected, leaves);
    setLeavesBulk(leaves, state !== "checked");
  };

  const toggleBranch = (topic: string, branch: string) => {
    const leaves = allLeavesForBranch(topic, branch);
    const state = deriveState(selected, leaves);
    setLeavesBulk(leaves, state !== "checked");
  };

  const expandTopic = (topic: string) =>
    setExpandedTopics((prev) => {
      const next = new Set(prev);
      if (next.has(topic)) next.delete(topic);
      else next.add(topic);
      return next;
    });

  const expandBranch = (key: string) =>
    setExpandedBranches((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });

  const collapseAll = () => {
    setExpandedTopics(new Set());
    setExpandedBranches(new Set());
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <div className="flex h-9 flex-1 items-center gap-2 rounded-md border border-border bg-background px-3">
          <Search className="h-4 w-4 text-muted" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter visible leaves…"
            className="flex-1 bg-transparent text-sm outline-none"
          />
          {query && (
            <button
              type="button"
              className="text-muted hover:text-text"
              onClick={() => setQuery("")}
              aria-label="Clear search"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
        <Button variant="ghost" size="sm" onClick={collapseAll}>
          Collapse leaves
        </Button>
      </div>

      <div className="max-h-[24rem] overflow-y-auto rounded-md border border-border bg-background py-1">
        {topicEntries.length === 0 && (
          <p className="px-4 py-6 text-sm text-muted">
            {queryLower ? "No leaves match." : "No taxonomy data — ingest the seed first."}
          </p>
        )}
        {topicEntries.map(([topic, branches]) => {
          const topicLeaves = allLeavesForTopic(topic);
          const topicState = deriveState(selected, topicLeaves);
          const topicOpen = queryLower !== "" || expandedTopics.has(topic);
          return (
            <div key={topic} className="px-1">
              <Row
                indent={0}
                state={topicState}
                expanded={topicOpen}
                onToggleExpand={() => expandTopic(topic)}
                onToggleCheck={() => toggleTopic(topic)}
                label={topic}
                bold
              />
              {topicOpen &&
                Object.entries(branches).map(([branch, subs]) => {
                  const branchKey = `${topic}\u0001${branch}`;
                  const branchLeaves = allLeavesForBranch(topic, branch);
                  const branchState = deriveState(selected, branchLeaves);
                  const branchOpen = queryLower !== "" || expandedBranches.has(branchKey);
                  return (
                    <div key={branch}>
                      <Row
                        indent={1}
                        state={branchState}
                        expanded={branchOpen}
                        onToggleExpand={() => expandBranch(branchKey)}
                        onToggleCheck={() => toggleBranch(topic, branch)}
                        label={branch}
                      />
                      {branchOpen &&
                        subs.map((sub) => {
                          const lk = leafKey(topic, branch, sub);
                          const isOn = selected.has(lk);
                          return (
                            <Row
                              key={sub}
                              indent={2}
                              state={isOn ? "checked" : "unchecked"}
                              onToggleCheck={() => toggleLeaf(lk, !isOn)}
                              label={sub}
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
    </div>
  );
}

interface RowProps {
  indent: 0 | 1 | 2;
  state: TriState;
  expanded?: boolean;
  onToggleExpand?: () => void;
  onToggleCheck: () => void;
  label: string;
  bold?: boolean;
}

function Row({ indent, state, expanded, onToggleExpand, onToggleCheck, label, bold }: RowProps) {
  const indentPx = ["pl-2", "pl-7", "pl-12"][indent];
  return (
    <div className={cn("flex items-center gap-2 rounded px-2 py-1 hover:bg-surface", indentPx)}>
      {onToggleExpand ? (
        <button
          type="button"
          onClick={onToggleExpand}
          className="flex h-4 w-4 flex-none items-center justify-center text-muted"
          aria-label={expanded ? "collapse" : "expand"}
        >
          <ChevronRight className={cn("h-3 w-3 transition-transform", expanded && "rotate-90")} />
        </button>
      ) : (
        <span className="h-4 w-4 flex-none" />
      )}
      <Checkbox state={state} onChange={onToggleCheck} aria-label={label} />
      <span className={cn("flex-1 truncate text-sm", bold && "font-medium")} onClick={onToggleCheck}>
        {label}
      </span>
    </div>
  );
}
