import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight, Loader2 } from "lucide-react";
import { ipc } from "../../lib/ipc";
import { useQuizStore } from "../../state/quiz";
import { useGenerateStore, draftToFilters } from "../../state/generate";
import { ElapsedTime } from "./ElapsedTime";
import { QuestionViewer } from "./QuestionViewer";

export function DiscoverRunner() {
  const {
    nQuestions,
    questions,
    setQuestions,
    currentIndex,
    setCurrentIndex,
    quizStartTime,
    setQuizStartTime,
    questionStartTime,
    setQuestionStartTime,
    resetToggles,
  } = useQuizStore();

  const draft = useGenerateStore();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [diversityScore, setDiversityScore] = useState<number | null>(null);

  // Initialize Discover
  useEffect(() => {
    if (questions.length > 0) return; // Already started
    
    let active = true;
    const start = async () => {
      try {
        setLoading(true);
        const filters = draftToFilters(draft);
        const res = await ipc.quiz_discover(filters, nQuestions);
        
        if (!active) return;
        
        if (!res.success || !res.questions || res.questions.length === 0) {
          setError(res.error || "Failed to find diverse questions matching your filters.");
          setLoading(false);
          return;
        }
        
        setQuestions(res.questions);
        setDiversityScore(res.diversity_score ?? null);
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
  }, [draft, nQuestions, questions.length, setCurrentIndex, setQuestionStartTime, setQuestions, setQuizStartTime]);

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
        <Loader2 className="animate-spin text-primary" size={32} />
        <div className="text-muted">Running Determinantal Point Process selection...</div>
      </div>
    );
  }

  const currentQuestion = questions[currentIndex];
  if (!currentQuestion) return null;

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
          {diversityScore !== null && (
            <div className="text-xs text-muted">
              Diversity Score: {(diversityScore * 100).toFixed(1)}%
            </div>
          )}
        </div>
      </div>

      <div className="bg-surface p-6 rounded-lg border border-border shadow-sm min-h-[400px]">
        <QuestionViewer question={currentQuestion} />
      </div>

      <div className="fixed bottom-0 left-0 right-0 p-4 bg-background/80 backdrop-blur border-t border-border z-10 flex justify-center">
        <div className="flex items-center justify-between gap-6 max-w-4xl w-full">
          <button
            onClick={handlePrev}
            disabled={currentIndex === 0}
            className="flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-colors hover:bg-surface-hover disabled:opacity-50 disabled:cursor-not-allowed border border-border"
          >
            <ChevronLeft size={20} />
            Previous
          </button>
          
          <button
            onClick={handleNext}
            disabled={currentIndex === questions.length - 1}
            className="flex items-center gap-2 bg-primary text-primary-foreground px-6 py-3 rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next Question
            <ChevronRight size={20} />
          </button>
        </div>
      </div>
    </div>
  );
}
