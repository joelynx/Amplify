/**
 * Home as a cozy illustrated room (Makeover.md §5.12). The room is the
 * navigation (door → Quiz, printer → Generate, filing cabinet → History,
 * chart → Stats, bookcase → Browser, noticeboard → today's reviews, pennant
 * and mug → About) and a quiet picture of progress: one book per practised
 * topic, trophies for milestones, a plant that grows with spaced reviews, a
 * window that follows the clock and the season. RoomPreview is the static
 * thumbnail the Wardrobe shows for a room item.
 */

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { resolve } from "../registry";
import { effectsLevel, useAppearance } from "../store";
import { examCountdown, greeting, type SceneData } from "./helpers";
import type { ObjectId } from "./model";
import { Scene, objectLabels } from "./Scene";
import { useRoomData } from "./useRoomData";

/** The lamp remembers its state while the app is open. */
let lampMemory = true;

function useNow(): Date {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const tick = () => {
      if (document.hidden) return;
      setNow((prev) => {
        const d = new Date();
        return d.getMinutes() === prev.getMinutes() && d.getHours() === prev.getHours() ? prev : d;
      });
    };
    const t = window.setInterval(tick, 20_000);
    document.addEventListener("visibilitychange", tick);
    return () => {
      window.clearInterval(t);
      document.removeEventListener("visibilitychange", tick);
    };
  }, []);
  return now;
}

function useHidden(): boolean {
  const [hidden, setHidden] = useState(() => typeof document !== "undefined" && document.hidden);
  useEffect(() => {
    const on = () => setHidden(document.hidden);
    document.addEventListener("visibilitychange", on);
    return () => document.removeEventListener("visibilitychange", on);
  }, []);
  return hidden;
}

/** effectsLevel() > 0, re-evaluated when settings, timed focus or the OS motion setting change. */
function useMotion(): boolean {
  useAppearance((s) => s.settings);
  useAppearance((s) => s.timedActive);
  const [, bump] = useState(0);
  useEffect(() => {
    const mq = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    const on = () => bump((n) => n + 1);
    mq?.addEventListener?.("change", on);
    return () => mq?.removeEventListener?.("change", on);
  }, []);
  return effectsLevel() > 0;
}

export function StudyRoom() {
  const navigate = useNavigate();
  const itemId = useAppearance((s) => resolve(s.loadout, "room")?.id ?? "room.study");
  const name = useAppearance((s) => s.settings.greetingName);
  const exam = useAppearance((s) => s.settings.exam);
  const motion = useMotion();
  const hidden = useHidden();
  const now = useNow();
  const data = useRoomData();
  const [lampOn, setLampOn] = useState(lampMemory);

  const activate = (id: ObjectId) => {
    switch (id) {
      case "door":
        navigate("/quiz");
        break;
      case "printer":
        navigate("/generate");
        break;
      case "cabinet":
        navigate("/history");
        break;
      case "chart":
        navigate("/stats");
        break;
      case "bookcase":
        navigate("/browser");
        break;
      case "noticeboard":
        if (data.due && data.due > 0) navigate("/quiz", { state: { startReview: "due", subject: data.subject } });
        else navigate("/quiz");
        break;
      case "lamp":
        setLampOn((v) => {
          lampMemory = !v;
          return !v;
        });
        break;
      case "pennant":
      case "mug":
        navigate("/about");
        break;
    }
  };

  const countdown = examCountdown(exam ?? { label: "", date: null }, now);

  return (
    <section className="amp-room mx-auto w-full max-w-[1000px]">
      <div className="overflow-hidden rounded-lg border border-border shadow-sm">
        <Scene
          itemId={itemId}
          data={data}
          now={now}
          lampOn={lampOn}
          motion={motion}
          paused={hidden}
          labels={objectLabels(data.due, lampOn)}
          onActivate={activate}
          title="Your study room"
        />
      </div>
      <p className="mt-2 text-center text-sm text-muted">
        {greeting(now, name ?? "")}
        {countdown && (
          <>
            <span aria-hidden="true"> · </span>
            <span className="font-medium text-text">{countdown}</span>
          </>
        )}
      </p>
    </section>
  );
}

/** Sample progress so thumbnails show a lived-in room. */
const SAMPLE: SceneData = {
  subject: null,
  topics: [
    { topic: "Linear Algebra", attempted: 30, independent: 22 },
    { topic: "Calculus", attempted: 25, independent: 18 },
    { topic: "Probability", attempted: 12, independent: 6 },
    { topic: "Number Theory", attempted: 8, independent: 3 },
    { topic: "Graph Theory", attempted: 6, independent: 4 },
    { topic: "Combinatorics", attempted: 15, independent: 9 },
    { topic: "Real Analysis", attempted: 9, independent: 2 },
    { topic: "Group Theory", attempted: 5, independent: 1 },
    { topic: "Geometry", attempted: 7, independent: 5 },
    { topic: "Mechanics", attempted: 4, independent: 2 },
  ],
  trophies: [{ id: "spaced_reviews", title: "Spaced reviewer" }],
  plantCount: 9,
  due: 3,
  nextDue: null,
  notes: ["Eigenvalues", "Series tests", "Bayes"],
};

/** A small static picture of a room item for the Wardrobe. */
export function RoomPreview({ itemId, className }: { itemId: string; className?: string }) {
  const [now] = useState(() => new Date());
  return (
    <Scene
      itemId={itemId}
      data={SAMPLE}
      now={now}
      lampOn
      motion={false}
      preview
      className={className}
    />
  );
}
