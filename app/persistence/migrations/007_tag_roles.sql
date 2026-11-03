-- 007: every tag row carries a role. Technique tags are 'key' (the idea the
-- solution rests on) or 'supporting' (a technique that does real work but is
-- not the main idea); task tags, which name what the question asks (for
-- example "Point Finding"), are 'task'. Existing rows default to 'key'.
ALTER TABLE question_tags ADD COLUMN role TEXT NOT NULL DEFAULT 'key'
    CHECK (role IN ('key', 'supporting', 'task'));
CREATE INDEX IF NOT EXISTS idx_question_tags_tag_role ON question_tags(tag, role);
