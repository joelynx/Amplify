/**
 * Runs a fixed list of questions: Discover (DPP-diverse batch), a review
 * session (the next questions of one review list), a lecture session
 * (questions split across confirmed keyword concepts) or a mixed review
 * (interleaved techniques, labels hidden until answered).
 *
 * Only the first question counts as used when the session starts; each one
 * after it is reported (`quiz_mark_presented`) when it comes on screen.
 */

import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { ipc, type DiscoverResult } from "../../lib/ipc";
import { useQuizStore } from "../../state/quiz";
import { useGenerateStore, draftToFilters } from "../../state/generate";
import { ElapsedTime } from "./ElapsedTime";
import { PracticeAnswer } from "./PracticeAnswer";
import { QuestionViewer } from "./QuestionViewer";
import { MatrixLoader } from "../../appearance/brand/Loader";

const LOADING: Record<string, string> = {
  discover: "Running Determinantal Point Process selection...",
  review: "Gathering your review questions...",
  lecture: "Picking questions for each concept...",
  mixed: "Mixing questions across your techniques...",
};

export function DiscoverRunner() {
  const {
    mode,
    nQuestions,
    reviewKind,
    concepts,
    questions,
    setQuestions,
    currentIndex,
    setCurrentIndex,
    quizStartTime,
    setQuizStartTime,
    questionStartTime,
    setQuestionStartTime,
    resetToggles,
    quizId,
    setQuizId,
    conceptLabels,
    setConceptLabels,
    results,
    diversityScore,
    setDiversityScore,
    shortfall,
    setShortfall,
  } = useQuizStore();

  const draft = useGenerateStore();

  const [loading, setLoading] = useState(questions.length === 0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (questions.length > 0) return; // Already started

    let active = true;
    const start = async () => {
      try {
        setLoading(true);
        const filters = draftToFilters(draft);
        let res: DiscoverResult;
        if (mode === "review") res = await ipc.quiz_review_start(draft.subject, reviewKind, nQuestions);
        else if (mode === "lecture") res = await ipc.quiz_concepts_start(filters, concepts, nQuestions, "LECTURE");
        else if (mode === "mixed") res = await ipc.quiz_concepts_start(filters, concepts, nQuestions, "MIXED");
        else res = await ipc.quiz_discover(filters, nQuestions);

        if (!active) return;

        if (!res.success || !res.questions || res.questions.length === 0) {
          setError(res.error || "No questions match these settings.");
          setLoading(false);
          return;
        }

        setQuestions(res.questions);
        setQuizId(res.quiz_id ?? null);
        setDiversityScore(res.diversity_score ?? null);
        setConceptLabels(res.concept_labels ?? {});
        setShortfall(res.shortfall ?? 0);
        setCurrentIndex(0);

        const now = Date.now();
        setQuizStartTime(now);
        setQuestionStartTime(now);
        setLoading(false);
      } catch (e: any) {
        if (!active) return;
        setError(e.message || "IPC error");
        setLoading(false);
      }
    };
    start();

    return () => { active = false; };
    // The session starts once from the settings at mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [questions.length]);

  const current = questions[currentIndex];
  const currentId = current?.question_id;

  useEffect(() => {
    if (quizId && currentId != null) void ipc.quiz_mark_presented(quizId, currentId).catch(() => undefined);
  }, [quizId, currentId]);

  const handleNext = () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex(currentIndex + 1);
      setQuestionStartTime(Date.now());
      resetToggles();
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
      setQuestionStartTime(Date.now());
      resetToggles();
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 space-y-4">
        <div className="text-error font-medium">{error}</div>
      </div>
    );
  }

  if (loading && questions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 space-y-4">
        <MatrixLoader className="w-28" />
        <div className="text-muted">{LOADING[mode] ?? LOADING.discover}</div>
      </div>
    );
  }

  if (!current) return null;

  const result = results[current.question_id];
  const answered = Boolean(result && !result.pending);
  const label = conceptLabels[String(current.question_id)];
  const nAnswered = questions.filter((q) => {
    const r = results[q.question_id];
    return r && !r.pending;
  }).length;

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-20">
      <div className="flex flex-wrap items-center justify-between gap-4 bg-surface p-4 rounded-lg border border-border">
        <div className="flex items-center gap-6 text-sm">
          <div className="flex flex-col">
            <span className="text-muted text-xs uppercase tracking-wider font-semibold">Since Question</span>
            <ElapsedTime startTime={questionStartTime} />
          </div>
          <div className="w-px h-8 bg-border" />
          <div className="flex flex-col">
            <span className="text-muted text-xs uppercase tracking-wider font-semibold">Since Start</span>
            <ElapsedTime startTime={quizStartTime} />
          </div>
        </div>

        <div className="flex flex-col items-end gap-1 text-sm">
          <div className="font-medium">
            Question {currentIndex + 1} of {questions.length}
          </div>
          <div className="text-xs text-muted">{nAnswered} answered</div>
          {mode === "discover" && diversityScore !== null && (
            <div className="text-xs text-muted">
              Diversity Score: {(diversityScore * 100).toFixed(1)}%
            </div>
          )}
          {shortfall > 0 && (
            <div className="text-xs text-warning">{shortfall} fewer than asked matched these concepts.</div>
          )}
        </div>
      </div>

      {mode === "lecture" && label && (
        <div className="text-sm text-muted">
          Concept: <span className="font-medium text-text">{label}</span>
        </div>
      )}
      {mode === "mixed" && (
        <div className="text-sm text-muted">
          {answered && label ? (
            <>
              Technique: <span className="font-medium text-text">{label}</span>
            </>
          ) : (
            "Decide which technique this needs. The label shows once you have answered."
          )}
        </div>
      )}

      <div className="bg-surface p-6 rounded-lg border border-border shadow-sm min-h-[400px]">
        <QuestionViewer question={current} hideLabels={mode === "mixed" && !answered}>
          <PracticeAnswer key={current.question_id} quizId={quizId} question={current} />
        </QuestionViewer>
      </div>

      <div className="fixed bottom-0 left-0 right-0 p-4 bg-background/80 backdrop-blur border-t border-border z-10 flex justify-center">
        <div className="flex items-center justify-between gap-6 max-w-4xl w-full">
          <button
            onClick={handlePrev}
            disabled={currentIndex === 0}
            className="flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-colors hover:bg-surface disabled:opacity-50 disabled:cursor-not-allowed border border-border"
          >
            <ChevronLeft size={20} />
            Previous
          </button>

          <button
            onClick={handleNext}
            disabled={currentIndex === questions.length - 1}
            className="flex items-center gap-2 bg-primary text-on-primary px-6 py-3 rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next Question
            <ChevronRight size={20} />
          </button>
        </div>
      </div>
    </div>
  );
}
