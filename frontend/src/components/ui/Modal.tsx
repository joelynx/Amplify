import { type ReactNode, useEffect, useId, useRef } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";

import { cn } from "../../lib/cn";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  footer?: ReactNode;
  className?: string;
  /** Tone of the title bar — drives a left accent border. */
  tone?: "default" | "success" | "error";
}

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

export function Modal({ open, onClose, title, children, footer, className, tone = "default" }: ModalProps) {
  const titleId = useId();
  const panelRef = useRef<HTMLDivElement>(null);
  // Latest onClose without re-running the effect (callers pass inline closures).
  const closeRef = useRef(onClose);
  closeRef.current = onClose;

  // Escape-to-close, lock body scroll, and keep keyboard focus inside while open.
  useEffect(() => {
    if (!open) return;
    const panel = panelRef.current;
    const trigger = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    // Focus moves in unless a child took it already (autoFocus).
    if (panel && !panel.contains(document.activeElement)) panel.focus();

    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        closeRef.current();
        return;
      }
      if (e.key !== "Tab" || !panel) return;
      const items = Array.from(panel.querySelectorAll<HTMLElement>(FOCUSABLE));
      if (items.length === 0) {
        e.preventDefault();
        return;
      }
      const first = items[0];
      const last = items[items.length - 1];
      const at = document.activeElement;
      if (!panel.contains(at) || at === panel) {
        e.preventDefault();
        (e.shiftKey ? last : first).focus();
      } else if (e.shiftKey && at === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && at === last) {
        e.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKey);
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevOverflow;
      if (trigger?.isConnected) trigger.focus();
    };
  }, [open]);

  if (!open) return null;

  const accent =
    tone === "success" ? "border-l-success" : tone === "error" ? "border-l-error" : "border-l-primary";

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center" role="dialog" aria-modal="true" aria-labelledby={titleId}>
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div
        ref={panelRef}
        tabIndex={-1}
        data-ui="dialog"
        className={cn(
          "relative z-10 mx-4 w-full max-w-lg rounded-lg border border-border border-l-4 bg-background p-6 shadow-xl outline-none",
          accent,
          className,
        )}
      >
        <header data-ui="dialog-header" className="mb-3 flex items-center justify-between gap-2">
          <h2 id={titleId} className="text-lg font-semibold">{title}</h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1 text-muted hover:bg-surface hover:text-text focus:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        </header>
        <div className="mb-4 text-sm">{children}</div>
        {footer && <div className="flex justify-end gap-2">{footer}</div>}
      </div>
    </div>,
    document.body,
  );
}
