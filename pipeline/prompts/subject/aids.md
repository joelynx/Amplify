Role: {{ROLE}}

Task: The message gives a question and the textbook's own worked solution to it. The book's solution stays exactly as it is; it is what the student will read. Your job is to add what a student studying on their own needs around it: an answer key so they can check their own attempt, a hint for when they are stuck, and takeaways. Read the question and the book's solution carefully and base everything on them.

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

4. HINT (write this last):
- A hint for a student who is stuck and does not want the solution spoiled: point toward the starting idea, the governing principle, or the right method, the way the book's solution starts.
- The hint does none of the actual work: no computed values, no intermediate results, no step-by-step outline. It must not reveal or strongly imply the answer: for a numerical question no value from the solution, for a multiple-choice question nothing that names or singles out an option, for a descriptive question not the list of points itself.
- One to three sentences, matching the length, tone, and LaTeX style of these hints:
{{HINT_EXAMPLES}}

OUTPUT FORMAT:
Write the takeaways, the POINT lines of the answer key, and the hint in LaTeX. They are compiled into a PDF and also shown in a web view, so:
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
%%% BEGIN HINT
<hint in LaTeX>
%%% END HINT

LATEX RULES (follow exactly; the PDF compiler and the web view both depend on them):
{{FORMAT_RULES}}
