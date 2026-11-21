-- 013: how sure a question's classification is (owner 2026-11-21: record the
-- confidence of the sort). `classification_conf` is the confidence of the label
-- kept: high | medium | low. `classification_how` says how it was reached: high
-- (first pass sure), agree (first pass and blind second opinion agree), second
-- (the second opinion accepted), opus (decided by adjudication), with a refile-
-- prefix when the question was filed again after a tree change. NULL: labelled
-- before 2026-11-21 or by hand. Written only by taxonomy/tools/apply_full_run.py;
-- the app never writes it.
ALTER TABLE questions ADD COLUMN classification_conf TEXT;
ALTER TABLE questions ADD COLUMN classification_how TEXT;
