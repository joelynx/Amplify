import { useEffect, useState } from "react";

import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { Modal } from "../ui/Modal";
import type { DateRange } from "../../lib/ipc";
import { SubjectPicker } from "../generate/SubjectPicker";

interface Props {
  open: boolean;
  onClose: () => void;
  initial: { subject: string | null; dateRange: DateRange };
  subjects: readonly string[];
  onApply: (subject: string | null, dateRange: DateRange) => void;
}

export function StatsFiltersDialog({ open, onClose, initial, subjects, onApply }: Props) {
  const [subject, setSubject] = useState<string | null>(initial.subject);
  const [from, setFrom] = useState<string>(initial.dateRange.from ?? "");
  const [to, setTo] = useState<string>(initial.dateRange.to ?? "");

  // Re-sync from props whenever the dialog opens (parent may have changed defaults).
  useEffect(() => {
    if (open) {
      setSubject(initial.subject);
      setFrom(initial.dateRange.from ?? "");
      setTo(initial.dateRange.to ?? "");
    }
  }, [open, initial]);

  const apply = () => {
    onApply(subject, { from: from || null, to: to || null });
    onClose();
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Stats filters"
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="primary" onClick={apply}>
            Apply
          </Button>
        </>
      }
    >
      <div className="space-y-3">
        <div className="flex flex-col gap-1 text-sm">
          <span className="text-muted">Subject</span>
          <SubjectPicker subjects={subjects} value={subject} onChange={setSubject} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <label className="flex flex-col gap-1 text-sm">
            <span className="text-muted">From</span>
            <Input type="date" value={from} onChange={(e) => setFrom(e.target.value)} />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="text-muted">To</span>
            <Input type="date" value={to} onChange={(e) => setTo(e.target.value)} />
          </label>
        </div>
        <p className="text-xs text-muted">
          Date range filters PSet counts. Per-question multiplicity and difficulty stay lifetime.
        </p>
      </div>
    </Modal>
  );
}
