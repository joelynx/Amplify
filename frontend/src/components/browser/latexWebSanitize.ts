/**
 * Web-only LaTeX sanitizer for the KaTeX view.
 *
 * Stored question and solution texts are written for XeLaTeX. The web view
 * (LatexContent.tsx) understands math and a handful of text commands, so
 * everything else (figure/table scaffolding, spacing, sectioning, tabular,
 * TikZ, text symbols, escaped characters, bare brace groups) used to show up
 * as raw `\commands` and stray braces. This pass rewrites those constructs
 * into plain text or sentinel-marked HTML at render time only: the stored
 * LaTeX is never modified, so the PDF path is unaffected.
 *
 * Math segments ($…$, $$…$$, \(…\), \[…\]) are handed to KaTeX untouched
 * except for a few commands KaTeX lacks (`fixMath`). The segmenting mirrors
 * the chunker in LatexContent.tsx so both agree on what is math.
 */

// --- Sentinels shared with LatexContent.tsx ------------------------------
export const STRONG_OPEN = "@@AMP_STRONG_OPEN@@";
export const STRONG_CLOSE = "@@AMP_STRONG_CLOSE@@";
export const EM_OPEN = "@@AMP_EM_OPEN@@";
export const EM_CLOSE = "@@AMP_EM_CLOSE@@";
export const U_OPEN = "@@AMP_U_OPEN@@";
export const U_CLOSE = "@@AMP_U_CLOSE@@";
export const TT_OPEN = "@@AMP_TT_OPEN@@";
export const TT_CLOSE = "@@AMP_TT_CLOSE@@";

// --- Sentinels owned by this module --------------------------------------
const SUB_OPEN = "@@AMP_SUB_OPEN@@";
const SUB_CLOSE = "@@AMP_SUB_CLOSE@@";
const SUP_OPEN = "@@AMP_SUP_OPEN@@";
const SUP_CLOSE = "@@AMP_SUP_CLOSE@@";
const HEAD_OPEN = "@@AMP_HEAD_OPEN@@";
const HEAD_CLOSE = "@@AMP_HEAD_CLOSE@@";
const CAPTION_OPEN = "@@AMP_CAPTION_OPEN@@";
const CAPTION_CLOSE = "@@AMP_CAPTION_CLOSE@@";
const FOOT_OPEN = "@@AMP_FOOT_OPEN@@";
const FOOT_CLOSE = "@@AMP_FOOT_CLOSE@@";
const CENTER_OPEN = "@@AMP_CENTER_OPEN@@";
const CENTER_CLOSE = "@@AMP_CENTER_CLOSE@@";
const PRE_OPEN = "@@AMP_PRE_OPEN@@";
const PRE_CLOSE = "@@AMP_PRE_CLOSE@@";
const TABLE_OPEN = "@@AMP_TABLE_OPEN@@";
const TABLE_CLOSE = "@@AMP_TABLE_CLOSE@@";
const TR_OPEN = "@@AMP_TR_OPEN@@";
const TR_CLOSE = "@@AMP_TR_CLOSE@@";
const TD_OPEN = "@@AMP_TD_OPEN@@";
const TD_CLOSE = "@@AMP_TD_CLOSE@@";
const TDC_OPEN = "@@AMP_TDC_OPEN@@"; // followed by the colspan digits and TDC_DELIM
const TDC_DELIM = "@@AMP_TDC_DELIM@@";
const DIAGRAM = "@@AMP_DIAGRAM@@";
const HR = "@@AMP_HR@@";
// Characters that the chunker or the HTML would otherwise misread.
const DOLLAR = "@@AMP_DOLLAR@@";
const LBRACE = "@@AMP_LBRACE@@";
const RBRACE = "@@AMP_RBRACE@@";
const BACKSLASH = "@@AMP_BACKSLASH@@";

const TD_CLASS = "border border-border px-2 py-1 align-top";

/** Replace this module's sentinels in the final HTML (LatexContent calls it
 * before its own sentinel pass and the catch-all nuke). */
export function postprocessWebSentinels(html: string): string {
  let s = html.replace(
    new RegExp(`${reEscape(TDC_OPEN)}(\\d+)${reEscape(TDC_DELIM)}`, "g"),
    (_m, n: string) => `<td colspan="${n}" class="${TD_CLASS}">`,
  );
  const map: [string, string][] = [
    [SUB_OPEN, "<sub>"],
    [SUB_CLOSE, "</sub>"],
    [SUP_OPEN, "<sup>"],
    [SUP_CLOSE, "</sup>"],
    [HEAD_OPEN, `<div class="mt-3 mb-1 font-semibold text-text">`],
    [HEAD_CLOSE, "</div>"],
    [CAPTION_OPEN, `<div class="my-1 text-xs italic text-muted">`],
    [CAPTION_CLOSE, "</div>"],
    [FOOT_OPEN, `<span class="text-xs text-muted">[`],
    [FOOT_CLOSE, "]</span>"],
    [CENTER_OPEN, `<div class="my-1 text-center">`],
    [CENTER_CLOSE, "</div>"],
    [PRE_OPEN, `<pre class="my-2 overflow-x-auto rounded bg-surface p-2 text-xs">`],
    [PRE_CLOSE, "</pre>"],
    [TABLE_OPEN, `<table class="my-2 border-collapse text-sm">`],
    [TABLE_CLOSE, "</table>"],
    [TR_OPEN, "<tr>"],
    [TR_CLOSE, "</tr>"],
    [TD_OPEN, `<td class="${TD_CLASS}">`],
    [TD_CLOSE, "</td>"],
    [DIAGRAM, `<div class="my-1 text-xs text-muted">[figure drawn in LaTeX: open the PDF view to see it]</div>`],
    [HR, `<hr class="my-2 border-border"/>`],
    [DOLLAR, "&#36;"],
    [LBRACE, "&#123;"],
    [RBRACE, "&#125;"],
    [BACKSLASH, "&#92;"],
  ];
  for (const [k, v] of map) s = s.split(k).join(v);
  return s;
}

