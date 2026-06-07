/**
 * Typed wrapper over `window.pywebview.api.*`. Every IPC call funnels through
 * here so the frontend never touches the bridge directly — keeps the desktop
 * wrapper swappable later (spec §2.2 hard rule 1).
 *
 * Step 1 surface: ping, log.
 */

export type LogLevel = "debug" | "info" | "warning" | "error";

export interface TagFilters {
  compulsory?: string[];
  optional?: string[];
  excluded?: string[];
}

export interface Filters {
  subject?: string | null;
  topics?: string[];
  branches?: string[];
  subtopics?: string[];
  sources?: string[];
  types?: string[];
  tags?: TagFilters;
  min_difficulty?: number;
  reuse_questions?: boolean;
  in_syllabus_only?: boolean;
  /** One-off "Generate PSet from selection" mode (spec §8.6). */
  question_ids?: number[];
}

/** A `Question` as projected by the questions repo for the Generate / Browser pages.
 * Embedding BLOBs are not included; similarity search has its own code path. */
export interface Question {
  question_id: number;
  semester: number | null;
  topic: string;
  branch: string;
  subtopic: string;
  latexcode: string;
  type: string | null;
  in_syllabus: number;
  source: string | null;
  subsource: string | null;
  answer: string | null;
  solution: string | null;
  solution_outline: string | null;
  hints: string | null;
  instructions: string | null;
  date_last_accessed: string | null;
  times_used: number;
  interactive_times_used: number;
  difficulty_rating: number | null;
  latex_hash: string;
  tags: string[];
}

/** A `Question` plus the cosine similarity from `get_similar_questions`. */
export interface SimilarQuestion extends Question {
  similarity: number;
}

export interface SearchResult {
  rows: Question[];
  total: number;
  error?: string;
}

// ---- Smart difficulty (Phase 2) ----------------------------------------

export interface DifficultyWeights {
  length: number;
  novelty: number;
  depth: number;
}

export interface DifficultyState {
  enabled: boolean;
  weights_by_topic: Record<string, DifficultyWeights>;
  defaults: DifficultyWeights;
  topics_with_depth: string[];
}

export interface RecomputeDifficultyResult {
  updated: number;
  skipped: number;
  avg_rating: number | null;
  topics_covered: number;
}

export interface PairwiseSide {
  question: Question;
  sub_scores: DifficultyWeights;
  rating: number;
}

export interface PairwisePair {
  topic: string;
  weights: DifficultyWeights;
  a: PairwiseSide;
  b: PairwiseSide;
}

// ---- Quiz (Phase 2 interactive practice) -------------------------------

export type QuizTemplate = "PBS" | "MIT_INTEGRATION_BEE" | "FREE_ANSWERING";
export type QuizGradient = "random" | "constant" | "custom";

export interface QuizSettings {
  template: QuizTemplate;
  n_questions: number;
  time_per_question_s?: number | null;
  total_time_s?: number | null;
  allow_skips?: boolean;
  show_scoring?: boolean;
  penalize_skips_marks?: number | null;
  enable_hints?: boolean;
  instant_scoring?: boolean;
  show_solutions?: boolean;
  wait_for_correct?: boolean;
  gradient_mode?: QuizGradient;
  max_points?: number;
  pbs_num_widgets?: number;
  pbs_pool_size?: number;
}

export interface QuizQuestion {
  question_id: number;
  topic: string;
  branch: string;
  subtopic: string;
  latexcode: string;
  type: string | null;
  hints?: string | null;
  instructions?: string | null;
}

export interface QuizSlot {
  slot_index: number;
  question: QuizQuestion | null;
  available_score: number;
}

export interface QuizQuestionFull {
  question_id: number;
  topic: string;
  branch: string;
  subtopic: string;
  latexcode: string;
  type: string | null;
  hints: string | null;
  answer: string | null;
  solution: string | null;
  instructions: string | null;
  source: string | null;
  difficulty_rating: number | null;
  tags: string[];
}

