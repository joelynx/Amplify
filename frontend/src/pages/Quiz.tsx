/**
 * Quiz wrapper page — three states:
 *
 *   1. Settings panel (default).
 *   2. Active runner (non-PBS or PBS, after Start).
 *   3. Inline summary card (after Finish; click "View review" to navigate
 *      to /quiz/review/:id).
 */

import { useNavigate } from "react-router-dom";
import { useState } from "react";

import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { PBSGridRunner } from "../components/quiz/PBSGridRunner";
import { QuizSettingsPanel } from "../components/quiz/QuizSettings";
import { SingleWidgetRunner } from "../components/quiz/SingleWidgetRunner";
import { useSubjectStore } from "../state/subject";
import {
  ipc,
  type QuizSettings,
  type QuizSlot,
  type StartQuizResult,
} from "../lib/ipc";

type Phase =
  | { kind: "settings" }
  | { kind: "running"; result: StartQuizResult; settings: QuizSettings }
  | { kind: "done"; attempt_id: string };

export default function QuizPage() {
  const activeSubject = useSubjectStore((s) => s.active);
  const [phase, setPhase] = useState<Phase>({ kind: "settings" });
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleStart = async (settings: QuizSettings) => {
    setError(null);
    const r = await ipc.start_quiz(
      {
        subject: activeSubject,
        reuse_questions: true,
        in_syllabus_only: true,
      },
      settings,
    );
    if (!r.success) {
      setError(r.error ?? "Could not start quiz");
      return;
    }
    setPhase({ kind: "running", result: r, settings });
  };

  const handleFinished = (attemptId: string) => {
    setPhase({ kind: "done", attempt_id: attemptId });
  };

  return (
    <main className="h-full overflow-y-auto">
      {phase.kind === "settings" && (
        <>
          <QuizSettingsPanel onStart={handleStart} />
          {error && (
            <div className="mx-auto max-w-3xl px-6 pb-6">
              <p className="rounded-md border border-error bg-error/10 px-3 py-2 text-sm text-error">
                {error}
              </p>
            </div>
          )}
        </>
      )}

      {phase.kind === "running" && phase.result.mode === "non_pbs" && (
        <SingleWidgetRunner
          quizId={phase.result.quiz_id!}
          settings={phase.settings}
          initial={(phase.result.initial_widgets ?? [])[0] as QuizSlot}
          totalTimeS={phase.result.total_time_s ?? null}
          onFinished={handleFinished}
        />
      )}

      {phase.kind === "running" && phase.result.mode === "pbs" && (
        <PBSGridRunner
          quizId={phase.result.quiz_id!}
          settings={phase.settings}
          initial={phase.result.initial_widgets ?? []}
          totalTimeS={phase.result.total_time_s ?? null}
          onFinished={handleFinished}
        />
      )}

      {phase.kind === "done" && (
        <div className="mx-auto max-w-3xl px-6 py-10">
          <Card title="Quiz finished">
            <p className="mb-3 text-sm">Attempt recorded as <code className="font-mono">{phase.attempt_id}</code>.</p>
            <div className="flex flex-wrap gap-2">
              <Button variant="primary" onClick={() => navigate(`/quiz/review/${phase.attempt_id}`)}>
                View review
              </Button>
              <Button variant="outline" onClick={() => setPhase({ kind: "settings" })}>
                Run another
              </Button>
            </div>
          </Card>
        </div>
      )}
    </main>
  );
}
