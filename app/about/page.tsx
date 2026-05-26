import { Card } from "@/components/ui/Card";
import { getAllSources } from "@/lib/cached";
import { getServerSupabase } from "@/lib/supabase/server";

export default async function AboutPage() {
  const sources = await getAllSources();
  const supabase = await getServerSupabase();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  return (
    <main className="mx-auto max-w-3xl space-y-6 px-6 py-10">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">About</h1>
      </header>

      <Card title="What this is">
        <p className="text-sm leading-relaxed">
          A peer-reviewed open bank of university math, physics, and CS
          problems with mastery-tracked practice on top. Each question carries
          a vector embedding, which lets the app generate practice sets that
          cover the concept space evenly, surface similar questions, and rank
          difficulty against the actual pool instead of against a textbook
          editor&rsquo;s guess.
        </p>
      </Card>

      <Card title="Stack">
        <ul className="space-y-1 text-sm">
          <li>Next.js 15, React 19, TypeScript</li>
          <li>Supabase Postgres with pgvector (HNSW) and row-level security</li>
          <li>Gemini text-embedding-001 truncated to 768 dimensions (Matryoshka)</li>
          <li>Bayesian Beta posterior per (user, subtopic) for mastery</li>
          <li>Determinantal point processes for diverse practice generation</li>
          <li>KaTeX for math rendering, D3 for charts</li>
        </ul>
      </Card>

      <Card title="Question sources">
        {sources.length === 0 ? (
          <p className="text-sm text-muted">
            No sources yet. Seed the bank from{" "}
            <span className="font-mono">Files/TEST.csv</span>.
          </p>
        ) : (
          <ul className="grid grid-cols-1 gap-1 text-sm sm:grid-cols-2">
            {sources.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
        )}
      </Card>

      <Card title="Credits">
        <p className="text-sm">
          Built by Karth Puthiyedathu and Joel Jobi at IIT Delhi Abu Dhabi.
        </p>
      </Card>

      {user && (
        <Card title="Account">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm text-ink-700">
              Signed in as <span className="font-medium">{user.email}</span>
            </p>
            <form action="/auth/signout" method="post">
              <button
                type="submit"
                className="rounded-md border border-ink-200 bg-white px-3 py-1.5 text-sm font-medium hover:bg-ink-50"
              >
                Sign out
              </button>
            </form>
          </div>
        </Card>
      )}
    </main>
  );
}
