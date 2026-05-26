import { Card } from "@/components/ui/Card";

export default function TutorialPage() {
  return (
    <main className="mx-auto max-w-3xl space-y-4 px-6 py-10">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">Tutorial</h1>
        <p className="mt-1 text-sm text-muted">
          Quick orientation to every page in the app.
        </p>
      </header>

      <Card title="Practice">
        <p className="text-sm leading-relaxed">
          Pick subtopics from the topic tree (tri-state checkboxes — check a
          parent to include all children). Layer in tag, source, type, and
          mode filters. The status bar counts matches in real time as you
          adjust filters. Pick a question count and click{" "}
          <span className="font-mono">Start practice</span>.
        </p>
        <p className="mt-2 text-sm leading-relaxed">
          <strong>Mode</strong>: <em>Random</em> = uniform shuffle.{" "}
          <em>Diverse</em> = DPP-selected for broad coverage across the topic
          space. The Diversity badge on each session shows mean pairwise
          dissimilarity of the selected set.
        </p>
      </Card>

      <Card title="PBS — Parallel Burst Session">
        <p className="text-sm leading-relaxed">
          Three numerical-only questions visible at once. Each starts at 20
          points; wrong attempts <em>halve</em> the available score (min 1).
          A correct answer dequeues the widget and pulls the next from the
          pool. Beat the 5-minute clock.
        </p>
      </Card>

      <Card title="Browse">
        <p className="text-sm leading-relaxed">
          Paginated question viewer. Each question page renders the LaTeX in
          the browser (no PDF, no install) and offers a{" "}
          <em>Reveal solution</em> toggle. Below the solution: top-6 similar
          questions via cosine-KNN on the embedding vectors.
        </p>
      </Card>

      <Card title="Your mastery (/me)">
        <p className="text-sm leading-relaxed">
          Bayesian Beta posterior per subtopic. The Lower Credibility Bound
          ranks weakness — penalising low-evidence rows so a 0/0 prior
          doesn&rsquo;t beat a 5/5 prior. The personalised welcome strip on{" "}
          <span className="font-mono">/</span> uses the same signal.
        </p>
      </Card>

      <Card title="Stats">
        <p className="text-sm leading-relaxed">
          Eight numeric cards plus four D3 charts: topic distribution pie,
          multiplicity histogram, last-30-day activity line, and a
          calendar-heatmap of practice days for the current year.
        </p>
      </Card>

      <Card title="History">
        <p className="text-sm leading-relaxed">
          Your last 50 practice sessions. Each row shows the filters,
          generation mode, diversity score, and answered/total. Click{" "}
          <em>Run again</em> to spin up an identical fresh session.
        </p>
      </Card>

      <Card title="Themes">
        <p className="text-sm leading-relaxed">
          Nine themes ship: Default Light, Default Dark, Pastel,
          Frutiger Aero, Pixel Art, Windows XP, Comic, ASCII, Android KitKat.
          Each ships its own font, colors, accent, and tooltip flavor.
          Switch via the glyph button in the top-right of the nav; the
          choice persists in localStorage.
        </p>
      </Card>
    </main>
  );
}
