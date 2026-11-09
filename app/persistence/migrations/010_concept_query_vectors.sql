-- 010: query vectors for lecture-keyword retrieval (Low_Hanging_Fruit.md §3,
-- stage 2). One row per concept (topic, branch, subtopic or tag), embedded
-- ahead of time by app/tools/retrieval_embed.py in the asymmetric query format;
-- the app never embeds at run time. A lecture session orders each concept's
-- questions by cosine between this vector and the question's similarity_emb.
-- Concepts without a row keep the diverse pick.
--
-- query_key is app.core.retrieval.query_key(): "tag:<name>" for tags and
-- "<kind>:<topic › branch › subtopic>" for taxonomy nodes.
CREATE TABLE concept_query_vectors (
    query_key     TEXT PRIMARY KEY,
    kind          TEXT NOT NULL,
    label         TEXT NOT NULL,
    emb           BLOB NOT NULL,
    emb_model     TEXT NOT NULL,
    emb_text_hash TEXT NOT NULL
);

CREATE INDEX idx_concept_query_vectors_label ON concept_query_vectors(kind, label);
