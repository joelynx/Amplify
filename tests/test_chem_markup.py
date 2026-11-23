"""mhchem's \\pu (KaTeX/MathJax only) rewritten as plain LaTeX at import (app/tools/chem_markup.py)."""

from __future__ import annotations

import pytest

from app.tools.chem_markup import pu_to_latex


@pytest.mark.parametrize(("src", "want"), [
    (r"at \pu{500 K}.", r"at $500\ \mathrm{K}$."),
    (r"c = \pu{1.5e-3 mol L-1}", r"c = $1.5\times 10^{-3}\ \mathrm{mol\,L^{-1}}$"),
    (r"$\Delta H = \pu{-24.8 kJ mol-1}$", r"$\Delta H = -24.8\ \mathrm{kJ\,mol^{-1}}$"),
    (r"$R = \pu{8.314 J K-1 mol-1}$", r"$R = 8.314\ \mathrm{J\,K^{-1}\,mol^{-1}}$"),
    (r"\(k = \pu{2.0 \times 10^{-4} s^-1}\)", r"\(k = 2.0\times 10^{-4}\ \mathrm{s^{-1}}\)"),
    (r"in \pu{kJ/mol}", r"in $\mathrm{kJ/mol}$"),
    (r"\pu{3 m^2}", r"$3\ \mathrm{m^{2}}$"),
    (r"no units here", r"no units here"),
    (r"price \$5 and \pu{2 mol}", r"price \$5 and $2\ \mathrm{mol}$"),
])
def test_pu_becomes_plain_latex(src: str, want: str) -> None:
    assert pu_to_latex(src) == want


def test_ce_is_left_alone() -> None:
    s = r"\ce{Fe2O3 + 3CO -> 2Fe + 3CO2}"
    assert pu_to_latex(s) == s