export interface TraverseStartResult {
  success: boolean;
  error?: string;
  quiz_id?: string;
  question?: QuizQuestionFull;
  pool_size?: number;
}

export interface TraverseNextResult {
  success: boolean;
  error?: string;
  question?: QuizQuestionFull | null;
  remaining?: number;
}

export interface DiscoverResult {
  success: boolean;
  error?: string;
  questions?: QuizQuestionFull[];
  diversity_score?: number | null;
}

export interface StartQuizResult {
  success: boolean;
  error?: string;
  quiz_id?: string;
  mode?: "pbs" | "non_pbs";
  initial_widgets?: QuizSlot[];
  total_time_s?: number | null;
  n_questions?: number;
}

export interface QuizAnswerPayload {
  user_answer: string;
  self_assessment?: "got_it" | "partial" | "missed" | null;
  time_taken_ms?: number;
  hints_used?: number;
}

export interface QuizAnswerResult {
  correct: boolean | null;
  partial_score?: number;
  canonical_answer?: string | null;
  solution?: string | null;
  replacement?: QuizSlot | { question_id?: number; topic?: string; branch?: string; subtopic?: string; latexcode?: string; type?: string | null } | null;
  finished?: boolean;
  current_total?: number;
  error?: string;
}

export interface QuizFinishSummary {
  total_score: number;
  n_answered: number;
  n_correct: number;
}

export interface QuizAttemptSummary {
  attempt_id: string;
  quiz_id: string;
  date_started: string;
  date_finished: string | null;
  total_score: number | null;
  subject: string | null;
  n_questions: number;
  template_name: string | null;
}

export interface QuizAttemptAnswer {
  question_id: number;
  slot_index: number;
  user_answer: string;
  correct: boolean | null;
  score: number;
  wrong_attempts: number;
  self_assessment: string | null;
  hints_used: number;
  time_taken_ms: number;
  submitted_at: string;
}

export interface QuizAttemptDetail {
  attempt_id: string;
  quiz_id: string;
  date_started: string;
  date_finished: string | null;
  total_score: number | null;
  subject: string | null;
  template_name: string | null;
  n_questions: number;
  answers: QuizAttemptAnswer[];
}

export type GenerationStrategy = "random" | "diverse" | "focused" | "frontier";

export interface RandomQuestionsResult {
  questions: Question[];
  shortfall: number;
  strategy?: GenerationStrategy;
  diversity_score?: number | null;
  used_fallback?: boolean;
  error?: string;
}

export type ConceptTree = Record<string, Record<string, string[]>>;

/** Wire shape of a saved subject (spec §3.6). */
export interface SubjectPayload {
  name: string;
  topics: string[];
  excluded_branches: Record<string, string[]>;
  excluded_subtopics: Record<string, Record<string, string[]>>;
  description: string;
  schema_version: number;
  is_active?: boolean;
}

/** Wire shape of a saved template (spec §3.3 + the solutions column added in Step 2). */
export interface TemplatePayload {
  name: string;
  subject: string | null;
  topic_list: string[];
  branch_list: string[];
  subtopic_list: string[];
  type_list: string[];
  source_list: string[];
  tag_list: { compulsory: string[]; optional: string[]; excluded: string[] };
  n_questions: number;
  reuse_questions: boolean;
  include_sources: boolean;
  in_syllabus_only: boolean;
  min_difficulty: number | null;
  save_directory: string | null;
  solutions: string | null;
}

