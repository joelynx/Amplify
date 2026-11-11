-- A hint or solution the student marked as unusable (wrong, about the wrong
-- question, or a note about the data rather than help). Flagged parts are
-- hidden behind a notice in Quiz and the Browser, and listed in Settings so
-- the bank can be repaired.
CREATE TABLE content_flags (
    question_id INTEGER NOT NULL,
    part        TEXT    NOT NULL CHECK (part IN ('hint', 'solution')),
    flagged_at  TEXT    NOT NULL,
    PRIMARY KEY (question_id, part),
    FOREIGN KEY (question_id) REFERENCES questions(question_id) ON DELETE CASCADE
);
