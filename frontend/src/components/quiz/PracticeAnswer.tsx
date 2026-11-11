/**
 * The answer panel in Traverse / Discover. These modes have no slots: answers
 * name the question, are graded from its answer key, and are logged on the
 * session's attempt (one point times the credit).
 *
 * The question viewer can still show the answer and solution on request.
 * Opening either before answering ends the attempt at grading: the panel then
 * says the question is not graded instead of offering inputs, and the reveal
 * is logged so the question lands on the "try it independently" review list.
 * A hint opened before answering is sent as `hints_used` (an assisted answer).
 */

import { useEffect } from "react";

import { AnswerPanel } from "./AnswerPanel";
import { emit } from "../../appearance/events";
import { ipc, type QuizQuestionFull } from "../../lib/ipc";
import { useQuizStore } from "../../state/quiz";

interface Props {
  quizId: string | null;
  question: QuizQuestionFull;
}

export function PracticeAnswer({ quizId, question }: Props) {
  const {
    showAnswer,
    showSolution,
    questionStartTime,
    results,
    revealedIds,
    hintedIds,
    drafts,
    setResult,
    markRevealed,
    setDraft,
  } = useQuizStore();
  const qid = question.question_id;
  const result = results[qid] ?? null;
  const revealed = Boolean(revealedIds[qid]);
  const gradable = question.answer_fields.length > 0;

  useEffect(() => {
    if ((showAnswer || showSolution) && !result && !revealed) {
      markRevealed(qid);
      emit({ type: "reveal" });
      if (quizId && gradable) void ipc.quiz_log_reveal(quizId, qid).catch(() => undefined);
    }
  }, [showAnswer, showSolution, result, revealed, qid, quizId, gradable, markRevealed]);

  if (!quizId || question.answer_fields.length === 0) return null;

  return (
    <div data-ui="answer" className="rounded-lg border border-border bg-surface/50 p-4">
      <div className="mb-3 text-xs font-medium uppercase tracking-wide text-muted">Your answer</div>
      <AnswerPanel
        fields={question.answer_fields}
        result={result}
        lockedNote={
          revealed && !result ? "You opened the answer or solution before answering, so this one is not graded." : null
        }
        submit={(answers) =>
          ipc.quiz_submit_answer(quizId, 0, {
            answers,
            question_id: qid,
            time_taken_ms: questionStartTime ? Date.now() - questionStartTime : 0,
            hints_used: hintedIds[qid] ? 1 : 0,
          })
        }
        assess={(marks) => ipc.quiz_self_assess(quizId, 0, { marks, question_id: qid })}
        onResult={(r) => setResult(qid, r)}
        draft={drafts[qid]}
        onDraft={(inputs) => setDraft(qid, inputs)}
        assisted={Boolean(hintedIds[qid]) || revealed}
      />
    </div>
  );
}
