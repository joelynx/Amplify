import { Info } from "lucide-react";
import { Combobox } from "../ui/Combobox";
import { Button } from "../ui/Button";

interface Props {
  templates: readonly string[];
  value: string | null;
  onChange: (name: string | null) => void;
  onOpenManager: () => void;
}

/** Template combobox + info button. The info button opens the Template Manager
 * dialog (stubbed for Step 4; wired up properly in Step 6). */
export function TemplatePicker({ templates, value, onChange, onOpenManager }: Props) {
  return (
    <div className="flex items-center gap-2">
      <Combobox
        options={templates}
        value={value}
        onSelect={onChange}
        placeholder="Pick a template (optional)"
        searchPlaceholder="Search templates"
        emptyMessage="No templates yet"
        clearable
        className="min-w-[14rem]"
      />
      <Button variant="ghost" size="sm" onClick={onOpenManager} aria-label="Open template manager">
        <Info className="h-4 w-4" />
      </Button>
    </div>
  );
}
