-- Spec §3.1 enumerates question types as lowercase (`proof`, `numerical`,
-- `explanation/reasoning`). The shipped seed CSV had a handful of 'Proof' /
-- 'Numerical' rows that broke "distinct types" listings. Normalize in place;
-- new ingest writes lowercase, so this only ever fixes legacy rows.
UPDATE questions
SET type = LOWER(TRIM(type))
WHERE type IS NOT NULL AND type <> LOWER(TRIM(type));
