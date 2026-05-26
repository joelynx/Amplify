// lib/ipc.ts
// Stub of Joel's PyWebView IPC types. In his offline-app build these come from
// the Python backend; here we just re-export the shape so the components he
// authored compile cleanly inside our Next.js app. The actual data is computed
// server-side in /app/stats/page.tsx and passed as props.

export interface StatsBundle {
  psets_generated: number;
  total_questions_seen: number;
  unique_questions_seen: number;
  total_questions_in_subject: number;
  fraction_questions_seen: number; // 0..100 (already a percentage)
  max_questions_in_single_pset: number;
  max_question_multiplicity: number;
  avg_question_multiplicity: number;
  avg_difficulty_rating: number | null;
}

export interface ActivityDatum {
  date: string; // YYYY-MM-DD
  papers: number;
  questions: number;
}

export interface DistributionDatum {
  label: string;
  count: number;
}
