/**
 * Zustand store for the Generate-form draft (spec §8.1).
 *
 * Tree state is stored as a flat Set of `"topic||branch||subtopic"` leaf keys.
 * Parent (topic/branch) checkbox states are derived from the leaf set so the
 * spec's "deepest non-empty level" filter rule and the "fully-checked parent"
 * UI state stay in sync without duplicate sources of truth.
 */

import { create } from "zustand";

import type { Filters, TagFilters } from "../lib/ipc";

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
