"use client";

import { useState } from "react";
import { LatexBlock } from "@/components/latex-block";

type CourseOpt = { id: number; code: string; name: string; slug: string };

export function AuthorForm({ courses }: { courses: CourseOpt[] }) {
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
  const [done, setDone] = useState<string | null>(null);
  const [error, setError] = useState<string>("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
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
      setDone(`Draft #${json.id} submitted. Moderators will review shortly.`);
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
      setSubmitting(false);
    }
  }

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
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g. Calculus"
              className="input"
            />
          </Field>
          <Field label="Branch" required>
            <input
              required
              value={branch}
              onChange={(e) => setBranch(e.target.value)}
              placeholder="e.g. Single Variable…"
              className="input"
            />
          </Field>
          <Field label="Subtopic" required>
            <input
              required
              value={subtopic}
              onChange={(e) => setSubtopic(e.target.value)}
              placeholder="e.g. Mean Value Theorem"
              className="input"
            />
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

        <Field label="Answer (optional)">
          <input
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="$\\tfrac{1}{3}$ — leave blank for non-numerical"
            className="input"
          />
        </Field>

        <Field label="Solution (LaTeX)">
          <textarea
            value={solution}
            onChange={(e) => setSolution(e.target.value)}
            rows={8}
            placeholder="By the power rule, $\\int_0^1 x^2 \\, dx = \\left[\\tfrac{x^3}{3}\\right]_0^1 = \\tfrac{1}{3}$."
            className="input font-mono text-sm"
          />
        </Field>

        <Field label="Source (optional)">
          <input
            value={source}
            onChange={(e) => setSource(e.target.value)}
            placeholder="e.g. IITD-AD Quiz 2024-Fall"
            className="input"
          />
        </Field>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={submitting}
            className="rounded-md bg-ink-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-ink-700 disabled:opacity-50"
          >
            {submitting ? "Submitting…" : "Submit for review"}
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
          border: 1px solid #d6d8de;
          padding: 0.5rem 0.75rem;
          font-size: 0.875rem;
          background: white;
        }
        :global(.input:focus) {
          outline: none;
          border-color: #52596b;
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
