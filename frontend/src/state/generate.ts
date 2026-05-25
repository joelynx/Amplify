/**
 * Zustand store for the Generate-form draft (spec §8.1).
 *
 * Tree state is stored as a flat Set of `"topic||branch||subtopic"` leaf keys.
 * Parent (topic/branch) checkbox states are derived from the leaf set so the
 * spec's "deepest non-empty level" filter rule and the "fully-checked parent"
 * UI state stay in sync without duplicate sources of truth.
 */

import { create } from "zustand";

import type { ConceptTree, Filters, OutputSettings, TagFilters, TemplatePayload } from "../lib/ipc";

export type SolutionsValue =
  | "none"
  | "appendix"
  | "interleaved"
  | "outline_appendix"
  | "outline_interleaved";

export type TagCategory = "compulsory" | "optional" | "excluded";

const LEAF_SEP = "\u0001"; // unicode SOH — won't collide with any human text

export const leafKey = (topic: string, branch: string, subtopic: string): string =>
  `${topic}${LEAF_SEP}${branch}${LEAF_SEP}${subtopic}`;

export const parseLeaf = (key: string): { topic: string; branch: string; subtopic: string } => {
  const [topic, branch, subtopic] = key.split(LEAF_SEP);
  return { topic, branch, subtopic };
};

export interface GenerateDraft {
  templateName: string | null;
  subject: string | null;

  selectedLeaves: Set<string>;

  tags: Record<TagCategory, string[]>;
  sources: string[];
  types: string[];

  nQuestions: number;
  reuseQuestions: boolean;
  includeSources: boolean;
  solutions: SolutionsValue;
  minDifficulty: number;
  inSyllabusOnly: boolean;
  saveDirectory: string | null;
}

interface GenerateState extends GenerateDraft {
  // --- mutators -------------------------------------------------------
  setTemplate: (name: string | null) => void;
  setSubject: (name: string | null) => void;

  toggleLeaf: (key: string, checked: boolean) => void;
  setLeavesBulk: (keys: string[], checked: boolean) => void;
  clearLeaves: () => void;

  addTag: (tag: string, category: TagCategory) => void;
  removeTag: (tag: string) => void;
  reclassifyTag: (tag: string, category: TagCategory) => void;
  clearTags: () => void;

  setSources: (sources: string[]) => void;
  setTypes: (types: string[]) => void;

  setNQuestions: (n: number) => void;
  setReuseQuestions: (v: boolean) => void;
  setIncludeSources: (v: boolean) => void;
  setSolutions: (v: SolutionsValue) => void;
  setMinDifficulty: (n: number) => void;
  setInSyllabusOnly: (v: boolean) => void;
  setSaveDirectory: (path: string | null) => void;
}

const initialDraft: GenerateDraft = {
  templateName: null,
  subject: null,
  selectedLeaves: new Set(),
  tags: { compulsory: [], optional: [], excluded: [] },
  sources: [],
  types: [],
  nQuestions: 10,
  reuseQuestions: false,
  includeSources: true,
  solutions: "none",
  minDifficulty: 0,
  inSyllabusOnly: true,
  saveDirectory: null,
};

function removeFromAll(tags: Record<TagCategory, string[]>, tag: string): Record<TagCategory, string[]> {
  return {
    compulsory: tags.compulsory.filter((t) => t !== tag),
    optional: tags.optional.filter((t) => t !== tag),
    excluded: tags.excluded.filter((t) => t !== tag),
  };
}

export const useGenerateStore = create<GenerateState>((set) => ({
  ...initialDraft,

  setTemplate: (name) => set({ templateName: name }),

  // Subject change clears tree + tag trays per spec §8.1 (the subject's concept
  // tree may be entirely different from the previous one).
  setSubject: (name) =>
    set({
      subject: name,
      selectedLeaves: new Set(),
      tags: { compulsory: [], optional: [], excluded: [] },
    }),

  toggleLeaf: (key, checked) =>
    set((s) => {
      const next = new Set(s.selectedLeaves);
      if (checked) next.add(key);
      else next.delete(key);
      return { selectedLeaves: next };
    }),
  setLeavesBulk: (keys, checked) =>
    set((s) => {
      const next = new Set(s.selectedLeaves);
      for (const k of keys) {
        if (checked) next.add(k);
        else next.delete(k);
      }
      return { selectedLeaves: next };
    }),
  clearLeaves: () => set({ selectedLeaves: new Set() }),

  addTag: (tag, category) =>
    set((s) => {
      if (s.tags[category].includes(tag)) return s;
      const cleaned = removeFromAll(s.tags, tag);
      cleaned[category] = [...cleaned[category], tag];
      return { tags: cleaned };
    }),
  removeTag: (tag) => set((s) => ({ tags: removeFromAll(s.tags, tag) })),
  reclassifyTag: (tag, category) =>
    set((s) => {
      const cleaned = removeFromAll(s.tags, tag);
      cleaned[category] = [...cleaned[category], tag];
      return { tags: cleaned };
    }),
  clearTags: () => set({ tags: { compulsory: [], optional: [], excluded: [] } }),

  setSources: (sources) => set({ sources }),
  setTypes: (types) => set({ types }),

  setNQuestions: (n) => set({ nQuestions: Math.max(1, Math.min(200, Math.floor(n))) }),
  setReuseQuestions: (v) => set({ reuseQuestions: v }),
  setIncludeSources: (v) => set({ includeSources: v }),
  setSolutions: (v) => set({ solutions: v }),
  setMinDifficulty: (n) => set({ minDifficulty: Math.max(0, Math.min(20, n)) }),
  setInSyllabusOnly: (v) => set({ inSyllabusOnly: v }),
  setSaveDirectory: (path) => set({ saveDirectory: path }),
}));

