import { useEffect, useState } from "react";

import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { Modal } from "../ui/Modal";

interface Props {
  open: boolean;
  title: string;
  /** Initial input value — used for rename flows. */
  initialValue?: string;
  /** Reserve a list of names the user must not re-use (case-insensitive). */
  takenNames?: readonly string[];
  /** Optional async check (e.g. IPC) for "is this name still available". */
  validateAsync?: (name: string) => Promise<string | null>;
  confirmLabel?: string;
  onCancel: () => void;
  onConfirm: (name: string) => void;
}

export function NameDialog({
  open,
  title,
  initialValue = "",
  takenNames = [],
  validateAsync,
  confirmLabel = "Save",
  onCancel,
  onConfirm,
}: Props) {
  const [value, setValue] = useState(initialValue);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setValue(initialValue);
      setError(null);
    }
  }, [open, initialValue]);

  const validate = async (raw: string): Promise<string | null> => {
    const v = raw.trim();
    if (!v) return "Name cannot be empty";
    if (
      v !== initialValue &&
      takenNames.some((n) => n.toLowerCase() === v.toLowerCase())
    ) {
      return "Name already in use";
    }
    if (validateAsync) {
      const remote = await validateAsync(v);
      if (remote) return remote;
    }
    return null;
  };

  const handleSubmit = async () => {
    const err = await validate(value);
    setError(err);
    if (!err) onConfirm(value.trim());
  };

  return (
    <Modal
      open={open}
      onClose={onCancel}
      title={title}
      footer={
        <>
          <Button variant="ghost" onClick={onCancel}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleSubmit}>
            {confirmLabel}
          </Button>
        </>
      }
    >
      <Input
        value={value}
        onChange={(e) => {
          setValue(e.target.value);
          setError(null);
        }}
        onKeyDown={(e) => {
          if (e.key === "Enter") handleSubmit();
        }}
        placeholder="Template name"
        autoFocus
      />
      {error && <p className="mt-2 text-sm text-error">{error}</p>}
    </Modal>
  );
}
