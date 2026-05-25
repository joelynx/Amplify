"""Theme metadata + asset-path resolution.

Spec §11.2: a theme is `(CSS overlay) + (sprite pack) + (sound pack)`. The
CSS overlay lives entirely in `frontend/styles/themes/<id>/theme.css` and is
bundled by Vite — backend doesn't touch it.

The sprite pack and sound pack live under `app/resources/{sprites,sounds}/<id>/`.
This module exposes the registry (`THEMES`) and helpers for resolving asset
paths on disk. `play_sound` consults this registry; missing files fail soft
per the spec.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

_RESOURCES: Final[Path] = Path(__file__).resolve().parent.parent / "resources"


@dataclass(slots=True, frozen=True)
class ThemeMeta:
    id: str
    name: str
    description: str

    def sounds_dir(self) -> Path:
        return _RESOURCES / "sounds" / self.id

    def sprites_dir(self) -> Path:
        return _RESOURCES / "sprites" / self.id


THEMES: Final[tuple[ThemeMeta, ...]] = (
    ThemeMeta(
        id="default-light",
        name="Default Light",
        description="Clean, neutral light theme. WCAG AA contrast.",
    ),
    ThemeMeta(
        id="default-dark",
        name="Default Dark",
        description="Same shape, dark surfaces. WCAG AA contrast.",
    ),
    ThemeMeta(
        id="pastel",
        name="Pastel",
        description="Soft pastel palette with rounded edges and a pillowy tooltip.",
    ),
    ThemeMeta(
        id="frutiger-aero",
        name="Frutiger Aero",
        description="Glassy sky-blue era. Subtle blur, soft glows, orange accents.",
    ),
    ThemeMeta(
        id="pixel-art",
        name="Pixel Art",
        description="Chunky 8/16-bit aesthetic. Monospace, square borders, drop-shadow blocks.",
    ),
    ThemeMeta(
        id="windows-xp",
        name="Windows XP",
        description="Early-2000s desktop palette. Bevels, Tahoma, sticky-note tooltips.",
    ),
    ThemeMeta(
        id="comic",
        name="Comic",
        description="Heavy ink borders, speech-bubble tooltips, hand-drawn type.",
    ),
    ThemeMeta(
        id="ascii",
        name="ASCII",
        description="Monospace terminal aesthetic. Green on near-black, no rounding.",
    ),
    ThemeMeta(
        id="android-kitkat",
        name="Android KitKat",
        description="Material 1 flat surfaces, teal primary, dark Material toast tooltip.",
    ),
)

_BY_ID: Final[dict[str, ThemeMeta]] = {t.id: t for t in THEMES}


def get(theme_id: str) -> ThemeMeta | None:
    return _BY_ID.get(theme_id)


def resolve_sound_path(theme_id: str, event: str) -> Path | None:
    """Return the on-disk path to the requested sound, or None if missing.

    Falls back to the `default-light` pack when the active theme has no file —
    keeps a click sound playing even before a flavor theme's audio is shipped.
    """
    candidates: list[Path] = []
    theme = get(theme_id) or get("default-light")
    if theme is None:
        return None
    candidates.append(theme.sounds_dir() / f"{event}.mp3")
    if theme.id != "default-light":
        candidates.append((_BY_ID["default-light"]).sounds_dir() / f"{event}.mp3")
    for p in candidates:
        if p.exists():
            return p
    return None