interface PyWebViewApi {
  ping: () => Promise<string>;
  log: (level: LogLevel, message: string) => Promise<void>;
  count_matching_questions: (filters: Filters) => Promise<number>;
  get_random_questions: (
    filters: Filters,
    n: number,
    strategy?: GenerationStrategy,
  ) => Promise<RandomQuestionsResult>;
  get_similar_questions: (question_id: number, k?: number) => Promise<SimilarQuestion[]>;
  search_questions: (
    filters?: Filters | null,
    sort_by?: string,
    page?: number,
    page_size?: number,
    text_query?: string | null,
  ) => Promise<SearchResult>;
  get_question: (question_id: number) => Promise<Question | null>;
  mass_action: (
    question_ids: number[],
    action: string,
    payload?: Record<string, unknown> | null,
  ) => Promise<number>;
  recompute_difficulty: () => Promise<RecomputeDifficultyResult>;
  get_difficulty_state: () => Promise<DifficultyState>;
  set_smart_difficulty_enabled: (on: boolean) => Promise<void>;
  get_pairwise_pair: (topic?: string | null) => Promise<PairwisePair | null>;
  submit_pairwise_judgment: (
    harder_id: number,
    easier_id: number,
    magnitude: number,
  ) => Promise<{ topic: string; weights: DifficultyWeights; error?: string } | null>;
  start_quiz: (filters: Filters, settings: QuizSettings) => Promise<StartQuizResult>;
  quiz_take_widget: (quiz_id: string, slot_index: number) => Promise<QuizSlot | null>;
  quiz_submit_answer: (
    quiz_id: string,
    slot_index: number,
    payload: QuizAnswerPayload,
  ) => Promise<QuizAnswerResult>;
  quiz_skip: (quiz_id: string, slot_index?: number) => Promise<QuizAnswerResult>;
  quiz_request_hint: (quiz_id: string, slot_index: number) => Promise<{ hint: string | null; hint_index: number }>;
  quiz_finish: (quiz_id: string) => Promise<{ attempt_id: string; summary: QuizFinishSummary }>;
  list_quiz_attempts: (subject?: string | null, date_range?: DateRange | null) => Promise<QuizAttemptSummary[]>;
  get_quiz_attempt: (attempt_id: string) => Promise<QuizAttemptDetail | null>;
  quiz_traverse_check_seed: (question_id: number, filters: Filters) => Promise<{valid: boolean; is_used: boolean; reason?: string}>;
  quiz_traverse_start: (filters: Filters, seed_id?: number | null, seed_diversity?: number) => Promise<TraverseStartResult>;
  quiz_traverse_next: (quiz_id: string, current_question_id: number, diversity: number) => Promise<TraverseNextResult>;
  quiz_discover: (filters: Filters, n: number) => Promise<DiscoverResult>;
  get_topics: (subject?: string | null, in_syllabus_only?: boolean) => Promise<string[]>;
  get_branches: (subject: string | null, topic: string, in_syllabus_only?: boolean) => Promise<string[]>;
  get_subtopics: (
    subject: string | null,
    topic: string,
    branch: string,
    in_syllabus_only?: boolean,
  ) => Promise<string[]>;
  get_concept_tree: (subject?: string | null, in_syllabus_only?: boolean) => Promise<ConceptTree>;
  get_types: (filters?: Filters | null) => Promise<string[]>;
  get_sources: (filters?: Filters | null) => Promise<string[]>;
  get_all_tags: (filters?: Filters | null) => Promise<string[]>;
  list_subjects: () => Promise<string[]>;
  get_active_subject: () => Promise<string | null>;
  load_subject: (name: string) => Promise<SubjectPayload | null>;
  save_subject: (name: string, payload: SubjectPayload) => Promise<void>;
  delete_subject: (name: string) => Promise<void>;
  rename_subject: (old_name: string, new_name: string) => Promise<void>;
  subject_name_available: (name: string) => Promise<boolean>;
  activate_subject: (name: string | null) => Promise<void>;
  export_subject_to_file: (name: string) => Promise<string | null>;
  import_subject_from_file: () => Promise<SubjectPayload | null>;
  list_templates: () => Promise<string[]>;
  template_name_available: (name: string) => Promise<boolean>;
  load_template: (name: string) => Promise<TemplatePayload | null>;
  save_template: (name: string, payload: TemplatePayload) => Promise<void>;
  delete_template: (name: string) => Promise<void>;
  rename_template: (old_name: string, new_name: string) => Promise<void>;
  get_config: (key: string) => Promise<unknown>;
  set_config: (key: string, value: unknown) => Promise<void>;
  pick_save_directory: () => Promise<string | null>;
  list_themes: () => Promise<ThemeMeta[]>;
  set_theme: (theme_id: string) => Promise<void>;
  play_sound: (event: string) => Promise<void>;
  run_seed_ingest: () => Promise<IngestResult>;
  augment_seed_from_csv: (csv_path: string) => Promise<AugmentResult>;
  seed_tags_from_metadata: () => Promise<SeedTagsResult>;
  factory_reset: () => Promise<void>;
  reset_active_subject: () => Promise<ResetSubjectResult>;
  get_seed_diagnostics: () => Promise<SeedDiagnostics>;
  restart_app: () => Promise<void>;
  pick_csv_file: () => Promise<string | null>;
  pick_image_file: () => Promise<string | null>;
  validate_header_text: (text: string, level: "basic" | "extended") => Promise<string | null>;
  generate_pdf: (filters: Filters, output_settings: OutputSettings) => Promise<GenerateResult>;
  export_tex: (filters: Filters, output_settings: OutputSettings) => Promise<ExportResult>;
  open_file: (path: string) => Promise<void>;
  get_stats: (subject?: string | null, date_range?: DateRange | null) => Promise<StatsBundle>;
  get_subject_distribution: (date_range?: DateRange | null) => Promise<DistributionDatum[]>;
  get_topic_distribution: (
    subject?: string | null,
    date_range?: DateRange | null,
  ) => Promise<DistributionDatum[]>;
  get_source_attribution: (
    subject?: string | null,
    date_range?: DateRange | null,
  ) => Promise<DistributionDatum[]>;
  get_trends: (subject?: string | null) => Promise<TrendInsight[]>;
  get_question_multiplicity_dist: (subject?: string | null) => Promise<Record<number, number>>;
  get_calendar_heatmap: (year?: number | null) => Promise<Record<string, number>>;
  get_activity_line: (date_range?: DateRange | null) => Promise<ActivityDatum[]>;
  list_psets: (subject?: string | null, date_range?: DateRange | null) => Promise<PSetSummary[]>;
  delete_pset: (pset_id: string) => Promise<void>;
  open_pset_file: (pset_id: string) => Promise<OpenPsetResult>;
  re_export_pset_pdf: (pset_id: string) => Promise<GenerateResult>;
  get_pset_filters: (pset_id: string) => Promise<TemplatePayload | null>;
  resolve_images: (filenames: string[]) => Promise<Record<string, string>>;
}

