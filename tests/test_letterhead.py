"""Club letterhead and header images in generated PSets (app/tex/pdfgen)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.persistence.repositories import configs as configs_repo
from app.tex import pdfgen


def test_letterhead_off_by_default(conn: sqlite3.Connection, tmp_path: Path) -> None:
    assert pdfgen.letterhead(conn, tmp_path) is None
    assert list(tmp_path.iterdir()) == []


def test_letterhead_copies_logos_and_returns_includes(
    conn: sqlite3.Connection, tmp_path: Path
) -> None:
    configs_repo.set_(conn, "PDF_CLUB_LETTERHEAD", True)
    tex = pdfgen.letterhead(conn, tmp_path)
    assert tex is not None
    assert tex["left"] == r"\includegraphics[height=11pt]{amp-club-ampliphi_inline.pdf}"
    assert tex["right"] == r"\includegraphics[height=8pt]{amp-club-coding_club.pdf}"
    copied = sorted(p.name for p in tmp_path.iterdir())
    assert copied == ["amp-club-ampliphi_inline.pdf", "amp-club-coding_club.pdf"]
    for name in copied:
        assert (tmp_path / name).read_bytes().startswith(b"%PDF")


def test_import_header_image_names_by_content(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    dest = tmp_path / "teximages"
    dest.mkdir()
    (src / "Crest.JPEG").write_bytes(b"\xff\xd8 not really a jpeg")
    name = pdfgen.import_header_image(src / "Crest.JPEG", dest)
    assert name.startswith("amp-header-") and name.endswith(".jpg")
    assert (dest / name).read_bytes() == b"\xff\xd8 not really a jpeg"
    # Same bytes, same name: picking it again does not pile up copies.
    assert pdfgen.import_header_image(src / "Crest.JPEG", dest) == name
    assert len(list(dest.iterdir())) == 1


def test_import_header_image_rejects_other_types(tmp_path: Path) -> None:
    (tmp_path / "logo.svg").write_text("<svg/>")
    with pytest.raises(ValueError, match="PNG, JPEG or PDF"):
        pdfgen.import_header_image(tmp_path / "logo.svg", tmp_path)


def test_header_image_only_trusts_its_own_names(conn: sqlite3.Connection, tmp_path: Path) -> None:
    assert pdfgen.header_image(conn, "left", tmp_path) is None
    (tmp_path / "x.png").write_bytes(b"png")
    for bad in (
        "x.png",
        r"amp-header-0123456789ab.png}\input{evil",
        "../amp-header-0123456789ab.png",
    ):
        configs_repo.set_(conn, "PDF_LEFT_HEADER_IMAGE", bad)
        assert pdfgen.header_image(conn, "left", tmp_path) is None
    configs_repo.set_(conn, "PDF_LEFT_HEADER_IMAGE", "amp-header-0123456789ab.png")
    assert pdfgen.header_image(conn, "left", tmp_path) is None  # not copied yet
    (tmp_path / "amp-header-0123456789ab.png").write_bytes(b"png")
    assert (
        pdfgen.header_image(conn, "left", tmp_path)
        == r"\includegraphics[height=11pt]{amp-header-0123456789ab.png}"
    )


def test_assemble_puts_images_outside_the_header_text(
    conn: sqlite3.Connection, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(pdfgen, "image_dir", lambda: tmp_path)
    (tmp_path / "img.png").write_bytes(b"png")
    name = pdfgen.import_header_image(tmp_path / "img.png", tmp_path)
    configs_repo.set_(conn, "PDF_LEFT_HEADER", "Left text")
    configs_repo.set_(conn, "PDF_RIGHT_HEADER", "Right text")
    configs_repo.set_(conn, "PDF_LEFT_HEADER_IMAGE", name)
    configs_repo.set_(conn, "PDF_RIGHT_HEADER_IMAGE", name)
    configs_repo.set_(conn, "PDF_CLUB_LETTERHEAD", True)
    tex = pdfgen.assemble(conn, [], {"solutions": "none"}, pset_id="t")
    img = rf"\includegraphics[height=11pt]{{{name}}}"
    club_l = r"\includegraphics[height=11pt]{amp-club-ampliphi_inline.pdf}"
    club_r = r"\includegraphics[height=8pt]{amp-club-coding_club.pdf}"
    assert rf"\fancyhead[L]{{{club_l}\quad {img}\quad Left text}}" in tex
    assert rf"\fancyhead[R]{{Right text\quad {img}\quad {club_r}}}" in tex
    assert r"\setlength{\headheight}{15pt}" in tex
