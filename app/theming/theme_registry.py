"""Theme metadata + asset-path resolution.

Spec §11.2: a theme is `(CSS overlay) + (sprite pack) + (sound pack)`. Since
the makeover a theme id here names a *palette* (the CSS colour overlay in
`frontend/styles/themes/`); the other slots (chrome, sounds, room, …)
live in the frontend appearance system (frontend/src/appearance/). The
backend keeps this list to enforce the reward locks on `set_theme`.

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
    # Earned through a practice milestone (app/core/learning.py MILESTONES);
    # the built-in themes are always available.
    reward: bool = False

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
    ThemeMeta(
        id="sage",
        name="Sage",
        description="Calm green-grey light theme. Earned with spaced reviews.",
        reward=True,
    ),
    ThemeMeta(
        id="ember",
        name="Ember",
        description="Warm paper tones with a deep orange accent. Earned by fixing old mistakes.",
        reward=True,
    ),
    ThemeMeta(
        id="midnight",
        name="Midnight",
        description="Deep navy dark theme with a soft violet accent. Earned with honest attempts.",
        reward=True,
    ),
    # Palettes added with the makeover (frontend/styles/themes/extra.css).
    ThemeMeta(id="blackboard", name="Blackboard", description="Slate green and chalk."),
    ThemeMeta(id="blueprint", name="Blueprint", description="White line work on drafting blue."),
    ThemeMeta(id="engineer", name="Engineer's Notebook", description="Pale green engineering paper."),
    ThemeMeta(id="manuscript", name="Manuscript", description="Parchment with gilt and lapis."),
    ThemeMeta(id="dark-academia", name="Dark Academia", description="Leather brown and brass."),
    ThemeMeta(id="synthwave", name="Synthwave", description="Magenta and cyan on a purple night."),
    ThemeMeta(id="vaporwave", name="Vaporwave", description="Pink, teal and marble. Unlocked by an easter egg (frontend)."),
    ThemeMeta(id="handheld", name="Handheld", description="Four shades of LCD green."),
    ThemeMeta(id="amber-crt", name="Amber CRT", description="Amber phosphor on black."),
    ThemeMeta(id="dracula", name="Dracula", description="The Dracula editor palette (MIT)."),
    ThemeMeta(id="nord", name="Nord", description="Arctic blue-greys (MIT)."),
    ThemeMeta(id="catppuccin", name="Catppuccin Mocha", description="Soft pastel dark (MIT)."),
    ThemeMeta(id="catppuccin-latte", name="Catppuccin Latte", description="Soft pastel light (MIT)."),
    ThemeMeta(id="gruvbox", name="Gruvbox", description="Retro warm dark (MIT)."),
    ThemeMeta(id="solarized", name="Solarized Light", description="Ethan Schoonover's light palette (MIT)."),
    ThemeMeta(id="tokyo-night", name="Tokyo Night", description="Neon city dark (MIT)."),
    ThemeMeta(id="lofi-cafe", name="Lo-fi Café", description="Coffee and dusk."),
    ThemeMeta(id="desert-night", name="Desert Night", description="Indigo sky over sand."),
    ThemeMeta(id="sakura", name="Sakura", description="Blossom pink on rice paper."),
    ThemeMeta(id="bauhaus", name="Bauhaus", description="Primary red, yellow and blue."),
    ThemeMeta(id="brutalist", name="Brutalist", description="Black, white and one loud accent."),
    ThemeMeta(id="club", name="Club", description="Mathematics Club red and Coding Club yellow."),
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
