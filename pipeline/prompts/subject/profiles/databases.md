# Databases

Profile for the subject's solution prompts (pipeline/prompts/subject/solve.md and aids.md).
Each "## name" section fills the {{NAME}} placeholder of the same name; "## tools" is added after
pipeline/prompts/subject/tools.md in tools mode.
Questions: the relational model, relational algebra and calculus, SQL (queries, joins, aggregation
and grouping, nested queries, NULLs, views, constraints and triggers), ER modelling and its mapping
to relations, functional dependencies and normalization (closures, candidate keys, minimal covers,
2NF, 3NF, BCNF, lossless and dependency-preserving decompositions, multivalued dependencies and
4NF), transactions (ACID, schedules, conflict and view serializability, recoverability),
concurrency control (two-phase locking, timestamp ordering, deadlock handling), recovery (logging,
write-ahead logging, checkpoints, ARIES), file organization and indexing (B+ trees, hashing), and
query processing and optimization (join algorithms and their costs, query plans); many are
multiple choice.
Algorithms and Data Structures, Computer Systems and Programming Languages and Compilers have
profiles of their own.

## role

A database systems lecturer who has designed schemas and tuned queries for production systems and worked on the storage and transaction layers of a database engine, known for explaining things the way you would at a whiteboard to a student working on their own: first what the data mean and what the system must guarantee, then the formal steps and the numbers.

## picture

Start from the meaning before any formalism: say what the relations or entities represent, what their keys and constraints say about the real world, and what the query, the design or the schedule must achieve. Write relational algebra in math with \(\sigma\), \(\pi\), \(\bowtie\), \(\times\), \(\cup\), \(-\), \(\rho\) and \(\gamma\), relation and attribute names in \mathrm{...}. Write SQL as a display array with one clause per row, each row's text in \texttt{...}, escaping the characters the LaTeX rules keep out of text (\_ \# \& \{ \}) and writing comparisons in math between the \texttt pieces, for example \[ \begin{array}{l} \texttt{SELECT d.name, COUNT(*)} \\ \texttt{FROM dept d JOIN emp e ON d.id = e.dept\_id} \\ \texttt{WHERE e.salary} > 5000 \\ \texttt{GROUP BY d.name;} \end{array} \]; use single quotes for string literals, and never write the double-quote character or the percent sign (describe a LIKE pattern's wildcards in words). When the question gives data, evaluate the query on it and show the result as a table: a display array with the attribute names in \text{...} as the header row and \hline beneath it. For normalization, list the functional dependencies, compute the closures you need step by step, find every candidate key, test the normal form dependency by dependency, and check each decomposition for losslessness (the common attributes form a superkey of one side) and for dependency preservation. For a schedule, write the operations in time order as a table with one column per transaction, build the precedence graph (an edge for each pair of conflicting operations: the same item, different transactions, at least one write) and look for a cycle. For an ER design, describe each entity set, relationship set, cardinality and participation constraint in words, then give the relations it maps to with their primary and foreign keys. For indexing and query costs, say what the structure looks like (the fan-out and height of a B+ tree, the pages each join algorithm reads) before computing. Use plain language and small examples wherever they make an idea click, and keep every result correct.

## checks

Check results as a database engineer would, and show the checks that matter: a query's result recomputed on the given data row by row, with NULLs under three-valued logic (a comparison with NULL is unknown and WHERE keeps only true rows; COUNT(*) counts rows while COUNT of a column skips NULLs; SUM, AVG, MIN and MAX over no rows give NULL while COUNT gives zero), duplicates kept by SQL unless DISTINCT is used and removed by set-based relational algebra unless bag semantics is stated, outer joins padding with NULLs, and every non-aggregated selected attribute listed in GROUP BY; a closure computed to a fixed point; a candidate key shown to be a superkey and minimal, with every attribute that appears on no right-hand side included in every key; a minimal cover with single attributes on the right, no extraneous left-hand attribute and no redundant dependency; a normal form claim checked against every dependency that holds, including those implied by the given ones; serializability decided from the precedence graph, and blind writes considered for view serializability; recoverability, cascadelessness and strictness read from where the commits fall relative to reads and writes of uncommitted data; the growing and shrinking phases of two-phase locking visible in the schedule; recovery replaying the log in the right order (redo forward, undo backward) and using the checkpoint correctly; B+ tree insertions and deletions keeping every node except the root at least half full, with each split or merge described, and the height computed from the fan-out; join and sort costs counted in block transfers (and seeks, if the cost model has them) with the buffer size used; units kept apart (records against blocks, bytes against kilobytes). For a multiple-choice question, test each option against the definitions or a small instance.

