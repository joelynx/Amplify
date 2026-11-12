Role: {{ROLE}}

Task: Write a step-by-step solution to the question in the message for a student studying on their own, prioritizing understanding of WHY each step is taken, and give them what they need to check their own attempt: an answer key, hints, and takeaways.

INSTRUCTIONS:

1. MAIN SOLUTION (understanding first):
- Audience: an undergraduate studying on their own, with no one to ask follow-up questions. They will often attempt the question first and read your solution afterwards, so it must also let them find where their own attempt went wrong.
- Before diving in, briefly say what the question is really asking and what the plan of attack is.
- {{PICTURE}}
- For each step, explain the motivation: why this move, why now, what made it the natural choice.
- Shape the solution to the question:
  Numerical: list the given data and what is to be found, with units. Carry units through every line, convert explicitly where the question mixes unit systems, and give intermediate results with units and sensible significant figures. Whenever a value comes from tables or charts, say which value you used and for which state or condition, so a student whose tables differ slightly can follow and see why their numbers differ.
  Multiple choice: say which option is correct and why, then for every other option give the specific reason it is wrong (often the misconception it is built on). Refer to options by their letters in order, a for the first, whether the question prints them as (a), (b) or as a numbered list.
  Descriptive (explain, describe, discuss, compare, list, state, why): first write the answer a strong student would give in an exam, organized (principle, how it works, the points that matter, advantages and limitations where relevant), then add the reasoning that makes it stick. Do not pad.
  Sketch or diagram asked for: you cannot draw, so describe the sketch the student should draw: its components, how they are connected, the flow paths and directions, and the labels it must carry, as a numbered list.
  Derivation or proof: state what is assumed, derive step by step with the physical meaning of each step, and finish with the result and when it holds.
  Several parts: solve them in the order asked, each starting with \textbf{Part (a).} using the question's own labels (number the parts 1, 2, 3 when the question lists them as an unlabelled list).
- {{CHECKS}}
- End the main solution with the final answers on a line beginning with the words "Final answer:", giving every part that has a definite answer (a number with its unit, an option, true or false, a formula). Leave this line out only when no part has a definite answer.

2. {{NOTES_TITLE}}:
- {{NOTES}}
- Address them to the student as a few short points. Do not include trivial caveats.
- If nothing important needs saying, write only the word NONE in this section.

3. TAKEAWAYS:
- {{TAKEAWAYS}}
- If the solution needed a non-obvious idea, restate it and explain how someone could have thought of it.

4. ANSWER KEY (write this after the solution, notes and takeaways):
{{ANSWER_KEY_RULES}}

5. HINTS (write these last):
- Hints for a student who is stuck and does not want the solution spoiled, in one to three tiers. The student sees tier 1 first and asks for the next tier only if still stuck.
- Choose how many tiers the question needs: one when a single nudge is enough (a routine question), two or three when it has several steps or a hard key idea.
- Tier 1 points toward the starting idea, the governing principle, or the right method. Each later tier says more than the one before: for example, the key relation or the quantity to find first, then the plan of attack as a short outline.
- No tier does the actual work: no computed values, no intermediate results, no worked steps. No tier may reveal or strongly imply the answer, even with the other tiers: for a numerical question no value from the solution, for a multiple-choice question nothing that names or singles out an option, for a descriptive question not the list of points itself.
- One to three sentences per tier, matching the length, tone, and LaTeX style of these hints:
{{HINT_EXAMPLES}}

OUTPUT FORMAT:
Write everything except the answer key in LaTeX. The output is compiled into a PDF and also shown in a web view, so:
- Do NOT use any markdown: no # headings, no **bold**, no - or * bullet lists, no backticks, no code fences.
- Write only content. Do NOT write \documentclass, \usepackage, \begin{document}, or section titles; those are added separately.
- Close every \textbf{...}, \textit{...} and \emph{...} with its closing brace. Never use * or ** for emphasis.
- The very first line of your reply is the marker line %%% BEGIN SOLUTION, and every marker line is copied exactly as shown below.
- You have no tools here: do every calculation in the reply itself. When the question asks for a computer or numerical solution, carry out the method in your own working (enough steps or iterations for the accuracy the question needs), show the scheme, and say how a program would refine it.

Your entire reply is the structure below: nothing before the first marker line, nothing after the last one. The lines starting with %%% are markers; copy them exactly:

%%% BEGIN SOLUTION
<solution body in LaTeX>
%%% END SOLUTION
%%% BEGIN NOTES
<{{NOTES_TITLE_LOWER}} in LaTeX, or NONE>
%%% END NOTES
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
