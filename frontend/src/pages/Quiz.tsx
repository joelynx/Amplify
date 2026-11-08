import { useEffect, useState, useMemo } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useQuizStore, type QuizMode } from "../state/quiz";
import { useGenerateStore, draftToFilters, draftToTemplate, templateToLeaves } from "../state/generate";
import { useDebounced } from "../lib/debounce";

import { CheckableTree } from "../components/generate/CheckableTree";
import { TagTray } from "../components/generate/TagTray";
import { ChipTray } from "../components/generate/ChipTray";
import { SubjectPicker } from "../components/generate/SubjectPicker";
import { TemplatePicker } from "../components/generate/TemplatePicker";
import { NameDialog } from "../components/generate/NameDialog";
import { TemplateManager } from "../components/generate/TemplateManager";
import { Button } from "../components/ui/Button";

import { TraverseRunner } from "../components/quiz/TraverseRunner";
import { DiscoverRunner } from "../components/quiz/DiscoverRunner";
import { ReviewPanel } from "../components/quiz/ReviewPanel";
import { LecturePanel } from "../components/quiz/LecturePanel";
import { TechniquePanel } from "../components/quiz/TechniquePanel";

import { ipc, type ConceptTree, type ReviewList, type TemplatePayload } from "../lib/ipc";
import { Map, Zap, Loader2, RotateCcw, NotebookPen, Shuffle } from "lucide-react";

const MODES: { id: QuizMode; title: string; blurb: string; Icon: typeof Map }[] = [
  { id: "review", title: "Review", blurb: "Questions due again, past mistakes, and ones you solved with help.", Icon: RotateCcw },
  { id: "lecture", title: "From a lecture", blurb: "Paste the lecture's keywords, confirm the matches, practise.", Icon: NotebookPen },
  { id: "mixed", title: "Mixed review", blurb: "Interleave techniques you have studied; spot which one each needs.", Icon: Shuffle },
  { id: "traverse", title: "Traverse", blurb: "One question at a time; a slider sets how similar the next one is.", Icon: Map },
  { id: "discover", title: "Discover", blurb: "A batch of N maximally diverse questions (DPP selection).", Icon: Zap },
];

const TITLES: Record<QuizMode, string> = {
  traverse: "Traverse Mode",
  discover: "Discover Mode",
  review: "Review",
  lecture: "Lecture practice",
  mixed: "Mixed review",
};

