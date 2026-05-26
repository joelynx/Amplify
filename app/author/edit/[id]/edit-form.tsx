"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { LatexBlock } from "@/components/latex-block";

export function EditForm({
  questionId,
  initial,
}: {
  questionId: number;
  initial: {
    topic: string;
    branch: string;
    subtopic: string;
    type: string;
    latexcode: string;
    answer: string;
    solution: string;
    source: string;
  };
}) {
  const router = useRouter();
  const [topic, setTopic] = useState(initial.topic);
  const [branch, setBranch] = useState(initial.branch);
  const [subtopic, setSubtopic] = useState(initial.subtopic);
  const [type, setType] = useState(initial.type);
  const [latexcode, setLatex] = useState(initial.latexcode);
  const [answer, setAnswer] = useState(initial.answer);
  const [solution, setSolution] = useState(initial.solution);
  const [source, setSource] = useState(initial.source);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    const res = await fetch(`/api/drafts/${questionId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        topic,
        branch,
        subtopic,
        type,
        latexcode,
        answer,
        solution,
        source,
      }),
    });
    if (!res.ok) {
      const j = await res.json().catch(() => ({}));
      setError(j.error || `HTTP ${res.status}`);
      setSubmitting(false);
      return;
    }
    setDone(true);
    setSubmitting(false);
    router.refresh();
  }

  return (
    <form onSubmit={onSubmit} className="grid gap-8 lg:grid-cols-2">
      <div className="flex flex-col gap-4">
        <div className="grid grid-cols-3 gap-3">
          <Field label="Topic">
            <input
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              className="input"
            />
          </Field>
          <Field label="Branch">
            <input
              value={branch}
              onChange={(e) => setBranch(e.target.value)}
              className="input"
            />
          </Field>
          <Field label="Subtopic">
            <input
              value={subtopic}
              onChange={(e) => setSubtopic(e.target.value)}
              className="input"
            />
          </Field>
        </div>

        <Field label="Type">
          <select
            value={type}
            onChange={(e) => setType(e.target.value)}
            className="input"
          >
            <option value="numerical">numerical</option>
            <option value="proof">proof</option>
            <option value="explanation/reasoning">explanation/reasoning</option>
          </select>
        </Field>

        <Field label="Question (LaTeX)">
          <textarea
            value={latexcode}
            onChange={(e) => setLatex(e.target.value)}
            rows={6}
            className="input font-mono text-sm"
          />
        </Field>

        <Field label="Answer">
          <input
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            className="input"
          />
        </Field>

        <Field label="Solution">
          <textarea
            value={solution}
            onChange={(e) => setSolution(e.target.value)}
            rows={6}
            className="input font-mono text-sm"
          />
        </Field>

        <Field label="Source">
          <input
            value={source}
            onChange={(e) => setSource(e.target.value)}
            className="input"
          />
        </Field>

        {error && <p className="text-sm text-red-600">{error}</p>}
        {done && (
          <p className="text-sm text-emerald-700">Saved.</p>
        )}

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={submitting}
            className="rounded-md bg-ink-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-ink-700 disabled:opacity-50"
          >
            {submitting ? "Saving…" : "Save changes"}
          </button>
        </div>
      </div>

      <div className="lg:sticky lg:top-6 lg:self-start">
        <div className="text-xs font-medium uppercase tracking-wider text-ink-500">
          Live preview
        </div>
        <div className="mt-3 rounded-lg border border-ink-200 bg-white p-6 shadow-sm">
          <div className="mb-2 flex flex-wrap items-center gap-1 text-xs text-ink-500">
            <span className="rounded-full bg-ink-100 px-2 py-0.5">{topic}</span>
            <span>›</span>
            <span>{branch}</span>
            <span>›</span>
            <span>{subtopic}</span>
          </div>
          <LatexBlock src={latexcode} className="text-lg leading-relaxed" />
          {solution && (
            <div className="mt-6 border-t border-ink-200 pt-4">
              <div className="mb-2 text-xs font-medium uppercase tracking-wider text-ink-500">
                Solution
              </div>
              <LatexBlock src={solution} />
            </div>
          )}
        </div>
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
      `}</style>
    </form>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium uppercase tracking-wider text-ink-500">
        {label}
      </span>
      {children}
    </label>
  );
}
