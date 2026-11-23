"""SMILES drawn as PNGs through the calc venv's RDKit (app/tools/smiles_draw.py)."""

from __future__ import annotations

import pytest

from app.tools import smiles_draw

pytestmark = pytest.mark.skipif(not smiles_draw._calc_python().exists(), reason="calc venv (RDKit) not installed")


def test_molecules_and_reactions_are_drawn() -> None:
    mol, rxn, bad = r"C#C/C=C\C#C", "CCO.CC(=O)O>>CCOC(C)=O", "C1CC(("
    got = smiles_draw.draw_many([mol, rxn, bad, mol])
    assert set(got) == {mol, rxn, bad}
    assert got[mol][:4] == b"\x89PNG" and got[rxn][:4] == b"\x89PNG"
    assert got[bad] is None
    assert smiles_draw.image_name(got[mol]).startswith("smi-")
