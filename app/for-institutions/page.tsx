import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "For institutions",
  description:
    "Bring Amplify to your university. A peer-reviewed problem-bank for your courses, faculty dashboards, cohort mastery analytics. Free for students and faculty; institutional licenses fund the platform.",
};

export default function ForInstitutionsPage() {
  return (
    <main className="hero-bg">
      <section className="mx-auto max-w-3xl px-6 py-20">
        <span className="self-start rounded-full border border-ink-200 px-3 py-1 text-xs font-medium uppercase tracking-wider text-ink-500">
          for universities · departments · institutes
        </span>

        <h1 className="display mt-7 text-4xl font-semibold sm:text-5xl">
          Make your institution
          <br />
          <span className="text-ink-500">
            the next on Amplify.
          </span>
        </h1>

        <p className="mt-6 text-lg text-ink-500">
          Every STEM department in the world has the same problem: the
          institutional knowledge of how to teach calculus, eigenvalues, or
          Maxwell&apos;s equations is locked inside individual faculty
          members&apos; LaTeX files. It does not compound. It does not
          transfer. It is not measured.
        </p>
        <p className="mt-4 text-lg text-ink-500">
          Amplify is the canonical home for that knowledge.
        </p>

        <div className="mt-12 space-y-12">
          <Section
            number="01"
            title="The problem nobody owns"
            body={
              <>
                <p>
                  Students at every IIT, IIM, and STEM-track university in the
                  world practice the same way: hunt for problem sets in a
                  Dropbox folder, print a PDF, write answers in a notebook,
                  find out next week from the TA if they were right. There is
                  no instant feedback. No record of what they&apos;ve
                  practiced. No view of where their gaps are.
                </p>
                <p className="mt-3">
                  Faculty have it worse: a new problem set is a 30-minute
                  copy-paste-and-swap-numbers task, the LaTeX breaks every
                  alignment, last year&apos;s questions are scattered across
                  five `.tex` files. There is no version control, no peer
                  review, no measurement of which questions actually teach the
                  concept.
                </p>
                <p className="mt-3">
                  The vendor alternatives — WebAssign, Pearson MyLab, ALEKS —
                  are paywalled, hated by students, and locked to the
                  publisher&apos;s textbook. They are not what your faculty
                  would build if they were given a year.
                </p>
              </>
            }
          />

          <Section
            number="02"
            title="What Amplify gives an institution"
            body={
              <ul className="list-disc space-y-3 pl-5">
                <li>
                  <strong>A branded problem-bank</strong> for your courses.
                  Custom URL (e.g.{" "}
                  <code className="rounded bg-ink-100 px-1.5 py-0.5 text-sm">
                    amplify.app/i/your-uni
                  </code>
                  ). Faculty add and curate; students practice; the bank
                  compounds every semester.
                </li>
                <li>
                  <strong>Faculty dashboards.</strong> Aggregate cohort
                  mastery, by subtopic, in real time. Spot the topics your
                  cohort is bombing <em>before</em> the midterm.
                </li>
                <li>
                  <strong>Peer review built in.</strong> Every accepted
                  question has an author, a review trail, and a revision
                  history. Faculty get co-author credit; nothing disappears
                  into a black box.
                </li>
                <li>
                  <strong>Exam paper generation</strong> in seconds. Filter by
                  topic, difficulty, source. Export to LaTeX, PDF, or print
                  directly from the browser.
                </li>
                <li>
                  <strong>Open standards.</strong> Export to QTI, Canvas,
                  Moodle, Anki, raw LaTeX. We are the source of truth;
                  everything else is an export target.
                </li>
                <li className="opacity-60">
                  <strong>Coming:</strong> SSO with your campus IdP, LMS
                  integration (Canvas / Moodle / Blackboard), proctored
                  in-browser assessments, plagiarism detection on student
                  solutions.
                </li>
              </ul>
            }
          />

          <Section
            number="03"
            title="What we ask for in a pilot"
            body={
              <ul className="list-disc space-y-3 pl-5">
                <li>
                  <strong>One course.</strong> A freshman flagship — calculus,
                  linear algebra, classical mechanics, intro programming.
                  Whatever you teach, whatever has the most students.
                </li>
                <li>
                  <strong>Your existing problem-set archive.</strong> We
                  typeset, tag, and import it. You review and accept. The bank
                  is yours.
                </li>
                <li>
                  <strong>A Moodle announcement</strong> when the semester
                  starts. No mandate — just &quot;the practice tool for this
                  course is at <em>amplify.app/i/...</em>.&quot; Students do
                  the rest.
                </li>
              </ul>
            }
          />

          <Section
            number="04"
            title="Pricing"
            body={
              <>
                <p>
                  Free for individual students and individual faculty,
                  forever. No paywall, no &quot;your free trial has ended,&quot;
                  no upgrade nag.
                </p>
                <p className="mt-3">
                  Institutional licenses are how the platform funds itself.
                  They unlock SSO, LMS integration, in-platform exams,
                  department-level analytics, custom branding, and priority
                  ingestion of your archive. Pilot programs are free for the
                  first two semesters while we get the integration right.
                </p>
                <p className="mt-3 text-sm text-ink-500">
                  We are deliberately not charging students. Charging students
                  is what made the incumbents hated. We will not repeat that
                  mistake.
                </p>
              </>
            }
          />

          <Section
            number="05"
            title="The bigger picture"
            body={
              <>
                <p>
                  Amplify started at IIT-Delhi Abu Dhabi. The next step is the
                  IIT system — 23 campuses, 16,000 STEM students per year,
                  with a shared curricular spine. After that: engineering
                  colleges across India (10,000+ institutions, 3M students
                  per year), then Olympiad coaching, then universities in the
                  US, UK, and EU.
                </p>
                <p className="mt-3">
                  Each step is credible because the last one delivered evidence.
                  We&apos;re looking for the institutions that want to be on
                  the front of that timeline, not the back.
                </p>
              </>
            }
          />
        </div>

        {/* CTA */}
        <div className="mt-20 rounded-xl border border-ink-200 bg-ink-50 p-8 text-center">
          <h2 className="display text-2xl font-semibold">
            Bring Amplify to your campus.
          </h2>
          <p className="mt-2 text-sm text-ink-500">
            Email us a one-liner. We&apos;ll be back to you in 24 hours.
          </p>
          <a
            href="mailto:24a1cseb0015@iitdabudhabi.ac.ae?subject=Amplify%20pilot%20at%20[your%20institution]"
            className="mt-6 inline-block rounded-md bg-ink-900 px-6 py-3 text-sm font-medium text-white hover:bg-ink-700"
          >
            Start a conversation
          </a>
          <p className="mt-4 text-xs text-ink-400">
            or DM{" "}
            <a
              href="https://github.com/joelynx/Amplify"
              className="underline hover:text-ink-700"
            >
              github.com/joelynx/Amplify
            </a>
          </p>
        </div>

        <p className="mt-12 text-center text-xs text-ink-400">
          <Link href="/" className="underline hover:text-ink-700">
            ← back to amplify
          </Link>
        </p>
      </section>
    </main>
  );
}

function Section({
  number,
  title,
  body,
}: {
  number: string;
  title: string;
  body: React.ReactNode;
}) {
  return (
    <section>
      <div className="flex items-baseline gap-3">
        <span className="font-mono text-xs text-brand-600">{number}</span>
        <h2 className="display text-2xl font-semibold">{title}</h2>
      </div>
      <div className="mt-4 text-ink-700">{body}</div>
    </section>
  );
}