export default function QuizPage() {
  const {
    mode,
    setMode,
    nQuestions,
    setNQuestions,
    useSeed,
    setUseSeed,
    setSeedId,
    seedDiversity,
    setSeedDiversity,
    isStarted,
    setIsStarted,
    resetQuizState,
    concepts,
    setConcepts,
    setReviewKind,
  } = useQuizStore();

  const chooseMode = (m: QuizMode) => {
    if (m !== mode) setConcepts([]);
    setMode(m);
  };

  const startReview = (kind: ReviewList) => {
    resetQuizState();
    setMode("review");
    setReviewKind(kind);
    setIsStarted(true);
  };

  const draft = useGenerateStore();

  const [subjects, setSubjects] = useState<string[]>([]);
  const [tree, setTree] = useState<ConceptTree>({});
  
  const [tags, setTags] = useState<string[]>([]);
  const [sources, setSources] = useState<string[]>([]);
  const [types, setTypes] = useState<string[]>([]);

  const [seedInput, setSeedInput] = useState<string>("");
  const debouncedSeedInput = useDebounced(seedInput, 300);
  const [seedValidating, setSeedValidating] = useState(false);
  const [seedValidation, setSeedValidation] = useState<{valid: boolean; is_used: boolean; reason?: string} | null>(null);

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

  const [templates, setTemplates] = useState<string[]>([]);
  const [managerOpen, setManagerOpen] = useState(false);
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [loadedTemplate, setLoadedTemplate] = useState<any>(null);

  useEffect(() => {
    let cancelled = false;
    ipc.list_templates().then((tmpls) => {
      if (!cancelled) setTemplates(tmpls);
    });
    return () => { cancelled = true; };
  }, []);

  const refreshTemplates = async () => {
    const tmpls = await ipc.list_templates();
    setTemplates(tmpls);
  };

  const applyPayload = (payload: TemplatePayload) => {
    draft.setSubject(payload.subject);
    const leaves = templateToLeaves(payload, tree);
    draft.clearLeaves();
    draft.setLeavesBulk(Array.from(leaves), true);
    draft.clearTags();
    for (const t of payload.tag_list.compulsory) draft.addTag(t, "compulsory");
    for (const t of payload.tag_list.optional) draft.addTag(t, "optional");
    for (const t of payload.tag_list.excluded) draft.addTag(t, "excluded");
    draft.setSources(payload.source_list);
    draft.setTypes(payload.type_list);
    draft.setNQuestions(payload.n_questions);
    draft.setReuseQuestions(payload.reuse_questions);
    draft.setInSyllabusOnly(payload.in_syllabus_only);
  };

  const location = useLocation();
  const navigate = useNavigate();
  const navState = location.state as
    | { template?: TemplatePayload; startReview?: ReviewList; subject?: string | null; mode?: QuizMode }
    | null;

  useEffect(() => {
    if (!navState) return;
    if (navState.startReview) {
      if (navState.subject !== undefined) draft.setSubject(navState.subject);
      startReview(navState.startReview);
      navigate("/quiz", { replace: true, state: null });
    } else if (navState.mode && !navState.template) {
      resetQuizState();
      chooseMode(navState.mode);
      navigate("/quiz", { replace: true, state: null });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [navState]);

  const pendingTemplate = navState?.template;
  useEffect(() => {
    if (!pendingTemplate) return;
    if (Object.keys(tree).length === 0) return;
    resetQuizState();
    if (mode !== "traverse" && mode !== "discover") chooseMode("discover");
    applyPayload(pendingTemplate);
    draft.setTemplate(null);
    setLoadedTemplate(null);
    navigate("/quiz", { replace: true, state: null });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingTemplate, tree]);

  const handleSelectTemplate = async (name: string | null) => {
    draft.setTemplate(name);
    if (!name) {
      setLoadedTemplate(null);
      return;
    }
    const payload = await ipc.load_template(name);
    if (!payload) return;
    setLoadedTemplate(payload);
    applyPayload(payload);
  };

  const handleSaveDialogConfirm = async (name: string) => {
    const payload = draftToTemplate(draft, name);
    await ipc.save_template(name, payload);
    setSaveDialogOpen(false);
    setLoadedTemplate(payload);
    draft.setTemplate(name);
    await refreshTemplates();
  };

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

  useEffect(() => {
    if (!useSeed || !debouncedSeedInput.trim()) {
      setSeedValidation(null);
      setSeedId(null);
      return;
    }
    const id = parseInt(debouncedSeedInput.trim());
    if (isNaN(id)) {
      setSeedValidation({valid: false, is_used: false, reason: "Invalid ID format"});
      setSeedId(null);
      return;
    }
    setSeedValidating(true);
    let cancelled = false;
    ipc.quiz_traverse_check_seed(id, debouncedFilters).then((res) => {
      if (cancelled) return;
      setSeedValidation(res);
      if (res.valid) {
        setSeedId(id);
      } else {
        setSeedId(null);
      }
      setSeedValidating(false);
    });
    return () => { cancelled = true; };
  }, [useSeed, debouncedSeedInput, debouncedFilters, setSeedId]);


  if (isStarted) {
    return (
      <main className="h-full overflow-y-auto bg-background px-6 pt-6 pb-20">
        <div className="max-w-4xl mx-auto mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-semibold text-text">{TITLES[mode]}</h1>
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
          <p className="text-muted">Practise interactively: review what is due, work from a lecture, or explore the bank.</p>
        </div>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {MODES.map(({ id, title, blurb, Icon }) => (
            <button
              key={id}
              onClick={() => chooseMode(id)}
              className={`p-4 rounded-xl border text-left transition-all ${
                mode === id
                  ? "border-primary bg-primary/5 ring-1 ring-primary"
                  : "border-border bg-surface hover:border-primary/50"
              }`}
            >
              <Icon className={`w-6 h-6 mb-2 ${mode === id ? "text-primary" : "text-muted"}`} />
              <h3 className="font-semibold mb-1 text-text">{title}</h3>
              <p className="text-xs text-muted">{blurb}</p>
            </button>
          ))}
        </div>

        {(mode === "review" || mode === "lecture" || mode === "mixed") && (
          <div className="bg-surface rounded-lg border border-border p-5 space-y-4">
            <div className="flex items-center justify-between gap-4">
              <h3 className="font-medium text-text">
                {mode === "review" ? "Your review queue" : mode === "lecture" ? "What did the lecture cover?" : "Techniques to mix"}
              </h3>
              <div className="w-64">
                <SubjectPicker subjects={subjects} value={draft.subject} onChange={draft.setSubject} />
              </div>
            </div>
            {mode === "review" && <ReviewPanel subject={draft.subject} onStart={startReview} />}
            {mode === "lecture" && <LecturePanel filters={filters} onChange={setConcepts} />}
            {mode === "mixed" && <TechniquePanel subject={draft.subject} selected={concepts} onChange={setConcepts} />}
          </div>
        )}

        {(mode === "traverse" || mode === "discover") && (<>
        <div className="bg-surface rounded-lg border border-border p-5 space-y-5">
          <div className="flex items-center justify-between">
            <h3 className="font-medium text-text">Subject Filters</h3>
            <div className="flex items-center gap-2">
              <TemplatePicker
                templates={templates}
                value={draft.templateName}
                onChange={handleSelectTemplate}
                onOpenManager={() => setManagerOpen(true)}
              />
              <Button variant="secondary" onClick={() => setSaveDialogOpen(true)}>
                Save template
              </Button>
              <div className="w-64 ml-4">
                <SubjectPicker
                  subjects={subjects}
                  value={draft.subject}
                  onChange={draft.setSubject}
                />
              </div>
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

        </>)}

        <div className="bg-surface rounded-lg border border-border p-5 space-y-4">
          <h3 className="font-medium text-text">Options</h3>

          {mode !== "review" && (
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
          )}

          {mode !== "review" && mode !== "mixed" && (
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
          )}

          {mode !== "traverse" && (
            <div className={mode === "review" ? "" : "pt-4 border-t border-border"}>
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

          {mode === "traverse" && (
            <div className="pt-4 border-t border-border space-y-4">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="useSeed"
                  checked={useSeed}
                  onChange={(e) => setUseSeed(e.target.checked)}
                  className="rounded border-border text-primary focus:ring-primary h-4 w-4"
                />
                <label htmlFor="useSeed" className="text-sm font-medium text-text">Seed Question?</label>
              </div>
              
              {useSeed && (
                <div className="pl-6 space-y-4">
                  <div>
                    <label htmlFor="seedIdInput" className="block text-sm text-text mb-1">Question ID</label>
                    <div className="flex items-center gap-2">
                      <input
                        id="seedIdInput"
                        type="text"
                        value={seedInput}
                        onChange={(e) => setSeedInput(e.target.value)}
                        placeholder="e.g. 1234"
                        className="w-32 rounded-md border border-border bg-background px-3 py-1.5 text-sm outline-none focus:border-primary"
                      />
                      {seedValidating && <Loader2 className="w-4 h-4 animate-spin text-muted" />}
                      {!seedValidating && seedValidation && (
                        <span className={`text-sm ${seedValidation.valid ? "text-success" : "text-error"}`}>
                          {seedValidation.valid ? "Valid" : seedValidation.reason}
                        </span>
                      )}
                    </div>
                    {seedValidation?.valid && seedValidation.is_used && !draft.reuseQuestions && (
                      <p className="text-xs text-warning mt-1">
                        Question is already used. It will be used as a seed to find the next question.
                      </p>
                    )}
                  </div>
                  
                  <div>
                    <div className="flex justify-between items-center mb-1 max-w-xs">
                      <label htmlFor="seedDiversity" className="text-sm text-text">Seed Diversity</label>
                      <span className="text-xs text-muted">{(seedDiversity * 100).toFixed(0)}%</span>
                    </div>
                    <div className="flex items-center gap-3 max-w-xs">
                      <span className="text-xs text-muted">Random</span>
                      <input
                        id="seedDiversity"
                        type="range"
                        min="0"
                        max="1"
                        step="0.05"
                        value={seedDiversity}
                        onChange={(e) => setSeedDiversity(parseFloat(e.target.value))}
                        className="flex-1 accent-primary"
                      />
                      <span className="text-xs text-muted">Similar</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {mode !== "review" && (
          <div className="flex justify-end pt-4">
            <button
              onClick={() => setIsStarted(true)}
              disabled={
                (mode === "traverse" && useSeed && (!seedValidation?.valid || seedValidating)) ||
                (mode === "lecture" && concepts.length === 0) ||
                (mode === "mixed" && concepts.length < 2)
              }
              className="bg-primary text-primary-foreground px-8 py-3 rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Start {TITLES[mode].replace(" Mode", "")} Session
            </button>
          </div>
        )}
      </div>

      <NameDialog
        open={saveDialogOpen}
        title="Save template"
        initialValue={loadedTemplate?.name ?? ""}
        takenNames={templates.filter((n) => n !== loadedTemplate?.name)}
        confirmLabel="Save"
        onCancel={() => setSaveDialogOpen(false)}
        onConfirm={handleSaveDialogConfirm}
      />
      <TemplateManager
        open={managerOpen}
        onClose={() => setManagerOpen(false)}
        templates={templates}
        onChange={refreshTemplates}
        loadedName={loadedTemplate?.name ?? null}
        onLoadedRenamed={(newName) => {
          setLoadedTemplate((t: any) => (t ? { ...t, name: newName } : t));
          draft.setTemplate(newName);
        }}
        onLoadedDeleted={() => {
          setLoadedTemplate(null);
          draft.setTemplate(null);
        }}
      />
    </main>
  );
}
