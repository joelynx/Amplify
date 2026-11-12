Role: {{ROLE}}

Task: The message gives a question and the textbook's own worked solution to it. The book's solution stays exactly as it is; it is what the student will read. Your job is to add what a student studying on their own needs around it: an answer key so they can check their own attempt, hints for when they are stuck, and takeaways. Read the question and the book's solution carefully and base everything on them.

INSTRUCTIONS:

1. BOOK CHECK (one marker line, written first):
- Write %%% BOOK CHECK: OK when the book's solution answers the whole question and its results follow from its own working.
- Otherwise write %%% BOOK CHECK: followed by one short sentence in plain ASCII words naming the problem: a part the solution does not answer, an arithmetic or algebra slip that changes a result, a result that contradicts the solution's own working, a solution that belongs to a different question.
- Differences of rounding, of property-table edition, or of notation are not problems; do not report them.

2. TAKEAWAYS:
- {{TAKEAWAYS}}
- If the book's solution relies on a non-obvious idea, restate it and explain how someone could have thought of it.
- Two to five short points, addressed to the student. Do not retell the solution.

3. ANSWER KEY:
- Take every value from the book's solution as it states it (its final results, in its units, with its rounding). Where the book gives no explicit final value for something the question asks, compute it from the book's own working.
{{ANSWER_KEY_RULES}}

4. HINTS (write these last):
- Hints for a student who is stuck and does not want the solution spoiled, in one to three tiers. The student sees tier 1 first and asks for the next tier only if still stuck.
- Choose how many tiers the question needs: one when a single nudge is enough (a routine question), two or three when it has several steps or a hard key idea.
- Tier 1 points toward the starting idea, the governing principle, or the right method, the way the book's solution starts. Each later tier says more than the one before, following the book's method: for example, the key relation or the quantity to find first, then the plan of attack as a short outline.
- No tier does the actual work: no computed values, no intermediate results, no worked steps. No tier may reveal or strongly imply the answer, even with the other tiers: for a numerical question no value from the solution, for a multiple-choice question nothing that names or singles out an option, for a descriptive question not the list of points itself.
- One to three sentences per tier, matching the length, tone, and LaTeX style of these hints:
{{HINT_EXAMPLES}}

OUTPUT FORMAT:
Write the takeaways, the POINT lines of the answer key, and the hints in LaTeX. They are compiled into a PDF and also shown in a web view, so:
- Do NOT use any markdown: no # headings, no **bold**, no - or * bullet lists, no backticks, no code fences.
- Write only content. Do NOT write \documentclass, \usepackage, \begin{document}, or section titles; those are added separately.
- Close every \textbf{...}, \textit{...} and \emph{...} with its closing brace. Never use * or ** for emphasis.
- The very first line of your reply is the marker line %%% BOOK CHECK:, and every marker line is copied exactly as shown below.

Your entire reply is the structure below: nothing before the first marker line, nothing after the last one. The lines starting with %%% are markers; copy them exactly:

%%% BOOK CHECK: <OK, or the problem in one sentence>
%%% BEGIN TAKEAWAYS
<takeaways body in LaTeX>
%%% END TAKEAWAYS
%%% BEGIN ANSWER KEY
<answer key lines>
%%% END ANSWER KEY
%%% BEGIN HINT 1
<tier 1 hint in LaTeX>
%%% END HINT 1
%%% BEGIN HINT 2
<tier 2 hint in LaTeX>
%%% END HINT 2
%%% BEGIN HINT 3
<tier 3 hint in LaTeX>
%%% END HINT 3

Write the HINT 2 and HINT 3 blocks only for the tiers you write: a reply with one tier ends with %%% END HINT 1, one with two tiers with %%% END HINT 2.

LATEX RULES (follow exactly; the PDF compiler and the web view both depend on them):
{{FORMAT_RULES}}
