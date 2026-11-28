# Reclassification kit

Reclassifies rows whose label was chosen without the solution they have now. Owner rules:
- Rows labelled from the question alone are reclassified once solved, judged and embedded (2026-11-25).
- New imports classify only solved rows (2026-11-28).

This is the tooling the 2026-11-27/28 waves used: `taxonomy/full_run_20261128_reclass_{a,b,c,extra23}`.

The scripts write next to themselves, so **copy this folder to a work folder** (a scratchpad), and run from the repo
root unless a step says otherwise. Set:

```
export AMPLIFY_ROOT=<repo root>                     # prep_reclass.py, build7.py, passes_reclass.py read the DB and taxonomy here
export RECLASS_OUT=full_run_<yyyymmdd>_reclass_<x>  # passes_reclass.py writes taxonomy/$RECLASS_OUT
W=<work folder>
```

## Steps

1. **Embeddings first.** Run `python -m app.tools.reembed_solved` (dry run), then `--apply`. It embeds only rows with both
   a question and a solution, and nothing is reclassified before its embedding is current.
2. **Candidates.** From the repo root: `python $W/find_candidates.py`. It writes `$W/candidates.json` and prints the
   kinds:
   - `question_only` rows are the ones to reclassify.
   - `generated_changed` (about 6,800 from `full_run_20261126_reclass`) are known false positives: only the
     attribution line changed.
   - `book_then_generated_added` rows were labelled with their book solution in view, so they need nothing.
3. **Wave ids.** Write the `question_only` ids to `$W/wave_ids.json` as a JSON list.
4. **Route and build.** `cd $W`, then:
   - `python prep_reclass.py` writes `full/routed.json`.
   - `python build7.py` writes `full/in/*.txt` and `full/trees`.
   - Copy `CLASSIFY.md` and `TAGS_TEXT.md` into `$W/full/`. `run_classify.py` reads the brief from there, and the run
     fails at once without it.
5. **Classify and apply.** These are the passes `chain_reclass_extra23.sh` ran, from the repo root. Sonnet medium, then
   Opus medium for the low-confidence and invalid rows:

   ```
   VB=<any earlier batch file, for the request check>
   python pipeline/scripts/run_classify.py run --wave "$W/full" --in in --out out --brief CLASSIFY.md \
       --model claude-sonnet-5-5 --effort medium --workers 16 --wait-on-limit --force-unlock --verify-batch "$VB"
   python $W/passes_reclass.py adjud
   # only if $W/full/in3 has files:
   python pipeline/scripts/run_classify.py run --wave "$W/full" --in in3 --out out3 --brief CLASSIFY.md \
       --model claude-opus-5-5 --effort medium --workers 16 --wait-on-limit --force-unlock --verify-batch "$VB"
   python $W/passes_reclass.py final
   python $W/passes_reclass.py report      # taxonomy/$RECLASS_OUT/{final_labels.json, flags.csv, REPORT.md}
   python $W/passes_reclass.py relabels
   # back up app/data/appdata/amplify.db (sqlite backup API), then:
   python taxonomy/tools/apply_full_run.py --labels taxonomy/$RECLASS_OUT --apply
   python taxonomy/tools/apply_relabels.py --labels taxonomy/$RECLASS_OUT --apply
   ```

6. **Afterwards.** Commit `taxonomy/$RECLASS_OUT` and report its `flags.csv`: statements false or garbled as printed.
   Never apply labels while a judge import or an embedding is writing the DB; it fails with "database is locked".
