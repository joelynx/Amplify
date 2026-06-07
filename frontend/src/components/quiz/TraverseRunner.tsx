import { useEffect, useState } from "react";
import { ChevronRight, Loader2 } from "lucide-react";
import { ipc } from "../../lib/ipc";
import { useQuizStore } from "../../state/quiz";
import { useGenerateStore, draftToFilters } from "../../state/generate";
import { ElapsedTime } from "./ElapsedTime";
import { QuestionViewer } from "./QuestionViewer";

export function TraverseRunner() {
  const {
    diversity,
    setDiversity,
    questions,
    setQuestions,
    currentIndex,
    setCurrentIndex,
    quizStartTime,
    setQuizStartTime,
    questionStartTime,
    setQuestionStartTime,
    resetToggles,
    useSeed,
    seedId,
    seedDiversity,
  } = useQuizStore();

  const draft = useGenerateStore();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [quizId, setQuizId] = useState<string | null>(null);
  const [remaining, setRemaining] = useState<number | null>(null);

  // Initialize Traverse
  useEffect(() => {
    if (questions.length > 0 || quizId) return; // Already started
    
    let active = true;
    const start = async () => {
      try {
        setLoading(true);
        const filters = draftToFilters(draft);
        const res = await ipc.quiz_traverse_start(
          filters,
          useSeed ? seedId : null,
          useSeed ? seedDiversity : undefined
        );
        
        if (!active) return;
        
        if (!res.success || !res.question || !res.quiz_id) {
          setError(res.error || "Failed to start Traverse mode");
          setLoading(false);
          return;
        }
        
        setQuizId(res.quiz_id);
        setQuestions([res.question]);
        setCurrentIndex(0);
        setRemaining(res.pool_size ? res.pool_size - 1 : 0);
        
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
  }, [draft, questions.length, quizId, setCurrentIndex, setQuestionStartTime, setQuestions, setQuizStartTime]);

  const handleNext = async () => {
    if (!quizId) return;
    
    try {
      setLoading(true);
      const currentQ = questions[currentIndex];
      const res = await ipc.quiz_traverse_next(quizId, currentQ.question_id, diversity);
      
      if (!res.success) {
        setError(res.error || "Failed to get next question");
        setLoading(false);
        return;
      }
      
      if (!res.question) {
        // Pool exhausted
        setRemaining(0);
        setLoading(false);
        return;
      }
      
      setQuestions([...questions, res.question]);
      setCurrentIndex(currentIndex + 1);
      setRemaining(res.remaining ?? 0);
      setQuestionStartTime(Date.now());
      resetToggles();
      setLoading(false);
      
      // Scroll to top smoothly
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (e: any) {
      setError(e.message || "IPC error");
      setLoading(false);
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
        <div className="text-muted">Initializing Traverse mode...</div>
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
        
        <div className="flex items-center gap-2 text-sm">
          <span className="text-muted">Unseen remaining:</span>
          <span className="font-medium tabular-nums">{remaining !== null ? remaining : "—"}</span>
        </div>
      </div>

      <div className="bg-surface p-6 rounded-lg border border-border shadow-sm min-h-[400px]">
        <QuestionViewer question={currentQuestion} />
      </div>

      <div className="fixed bottom-0 left-0 right-0 p-4 bg-background/80 backdrop-blur border-t border-border z-10 flex justify-center">
        <div className="flex items-center gap-6 max-w-4xl w-full">
          <div className="flex-1 flex flex-col space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted">Diversity</span>
              <span className="font-medium text-primary">{(diversity * 100).toFixed(0)}%</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-muted">Random</span>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={diversity}
                onChange={(e) => setDiversity(parseFloat(e.target.value))}
                className="flex-1 accent-primary"
                disabled={loading || remaining === 0}
              />
              <span className="text-xs text-muted">Similar</span>
            </div>
          </div>
          
          <button
            onClick={handleNext}
            disabled={loading || remaining === 0}
            className="flex items-center gap-2 bg-primary text-primary-foreground px-6 py-3 rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? <Loader2 size={20} className="animate-spin" /> : <ChevronRight size={20} />}
            {remaining === 0 ? "Pool Exhausted" : "Next Question"}
          </button>
        </div>
      </div>
    </div>
  );
}
