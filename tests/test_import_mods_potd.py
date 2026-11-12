"""The repairs app/tools/import_mods_potd.py makes on the way in: the TeX bot's macros, the
enumerate package's labels, URLs and paragraph-start breaks for XeLaTeX, bare-math answers and
the hint tiers."""

from __future__ import annotations

import json

from app.tools import import_mods_potd as potd


def test_bot_macros_are_written_out() -> None:
    assert potd.expand_macros(r"$f\colon \bR \to \bZ_{>0}$") == r"$f\colon \mathbb{R} \to \mathbb{Z}_{>0}$"
    assert potd.expand_macros(r"$\ord_p(2) \mid \lcm(a, b)$") == r"$\operatorname{ord}_p(2) \mid \operatorname{lcm}(a, b)$"
    assert potd.expand_macros(r"$\bRx \bot$") == r"$\bRx \bot$"  # longer names are left alone


def test_floor_takes_its_braced_argument() -> None:
    assert potd.expand_macros(r"$\floor{\frac{n}{2}} + \ceil {x}$") == r"$\lfloor \frac{n}{2} \rfloor + \lceil x \rceil$"


def test_a_line_break_before_letters_is_not_a_macro() -> None:
    assert potd.expand_macros("a\\\\ii) b") == "a\\\\ii) b"
    assert potd.expand_macros("\\ii First") == "\\item First"
    assert potd.expand_macros("done.\\newlineProof: x") == "done.\\newline Proof: x"


def test_enumerate_labels_in_enumitem_form() -> None:
    assert potd.enumitem_labels(r"\begin{enumerate}[(a)]") == r"\begin{enumerate}[label=(\alph*)]"
    assert potd.enumitem_labels(r"\begin{enumerate}[i)]") == r"\begin{enumerate}[label=\roman*)]"
    assert potd.enumitem_labels(r"\begin{enumerate}[1.]") == r"\begin{enumerate}[label=\arabic*.]"
    assert potd.enumitem_labels(r"\begin{enumerate}[resume]") == r"\begin{enumerate}[resume]"
    assert potd.enumitem_labels(r"\begin{enumerate}[label=(\alph*)]") == r"\begin{enumerate}[label=(\alph*)]"


def test_pdf_safe_urls_and_paragraph_breaks() -> None:
    assert potd.pdf_safe("see https://x.org/a_b.pdf#page=4 now") == r"see https://x.org/a\_b.pdf\#page=4 now"
    assert potd.pdf_safe(r"see https://x.org/a\_b") == r"see https://x.org/a\_b"
    assert potd.pdf_safe("end.\n\n\\newline\nNext") == "end.\n\n\nNext"
    assert potd.pdf_safe("a \\\\\nb") == "a \\\\\nb"  # a break inside a paragraph stays


def test_answers_in_bare_math_get_dollars() -> None:
    assert potd._answer(r"n\geq 1005") == r"$n\geq 1005$"
    assert potd._answer("$2$") == "$2$"
    assert potd._answer("No.") == "No."
    assert potd._answer(" - ") is None


def test_solution_cells_that_are_no_solution(tmp_path, monkeypatch) -> None:
    header = ["/f", "Date", "Source", "Problem Statement", "Hint 1", "Hint 2", "Hint 3", "Answer", "Solution",
              "Solution Link"]
    rows = [["7", "1 Jan 2020", "Folklore", "Prove it.", "", "", "", "", "https://x.org/sol.pdf", ""],
            ["8", "2 Jan 2020", "Folklore", "Prove that.", "", "", "", "", "lol no", ""]]
    path = tmp_path / "potd.csv"
    path.write_text("\n".join(",".join(f'"{c}"' for c in r) for r in [header, *rows]) + "\n", encoding="utf-8")
    assigned = {n: {"potd_number": n, "source_as_in_sheet": "Folklore", "skip": "",
                    "source": "Math Olympiad Discord Server", "subsource": "Folklore"} for n in ("7", "8")}
    fixes = tmp_path / "fixes.json"
    fixes.write_text(json.dumps([{"potd": 8, "field": "solution", "drop": True, "reason": "a joke"}]), encoding="utf-8")
    monkeypatch.setattr(potd, "FIXES_PATH", fixes)
    out, _ = potd.parse(path, assigned)
    potd.apply_fixes(out)
    by = {r["potd"]: r for r in out}
    assert (by["7"]["solution"], by["7"]["link"]) == (None, "https://x.org/sol.pdf")
    assert by["8"]["solution"] is None


def test_hint_tiers_close_gaps(tmp_path) -> None:
    header = ["/f", "Date", "Source", "Problem Statement", "Hint 1", "Hint 2", "Hint 3", "Answer", "Solution",
              "Solution Link"]
    rows = [["7", "1 Jan 2020", "Folklore", "Prove it.", "", "", "Only the third.", "", "", "AoPS"],
            ["8", "2 Jan 2020", "Folklore", "Prove that.", "One.", "", "Three.", "", "", "https://x.org"]]
    path = tmp_path / "potd.csv"
    path.write_text("\n".join(",".join(f'"{c}"' for c in r) for r in [header, *rows]) + "\n", encoding="utf-8")
    assigned = {n: {"potd_number": n, "source_as_in_sheet": "Folklore", "skip": "",
                    "source": "Math Olympiad Discord Server", "subsource": "Folklore"} for n in ("7", "8")}
    out, log = potd.parse(path, assigned)
    assert log == []
    by = {r["potd"]: r for r in out}
    assert (by["7"]["hints"], by["7"]["more_hints"], by["7"]["link"]) == ("Only the third.", None, None)
    assert (by["8"]["hints"], json.loads(by["8"]["more_hints"]), by["8"]["link"]) == ("One.", ["Three."], "https://x.org")
