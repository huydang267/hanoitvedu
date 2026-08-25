# CLAUDE.md — HaNoiTVEdu

Guidance for Claude Code when working in this repository.

---

## 1. What this project is

**HaNoiTVEdu** is a workplace learning platform for Hanoi TV employees: short, role-based
modules that teach practical AI skills for editorial, admin and content work.

Tagline: **LEARN AI. SHARPEN YOUR STORY.**

This repo implements a **Flask** web app that reproduces, page-for-page, a set of screens that
were already designed in Canva (`HRD A2.pdf`, 16 screens). The design is fixed. The job of the
code is to render those screens faithfully as responsive HTML, not to reinvent them.

**Content is in English. Forum sample posts are in Vietnamese. Comments/commits in English.**

---

## 2. Tech stack (do not add to this without being asked)

| Layer | Choice |
|---|---|
| Server | Flask (app factory + blueprints) |
| Templates | Jinja2, server-rendered |
| Styling | One hand-written CSS file + CSS custom properties. No Tailwind, no Bootstrap, no SASS build step. |
| JS | Vanilla ES6, progressive enhancement only (nav toggle, quiz check, accordions). No React/Vue/jQuery. |
| Content data | Python dicts / JSON in `app/data/` — modules, lessons, prompts are **content**, not database rows |
| Dynamic data | SQLite via `Flask-SQLAlchemy` — only for forum posts, quiz attempts, user info |
| Fonts | League Spartan (Google Fonts) + Canva Sans (self-hosted if licensed, else fallback stack) |
| Deps | `Flask`, `Flask-SQLAlchemy`, `python-dotenv`. Pin in `requirements.txt`. |

---

## 3. Directory layout

```
hanoitvedu/
├── run.py                     # dev entrypoint: create_app() + app.run(debug=True)
├── config.py                  # Config / DevConfig / ProdConfig
├── requirements.txt
├── CLAUDE.md
├── instance/                  # SQLite db lives here, gitignored
└── app/
    ├── __init__.py            # create_app(), blueprint registration, jinja globals
    ├── models.py              # ForumPost, QuizAttempt, UserProfile
    ├── data/
    │   ├── modules.py         # module + lesson content (steps 01–06)
    │   ├── programs.py        # Editorial / Admin / Content role trees
    │   └── prompts.py         # Notebook prompt library
    ├── blueprints/
    │   ├── overview/          # /, /about, /program, /program/<role>, /blogs, /me
    │   ├── learn/             # /learn, /learn/<module>, /learn/<module>/<step>
    │   ├── practice/          # /practice/<module>, /practice/<module>/quiz
    │   ├── notebook/          # /notebook
    │   └── forum/             # /forum, /forum/<channel>, POST /forum/post
    ├── templates/
    │   ├── base.html          # <html> shell: background layers, navbar, LIVE badge, card
    │   ├── macros/
    │   │   ├── boxes.html     # heading_box(), body_box(), key_idea(), tip_box(), step_badge()
    │   │   └── icons.html     # inline SVG icon set (NO emoji, NO raster illustrations)
    │   ├── overview/…  learn/…  practice/…  notebook/…  forum/…
    └── static/
        ├── css/
        │   ├── tokens.css     # ALL colours, fonts, spacing, radii — single source of truth
        │   ├── layout.css     # background, navbar, white card, bottom bars
        │   └── components.css # boxes, badges, tables, cards, quiz, forum
        ├── js/main.js
        ├── fonts/             # league-spartan-*.woff2, canva-sans-*.woff2 (if licensed)
        └── image/
            └── logo.png       # Hanoi TV logo — ALREADY PRESENT, do not replace or recolour
```

---

## 4. Page map (from `HRD A2.pdf`)

