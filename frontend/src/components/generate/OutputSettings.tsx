import { FolderOpen } from "lucide-react";

import { Button } from "../ui/Button";
import { Combobox } from "../ui/Combobox";
import { NumberInput } from "../ui/NumberInput";
import { Switch } from "../ui/Switch";
import { cn } from "../../lib/cn";
import { ipc, type GenerationStrategy } from "../../lib/ipc";
import { useGenerateStore, type GenerateDraft, type SolutionsValue } from "../../state/generate";

const STRATEGIES: readonly { id: GenerationStrategy; label: string; hint: string }[] = [
  { id: "random", label: "Random", hint: "Any questions that match your filters." },
  {
    id: "diverse",
    label: "Varied",
    hint:
      "Varied practice: questions chosen to be as different from each other as possible.",
  },
  {
    id: "focused",
    label: "Similar",
    hint:
      "Similar questions: the ones closest to a starting question.",
  },
  {
    id: "frontier",
    label: "Challenging",
    hint:
      "Hard questions you have seen least come first.",
  },
];

const SOLUTIONS_PRIMARY: readonly { id: SolutionsValue | "outline_only"; label: string }[] = [
  { id: "none", label: "None" },
  { id: "appendix", label: "Appendix" },
  { id: "interleaved", label: "Interleaved" },
  { id: "outline_only", label: "Outline only" },
];

const OPTION_LABELS: Record<string, string> = {
  none: "None",
  appendix: "Appendix",
  interleaved: "Interleaved",
  outline_only: "Outline only",
  outline_appendix: "Outline only",
  outline_interleaved: "Outline only",
};

function isOutline(value: SolutionsValue): boolean {
  return value === "outline_appendix" || value === "outline_interleaved";
}

/** How questions are picked from the ones that match: strategy, difficulty
 * floor, reuse, syllabus. Sits under "More filters" on Generate. */
export function SelectionOptions() {
  const draft = useGenerateStore();
  const activeStrategy = STRATEGIES.find((s) => s.id === draft.strategy) ?? STRATEGIES[0];

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <FieldRow label="How to pick" className="sm:col-span-2 items-start sm:items-center">
        <div className="flex w-full flex-col items-end gap-1">
          <div className="inline-flex overflow-hidden rounded-md border border-border">
            {STRATEGIES.map((s) => (
              <button
                key={s.id}
                type="button"
                onClick={() => draft.setStrategy(s.id)}
                className={cn(
                  "px-3 py-1.5 text-xs font-medium transition",
                  draft.strategy === s.id
                    ? "bg-primary text-on-primary"
                    : "bg-surface text-text hover:bg-primary/10",
                )}
                aria-pressed={draft.strategy === s.id}
              >
                {s.label}
              </button>
            ))}
          </div>
          <p className="max-w-prose text-right text-xs text-muted">{activeStrategy.hint}</p>
        </div>
      </FieldRow>

      <FieldRow label="Minimum difficulty (0–20)">
        <NumberInput
          value={draft.minDifficulty}
          onChange={draft.setMinDifficulty}
          min={0}
          max={20}
          ariaLabel="min difficulty"
        />
      </FieldRow>

      <FieldRow label="Allow questions used before">
        <Switch
          checked={draft.reuseQuestions}
          onCheckedChange={draft.setReuseQuestions}
          ariaLabel="reuse questions"
        />
      </FieldRow>

      <FieldRow label="Only questions in the syllabus">
        <Switch
          checked={draft.inSyllabusOnly}
          onCheckedChange={draft.setInSyllabusOnly}
          ariaLabel="in syllabus only"
        />
      </FieldRow>
    </div>
  );
}

