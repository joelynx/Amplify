import { useEffect, useState } from "react";
import { Pencil, Trash2 } from "lucide-react";

import { Button } from "../ui/Button";
import { Modal } from "../ui/Modal";
import { ipc } from "../../lib/ipc";
import { NameDialog } from "./NameDialog";

interface Props {
  open: boolean;
  onClose: () => void;
  templates: readonly string[];
  /** Called after any change so the parent re-fetches `list_templates`. */
  onChange: () => void;
  /** Optional — if the user just renamed/deleted the currently-loaded template,
   * the parent may want to update its loaded-template state. */
  loadedName: string | null;
  onLoadedRenamed: (newName: string) => void;
  onLoadedDeleted: () => void;
}

export function TemplateManager({
  open,
  onClose,
  templates,
  onChange,
  loadedName,
  onLoadedRenamed,
  onLoadedDeleted,
}: Props) {
  const [renaming, setRenaming] = useState<string | null>(null);
  const [confirmingDelete, setConfirmingDelete] = useState<string | null>(null);

  useEffect(() => {
    if (!open) {
      setRenaming(null);
      setConfirmingDelete(null);
    }
  }, [open]);

  const handleRenameConfirm = async (newName: string) => {
    if (!renaming) return;
    try {
      await ipc.rename_template(renaming, newName);
      if (loadedName === renaming) onLoadedRenamed(newName);
      onChange();
    } finally {
      setRenaming(null);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!confirmingDelete) return;
    try {
      await ipc.delete_template(confirmingDelete);
      if (loadedName === confirmingDelete) onLoadedDeleted();
      onChange();
    } finally {
      setConfirmingDelete(null);
    }
  };

  return (
    <>
      <Modal
        open={open}
        onClose={onClose}
        title="Templates"
        footer={
          <Button variant="primary" onClick={onClose}>
            Close
          </Button>
        }
      >
        {templates.length === 0 ? (
          <p className="text-muted">No templates yet. Save the current form to create one.</p>
        ) : (
          <ul className="divide-y divide-border rounded-md border border-border">
            {templates.map((name) => (
              <li
                key={name}
                className="flex items-center justify-between gap-2 px-3 py-2 text-sm"
              >
                <span className="truncate font-medium">{name}</span>
                <span className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setRenaming(name)}
                    aria-label={`Rename ${name}`}
                  >
                    <Pencil className="h-4 w-4" />
                    Rename
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setConfirmingDelete(name)}
                    aria-label={`Delete ${name}`}
                  >
                    <Trash2 className="h-4 w-4 text-error" />
                    Delete
                  </Button>
                </span>
              </li>
            ))}
          </ul>
        )}
      </Modal>

      <NameDialog
        open={renaming !== null}
        title="Rename template"
        initialValue={renaming ?? ""}
        takenNames={templates.filter((n) => n !== renaming)}
        confirmLabel="Rename"
        onCancel={() => setRenaming(null)}
        onConfirm={handleRenameConfirm}
      />

      <Modal
        open={confirmingDelete !== null}
        onClose={() => setConfirmingDelete(null)}
        title="Delete template?"
        tone="error"
        footer={
          <>
            <Button variant="ghost" onClick={() => setConfirmingDelete(null)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleDeleteConfirm}>
              Delete
            </Button>
          </>
        }
      >
        <p>
          Delete <code className="font-mono">{confirmingDelete}</code>? The form draft stays as-is.
        </p>
      </Modal>
    </>
  );
}
