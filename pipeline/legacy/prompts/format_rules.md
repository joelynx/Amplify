1. Write LaTeX body content only. Never write \documentclass, \usepackage, \begin{document}, \end{document}, \newcommand, \renewcommand, \def, \DeclareMathOperator, \input, or \include.

2. No markdown of any kind: no # headings, no **bold** or *italics*, no lines starting with - or * as bullets, no backticks, no tables drawn with | characters, no horizontal rules.

3. Math delimiters: inline math is \( ... \) and display math is \[ ... \]. Do not use $ or $$. Close every delimiter you open.

4. Multi-line display math: write \[ \begin{aligned} ... \end{aligned} \] with & for alignment points and \\ for new lines. (\begin{align*} ... \end{align*} on its own, NOT inside \[ \], is also acceptable.) Never nest align* inside \[ \].

5. Allowed environments, and no others: aligned, align*, gathered, gather*, cases, pmatrix, bmatrix, vmatrix, matrix, smallmatrix, array, split (math); itemize and enumerate with \item (text); proof, claim, lemma (text). In particular do NOT use tabular, table, figure, center, minipage, tikzpicture, verbatim, lstlisting, theorem, equation, or quote.

6. Text structure: separate paragraphs with one blank line. Use \textbf{...} for short run-in labels such as \textbf{Step 1.} or \textbf{Why this works.} and \textit{...} or \emph{...} for emphasis. Do NOT use \section, \subsection, \paragraph, \chapter, \title, \maketitle. Do NOT use \\, \newline, \linebreak, \par, \noindent, \vspace, \hspace, \hfill, \centering, \smallskip, \medskip, \bigskip, \newpage, or \clearpage in text.

7. No comments. Never write a % character except in the marker lines that begin with %%%. In text write the word "percent".

8. Special characters in text mode: do not write %, &, #, _, ^, ~, $, {, }, \, <, or > as plain text. Put symbols, variable names, and subscripts in math mode (write \(x_1\), never x_1 in text) and spell out words (percent, and, number). Inside math mode, \{ and \} give braces and \lt \gt are not needed (use < and > inside math only).

9. ASCII only. No Unicode characters at all: no curly quotes, no en or em dashes, no Greek letters, no symbols such as the less-than-or-equal, arrow, times, or middle-dot characters, no accented letters. Inside math use \le \ge \ne \to \times \cdot \pi \alpha and so on. In text use - hyphens. Do not use quotation marks of any kind (the " character renders as a closing quote in the PDF): to mention a word or phrase, write it with \emph{...} instead, for example \emph{shift and add}.

10. Allowed macros (these work in both the PDF and the web view):
    Operators and layout: \frac \dfrac \tfrac \sqrt \binom \sum \prod \int \iint \iiint \oint \lim \limsup \liminf \sup \inf \max \min \gcd \lcm \log \ln \exp \sin \cos \tan \sec \csc \cot \arcsin \arccos \arctan \sinh \cosh \tanh \det \dim \ker \deg \Pr \left \right \big \Big \bigl \bigr \Bigl \Bigr \cdots \ldots \vdots \ddots \quad \qquad \, \; \! \operatorname{...} \text{...} \textbf{...} (inside math too) \mathbb \mathbf \mathrm \mathcal \mathfrak \boldsymbol \overline \underline \hat \tilde \bar \vec \dot \ddot \widehat \widetilde \overbrace \underbrace \overset \underset \stackrel \substack \boxed \tag \pmod \bmod \lfloor \rfloor \lceil \rceil \lvert \rvert \langle \rangle \not
    Relations and symbols: \equiv \mid \nmid \in \notin \subset \subseteq \supset \supseteq \cup \cap \setminus \bigcup \bigcap \times \cdot \circ \pm \mp \le \ge \ne \neq \leq \geq \ll \gg \approx \sim \simeq \cong \propto \infty \partial \nabla \emptyset \varnothing \to \mapsto \rightarrow \leftarrow \Rightarrow \Leftarrow \Leftrightarrow \implies \iff \longrightarrow \xrightarrow{...} \forall \exists \neg \land \lor \therefore \because \prime \angle \triangle \perp \parallel \ell \hbar \Re \Im
    Greek: \alpha \beta \gamma \delta \epsilon \varepsilon \zeta \eta \theta \vartheta \iota \kappa \lambda \mu \nu \xi \pi \rho \sigma \tau \upsilon \phi \varphi \chi \psi \omega \Gamma \Delta \Theta \Lambda \Xi \Pi \Sigma \Upsilon \Phi \Psi \Omega
    NOT allowed: \mathscr \mathbbm \degree \textdegree \SI \num \si \color \textcolor \url \href \footnote \cite \label \ref \eqref \includegraphics \caption \setcounter \item outside a list.

11. Images: never include images. If the question refers to a figure, describe in words whatever you use from it.

12. Keep every \begin{...} matched by \end{...}, every \( by \), every \[ by \], and every { by }. The output is rejected automatically if anything is unbalanced.

13. Double backslashes must survive saving. A row separator in aligned, cases, or a matrix is two backslash characters. If you save the file through a tool whose arguments are JSON strings, each of those two backslashes must be escaped (four backslashes in the JSON) so that the file on disk contains exactly two. Inside those environments a lone backslash followed by a space or a newline is a lost row separator and the output is rejected. After saving, read the file back once and confirm every row separator is still a double backslash; fix and re-save if not.
