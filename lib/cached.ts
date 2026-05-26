// lib/cached.ts
// Cached taxonomy + bank-level reads. These rarely change (new questions
// only get added when an author uploads), so we cache for 5 minutes and
// avoid hammering Supabase on every page hit.
//
// Uses the admin (service-role) client so the cached read doesn't depend on
// any per-user cookie — that's what makes the cache safe to share.

import { unstable_cache } from "next/cache";
import { getAdminSupabase } from "@/lib/supabase/admin";

export const getPracticeTaxonomy = unstable_cache(
  async () => {
    const sb = getAdminSupabase();
    const [
      { data: taxonomyRows },
      { data: typeRows },
      { data: sourceRows },
      { data: tagRows },
    ] = await Promise.all([
      sb.from("questions").select("topic, branch, subtopic").order("topic"),
      sb.from("questions").select("type"),
      sb.from("questions").select("source"),
      sb.from("question_tags").select("tag"),
    ]);

    const tree: Record<string, Record<string, string[]>> = {};
    const branchSets: Record<string, Record<string, Set<string>>> = {};
    for (const row of taxonomyRows ?? []) {
      const { topic, branch, subtopic } = row as {
        topic: string;
        branch: string;
        subtopic: string;
      };
      branchSets[topic] ??= {};
      branchSets[topic][branch] ??= new Set();
      branchSets[topic][branch].add(subtopic);
    }
    for (const [t, branches] of Object.entries(branchSets)) {
      tree[t] = Object.fromEntries(
        Object.entries(branches).map(([b, subs]) => [b, [...subs].sort()])
      );
    }

    const types = [...new Set((typeRows ?? []).map((r) => r.type as string))];
    const sources = [
      ...new Set(
        (sourceRows ?? [])
          .map((r) => r.source as string | null)
          .filter((s): s is string => !!s)
      ),
    ].sort();
    const tags = [
      ...new Set((tagRows ?? []).map((r) => r.tag as string)),
    ].sort();

    return { tree, types, sources, tags };
  },
  ["practice-taxonomy-v2"],
  { revalidate: 300, tags: ["taxonomy"] }
);

export const getBankStats = unstable_cache(
  async () => {
    const sb = getAdminSupabase();
    const { data: qStats } = await sb
      .from("questions")
      .select("times_used, difficulty_rating, topic");
    return (qStats ?? []) as {
      times_used: number;
      difficulty_rating: number | null;
      topic: string;
    }[];
  },
  ["bank-stats-v1"],
  { revalidate: 300, tags: ["bank-stats"] }
);

export const getInstitutions = unstable_cache(
  async () => {
    const sb = getAdminSupabase();
    const { data } = await sb
      .from("institutions")
      .select("*")
      .order("status", { ascending: true })
      .order("short_name");
    return data ?? [];
  },
  ["institutions-v1"],
  { revalidate: 600, tags: ["institutions"] }
);

export const getAllSources = unstable_cache(
  async () => {
    const sb = getAdminSupabase();
    const { data } = await sb.from("questions").select("source");
    return [
      ...new Set(
        (data ?? [])
          .map((r) => (r as { source: string | null }).source)
          .filter((s): s is string => !!s)
      ),
    ].sort();
  },
  ["sources-v1"],
  { revalidate: 600, tags: ["sources"] }
);
