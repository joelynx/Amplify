/**
 * About — spec §8 / §13. Static blurb + dynamic credits sourced from the
 * questions table's distinct `source` values.
 */

import { useEffect, useState } from "react";

import { Logo } from "../appearance/brand/Logo";
import { allItems } from "../appearance/registry";
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
    <main className="h-full overflow-y-auto">
      <div className="mx-auto max-w-3xl space-y-6 px-6 py-6">
        <header>
          <h1 className="text-2xl font-semibold">About Amplify</h1>
          <p className="text-sm text-muted">
            Practice problem sets from a curated bank — offline, local, single-user.
            {version && <> Version {version}.</>}
          </p>
        </header>

        <Card title="The clubs">
          <div className="flex flex-wrap items-center gap-6">
            <Logo name="matrix" style={{ width: 150 }} />
            <Logo name="coding" style={{ width: 180 }} />
          </div>
          <p className="mt-3 text-sm leading-relaxed">
            Amplify is an offering of ampliφ, the Mathematics Club, and the Coding Club at IIT Delhi – Abu Dhabi. The
            ampliφ logo is a diagonal matrix whose entries, amp(z), li(x) and φ(n), spell the club's name.
          </p>
        </Card>

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
            <p className="text-muted">No sources yet. Import the question bank in Settings first.</p>
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

        <AssetCredits />
      </div>
    </main>
  );
}

/** Credits for palettes, fonts and packs, from each item's `credits`. */
function AssetCredits() {
  const credits = allItems().flatMap((i) => (i.credits ?? []).map((c) => ({ ...c, item: i.name })));
  if (credits.length === 0) return null;
  return (
    <Card title="Theme credits">
      <ul className="space-y-1 text-sm">
        {credits.map((c, k) => (
          <li key={k}>
            <span className="font-medium">{c.item}</span> ({c.what}): {c.who}, {c.license}
            {c.url && <span className="text-muted"> · {c.url}</span>}
          </li>
        ))}
      </ul>
    </Card>
  );
}
