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

import { ActionBar } from "../components/ui/ActionBar";
import { Disclosure } from "../components/ui/Disclosure";
import { filterSummary } from "../components/generate/OutputSettings";
import { todayStatus } from "../components/quiz/TodayCard";

import { ipc, type ConceptTree, type ReviewList, type ReviewSummary, type TemplatePayload } from "../lib/ipc";
import { Map, Zap, RotateCcw, NotebookPen, Shuffle } from "lucide-react";
import { createPortal } from "react-dom";
import { Spinner } from "../appearance/brand/Loader";
import type { SessionSummary } from "../appearance/events";
import { ResultsScreen } from "../appearance/results/ResultsScreen";
import { endSession, sessionActive, startSession } from "../appearance/session";

const MODES: { id: QuizMode; title: string; blurb: string; Icon: typeof Map }[] = [
  { id: "review", title: "Review", blurb: "Questions due again, past mistakes, and ones you solved with help.", Icon: RotateCcw },
  { id: "lecture", title: "From a lecture", blurb: "Paste the lecture's keywords, confirm the matches, practise.", Icon: NotebookPen },
  { id: "mixed", title: "Mixed review", blurb: "Interleave techniques you have studied; spot which one each needs.", Icon: Shuffle },
  { id: "traverse", title: "Traverse", blurb: "One question at a time; a slider sets how similar the next one is.", Icon: Map },
  { id: "discover", title: "Discover", blurb: "A set of questions chosen to be as different from each other as possible.", Icon: Zap },
];

const TITLES: Record<QuizMode, string> = {
  traverse: "Traverse Mode",
  discover: "Discover Mode",
  review: "Review",
  lecture: "Lecture practice",
  mixed: "Mixed review",
};

/** Whether a mode has been picked (by the student, or once by the
 * recommendation) since the app opened: the recommendation never overrides it. */
