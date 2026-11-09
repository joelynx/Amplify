# Drop-in packs

A pack is a folder with an `item.json` and its assets. It shows up in the
Wardrobe after a rebuild (or immediately with the dev server).

    packs/my-pixel-icons/item.json
    packs/my-pixel-icons/home.png
    packs/my-pixel-icons/quiz.png

`item.json` is one item or a list of items, same shape as `Item` in
`src/appearance/types.ts`. Paths inside `data` that start with `./` are
rewritten to the bundled file. What `data` holds depends on the slot:

| Slot | `data` |
|---|---|
| icons | `{ "icons": { "home": "./home.png", "quiz": "./quiz.png", … } }` (names: see ThemedIcon.tsx) |
| sfx | `{ "files": { "click": "./click.ogg", "correct": "./correct.ogg", … } }` (cues: see sound/engine.ts) |
| ambience | `{ "file": "./rain-loop.ogg" }` |
| wallpaper | `{ "image": "./day.webp", "night": "./night.webp" }` |

Example:

```json
{
  "id": "icons.my-pixel",
  "slot": "icons",
  "name": "My pixel icons",
  "description": "16×16 icons I drew.",
  "credits": [{ "what": "icons", "who": "Me", "license": "CC0" }],
  "data": { "icons": { "home": "./home.png", "quiz": "./quiz.png" } }
}
```

Formats and sizes: Makeover.md §12. The repo is public, so only commit assets
whose licence allows redistribution; keep others in a git-ignored folder.
