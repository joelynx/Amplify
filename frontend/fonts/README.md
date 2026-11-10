# Bundled fonts

Drop font files into a folder named after the family, exactly as the
typography items in `src/appearance/core/items.ts` spell it:

    fonts/Inter/Inter-Variable.woff2
    fonts/Comic Neue/ComicNeue-Bold.woff2

`src/appearance/fonts.ts` registers every file at startup. Weight and style
come from the file name (Regular, Bold, SemiBold, Italic, Variable, …).
WOFF2 is smallest; TTF/OTF also work. A missing family just falls back to the
next font in the stack. Theme Lab (#/theme-lab) shows which ones are bundled.

The app is offline: never link fonts from a CDN. Use fonts whose licence allows
redistribution (SIL OFL, Apache 2.0); the repo is public. Keep each font's
licence file next to it (e.g. `fonts/Inter/OFL.txt`) and credit it in the
typography item that uses it (`credits`, shown on the About page).

## What's here

The owner's picks (2026-11-10), all SIL OFL 1.1, from github.com/google/fonts,
converted from TTF to WOFF2 without other changes (full character sets):
Inter, Figtree, Rubik, Bricolage Grotesque, Recursive, Fira Sans, Nunito,
Literata, Source Serif 4, Alegreya, EB Garamond, JetBrains Mono, DM Mono,
Pixelify Sans, VT323 and Comic Neue.
