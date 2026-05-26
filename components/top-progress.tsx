"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";

/** Slim sliding bar at the top edge of the viewport. Fires on every
 *  pathname change (client-side navigation). Auto-hides after ~800ms. */
export function TopProgressBar() {
  const pathname = usePathname();
  const [tick, setTick] = useState(0);
  const [show, setShow] = useState(false);

  useEffect(() => {
    setTick((t) => t + 1);
    setShow(true);
    const t = setTimeout(() => setShow(false), 800);
    return () => clearTimeout(t);
  }, [pathname]);

  if (!show) return null;
  return (
    <div
      key={tick}
      aria-hidden
      className="pointer-events-none fixed inset-x-0 top-0 z-50 h-0.5 overflow-hidden"
    >
      <div
        className="absolute top-0 h-full rounded-r-full bg-brand-500"
        style={{ animation: "amp-top-bar 800ms ease-out forwards" }}
      />
    </div>
  );
}
