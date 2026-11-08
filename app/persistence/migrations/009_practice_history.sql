-- 009: what the student did with each question, for the review queue and the
-- learning stats (Low_Hanging_Fruit.md §1-2).
--
-- answer_events: one row per finished answer ('answered') or per question whose
-- answer / solution was opened before answering ('revealed', no grade). Paper
-- results recorded from History are 'answered' rows with mode 'PAPER' and the
-- pset_id. hints_used / revealed / self_assessed are NULL when not recorded:
-- Traverse and Discover answers from before 009 never captured hint use, and
-- they stay "unknown" rather than being read as unassisted.
CREATE TABLE answer_events (
    event_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id   INTEGER NOT NULL,
    quiz_id       TEXT,
    pset_id       TEXT,
    mode          TEXT    NOT NULL,
    occurred_at   TEXT    NOT NULL,
    kind          TEXT    NOT NULL CHECK (kind IN ('answered', 'revealed')),
    credit        REAL,
    self_assessed INTEGER,
    hints_used    INTEGER,
    revealed      INTEGER,
    time_taken_ms INTEGER,
    FOREIGN KEY (question_id) REFERENCES questions(question_id) ON DELETE CASCADE
);

CREATE INDEX idx_answer_events_question ON answer_events(question_id, occurred_at);
CREATE INDEX idx_answer_events_time     ON answer_events(occurred_at);
CREATE INDEX idx_answer_events_pset     ON answer_events(pset_id);

-- Back-fill from the answer logs already stored on quiz attempts. Skips are not
-- answers. Records from before answer keys carry no credit: read it from the
-- self-assessment, else from `correct`.
INSERT INTO answer_events (
    question_id, quiz_id, mode, occurred_at, kind, credit,
    self_assessed, hints_used, revealed, time_taken_ms
)
SELECT
    CAST(json_extract(j.value, '$.question_id') AS INTEGER),
    a.quiz_id,
    COALESCE(z.template_name, 'QUIZ'),
    COALESCE(NULLIF(json_extract(j.value, '$.submitted_at'), ''), a.date_started),
    'answered',
    COALESCE(
        json_extract(j.value, '$.credit'),
        CASE json_extract(j.value, '$.self_assessment')
            WHEN 'got_it' THEN 1.0 WHEN 'partial' THEN 0.5 WHEN 'missed' THEN 0.0 END,
        CASE json_extract(j.value, '$.correct') WHEN 1 THEN 1.0 WHEN 0 THEN 0.0 END
    ),
    CASE
        WHEN json_extract(j.value, '$.self_assessment') IS NOT NULL THEN 1
        WHEN EXISTS (
            SELECT 1 FROM json_each(j.value, '$.parts') p
            WHERE json_extract(p.value, '$.mark') IS NOT NULL
        ) THEN 1
        ELSE 0
    END,
    CASE WHEN z.template_name IN ('TRAVERSE', 'DISCOVER') THEN NULL
         ELSE json_extract(j.value, '$.hints_used') END,
    NULL,
    json_extract(j.value, '$.time_taken_ms')
FROM quiz_attempts a
JOIN quizzes z ON z.quiz_id = a.quiz_id
JOIN json_each(a.summary, '$.answers') j
WHERE json_valid(a.summary)
  AND COALESCE(json_extract(j.value, '$.self_assessment'), '') <> 'skipped'
  AND COALESCE(
        json_extract(j.value, '$.credit'),
        CASE json_extract(j.value, '$.self_assessment')
            WHEN 'got_it' THEN 1.0 WHEN 'partial' THEN 0.5 WHEN 'missed' THEN 0.0 END,
        CASE json_extract(j.value, '$.correct') WHEN 1 THEN 1.0 WHEN 0 THEN 0.0 END
      ) IS NOT NULL
  AND EXISTS (
        SELECT 1 FROM questions qs
        WHERE qs.question_id = CAST(json_extract(j.value, '$.question_id') AS INTEGER)
      );

-- When a quiz question was actually put in front of the student. Discover used
-- to count its whole batch as used at the start; from 009 a question counts
-- when it is shown. Earlier rows keep the old meaning (shown at creation).
ALTER TABLE quiz_questions ADD COLUMN presented_at TEXT;
UPDATE quiz_questions
SET presented_at = (SELECT date_created FROM quizzes WHERE quizzes.quiz_id = quiz_questions.quiz_id);

-- A personal note per question (self-explanations land here too) and a bookmark.
CREATE TABLE question_notes (
    question_id INTEGER PRIMARY KEY,
    note        TEXT    NOT NULL DEFAULT '',
    bookmarked  INTEGER NOT NULL DEFAULT 0,
    updated_at  TEXT    NOT NULL,
    FOREIGN KEY (question_id) REFERENCES questions(question_id) ON DELETE CASCADE
);

CREATE INDEX idx_question_notes_bookmarked ON question_notes(bookmarked);

-- Questions the student took out of the review queue. A later answer brings the
-- question back (the queue only skips events up to dismissed_at).
CREATE TABLE review_dismissals (
    question_id  INTEGER PRIMARY KEY,
    dismissed_at TEXT    NOT NULL,
    FOREIGN KEY (question_id) REFERENCES questions(question_id) ON DELETE CASCADE
);
