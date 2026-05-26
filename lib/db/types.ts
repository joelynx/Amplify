// Hand-written DB types matching supabase/migrations/0001_initial.sql.
// Once Supabase CLI is set up, run `npm run types` to regenerate from the live schema.

export type QuestionType = "proof" | "numerical" | "explanation/reasoning";

export interface Question {
  id: number;
  topic: string;
  branch: string;
  subtopic: string;
  latexcode: string;
  type: QuestionType;
  in_syllabus: boolean;
  source: string | null;
  subsource: string | null;
  answer: string | null;
  solution: string | null;
  difficulty_rating: number;
  latex_hash: string;
  times_used: number;
  created_at: string;
}

export interface QuestionTag {
  question_id: number;
  tag: string;
}

export interface PracticeSession {
  id: string;
  user_id: string | null;
  anon_key: string | null;
  filters: PracticeFilters;
  n_target: number;
  created_at: string;
  completed_at: string | null;
}

export interface PracticeResponse {
  id: number;
  session_id: string;
  question_id: number;
  question_order: number;
  user_answer: string | null;
  is_correct: boolean | null;
  time_taken_ms: number | null;
  answered_at: string;
}

export interface UserMastery {
  user_id: string;
  topic: string;
  branch: string;
  subtopic: string;
  alpha: number;
  beta: number;
  total_seen: number;
  last_updated: string;
}

export interface PracticeFilters {
  topics?: string[];
  branches?: string[];
  subtopics?: string[];
  types?: QuestionType[];
  sources?: string[];
  min_difficulty?: number;
  in_syllabus_only?: boolean;
  course_id?: number;
  tags?: {
    compulsory?: string[];
    optional?: string[];
    excluded?: string[];
  };
}

export type UserRole = "student" | "faculty" | "admin" | "moderator";
export type InstitutionStatus = "active" | "pilot" | "interested";

export interface Institution {
  id: number;
  slug: string;
  name: string;
  short_name: string;
  country: string;
  logo_url: string | null;
  primary_color: string | null;
  joined_at: string;
  is_active: boolean;
  status: InstitutionStatus;
  description: string | null;
}

export interface Course {
  id: number;
  institution_id: number;
  slug: string;
  code: string;
  name: string;
  description: string | null;
  created_at: string;
}

export interface UserProfile {
  user_id: string;
  institution_id: number | null;
  display_name: string | null;
  role: UserRole;
  created_at: string;
}

export interface QuestionRevision {
  id: number;
  question_id: number;
  revised_by: string | null;
  revised_at: string;
  reason: string | null;
}

export interface QuestionDraft {
  id: number;
  author_id: string | null;
  institution_id: number | null;
  course_id: number | null;
  topic: string;
  branch: string;
  subtopic: string;
  latexcode: string;
  type: QuestionType;
  source: string | null;
  answer: string | null;
  solution: string | null;
  status: "pending" | "approved" | "rejected" | "needs_revision";
  reviewer_id: string | null;
  reviewed_at: string | null;
  review_notes: string | null;
  created_at: string;
}