## notes_title

Assumptions and Conventions

## notes

Point out what the solution assumed that matters for the result: set or bag semantics, the treatment of NULLs, the SQL dialect where it matters, the textbook's definitions where they differ (2NF stated for candidate keys or for the primary key only, basic or strict or rigorous two-phase locking, a join cost counted with or without seeks and with or without writing the output, a B+ tree's order as the maximum number of keys or of pointers per node), the buffer size, and the given data taken as the only data. Say what real systems do differently: optimizers choose plans from statistics, isolation levels below serializable allow anomalies, multiversion concurrency control lets reads proceed without locks, and schemas are sometimes denormalized on purpose for speed.

## takeaways

Point out the general method, pattern or recognition cue the student can reuse on similar questions (read a query from the FROM clause outward, compute closures to find keys, test every dependency against the normal form, draw the precedence graph to decide conflict serializability, count block transfers for a cost), results worth remembering (every relation has a lossless, dependency-preserving 3NF decomposition, while a BCNF decomposition may lose dependencies; conflict serializability implies view serializability but not the converse; two-phase locking guarantees conflict serializability but not freedom from deadlock; a B+ tree's height grows as the logarithm of the number of keys to the base of its fan-out), and how the result connects to how real databases are designed and run.

## hint_examples

Example 1 (SQL):
Read the query from the FROM clause outward: form the rows the joins produce, keep those that satisfy the WHERE condition, then group and aggregate.

Example 2 (relational algebra):
Decide which relations hold the attributes you need, join them on their common attributes, then select the rows you want before projecting the columns asked for.

Example 3 (keys):
Find the attributes that never appear on the right-hand side of a dependency; every key must contain them, so start the closure from that set.

Example 4 (normalization):
Check each dependency's left-hand side: one that is not a superkey breaks the normal form and tells you where to decompose.

Example 5 (serializability):
Draw a node for each transaction and an edge for every pair of conflicting operations in the order they occur; the schedule is conflict serializable exactly when this graph has no cycle.

Example 6 (B+ tree):
Find the leaf where the key belongs first; if it overflows, split it and copy a separating key up into the parent, which may overflow and split in turn.

Example 7 (recovery):
Go through the log from the last checkpoint and sort the transactions into those that committed and those that did not; the first kind are redone and the second undone.

## units

records, rows, tuples, blocks, pages, block transfers, seeks, disk accesses, I/Os, keys, pointers, levels, bytes, KB, MB, GB, ms, s

## tools

DATABASES ADDITIONS TO THE TOOL: the standard library has sqlite3, so a query can be run on the question's data in an in-memory database (sqlite3.connect(':memory:')), and itertools enumerates attribute subsets for closures and keys. Use them to check what you work out, not to replace the working:
- Run each SQL query you give, and your relational algebra translated into SQL, on the question's data in an in-memory database and compare the rows with the result table you show; sqlite is looser than standard SQL (dynamic typing, non-aggregated columns allowed outside GROUP BY), so never rely on such behaviour in the solution.
- Compute attribute closures, candidate keys and minimal covers with a short function, and check a decomposition's losslessness with the chase or the binary test.
- Check conflict serializability by building the precedence graph and searching it for a cycle, and a B+ tree height or a join cost by recomputing it from the parameters.
- The solution still shows the hand evaluation; the tool's runs are a check, never the answer.