export interface OutputSettings {
  n_questions: number;
  reuse_questions: boolean;
  include_sources: boolean;
  solutions: string;
  min_difficulty: number;
  in_syllabus_only: boolean;
  save_directory: string | null;
  template_name?: string | null;
  strategy?: GenerationStrategy;
}

export interface GenerateResult {
  success: boolean;
  pset_id?: string;
  path?: string | null;
  fallback?: string | null;
  errors?: string;
  shortfall?: number;
  strategy?: GenerationStrategy;
  diversity_score?: number | null;
  used_fallback?: boolean;
}

export interface ExportResult {
  success: boolean;
  path?: string;
  errors?: string;
  shortfall?: number;
}

export interface DateRange {
  from?: string | null;
  to?: string | null;
}

export interface StatsBundle {
  psets_generated: number;
  total_questions_seen: number;
  unique_questions_seen: number;
  fraction_questions_seen: number;
  max_questions_in_single_pset: number;
  max_question_multiplicity: number;
  avg_question_multiplicity: number;
  avg_difficulty_rating: number | null;
  total_questions_in_subject: number;
}

export interface DistributionDatum {
  label: string;
  count: number;
  /** Optional pre-computed percent share; backend supplies this for source attribution. */
  percent?: number;
}

/** Step 21: one row of the Trends panel. `cta_filters` is a partial
 * TemplatePayload that the Generate page consumes via location.state.template. */
export interface TrendInsight {
  id: string;
  title: string;
  body: string;
  cta_label: string;
  cta_filters: Partial<TemplatePayload>;
}

