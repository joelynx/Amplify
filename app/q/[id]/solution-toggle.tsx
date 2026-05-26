"use client";

import { useState } from "react";
import { LatexBlock } from "@/components/latex-block";

export function SolutionToggle({
  solution,
  answer,
}: {
  solution: string;
  answer?: string;
}) {
  const [open, setOpen] = useState(false);

  return (
    <section className="mt-10 border-t border-ink-200 pt-6">
      <button
        onClick={() => setOpen((v) => !v)}
        className="text-sm font-medium text-ink-700 hover:text-ink-900"
      >
        {open ? "▾ Hide solution" : "▸ Reveal solution"}
      </button>

      {open && (
        <div className="mt-4 space-y-4">
          {answer && answer !== "N/A" && (
            <div>
              <div className="text-xs font-medium uppercase tracking-wide text-ink-400">
                Answer
              </div>
              <LatexBlock src={answer} className="mt-1" />
            </div>
          )}
          <div>
            <div className="text-xs font-medium uppercase tracking-wide text-ink-400">
              Solution
            </div>
            <LatexBlock src={solution} className="mt-1 leading-relaxed" />
          </div>
        </div>
      )}
    </section>
  );
}
