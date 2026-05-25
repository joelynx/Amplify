-- Step 8 (History page) needs to know where each PSet's PDF actually lives
-- so "Open" and "Re-export" can find it; the original spec's psets schema
-- (§3.4) didn't carry the save dir. include_sources is added so re-export
-- mirrors the user's original choice when assembling.
-- Existing rows get NULL/default — Open falls back to configs.FILE_SAVE_LOCATION.
ALTER TABLE psets ADD COLUMN save_directory  TEXT;
ALTER TABLE psets ADD COLUMN include_sources INTEGER NOT NULL DEFAULT 1;