export interface ActivityDatum {
  date: string; // YYYY-MM-DD
  papers: number;
  questions: number;
}

export interface ThemeMeta {
  id: string;
  name: string;
  description: string;
  preview: string | null;
}

export interface SeedDiagnostics {
  embed_model_version: string;
  questions_total: number;
  questions_with_embeddings: number;
  questions_without_embeddings: number;
  questions_with_outlines: number;
  questions_without_outlines: number;
}

export interface AugmentResult {
  added: number;
  skipped: number;
  errors: string[];
  warnings: string[];
}

export interface SeedTagsResult {
  questions_scanned: number;
  rows_inserted: number;
}

export interface IngestResult {
  imported: number;
  skipped: number;
  embeddings_loaded: number;
  outlines_loaded: number;
  warnings: string[];
}

export interface ResetSubjectResult {
  subject: string;
  rows_reset: number;
}

export interface PSetSummary {
  pset_id: string;
  date_created: string;
  n_questions: number;
  subject: string | null;
  template_name: string | null;
  generation_mode?: GenerationStrategy;
  diversity_score?: number | null;
}

export interface OpenPsetResult {
  success: boolean;
  path?: string;
  errors?: string;
}

declare global {
  interface Window {
    pywebview?: { api: PyWebViewApi };
  }
}

/** Thrown when the IPC bridge never materializes — typically because the page
 * is being viewed in a plain browser instead of the PyWebView shell. Callers
 * can catch this specifically to render a "browser preview" state instead of
 * a hard error. */
export class BridgeUnavailableError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "BridgeUnavailableError";
  }
}

const BRIDGE_TIMEOUT_MS = 1500;

let bridgePromise: Promise<PyWebViewApi> | null = null;

function bridge(): Promise<PyWebViewApi> {
  if (bridgePromise) return bridgePromise;
  bridgePromise = new Promise<PyWebViewApi>((resolve, reject) => {
    if (window.pywebview?.api) {
      resolve(window.pywebview.api);
      return;
    }
    const onReady = () => {
      cleanup();
      if (window.pywebview?.api) resolve(window.pywebview.api);
      else reject(new BridgeUnavailableError("pywebviewready fired but window.pywebview.api missing"));
    };
    const onTimeout = () => {
      cleanup();
      reject(
        new BridgeUnavailableError(
          `PyWebView bridge not available after ${BRIDGE_TIMEOUT_MS}ms — likely a standalone browser preview`,
        ),
      );
    };
    const timer = window.setTimeout(onTimeout, BRIDGE_TIMEOUT_MS);
    const cleanup = () => {
      window.clearTimeout(timer);
      window.removeEventListener("pywebviewready", onReady);
    };
    window.addEventListener("pywebviewready", onReady, { once: true });
  });
  return bridgePromise;
}

/** Best-effort sync check for whether the bridge is already present. Returns
 * false during the early window before `pywebviewready` fires — use `bridge()`
 * if you need to await. */
export function isBridgeReady(): boolean {
  return Boolean(window.pywebview?.api);
}