/** Convert the form draft into the `Filters` shape consumed by IPC.
 * The selected-leaves Set is unrolled into a flat list of subtopic names
 * (spec §7.2's "deepest non-empty rule" handles the rest). */
export function draftToFilters(draft: GenerateDraft): Filters {
  const subtopics = Array.from(draft.selectedLeaves).map((key) => parseLeaf(key).subtopic);
  const tags: TagFilters = {
    compulsory: draft.tags.compulsory,
    optional: draft.tags.optional,
    excluded: draft.tags.excluded,
  };
  return {
    subject: draft.subject,
    subtopics,
    sources: draft.sources,
    types: draft.types,
    tags,
    min_difficulty: draft.minDifficulty,
    reuse_questions: draft.reuseQuestions,
    in_syllabus_only: draft.inSyllabusOnly,
  };
}

/** Output-side settings the Python backend reads when assembling the PDF. */
export function draftToOutputSettings(draft: GenerateDraft): OutputSettings {
  return {
    n_questions: draft.nQuestions,
    reuse_questions: draft.reuseQuestions,
    include_sources: draft.includeSources,
    solutions: draft.solutions,
    min_difficulty: draft.minDifficulty,
    in_syllabus_only: draft.inSyllabusOnly,
    save_directory: draft.saveDirectory,
    template_name: draft.templateName,
  };
}

// ---- Template (de)serialization ----------------------------------------

/** Collapse the form draft into the JSON shape saved in the `templates` table.
 * Subtopic names alone are stored (taxonomy lookups happen on load against the
 * live concept tree). */
export function draftToTemplate(draft: GenerateDraft, name: string): TemplatePayload {
  const subtopics = Array.from(new Set(
    Array.from(draft.selectedLeaves).map((k) => parseLeaf(k).subtopic),
  )).sort();
  return {
    name,
    subject: draft.subject,
    topic_list: [],
    branch_list: [],
    subtopic_list: subtopics,
    type_list: [...draft.types].sort(),
    source_list: [...draft.sources].sort(),
    tag_list: {
      compulsory: [...draft.tags.compulsory].sort(),
      optional: [...draft.tags.optional].sort(),
      excluded: [...draft.tags.excluded].sort(),
    },
    n_questions: draft.nQuestions,
    reuse_questions: draft.reuseQuestions,
    include_sources: draft.includeSources,
    in_syllabus_only: draft.inSyllabusOnly,
    min_difficulty: draft.minDifficulty,
    save_directory: draft.saveDirectory,
    solutions: draft.solutions,
  };
}

/** Reconstruct the leaf-key set from a template's `subtopic_list` using the
 * current concept tree to find each subtopic's `(topic, branch)` parent.
 *
 * If a subtopic name appears under multiple branches (rare in practice), every
 * occurrence is included — round-trip is then necessarily lossy, but inclusive
 * matches user intent better than dropping the entry. */
export function templateSubtopicsToLeaves(
  subtopics: readonly string[],
  tree: ConceptTree,
): Set<string> {
  const want = new Set(subtopics);
  const out = new Set<string>();
  for (const [topic, branches] of Object.entries(tree)) {
    for (const [branch, subs] of Object.entries(branches)) {
      for (const sub of subs) {
        if (want.has(sub)) out.add(leafKey(topic, branch, sub));
      }
    }
  }
  return out;
}

/** Compare a draft against a saved template's payload for the spec's
 * "Save Template greys when payload exactly matches" rule (§8.1). */
export function draftEqualsTemplate(draft: GenerateDraft, t: TemplatePayload): boolean {
  const a = draftToTemplate(draft, t.name);
  return JSON.stringify(a) === JSON.stringify(t);
}
