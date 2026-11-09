/**
 * Session-end card (Makeover.md §5.11) in the style the `results` slot picks:
 * report card, JRPG victory window, arcade scoreboard, newspaper front page,
 * terminal log, setup-wizard dialog, sticker sheet or parchment scroll. Every
 * style shows the same honest numbers (answered, unaided, with help, partial,
 * missed, review queue, elapsed time). Count-ups and entrances run only when
 * effectsLevel() > 0, decided once on mount.
 *
 * The card renders inline; wrap it in a modal or page section as needed.
 */

import { type ComponentType, useState } from "react";

import type { SessionSummary } from "../events";
import { getItem, resolve } from "../registry";
import { effectsLevel, useAppearance } from "../store";
import { SAMPLE, type StyleProps } from "./shared";
import { Arcade } from "./styles/Arcade";
import { Dialog } from "./styles/Dialog";
import { Jrpg } from "./styles/Jrpg";
import { Newspaper } from "./styles/Newspaper";
import { Report } from "./styles/Report";
import { Scroll } from "./styles/Scroll";
import { Sticker } from "./styles/Sticker";
import { Terminal } from "./styles/Terminal";

export const RESULT_STYLES: Record<string, ComponentType<StyleProps>> = {
  report: Report,
  jrpg: Jrpg,
  arcade: Arcade,
  newspaper: Newspaper,
  terminal: Terminal,
  dialog: Dialog,
  sticker: Sticker,
  scroll: Scroll,
};

/** The renderer for a results item: its `data.style`, else the id suffix, else the report card. */
function styleOf(itemId: string | undefined): ComponentType<StyleProps> {
  const it = getItem(itemId);
  const style = typeof it?.data?.style === "string" ? it.data.style : itemId?.slice(itemId.indexOf(".") + 1);
  return (style && RESULT_STYLES[style]) || Report;
}

/** One results style with explicit numbers; `level` 0 renders it static. */
export function ResultsCard({
  itemId,
  summary,
  level = 0,
  onClose,
}: {
  itemId: string;
  summary: SessionSummary;
  level?: 0 | 1 | 2;
  onClose?: () => void;
}) {
  const Style = styleOf(itemId);
  return (
    <div role="region" aria-label="Session results" className="mx-auto w-full max-w-2xl">
      <Style s={summary} level={level} onClose={onClose} />
    </div>
  );
}

export function ResultsScreen({ summary, onClose }: { summary: SessionSummary; onClose?: () => void }) {
  const itemId = useAppearance((s) => resolve(s.loadout, "results")?.id ?? "results.report");
  const [level] = useState(effectsLevel);
  // Tall styles (newspaper, scroll) scroll inside the viewport instead of overflowing a modal.
  return (
    <div className="-m-3 max-h-[calc(100dvh-1rem)] overflow-y-auto p-3">
      <ResultsCard itemId={itemId} summary={summary} level={level} onClose={onClose} />
    </div>
  );
}

/** A results style with sample numbers, static, for the Wardrobe. */
export function ResultsPreview({ itemId, summary = SAMPLE }: { itemId: string; summary?: SessionSummary }) {
  return <ResultsCard itemId={itemId} summary={summary} />;
}
