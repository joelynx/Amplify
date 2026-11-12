-- 012: tiered hints. `hints` stays the first (gentlest) hint; `more_hints` holds
-- the further tiers as a JSON array of LaTeX strings, tier 2 then tier 3 (at
-- most three tiers in all). NULL means the question has only the one hint in
-- `hints`. The quiz reveals the tiers one at a time ("Show additional hint").
-- Written only by imports and the pipeline; the app never writes it.
ALTER TABLE questions ADD COLUMN more_hints TEXT;
