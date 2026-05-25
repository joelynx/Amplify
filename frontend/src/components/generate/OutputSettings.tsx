import { FolderOpen } from "lucide-react";

import { Button } from "../ui/Button";
import { Checkbox } from "../ui/Checkbox";
import { Combobox } from "../ui/Combobox";
import { NumberInput } from "../ui/NumberInput";
import { Switch } from "../ui/Switch";
import { ipc } from "../../lib/ipc";
import { useGenerateStore, type SolutionsValue } from "../../state/generate";

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

export function OutputSettings() {
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
      <FieldRow label="Number of questions">
        <NumberInput
          value={draft.nQuestions}
          onChange={draft.setNQuestions}
          min={1}
          max={200}
          ariaLabel="number of questions"
        />
      </FieldRow>

      <FieldRow label="Min difficulty">
        <NumberInput
          value={draft.minDifficulty}
          onChange={draft.setMinDifficulty}
          min={0}
          max={20}
          ariaLabel="min difficulty"
        />
      </FieldRow>

      <FieldRow label="Reuse questions">
        <Switch
          checked={draft.reuseQuestions}
          onCheckedChange={draft.setReuseQuestions}
          ariaLabel="reuse questions"
        />
      </FieldRow>

      <FieldRow label="In-syllabus only">
        <Switch
          checked={draft.inSyllabusOnly}
          onCheckedChange={draft.setInSyllabusOnly}
          ariaLabel="in syllabus only"
        />
      </FieldRow>

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

// Re-exports kept so the file compiles cleanly even if Checkbox isn't used yet.
export const _kept = { Checkbox };
