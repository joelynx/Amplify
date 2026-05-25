import { useEffect, useState } from "react";
import { HashRouter, Link, Route, Routes, useLocation } from "react-router-dom";

import { BridgeUnavailableError, ipc } from "./lib/ipc";
import GeneratePage from "./pages/Generate";
import WelcomePage from "./pages/Welcome";

/**
 * Top-level shell. Probes the PyWebView bridge on mount so that — if the user
 * opens `localhost:5173` in a regular browser — every page degrades to the
 * "browser preview" state instead of dying with a 1.5s timeout.
 */

export default function App() {
  const [bridgeState, setBridgeState] = useState<"connecting" | "ready" | "standalone">("connecting");

  useEffect(() => {
    ipc
      .ping()
      .then(() => setBridgeState("ready"))
      .catch((e: unknown) => {
        if (e instanceof BridgeUnavailableError) {
          setBridgeState("standalone");
        } else {
          setBridgeState("standalone");
        }
      });
  }, []);

  if (bridgeState === "connecting") {
    return (
      <main className="flex h-full items-center justify-center">
        <p className="text-muted">Connecting to Python…</p>
      </main>
    );
  }

  if (bridgeState === "standalone") {
    return (
      <main className="flex h-full items-center justify-center px-6">
        <div className="space-y-2 text-center">
          <h1 className="text-3xl font-semibold">Amplify</h1>
          <p className="text-muted">
            Browser preview — IPC unavailable. Launch via{" "}
            <code className="font-mono">uv run python -m app.main</code> for full integration.
          </p>
        </div>
      </main>
    );
  }

  return (
    <HashRouter>
      <div className="flex h-full flex-col">
        <NavBar />
        <div className="flex-1 overflow-hidden">
          <Routes>
            <Route path="/" element={<WelcomePage />} />
            <Route path="/generate" element={<GeneratePage />} />
          </Routes>
        </div>
      </div>
    </HashRouter>
  );
}

const NAV: Array<{ to: string; label: string }> = [
  { to: "/", label: "Home" },
  { to: "/generate", label: "Generate" },
];

function NavBar() {
  const { pathname } = useLocation();
  return (
    <nav className="flex h-12 items-center gap-1 border-b border-border bg-surface px-4 text-sm">
      <span className="mr-3 font-semibold tracking-tight">Amplify</span>
      {NAV.map((item) => {
        const active = pathname === item.to;
        return (
          <Link
            key={item.to}
            to={item.to}
            className={
              "rounded-md px-3 py-1.5 text-text/80 hover:bg-background hover:text-text " +
              (active ? "bg-background text-text font-medium" : "")
            }
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
