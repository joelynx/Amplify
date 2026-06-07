import { useEffect, useState, useMemo } from "react";
import { useQuizStore } from "../state/quiz";
import { useGenerateStore, draftToFilters } from "../state/generate";
import { useDebounced } from "../lib/debounce";

import { CheckableTree } from "../components/generate/CheckableTree";
import { TagTray } from "../components/generate/TagTray";
import { ChipTray } from "../components/generate/ChipTray";
import { SubjectPicker } from "../components/generate/SubjectPicker";

import { TraverseRunner } from "../components/quiz/TraverseRunner";
import { DiscoverRunner } from "../components/quiz/DiscoverRunner";

import { ipc, type ConceptTree } from "../lib/ipc";
import { Map, Zap } from "lucide-react";

export default function QuizPage() {
  const {
    mode,
    setMode,
    nQuestions,
    setNQuestions,
    isStarted,
    setIsStarted,
    resetQuizState
  } = useQuizStore();

  const draft = useGenerateStore();

  const [subjects, setSubjects] = useState<string[]>([]);
  const [tree, setTree] = useState<ConceptTree>({});
  
  const [tags, setTags] = useState<string[]>([]);
  const [sources, setSources] = useState<string[]>([]);
  const [types, setTypes] = useState<string[]>([]);

  useEffect(() => {
    let cancelled = false;
    ipc.list_subjects().then((subs) => {
      if (!cancelled) setSubjects(subs);
    });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    let cancelled = false;
    ipc.get_concept_tree(draft.subject, draft.inSyllabusOnly).then((t) => {
      if (!cancelled) setTree(t);
    });
    return () => { cancelled = true; };
  }, [draft.subject, draft.inSyllabusOnly]);

  const filters = useMemo(() => draftToFilters(draft), [draft]);
  const debouncedFilters = useDebounced(filters, 150);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      ipc.get_all_tags(debouncedFilters),
      ipc.get_sources(debouncedFilters),
      ipc.get_types(debouncedFilters),
    ]).then(([t, s, ty]) => {
      if (cancelled) return;
      setTags(t);
      setSources(s);
      setTypes(ty);
    });
    return () => { cancelled = true; };
  }, [debouncedFilters]);


  if (isStarted) {
    return (
      <main className="h-full overflow-y-auto bg-background px-6 pt-6 pb-20">
        <div className="max-w-4xl mx-auto mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-semibold text-text">
            {mode === "traverse" ? "Traverse Mode" : "Discover Mode"}
          </h1>
          <button
            onClick={() => resetQuizState()}
            className="text-sm font-medium text-muted hover:text-text transition-colors"
          >
            End Session
          </button>
        </div>
        {mode === "traverse" ? <TraverseRunner /> : <DiscoverRunner />}
      </main>
    );
  }

  // Setup phase
  return (
    <main className="h-full overflow-y-auto bg-background px-6 pt-6 pb-20">
      <div className="mx-auto max-w-3xl space-y-6">
        <div className="space-y-1">
          <h1 className="text-3xl font-semibold text-text">Quiz</h1>
          <p className="text-muted">Explore questions interactively.</p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <button
            onClick={() => setMode("traverse")}
            className={`p-6 rounded-xl border text-left transition-all ${
              mode === "traverse"
                ? "border-primary bg-primary/5 ring-1 ring-primary"
                : "border-border bg-surface hover:border-primary/50"
            }`}
          >
            <Map className={`w-8 h-8 mb-4 ${mode === "traverse" ? "text-primary" : "text-muted"}`} />
            <h3 className="font-semibold text-lg mb-1 text-text">Traverse</h3>
            <p className="text-sm text-muted">
              Sequential browsing. Control the similarity of the next question using a diversity slider.
            </p>
          </button>

          <button
            onClick={() => setMode("discover")}
            className={`p-6 rounded-xl border text-left transition-all ${
              mode === "discover"
                ? "border-primary bg-primary/5 ring-1 ring-primary"
                : "border-border bg-surface hover:border-primary/50"
            }`}
          >
            <Zap className={`w-8 h-8 mb-4 ${mode === "discover" ? "text-primary" : "text-muted"}`} />
            <h3 className="font-semibold text-lg mb-1 text-text">Discover</h3>
            <p className="text-sm text-muted">
              Batch generation. Uses a Determinantal Point Process to select N maximally diverse questions.
            </p>
          </button>
        </div>

        <div className="bg-surface rounded-lg border border-border p-5 space-y-5">
          <div className="flex items-center justify-between">
            <h3 className="font-medium text-text">Subject Filters</h3>
            <div className="w-64">
              <SubjectPicker
                subjects={subjects}
                value={draft.subject}
                onChange={draft.setSubject}
              />
            </div>
          </div>
          
          <CheckableTree tree={tree} />
        </div>

        <div className="bg-surface rounded-lg border border-border p-5">
          <TagTray available={tags} />
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          <div className="bg-surface rounded-lg border border-border p-5">
            <ChipTray
              available={sources}
              selected={draft.sources}
              onChange={draft.setSources}
              placeholder="Add a source…"
              searchPlaceholder="Search sources"
              emptyMessage="No sources available"
            />
          </div>
          <div className="bg-surface rounded-lg border border-border p-5">
            <ChipTray
              available={types}
              selected={draft.types}
              onChange={draft.setTypes}
              placeholder="Add a question type…"
              searchPlaceholder="Search types"
              emptyMessage="No types available"
            />
          </div>
        </div>

        <div className="bg-surface rounded-lg border border-border p-5 space-y-4">
          <h3 className="font-medium text-text">Options</h3>
          
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="inSyllabusOnly"
              checked={draft.inSyllabusOnly}
              onChange={(e) => draft.setInSyllabusOnly(e.target.checked)}
              className="rounded border-border text-primary focus:ring-primary h-4 w-4"
            />
            <label htmlFor="inSyllabusOnly" className="text-sm text-text">In syllabus only</label>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="reuseQuestions"
              checked={draft.reuseQuestions}
              onChange={(e) => draft.setReuseQuestions(e.target.checked)}
              className="rounded border-border text-primary focus:ring-primary h-4 w-4"
            />
            <label htmlFor="reuseQuestions" className="text-sm text-text">Allow reused questions</label>
          </div>
          
          {mode === "discover" && (
            <div className="pt-4 border-t border-border">
              <label htmlFor="nQuestions" className="block text-sm font-medium text-text mb-2">
                Number of Questions
              </label>
              <input
                id="nQuestions"
                type="number"
                min="1"
                max="200"
                value={nQuestions}
                onChange={(e) => setNQuestions(parseInt(e.target.value) || 10)}
                className="w-32 rounded-md border border-border bg-background px-3 py-1.5 text-sm outline-none focus:border-primary"
              />
            </div>
          )}
        </div>

        <div className="flex justify-end pt-4">
          <button
            onClick={() => setIsStarted(true)}
            className="bg-primary text-primary-foreground px-8 py-3 rounded-lg font-medium hover:bg-primary/90 transition-colors"
          >
            Start {mode === "traverse" ? "Traverse" : "Discover"} Session
          </button>
        </div>
      </div>
    </main>
  );
}
