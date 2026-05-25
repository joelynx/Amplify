import { Save, Download, FileText } from "lucide-react";

import { Button } from "../ui/Button";
import { Tooltip } from "../ui/Tooltip";

interface Props {
  /** Disabled when the form payload matches a saved template's payload exactly. */
  saveTemplateDisabled: boolean;
  /** Reason the Generate-PDF button is disabled (renders as the tooltip). null = enabled. */
  generateDisabledReason: string | null;
  onSaveTemplate: () => void;
  onExportLatex: () => void;
  onGenerate: () => void;
}

/** Save Template / Export LaTeX / Generate PDF. All three are no-ops in Step 4. */
export function ActionRow({
  saveTemplateDisabled,
  generateDisabledReason,
  onSaveTemplate,
  onExportLatex,
  onGenerate,
}: Props) {
  return (
    <div className="flex flex-wrap items-center justify-end gap-2">
      <Button variant="outline" onClick={onSaveTemplate} disabled={saveTemplateDisabled}>
        <Save className="h-4 w-4" />
        Save Template
      </Button>
      <Button variant="outline" onClick={onExportLatex}>
        <FileText className="h-4 w-4" />
        Export LaTeX
      </Button>
      <Tooltip content={generateDisabledReason}>
        <Button
          variant="primary"
          onClick={onGenerate}
          disabled={generateDisabledReason !== null}
        >
          <Download className="h-4 w-4" />
          Generate PDF
        </Button>
      </Tooltip>
    </div>
  );
}
