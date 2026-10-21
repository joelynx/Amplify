-- 006: provenance of the embedding vectors, so re-embedding is incremental.
-- emb_text_hash = sha256 of the exact text that was embedded (app/tools/reembed.py
-- builds it: task prefix + question + best available solution); emb_model = the
-- Gemini model id. A row whose current text hashes differently is re-embedded.
ALTER TABLE questions ADD COLUMN emb_text_hash TEXT;
ALTER TABLE questions ADD COLUMN emb_model TEXT;
