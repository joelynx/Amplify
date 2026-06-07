/**
 * Quiz settings panel (spec §10 "Options" block). The three preset templates:
 *
 *   - PBS                — locked layout, numerical-only, total-timer only
 *   - MIT Integration Bee — fully editable, defaults to no-hints + total timer
 *   - Free Answering      — fully editable, defaults to per-question timer off
 *
 * Each toggle's enable/disable hint mirrors spec §10. PBS resets the toggles
 * that don't apply when chosen; the rest are user-driven.
 */

/**
 * @deprecated Replaced by the new Traverse and Discover setup in pages/Quiz.tsx.
 * Kept for reference.
 */
import { useEffect, useMemo, useState } from "react";

import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { Checkbox } from "../ui/Checkbox";
import { Combobox } from "../ui/Combobox";
import { NumberInput } from "../ui/NumberInput";
import { Switch } from "../ui/Switch";
import { useSubjectStore } from "../../state/subject";
import { ipc, type QuizSettings, type QuizTemplate } from "../../lib/ipc";

interface Props {
  onStart: (settings: QuizSettings, count: number) => void;
}

const TEMPLATES: { id: QuizTemplate; label: string; blurb: string }[] = [
  { id: "FREE_ANSWERING", label: "Free Answering", blurb: "Self-paced. All toggles editable." },
  { id: "MIT_INTEGRATION_BEE", label: "MIT Integration Bee", blurb: "Total timer, fixed-point gradient." },
  { id: "PBS", label: "[PBS] Physics Brawl Style", blurb: "Parallel widget pool. Numerical only, total timer only, no hints." },
];

function templateDefaults(t: QuizTemplate): QuizSettings {
  if (t === "PBS") {
    return {
      template: "PBS",
      n_questions: 10,
      total_time_s: 600,
      allow_skips: true, // implicit only — UI hides explicit skip
      show_scoring: true,
      enable_hints: false,
      instant_scoring: true,
      show_solutions: false,
      wait_for_correct: false,
      gradient_mode: "constant",
      max_points: 10,
      pbs_num_widgets: 3,
      pbs_pool_size: 10,
    };
  }
  if (t === "MIT_INTEGRATION_BEE") {
    return {
      template: "MIT_INTEGRATION_BEE",
      n_questions: 10,
      total_time_s: 600,
      allow_skips: true,
      show_scoring: true,
      enable_hints: false,
      instant_scoring: true,
      show_solutions: false,
      wait_for_correct: false,
      gradient_mode: "constant",
      max_points: 10,
    };
  }
  return {
    template: "FREE_ANSWERING",
    n_questions: 10,
    total_time_s: null,
    allow_skips: true,
    show_scoring: true,
    enable_hints: true,
    instant_scoring: false,
    show_solutions: true,
    wait_for_correct: false,
    gradient_mode: "constant",
    max_points: 10,
  };
}

