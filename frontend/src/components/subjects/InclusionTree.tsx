/**
 * Per-topic inclusion tree for the Subjects editor (spec §8.2).
 *
 * Inverted from the Generate page's CheckableTree:
 *   - Default state is fully *checked* (everything in the topic is included).
 *   - Unchecking a branch  → `excludedBranches[topic].push(branch)`
 *   - Unchecking a subtopic → `excludedSubtopics[topic][branch].push(subtopic)`
 *
 * Branch checkbox state:
 *   - "checked"   — branch not in excludedBranches AND every subtopic included
 *   - "unchecked" — branch in excludedBranches OR every subtopic excluded
 *   - "partial"   — some subtopics excluded but branch itself not excluded
 */

import { useState } from "react";
import { ChevronRight, X } from "lucide-react";

import { cn } from "../../lib/cn";
import { Checkbox } from "../ui/Checkbox";
import { Button } from "../ui/Button";

interface Props {
  topic: string;
  /** {branch: [subtopic, ...]} for THIS topic, from get_concept_tree. */
  branches: Record<string, string[]>;
  /** branches currently excluded for this topic. */
  excludedBranches: string[];
  /** {branch: [subtopic, ...]} of excluded subtopics for this topic. */
  excludedSubtopics: Record<string, string[]>;
  onChange: (next: {
    excludedBranches: string[];
    excludedSubtopics: Record<string, string[]>;
  }) => void;
  onRemoveTopic: () => void;
}

type TriState = "checked" | "unchecked" | "partial";

function deriveBranchState(
  subtopics: readonly string[],
  branchExcluded: boolean,
  excludedSubs: readonly string[],
): TriState {
  if (branchExcluded) return "unchecked";
  const excl = new Set(excludedSubs);
  const numExcluded = subtopics.filter((s) => excl.has(s)).length;
  if (numExcluded === 0) return "checked";
  if (numExcluded === subtopics.length) return "unchecked";
  return "partial";
}

export function InclusionTree({
  topic,
  branches,
  excludedBranches,
  excludedSubtopics,
  onChange,
  onRemoveTopic,
}: Props) {
  const [open, setOpen] = useState(true);
  const branchSet = new Set(excludedBranches);

  const toggleBranch = (branch: string) => {
    const isExcluded = branchSet.has(branch);
    if (isExcluded) {
      // Re-include: drop from excluded list, clear per-subtopic exclusions too.
      const next = excludedBranches.filter((b) => b !== branch);
      const subs = { ...excludedSubtopics };
      delete subs[branch];
      onChange({ excludedBranches: next, excludedSubtopics: subs });
    } else {
      // Exclude whole branch: add to list, drop any per-subtopic noise.
      const next = [...excludedBranches, branch];
      const subs = { ...excludedSubtopics };
      delete subs[branch];
      onChange({ excludedBranches: next, excludedSubtopics: subs });
    }
  };

  const toggleSubtopic = (branch: string, sub: string) => {
    const wasExcludedByBranch = branchSet.has(branch);
    // If the parent branch is excluded, "checking" a single subtopic means
    // re-including the branch but excluding all OTHER subtopics.
    if (wasExcludedByBranch) {
      const otherSubs = (branches[branch] ?? []).filter((s) => s !== sub);
      const nextBranches = excludedBranches.filter((b) => b !== branch);
      const subs = { ...excludedSubtopics };
      if (otherSubs.length === 0) {
        delete subs[branch];
      } else {
        subs[branch] = otherSubs;
      }
      onChange({ excludedBranches: nextBranches, excludedSubtopics: subs });
      return;
    }
    const current = excludedSubtopics[branch] ?? [];
    const isOn = !current.includes(sub);
    const nextSubs = isOn ? [...current, sub] : current.filter((s) => s !== sub);
    const subs = { ...excludedSubtopics };
    if (nextSubs.length === 0) {
      delete subs[branch];
    } else {
      subs[branch] = nextSubs;
    }
    onChange({ excludedBranches, excludedSubtopics: subs });
  };

  return (
    <div className="rounded-md border border-border bg-background">
      <header className="flex items-center gap-2 px-3 py-2">
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          className="flex h-5 w-5 items-center justify-center text-muted"
          aria-label={open ? "collapse" : "expand"}
        >
          <ChevronRight className={cn("h-4 w-4 transition-transform", open && "rotate-90")} />
        </button>
        <span className="flex-1 font-medium">{topic}</span>
        <Button variant="ghost" size="sm" onClick={onRemoveTopic} aria-label={`Remove ${topic}`}>
          <X className="h-4 w-4" />
        </Button>
      </header>
      {open && (
        <div className="space-y-1 px-3 pb-3">
          {Object.keys(branches).length === 0 && (
            <p className="text-xs text-muted">No questions tagged under this topic yet.</p>
          )}
          {Object.entries(branches).map(([branch, subs]) => {
            const isBranchExcluded = branchSet.has(branch);
            const branchState = deriveBranchState(
              subs,
              isBranchExcluded,
              excludedSubtopics[branch] ?? [],
            );
            const subExclSet = new Set(excludedSubtopics[branch] ?? []);
            return (
              <div key={branch}>
                <div className="flex items-center gap-2 rounded px-2 py-1 hover:bg-surface">
                  <Checkbox
                    state={branchState}
                    onChange={() => toggleBranch(branch)}
                    aria-label={branch}
                  />
                  <span className="flex-1 text-sm font-medium">{branch}</span>
                </div>
                {!isBranchExcluded && (
                  <div className="ml-7 space-y-1">
                    {subs.map((sub) => {
                      const isOn = !subExclSet.has(sub);
                      return (
                        <div
                          key={sub}
                          className="flex items-center gap-2 rounded px-2 py-0.5 text-sm hover:bg-surface"
                        >
                          <Checkbox
                            state={isOn ? "checked" : "unchecked"}
                            onChange={() => toggleSubtopic(branch, sub)}
                            aria-label={sub}
                          />
                          <span className="flex-1 truncate">{sub}</span>
                        </div>
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
}
