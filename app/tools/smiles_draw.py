"""SMILES strings drawn as 2D structure PNGs for imported chemistry questions (owner 2026-11-23: "Can we have a
converter to convert smiles to drawings?").

RDKit lives in the calc tool's venv (config tools.python), not in the app's .venv, so draw_many() runs this file
there as a worker: SMILES in on stdin (JSON list), PNGs out on stdout (JSON {smiles: base64 or null}). Molecules and
reaction SMILES ("A.B>>C") are drawn plainly: no atom indices, CIP labels or stereo annotations, which could give an
answer away. A SMILES RDKit cannot parse gets None, and the question keeps only its text.

Importers: png = draw_many([s])[s]; name = image_name(png); text += "\\n\\n" + GRAPHIC.format(name); image = [(name, png)]."""

from __future__ import annotations

import base64
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def image_name(png: bytes) -> str:
    return "smi-" + hashlib.sha1(png).hexdigest()[:16]


def _calc_python() -> Path:
    cfg = json.loads((REPO / "pipeline" / "config.json").read_text(encoding="utf-8"))
    return REPO / cfg["tools"]["python"]


def draw_many(smiles: list[str], timeout: int = 600) -> dict[str, bytes | None]:
    """{smiles: PNG bytes or None} for each distinct string, drawn in one worker run."""
    todo = sorted(set(smiles))
    if not todo:
        return {}
    p = subprocess.run([str(_calc_python()), "-I", str(Path(__file__).resolve()), "--worker"],
                       input=json.dumps(todo), capture_output=True, text=True, timeout=timeout, encoding="utf-8")
    if p.returncode:
        raise RuntimeError(f"SMILES worker failed: {p.stderr[-800:]}")
    got = json.loads(p.stdout)
    return {s: (base64.b64decode(got[s]) if got.get(s) else None) for s in todo}


# --- the worker (runs in the calc venv) -------------------------------------------------------------------


def _draw(s: str) -> bytes | None:
    from rdkit import Chem, RDLogger
    from rdkit.Chem import rdChemReactions
    from rdkit.Chem.Draw import rdMolDraw2D

    RDLogger.DisableLog("rdApp.*")
    if ">" in s:
        try:
            rxn = rdChemReactions.ReactionFromSmarts(s, useSmiles=True)
        except ValueError:
            return None
        if rxn is None or rxn.GetNumReactantTemplates() + rxn.GetNumProductTemplates() == 0:
            return None
        n = rxn.GetNumReactantTemplates() + rxn.GetNumProductTemplates()
        d = rdMolDraw2D.MolDraw2DCairo(min(1400, 260 * n + 120), 280)
        _style(d)
        d.DrawReaction(rxn)
    else:
        mol = Chem.MolFromSmiles(s)
        if mol is None or mol.GetNumAtoms() == 0:
            return None
        heavy = mol.GetNumHeavyAtoms()
        w = 300 if heavy <= 8 else 420 if heavy <= 25 else 560
        d = rdMolDraw2D.MolDraw2DCairo(w, int(w * 0.75))
        _style(d)
        rdMolDraw2D.PrepareAndDrawMolecule(d, mol)
    d.FinishDrawing()
    return d.GetDrawingText()


def _style(d) -> None:
    o = d.drawOptions()
    o.addAtomIndices = False
    o.addStereoAnnotation = False
    o.bondLineWidth = 2
    o.padding = 0.08
    o.setBackgroundColour((1, 1, 1, 1))


def _worker() -> None:
    out = {}
    for s in json.loads(sys.stdin.read()):
        try:
            png = _draw(s)
        except Exception:  # noqa: BLE001  (a SMILES RDKit chokes on keeps its text only)
            png = None
        out[s] = base64.b64encode(png).decode("ascii") if png else None
    sys.stdout.write(json.dumps(out))


if __name__ == "__main__" and "--worker" in sys.argv:
    _worker()
