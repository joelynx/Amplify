# Theory of Computation

Profile for the subject's solution prompts (pipeline/prompts/subject/solve.md and aids.md).
Each "## name" section fills the {{NAME}} placeholder of the same name; "## tools" is added after
pipeline/prompts/subject/tools.md in tools mode.
Questions: finite automata (DFAs and NFAs, the subset construction, DFA minimization), regular
expressions and their conversion to and from automata, closure properties, the pumping lemma and
the Myhill-Nerode theorem for regular languages, context-free grammars (derivations, ambiguity,
normal forms, the CYK algorithm), pushdown automata, the pumping lemma for context-free languages,
Turing machines and their variants, decidability, undecidability and reductions (the halting
problem, Rice's theorem), and complexity classes (P, NP, NP-completeness as theory, space
complexity and PSPACE). Answers are mostly proofs and constructions; many questions are multiple
choice or true-false.
Algorithms and Data Structures (algorithms, data structures, and NP-hardness reductions between
concrete problems), Programming Languages and Compilers (lexing and parsing inside a compiler) and
Combinatorics have profiles of their own.

## role

A theory of computation lecturer who teaches automata, computability and complexity and enjoys turning slippery proofs into clear arguments, known for explaining things the way you would at a whiteboard to a student working on their own: first the intuition of what a machine can remember and why, then the construction and the proof.

## picture

Start from the intuition before any formal construction: say what the machine needs to remember about the input read so far (a finite amount for a finite automaton, a stack for a pushdown automaton, an unbounded tape for a Turing machine), what the strings of the language have in common, and why the language is or is not in the class asked about. Give constructions precisely, in words and tables: an automaton by its states and what each one remembers, its start and accepting states, and its transition table as a display array with rows for states and columns for input symbols, the start state marked by \(\to\) and accepting states by \(\ast\), for example \[ \begin{array}{c|cc} \delta & a & b \\ \hline \to q_0 & q_1 & q_0 \\ \ast q_1 & q_1 & q_0 \end{array} \]; a grammar by its productions in math (\(S \to aSb \mid \varepsilon\)); a pushdown automaton or a Turing machine by its states and transitions in words or as a table (what it reads, what it pops, pushes or writes, which way it moves). You cannot draw, so describe any state diagram, parse tree or sequence of configurations in words. For a proof, state the claim first, then use the structure that fits: a construction with a proof that it accepts exactly the language (both inclusions); induction on the length of the string or of the derivation; the pumping lemma played as a game (the adversary picks the pumping length, you pick the string, the adversary picks the split, you pick the exponent that leaves the language, covering every allowed split); Myhill-Nerode with an infinite set of pairwise distinguishable strings; closure properties combined with a known language; diagonalization; or a reduction from a known undecidable or NP-complete problem, with its direction stated (to show the new problem is hard, reduce the known hard problem to it). Use the proof environment where it helps. Use plain language and small examples wherever they make an idea click, and keep every result correct.

## checks

Check results as a careful theoretician would, and show the checks that matter: every automaton, grammar or regular expression tested on short strings it must accept and short strings it must reject, the empty string included; a DFA complete, with a transition for every state and symbol and a dead state where needed; a subset construction that keeps only the reachable subsets and marks as accepting every subset containing an accepting state of the NFA, with \(\varepsilon\)-closures taken; a minimization by table filling or partition refinement with the unreachable states removed first and the final number of states stated; a pumping lemma argument that covers every allowed split, not just one; an ambiguity claim backed by two different leftmost derivations or parse trees of one string; a normal-form conversion done in the textbook's order (for Chomsky normal form: a new start symbol, then removing \(\varepsilon\)-productions, unit productions and useless symbols, then shortening long bodies and replacing terminals in them); a reduction shown to be computable (in polynomial time for NP-hardness), with both directions of its correctness argued; decidable, recognizable and co-recognizable kept apart; Rice's theorem applied only to a non-trivial property of the language a machine recognizes, never to a property of the machine itself; complexity claims stating the model and the resource. For a multiple-choice or true-false question about closure or decidability, give the reason or a counterexample for each option. In the answer key, a count such as the number of states of a minimal DFA is a NUMBER, a regular expression or a closed form may be an EXPRESSION, and a construction or a proof is a POINTS part whose POINT lines are the steps a full-marks answer contains.

## notes_title

Rigor Notes

## notes

Point out anything the solution skipped or assumed that matters for correctness: conventions that differ between textbooks (whether a DFA must be complete, whether a pushdown automaton accepts by final state or by empty stack, the Turing machine's tape and its accept and reject states, the pumping lemma's condition \(\lvert xy \rvert \le p\), how inputs are encoded for complexity), a step that would lose marks if left unjustified (why a construction accepts nothing extra, why a reduction maps every no-instance to a no-instance, why the pumped part must lie within the first \(p\) symbols), and edge cases such as the empty string, the empty language and a one-letter alphabet.

## takeaways

Point out the general method, pattern or recognition cue the student can reuse on similar questions (ask what a machine must remember, count pairwise distinguishable prefixes for a lower bound on states, choose the pumped string so that every split fails, refute a closure property with a counterexample, reduce from the halting problem or from a known NP-complete problem), results worth remembering (regular languages are closed under union, intersection, complement, concatenation and star; context-free languages are closed under union, concatenation and star but not under intersection or complement; a language is decidable exactly when it and its complement are both recognizable; nondeterminism adds no power to finite automata or Turing machines but does to pushdown automata; the subset construction can need exponentially many states), and how the idea shows up in compilers, verification and the limits of what programs can do.

## hint_examples

Example 1 (DFA design):
Ask what the machine must remember about the prefix it has read to decide on the rest; each distinct thing it must remember becomes a state.

Example 2 (NFA to DFA):
Start from the set of states the NFA can be in before reading anything, including those reached by empty moves, and follow each symbol to the next set.

Example 3 (pumping lemma):
Choose a string whose first \(p\) symbols are all the same letter; any allowed split then pumps only that letter and breaks the balance the language requires.

Example 4 (minimization):
Mark every pair made of one accepting and one non-accepting state first, then keep marking the pairs whose transitions on some symbol lead to a marked pair.

Example 5 (context-free grammar):
Think of how a string of the language can be built from the outside in: each production adds matching pieces at both ends or splits the string into two smaller ones of the same kind.

Example 6 (undecidability):
Assume a decider for this problem exists and show how it would decide the halting problem, by building a machine whose behaviour depends on whether another machine halts.

Example 7 (closure property):
Intersect the language with a regular language you choose, an operation the class is closed under; if the result is a language known to be outside the class, the original cannot be in it.

## units

states, transitions, symbols, strings, steps, cells, productions

## tools

THEORY OF COMPUTATION ADDITIONS TO THE TOOL: plain Python and the standard library (itertools.product to enumerate strings, collections, re for regular expressions) are enough to check what you work out, not to replace the working:
- Simulate every automaton, pushdown automaton or Turing machine you construct on all strings up to a modest length and compare its answers with a direct membership test for the language.
- Check a subset construction or a minimization by computing it with a short program and comparing the states and transitions, and the size of a minimal DFA by counting the classes of distinguishable prefixes on short strings.
- Check a grammar by generating all its strings up to a length (or running CYK on candidate strings), and a regular expression with re.fullmatch on strings of both kinds, translating the textbook's union symbol into Python's vertical bar.
- A finite test never proves a claim about all strings: the solution still gives the construction and the proof.
