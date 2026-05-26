"use client";

import { useState } from "react";
import { LatexBlock } from "@/components/latex-block";
import { Card } from "@/components/ui/Card";

type CourseOpt = { id: number; code: string; name: string; slug: string };

export function AuthorForm({
  courses,
  knownTopics,
  knownBranches,
  knownSubtopics,
}: {
  courses: CourseOpt[];
  knownTopics: string[];
  knownBranches: string[];
  knownSubtopics: string[];
}) {
  const [topic, setTopic] = useState("");
  const [branch, setBranch] = useState("");
  const [subtopic, setSubtopic] = useState("");
  const [type, setType] = useState<
    "numerical" | "proof" | "explanation/reasoning"
  >("numerical");
  const [latexcode, setLatex] = useState("");
  const [answer, setAnswer] = useState("");
  const [solution, setSolution] = useState("");
  const [source, setSource] = useState("");
  const [courseId, setCourseId] = useState<number | null>(
    courses[0]?.id ?? null
  );
  const [submitting, setSubmitting] = useState(false);
  const [stage, setStage] = useState<
    "idle" | "saving" | "vectorizing" | "indexing"
  >("idle");
  const [done, setDone] = useState<string | null>(null);
  const [error, setError] = useState<string>("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    setStage("saving");
    // Server-side: insert → tags → embed → index. We advance the stage label
    // on a timer so the user sees the steps even though the endpoint is one call.
    const stageTimer1 = setTimeout(() => setStage("vectorizing"), 350);
    const stageTimer2 = setTimeout(() => setStage("indexing"), 1100);
    try {
      const res = await fetch("/api/drafts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic,
          branch,
          subtopic,
          type,
          latexcode,
          answer: answer || null,
          solution: solution || null,
          source: source || null,
          course_id: courseId,
        }),
      });
      if (!res.ok) {
        const j = await res.json().catch(() => ({}));
        throw new Error(j.error || `HTTP ${res.status}`);
      }
      const json = await res.json();
      setDone(`Question #${json.id} is live. Embedded, tagged, and searchable.`);
      // Reset for the next submission.
      setTopic("");
      setBranch("");
      setSubtopic("");
      setLatex("");
      setAnswer("");
      setSolution("");
      setSource("");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      clearTimeout(stageTimer1);
      clearTimeout(stageTimer2);
      setSubmitting(false);
      setStage("idle");
    }
  }

  const stageLabel: Record<typeof stage, string> = {
    idle: "Add to the bank",
    saving: "Saving the question…",
    vectorizing: "Vectorizing with Gemini…",
    indexing: "Indexing for similarity search…",
  };
  const stagePct: Record<typeof stage, number> = {
    idle: 0,
    saving: 25,
    vectorizing: 65,
    indexing: 90,
  };

  if (done) {
    return (
      <div className="rounded-md border border-emerald-200 bg-emerald-50 p-6">
        <h2 className="font-medium text-emerald-900">✓ Submitted</h2>
        <p className="mt-1 text-sm text-emerald-800">{done}</p>
        <button
          onClick={() => setDone(null)}
          className="mt-4 rounded-md bg-emerald-700 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-800"
        >
          Add another
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="grid gap-8 lg:grid-cols-2">
      {/* Left: form */}
      <div className="flex flex-col gap-4">
        <div className="grid grid-cols-3 gap-3">
          <Field label="Topic" required>
            <input
              required
              list="known-topics"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Pick or type a new one"
              className="input"
            />
            <datalist id="known-topics">
              {knownTopics.map((t) => (
                <option key={t} value={t} />
              ))}
            </datalist>
          </Field>
          <Field label="Branch" required>
            <input
              required
              list="known-branches"
              value={branch}
              onChange={(e) => setBranch(e.target.value)}
              placeholder="Pick or type a new one"
              className="input"
            />
            <datalist id="known-branches">
              {knownBranches.map((b) => (
                <option key={b} value={b} />
              ))}
            </datalist>
          </Field>
          <Field label="Subtopic" required>
            <input
              required
              list="known-subtopics"
              value={subtopic}
              onChange={(e) => setSubtopic(e.target.value)}
              placeholder="Pick or type a new one"
              className="input"
            />
            <datalist id="known-subtopics">
              {knownSubtopics.map((s) => (
                <option key={s} value={s} />
              ))}
            </datalist>
          </Field>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <Field label="Type" required>
            <select
              value={type}
              onChange={(e) =>
                setType(
                  e.target.value as
                    | "numerical"
                    | "proof"
                    | "explanation/reasoning"
                )
              }
              className="input"
            >
              <option value="numerical">numerical</option>
              <option value="proof">proof</option>
              <option value="explanation/reasoning">
                explanation/reasoning
              </option>
            </select>
          </Field>
          {courses.length > 0 && (
            <Field label="Course (your institution)">
              <select
                value={courseId ?? ""}
                onChange={(e) =>
                  setCourseId(
                    e.target.value ? Number.parseInt(e.target.value, 10) : null
                  )
                }
                className="input"
              >
                <option value="">— general / unassigned —</option>
                {courses.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.code} — {c.name}
                  </option>
                ))}
              </select>
            </Field>
          )}
        </div>

        <Field label="Question (LaTeX)" required>
          <textarea
            required
            value={latexcode}
            onChange={(e) => setLatex(e.target.value)}
            rows={6}
            placeholder="Prove that $\\int_0^1 x^2 \\, dx = \\tfrac{1}{3}$."
            className="input font-mono text-sm"
          />
        </Field>

        <Card
          title="Answer"
          actions={
            <span className="text-[10px] font-normal normal-case tracking-normal text-ink-400">
              optional · recommended for numerical
            </span>
          }
        >
          <p className="mb-2 text-xs text-ink-500">
            Used by the auto-grader for instant feedback during practice.
            Leave blank for proof / explanation questions.
          </p>
          <input
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="e.g. $\\tfrac{1}{3}$ or 42 or $e^{i\\pi}$"
            className="input"
          />
        </Card>

        <Card
          title="Solution"
          actions={
            <span className="text-[10px] font-normal normal-case tracking-normal text-ink-400">
              optional · shown on Reveal
            </span>
          }
        >
          <p className="mb-2 text-xs text-ink-500">
            The worked-out solution in LaTeX. Renders in the &ldquo;Reveal
            solution&rdquo; toggle on the question page.
          </p>
          <textarea
            value={solution}
            onChange={(e) => setSolution(e.target.value)}
            rows={8}
            placeholder="By the power rule, $\\int_0^1 x^2 \\, dx = \\left[\\tfrac{x^3}{3}\\right]_0^1 = \\tfrac{1}{3}$."
            className="input font-mono text-sm"
          />
        </Card>

        <Field label="Source (optional)">
          <input
            value={source}
            onChange={(e) => setSource(e.target.value)}
            placeholder="e.g. IITD-AD Quiz 2024-Fall"
            className="input"
          />
        </Field>

        {error && <p className="text-sm text-red-600">{error}</p>}

        {submitting && (
          <div className="rounded-md border border-brand-200 bg-brand-50 p-3">
            <div className="mb-2 flex items-center justify-between text-xs">
              <span className="font-medium text-brand-700">
                {stageLabel[stage]}
              </span>
              <span className="text-brand-600 tabular-nums">
                {stagePct[stage]}%
              </span>
            </div>
            <div className="h-1 overflow-hidden rounded-full bg-brand-100">
              <div
                className="h-full bg-brand-500 transition-all duration-500 ease-out"
                style={{ width: `${stagePct[stage]}%` }}
              />
            </div>
          </div>
        )}

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={submitting}
            className="rounded-md bg-ink-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-ink-700 disabled:opacity-50"
          >
            {submitting ? stageLabel[stage] : "Submit to the bank"}
          </button>
        </div>
      </div>

      {/* Right: live preview */}
      <div className="lg:sticky lg:top-6 lg:self-start">
        <div className="text-xs font-medium uppercase tracking-wider text-ink-500">
          Live preview
        </div>
        <div className="mt-3 rounded-lg border border-ink-200 bg-white p-6 shadow-sm">
          {topic || branch || subtopic ? (
            <div className="mb-2 flex flex-wrap items-center gap-1 text-xs text-ink-500">
              {topic && (
                <span className="rounded-full bg-ink-100 px-2 py-0.5">
                  {topic}
                </span>
              )}
              {branch && (
                <>
                  <span>›</span>
                  <span>{branch}</span>
                </>
              )}
              {subtopic && (
                <>
                  <span>›</span>
                  <span>{subtopic}</span>
                </>
              )}
            </div>
          ) : null}

          {latexcode ? (
            <LatexBlock src={latexcode} className="text-lg leading-relaxed" />
          ) : (
            <p className="text-sm text-ink-400">
              Start typing the question to see it render.
            </p>
          )}

          {solution && (
            <div className="mt-6 border-t border-ink-200 pt-4">
              <div className="mb-2 text-xs font-medium uppercase tracking-wider text-ink-500">
                Solution
              </div>
              <LatexBlock src={solution} />
            </div>
          )}
        </div>

        <p className="mt-3 text-xs text-ink-500">
          LaTeX supports inline <code>$...$</code> and display{" "}
          <code>$$...$$</code>. Question bodies are not sanitised; write the
          LaTeX you&apos;d put in a textbook.
        </p>
      </div>

      <style jsx>{`
        :global(.input) {
          width: 100%;
          border-radius: 0.375rem;
          border: 1px solid var(--border, #d6d8de);
          padding: 0.5rem 0.75rem;
          font-size: 0.875rem;
          background: var(--surface, #ffffff);
          color: var(--text, #0a0c14);
        }
        :global(.input::placeholder) {
          color: var(--muted, #7a8090);
          opacity: 0.7;
        }
        :global(.input:focus) {
          outline: none;
          border-color: var(--primary, #52596b);
        }
      `}</style>
    </form>
  );
}

function Field({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium uppercase tracking-wider text-ink-500">
        {label}
        {required && <span className="ml-1 text-red-500">*</span>}
      </span>
      {children}
    </label>
  );
}