function reEscape(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

// --- Tables ----------------------------------------------------------------

const words = (s: string): Set<string> => new Set(s.split(/\s+/).filter(Boolean));

/** Commands that only make sense in math mode; a leftover in prose is wrapped
 * in `$…$` together with its attached arguments and scripts. */
const MATH_CMDS = words(`
  alpha beta gamma delta epsilon varepsilon zeta eta theta vartheta iota kappa lambda mu nu xi pi varpi
  rho varrho sigma varsigma tau upsilon phi varphi chi psi omega Gamma Delta Theta Lambda Xi Pi Sigma
  Upsilon Phi Psi Omega
  frac dfrac tfrac cfrac binom dbinom tbinom sqrt
  cdot cdots vdots ddots dotsb dotsc dotsm dotsi times div pm mp ast star circ bullet oplus ominus otimes
  oslash odot bigcirc dagger ddagger amalg wedge vee cap cup sqcap sqcup uplus setminus wr diamond
  triangleleft triangleright lhd rhd unlhd unrhd
  leq le geq ge neq ne equiv sim simeq approx cong propto ll gg prec succ preceq succeq subset supset
  subseteq supseteq subsetneq supsetneq nsubseteq sqsubseteq sqsupseteq in ni notin mid nmid parallel perp
  vdash dashv models bowtie asymp doteq lesssim gtrsim leqslant geqslant
  infty partial nabla forall exists nexists neg lnot land lor emptyset varnothing aleph hbar ell Re Im wp
  imath jmath prime top bot angle measuredangle sphericalangle triangle square Box Diamond blacksquare
  clubsuit diamondsuit heartsuit spadesuit flat natural sharp surd therefore because
  sum prod coprod int iint iiint oint bigcup bigcap bigvee bigwedge bigoplus bigotimes bigsqcup
  lim limsup liminf varlimsup varliminf max min sup inf det gcd lcm deg dim ker hom arg Pr exp log ln lg
  sin cos tan cot sec csc arcsin arccos arctan sinh cosh tanh coth
  to rightarrow leftarrow Rightarrow Leftarrow leftrightarrow Leftrightarrow longrightarrow longleftarrow
  Longrightarrow Longleftarrow longleftrightarrow Longleftrightarrow mapsto longmapsto uparrow downarrow
  updownarrow Uparrow Downarrow nearrow searrow swarrow nwarrow hookrightarrow hookleftarrow implies
  impliedby iff xrightarrow xleftarrow rightleftharpoons leftharpoonup rightharpoonup
  mathbb mathcal mathfrak mathscr mathbf mathsf mathtt boldsymbol bm operatorname overline overrightarrow
  overleftarrow underbrace overbrace underset overset stackrel vec hat bar tilde dot ddot widehat widetilde
  check breve acute grave mathring
  left right bigl bigr Bigl Bigr biggl biggr Biggl Biggr big Big bigg Bigg langle rangle lfloor rfloor
  lceil rceil vert Vert lvert rvert lVert rVert
  pmod bmod mod choose not displaystyle textstyle scriptstyle scriptscriptstyle limits nolimits substack
  boxed cancel bcancel xcancel circledast circledcirc
`);

/** Text-mode symbols and their Unicode rendering. */
const SYMBOLS = new Map<string, string>(
  Object.entries({
    AA: "Å",
    aa: "å",
    qed: "∎",
    textbackslash: BACKSLASH,
    textasciitilde: "~",
    textasciicircum: "^",
    ldots: "…",
    dots: "…",
    textellipsis: "…",
    textdegree: "°",
    degree: "°",
    textquoteleft: "‘",
    textquoteright: "’",
    textquotedblleft: "“",
    textquotedblright: "”",
    textendash: "–",
    textemdash: "—",
    LaTeX: "LaTeX",
    LaTeXe: "LaTeX2e",
    TeX: "TeX",
    textregistered: "®",
    copyright: "©",
    texttrademark: "™",
    S: "§",
    P: "¶",
    pounds: "£",
    euro: "€",
    textbullet: "•",
    textperiodcentered: "·",
    textpm: "±",
    texttimes: "×",
    textdiv: "÷",
    textmu: "µ",
    textonehalf: "½",
    textonequarter: "¼",
    textthreequarters: "¾",
    textgreater: ">",
    textless: "<",
    textbar: "|",
    textbraceleft: LBRACE,
    textbraceright: RBRACE,
    textunderscore: "_",
    textdollar: DOLLAR,
    textsection: "§",
    textparagraph: "¶",
    dag: "†",
    ddag: "‡",
    i: "ı",
    j: "ȷ",
    ss: "ß",
    ae: "æ",
    AE: "Æ",
    oe: "œ",
    OE: "Œ",
    o: "ø",
    O: "Ø",
    l: "ł",
    L: "Ł",
    checkmark: "✓",
    textasteriskcentered: "∗",
    textexclamdown: "¡",
    textquestiondown: "¿",
    textvisiblespace: "␣",
    slash: "/",
    celsius: "°C",
    textcelsius: "°C",
    micro: "µ",
    percent: "%",
    ohm: "Ω",
    textohm: "Ω",
    quad: " ",
    qquad: "  ",
    enspace: " ",
    enskip: " ",
    thinspace: " ",
    negthinspace: "",
    hfilneg: "",
  }),
);

/** Commands without arguments that produce nothing on the web. */
const DROP0 = words(`
  centering raggedright raggedleft justifying sloppy fussy relax protect ignorespaces strut null indent
  noindent hfil hfill vfil vfill tightlist frenchspacing nonfrenchspacing allowbreak samepage unskip
  leavevmode selectfont normalsize small footnotesize scriptsize tiny large Large LARGE huge Huge bfseries
  mdseries itshape upshape slshape scshape rmfamily sffamily ttfamily normalfont bf it em sc tt sl rm sf
  textwidth linewidth columnwidth textheight baselineskip parindent parskip the today maketitle
  tableofcontents listoffigures listoftables appendix begingroup endgroup makeatletter makeatother qedhere
  hrulefill dotfill hline displaybreak onehalfspacing doublespacing singlespacing noalign hrule vrule
  bigskipamount medskipamount smallskipamount fill hss vss endinput
`);

/** Commands dropped together with a following optional [..] argument. */
const DROP_OPT = words("nopagebreak nolinebreak footnotemark toprule midrule bottomrule setlist hdashline");

/** Commands that become a line break (an optional [..] argument is dropped). */
const BREAKS = words("newline linebreak break clearpage newpage pagebreak cleardoublepage smallbreak medbreak bigbreak");

/** Commands dropped together with their arguments. Pattern letters: o = optional [..], a = {..}. */
const DROP_ARGS = new Map<string, string>(
  Object.entries({
    captionsetup: "oa",
    setcounter: "aa",
    addtocounter: "aa",
    stepcounter: "a",
    refstepcounter: "a",
    newcounter: "ao",
    setlength: "aa",
    addtolength: "aa",
    settowidth: "aa",
    newlength: "a",
    label: "a",
    index: "a",
    phantom: "a",
    hphantom: "a",
    vphantom: "a",
    usepackage: "oa",
    documentclass: "oa",
    pagestyle: "a",
    thispagestyle: "a",
    pagenumbering: "a",
    color: "oa",
    fontsize: "aa",
    fontfamily: "a",
    fontseries: "a",
    fontshape: "a",
    linespread: "a",
    setstretch: "a",
    bibliography: "a",
    bibliographystyle: "a",
    nocite: "a",
    bibitem: "oa",
    cline: "a",
    cmidrule: "a",
    rowcolor: "oa",
    cellcolor: "oa",
    arrayrulecolor: "a",
    title: "a",
    author: "a",
    date: "a",
    includegraphics: "oa",
    graphicspath: "a",
    newtheorem: "aoao",
    theoremstyle: "a",
    numberwithin: "aa",
    DeclareMathOperator: "aa",
    newcolumntype: "aoa",
    definecolor: "aaa",
    hypersetup: "a",
    geometry: "a",
    setmainfont: "oa",
    setmathfont: "oa",
    lhead: "a",
    rhead: "a",
    chead: "a",
    lfoot: "a",
    rfoot: "a",
    cfoot: "a",
    markboth: "aa",
    markright: "a",
    marginpar: "oa",
    hyphenation: "a",
    input: "a",
    include: "a",
    value: "a",
    roman: "a",
    Roman: "a",
    alph: "a",
    Alph: "a",
    arabic: "a",
    hangindent: "",
    hangafter: "",
    captionof: "aoa",
    vspace: "a",
    addvspace: "a",
    hspace: "a",
  }),
);

interface Keep {
  pat: string;
  /** Build the output from the raw arguments (null = missing). */
  render: (args: (string | null)[]) => string;
  /** Block-level output: also swallow the newline that follows the command. */
  block?: boolean;
  /** Swallow the spaces that follow the command (run-in headings). */
  trim?: boolean;
}

function keepLast(pat: string, open = "", close = "", block = false, trim = false): Keep {
  return {
    pat,
    block,
    trim,
    render: (a) => {
      const x = a[pat.length - 1];
      return x === null || x === undefined ? "" : open + walk(x) + close;
    },
  };
}

const unwrap = keepLast("a");
const emph = keepLast("a", EM_OPEN, EM_CLOSE);
const citeLike: Keep = { pat: "ooa", render: (a) => (a[2] == null ? "" : `[${protect(a[2].trim())}]`) };
const refLike: Keep = { pat: "oa", render: (a) => (a[1] == null ? "" : `[${protect(a[1].trim())}]`) };
const urlLike: Keep = { pat: "a", render: (a) => (a[0] == null ? "" : TT_OPEN + protect(a[0].trim()) + TT_CLOSE) };
const heading = keepLast("oa", HEAD_OPEN, HEAD_CLOSE, true);
const runIn = keepLast("oa", "\n" + STRONG_OPEN, STRONG_CLOSE + " ", true, true);

/** Commands that keep (part of) their argument. */
const KEEP = new Map<string, Keep>(
  Object.entries({
    textrm: unwrap,
    textsf: unwrap,
    textnormal: unwrap,
    textsc: unwrap,
    textup: unwrap,
    textmd: unwrap,
    text: unwrap,
    mbox: unwrap,
    mathrm: unwrap,
    hbox: unwrap,
    fbox: unwrap,
    uppercase: unwrap,
    MakeUppercase: unwrap,
    lowercase: unwrap,
    MakeLowercase: unwrap,
    textcircled: unwrap,
    emph,
    textit: emph,
    textsl: emph,
    mathit: emph,
    textbf: keepLast("a", STRONG_OPEN, STRONG_CLOSE),
    underline: keepLast("a", U_OPEN, U_CLOSE),
    texttt: keepLast("a", TT_OPEN, TT_CLOSE),
    textsubscript: keepLast("a", SUB_OPEN, SUB_CLOSE),
    textsuperscript: keepLast("a", SUP_OPEN, SUP_CLOSE),
    framebox: keepLast("ooa"),
    makebox: keepLast("ooa"),
    parbox: keepLast("oooaa"),
    raisebox: keepLast("aooa"),
    textcolor: keepLast("oaa"),
    colorbox: keepLast("oaa"),
    fcolorbox: keepLast("oaaa"),
    multicolumn: keepLast("aaa"),
    multirow: keepLast("oaoaoa"),
    centerline: keepLast("a", CENTER_OPEN, CENTER_CLOSE, true),
    caption: keepLast("oa", CAPTION_OPEN, CAPTION_CLOSE, true),
    footnote: keepLast("oa", " " + FOOT_OPEN, FOOT_CLOSE),
    footnotetext: keepLast("oa", "\n" + FOOT_OPEN, FOOT_CLOSE, true),
    section: heading,
    subsection: heading,
    subsubsection: heading,
    chapter: heading,
    part: heading,
    paragraph: runIn,
    subparagraph: runIn,
    ensuremath: { pat: "a", render: (a) => (a[0] == null ? "" : `$${fixMath(a[0])}$`) },
    url: urlLike,
    path: urlLike,
    nolinkurl: urlLike,
    href: {
      pat: "aa",
      render: (a) => (a[1] == null ? "" : `${walk(a[1])} [${TT_OPEN}${protect((a[0] ?? "").trim())}${TT_CLOSE}]`),
    },
    hyperref: keepLast("oa"),
    ref: refLike,
    eqref: refLike,
    pageref: refLike,
    autoref: refLike,
    cref: refLike,
    Cref: refLike,
    nameref: refLike,
    cite: citeLike,
    citep: citeLike,
    citet: citeLike,
    citeauthor: citeLike,
    citeyear: citeLike,
    citealp: citeLike,
    rule: {
      pat: "oaa",
      render: (a) => (/width|\\(?:textwidth|linewidth|columnwidth|hsize)/.test(a[1] ?? "") ? HR : ""),
    },
    chemfig: { pat: "a", render: () => DIAGRAM },
    tikz: { pat: "oa", render: () => DIAGRAM },
  }),
);

/** `{\bf …}`-style groups: font switch right after the brace. */
const SWITCHES = new Map<string, [string, string]>([
  ["bf", [STRONG_OPEN, STRONG_CLOSE]],
  ["bfseries", [STRONG_OPEN, STRONG_CLOSE]],
  ["em", [EM_OPEN, EM_CLOSE]],
  ["it", [EM_OPEN, EM_CLOSE]],
  ["itshape", [EM_OPEN, EM_CLOSE]],
  ["sl", [EM_OPEN, EM_CLOSE]],
  ["slshape", [EM_OPEN, EM_CLOSE]],
  ["tt", [TT_OPEN, TT_CLOSE]],
  ["ttfamily", [TT_OPEN, TT_CLOSE]],
  ["centering", [CENTER_OPEN, CENTER_CLOSE]],
  ...[
    "sc", "scshape", "rm", "rmfamily", "sf", "sffamily", "mdseries", "upshape", "normalfont", "small",
    "footnotesize", "scriptsize", "tiny", "large", "Large", "LARGE", "huge", "Huge", "normalsize",
    "raggedright", "raggedleft",
  ].map((k): [string, [string, string]] => [k, ["", ""]]),
]);

const STARRED = words("section subsection subsubsection paragraph subparagraph chapter part vspace hspace caption newcommand renewcommand providecommand");

const CHAR_ESCAPES = new Map<string, string>([
  ["$", DOLLAR],
  ["%", "%"],
  ["&", "&"],
  ["_", "_"],
  ["#", "#"],
  ["{", LBRACE],
  ["}", RBRACE],
  [" ", " "],
  ["\n", " "],
  ["\t", " "],
  [",", " "],
  [";", " "],
  [":", " "],
  ["!", ""],
  [">", " "],
  ["-", ""],
  ["/", ""],
  ["@", ""],
  ["*", ""],
  ["|", "|"],
]);

/** Accent control symbols → combining character. */
const ACCENTS = new Map<string, string>([
  ["'", "́"],
  ["`", "̀"],
  ["^", "̂"],
  ['"', "̈"],
  ["~", "̃"],
  ["=", "̄"],
  [".", "̇"],
]);
/** Letter-named accents (only when followed by a brace group). */
const LETTER_ACCENTS = new Map<string, string>([
  ["c", "̧"],
  ["v", "̌"],
  ["u", "̆"],
  ["H", "̋"],
  ["k", "̨"],
  ["r", "̊"],
  ["d", "̣"],
  ["b", "̱"],
]);

const TABULAR_ENVS = words("tabular tabularx longtable tabulary supertabular xtabular");
const DIAGRAM_ENVS = words("tikzpicture circuitikz pgfpicture picture pspicture asy tikzcd forest axis");
const VERBATIM_ENVS = words("verbatim Verbatim lstlisting minted alltt BVerbatim LVerbatim");
const MATH_ONLY_ENVS = words(`
  array cases dcases rcases matrix pmatrix bmatrix Bmatrix vmatrix Vmatrix smallmatrix aligned gathered
  split alignat alignedat flalign eqnarray displaymath math subequations CD equation align gather multline
`);
/** Brace arguments that follow `\begin{env}` (after an optional [..]). */
const ENV_ARGS = new Map<string, number>(
  Object.entries({
    minipage: 1,
    wrapfigure: 2,
    wraptable: 2,
    subfigure: 1,
    subtable: 1,
    adjustbox: 1,
    multicols: 1,
    spacing: 1,
    list: 2,
    adjustwidth: 2,
    changemargin: 2,
    lrbox: 1,
    boxedminipage: 1,
    tcolorbox: 0,
  }),
);

const SPECIAL = new Set(["$", "\\", "{", "}", "~", "%"]);

/** `\\[2mm]`-style length argument after a line break. */
const BREAK_LEN_RE = /^[ \t]*\[\s*-?(?:[\d.]+\s*(?:pt|em|ex|cm|mm|in|pc|bp|dd|cc|sp|mu|px)|\\[A-Za-z]+)\s*\]/;
const LENGTH_RE = /^\s*-?(?:[\d.]+\s*(?:pt|em|ex|cm|mm|in|pc|bp|dd|cc|sp|mu|px|fil+)|\\[A-Za-z]+)(?:\s+plus\s+\S+)?(?:\s+minus\s+\S+)?/;
/** Display math that wraps nothing but a tabular: drop the math delimiters. */
const DISPLAY_TABULAR_RE =
  /(\\\[|\$\$)\s*(\\begin\{(tabular\*?|tabularx|longtable)\}[\s\S]*?\\end\{\3\})\s*(\\\]|\$\$)/g;
/** Inline math whose whole content is display math (`$ \[ … \] $`) or a
 * display-only environment (`$\begin{align*}…\end{align*}$`): both are
 * errors for KaTeX in inline mode, so the segment is promoted to display. */
const INLINE_DISPLAY_RE = /^\s*\\\[([\s\S]*)\\\]\s*$/;
const INLINE_ENV_RE = /^\s*\\begin\{(align|gather|equation|alignat|flalign|multline|eqnarray)\*?\}[\s\S]*\\end\{\1\*?\}\s*$/;

function inlineSegment(inner: string, open: string, close: string): string {
  const dm = INLINE_DISPLAY_RE.exec(inner);
  if (dm) return `\\[${fixMath(dm[1], true)}\\]`;
  if (INLINE_ENV_RE.test(inner)) return `$$${fixMath(inner, true)}$$`;
  return `${open}${fixMath(inner)}${close}`;
}

// --- Entry point -----------------------------------------------------------

/** Rewrite PDF-only LaTeX for the web view. Pure; never touches math except
 * through `fixMath`. */
export function sanitizeForWeb(src: string): string {
  if (!src) return src;
  const s = src
    .replace(DISPLAY_TABULAR_RE, "$2")
    // `\$` would split the chunker's `$…$` pairing; this spelling is safe in
    // both modes (KaTeX renders it, the prose walk maps it to a sentinel).
    .replace(/(?<!\\)\\\$/g, "\\text{\\textdollar}");
  return (
    walk(s)
      // Block-level output makes its own visual break: drop line breaks that
      // touch it, then cap runs of blank lines.
      .replace(/[ \t]*\n[ \t]*(?=@@AMP_(?:CENTER|HEAD|CAPTION|PRE|TABLE|TR|TD|TDC)_(?:OPEN|CLOSE)@@|@@AMP_(?:DIAGRAM|HR)@@)/g, "")
      .replace(/(@@AMP_(?:CENTER|HEAD|CAPTION|PRE|TABLE|TR|TD|TDC)_(?:OPEN|CLOSE)@@|@@AMP_(?:DIAGRAM|HR)@@)[ \t]*\n/g, "$1")
      .replace(/(?:[ \t]*\n){3,}/g, "\n\n")
      .replace(/^(?:[ \t]*\n)+/, "")
  );
}

// --- Helpers ---------------------------------------------------------------

function isLetter(ch: string): boolean {
  return ch !== "" && /[A-Za-z]/.test(ch);
}

/** Balanced `{…}` group starting at `src[i] === "{"`: [content, index after `}`]. */
function readGroup(src: string, i: number): [string, number] | null {
  if (src.charAt(i) !== "{") return null;
  let depth = 0;
  for (let k = i; k < src.length; k++) {
    const c = src.charAt(k);
    if (c === "\\") {
      k++;
      continue;
    }
    if (c === "{") depth++;
    else if (c === "}") {
      depth--;
      if (depth === 0) return [src.slice(i + 1, k), k + 1];
    }
  }
  return null;
}

/** Spaces, then a balanced `{…}` group. */
function readArg(src: string, i: number): [string, number] | null {
  let j = i;
  while (src.charAt(j) === " " || src.charAt(j) === "\t") j++;
  return readGroup(src, j);
}

/** Spaces, then an optional `[…]` argument (brace-aware). Returns the index
 * after `]`, or `i` when there is none. */
function skipOpt(src: string, i: number): number {
  let j = i;
  while (src.charAt(j) === " " || src.charAt(j) === "\t") j++;
  if (src.charAt(j) !== "[") return i;
  let depth = 0;
  for (let k = j; k < src.length && k < j + 400; k++) {
    const c = src.charAt(k);
    if (c === "\\") {
      k++;
      continue;
    }
    if (c === "{") depth++;
    else if (c === "}") depth--;
    else if (c === "]" && depth === 0) return k + 1;
    else if (c === "\n" && src.charAt(k + 1) === "\n") return i;
  }
  return i;
}

function readArgs(src: string, j: number, pat: string): { args: (string | null)[]; end: number } {
  const args: (string | null)[] = [];
  let k = j;
  for (const t of pat) {
    if (t === "o") {
      const e = skipOpt(src, k);
      args.push(e > k ? src.slice(src.indexOf("[", k) + 1, e - 1) : null);
      k = e;
    } else {
      const g = readArg(src, k);
      if (!g) break;
      args.push(g[0]);
      k = g[1];
    }
  }
  while (args.length < pat.length) args.push(null);
  return { args, end: k };
}

/** Body and end index of the `\end{env}` matching a `\begin{env}` whose body
 * starts at `i` (nesting-aware). */
function findEnvEnd(src: string, env: string, i: number): [string, number] | null {
  const open = `\\begin{${env}}`;
  const close = `\\end{${env}}`;
  let depth = 1;
  let j = i;
  while (j < src.length) {
    const o = src.indexOf(open, j);
    const c = src.indexOf(close, j);
    if (c === -1) return null;
    if (o !== -1 && o < c) {
      depth++;
      j = o + open.length;
      continue;
    }
    depth--;
    if (depth === 0) return [src.slice(i, c), c + close.length];
    j = c + close.length;
  }
  return null;
}

/** Skip trailing spaces and at most one newline (used after block output). */
function eatNewline(src: string, k: number): number {
  let j = k;
  while (src.charAt(j) === " " || src.charAt(j) === "\t") j++;
  return src.charAt(j) === "\n" ? j + 1 : k;
}

function skipLength(src: string, j: number): number {
  const m = LENGTH_RE.exec(src.slice(j, j + 60));
  return m ? j + m[0].length : j;
}

/** Make literal text safe against the chunker and the brace check. */
function protect(text: string): string {
  return text.split("\\").join(BACKSLASH).split("$").join(DOLLAR).split("{").join(LBRACE).split("}").join(RBRACE);
}

const TOP_LEVEL_DISPLAY_ENV = /^\s*\\begin\{(?:align|gather|equation|alignat|flalign|multline|eqnarray)\*?\}/;
const ARRAY_SPEC_RE = /\\begin\{array\}\s*(?:\[[^\]]*\])?\s*\{((?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*)\}/g;

const TEXT_GROUP_RE = /\\(?:text|textbf|textit|textrm|textsf|texttt|textnormal|mbox|hbox|emph|underline)\s*\{/g;

/** Drop bare `$` inside a math segment, except inside `\text{…}`-like
 * groups where KaTeX accepts `$…$` for nested math. */
function stripBareDollars(s: string): string {
  let out = "";
  let i = 0;
  while (i < s.length) {
    TEXT_GROUP_RE.lastIndex = i;
    const m = TEXT_GROUP_RE.exec(s);
    const upto = m ? m.index : s.length;
    out += s.slice(i, upto).replace(/(?<!\\)\$/g, "");
    if (!m) break;
    const braceAt = m.index + m[0].length - 1;
    const g = readGroup(s, braceAt);
    if (!g) {
      out += s.slice(m.index, braceAt + 1);
      i = braceAt + 1;
      continue;
    }
    out += s.slice(m.index, g[1]);
    i = g[1];
  }
  return out;
}

/** Substitutions inside math for commands KaTeX does not know. `display` is
 * true for `$$…$$` and `\[…\]` segments. */
function fixMath(m: string, display = false): string {
  // A bare `$` inside \(…\) or \[…\] is always an error for KaTeX (and a
  // source mistake); dropping it renders the rest.
  let s = m.includes("$") ? stripBareDollars(m) : m;
  if (!s.includes("\\")) return s;
  if (s.includes("\\begin{")) {
    s = s
      .replace(/\\(begin|end)\{tabular\}/g, "\\$1{array}")
      .replace(/\\(begin|end)\{multline(\*?)\}/g, "\\$1{gather$2}")
      .replace(/\\(begin|end)\{eqnarray(\*?)\}/g, "\\$1{align$2}")
      .replace(ARRAY_SPEC_RE, (_m, spec: string) => {
        const clean = spec.replace(/@\{(?:[^{}]|\{[^{}]*\})*\}/g, "").replace(/[pmb]\{[^{}]*\}/g, "l").replace(/\s+/g, "");
        return `\\begin{array}{${clean}}`;
      });
    // align/gather/equation are only valid at the top level of display math;
    // nested in \left…\right or an inline segment they need the inner forms.
    if (!display || !TOP_LEVEL_DISPLAY_ENV.test(s)) {
      s = s
        .replace(/\\(begin|end)\{align\*?\}/g, "\\$1{aligned}")
        .replace(/\\(begin|end)\{gather\*?\}/g, "\\$1{gathered}")
        .replace(/\\(begin|end)\{alignat\*?\}/g, "\\$1{alignedat}")
        .replace(/\\(begin|end)\{(?:equation|flalign|eqnarray)\*?\}/g, "");
    }
  }
  return s
    .replace(/\\text\s*\{([^{}]*_[^{}]*)\}/g, (_m, inner: string) => `\\text{${inner.replace(/(?<!\\)_/g, "\\_")}}`)
    .replace(/\\label\s*\{[^{}]*\}/g, "")
    .replace(/\\vspace\*?\s*\{[^{}]*\}/g, "")
    .replace(/\\(?:centering|qedhere|allowdisplaybreaks|noindent|hfill|tightlist)(?![A-Za-z])/g, "")
    .replace(/\\bm\{/g, "\\boldsymbol{")
    .replace(/\\(?:textdegree|degree)(?![A-Za-z])/g, "{}^{\\circ}")
    .replace(/\\(?:sfrac|nicefrac)(?![A-Za-z])/g, "\\frac")
    .replace(/\\(?:mathds|mathbbm)(?![A-Za-z])/g, "\\mathbb")
    .replace(/\\textsc\{/g, "\\text{")
    .replace(/\\textsubscript\{([^{}]*)\}/g, "_{\\text{$1}}")
    .replace(/\\textsuperscript\{([^{}]*)\}/g, "^{\\text{$1}}")
    .replace(/\\ensuremath\{([^{}]*)\}/g, "$1")
    .replace(/\\AA(?![A-Za-z])/g, "\\text{Å}")
    .replace(/\\(?:Varangle|varangle)(?![A-Za-z])/g, "\\angle")
    .replace(/\\(?:wideparen|overarc)\{/g, "\\overset{\\frown}{")
    .replace(/\\(?:intertext|shortintertext)\{/g, "\\text{")
    .replace(/\\rupee(?![A-Za-z])/g, "\\text{Rs.}");
}

// --- The walk ----------------------------------------------------------------

/** Walk prose; math segments pass through (mirrors the chunker in
 * LatexContent.tsx). Bare brace groups are tracked across math so that
 * `{\bf a $x$ b}` closes correctly. */
function walk(src: string): string {
  const out: string[] = [];
  const groups: string[] = [];
  const n = src.length;
  let i = 0;
  while (i < n) {
    const c = src.charAt(i);
    const c1 = src.charAt(i + 1);
    if (c === "$") {
      if (c1 === "$") {
        const end = src.indexOf("$$", i + 2);
        if (end !== -1) {
          out.push(`$$${fixMath(src.slice(i + 2, end), true)}$$`);
          i = end + 2;
          continue;
        }
      }
      const end = src.indexOf("$", i + 1);
      if (end !== -1) {
        out.push(inlineSegment(src.slice(i + 1, end), "$", "$"));
        i = end + 1;
        continue;
      }
      out.push(DOLLAR);
      i += 1;
      continue;
    }
    if (c === "\\" && c1 === "[") {
      const end = src.indexOf("\\]", i + 2);
      if (end !== -1) {
        out.push(`\\[${fixMath(src.slice(i + 2, end), true)}\\]`);
        i = end + 2;
        continue;
      }
      out.push("[");
      i += 2;
      continue;
    }
    if (c === "\\" && c1 === "(") {
      const end = src.indexOf("\\)", i + 2);
      if (end !== -1) {
        out.push(inlineSegment(src.slice(i + 2, end), "\\(", "\\)"));
        i = end + 2;
        continue;
      }
      out.push("(");
      i += 2;
      continue;
    }
    if (c === "\\") {
      i = command(src, i, out);
      continue;
    }
    if (c === "{") {
      const m = /^\{[ \t]*\\([A-Za-z]+)(?![A-Za-z])[ \t]*/.exec(src.slice(i, i + 24));
      const sw = m ? SWITCHES.get(m[1]) : undefined;
      if (m && sw !== undefined) {
        out.push(sw[0]);
        groups.push(sw[1]);
        i += m[0].length;
        continue;
      }
      groups.push("");
      i += 1;
      continue;
    }
    if (c === "}") {
      out.push(groups.pop() ?? "");
      i += 1;
      continue;
    }
    if (c === "~") {
      out.push(" ");
      i += 1;
      continue;
    }
    if (c === "%") {
      // LaTeX comment, unless it is a percentage ("75% of").
      if (i > 0 && /[0-9]/.test(src.charAt(i - 1))) {
        out.push("%");
        i += 1;
        continue;
      }
      let e = src.indexOf("\n", i);
      if (e === -1) e = n;
      i = e + 1;
      while (src.charAt(i) === " " || src.charAt(i) === "\t") i += 1;
      continue;
    }
    let j = i + 1;
    while (j < n && !SPECIAL.has(src.charAt(j))) j += 1;
    out.push(src.slice(i, j));
    i = j;
  }
  while (groups.length) out.push(groups.pop() as string);
  return out.join("");
}

/** Handle a backslash at `src[i]` in prose; returns the index to continue from. */
function command(src: string, i: number, out: string[]): number {
  const c1 = src.charAt(i + 1);
  if (c1 === "") return i + 1;
  if (c1 === "\\") {
    // Line break: \\ \\* \\[2mm]; the newline that usually follows is folded in.
    let j = i + 2;
    if (src.charAt(j) === "*") j += 1;
    const m = BREAK_LEN_RE.exec(src.slice(j, j + 40));
    if (m) j += m[0].length;
    out.push("\n");
    return eatNewline(src, j);
  }
  if (!isLetter(c1)) {
    const acc = ACCENTS.get(c1);
    if (acc !== undefined) return accent(src, i + 2, acc, c1, out);
    out.push(CHAR_ESCAPES.get(c1) ?? c1);
    return i + 2;
  }
  const nm = /^[A-Za-z]+/.exec(src.slice(i + 1, i + 48));
  const name = nm ? nm[0] : c1;
  let j = i + 1 + name.length;
  if (src.charAt(j) === "*" && STARRED.has(name)) j += 1;

  if (name === "begin") return beginEnv(src, j, out);
  if (name === "end") {
    const g = readArg(src, j);
    if (!g) return j;
    const env = g[0].trim();
    if (env === "center") out.push(CENTER_CLOSE);
    else if (env !== "document") out.push("\n");
    return eatNewline(src, g[1]);
  }
  const sym = SYMBOLS.get(name);
  if (sym !== undefined) {
    out.push(sym);
    return j;
  }
  if (DROP0.has(name)) return j;
  if (DROP_OPT.has(name)) return skipOpt(src, j);
  if (name === "par") {
    out.push("\n\n");
    return j;
  }
  if (BREAKS.has(name)) {
    out.push("\n");
    return eatNewline(src, skipOpt(src, j));
  }
  if (name === "vskip") {
    out.push("\n");
    return skipLength(src, j);
  }
  if (name === "hskip" || name === "kern" || name === "mkern" || name === "mskip") {
    out.push(" ");
    return skipLength(src, j);
  }
  if (name === "verb") return verb(src, j, out);
  const lacc = LETTER_ACCENTS.get(name);
  if (lacc !== undefined && src.charAt(j) === "{") return accent(src, j, lacc, "", out);
  if (name === "newcommand" || name === "renewcommand" || name === "providecommand" || name === "DeclareRobustCommand") {
    return skipMacroDef(src, j);
  }
  if (name === "def" || name === "gdef" || name === "edef") return skipDef(src, j);
  if (name === "let") {
    const m = /^\s*\\(?:[A-Za-z]+|.)\s*=?\s*\\(?:[A-Za-z]+|.)/.exec(src.slice(j, j + 80));
    return m ? j + m[0].length : j;
  }
  const drop = DROP_ARGS.get(name);
  if (drop !== undefined) {
    const r = readArgs(src, j, drop);
    if (name === "vspace" || name === "addvspace") out.push("\n");
    else if (name === "hspace") out.push(" ");
    return r.end;
  }
  const keep = KEEP.get(name);
  if (keep !== undefined) {
    const r = readArgs(src, j, keep.pat);
    out.push(keep.render(r.args));
    let e = keep.block ? eatNewline(src, r.end) : r.end;
    if (keep.trim) while (src.charAt(e) === " " || src.charAt(e) === "\t") e++;
    return e;
  }
  if (MATH_CMDS.has(name)) {
    const end = mathRunEnd(src, j, name);
    const run = src.slice(i, end);
    if (!run.includes("$")) {
      out.push(`$${fixMath(run)}$`);
      return end;
    }
    return j;
  }
  // Unknown command. A JSON-style lost escape (`\nTherefore`) keeps its word;
  // anything else is dropped and its brace argument (if any) is unwrapped by
  // the group rule in walk().
  if (name.length > 1 && "ntr".includes(name.charAt(0)) && /[A-Z]/.test(name.charAt(1))) {
    const lead = name.charAt(0) === "n" ? "\n" : name.charAt(0) === "t" ? " " : "";
    out.push(lead + name.slice(1));
    return j;
  }
  if (src.charAt(j) === "[") {
    const e = skipOpt(src, j);
    if (e > j) return e;
  }
  return j;
}

function accent(src: string, k: number, comb: string, raw: string, out: string[]): number {
  const g = readGroup(src, k);
  if (g) {
    const inner = g[0].trim();
    out.push(inner.length === 1 ? (inner + comb).normalize("NFC") : walk(inner));
    return g[1];
  }
  const ch = src.charAt(k);
  if (isLetter(ch)) {
    out.push((ch + comb).normalize("NFC"));
    return k + 1;
  }
  out.push(raw);
  return k;
}

function verb(src: string, j: number, out: string[]): number {
  let k = j;
  if (src.charAt(k) === "*") k++;
  const d = src.charAt(k);
  if (d === "" || isLetter(d) || d === " " || d === "\n" || d === "{") return k;
  const e = src.indexOf(d, k + 1);
  if (e === -1) return k;
  out.push(TT_OPEN + protect(src.slice(k + 1, e)) + TT_CLOSE);
  return e + 1;
}

function skipMacroDef(src: string, j: number): number {
  let k = j;
  while (src.charAt(k) === " ") k++;
  if (src.charAt(k) === "{") {
    const g = readGroup(src, k);
    if (!g) return k;
    k = g[1];
  } else if (src.charAt(k) === "\\") {
    const m = /^\\(?:[A-Za-z]+|.)/.exec(src.slice(k, k + 48));
    k += m ? m[0].length : 1;
  } else {
    return k;
  }
  k = skipOpt(src, k);
  k = skipOpt(src, k);
  const g = readArg(src, k);
  return g ? g[1] : k;
}

function skipDef(src: string, j: number): number {
  const m = /^\s*\\(?:[A-Za-z]+|.)[^{\n]{0,40}/.exec(src.slice(j, j + 90));
  if (!m) return j;
  const k = j + m[0].length;
  const g = readGroup(src, k);
  return g ? g[1] : k;
}

/** End of a math run that starts with a math-only command whose name ends at
 * `j`: attached brace groups, scripts, and further math commands. */
function mathRunEnd(src: string, j: number, name: string): number {
  let k = j;
  if (name === "left") {
    const r = src.indexOf("\\right", k);
    if (r === -1) return k;
    k = r + "\\right".length;
    const dm = /^\s*(?:\\[A-Za-z]+|\\.|[^\s])/.exec(src.slice(k, k + 20));
    return dm ? k + dm[0].length : k;
  }
  let groups = 0;
  if (name === "sqrt" && src.charAt(k) === "[") k = skipOpt(src, k);
  for (;;) {
    const g = readGroup(src, k);
    if (g) {
      k = g[1];
      groups++;
      continue;
    }
    const ch = src.charAt(k);
    if (ch === "^" || ch === "_") {
      k++;
      const g2 = readGroup(src, k);
      if (g2) k = g2[1];
      else if (src.charAt(k) === "\\") {
        const nm = /^\\[A-Za-z]+/.exec(src.slice(k, k + 30));
        k += nm ? nm[0].length : 2;
      } else if (k < src.length) k++;
      continue;
    }
    if (ch === "\\") {
      const nm = /^\\([A-Za-z]+)/.exec(src.slice(k, k + 40));
      if (nm && MATH_CMDS.has(nm[1]) && nm[1] !== "left") {
        k += nm[0].length;
        continue;
      }
    }
    break;
  }
  if ((name === "frac" || name === "dfrac" || name === "tfrac" || name === "binom") && groups < 2) {
    // \frac12 without braces: take single-character arguments.
    while (groups < 2 && /[A-Za-z0-9]/.test(src.charAt(k))) {
      k++;
      groups++;
    }
  }
  return k;
}

function beginEnv(src: string, j: number, out: string[]): number {
  const g = readArg(src, j);
  if (!g) return j;
  const env = g[0].trim();
  const base = env.replace(/\*$/, "");
  let k = g[1];
  if (TABULAR_ENVS.has(base)) {
    k = skipOpt(src, k);
    const nArgs = env === "tabular" || env === "longtable" || env === "supertabular" || env === "xtabular" ? 1 : 2;
    for (let a = 0; a < nArgs; a++) {
      const ga = readArg(src, k);
      if (!ga) break;
      k = ga[1];
    }
    const body = findEnvEnd(src, env, k);
    if (!body) {
      out.push("\n");
      return eatNewline(src, k);
    }
    out.push("\n" + tabularToSentinels(body[0]) + "\n");
    return eatNewline(src, body[1]);
  }
  if (DIAGRAM_ENVS.has(base)) {
    k = skipOpt(src, k);
    const body = findEnvEnd(src, env, k);
    if (!body) {
      out.push("\n");
      return eatNewline(src, k);
    }
    out.push("\n" + DIAGRAM + "\n");
    return eatNewline(src, body[1]);
  }
  if (VERBATIM_ENVS.has(base)) {
    k = skipOpt(src, k);
    const body = findEnvEnd(src, env, k);
    if (!body) {
      out.push("\n");
      return eatNewline(src, k);
    }
    const text = body[0].replace(/^[ \t]*\n/, "").replace(/\n[ \t]*$/, "");
    out.push(PRE_OPEN + protect(text) + PRE_CLOSE);
    return eatNewline(src, body[1]);
  }
  if (base === "comment") {
    const body = findEnvEnd(src, env, k);
    return body ? eatNewline(src, body[1]) : k;
  }
  if (MATH_ONLY_ENVS.has(base)) {
    const body = findEnvEnd(src, env, k);
    if (!body) {
      out.push("\n");
      return eatNewline(src, k);
    }
    const inner = body[0];
    if (base === "displaymath") out.push(`$$${fixMath(inner, true)}$$`);
    else if (base === "math") out.push(`$${fixMath(inner)}$`);
    else if (base === "subequations") out.push(walk(inner));
    else out.push(`$$${fixMath(`\\begin{${env}}${inner}\\end{${env}}`, true)}$$`);
    return body[1];
  }
  k = skipOpt(src, k);
  if (base === "center") {
    out.push("\n" + CENTER_OPEN);
    return eatNewline(src, k);
  }
  const nArgs = ENV_ARGS.get(base) ?? 0;
  for (let a = 0; a < nArgs; a++) {
    const ga = readArg(src, k);
    if (!ga) break;
    k = ga[1];
  }
  out.push("\n");
  return eatNewline(src, k);
}

// --- Tabular ---------------------------------------------------------------

const RULES_RE =
  /\\(?:hline|toprule|midrule|bottomrule|hdashline)(?![A-Za-z])|\\(?:cline|noalign|rowcolor|arrayrulecolor|cellcolor)\s*\{[^{}]*\}|\\cmidrule(?:\([^)]*\))?\s*\{[^{}]*\}|\\specialrule\s*\{[^{}]*\}\s*\{[^{}]*\}\s*\{[^{}]*\}/g;

/** Split a tabular body into rows (`\\`) or a row into cells (`&`), ignoring
 * separators inside braces, math, and nested environments. */
function splitTop(s: string, sep: "row" | "cell"): string[] {
  const parts: string[] = [];
  let depth = 0;
  let env = 0;
  let inMath = false;
  let start = 0;
  let i = 0;
  const n = s.length;
  while (i < n) {
    const c = s.charAt(i);
    if (c === "\\") {
      const c1 = s.charAt(i + 1);
      if (c1 === "\\") {
        if (sep === "row" && depth === 0 && env === 0 && !inMath) {
          parts.push(s.slice(start, i));
          let k = i + 2;
          if (s.charAt(k) === "*") k++;
          const m = BREAK_LEN_RE.exec(s.slice(k, k + 40));
          if (m) k += m[0].length;
          start = k;
          i = k;
          continue;
        }
        i += 2;
        continue;
      }
      if (c1 === "(" || c1 === "[") inMath = true;
      else if (c1 === ")" || c1 === "]") inMath = false;
      else if (s.startsWith("\\begin{", i)) env++;
      else if (s.startsWith("\\end{", i)) env = Math.max(0, env - 1);
      i += 2;
      continue;
    }
    if (c === "$") {
      const two = s.charAt(i + 1) === "$";
      inMath = !inMath;
      i += two ? 2 : 1;
      continue;
    }
    if (c === "{") depth++;
    else if (c === "}") depth = Math.max(0, depth - 1);
    else if (c === "&" && sep === "cell" && depth === 0 && env === 0 && !inMath) {
      parts.push(s.slice(start, i));
      start = i + 1;
    }
    i++;
  }
  parts.push(s.slice(start));
  return parts;
}

function tabularToSentinels(body: string): string {
  const out: string[] = [TABLE_OPEN];
  for (const row of splitTop(body, "row")) {
    const cells = splitTop(row, "cell").map((c) => c.replace(RULES_RE, "").trim());
    if (cells.every((c) => c === "")) continue;
    out.push(TR_OPEN);
    for (let cell of cells) {
      let span = 1;
      const mc = /^\\multicolumn\s*\{\s*(\d+)\s*\}\s*\{[^{}]*\}\s*/.exec(cell);
      if (mc) {
        span = parseInt(mc[1], 10) || 1;
        const g = readGroup(cell, mc[0].length);
        cell = g ? g[0] + cell.slice(g[1]) : cell.slice(mc[0].length);
      }
      out.push(span > 1 ? `${TDC_OPEN}${span}${TDC_DELIM}` : TD_OPEN, walk(cell.trim()), TD_CLOSE);
    }
    out.push(TR_CLOSE);
  }
  out.push(TABLE_CLOSE);
  return out.join("");
}