export function QuizSettingsPanel({ onStart }: Props) {
  const activeSubject = useSubjectStore((s) => s.active);
  const [s, setS] = useState<QuizSettings>(() => templateDefaults("FREE_ANSWERING"));
  const [count, setCount] = useState<number>(0);
  const [matchingTotal, setMatchingTotal] = useState<number | null>(null);

  // When template changes, reset settings to its defaults.
  useEffect(() => {
    setS(templateDefaults(s.template));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [s.template]);

  // Live count of questions matching the implicit filters.
  const filters = useMemo(
    () => ({
      subject: activeSubject,
      reuse_questions: true,
      in_syllabus_only: true,
      types: s.template === "PBS" ? ["numerical"] : [],
    }),
    [activeSubject, s.template],
  );

  useEffect(() => {
    let cancelled = false;
    ipc.count_matching_questions(filters).then((n) => {
      if (!cancelled) setMatchingTotal(n);
    });
    return () => {
      cancelled = true;
    };
  }, [filters]);

  useEffect(() => {
    setCount(s.template === "PBS" ? (s.pbs_pool_size ?? 10) : s.n_questions);
  }, [s.template, s.n_questions, s.pbs_pool_size]);

  const canStart = matchingTotal !== null && matchingTotal > 0;
  const isPBS = s.template === "PBS";

  const handleStart = () => {
    onStart(s, count);
  };

  return (
    <div className="mx-auto max-w-3xl space-y-4 px-6 py-6">
      <header>
        <h1 className="text-2xl font-semibold">Quiz</h1>
        <p className="text-sm text-muted">
          {activeSubject ? <>Scoped to <strong>{activeSubject}</strong>. </> : "All subjects. "}
          {matchingTotal !== null && <>{matchingTotal.toLocaleString()} questions available.</>}
        </p>
      </header>

      <Card title="Template">
        <div className="space-y-2">
          {TEMPLATES.map((t) => (
            <label
              key={t.id}
              className={
                "flex cursor-pointer items-start gap-3 rounded-md border p-3 " +
                (s.template === t.id ? "border-primary bg-primary/5" : "border-border hover:bg-surface")
              }
            >
              <input
                type="radio"
                name="template"
                checked={s.template === t.id}
                onChange={() => setS((prev) => ({ ...prev, template: t.id }))}
                className="mt-0.5"
              />
              <div>
                <div className="font-medium">{t.label}</div>
                <div className="text-sm text-muted">{t.blurb}</div>
              </div>
            </label>
          ))}
        </div>
      </Card>

      <Card title="Options">
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label={isPBS ? "Pool size" : "Number of questions"}>
            <NumberInput
              value={isPBS ? (s.pbs_pool_size ?? 10) : s.n_questions}
              onChange={(v) =>
                setS((p) => (isPBS ? { ...p, pbs_pool_size: v } : { ...p, n_questions: v }))
              }
              min={1}
              max={200}
            />
          </Field>

          {isPBS && (
            <Field label="Visible widgets">
              <NumberInput
                value={s.pbs_num_widgets ?? 3}
                onChange={(v) => setS((p) => ({ ...p, pbs_num_widgets: v }))}
                min={1}
                max={8}
              />
            </Field>
          )}

          <Field label="Total time (seconds, 0 = none)">
            <NumberInput
              value={s.total_time_s ?? 0}
              onChange={(v) => setS((p) => ({ ...p, total_time_s: v === 0 ? null : v }))}
              min={0}
              max={3600 * 4}
            />
          </Field>

          {!isPBS && (
            <Field label="Per-question time (s, 0 = none)">
              <NumberInput
                value={s.time_per_question_s ?? 0}
                onChange={(v) => setS((p) => ({ ...p, time_per_question_s: v === 0 ? null : v }))}
                min={0}
                max={3600}
              />
            </Field>
          )}

          <Field label="Max points per Q">
            <NumberInput
              value={s.max_points ?? 10}
              onChange={(v) => setS((p) => ({ ...p, max_points: v }))}
              min={1}
              max={100}
            />
          </Field>

          <Field label="Allow skips" disabled={isPBS}>
            <Switch
              checked={!!s.allow_skips}
              onCheckedChange={(v) => setS((p) => ({ ...p, allow_skips: v }))}
              disabled={isPBS}
            />
          </Field>

          <Field label="Show scoring">
            <Switch
              checked={!!s.show_scoring}
              onCheckedChange={(v) => setS((p) => ({ ...p, show_scoring: v }))}
            />
          </Field>

          <Field label="Enable hints" disabled={isPBS}>
            <Switch
              checked={!!s.enable_hints && !isPBS}
              onCheckedChange={(v) => setS((p) => ({ ...p, enable_hints: v }))}
              disabled={isPBS}
            />
          </Field>

          <Field label="Instant scoring">
            <Switch
              checked={!!s.instant_scoring}
              onCheckedChange={(v) => setS((p) => ({ ...p, instant_scoring: v }))}
            />
          </Field>

          <Field label="Show solutions (only without timer)" disabled={!!s.total_time_s || !!s.time_per_question_s}>
            <Switch
              checked={!!s.show_solutions && !s.total_time_s && !s.time_per_question_s}
              onCheckedChange={(v) => setS((p) => ({ ...p, show_solutions: v }))}
              disabled={!!s.total_time_s || !!s.time_per_question_s}
            />
          </Field>

          <Field label="Wait for correct (phys mode)" disabled={isPBS}>
            <Switch
              checked={!!s.wait_for_correct && !isPBS}
              onCheckedChange={(v) =>
                setS((p) => ({ ...p, wait_for_correct: v, allow_skips: v ? false : p.allow_skips }))
              }
              disabled={isPBS}
            />
          </Field>

          <Field label="Gradient">
            <Combobox
              options={["constant", "random"]}
              value={s.gradient_mode ?? "constant"}
              onSelect={(v) => setS((p) => ({ ...p, gradient_mode: (v as "constant" | "random") ?? "constant" }))}
              placeholder="constant"
              searchPlaceholder="Search"
              emptyMessage="—"
              className="min-w-[10rem]"
            />
          </Field>

          {!isPBS && s.allow_skips && s.show_scoring && (
            <Field label="Skip penalty (marks)">
              <NumberInput
                value={s.penalize_skips_marks ?? 0}
                onChange={(v) => setS((p) => ({ ...p, penalize_skips_marks: v === 0 ? null : v }))}
                min={0}
                max={100}
              />
            </Field>
          )}
        </div>
      </Card>

      <div className="flex items-center justify-end gap-2">
        <Button variant="primary" onClick={handleStart} disabled={!canStart}>
          Start quiz ({count} {isPBS ? "in pool" : "questions"})
        </Button>
      </div>
    </div>
  );
}

function Field({
  label,
  children,
  disabled,
}: {
  label: string;
  children: React.ReactNode;
  disabled?: boolean;
}) {
  return (
    <label className={"flex items-center justify-between gap-3 text-sm " + (disabled ? "opacity-50" : "")}>
      <span>{label}</span>
      {children}
    </label>
  );
}

// Keep Checkbox importable for downstream use without lint errors.
export const _kept = { Checkbox };
