import { useEffect, useState } from "react";

export function ElapsedTime({ startTime }: { startTime: number | null }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!startTime) {
      setElapsed(0);
      return;
    }

    const interval = setInterval(() => {
      setElapsed(Math.max(0, Date.now() - startTime));
    }, 1000);

    // Initial set
    setElapsed(Math.max(0, Date.now() - startTime));

    return () => clearInterval(interval);
  }, [startTime]);

  const totalSeconds = Math.floor(elapsed / 1000);
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  const h = Math.floor(m / 60);
  const mDisplay = m % 60;

  const formatted = h > 0 
    ? `${h}:${mDisplay.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`
    : `${m}:${s.toString().padStart(2, "0")}`;

  return <span className="font-mono tabular-nums">{formatted}</span>;
}
