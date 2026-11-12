import type { ReactNode } from "react";
import { emit } from "../../appearance/events";
import { ThemedIcon } from "../../appearance/icons/ThemedIcon";
import { Eye, EyeOff } from "lucide-react";
import type { QuizQuestionFull } from "../../lib/ipc";
import { LatexContent } from "../browser/LatexContent";
import { BookmarkButton, SelfExplain } from "../notes/QuestionNotes";
import { Flaggable } from "../notes/ContentFlag";
import { useQuizStore } from "../../state/quiz";

interface QuestionViewerProps {
  question: QuizQuestionFull;
  /** Shown right under the question (the answer panel). */
  children?: ReactNode;
  /** Mixed review: keep the metadata (topic, tags) out of sight so the
   * student has to choose the method; the runner lifts it once answered. */
  hideLabels?: boolean;
}

export function QuestionViewer({ question, children, hideLabels = false }: QuestionViewerProps) {
  const {
    hintLevel,
    showAnswer,
    showSolution,
    showMetadata,
    setHintLevel,
    setShowAnswer,
    setShowSolution,
    setShowMetadata,
    markHinted,
    results,
  } = useQuizStore();
  const result = results[question.question_id];
  const answered = Boolean(result && !result.pending);
  const helpButton = (on: boolean) =>
    `flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
      on ? "bg-primary/10 text-primary" : "bg-surface text-text/80 hover:bg-background"
    }`;
  // Hint tiers are revealed one at a time; each says more than the one before.
  const tiers = question.hint_tiers ?? (question.hints?.trim() ? [question.hints] : []);
  const hasHint = tiers.length > 0;
  const shownTiers = Math.min(hintLevel, tiers.length);
  const moreHints = shownTiers < tiers.length;
  const hasAnswer = Boolean(question.answer?.trim());
  const hasSolution = Boolean(question.solution?.trim());
  // What opening help does to this answer, said before the click.
  const consequence =
    answered || question.answer_fields.length === 0
      ? null
      : [
          hasHint ? "A hint counts this answer as solved with help." : null,
          hasAnswer || hasSolution
            ? "Revealing the answer or solution before you answer leaves this question ungraded; it comes back later for a try on your own."
            : null,
        ]
          .filter(Boolean)
          .join(" ");

  return (
    <div className="flex flex-col space-y-6">
      <div className="flex flex-wrap gap-2 pb-4 border-b border-border">
        <div className="flex-1" />

        <BookmarkButton questionId={question.question_id} />

        {!hideLabels && (
          <button
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              showMetadata ? "bg-primary/10 text-primary" : "bg-surface text-text/80 hover:bg-background"
            }`}
            onClick={() => setShowMetadata(!showMetadata)}
          >
            {showMetadata ? <EyeOff size={16} /> : <Eye size={16} />}
            {showMetadata ? "Hide details" : "Question details"}
          </button>
        )}
      </div>

      {showMetadata && !hideLabels && (
        <div className="bg-surface rounded-lg p-4 border border-border space-y-3 text-sm">
          <h3 className="font-semibold text-text mb-2">Question details</h3>
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

      <div data-ui="question" className="prose dark:prose-invert max-w-none">
        <LatexContent source={question.latexcode} />
      </div>

      {children}

      {/* Help comes after the answer area: the attempt first, then hint / reveal. */}
      {(hasHint || hasAnswer || hasSolution) && (
        <div data-ui="help-row" className="flex flex-wrap items-center gap-2 border-t border-border pt-4">
          <span className="mr-1 text-xs font-medium uppercase tracking-wide text-muted">Help</span>
          {hasHint && (
            <button
              className={`${helpButton(shownTiers > 0)} disabled:cursor-not-allowed disabled:opacity-50`}
              disabled={!moreHints}
              title={moreHints ? undefined : "No more hints for this question"}
              onClick={() => {
                const next = shownTiers + 1;
                // A hint opened before answering makes the answer "assisted".
                if (!answered) {
                  markHinted(question.question_id, next);
                  emit({ type: "hint" });
                }
                setHintLevel(next);
              }}
            >
              <ThemedIcon name="hint" className="h-4 w-4" />
              {shownTiers === 0 ? "Show hint" : "Show additional hint"}
            </button>
          )}
          {hasAnswer && (
            <button className={helpButton(showAnswer)} aria-pressed={showAnswer} onClick={() => setShowAnswer(!showAnswer)}>
              {showAnswer ? <EyeOff size={16} /> : <ThemedIcon name="reveal" className="h-4 w-4" />}
              {showAnswer ? "Hide answer" : "Reveal answer"}
            </button>
          )}
          {hasSolution && (
            <button className={helpButton(showSolution)} aria-pressed={showSolution} onClick={() => setShowSolution(!showSolution)}>
              {showSolution ? <EyeOff size={16} /> : <Eye size={16} />}
              {showSolution ? "Hide solution" : "Reveal solution"}
            </button>
          )}
          {consequence && (
            <p data-ui="help-consequence" className="basis-full text-xs text-muted">
              {consequence}
            </p>
          )}
        </div>
      )}

      {shownTiers > 0 && (
        <div className="border border-border rounded-lg overflow-hidden">
          <div className="bg-surface px-4 py-2 font-medium border-b border-border">
            {tiers.length > 1 ? "Hints" : "Hint"}
          </div>
          <div className="p-4 bg-background">
            <Flaggable questionId={question.question_id} part="hint">
              {tiers.slice(0, shownTiers).map((tier, i) => (
                <div key={i} data-ui="hint-tier" className={i > 0 ? "border-t border-border pt-3" : undefined}>
                  {tiers.length > 1 && (
                    <div className="mb-1 text-xs font-medium uppercase tracking-wide text-muted">
                      Hint {i + 1} of {tiers.length}
                    </div>
                  )}
                  <LatexContent source={tier} />
                </div>
              ))}
            </Flaggable>
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
            <Flaggable questionId={question.question_id} part="solution">
              <LatexContent source={question.solution} />
            </Flaggable>
          </div>
        </div>
      )}

      {(showSolution || answered) && <SelfExplain questionId={question.question_id} />}
    </div>
  );
}
