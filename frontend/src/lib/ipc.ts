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

export interface RandomQuestionsResult {
  questions: Question[];
  shortfall: number;
  error?: string;
}

export type ConceptTree = Record<string, Record<string, string[]>>;

interface PyWebViewApi {
  ping: () => Promise<string>;
  log: (level: LogLevel, message: string) => Promise<void>;
  count_matching_questions: (filters: Filters) => Promise<number>;
  get_random_questions: (filters: Filters, n: number) => Promise<RandomQuestionsResult>;
  get_topics: (subject?: string | null, in_syllabus_only?: boolean) => Promise<string[]>;
  get_branches: (subject: string | null, topic: string, in_syllabus_only?: boolean) => Promise<string[]>;
  get_subtopics: (
    subject: string | null,
    topic: string,
    branch: string,
    in_syllabus_only?: boolean,
  ) => Promise<string[]>;
  get_concept_tree: (subject?: string | null, in_syllabus_only?: boolean) => Promise<ConceptTree>;
  get_types: () => Promise<string[]>;
  get_sources: () => Promise<string[]>;
  get_all_tags: (filters?: Filters | null) => Promise<string[]>;
  list_subjects: () => Promise<string[]>;
  get_active_subject: () => Promise<string | null>;
  list_templates: () => Promise<string[]>;
  get_config: (key: string) => Promise<unknown>;
  set_config: (key: string, value: unknown) => Promise<void>;
  pick_save_directory: () => Promise<string | null>;
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
  async get_random_questions(filters: Filters, n: number): Promise<RandomQuestionsResult> {
    const api = await bridge();
    return api.get_random_questions(filters, n);
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
  async get_types(): Promise<string[]> {
    const api = await bridge();
    return api.get_types();
  },
  async get_sources(): Promise<string[]> {
    const api = await bridge();
    return api.get_sources();
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
  async list_templates(): Promise<string[]> {
    const api = await bridge();
    return api.list_templates();
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
};
