/**
 * The answer panel in Traverse / Discover. These modes have no slots: answers
 * name the question, are graded from its answer key, and are logged on the
 * session's attempt (one point times the credit).
 *
 * The question viewer can still show the answer and solution on request.
 * Opening either before answering ends the attempt at grading: the panel then
 * says the question is not graded instead of offering inputs.
 */

import { useEffect } from "react";

import { AnswerPanel } from "./AnswerPanel";
import { ipc, type QuizQuestionFull } from "../../lib/ipc";
import { useQuizStore } from "../../state/quiz";

interface Props {
  quizId: string | null;
  question: QuizQuestionFull;
}

export function PracticeAnswer({ quizId, question }: Props) {
  const { showAnswer, showSolution, questionStartTime, results, revealedIds, setResult, markRevealed } =
    useQuizStore();
  const qid = question.question_id;
  const result = results[qid] ?? null;
  const revealed = Boolean(revealedIds[qid]);

  useEffect(() => {
    if ((showAnswer || showSolution) && !result) markRevealed(qid);
  }, [showAnswer, showSolution, result, qid, markRevealed]);

  if (!quizId || question.answer_fields.length === 0) return null;

  return (
    <div className="rounded-lg border border-border bg-surface/50 p-4">
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
          })
        }
        assess={(marks) => ipc.quiz_self_assess(quizId, 0, { marks, question_id: qid })}
        onResult={(r) => setResult(qid, r)}
      />
    </div>
  );
}
