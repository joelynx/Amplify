import { Eye, EyeOff } from "lucide-react";
import type { QuizQuestionFull } from "../../lib/ipc";
import { LatexContent } from "../browser/LatexContent";
import { useQuizStore } from "../../state/quiz";

interface QuestionViewerProps {
  question: QuizQuestionFull;
}

export function QuestionViewer({ question }: QuestionViewerProps) {
  const {
    showHint,
    showAnswer,
    showSolution,
    showMetadata,
    setShowHint,
    setShowAnswer,
    setShowSolution,
    setShowMetadata,
  } = useQuizStore();

  return (
    <div className="flex flex-col space-y-6">
      <div className="flex flex-wrap gap-2 pb-4 border-b border-border">
        {question.hints && question.hints.trim() !== "" && (
          <button
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              showHint ? "bg-primary/10 text-primary" : "bg-surface text-text/80 hover:bg-surface-hover"
            }`}
            onClick={() => setShowHint(!showHint)}
          >
            {showHint ? <EyeOff size={16} /> : <Eye size={16} />}
            {showHint ? "Hide Hint" : "Show Hint"}
          </button>
        )}
        
        {question.answer && question.answer.trim() !== "" && (
          <button
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              showAnswer ? "bg-primary/10 text-primary" : "bg-surface text-text/80 hover:bg-surface-hover"
            }`}
            onClick={() => setShowAnswer(!showAnswer)}
          >
            {showAnswer ? <EyeOff size={16} /> : <Eye size={16} />}
            {showAnswer ? "Hide Answer" : "Show Answer"}
          </button>
        )}
        
        {question.solution && question.solution.trim() !== "" && (
          <button
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              showSolution ? "bg-primary/10 text-primary" : "bg-surface text-text/80 hover:bg-surface-hover"
            }`}
            onClick={() => setShowSolution(!showSolution)}
          >
            {showSolution ? <EyeOff size={16} /> : <Eye size={16} />}
            {showSolution ? "Hide Solution" : "Show Solution"}
          </button>
        )}

        <div className="flex-1" />

        <button
          className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
            showMetadata ? "bg-primary/10 text-primary" : "bg-surface text-text/80 hover:bg-surface-hover"
          }`}
          onClick={() => setShowMetadata(!showMetadata)}
        >
          {showMetadata ? <EyeOff size={16} /> : <Eye size={16} />}
          See Metadata
        </button>
      </div>

      {showMetadata && (
        <div className="bg-surface rounded-lg p-4 border border-border space-y-3 text-sm">
          <h3 className="font-semibold text-text mb-2">Question Metadata</h3>
          <div className="grid grid-cols-2 gap-4">
            <div><span className="text-muted">Topic:</span> {question.topic}</div>
            <div><span className="text-muted">Branch:</span> {question.branch}</div>
            <div><span className="text-muted">Subtopic:</span> {question.subtopic}</div>
            <div><span className="text-muted">Type:</span> {question.type || "—"}</div>
            <div><span className="text-muted">Source:</span> {question.source || "—"}</div>
            <div>
              <span className="text-muted">Difficulty:</span>{" "}
              {question.difficulty_rating !== null ? question.difficulty_rating.toFixed(1) + " / 20" : "—"}
            </div>
            <div><span className="text-muted">ID:</span> {question.question_id}</div>
            <div className="col-span-2 flex flex-wrap gap-1 mt-1">
              <span className="text-muted mr-2">Tags:</span>
              {question.tags.length > 0 ? (
                question.tags.map(t => (
                  <span key={t} className="px-2 py-0.5 bg-background border border-border rounded text-xs">
                    {t}
                  </span>
                ))
              ) : (
                <span className="text-muted italic">none</span>
              )}
            </div>
          </div>
        </div>
      )}

      {question.instructions && question.instructions.trim() !== "" && (
        <div className="bg-surface/50 border-l-4 border-primary p-4 rounded-r-md">
          <LatexContent source={question.instructions} />
        </div>
      )}

      <div className="prose dark:prose-invert max-w-none">
        <LatexContent source={question.latexcode} />
      </div>

      {showHint && question.hints && (
        <div className="mt-8 border border-border rounded-lg overflow-hidden">
          <div className="bg-surface px-4 py-2 font-medium border-b border-border">Hint</div>
          <div className="p-4 bg-background">
            <LatexContent source={question.hints} />
          </div>
        </div>
      )}

      {showAnswer && question.answer && (
        <div className="mt-8 border border-border rounded-lg overflow-hidden">
          <div className="bg-surface px-4 py-2 font-medium border-b border-border">Answer</div>
          <div className="p-4 bg-background">
            <LatexContent source={question.answer} />
          </div>
        </div>
      )}

      {showSolution && question.solution && (
        <div className="mt-8 border border-border rounded-lg overflow-hidden">
          <div className="bg-surface px-4 py-2 font-medium border-b border-border">Solution</div>
          <div className="p-4 bg-background">
            <LatexContent source={question.solution} />
          </div>
        </div>
      )}
    </div>
  );
}
