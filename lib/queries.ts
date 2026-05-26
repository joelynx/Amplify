import type { SupabaseClient } from "@supabase/supabase-js";
import type { PracticeFilters } from "./db/types";
import { dppGreedyMAP, diversityScore } from "./dpp";

const EMBEDDING_MODEL = "gemini-embedding-001";
const CANDIDATE_POOL_SIZE = 500;

// Apply a PracticeFilters payload to a Supabase questions query.
// Returns a builder that callers can chain further (count, range, select).
export function applyFilters(
  db: SupabaseClient,
  filters: PracticeFilters
) {
  let q = db.from("questions").select("*", { count: "exact" });

  if (filters.subtopics && filters.subtopics.length > 0) {
    q = q.in("subtopic", filters.subtopics);
  } else if (filters.branches && filters.branches.length > 0) {
    q = q.in("branch", filters.branches);
  } else if (filters.topics && filters.topics.length > 0) {
    q = q.in("topic", filters.topics);
  }

  if (filters.types && filters.types.length > 0) {
    q = q.in("type", filters.types);
  }

  if (filters.sources && filters.sources.length > 0) {
    q = q.in("source", filters.sources);
  }

  if (typeof filters.min_difficulty === "number") {
    q = q.gte("difficulty_rating", filters.min_difficulty);
  }

  if (filters.in_syllabus_only) {
    q = q.eq("in_syllabus", true);
  }

  return q;
}

// Resolve a question-id whitelist/blacklist from compulsory/optional/excluded
// tag constraints. Returns null if no tag constraints were specified.
async function resolveTagConstraints(
  db: SupabaseClient,
  tags?: PracticeFilters["tags"]
): Promise<{
  allowIds?: number[];
  denyIds?: number[];
  emptyAllow?: boolean;
} | null> {
  if (!tags) return null;
  const compulsory = tags.compulsory ?? [];
  const optional = tags.optional ?? [];
  const excluded = tags.excluded ?? [];

  if (compulsory.length === 0 && optional.length === 0 && excluded.length === 0)
    return null;

  // Reject contradictory selections.
  const compSet = new Set(compulsory);
  for (const e of excluded) {
    if (compSet.has(e)) {
      throw new Error(
        `Tag "${e}" is both compulsory and excluded — pick one.`
      );
    }
  }

  let allowIds: number[] | undefined;

  if (compulsory.length > 0) {
    const { data } = await db
      .from("question_tags")
      .select("question_id, tag")
      .in("tag", compulsory);
    const seen = new Map<number, Set<string>>();
    for (const r of data ?? []) {
      const row = r as { question_id: number; tag: string };
      if (!seen.has(row.question_id)) seen.set(row.question_id, new Set());
      seen.get(row.question_id)!.add(row.tag);
    }
    allowIds = [...seen.entries()]
      .filter(([, t]) => t.size === compulsory.length)
      .map(([qid]) => qid);
  }

  if (optional.length > 0) {
    const { data } = await db
      .from("question_tags")
      .select("question_id")
      .in("tag", optional);
    const optIds = new Set(
      (data ?? []).map((r) => (r as { question_id: number }).question_id)
    );
    allowIds =
      allowIds === undefined
        ? [...optIds]
        : allowIds.filter((id) => optIds.has(id));
  }

  let denyIds: number[] | undefined;
  if (excluded.length > 0) {
    const { data } = await db
      .from("question_tags")
      .select("question_id")
      .in("tag", excluded);
    denyIds = [
      ...new Set(
        (data ?? []).map((r) => (r as { question_id: number }).question_id)
      ),
    ];
  }

  const emptyAllow = allowIds !== undefined && allowIds.length === 0;
  return { allowIds, denyIds, emptyAllow };
}

function applyFiltersIds(db: SupabaseClient, filters: PracticeFilters) {
  let q = db.from("questions").select("id", { count: "exact" });
  if (filters.subtopics && filters.subtopics.length > 0) {
    q = q.in("subtopic", filters.subtopics);
  } else if (filters.branches && filters.branches.length > 0) {
    q = q.in("branch", filters.branches);
  } else if (filters.topics && filters.topics.length > 0) {
    q = q.in("topic", filters.topics);
  }
  if (filters.types?.length) q = q.in("type", filters.types);
  if (filters.sources?.length) q = q.in("source", filters.sources);
  if (typeof filters.min_difficulty === "number")
    q = q.gte("difficulty_rating", filters.min_difficulty);
  if (filters.in_syllabus_only) q = q.eq("in_syllabus", true);
  return q;
}

// Count questions matching the given filters (including tag constraints).
export async function countMatchingQuestions(
  db: SupabaseClient,
  filters: PracticeFilters
): Promise<number> {
  const tagConstraints = await resolveTagConstraints(db, filters.tags);
  if (tagConstraints?.emptyAllow) return 0;

  let q = applyFiltersIds(db, filters);
  if (tagConstraints?.allowIds) {
    q = q.in("id", tagConstraints.allowIds);
  }
  if (tagConstraints?.denyIds && tagConstraints.denyIds.length > 0) {
    q = q.not("id", "in", `(${tagConstraints.denyIds.join(",")})`);
  }
  const { count, error } = await q.limit(1);
  if (error) throw error;
  return count ?? 0;
}