| # | Screen | Route | Nav active |
|---|---|---|---|
| 1 | Landing / hero + 4 entry cards | `/` | OVERVIEW |
| 2 | About Us | `/about` | OVERVIEW |
| 3 | Our Program — 3 role cards | `/program` | OVERVIEW |
| 4 | Editorial — 4 skill areas | `/program/editorial` | OVERVIEW |
| 5 | Module 1 overview + "What you will learn" | `/learn/ai-research-planning` | OVERVIEW |
| 6 | 01 Start with the topic | `/learn/ai-research-planning/01` | LEARN |
| 7 | 02 Build research questions | `…/02` | LEARN |
| 8 | 03 Create search keywords | `…/03` | LEARN |
| 9 | 04 Identify information gaps | `…/04` | LEARN |
| 10 | Common mistakes when using AI for planning | `…/mistakes` | LEARN |
| 11 | 05 The AI research flow | `…/05` | LEARN |
| 12 | 06 Quick checklist + Skill unlocked | `…/06` | LEARN |
| 13 | 07 Quick practice | `/practice/ai-research-planning` | PRACTICE |
| 14 | Quick check (3 MCQ) | `/practice/ai-research-planning/quiz` | PRACTICE |
| 15 | Notebook — Prompt library | `/notebook` | NOTEBOOK |
| 16 | AI Work Forum | `/forum` | FORUM |

`/program/admin` and `/program/content` follow the Editorial template with their own skill lists.

Lesson pages are **one template driven by data**. Do not write 8 near-identical templates —
write `learn/lesson.html` and feed it a lesson dict (`number`, `title`, `lead`, `blocks`).

---

## 5. Design system — this section is binding

### 5.1 Colour tokens (`tokens.css`)

```css
:root{
  /* logo palette — the 4 Hanoi TV colours */
  --c-red:    #da463d;
  --c-blue:   #507fbb;
  --c-yellow: #e0c148;
  --c-green:  #60b057;

  /* typography colours */
  --heading:  #e2011a;   /* League Spartan headings + subheadings */
  --body:     #26318c;   /* Canva Sans body text */
  --navy:     #1e2b6f;   /* dark navy for nav text, table headers */

  /* pastel fills for BODY text boxes */
  --pastel-green:  #e4f4e4;  --pastel-green-line:  #60b057;
  --pastel-yellow: #fffbed;  --pastel-yellow-line: #e0c148;
  --pastel-blue:   #eaf1fa;  --pastel-blue-line:   #507fbb;
  --pastel-red:    #fcf0ef;  --pastel-red-line:    #da463d;

  /* surfaces */
  --card:  #f7f9ff;
  --white: #ffffff;
}
```

### 5.2 Typography

