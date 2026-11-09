# Bundled fonts

Drop font files into a folder named after the family, exactly as the
typography items in `src/appearance/core/items.ts` spell it:

    fonts/Inter/Inter-VariableFont_opsz,wght.ttf
    fonts/Press Start 2P/PressStart2P-Regular.ttf
    fonts/Comic Neue/ComicNeue-Bold.ttf

`src/appearance/fonts.ts` registers every file at startup. Weight and style
come from the file name (Regular, Bold, SemiBold, Italic, VariableFont, …).
WOFF2 is smallest; TTF/OTF also work. A missing family just falls back to the
next font in the stack. Theme Lab (#/theme-lab) shows which ones are bundled.

The app is offline: never link fonts from a CDN. Use fonts whose licence allows
redistribution (SIL OFL, Apache 2.0); the repo is public. Keep each font's
licence file next to it (e.g. `fonts/Inter/OFL.txt`).
