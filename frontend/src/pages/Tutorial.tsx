/** Tutorial — static help (spec §8). Expand as features land. */

import { Card } from "../components/ui/Card";

export default function TutorialPage() {
  return (
    <main className="h-full overflow-y-auto">
      <div className="mx-auto max-w-3xl space-y-4 px-6 py-6">
        <header>
          <h1 className="text-2xl font-semibold">Tutorial</h1>
          <p className="text-sm text-muted">Quick orientation to the main pages.</p>
        </header>

        <Card title="Generate">
          <p className="text-sm">
            Pick subtopics from the tree (or check whole branches / topics — the form respects
            the deepest non-empty level). Layer in tag, source, type, difficulty, and reuse
            filters. The status bar counts matches live. Pick a save directory + a question
            count, then click <span className="font-mono">Generate PDF</span>.
          </p>
        </Card>

        <Card title="Quiz">
          <p className="text-sm">
            <em>Review</em> brings back questions when they are due: a miss or an answer you needed
            help with returns the next day, and questions you solve on your own return after longer
            gaps (3, 7, then 21 days) before they retire. <em>From a lecture</em> takes the
            lecture's keywords (abbreviations like SVD or CLT work), shows what each matched so you
            can untick wrong guesses, then practises across them. <em>Mixed review</em> interleaves
            techniques you have studied and hides the technique until you answer. Opening a hint
            or the solution before answering counts as help, and the question goes on the
            "try independently" list.
          </p>
        </Card>

        <Card title="Subjects">
          <p className="text-sm">
            A Subject is a curricular bundle pointing to topics, with optional branch /
            subtopic exclusions. The active subject scopes the Generate tree and stats. Subjects
            export to JSON for sharing with another Amplify install.
          </p>
        </Card>

        <Card title="History">
          <p className="text-sm">
            Every successful generate creates a PSet row with the questions, filters, and save
            directory. From the History page you can <em>Open</em> the saved PDF,{" "}
            <em>Re-export</em> the same questions, <em>Generate similar</em> (pre-fills the form
            with the recorded filters), <em>Record results</em> for work done on paper (solved,
            partial, missed; misses come back for review), or <em>Delete</em> the row.
          </p>
        </Card>

        <Card title="Themes">
          <p className="text-sm">
            Two defaults and seven flavor themes are always available; three more (Sage, Ember,
            Midnight) unlock with practice milestones: spaced reviews, fixing old mistakes, and
            honest attempts. Switching applies live; the choice persists. Each theme provides its
            own <span className="font-mono">.amplify-tooltip</span> shape on chart hover.
          </p>
        </Card>

        <Card title="Settings">
          <p className="text-sm">
            Configure default question count, save location, PDF header text, and theme. The
            Data card has buttons to <em>Re-run seed ingest</em> and <em>Augment seed from CSV</em>,
            plus diagnostics about embeddings / outlines coverage.
          </p>
        </Card>
      </div>
    </main>
  );
}