- **Headings + subheadings** — `League Spartan`, colour `--heading` (#e2011a).
  Weight 700–800. Keep the casing exactly as written in the source design; **do not add
  `text-transform`, letter-spacing tricks or text effects.**
- **Body** — `Canva Sans`, colour `--body` (#26318c).
  Fallback stack: `"Canva Sans", "Poppins", "Nunito Sans", system-ui, sans-serif`.
  If the licensed woff2 is not in `static/fonts/`, load Poppins from Google Fonts.
- Never use a third typeface.

### 5.3 Background (every page, defined once in `base.html` + `layout.css`)

Three fixed layers, back to front:

1. **Animated blue gradient** — slow-moving deep-blue field (`#0b1f6b → #1c3fa8 → #0b1f6b`,
   `background-size: 300% 300%`, ~18s ease-in-out infinite pan). Respect
   `@media (prefers-reduced-motion: reduce)` → freeze the animation.
2. **Two angled bars at the bottom** — one `--c-red`, one deep blue, skewed, sitting behind
   the card. These plus the blue background already supply 2 of the 4 logo colours.
3. **White content card** — centred, `border-radius: 28px`, generous padding, drop shadow.

**Adaptive rule (important):** the more content a page has, the larger the white card grows and
the smaller the blue field and bottom bars become. Implement as: card is
`width: min(1600px, 94vw)`, `margin: clamp(12px, 2.5vh, 40px) auto`, with the bars anchored to
the bottom of the viewport at `height: clamp(40px, 9vh, 120px)`. Content-heavy pages must never
push the bars over the text.

### 5.4 Colour balance rule

Background and bottom bars are **red + blue**. Therefore:

- **Text boxes use green and yellow** (pastel fills) as their default.
- **Decorative elements, badges, numbered chips, icons, table accents** must reintroduce
  **red and blue** so each screen carries all four logo colours.
- Target: every screen shows all 4 colours, none of them dominating. A page that is only green
  and yellow is wrong; so is a page that is only red and blue.

### 5.5 Box components (`macros/boxes.html`)

| Macro | Use | Fill | Border | Text |
|---|---|---|---|---|
| `heading_box(text, colour)` | headings / labels / pills | **solid** logo colour | none | white, League Spartan |
| `body_box(colour)` | paragraphs, lists, tips | **pastel** of that colour | 2px solid, matching line colour, radius 12px | `--body`, Canva Sans |
| `key_idea(text)` | the red "KEY IDEA" callout | red solid tab + pastel-red panel | red | red bold |
| `tip_box(text)` | "TIP FOR EDITORIAL TEAMS" | pastel green | green | body |
| `step_badge(n)` | the red arrow chip `01`…`07` | red arrow shape | none | white |

Never put body text directly on the white card — it always sits in a box.

### 5.6 LIVE badge

The `● LIVE` badge (red ring + red outlined "LIVE" wordmark) is a **fixed corner element on
every page**, top-left of the card. See screens 6–14 for placement. Build it as an inline SVG
in `macros/icons.html`, include it from `base.html`, never as an image file.

### 5.7 Navbar

White rounded pill floating over the background: logo (`static/image/logo.png`) at the left,
then `OVERVIEW · LEARN · PRACTICE · NOTEBOOK · FORUM` in navy League Spartan, then a hamburger
and a user icon at the right. The active item is `--heading` red with a 3px red underline.
Pass `active_nav` from every view; `base.html` handles the styling.

Below ~900px the links collapse behind the hamburger into a vertical sheet.

### 5.8 Icons and imagery — replacement policy

The Canva mockups use emoji and stock illustrations. **Do not reproduce them.**

- **No emoji anywhere** in templates, content data, or UI copy.
- **No stock/clip-art illustrations.** Where the mockup shows a person, laptop, clipboard or
  photo, either drop the element or replace it with a flat inline SVG icon in one of the four
  logo colours, sized 24–48px.
- The **only image asset** is `static/image/logo.png`, used in the navbar (and once in the hero).
- All icons live in `macros/icons.html` as named macros: `icon_clock()`, `icon_pin()`,
  `icon_person()`, `icon_question()`, `icon_idea()`, `icon_check()`, `icon_cross()`,
  `icon_arrow()`, `icon_key()`, `icon_folder()`. Each takes a `colour` argument.

---

## 6. Content — the verbatim rule

**All user-facing copy is the author's. Claude never writes, rewrites, shortens, expands,
"improves", translates or fixes the grammar of site copy.** If a sentence looks wrong, leave it
and raise it with the author instead of editing it.

### 6.1 Pipeline

```
HRD A2.pdf                                   ← author's Canva design, the origin
   │  pdftotext -layout   → content/source/page-NN.txt   (human-readable reference)
   │  pdftotext           → content/flow/page-NN.txt     (reading order, matching corpus)
   ▼
content/content.json      ← every string copied character-for-character from the dumps
   ▼
app/data/*.py             ← thin loaders: json.load(), no string literals of site copy
   ▼
Jinja templates           ← render values; never hard-code a sentence
```

Regenerate the dumps with:

```bash
for i in $(seq 1 16); do n=$(printf "%02d" $i)
  pdftotext -f $i -l $i -layout "HRD A2.pdf" "content/source/page-$n.txt"
  pdftotext -f $i -l $i          "HRD A2.pdf" "content/flow/page-$n.txt"
done
```

Both dumps are committed. `content/source/` is for reading; `content/flow/` is what the
verifier matches against, because `-layout` interleaves columns and breaks sentences.

### 6.2 `content/content.json`

Single source of truth for copy. Shape:

- `site`, `nav` — wordmark, tagline, nav labels
- `pages.<name>` — one entry per non-lesson screen (`home`, `about`, `program`,
  `role_editorial`, `notebook`, `forum`)
- `modules.<slug>` — module header, `overview`, `what_you_will_learn`, `lessons[]`,
  `practice`, `quiz`
- Each lesson: `number`, `title`, `lead`, `blocks[]`, `tip`, `key_idea`

Every node carries a `source` key naming the page dump it came from, so any string can be
traced back to a slide in one step.

**Keys that are copy** (verified): `heading`, `title`, `text`, `label`, `lead`, `items`,
`paragraphs`, `prompt`, `body`, `question`, `keywords`, …
**Keys that are structure** (not verified, safe to change): `source`, `active_nav`, `accent`,
`endpoint`, `key`, `slug`, `module`, `state`, `answer`, `n`, `id`, `likes`, `when`, `type`,
`columns`, `decor`.

`decor` marks text that exists only as artwork on the slide (e.g. the `VIE` / `ENG` badges) and
therefore has no text layer to verify against.

Templates read this file — they never contain a sentence of site copy. Structural words that
belong to the code (button `aria-label`s, `<title>` tags, error messages) are fine in templates.

### 6.3 Verification

```bash
python tools/verify_content.py            # report
python tools/verify_content.py --strict   # exit 1 on any miss — use in pre-commit and CI
```

It walks `content.json`, collects every authored string, normalises whitespace, and requires a
word-boundary exact match inside the page's flow dump. Current state: **267/267 strings match.**

If it reports a miss, the fix is to correct `content.json` to match the dump — never to relax
the wording, and never to edit the dump. The only legitimate exception is a phrase pdftotext
genuinely cannot reconstruct; verify it by eye against the PDF, then add it to the `ALLOW` set
with a comment explaining why.

Run the verifier after any content change, before any commit that touches `content/` or
`app/data/`, and as the last step of any task that adds a page.

### 6.4 Copy that does not exist yet

Screens 3 and 4 imply `/program/admin` and `/program/content`, and the Editorial screen lists
three skill areas with no module behind them. The PDF has no copy for these.

**Do not invent it.** Render those entries as disabled cards using the label text that does
exist, and ask the author for the missing copy. Placeholder text (`Lorem ipsum`, "Coming soon"
written by Claude) is a content change and is not allowed.

---

## 7. Coding conventions

- **App factory only.** `create_app(config)` in `app/__init__.py`; no module-level `app`.
- One blueprint per nav section, registered with a `url_prefix`.
- Views stay thin: fetch data, pick a template, `render_template`. Content lives in `app/data/`.
- Templates: `{% extends "base.html" %}`, always set `{% set active_nav = "learn" %}` and
  `{% block title %}`.
- CSS: token-first. **No hard-coded hex values outside `tokens.css`.** If you need a new colour,
  add a token or derive it from an existing one.
- Class naming: `block__element--modifier` (BEM-ish), lowercase, hyphenated.
- Python: 4 spaces, type hints on functions in `data/` and `models.py`, `snake_case`.
- No inline `style=""` except for one-off dynamic values (e.g. progress width).
- Accessibility: semantic landmarks, `alt` on the logo, ≥4.5:1 contrast for body text,
  keyboard-reachable nav and quiz, visible focus ring in `--c-blue`.
- Responsive: fluid down to 360px. Multi-column mockup layouts collapse to a single column.

---

## 8. Running it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=run.py FLASK_ENV=development
python run.py            # http://127.0.0.1:5000
```

Prod: `gunicorn "app:create_app()" -b 0.0.0.0:8000`.

---

## 9. Build order

0. `content/source/`, `content/flow/`, `content/content.json`, `tools/verify_content.py` — **done**
1. `config.py`, `run.py`, `app/__init__.py`, `requirements.txt`
2. `tokens.css` + `layout.css` + `base.html` — background, bars, card, navbar, LIVE badge
3. `macros/boxes.html` + `macros/icons.html`
4. Overview blueprint (screens 1–4)
5. `app/data/modules.py` + `learn/lesson.html` (screens 5–12)
6. Practice + quiz (13–14)
7. Notebook (15)
8. Forum with SQLite (16)
9. Responsive pass + accessibility pass
10. `python tools/verify_content.py --strict` must pass

---

## 10. Rules of thumb for changes

- **Do** match the PDF layout, wording and ordering exactly unless asked otherwise.
- **Do** add new colours only as tokens, and only from the four-logo palette.
- **Do** keep every page reachable from the navbar.
- **Don't** introduce a CSS framework, a JS framework, or a build step.
- **Don't** use emoji or stock imagery.
- **Don't** touch `static/image/logo.png`.
- **Don't** restyle headings with effects, transforms or extra letter-spacing.
- **Don't** duplicate a template when a data-driven one will do.
- **Don't** write, reword or invent any site copy — it comes from `content/content.json` only.
