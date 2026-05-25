/**
 * About — spec §8 / §13. Static blurb + dynamic credits sourced from the
 * questions table's distinct `source` values.
 */

import { useEffect, useState } from "react";

import { Card } from "../components/ui/Card";
import { ipc } from "../lib/ipc";

export default function AboutPage() {
  const [sources, setSources] = useState<string[]>([]);
  const [version, setVersion] = useState<string>("");

  useEffect(() => {
    ipc.get_sources().then(setSources);
    ipc.get_config("VERSION").then((v) => setVersion(typeof v === "string" ? v : ""));
  }, []);

  return (
    <main className="flex-1 overflow-y-auto">
      <div className="mx-auto max-w-3xl space-y-6 px-6 py-6">
        <header>
          <h1 className="text-2xl font-semibold">About Amplify</h1>
          <p className="text-sm text-muted">
            Practice problem sets from a curated bank — offline, local, single-user.
            {version && <> Version {version}.</>}
          </p>
        </header>

        <Card title="What this is">
          <p className="text-sm leading-relaxed">
            Amplify turns a curated LaTeX question bank into typeset PDFs, statistics, and
            (Phase 2) interactive practice sessions. Everything runs locally — no API calls
            and no cloud sync. The seed bank ships with vector embeddings and solution
            outlines pre-generated; the runtime never produces those itself.
          </p>
        </Card>

        <Card title="Question sources">
          {sources.length === 0 ? (
            <p className="text-muted">No sources yet — ingest the seed bundle first.</p>
          ) : (
            <ul className="grid grid-cols-1 gap-1 text-sm sm:grid-cols-2">
              {sources.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ul>
          )}
        </Card>

        <Card title="Stack">
          <ul className="space-y-1 text-sm">
            <li>PyWebView shell (Python ↔ JS bridge)</li>
            <li>SQLite (single-file persistence)</li>
            <li>React + Vite + Tailwind (UI)</li>
            <li>D3 (charts)</li>
            <li>XeLaTeX via TinyTeX (PDF compilation)</li>
            <li>LanceDB (embeddings, ingest-time only)</li>
          </ul>
        </Card>
      </div>
    </main>
  );
}
