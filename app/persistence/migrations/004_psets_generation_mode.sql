-- Step 22 (Diverse/Focused/Frontier generation): record which strategy a PSet
-- was generated with, and for the Diverse path also store the measured
-- 1 - mean_pairwise_cosine on the selected embeddings as a quality readout.
-- Existing rows default to 'random' so the History page can colour them
-- consistently without a backfill script.
ALTER TABLE psets ADD COLUMN generation_mode TEXT NOT NULL DEFAULT 'random';
ALTER TABLE psets ADD COLUMN diversity_score REAL;
