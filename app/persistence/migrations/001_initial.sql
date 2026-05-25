-- Initial schema. Tables per spec §3.
-- The `migrations` table is bootstrapped by app/persistence/db.py before this
-- file runs; it is intentionally NOT created here.

-- §3.1 questions ----------------------------------------------------------
CREATE TABLE questions (
    question_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    semester               INTEGER,
    topic                  TEXT    NOT NULL,
    branch                 TEXT    NOT NULL,
    subtopic               TEXT    NOT NULL,
    latexcode              TEXT    NOT NULL,
    type                   TEXT,
    in_syllabus            INTEGER NOT NULL DEFAULT 1,
    source                 TEXT,
    subsource              TEXT,
    answer                 TEXT,
    solution               TEXT,
    solution_outline       TEXT,
    hints                  TEXT,
    instructions           TEXT,
    date_last_accessed     TEXT,
    times_used             INTEGER NOT NULL DEFAULT 0,
    interactive_times_used INTEGER NOT NULL DEFAULT 0,
    difficulty_rating      REAL,
    latex_hash             TEXT    NOT NULL UNIQUE,
    classification_emb     BLOB,
    similarity_emb         BLOB
);

CREATE INDEX idx_questions_topic     ON questions(topic);
CREATE INDEX idx_questions_branch    ON questions(topic, branch);
CREATE INDEX idx_questions_subtopic  ON questions(topic, branch, subtopic);
CREATE INDEX idx_questions_in_syll   ON questions(in_syllabus);
CREATE INDEX idx_questions_type      ON questions(type);
CREATE INDEX idx_questions_source    ON questions(source);
CREATE INDEX idx_questions_times     ON questions(times_used);

-- §3.2 question_tags ------------------------------------------------------
CREATE TABLE question_tags (
    question_id INTEGER NOT NULL,
    tag         TEXT    NOT NULL,
    PRIMARY KEY (question_id, tag),
    FOREIGN KEY (question_id) REFERENCES questions(question_id) ON DELETE CASCADE
);

CREATE INDEX idx_question_tags_tag ON question_tags(tag);

-- §3.3 templates ----------------------------------------------------------
CREATE TABLE templates (
    name             TEXT    PRIMARY KEY,
    subject          TEXT,
    topic_list       TEXT,
    branch_list      TEXT,
    subtopic_list    TEXT,
    type_list        TEXT,
    source_list      TEXT,
    tag_list         TEXT,
    n_questions      INTEGER NOT NULL,
    reuse_questions  INTEGER NOT NULL,
    include_sources  INTEGER NOT NULL,
    in_syllabus_only INTEGER NOT NULL,
    min_difficulty   REAL,
    save_directory   TEXT,
    -- Spec §6.5 / dev cycle Step 6 — solutions placement captured in templates.
    solutions        TEXT
);

-- §3.4 psets + pset_questions --------------------------------------------
CREATE TABLE psets (
    pset_id         TEXT    PRIMARY KEY,
    date_created    TEXT    NOT NULL,
    subject         TEXT,
    topic_list      TEXT,
    branch_list     TEXT,
    subtopic_list   TEXT,
    source_list     TEXT,
    type_list       TEXT,
    tag_list        TEXT,
    n_questions     INTEGER NOT NULL,
    reuse_questions INTEGER NOT NULL,
    template_name   TEXT,
    topic_dist      TEXT,
    subtopic_dist   TEXT,
    solutions       TEXT
);

CREATE INDEX idx_psets_date_created ON psets(date_created);
CREATE INDEX idx_psets_subject      ON psets(subject);

CREATE TABLE pset_questions (
    pset_id        TEXT    NOT NULL,
    question_id    INTEGER NOT NULL,
    question_order INTEGER NOT NULL,
    PRIMARY KEY (pset_id, question_id),
    FOREIGN KEY (pset_id)     REFERENCES psets(pset_id)         ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(question_id) ON DELETE CASCADE
);

CREATE INDEX idx_pset_questions_qid ON pset_questions(question_id);

-- §3.5 quizzes / quiz_questions / quiz_attempts  (Phase 2; created now per dev cycle Step 2) ------
CREATE TABLE quizzes (
    quiz_id              TEXT    PRIMARY KEY,
    date_created         TEXT    NOT NULL,
    subject              TEXT,
    topic_list           TEXT,
    branch_list          TEXT,
    subtopic_list        TEXT,
    source_list          TEXT,
    type_list            TEXT,
    tag_list             TEXT,
    n_questions          INTEGER NOT NULL,
    reuse_questions      INTEGER NOT NULL,
    template_name        TEXT,
    -- quiz-specific settings (spec §3.5 / §10)
    time_per_question    INTEGER,
    total_time           INTEGER,
    allow_skips          INTEGER NOT NULL DEFAULT 1,
    show_scoring         INTEGER NOT NULL DEFAULT 1,
    penalize_skips_marks REAL,
    enable_hints         INTEGER NOT NULL DEFAULT 1,
    instant_scoring      INTEGER NOT NULL DEFAULT 0,
    show_solutions       INTEGER NOT NULL DEFAULT 0,
    gradient_mode        TEXT,
    wait_for_correct     INTEGER NOT NULL DEFAULT 0,
    -- PBS-specific overlay (spec §10.1)
    pbs_num_widgets      INTEGER,
    pbs_pool_size        INTEGER
);

CREATE TABLE quiz_questions (
    quiz_id        TEXT    NOT NULL,
    question_id    INTEGER NOT NULL,
    question_order INTEGER NOT NULL,
    PRIMARY KEY (quiz_id, question_id),
    FOREIGN KEY (quiz_id)     REFERENCES quizzes(quiz_id)       ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(question_id) ON DELETE CASCADE
);

CREATE TABLE quiz_attempts (
    attempt_id    TEXT    PRIMARY KEY,
    quiz_id       TEXT    NOT NULL,
    date_started  TEXT    NOT NULL,
    date_finished TEXT,
    total_score   REAL,
    summary       TEXT,
    FOREIGN KEY (quiz_id) REFERENCES quizzes(quiz_id) ON DELETE CASCADE
);

CREATE INDEX idx_quiz_attempts_quiz ON quiz_attempts(quiz_id);

-- §3.6 subjects -----------------------------------------------------------
CREATE TABLE subjects (
    name      TEXT    PRIMARY KEY,
    payload   TEXT    NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 0
);

-- At most one active subject (spec §3.6). Partial unique index on the flag.
CREATE UNIQUE INDEX idx_subjects_one_active ON subjects(is_active) WHERE is_active = 1;

-- §3.7 configs ------------------------------------------------------------
CREATE TABLE configs (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
