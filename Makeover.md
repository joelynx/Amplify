# Amplify makeover: customization, whimsy and a two-currency economy

This is a proposal for:
- making Amplify's look, sound and feel customizable along many independent dimensions;
- giving every theme real personality;
- adding the club's identity;
- putting most of the extras behind an earned two-currency system that rewards learning, not grinding.

Nothing here is built yet. The owner sources the graphics, audio and fonts. This doc says what is needed, in what format, and where each piece goes.

Contents
1. Where theming stands today
2. Principles
3. Architecture: slots, items, loadouts
4. Club identity (ampliφ Mathematics Club and Coding Club)
5. The customization dimensions
6. Easter eggs and references
7. Theme-by-theme makeover
8. New theme ideas
9. The economy: Bits and QEDs
10. New screens and settings
11. Accessibility and wellbeing guardrails
12. Asset sourcing guide
13. Roadmap
14. Decisions for the owner

## Status (2026-11-09)

The owner chose to build all of the theming first and decide later which parts go behind currencies. Section 9 stays a proposal; the owner liked the split between a short-term "cram" currency and a long-lasting one.

Built (frontend/src/appearance/, styles/appearance/):
- Slots, items, presets and loadouts; the Wardrobe (Themes page: Presets, Wardrobe, Settings, Colours, Saved, Collection); saved loadouts with share codes; day/night switching; token overrides with live contrast checks; Theme Lab (#/theme-lab).
- Club logos drawn from the owner's SVGs in 11 variants, four matrix loaders and two small spinners, the boot animation, the nav logo, the Welcome and About placements, a club letterhead option for PDFs, and the app icon.
- Chrome, motion, surface, paper, cursor, icon, chart and arena skins; 34 palettes; 19 typography stacks (fonts load from frontend/fonts/ when bundled).
- Procedural sound effects, still wallpapers, the study room, easter eggs, seasonal events and results screens (built by parallel modules; see each folder).
- Drop-in packs (frontend/packs/) and fonts (frontend/fonts/), each with a README.

Not built: the currencies and shop (§9), titles and the profile card (§5.11), PDF cover styles beyond the letterhead (§5.16).

**Evidence check (2026-11-09).** The owner asked for every decorative part near the study surface to be justified by learning research, and for anything that isn't to go. Removed (code archived in the git-ignored `pipeline/outputs/_removed/appearance-20261109/`):
- **The companion** (§5.9): see that section.
- **Ambience** (§5.7): background music overall shows no benefit and hurts reading and memory tasks (Kämpfe, Sedlmeier & Renkewitz, 2011, meta-analysis); changing sounds such as crackle, birdsong or a melody disrupt verbal working memory. Steady noise only helps as a mask for nearby speech, which is office-acoustics research, not what was built.
- **Celebration bursts** (§5.10): feedback works through the information it carries (Wisniewski, Zierer & Hattie, 2020, meta-analysis); the text already says correct, partial or wrong with the credit, so a burst adds no information and competes for attention (coherence / seductive-details findings, e.g. Rey, 2012; Noetel et al., 2021).
- **Voice packs** (§5.8): a conversational style helps (Ginns, Martin & Marsh, 2013, meta-analysis), and the plain wording already is one; themed rewording of feedback adds no information and can blur it.
- **Wallpaper animation** (§5.4): motion onsets capture attention involuntarily (Abrams & Christ); wallpapers are now still images. Still wallpapers stay as a cosmetic choice, like palettes, with no claim that they help learning.
- **The Hyperlegible and OpenDyslexic fonts** (§5.2), removed at the owner's request: the font choices are for personality, not special-purpose fonts. OpenDyslexic's claim to help dyslexic readers is not supported: a study with dyslexic students found no gain in reading speed or accuracy over Arial or Times New Roman (Wery & Diliberto, 2017), and the one gain found for a dyslexia font came from its wider spacing, not its letter shapes (Marinus et al., 2016). High contrast and reduced motion stay, always free.

---

## 1. Where theming stands today

| Piece | What the spec promised | What exists |
|---|---|---|
| CSS overlay (§11.2) | Tokens, button/dialog/tooltip skins | 12 overlays. Each defines 11 colour tokens, a font stack and `--rem`. Default Light/Dark, Sage, Ember and Midnight are tokens only (17 lines each). The flavor themes add 2–4 rules that match on Tailwind class names (`section[class*="rounded-lg"]`) for cards, buttons and the chart tooltip. |
| Sprite pack (§11.2) | Thematic icons, cursor, navigation arrows per theme | `app/resources/sprites/` doesn't exist. About 45 lucide icons are identical in every theme. |
| Sound pack (§11.2) | `click`, `generate`, `error`, `success`, `theme_switch` per theme | `app/resources/sounds/` is empty. `playSound` is called in exactly one place (theme switch). The frontend never plays audio: `lib/theme.ts` still says "Future". The backend finds the file path but can't hand it to the page. |
| Token overrides (§11.3) | "The user can override any token without leaving the theme", in Settings | Not built |
| Fonts | Theme fonts named in CSS | No fonts are bundled. "Inter", "Comic Sans MS", "Cascadia Mono" and the rest fall back to whatever Windows has. The runtime is offline, so web fonts can't be loaded from a CDN. |
| Motion | none specified | Only `animate-spin` loaders |
| Brand | none specified | The nav shows the word "Amplify". No logo, app icon or splash; the boot screen says "Connecting to Python…" |
| Feedback moments | none specified | Correct, wrong, reveal, session end and unlocks are plain text |
| Rewards | none specified | 3 milestone themes (Sage, Ember, Midnight); no currency |

So a theme today is a palette swap plus a couple of border tweaks. The makeover turns a theme into a **bundle of independently swappable parts**, gives each part real content, and lets people mix the parts.

---

## 2. Principles

1. **The study surface comes first.** Math must be legible in every combination. Whimsy lives at the edges: chrome, transitions, the home room. It never goes inside the question text. A one-click Focus mode strips it all out.
2. **Modular.** Every cosmetic belongs to exactly one slot. A theme is a preset that fills the slots, and any slot can be swapped on its own.
3. **Earned by learning, not grinding.** The economy pays for behaviour the app already measures honestly in `answer_events` and the review scheduler: attempting before revealing, spaced reviews, comebacks, retiring questions. Raw volume and reveal-first earn little or nothing.
4. **Never gate function.** Currency buys looks, sounds and personality, never hints, shorter review intervals, more questions, stats or features. Accessibility options (high contrast, reduced motion) are always free.
5. **Respect the person.** No shaming copy. No streaks that punish a missed day. No permanent fear-of-missing-out. Sound is quiet by default.
6. **Offline and fail-soft.** Every asset is local, and every slot falls back to the default when an asset is missing (as the spec already says for sounds).
7. **Homage, not copies.** Spec §11.4 already says flavors evoke an era and don't ship trademarked art or sounds. The repo is public, so anything committed is redistributed. Game references stay as short text nods and original art "in the style of", never ripped sprites, sounds or logos.

---

## 3. Architecture: slots, items, loadouts

### 3.1 Slots

A **slot** is one dimension of customization. Each slot has a default that is always owned.

| Group | Slot | Changes |
|---|---|---|
| Look | `palette` | The 11 colour tokens, plus the new ones (selection, math ink, scrollbar) |
| | `typography` | UI, heading and mono fonts; numeral style |
| | `chrome` | Corner radius, border weight, shadow style, bevels/glass/ink, button and input skins, scrollbars, progress bars, toggles |
| | `surface` | A tiled texture behind cards (graph paper, slate, parchment, scanlines) |
| | `wallpaper` | A still scene behind the app; has time-of-day variants |
| | `icons` | Thematic icon set (see §5.5) |
| | `cursor` | Pointer, text and busy cursors |
| | `motion` | Transition personality: springy, stepped, glassy, typewriter, none |
| Sound | `sfx` | UI and feedback sound pack |
| | `results` | Session-end screen style |
| Identity | `title`, `frame`, `nameplate`, `showcase` | Profile card on Home |
| Places | `room` | Home study-room theme and furniture |
| | `arena` | Quiz skins: PBS board, timer, answer box |
| | `paper` | Question-card paper and math ink colour |
| | `charts` | Heatmap, line and pie skins on Stats |
| Print | `pdf` | PSet letterhead, cover page and font set |
| Meta | `currency_icons` | How Bits and QEDs are drawn (coin, chalk, gem, …) |

### 3.2 Items and the manifest

Each cosmetic is an **item**: a folder with an `item.json` and its assets. A registry discovers the folders at startup.

```json
{
  "id": "pixel.icons.16bit",
  "slot": "icons",
  "name": "16-bit Toolkit",
  "description": "Chunky 16×16 icons for the nav and quiz buttons.",
  "set": "pixel-art",
  "rarity": "rare",
  "price": { "bits": 600 },
  "unlock": "purchase",
  "assets": { "atlas": "icons.png", "map": "icons.json" },
  "credits": [{ "what": "icons", "who": "…", "license": "CC0", "url": "…" }],
  "tags": ["pixel", "retro"]
}
```

The `unlock` field takes one of `starter`, `purchase`, `milestone:<id>`, `secret:<egg>` or `seasonal:<window>`.

- The `credits` block feeds an auto-generated credits list on the About page, so licence attribution never gets forgotten.
- Assets ship inside the frontend bundle (`frontend/public/packs/<item>/`) so that `<img src>` and audio elements work on the `file://` page PyWebView loads. Test audio under WebView2 on `file://` early: `fetch()` of local files can be blocked, while `HTMLAudioElement` and Vite-imported URLs normally work.

### 3.3 Loadouts and presets

- A **theme becomes a preset loadout**: a curated value for every slot.
- Applying a theme offers "apply everything" or "keep my …" for slots you have customized. For example, take the XP preset but keep the pixel cursor.
- **Saved loadouts** work like Generate templates: named, editable, one active.
- **Context loadouts** (optional): a calm loadout for Review and Lecture sessions, a loud one for PBS and Integration Bee, a printer-friendly one for Generate.
- **Day/night**: switch between two loadouts at set times, or follow the Windows light/dark setting.
- **Loadout codes**: a short copyable string, so club members can share setups. It only references items; you still need to own them.

### 3.4 Frontend mechanics

1. **Compose slots with separate attributes on `<html>`**:
   - `data-palette`, `data-chrome`, `data-type`, `data-motion`, `data-surface`, `data-paper` and so on.
   - Each slot's CSS keys only on its own attribute, so any palette works with any chrome.
   - Today everything hangs off a single `data-theme`.
2. **Expand the tokens.** Add:
   - radius scale (`--radius-sm/md/lg`), `--border-w`, `--shadow-card`, `--shadow-pop`, `--focus-ring`, `--density`;
   - `--font-heading`, `--font-mono`, `--motion-fast/slow`, `--ease`;
   - `--surface-texture`, `--math-ink`, `--selection`, `--scrollbar`.
3. **Replace the class-name selectors with component hooks.**
   - `Card`, `Button`, `Modal`, `Input`, `Switch`, `Tooltip`, the progress bars and the nav carry `data-ui="card|button|…"` and read the tokens above.
   - Chrome packs then skin components directly instead of matching `[class*="rounded-md"]`, which breaks whenever a class changes.
4. **`<ThemedIcon name="generate" />`.** Semantic names map to the active icon set, falling back to lucide.
   - This keeps the spec's split: thematic icons swap, functional icons (close, chevrons in dense tables) stay neutral.
5. **Sound engine.** Preload the active pack and play through an event bus:
   - Channels: UI, feedback, and session ends and unlocks; each has its own volume and mute.
   - Keep the backend `play_sound` call only for logging, or drop it.
6. **Effects layer.** Removed in the evidence check (celebration bursts; see the status note).
7. **Theme Lab** (dev page): the owner's workbench for sourced assets.
   - Point it at a pack folder on disk; it hot-reloads.
   - It shows every surface at once: a study preview (reuse `StudyPreview` from Themes), buttons, dialogs, toasts, charts, the PBS grid and the results screen.
   - It runs WCAG contrast checks on every text/background pair and math ink on paper.
   - It lists missing assets per slot.
8. **Personal packs folder** (`%APPDATA%\Amplify\packs\`): your own wallpaper photo, palette or sounds. They're yours, so they're free and skip the shop. A user wallpaper gets an automatic dim/blur layer so text keeps contrast.

### 3.5 Backend

- `app/theming/` grows an item registry (manifest discovery and validation) next to `theme_registry.py`.
- New IPC:
  - `list_items(slot?)`, `get_loadout`, `set_loadout`, `save_loadout`
  - `get_wallet`, `purchase(item_id)`, `get_ledger(range)`
  - `list_discoveries`, `report_discovery(egg_id)`
- New tables are in §9.12. They need migration 010.

---

## 4. Club identity (ampliφ Mathematics Club and Coding Club)

Amplify is an offering of two clubs: ampliφ, the Mathematics Club (its logo is a LaTeX diagonal matrix, diag(amp(z), li(x), φ(n)), with an inline form "ampliφ @iitd-ad"), and the Coding Club ("CODING CLUB", black and yellow). The marks should be visible but tasteful.

| Place | Treatment |
|---|---|
| App icon | Window and taskbar icon (PyWebView `icon`), installer icon. Built from a square mark, exported to `.ico` at 16–256 px. |
| Boot screen | Replace "Connecting to Python…" with the logo animating in (a draw-on stroke, or a pulse) while the bridge connects. |
| Nav bar | A small mark beside "Amplify"; clicking it goes Home. Seven clicks is an easter egg (§6). |
| Welcome hero | The matrix logo with "a ampliφ × Coding Club offering" under it. |
| About page | A club section: what the club does, contributors, maintainers, how to join. The auto-generated asset credits list sits below it. |
| Loading spinner | The default spinner becomes the logo mark (rotating, or a draw-on stroke) wherever `Loader2` spins today. |
| PSet PDFs | Optional letterhead with the club logo in the `fancyhdr` header, plus a small footer line. XeLaTeX can't include SVG, so the build converts the SVGs to PDF (cairosvg or Inkscape) and the preamble `\includegraphics` those. It is a toggle in Output settings. |
| Study room | A club pennant or poster on the wall of the home room (§5.12), and a club mug on the desk. |
| Idle screensaver | The bouncing-logo screensaver (§6) uses the club mark. |
| Per-theme treatments | The logo restyled for each theme: a pixelated mark for Pixel Art, box-drawing ASCII art for ASCII, an inked outline for Comic, glossy for Frutiger Aero, a beveled tile for XP. A single-colour SVG drawn in `currentColor` covers most of these with CSS; the rest are hand-made variants. |
| Club theme | A free preset built from the club colours, used for club events and the default Amplify look. |
| Club events | An owner-editable calendar file (contest days, Integration Bee, club anniversaries). On those days the club skin, a banner and a one-day item appear (§5.17). |

**Needed from the owner:** the club SVGs. The variant list is in §12.3.

---

## 5. The customization dimensions

### 5.1 Palette
- A light, dark and high-contrast variant of every theme, switched with the day/night loadout.
- **Custom palette editor** (owed by spec §11.3):
  - Pick any token and see a live preview.
  - Contrast warnings appear inline, and a palette can't be saved if body text fails WCAG AA.
  - Saved palettes become personal items.
- **Palette from wallpaper**: offline colour quantization proposes a palette from an image.
- **Code-editor palettes** for the coding side of the club: Dracula, Nord, Catppuccin (four flavours), Gruvbox, Solarized, Tokyo Night, One Dark. These are MIT-licensed palettes; credit them.
- **Retro palettes**: four-shade handheld green, an amber or green CRT, a 16-colour fantasy-console style, and Lospec community palettes. Check each palette's licence on Lospec.
- **New tokens**: text-selection colour, math ink, link colour, scrollbar thumb.

### 5.2 Typography
- Four sub-slots: UI font, heading font, mono font (answers, IDs, code), and tabular numerals for stats.
- Bundle each font locally as WOFF2, subset to the scripts needed, all under the SIL Open Font License. Suggestions per theme are in §7.
- Math keeps the KaTeX fonts. Only the math ink colour and size change, so formulas stay correct.
- Always free (accessibility, not cosmetics): a larger-text scale. The Hyperlegible and OpenDyslexic fonts were dropped (see the evidence check at the top).

### 5.3 Chrome
- **Corner and border styles**:
  - flat;
  - soft-rounded;
  - hard offset shadow (neo-brutalist);
  - beveled (XP);
  - glass (Aero);
  - stepped pixel corners (`clip-path` or `border-image`);
  - wobbly ink (an SVG turbulence filter for a hand-drawn line);
  - torn-paper edges.
- **Card title bars** in the XP chrome:
  - real minimize and close buttons that collapse or hide the card;
  - a pinned "restore hidden cards" tray.
- **Controls**:
  - progress bars: XP segmented green blocks, pixel HP bar, glossy Aero pill, ASCII `[#####-----]`;
  - toggles, checkboxes, sliders, dialogs, toasts, scrollbars and focus rings per chrome;
  - nav layouts: top bar (today), left rail, XP-style bottom taskbar with a "start" pill and tray clock, or a pixel-game menu.

### 5.4 Surfaces and wallpapers
- **Tiled textures**: graph paper, dot grid, engineering paper, ruled notebook with a red margin, blackboard slate, cork board, parchment, blueprint grid, halftone, CRT scanlines.
- **Wallpapers**:
  - a full scene per theme;
  - optional per-page variants (Quiz calmer than Home);
  - parallax layers;
  - time-of-day and seasonal variants of the same scene (dawn, day, dusk, night).
- **Animated wallpapers**: removed in the evidence check. Procedural scenes paint one still frame.

### 5.5 Icons, sprites and cursors
- **Thematic icon set**: one icon for each of these semantic names:
  - navigation: `home`, `generate`, `quiz`, `browser`, `history`, `stats`, `settings`;
  - quiz: `hint`, `reveal`, `bookmark`, `note`, `submit`, `next`, `back`, `timer`, `review`;
  - feedback: `success`, `error`;
  - currencies: `bits`, `qed`;
  - `loading`.
- **Styles**:
  - pixel 16×16;
  - glossy 32 px XP-era;
  - comic doodles;
  - ASCII glyph icons (`[#]`, `$_`, `<>`);
  - Aero orbs;
  - botanical line art for Sage.
- **Cursors**: a chalk stick, a pixel arrow with a busy hourglass while a PDF compiles, a quill (Ember), a pointing glove (Comic), a block caret (ASCII).
- **Loaders**: a pixel coin flip, a spinning Σ, a Möbius strip, a compass, an hourglass, typing dots, or the club mark.
- **Empty-state art for each page**: no PSets yet, no reviews due ("all caught up"), no bookmarks, no search results.
- **Currency icons for each theme**: Bits as a pixel coin, a chalk stub, a glass bead or a `0b1`; QEDs as a gem, a wax seal or a `∎` stamp.
- **Decorations**: ornamental dividers and list bullets (fleurons for parchment, `>` for ASCII).

### 5.6 Motion
- **Personalities**:
  - springy overshoot (Pastel);
  - `steps(4)` frame-stepped (Pixel);
  - soft glass fades (Aero);
  - a typewriter reveal for headings (ASCII);
  - panel pops with speed lines (Comic);
  - none (Focus).
- **Where motion appears**: page transitions, staggered card entrance, number roll-ups on stat tiles, charts drawing in, the tick of a review being cleared.
- **Limits**: everything obeys `prefers-reduced-motion` and the whimsy dial, and nothing flashes more than 3 times a second.

### 5.7 Sound

Event catalogue. These are the file names a sound pack provides; missing files fall back to the default pack, then to silence.

| Event | When |
|---|---|
| `click`, `toggle`, `nav` | UI basics (hover sounds exist but are off by default) |
| `correct`, `partial`, `wrong` | Answer feedback. `wrong` is soft and never a buzzer. |
| `combo` | Consecutive unaided correct answers in a session; played with rising pitch, Peggle-style |
| `hint`, `reveal`, `bookmark`, `note_saved` | Practice actions |
| `session_start`, `session_end` | Quiz bookends |
| `tick`, `time_up` | The last 10 s of a timed quiz, and expiry |
| `generate_done`, `generate_error` | PSet compile result |
| `earn_bits`, `earn_qed` | Currency gain, with two distinct timbres so you can hear which one |
| `purchase`, `unlock`, `egg_found` | Economy and discovery |
| `review_due` | One chime when the app opens with reviews due |
| `theme_switch` | Already exists |

- **Packs**:
  - chiptune bleeps (Pixel; make them in sfxr/jsfxr/ChipTone, and you own the output);
  - glassy chimes (Aero);
  - soft marimba (Pastel);
  - mechanical-keyboard clicks (ASCII);
  - pencil scratch, page turn and chalk tap (Sage, Ember, Blackboard);
  - whoosh and pop (Comic);
  - an original early-2000s "desktop" set for XP.
- **Ambience and music loops**: removed in the evidence check.
- **Mixer** in Settings: master, UI, feedback, and session ends and unlocks. Defaults are low.

### 5.8 Voice (copy packs) (removed)

Themed rewordings of feedback ("CRITICAL HIT!", "Operation completed successfully.") were built and removed in the evidence check. The app keeps one plain, conversational wording.

### 5.9 Companion (removed)

A corner mascot that reacted to answers was built and then removed on 2026-11-09. It was added for personality, not on evidence. Animated pedagogical agents do show small learning gains, but in that research the agent explains or guides; this one was barred from giving hints, which makes it a decorative addition. For decorative additions that are interesting but irrelevant to the lesson, the "seductive details" research mostly finds a small cost to learning. The self-explanation prompts it would have fronted are still in `QuestionNotes.tsx`.

### 5.10 Celebrations and feedback

- **Celebration bursts** on answers, session ends and unlocks were removed in the evidence check. Answer feedback is the text that states the result and the credit; a partial answer reads as partial.
- **Wrong** answers get no shake and no full-screen red.
- **Easter-egg moments** (the "QED ∎" stamp, achievement toasts) stay with the easter eggs.

### 5.11 Results screens (session end)

Styles the `results` slot can take:
- a **JRPG victory screen**: "QUIZ CLEAR!", an EXP tally, and the "items dropped" being the Bits and QEDs earned;
- **arcade high score**: personal bests only, with initials entry;
- a **newspaper front page** (Comic/Ember): "STUDENT CRACKS EIGENVALUES, CITY REJOICES";
- a **terminal log** (ASCII): a timestamped summary with `exit 0`;
- an **XP dialog** with a progress bar and "Finish" button;
- a **report card** (Default).

Every style shows the same honest numbers as `QuizReview`: attempted, unaided, with help, missed, and what goes into the review queue.

### 5.12 Home: the study room

The Welcome page can become a customizable room, the hub where cosmetics live. It works like a cozy room-decorating game.

- **Furniture and décor** are bought with Bits.
- **Bookshelf**: one book per topic, getting thicker as questions in that topic retire.
- **Trophy shelf**: milestones and titles.
- **Plant**: grows with spaced reviews. It never wilts; with no recent reviews it goes dormant and sprouts again.
- **Window**: shows the current time of day and the season.
- **Noticeboard**: today's reviews as sticky notes (the TodayCard data).
- **Club pennant and mug** (§4).
- **Clickable objects navigate**: door → Quiz, printer → Generate, filing cabinet → History, chart on the wall → Stats, bookcase → Browser.
- **Room themes**: dorm, library, observatory, treehouse, spaceship, pixel cabin, or an "XP desktop" whose objects are desktop icons.
- **Lighter alternative** if the room is too much: Home as widgets (profile card, today, exam countdown, quote) with layout presets.
- **Personal touches**: your name in the greeting ("Good evening, <name>"), a pinned motto, and an exam-countdown widget for a date you set.

### 5.13 Quiz arena skins
- **PBS boards**: chalkboard, arcade cabinet, game-show board, tavern quest board (each question a notice pinned to it), periodic-table tiles.
- **Timers**: hourglass, burning fuse, chess clock, draining pixel HP bar, sun crossing the sky.
- **Answer boxes**: chalk line, terminal prompt `> `, speech bubble, notebook line.
- **Traverse as an overworld map**: questions are nodes along a path that light up as you go, like a generic platformer world map.

### 5.14 Question paper and math ink
- **Card backgrounds**: ruled notebook, graph paper, blackboard (math in chalk white or yellow), parchment, index card, terminal, blueprint (white on blue).
- **Solution reveal styles**: scratch-off, paper unfold, envelope, a CRT "decrypt" animation.
  - A reveal still logs a `revealed` event.
  - Keep the reveal animation neutral, so the attempt-first path stays the more rewarding one.
- **Notes**: highlighter colours and margin doodles.

### 5.15 Chart skins
- **Heatmap**:
  - a night sky where days are stars, brighter with more activity;
  - a garden where flowers bloom;
  - pixel tiles;
  - ink stamps;
  - a contribution graph like a code-hosting site's (for the coding club).
- **Activity line**: hand-drawn (rough.js-style) for Comic and Pastel, phosphor glow for ASCII, glossy for Aero.
- **Pie**: pixel pie, donut, and a pizza on Pi Day.
- **Tooltips**: the per-theme chart tooltip skins that already exist get richer versions.

### 5.16 PDF cosmetics
- **Letterhead**: club logos plus an optional custom title line. The header variables (`<S>`, `<D>`, `<P>` …) already exist.
- **Cover page styles**: exam paper, worksheet, contest (Integration Bee bracket), problem-of-the-week.
- **Font sets**: these must be fonts that exist in the bundled TinyTeX; check before offering one.
- **Ornament**: optional ornamental rules between questions and a faint "Amplify · Math & Coding Club" watermark.
- **Keep it printable**: doodles are off by default and light on ink. Print styles could be free, since they affect real use; deciding that is the owner's call.

### 5.17 Seasonal and calendar events

Events switch on automatically in a date window, can be turned off in Settings, and return every year. Lunar-calendar festivals need a pre-computed date table shipped with the app (offline).

| Date | Event | Idea |
|---|---|---|
| 7 Feb | e Day (2/7…) | Exponential-growth particle effect; an "e" item |
| 14 Mar | Pi Day | Pie charts become pies; π digits scroll in the loader; "3.14 pm" egg |
| 23 Mar | Emmy Noether's birthday | Symmetry-themed wallpaper; quote |
| 15 Apr / 30 Apr | Euler's / Gauss's birthdays | Quote cards; small Bits gift |
| 25 May | Towel Day | "Don't panic" on the error screen |
| 23 Jun | Alan Turing's birthday | Coding-club skin; tape-machine loader |
| 28 Jun | Tau Day | A smug τ reskin of Pi Day |
| 22 Jul | Pi Approximation Day (22/7) | — |
| 256th day (13 Sep, 12 in leap years) | Programmers' Day | `0x100` banner; terminal skin discount |
| 2nd Tue of Oct | Ada Lovelace Day | Analytical Engine wallpaper |
| 23 Oct | Mole Day | Chemistry subjects get a skin (6:02 egg) |
| 31 Oct | Halloween | Spooky decorations |
| 23 Nov | Fibonacci Day | Golden-spiral loader |
| 2 Dec | UAE National Day | Flag-colour palette, optional |
| 9 Dec | Grace Hopper's birthday | "First actual case of bug being found" moth egg |
| 22 Dec | Ramanujan / National Mathematics Day (India) | 1729 taxicab card |
| Lunar dates | Diwali, Eid al-Fitr, Eid al-Adha | Lamps and lanterns décor, optional |
| Owner-set | Exam season | Calm mode: whimsy turned down, encouraging copy |
| Owner-set | Club contest / Integration Bee day | Bracket board, buzzer sounds, club banner |

---

## 6. Easter eggs and references

Found eggs go into a **Collection log** with `???` silhouettes for undiscovered ones, which drives discovery. Many grant a Secret item or a title. Eggs never touch grading, the learning record or real data.

**Global**
- **Konami code** (↑↑↓↓←→←→BA) anywhere: a CRT scanline overlay unlocks, plus the title "Cheat Code".
- **Click the nav logo 7 times**: "You are now a developer!", a nod to Android's build-number trick. Signature egg for the KitKat theme.
- **Idle for 5 minutes**: the club logo bounces around the screen like an old DVD player. If it hits a corner exactly, you get a title.
- **Answer at 3:14 or 15:14**: the π badge. **At 13:37**: the "leet" title.
- **Fermat's margin**: fill a note to its length limit and it says "I have discovered a truly marvelous proof of this, which this margin is too narrow to contain."
- **QED stamp**: end a self-explanation with "QED" or "∎" and a tombstone stamp lands.
- **"quack"**: typed anywhere, it summons the rubber duck.
- **Late at night** (after 2 am): a one-time note suggests sleep. This is deliberately not a reward (§11).

**Browser search eggs.** The real search still runs; a small card appears above the results.

| Query | Card |
|---|---|
| `42` | "The answer. Now, what was the question?" |
| `1729` | The Hardy–Ramanujan taxicab story |
| `xyzzy` | "Nothing happens." |
| `sudo` / `rm -rf` | "Nice try." / "Not today." |
| `hello world` | A card says hello back |
| `P=NP` | "Proof left as an exercise to the reader." |
| `Riemann` | "Still open. Get to work." |
| `Erdos` | "Erdős number of this app: ∞" |
| `coffee` | "A mathematician is a machine for turning coffee into theorems." |
| `do a barrel roll` | The page spins once (skipped with reduced motion) |

**Per theme**
- **XP**: on closing the app, "It is now safe to turn off your computer" (original art). Recording a full PSet's paper results triggers a solitaire-style card cascade.
- **Pixel**: a hidden "warp zone" in the Browser pagination. The Traverse map has a secret node.
- **Comic**: random "Meanwhile…" caption cards between Traverse questions.
- **ASCII**: a `fortune`-style daily quote and a falling-glyph screensaver.
- **Pastel**: clicking the clouds makes them rain sprinkles.
- **Ember**: every comeback makes the embers flare.
- **Sage**: the rarest flower blooms after your 50th retired question.

**Game and internet nods.** These are short text homages; the owner decides which to keep.
- "It's dangerous to go alone! Take this." when a hint opens.
- "Hey! Listen!" on the review-due chime.
- "Stay a while and listen" at the top of Tutorial.
- "The cake is a lie" when the Tutorial is finished.
- "A winner is you!" on a perfect PBS run.
- A "TIME'S UP" banner in the style of a famous death screen when a timed quiz expires.

**A hidden theme**: Vaporwave ("A E S T H E T I C") unlocks after finding 10 eggs.

---

## 7. Theme-by-theme makeover

Each preset fills every slot. Font suggestions are OFL fonts unless noted.

**Default Light / Default Dark → "Amplify" house style**
- Palette: tuned to the club colours. Stays WCAG AA.
- Typography: Inter, actually bundled. JetBrains Mono for answers and IDs.
- Chrome: crisp and quiet. Motion: short fades. Sounds: soft, low clicks.
- Identity: the club mark appears in the nav, the loader and the boot screen.
- Results: report card. Copy: plain.
- This is the theme for people who want polish without flavor.

**Pastel → kawaii stationery**
- Fonts: Quicksand or Nunito.
- Chrome: washi-tape corners on cards, sticker-style icons, cloud and confetti-dot textures.
- Sounds: marimba.
- Copy: gentle lowercase.
- Egg: clouds rain sprinkles.

**Frutiger Aero → glossy optimism**
- Fonts: Nunito Sans, or system Segoe UI (Frutiger itself is commercial).
- Wallpaper: sky, water, grass and bubbles, with lens-flare highlights.
- Icons: glossy orbs. Progress bars: glass pills.
- Sounds: glassy chimes.
- Egg: the fish follows the cursor.

**Pixel Art → 16-bit adventure**
- Fonts: Press Start 2P for headings, Silkscreen or VT323 for UI.
- Chrome: stepped-corner borders, HP-bar progress, 16×16 icons, pixel cursor.
- Sounds: sfxr coin and jump sounds.
- Results: JRPG victory screen.
- Arena: Traverse as an overworld map.
- Option: a CRT scanline overlay.
- Egg: the warp zone.

**Windows XP → early-2000s desktop**
- Wallpaper: an original rolling-hills scene.
- Chrome: beveled cards with title bars; optional bottom taskbar nav with a start pill and tray clock.
- Notifications: balloon pop-ups from the tray ("You have 3 reviews due").
- Fonts: system Tahoma on Windows, which is installed but not ours to bundle.
- Sounds: an original start-up chime set.
- Results: dialog style.
- Eggs: the solitaire cascade and the "safe to turn off" screen.

**Comic → Saturday-morning ink**
- Fonts: Bangers for headings, Comic Neue or Patrick Hand for UI.
- Chrome: halftone textures, a wobbly ink border filter, panel-gutter layouts, speech bubbles everywhere.
- Sounds: whoosh and pop.
- Results: newspaper front page.
- Egg: "Meanwhile…" captions.

**ASCII → terminal**
- Fonts: VT323 or IBM Plex Mono.
- Palettes: green, amber and white phosphor variants.
- Chrome: box-drawing borders (`┌─┐`), a blinking block caret, typewriter reveals, optional scanlines (flicker off by default).
- Sounds: keyboard clicks.
- Results: log file.
- Eggs: the `fortune` quote and the falling-glyph screensaver.

**Android KitKat → early mobile**
- Fonts: Roboto.
- Chrome: flat cards and toasts; reviews due come down as a notification shade from the top.
- Sounds: soft taps.
- Egg: logo × 7 gives "You are now a developer!" and unlocks a tile-swirl animation.

**Sage (earned with spaced reviews) → botanical study journal**
- Fonts: Fraunces or Source Serif 4.
- Chrome: pressed-leaf textures, botanical line icons.
- Home: the room's plant is the centerpiece, and the heatmap becomes a garden.
- Sounds: pencil and paper.

**Ember (earned by fixing old mistakes) → candlelit comeback**
- Fonts: EB Garamond or Crimson Pro.
- Chrome: warm paper texture and candlelight vignette.
- Motif: the phoenix, a comeback rising from the ashes. Ember particles on comebacks, wax-seal stamps on unlocks.

**Midnight (earned with honest attempts) → observatory**
- Fonts: Space Grotesk.
- Wallpaper: a deep-navy star chart, with constellation lines linking cleared reviews. The heatmap is a night sky.

---

## 8. New theme ideas

These are mostly QED-priced presets (§9).

| Theme | Concept |
|---|---|
| Blackboard | Slate texture, chalk fonts, chalk-dust particles, eraser-swipe transitions |
| Engineer's notebook | Green engineering paper, technical pen lines, drafting-compass loader |
| Blueprint | White line work on blue, dimension-line dividers |
| Illuminated manuscript | Parchment, drop caps, "Euclid's Elements" ornaments |
| Dark academia | Leather, brass, a quiet library |
| Vaporwave (secret) | Pink/cyan grid sunset, marble busts, slowed-down chimes |
| Synthwave | Neon grid, chrome type, retro drive music |
| Handheld green | Four-shade green LCD look, dot-matrix font |
| Amber CRT | Monochrome amber terminal |
| Code editor | Pick a palette (Dracula/Nord/Catppuccin…), line-number gutter on cards, minimap scrollbar |
| Lo-fi study café | Rainy window, steaming mug |
| Cozy farm | Seasons and crops; spaced reviews water the crops |
| Solarpunk | Greenery, sun, optimistic architecture |
| Bauhaus | Primary shapes, geometric sans, grid |
| Brutalist | Raw borders, system mono, no rounding |
| Origami | Folded-paper cards and fold transitions |
| Observatory+ | Planetarium wallpaper (an upgrade on Midnight) |
| Desert night | Dunes, stars, lanterns; a nod to the Abu Dhabi campus |
| Sakura | Spring petals; a seasonal return every March–April |
| Club edition | Club colours, logo-pattern texture, unlocked at club events |

---

## 9. The economy: Bits and QEDs

### 9.1 Goals
1. Reward the behaviour that makes learning stick, using the signals Amplify already records: an attempt before a reveal, unaided success, delayed reviews, comebacks, retirements.
2. Keep two kinds of progress apart: **showing up** (effort) and **learning that lasted** (mastery).
3. Make grinding pointless. Spacing is time-gated by the scheduler, so the scarce currency can't be farmed in one sitting.
4. Never sell function (§2). No real money.

### 9.2 The two currencies

| | **Bits** (soft) | **QEDs ∎** (hard) |
|---|---|---|
| Flavor | Coding club: small, plentiful, binary | Mathematics club: the end-of-proof tombstone, "proof you learned it" |
| Earned by | Honest effort: attempting, finishing sessions, recording paper results, self-explaining | Mastery: spaced-review success, comebacks, retiring a question, hard first-try solves, milestones |
| Rate | Several dozen to ~100 a day | 0 in the first days, then a handful a day once reviews come due |
| Buys | Common and mid-tier cosmetics: cursors, outfits, furniture, sound packs, wallpapers, textures | Prestige: new themes, room themes |
| Exchange | None in either direction. QEDs must keep meaning "learned". |

Alternative names, if Bits/QEDs don't land: Chalk / Halmos (∎); Ink / Seals; Coins / Stars.

### 9.3 Earning Bits

| Rule | Bits | Notes |
|---|---|---|
| Answer a question without revealing first | 2 | Any result counts: effort, not correctness |
| …and solve it unaided (full credit, no hint) | +2 | Partial credit unaided: +1 |
| Finish a session (≥5 questions that earned Bits) | 10 | |
| First session of the day | 15 | A daily welcome, not a streak |
| Record paper results for a PSet | 1 per question | Once per PSet, up to 30 |
| Write a self-explanation of ≥80 characters after a solution | 2 | Up to 5 a day; backs the self-explanation prompts |
| Revealing before answering | 0 | |
| Re-answering a question within 7 days of solving it unaided | 0 | The same "massed repeat" rule the reuse-pressure trend uses |

**Soft cap:** full rate up to 200 Bits a day, half rate after that, so a 6-hour cram isn't worth six normal days.

### 9.4 Earning QEDs

| Rule | QEDs | Notes |
|---|---|---|
| Spaced-review success: unaided, at least 1 day after the question was last seen | 1 | The same definition as "delayed review" in `review.py` |
| Comeback: unaided success on a later day after a miss or partial | 2 | Replaces the 1 above |
| Retire a question (clears the 21-day rung) | +2 | |
| First-try unaided in the 15–20 difficulty band, auto-graded | 1 | |
| Clear the due queue on a day that started with ≥5 due | 1 | Once a day |
| Milestones | 5–20 | Once each; the existing three plus new ones |
| Onboarding quest: "come back tomorrow and do your first review" | 3 | The first QED teaches the spaced loop itself |

**Honesty caps.** Self-assessed answers and recorded paper results still schedule reviews normally, but together they earn at most 3 QEDs a day. Auto-graded answers are uncapped.

### 9.5 Pacing estimates

These are rough steady-state numbers after the first three weeks. Tune them with the simulator (§9.12) against real `answer_events`.

| Persona | Pattern | Bits/week | QEDs/week |
|---|---|---|---|
| Steady | ~20 questions a day, 5 days a week, does reviews when due | ~500 | ~40–80 |
| Casual | ~10 a day, 3 days a week | ~170 | ~10–20 |
| Crammer | 150 questions in one weekend, never reviews | ~500 (in 2 days) | ~3–5 |
| Grinder | Repeats questions already solved | ~100 (daily bonus only) | 0 |

The crammer earns Bits but almost no QEDs; the steady reviewer earns both. That is the intended shape.

### 9.6 Prices

| Tier | Price | Examples |
|---|---|---|
| Common | 60–150 Bits | Cursor, single wallpaper, recolour, currency icon style |
| Uncommon | 200–450 Bits | UI sound pack, tiled texture, chart skin, timer skin, furniture set |
| Rare | 500–900 Bits | Icon set, results screen, paper style, PDF cover style |
| Epic | 60–150 QEDs | Full new theme preset, room theme |
| Legendary | Bits **and** QEDs (e.g. 1,000 + 80) | Animated room |
| Secret | Not for sale | Easter-egg finds |
| Earned | Not for sale | Titles, milestone themes, badges |

- **Sets**: owning every slot of a theme set unlocks a set bonus, such as an animated variant or a title. A whole preset bought at once costs about 20% less than its parts.
- **Wishlist**: progress bars toward wished items ("47 / 80 QEDs").

### 9.7 Unlock paths

1. **Starter**: free and always owned.
2. **Purchase**: with Bits, QEDs or both.
3. **Milestone**: the existing three themes, plus new ones. Not for sale; they're badges of learning.
4. **Secret**: easter eggs.
5. **Seasonal**: buyable only during the window, and returning every year, so nothing is lost forever.

### 9.8 What happens to today's themes
- All 12 current theme palettes stay free; nothing that's free today gets taken away.
- Sage, Ember and Midnight stay milestone unlocks.
- The new deluxe parts of each theme (sound packs, sprites, wallpapers, results screens) are shop items.
- **Retro grant**: when the economy ships, history already in `answer_events` pays out once, with a "back pay" receipt. It is idempotent, so it can never pay twice.

### 9.9 Shop design
- **Browsing**: by slot, by set, or by theme.
- **Fitting room**: try anything on for 10 minutes before buying. The Themes `StudyPreview` grows into a full try-on preview.
- **Featured shelf**: rotates weekly from a seed derived from the date (offline and deterministic). Every featured item returns regularly.
- **Undo purchase**: possible within 5 minutes, for misclicks.
- **No randomized boxes.** If a mystery item is ever added, its pool is shown, there are no duplicates, and it costs Bits only.

### 9.10 Weekly goals and quests
- **Weekly consistency** instead of streaks: "Study on 4 of 7 days" pays a bonus. Rest days cost nothing, and missing a week resets nothing.
- **Gentle weekly quests** that point at good habits:
  - "Do reviews on 3 different days";
  - "Revisit 2 old mistakes";
  - "Record results for a printed PSet";
  - "Try a mixed review".
- **A 7-day onboarding chain** that teaches the loop: first quiz → first review the next day → first comeback → first lecture set.

### 9.11 What we will not do
- Sell or gate hints, review intervals, question counts, stats or any feature.
- Pay for reveals, or for repeats in a short window.
- Punish streak losses, or show "you lost X".
- Use leaderboards. It's single-user anyway, and comparison demotivates most learners.
- Run timed FOMO sales on items that never return.
- Use real money.

### 9.12 Honesty, data model and tuning

**Honesty.** It's an offline app with a local SQLite file; anyone can edit their balance. The design doesn't police that. It makes the honest route the fastest one: reveal-first earns nothing, self-assessed QEDs are capped, and spacing can't be rushed.

**Data model** (migration 010):

```sql
wallet_ledger(entry_id PK, currency TEXT CHECK (currency IN ('bits','qed')), amount INTEGER,
              rule_id TEXT, source_key TEXT, rules_version INTEGER, occurred_at TEXT,
              UNIQUE (rule_id, source_key))       -- idempotent payouts
inventory(item_id PK, acquired_at, via TEXT CHECK (via IN ('starter','purchase','milestone','secret','seasonal','retro')))
loadouts(loadout_id PK, name, slots_json, active INTEGER)
discoveries(egg_id PK, found_at)
```

**Payouts.**
- Balances are `SUM(amount)`; spending is a negative ledger row.
- A pure `app/core/economy.py`, like `review.py`, turns new events and state transitions into payouts.
- It hooks into `_practice_answer`, `quiz_finish`, `record_paper_results` and the review state change.
- `source_key` is something like `event:1234` or `retire:qid:567`, so replaying never pays twice.
- `rules_version` lets the rates be retuned without rewriting history.

**Simulator** (`tools/economy_sim.py`):
- Replays real `answer_events`, plus the synthetic personas from §9.5, through the rules.
- Prints Bits/QEDs per week and days-to-first-epic per persona.
- Checks that a grinder never out-earns a steady reviewer in QEDs.

---

## 10. New screens and settings

- **Wallet chip in the nav**: Bits and QEDs with the theme's currency icons. Click it for the ledger.
- **Earn toasts**: small, themed, merged when several arrive ("+6 Bits, +1 ∎").
- **Session receipt** on the results screen: what was earned, and why (one comeback, one retired question, …).
- **Club Store** (the shop): browse, fitting room, wishlist, featured shelf.
- **Wardrobe** (loadout editor):
  - every slot with what you own;
  - live preview;
  - save, name and share loadouts;
  - day/night and context loadouts.
- **Collection log**: items owned, eggs found, `???` silhouettes.
- **Profile card** on Home: name, title, frame, a showcase of 3 badges, one honest stat line. Export it as PNG to share with the club.
- **Theme Lab** (dev only): see §3.4.
- **Settings additions**:
  - the sound mixer;
  - reduced motion;
  - the **whimsy dial** (Off / Subtle / Full);
  - **Focus mode**: hides the wallpaper and turns off decorative animation; can be automatic in timed quizzes;
  - seasonal events on/off;
  - easter eggs on/off;
  - personal greeting name and exam-countdown date.

---

## 11. Accessibility and wellbeing guardrails

- **Contrast**: the Theme Lab checks contrast for every palette, and the palette editor blocks saving below AA. The existing accessibility toggle overrides any loadout.
- **Motion**: `prefers-reduced-motion` plus the whimsy dial; nothing flashes faster than 3 Hz; CRT flicker is off by default.
- **Sound**: quiet defaults and a per-channel mixer.
- **Copy**: never shames. "Wrong" is supportive and still states the expected answer clearly.
- **Late night**: the app nudges toward sleep. No "night owl" reward for 3 am sessions; the Night Owl title, if kept, comes from evening sessions before midnight.
- **Effects never cover the question or the answer box**, and Focus mode is one click away during timed quizzes.

---

## 12. Asset sourcing guide

### 12.1 Formats and sizes

| Asset | Format | Size / spec |
|---|---|---|
| Icons | SVG, ideally single-colour paths for `currentColor` recolouring; or pixel-perfect PNG | 16, 24, 32 px. Pixel sets are exact 16×16 at integer scaling. |
| Sprite sheets (furniture, effects) | PNG atlas + JSON (Aseprite's export format is fine) | States × frames listed in the JSON |
| Wallpapers | WebP (or AVIF) | ≤ 2560×1440 and ≤ 600 KB; a tileable version for textures; dawn/day/dusk/night variants if possible |
| Cursors | PNG with a hotspot noted | 32×32 |
| UI sounds | OGG or MP3, 44.1 kHz | ≤ 300 ms, trimmed, normalized to the same loudness |
| Fonts | WOFF2 | Subset to Latin (plus any extra scripts needed); OFL or similar |
| Logos | SVG | See §12.3 |

Keep an eye on app size. Wallpapers and sound packs are the heavy items, so budget them, and consider an optional "deluxe pack" download kept outside git.

### 12.2 Licences and the public repo
- **Prefer CC0**, then CC-BY (with credit, filled in the item's `credits` block), then OFL for fonts.
- **Avoid**: NC and SA terms unless the owner is comfortable with them, and anything "for personal use only".
- **The repo is public**, so committing an asset redistributes it. Many paid asset packs forbid redistribution. Keep those in a git-ignored `packs_private/` folder and only ship them in builds if the licence allows.
- **Good sources**:
  - Kenney (CC0 UI, sprites and sounds);
  - game-icons.net (CC BY 3.0);
  - OpenGameArt and itch.io (licence per pack);
  - Google Fonts (OFL; download and bundle, never link);
  - Freesound (licence per file);
  - sfxr, jsfxr and ChipTone (generate your own sounds);
  - Lospec (palettes);
  - Incompetech (CC BY music).
- **No trademarked art or sounds** (spec §11.4): no OS chrome screenshots, console sprites or famous jingles. Original art "in the style of" is fine.

### 12.3 Club logos: what to send
1. One SVG per club logo (or per mark, if it's one club with one mark), with text converted to paths and no embedded bitmaps.
2. A single-colour version of each, so it can take the theme's colour.
3. A square mark (icon only, no wordmark) for the app icon and loader. It must read clearly at 16 px.
4. A horizontal lockup, if one exists, for the Welcome hero and the PDF letterhead.
5. Light-background and dark-background versions, if they differ.
6. The club colours as hex values, and the club names exactly as they should be written.
7. Any usage rules: may we recolour per theme, pixelate or stylize it, animate it? Minimum size and clear space.
8. Confirmation that the club is happy for the logos to be committed to the public repo.

### 12.4 First asset checklist (per existing theme)
- Wallpaper, plus a tileable surface texture.
- Icon set covering the semantic names in §5.5.
- Cursor (pointer and busy).
- Sound pack covering the events in §5.7. Starting with `click`, `correct`, `partial`, `wrong`, `session_end`, `generate_done`, `earn_bits` and `earn_qed` covers most of the feel.
- Fonts (see §7).

---

## 13. Roadmap

| Phase | Contents | Size |
|---|---|---|
| **0. Foundations** | Token expansion; component `data-ui` hooks replacing class-name selectors; per-slot `<html>` attributes; item manifest and registry; `ThemedIcon`; real sound playback with mixer; effects layer with reduced motion and the whimsy dial; bundled fonts; the token-override editor the spec owes; Theme Lab; club logo placements | L |
| **1. Rich themes** | Packs for the 12 existing themes (owner-sourced assets); results screens | M per theme (mostly assets) |
| **2. Economy** | Migration 010; `economy.py` and payout hooks; retro grant; wallet chip, toasts, receipts; Club Store with fitting room and wishlist; Wardrobe and loadouts; weekly goals and onboarding quests; simulator | L |
| **3. Personality** | Study room; easter eggs and collection log; seasonal calendar and club events; titles and profile card | L |
| **4. Expansion** | New themes and sets; quiz arena skins; chart skins; PDF cosmetics; personal packs folder | M each |

Phase 0 is worth doing even without an economy: every later phase becomes "drop in assets and a manifest" instead of new code.

---

## 14. Decisions for the owner

1. **Currency names**: Bits / QEDs (recommended), or one of the alternatives in §9.2.
2. **Today's flavor themes stay free** with their deluxe parts sold (recommended), or move them into the shop.
3. **Home**: a full study room or the lighter widget layout (§5.12).
4. **Game nods**: which of the text homages in §6 to keep. The default is short quotes only, no names or art.
5. **Print cosmetics**: free (recommended, since PDFs are functional) or shop items.
6. **Companion**: decided 2026-11-09: removed (see §5.9).
7. **Default sound**: off (recommended) or quiet.
8. **Seasonal events**: which cultural and national dates to include by default.
9. **Club logos**: the files and usage rules in §12.3.