let modeChosen = false;

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

  // Session events for sounds and the session-end screen.
  const [sessionSummary, setSessionSummary] = useState<SessionSummary | null>(null);
  useEffect(() => {
    // Coming back to a running session keeps its counts and clock.
    if (isStarted && !sessionActive()) startSession(mode);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isStarted]);
  const endQuizSession = () => {
    const summary = endSession();
    if (summary) setSessionSummary(summary);
    else resetQuizState();
  };

  const chooseMode = (m: QuizMode) => {
    modeChosen = true;
    if (m !== mode) setConcepts([]);
    setMode(m);
  };

  const startReview = (kind: ReviewList) => {
    modeChosen = true;
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
    modeChosen = true;
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

  // How many questions the current topics and filters leave to draw from.
  const [matchCount, setMatchCount] = useState<number | null>(null);
  useEffect(() => {
    let cancelled = false;
    ipc
      .count_matching_questions(debouncedFilters)
      .then((n) => {
        if (!cancelled) setMatchCount(n);
      })
      .catch(() => {
        if (!cancelled) setMatchCount(null);
      });
    return () => { cancelled = true; };
  }, [debouncedFilters]);

  // The suggested mode: Review while anything is waiting (spaced review comes
  // first), otherwise new questions one at a time.
  const [reviewSummary, setReviewSummary] = useState<ReviewSummary | null>(null);
  useEffect(() => {
    let cancelled = false;
    ipc
      .get_review_summary(draft.subject)
      .catch(() => null)
      .then((s) => {
        if (!cancelled) setReviewSummary(s);
      });
    return () => { cancelled = true; };
  }, [draft.subject]);
  const waiting = reviewSummary
    ? reviewSummary.counts.due + reviewSummary.counts.mistakes + reviewSummary.counts.assisted
    : 0;
  const recommended: QuizMode | null = reviewSummary ? (waiting > 0 ? "review" : "traverse") : null;
  useEffect(() => {
    if (!recommended || modeChosen || isStarted) return;
    modeChosen = true;
    setMode(recommended);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recommended]);

  if (isStarted) {
    return (
      <main data-ui="arena" className="h-full overflow-y-auto bg-background px-6 pt-6 pb-20">
        <div className="max-w-4xl mx-auto mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-semibold text-text">{TITLES[mode]}</h1>
          <button
            onClick={endQuizSession}
            className="text-sm font-medium text-muted hover:text-text transition-colors"
          >
            End Session
          </button>
        </div>
        {mode === "traverse" ? <TraverseRunner /> : <DiscoverRunner />}
        {sessionSummary &&
          createPortal(
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4" role="dialog" aria-modal="true">
              <div className="absolute inset-0 bg-black/40" />
              <div className="relative z-10 w-full max-w-lg">
                <ResultsScreen
                  summary={sessionSummary}
                  onClose={() => {
                    setSessionSummary(null);
                    resetQuizState();
                  }}
                />
              </div>
            </div>,
            document.body,
          )}
      </main>
    );
  }

  // Setup phase
  const browsing = mode === "traverse" || mode === "discover";
  const leafCount = draft.selectedLeaves.size;
  const startDisabledReason =
    mode === "traverse" && useSeed && (!seedValidation?.valid || seedValidating)
      ? "Enter the ID of the question to start from"
      : mode === "lecture" && concepts.length === 0
        ? "Paste the lecture's keywords and confirm at least one match"
        : mode === "mixed" && concepts.length < 2
          ? "Pick at least two techniques to mix"
          : browsing && matchCount === 0
            ? "No questions match: widen the topics or filters"
            : null;
  const optionSummary = [
    browsing ? filterSummary(draft) : draft.inSyllabusOnly ? "In syllabus only" : "Outside syllabus too",
    mode === "lecture" && draft.reuseQuestions ? "reuse allowed" : null,
    browsing && draft.templateName ? `template ${draft.templateName}` : null,
    mode === "traverse" && useSeed ? "starts from a chosen question" : null,
  ]
    .filter(Boolean)
    .join(" · ");

  const countField = (
    <div className="flex items-center gap-3">
      <label htmlFor="nQuestions" className="text-sm font-medium text-text">
        Number of questions
      </label>
      <input
        id="nQuestions"
        type="number"
        min="1"
        max="200"
        value={nQuestions}
        onChange={(e) => setNQuestions(parseInt(e.target.value) || 10)}
        className="w-24 rounded-md border border-border bg-background px-3 py-1.5 text-sm outline-none focus:border-primary"
      />
    </div>
  );

  return (
    <div className="flex h-full flex-col bg-background">
    <main className="flex-1 overflow-y-auto px-6 pt-6 pb-10">
      <div className="mx-auto max-w-3xl space-y-6">
        <div className="space-y-1">
          <h1 className="text-3xl font-semibold text-text">Quiz</h1>
          <p className="text-muted">Practise interactively: review what is due, work from a lecture, or explore the bank.</p>
        </div>

        <div className="space-y-2">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {MODES.map(({ id, title, blurb, Icon }) => (
              <button
                key={id}
                onClick={() => chooseMode(id)}
                aria-pressed={mode === id}
                className={`p-4 rounded-xl border text-left transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-primary ${
                  mode === id
                    ? "border-primary bg-primary/5 ring-1 ring-primary"
                    : "border-border bg-surface hover:border-primary/50"
                }`}
              >
                <div className="mb-2 flex items-center justify-between gap-2">
                  <Icon className={`w-6 h-6 ${mode === id ? "text-primary" : "text-muted"}`} />
                  {recommended === id && (
                    <span className="rounded-full bg-primary px-2 py-0.5 text-[11px] font-semibold text-on-primary">
                      Recommended
                    </span>
                  )}
                </div>
                <h3 className="font-semibold mb-1 text-text">{title}</h3>
                <p className="text-xs text-muted">{blurb}</p>
              </button>
            ))}
          </div>
          {recommended && (
            <p className="text-sm text-muted">
              {recommended === "review"
                ? `Recommended: Review. ${todayStatus(reviewSummary).headline}.`
                : "Recommended: Traverse. Nothing is waiting for review, so start on new questions."}
            </p>
          )}
        </div>

        {!browsing && (
          <div className="bg-surface rounded-lg border border-border p-5 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-4">
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
            <div className="border-t border-border pt-4">{countField}</div>
          </div>
        )}

        {browsing && (
          <div className="bg-surface rounded-lg border border-border p-5 space-y-4">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="min-w-0">
                <h3 className="font-medium text-text">What to practise</h3>
                <p className="text-xs text-muted">
                  Tick topics to narrow it down, or leave them all unticked to draw from the whole subject.
                </p>
              </div>
              <div className="w-64">
                <SubjectPicker subjects={subjects} value={draft.subject} onChange={draft.setSubject} />
              </div>
            </div>
            <CheckableTree tree={tree} />
            {mode === "discover" && <div className="border-t border-border pt-4">{countField}</div>}
          </div>
        )}

        {mode !== "review" && (
          <Disclosure title="More options" summary={optionSummary} prefKey="quiz.optionsOpen">
            <div className="space-y-5">
              {browsing && (
                <>
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium text-text">Saved template</h4>
                    <div className="flex flex-wrap items-center gap-2">
                      <TemplatePicker
                        templates={templates}
                        value={draft.templateName}
                        onChange={handleSelectTemplate}
                        onOpenManager={() => setManagerOpen(true)}
                      />
                      <Button variant="outline" size="sm" onClick={() => setSaveDialogOpen(true)}>
                        Save template
                      </Button>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium text-text">Tags</h4>
                    <TagTray available={tags} />
                  </div>
                  <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
                    <div className="space-y-2">
                      <h4 className="text-sm font-medium text-text">Sources</h4>
                      <ChipTray
                        available={sources}
                        selected={draft.sources}
                        onChange={draft.setSources}
                        placeholder="Add a source…"
                        searchPlaceholder="Search sources"
                        emptyMessage="No sources available"
                      />
                    </div>
                    <div className="space-y-2">
                      <h4 className="text-sm font-medium text-text">Question types</h4>
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
                </>
              )}

              <div className={browsing ? "space-y-3 border-t border-border pt-4" : "space-y-3"}>
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

                {mode !== "mixed" && (
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
              </div>

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
                    <label htmlFor="useSeed" className="text-sm font-medium text-text">Start from a specific question</label>
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
                          {seedValidating && <Spinner className="w-4 h-4 text-muted" />}
                          {!seedValidating && seedValidation && (
                            <span className={`text-sm ${seedValidation.valid ? "text-success" : "text-error"}`}>
                              {seedValidation.valid ? "Valid" : seedValidation.reason}
                            </span>
                          )}
                        </div>
                        {seedValidation?.valid && seedValidation.is_used && !draft.reuseQuestions && (
                          <p className="text-xs text-warning mt-1">
                            You have already done this question, so the session starts from the one after it.
                          </p>
                        )}
                      </div>

                      <div>
                        <label htmlFor="seedDiversity" className="mb-1 block text-sm text-text">
                          Similarity of the first question to this one
                        </label>
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
          </Disclosure>
        )}
      </div>
    </main>

    {mode !== "review" && (
      <ActionBar
        note={startDisabledReason}
        summary={
          <>
            <span className="font-semibold">{TITLES[mode].replace(" Mode", "")}</span> · {draft.subject ?? "All subjects"}
            {browsing && (
              <>
                {" · "}
                {leafCount > 0 ? `${leafCount} subtopic${leafCount === 1 ? "" : "s"} ticked` : "all topics"}
                {matchCount !== null && (
                  <>
                    {" · "}
                    <span className="font-semibold">{matchCount.toLocaleString()}</span> question
                    {matchCount === 1 ? "" : "s"} available
                  </>
                )}
              </>
            )}
          </>
        }
      >
        <Button variant="primary" onClick={() => setIsStarted(true)} disabled={startDisabledReason !== null}>
          Start {TITLES[mode].replace(" Mode", "")} session
        </Button>
      </ActionBar>
    )}

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
    </div>
  );
}
