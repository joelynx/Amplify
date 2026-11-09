"""The start-up URL must survive .NET Framework's Uri (pywebview on Windows),
which folds a `?query` on a file:// URL into the file name."""

from __future__ import annotations

from urllib.parse import urlsplit

from app import main


def test_boot_theme_goes_in_the_fragment(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "_boot_theme", lambda: "pastel")
    index = tmp_path / "index.html"
    url = main._with_theme(index.as_uri())
    parts = urlsplit(url)
    assert "?" not in url
    assert parts.path.endswith("/index.html")
    assert parts.fragment == "boot-theme=pastel"


def test_no_theme_leaves_the_url_alone(monkeypatch):
    monkeypatch.setattr(main, "_boot_theme", lambda: None)
    assert main._with_theme("http://localhost:5173/") == "http://localhost:5173/"
