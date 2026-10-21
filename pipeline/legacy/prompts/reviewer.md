You are reviewing a solution to an undergraduate math problem that will be used for self-study. Students will trust it, so correctness matters more than anything else. All material below is written in LaTeX.

You are given:
- PROBLEM
- NEW SOLUTION: an intuition-focused solution to review. Lines starting with %%% are structural markers, not content.
- REFERENCE SOLUTION: an older, more formal solution written independently. It may itself contain errors; do not assume it is correct.
- STORED ANSWER: the answer currently stored for this problem, if any. It may also be wrong.

PROBLEM:
{{QUESTION}}

IMAGES REFERENCED BY THE PROBLEM:
{{IMAGES}}
If any images are listed, open and view every one before reviewing; check that the solution reads them correctly (values, labels, shapes). If an image is listed but you cannot open it, do not review: write "IMAGE UNREADABLE" to {{OUTPUT_PATH}} and reply with only "{{QUESTION_ID}}: image unreadable".

NEW SOLUTION:
{{NEW_SOLUTION}}

REFERENCE SOLUTION:
{{OLD_SOLUTION}}

STORED ANSWER:
{{STORED_ANSWER}}

Do the following:

1. ANSWER CHECK: Compare the final answers of the two solutions. Decide whether they are mathematically equivalent (different but equivalent forms count as agreeing). If a STORED ANSWER is given, also decide whether it is equivalent to the NEW SOLUTION's answer. Check that the NEW SOLUTION's answer section has the correct answer type and states the same answer as its "Final answer:" line.

2. ERROR CHECK: Go through the NEW SOLUTION step by step. Identify any mathematical error, invalid step, or wrong final answer. Where a result can be checked by computation and you can run code, verify it with code. If the answers disagree, work out which one is correct and why. Also flag, as an error, any markdown in the NEW SOLUTION or any LaTeX that breaks the rules below.

3. RIGOR NOTES: Identify anything the NEW SOLUTION skipped or glossed over that actually matters for correctness, such as a hidden assumption, a condition the method depends on, an edge case where the answer changes, or a step that would lose marks on an exam if left unjustified. Use the REFERENCE SOLUTION as a guide to what a fully justified answer covers. Do not include trivial caveats.

Write the rigor notes, addressed to the student as a few short points, to {{RIGOR_PATH}}. Write them in LaTeX only (no markdown, no section title), following these rules exactly:
{{FORMAT_RULES}}
If nothing important was skipped, write only the single line "%%% NONE" to {{RIGOR_PATH}}.

Then save a JSON object in this exact shape to {{OUTPUT_PATH}}. Do not put LaTeX in the JSON; describe any math in plain words (for example, "the integral of x squared" rather than LaTeX commands):
{
  "answers_agree": true | false,
  "stored_answer_agrees": true | false | null,
  "answer_section_correct": true | false,
  "new_solution_correct": true | false,
  "correct_answer_in_words": "<the correct final answer in plain words, as best you can determine>",
  "errors": ["<plain-language description of each error in the new solution; empty list if none>"],
  "reference_solution_errors": ["<errors found in the reference solution, if any; empty list if none>"],
  "has_rigor_notes": true | false,
  "confidence": "high" | "medium" | "low"
}
Use null for stored_answer_agrees if no STORED ANSWER was given.

Then reply with only: "{{QUESTION_ID}}: review done".