export const ipc = {
  async ping(): Promise<string> {
    const api = await bridge();
    return api.ping();
  },
  async log(level: LogLevel, message: string): Promise<void> {
    const api = await bridge();
    return api.log(level, message);
  },
  async count_matching_questions(filters: Filters): Promise<number> {
    const api = await bridge();
    return api.count_matching_questions(filters);
  },
  async get_random_questions(
    filters: Filters,
    n: number,
    strategy: GenerationStrategy = "random",
  ): Promise<RandomQuestionsResult> {
    const api = await bridge();
    return api.get_random_questions(filters, n, strategy);
  },
  async get_similar_questions(question_id: number, k = 10): Promise<SimilarQuestion[]> {
    const api = await bridge();
    return api.get_similar_questions(question_id, k);
  },
  async search_questions(
    filters: Filters | null = null,
    sort_by = "question_id_asc",
    page = 0,
    page_size = 50,
    text_query: string | null = null,
  ): Promise<SearchResult> {
    const api = await bridge();
    return api.search_questions(filters, sort_by, page, page_size, text_query);
  },
  async get_question(question_id: number): Promise<Question | null> {
    const api = await bridge();
    return api.get_question(question_id);
  },
  async mass_action(
    question_ids: number[],
    action: string,
    payload: Record<string, unknown> | null = null,
  ): Promise<number> {
    const api = await bridge();
    return api.mass_action(question_ids, action, payload);
  },
  async recompute_difficulty(): Promise<RecomputeDifficultyResult> {
    const api = await bridge();
    return api.recompute_difficulty();
  },
  async get_difficulty_state(): Promise<DifficultyState> {
    const api = await bridge();
    return api.get_difficulty_state();
  },
  async set_smart_difficulty_enabled(on: boolean): Promise<void> {
    const api = await bridge();
    return api.set_smart_difficulty_enabled(on);
  },
  async get_pairwise_pair(topic: string | null = null): Promise<PairwisePair | null> {
    const api = await bridge();
    return api.get_pairwise_pair(topic);
  },
  async submit_pairwise_judgment(harder_id: number, easier_id: number, magnitude: number) {
    const api = await bridge();
    return api.submit_pairwise_judgment(harder_id, easier_id, magnitude);
  },
  async start_quiz(filters: Filters, settings: QuizSettings): Promise<StartQuizResult> {
    const api = await bridge();
    return api.start_quiz(filters, settings);
  },
  async quiz_take_widget(quiz_id: string, slot_index: number): Promise<QuizSlot | null> {
    const api = await bridge();
    return api.quiz_take_widget(quiz_id, slot_index);
  },
  async quiz_submit_answer(
    quiz_id: string,
    slot_index: number,
    payload: QuizAnswerPayload,
  ): Promise<QuizAnswerResult> {
    const api = await bridge();
    return api.quiz_submit_answer(quiz_id, slot_index, payload);
  },
  async quiz_skip(quiz_id: string, slot_index = 0): Promise<QuizAnswerResult> {
    const api = await bridge();
    return api.quiz_skip(quiz_id, slot_index);
  },
  async quiz_request_hint(quiz_id: string, slot_index: number) {
    const api = await bridge();
    return api.quiz_request_hint(quiz_id, slot_index);
  },
  async quiz_finish(quiz_id: string) {
    const api = await bridge();
    return api.quiz_finish(quiz_id);
  },
  async list_quiz_attempts(
    subject: string | null = null,
    date_range: DateRange | null = null,
  ): Promise<QuizAttemptSummary[]> {
    const api = await bridge();
    return api.list_quiz_attempts(subject, date_range);
  },
  async get_quiz_attempt(attempt_id: string): Promise<QuizAttemptDetail | null> {
    const api = await bridge();
    return api.get_quiz_attempt(attempt_id);
  },
  async quiz_traverse_check_seed(question_id: number, filters: Filters): Promise<{valid: boolean; is_used: boolean; reason?: string}> {
    const api = await bridge();
    return api.quiz_traverse_check_seed(question_id, filters);
  },
  async quiz_traverse_start(filters: Filters, seed_id?: number | null, seed_diversity?: number): Promise<TraverseStartResult> {
    const api = await bridge();
    return api.quiz_traverse_start(filters, seed_id, seed_diversity);
  },
  async quiz_traverse_next(quiz_id: string, current_question_id: number, diversity: number): Promise<TraverseNextResult> {
    const api = await bridge();
    return api.quiz_traverse_next(quiz_id, current_question_id, diversity);
  },
  async quiz_discover(filters: Filters, n: number): Promise<DiscoverResult> {
    const api = await bridge();
    return api.quiz_discover(filters, n);
  },
  async get_topics(subject: string | null = null, in_syllabus_only = true): Promise<string[]> {
    const api = await bridge();
    return api.get_topics(subject, in_syllabus_only);
  },
  async get_branches(
    subject: string | null,
    topic: string,
    in_syllabus_only = true,
  ): Promise<string[]> {
    const api = await bridge();
    return api.get_branches(subject, topic, in_syllabus_only);
  },
  async get_subtopics(
    subject: string | null,
    topic: string,
    branch: string,
    in_syllabus_only = true,
  ): Promise<string[]> {
    const api = await bridge();
    return api.get_subtopics(subject, topic, branch, in_syllabus_only);
  },
  async get_concept_tree(subject: string | null = null, in_syllabus_only = true): Promise<ConceptTree> {
    const api = await bridge();
    return api.get_concept_tree(subject, in_syllabus_only);
  },
  async get_types(filters: Filters | null = null): Promise<string[]> {
    const api = await bridge();
    return api.get_types(filters);
  },
  async get_sources(filters: Filters | null = null): Promise<string[]> {
    const api = await bridge();
    return api.get_sources(filters);
  },
  async get_all_tags(filters: Filters | null = null): Promise<string[]> {
    const api = await bridge();
    return api.get_all_tags(filters);
  },
  async list_subjects(): Promise<string[]> {
    const api = await bridge();
    return api.list_subjects();
  },
  async get_active_subject(): Promise<string | null> {
    const api = await bridge();
    return api.get_active_subject();
  },
  async load_subject(name: string): Promise<SubjectPayload | null> {
    const api = await bridge();
    return api.load_subject(name);
  },
  async save_subject(name: string, payload: SubjectPayload): Promise<void> {
    const api = await bridge();
    return api.save_subject(name, payload);
  },
  async delete_subject(name: string): Promise<void> {
    const api = await bridge();
    return api.delete_subject(name);
  },
  async rename_subject(old_name: string, new_name: string): Promise<void> {
    const api = await bridge();
    return api.rename_subject(old_name, new_name);
  },
  async subject_name_available(name: string): Promise<boolean> {
    const api = await bridge();
    return api.subject_name_available(name);
  },
  async activate_subject(name: string | null): Promise<void> {
    const api = await bridge();
    return api.activate_subject(name);
  },
  async export_subject_to_file(name: string): Promise<string | null> {
    const api = await bridge();
    return api.export_subject_to_file(name);
  },
  async import_subject_from_file(): Promise<SubjectPayload | null> {
    const api = await bridge();
    return api.import_subject_from_file();
  },
  async list_templates(): Promise<string[]> {
    const api = await bridge();
    return api.list_templates();
  },
  async template_name_available(name: string): Promise<boolean> {
    const api = await bridge();
    return api.template_name_available(name);
  },
  async load_template(name: string): Promise<TemplatePayload | null> {
    const api = await bridge();
    return api.load_template(name);
  },
  async save_template(name: string, payload: TemplatePayload): Promise<void> {
    const api = await bridge();
    return api.save_template(name, payload);
  },
  async delete_template(name: string): Promise<void> {
    const api = await bridge();
    return api.delete_template(name);
  },
  async rename_template(old_name: string, new_name: string): Promise<void> {
    const api = await bridge();
    return api.rename_template(old_name, new_name);
  },
  async get_config(key: string): Promise<unknown> {
    const api = await bridge();
    return api.get_config(key);
  },
  async set_config(key: string, value: unknown): Promise<void> {
    const api = await bridge();
    return api.set_config(key, value);
  },
  async pick_save_directory(): Promise<string | null> {
    const api = await bridge();
    return api.pick_save_directory();
  },
  async list_themes(): Promise<ThemeMeta[]> {
    const api = await bridge();
    return api.list_themes();
  },
  async set_theme(theme_id: string): Promise<void> {
    const api = await bridge();
    return api.set_theme(theme_id);
  },
  async play_sound(event: string): Promise<void> {
    const api = await bridge();
    return api.play_sound(event);
  },
  async run_seed_ingest(): Promise<IngestResult> {
    const api = await bridge();
    return api.run_seed_ingest();
  },
  async augment_seed_from_csv(csv_path: string): Promise<AugmentResult> {
    const api = await bridge();
    return api.augment_seed_from_csv(csv_path);
  },
  async seed_tags_from_metadata(): Promise<SeedTagsResult> {
    const api = await bridge();
    return api.seed_tags_from_metadata();
  },
  async factory_reset(): Promise<void> {
    const api = await bridge();
    return api.factory_reset();
  },
  async reset_active_subject(): Promise<ResetSubjectResult> {
    const api = await bridge();
    return api.reset_active_subject();
  },
  async get_seed_diagnostics(): Promise<SeedDiagnostics> {
    const api = await bridge();
    return api.get_seed_diagnostics();
  },
  async restart_app(): Promise<void> {
    const api = await bridge();
    return api.restart_app();
  },
  async pick_csv_file(): Promise<string | null> {
    const api = await bridge();
    return api.pick_csv_file();
  },
  async pick_image_file(): Promise<string | null> {
    const api = await bridge();
    return api.pick_image_file();
  },
  async validate_header_text(text: string, level: "basic" | "extended"): Promise<string | null> {
    const api = await bridge();
    return api.validate_header_text(text, level);
  },
  async generate_pdf(filters: Filters, output_settings: OutputSettings): Promise<GenerateResult> {
    const api = await bridge();
    return api.generate_pdf(filters, output_settings);
  },
  async export_tex(filters: Filters, output_settings: OutputSettings): Promise<ExportResult> {
    const api = await bridge();
    return api.export_tex(filters, output_settings);
  },
  async open_file(path: string): Promise<void> {
    const api = await bridge();
    return api.open_file(path);
  },
  async get_stats(
    subject: string | null = null,
    date_range: DateRange | null = null,
  ): Promise<StatsBundle> {
    const api = await bridge();
    return api.get_stats(subject, date_range);
  },
  async get_subject_distribution(date_range: DateRange | null = null): Promise<DistributionDatum[]> {
    const api = await bridge();
    return api.get_subject_distribution(date_range);
  },
  async get_topic_distribution(
    subject: string | null = null,
    date_range: DateRange | null = null,
  ): Promise<DistributionDatum[]> {
    const api = await bridge();
    return api.get_topic_distribution(subject, date_range);
  },
  async get_source_attribution(
    subject: string | null = null,
    date_range: DateRange | null = null,
  ): Promise<DistributionDatum[]> {
    const api = await bridge();
    return api.get_source_attribution(subject, date_range);
  },
  async get_trends(subject: string | null = null): Promise<TrendInsight[]> {
    const api = await bridge();
    return api.get_trends(subject);
  },
  async get_question_multiplicity_dist(
    subject: string | null = null,
  ): Promise<Record<number, number>> {
    const api = await bridge();
    return api.get_question_multiplicity_dist(subject);
  },
  async get_calendar_heatmap(year: number | null = null): Promise<Record<string, number>> {
    const api = await bridge();
    return api.get_calendar_heatmap(year);
  },
  async get_activity_line(date_range: DateRange | null = null): Promise<ActivityDatum[]> {
    const api = await bridge();
    return api.get_activity_line(date_range);
  },
  async list_psets(
    subject: string | null = null,
    date_range: DateRange | null = null,
  ): Promise<PSetSummary[]> {
    const api = await bridge();
    return api.list_psets(subject, date_range);
  },
  async delete_pset(pset_id: string): Promise<void> {
    const api = await bridge();
    return api.delete_pset(pset_id);
  },
  async open_pset_file(pset_id: string): Promise<OpenPsetResult> {
    const api = await bridge();
    return api.open_pset_file(pset_id);
  },
  async re_export_pset_pdf(pset_id: string): Promise<GenerateResult> {
    const api = await bridge();
    return api.re_export_pset_pdf(pset_id);
  },
  async get_pset_filters(pset_id: string): Promise<TemplatePayload | null> {
    const api = await bridge();
    return api.get_pset_filters(pset_id);
  },
  async resolve_images(filenames: string[]): Promise<Record<string, string>> {
    const api = await bridge();
    return (await api.resolve_images(filenames)) ?? {};
  },
};
