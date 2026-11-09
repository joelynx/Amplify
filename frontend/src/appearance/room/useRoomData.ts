/**
 * Loads what the room shows: practised topics (books, chart), earned
 * milestones (trophies), spaced reviews (plant) and today's reviews
 * (noticeboard) for the active subject. Any call that fails (no bridge in a
 * browser preview, a backend error) just leaves that part empty.
 */

import { useEffect, useState } from "react";

import { ipc } from "../../lib/ipc";
import { useSubjectStore } from "../../state/subject";
import { EMPTY_SCENE, toSceneData, type SceneData } from "./helpers";

export function useRoomData(): SceneData {
  // Loaded at startup and kept in step by the Subjects page.
  const subject = useSubjectStore((s) => s.active);
  const [data, setData] = useState<SceneData>(EMPTY_SCENE);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const [stats, reviews, milestones] = await Promise.all([
        ipc.get_learning_stats(subject, { from: null, to: null }).catch(() => null),
        ipc.get_review_summary(subject).catch(() => null),
        ipc.get_milestones().catch(() => null),
      ]);
      if (!cancelled) setData(toSceneData(subject, stats, reviews, milestones));
    })().catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [subject]);

  return data;
}