// Pick N random question IDs matching the filters.
// We fetch up to CANDIDATE_POOL_SIZE matching IDs, shuffle, take N.
export async function pickRandomQuestionIds(
  db: SupabaseClient,
  filters: PracticeFilters,
  n: number
): Promise<{ ids: number[]; total: number; shortfall: number }> {
  const tagConstraints = await resolveTagConstraints(db, filters.tags);
  if (tagConstraints?.emptyAllow) {
    return { ids: [], total: 0, shortfall: n };
  }

  let q = applyFiltersIds(db, filters);
  if (tagConstraints?.allowIds) {
    q = q.in("id", tagConstraints.allowIds);
  }
  if (tagConstraints?.denyIds && tagConstraints.denyIds.length > 0) {
    q = q.not("id", "in", `(${tagConstraints.denyIds.join(",")})`);
  }

  const { data, count, error } = await q.limit(CANDIDATE_POOL_SIZE);
  if (error) throw error;

  const allIds = (data ?? []).map((r) => r.id as number);
  // Fisher-Yates shuffle.
  for (let i = allIds.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [allIds[i], allIds[j]] = [allIds[j], allIds[i]];
  }
  const picked = allIds.slice(0, n);
  return {
    ids: picked,
    total: count ?? allIds.length,
    shortfall: Math.max(0, n - picked.length),
  };
}

// pgvector returns either an array of numbers OR a textual literal like "[0.1,0.2,...]"
// depending on supabase-js version. Handle both.
function parseEmbedding(raw: unknown): number[] | null {
  if (Array.isArray(raw)) return (raw as unknown[]).map(Number);
  if (typeof raw === "string") {
    const inner = raw.replace(/^\[|\]$/g, "");
    if (!inner) return null;
    return inner.split(",").map((s) => Number(s));
  }
  return null;
}

// Pick N question IDs that maximise diversity (greedy MAP DPP on cosine similarity
// of question embeddings). Falls back to random selection if embeddings haven't
// been generated yet (e.g. the embed script hasn't finished).
export async function pickDiverseQuestionIds(
  db: SupabaseClient,
  filters: PracticeFilters,
  n: number
): Promise<{
  ids: number[];
  total: number;
  shortfall: number;
  diversity_score: number | null;
  used_fallback: boolean;
}> {
  // 1. Filter to candidate pool (up to CANDIDATE_POOL_SIZE matching IDs).
  const tagConstraints = await resolveTagConstraints(db, filters.tags);
  if (tagConstraints?.emptyAllow) {
    return { ids: [], total: 0, shortfall: n, diversity_score: null, used_fallback: false };
  }

  let idsQ = applyFiltersIds(db, filters);
  if (tagConstraints?.allowIds) {
    idsQ = idsQ.in("id", tagConstraints.allowIds);
  }
  if (tagConstraints?.denyIds && tagConstraints.denyIds.length > 0) {
    idsQ = idsQ.not("id", "in", `(${tagConstraints.denyIds.join(",")})`);
  }
  const { data: idRows, count, error: idErr } = await idsQ.limit(CANDIDATE_POOL_SIZE);
  if (idErr) throw idErr;

  const candidateIds = (idRows ?? []).map((r) => r.id as number);
  if (candidateIds.length === 0) {
    return {
      ids: [],
      total: 0,
      shortfall: n,
      diversity_score: null,
      used_fallback: false,
    };
  }

  // 2. Fetch embeddings for those candidates.
  const { data: embedRows, error: embedErr } = await db
    .from("question_embeddings")
    .select("question_id, embedding")
    .eq("model", EMBEDDING_MODEL)
    .in("question_id", candidateIds);
  if (embedErr) throw embedErr;

  const byId = new Map<number, number[]>();
  for (const row of embedRows ?? []) {
    const r = row as { question_id: number; embedding: unknown };
    const v = parseEmbedding(r.embedding);
    if (v) byId.set(r.question_id, v);
  }

  // 3. Keep only candidates that have embeddings.
  const usableIds = candidateIds.filter((id) => byId.has(id));

  // Not enough usable embeddings → graceful fallback to random across full candidate pool.
  if (usableIds.length < Math.min(2, n)) {
    const fallback = await pickRandomQuestionIds(db, filters, n);
    return {
      ...fallback,
      diversity_score: null,
      used_fallback: true,
    };
  }

  // 4. Greedy MAP DPP over the usable subset.
  const embeddings = usableIds.map((id) => byId.get(id)!);
  const selectedIndices = dppGreedyMAP(embeddings, n);
  const selectedIds = selectedIndices.map((i) => usableIds[i]);
  const selectedEmbeddings = selectedIndices.map((i) => embeddings[i]);

  const div =
    selectedEmbeddings.length >= 2 ? diversityScore(selectedEmbeddings) : null;

  return {
    ids: selectedIds,
    total: count ?? candidateIds.length,
    shortfall: Math.max(0, n - selectedIds.length),
    diversity_score: div,
    used_fallback: false,
  };
}