/** How the PDF is laid out and where it is saved. */
export function PaperOptions() {
  const draft = useGenerateStore();

  const solutionsPrimary = isOutline(draft.solutions) ? "outline_only" : draft.solutions;
  const outlineSubMode: "appendix" | "interleaved" =
    draft.solutions === "outline_interleaved" ? "interleaved" : "appendix";

  const onPrimarySolutions = (raw: string | null) => {
    if (raw === null) return;
    if (raw === "outline_only") {
      draft.setSolutions(outlineSubMode === "interleaved" ? "outline_interleaved" : "outline_appendix");
    } else {
      draft.setSolutions(raw as SolutionsValue);
    }
  };

  const onOutlineSubChange = (next: "appendix" | "interleaved") => {
    draft.setSolutions(next === "interleaved" ? "outline_interleaved" : "outline_appendix");
  };

  const pickFolder = async () => {
    const path = await ipc.pick_save_directory();
    if (path) {
      draft.setSaveDirectory(path);
      ipc.set_config("FILE_SAVE_LOCATION", path);
    }
  };

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <FieldRow label="Include sources in PDF">
        <Switch
          checked={draft.includeSources}
          onCheckedChange={draft.setIncludeSources}
          ariaLabel="include sources"
        />
      </FieldRow>

      <FieldRow label="Solutions" className="sm:col-span-2">
        <div className="flex flex-wrap items-center gap-2">
          <Combobox
            options={SOLUTIONS_PRIMARY.map((s) => s.id)}
            value={solutionsPrimary}
            onSelect={onPrimarySolutions}
            placeholder="None"
            searchPlaceholder="Solutions placement"
            emptyMessage="—"
            className="min-w-[12rem]"
          />
          {solutionsPrimary === "outline_only" && (
            <div className="inline-flex items-center gap-2 text-xs">
              <span className="text-muted">Outline placement:</span>
              <Switch
                checked={outlineSubMode === "interleaved"}
                onCheckedChange={(v) => onOutlineSubChange(v ? "interleaved" : "appendix")}
                ariaLabel="outline placement"
              />
              <span>{outlineSubMode === "interleaved" ? "Interleaved" : "Appendix"}</span>
            </div>
          )}
          <span className="text-xs text-muted">
            Current: <span className="font-medium text-text">{OPTION_LABELS[draft.solutions]}</span>
            {isOutline(draft.solutions) && ` (${outlineSubMode})`}
          </span>
        </div>
      </FieldRow>

      <FieldRow label="Save directory" className="sm:col-span-2">
        <div className="flex w-full items-center gap-2">
          <div className="flex-1 truncate rounded-md border border-border bg-background px-3 py-1.5 text-sm">
            {draft.saveDirectory ?? <span className="text-muted">Not set</span>}
          </div>
          <Button variant="outline" size="sm" onClick={pickFolder}>
            <FolderOpen className="h-4 w-4" />
            Browse…
          </Button>
        </div>
      </FieldRow>
    </div>
  );
}

const plural = (n: number, word: string) => `${n} ${word}${n === 1 ? "" : "s"}`;

/** What is set under "More filters", for the collapsed header. */
export function filterSummary(draft: GenerateDraft): string {
  const parts: string[] = [];
  const tags = draft.tags.compulsory.length + draft.tags.optional.length + draft.tags.excluded.length;
  if (tags > 0) parts.push(plural(tags, "tag"));
  if (draft.sources.length > 0) parts.push(plural(draft.sources.length, "source"));
  if (draft.types.length > 0) parts.push(plural(draft.types.length, "type"));
  if (draft.minDifficulty > 0) parts.push(`difficulty ${draft.minDifficulty}+`);
  if (draft.strategy !== "random") parts.push(STRATEGIES.find((s) => s.id === draft.strategy)?.label.toLowerCase() ?? draft.strategy);
  if (draft.reuseQuestions) parts.push("reuse allowed");
  if (!draft.inSyllabusOnly) parts.push("outside syllabus too");
  return parts.length > 0 ? parts.join(" · ") : "None set";
}

/** What is set under "Paper options", for the collapsed header. */
export function paperSummary(draft: GenerateDraft): string {
  const solutions = draft.solutions === "none" ? "No solutions" : `Solutions: ${OPTION_LABELS[draft.solutions].toLowerCase()}`;
  const folder = draft.saveDirectory
    ? `saved to ${draft.saveDirectory.split(/[\\/]/).filter(Boolean).pop() ?? draft.saveDirectory}`
    : "no save folder chosen";
  return `${solutions} · ${folder}`;
}

function FieldRow({
  label,
  children,
  className,
}: {
  label: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <label className={`flex items-center justify-between gap-3 ${className ?? ""}`}>
      <span className="text-sm">{label}</span>
      {children}
    </label>
  );
}
