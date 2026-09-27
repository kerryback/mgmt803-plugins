# mgmt803-plugins

A Claude Code plugin marketplace for MGMT 803 at Rice Business. Twenty-six
plugins: scheduling and planning agents, market-data briefs, a job scout,
teaching tools, app scaffolds, and a handful of browser games — most of them
built by the class.

## Install

Register the marketplace once:

```
/plugin marketplace add kerryback/mgmt803-plugins
```

Then install whatever you need:

```
/plugin install voiceover@mgmt803
/plugin install shoji@mgmt803
```

Or type `/plugin` alone to browse and install from the menu. Start a fresh
session after installing, because a plugin's skills don't load until the session
restarts.

## Planning and scheduling

| Plugin | Author | What it does |
| --- | --- | --- |
| `calendar-keeper@mgmt803` | bb151-pixel | Plans your week across several Google calendars from rules you set once, and keeps anything that isn't work off your work calendar — including the attendee trap that silently copies events onto your primary calendar. Proposes before editing, then verifies its own edits. Your details stay in a private profile on your computer. |
| `syllabus-to-trello@mgmt803` | bb151-pixel | Turns syllabi into dated Trello cards and calendar reminders, with personal targets set ahead of each official deadline. Labels derived dates as derived, flags missing or contradictory ones, and shows you the whole plan before creating anything. |
| `smithers@mgmt803` | Kerry Back | A local email and calendar desk over Gmail and Calendar. Drafts replies for you to send; never sends mail or deletes events itself. |
| `countdown@mgmt803` | jessica-george | A countdown page with no fixed look — Claude designs the colors, emoji, font and particle effect live for whatever occasion you type in. Needs an Anthropic API key. |

## Markets and career

| Plugin | Author | What it does |
| --- | --- | --- |
| `wolverine-brief@mgmt803` | Cspiteri33 | A weekly cross-asset brief in Wolverine's voice: the last week of stocks, Treasuries, the dollar, gold and oil from Yahoo Finance, with a blunt take on the biggest moves and how they moved relative to each other. Builds its own virtualenv; no API key needed. |
| `doom-desk@mgmt803` | Hannah Wood | The same five ETFs, narrated as pessimistically as possible. Pulls the real returns and has Claude describe the carnage, citing only the actual numbers. Needs an Anthropic API key. |
| `job-scout@mgmt803` | bazingasc | Builds a profile from your resume and target roles, searches current postings, scores each against your background, emails a digest of the best matches, and recommends specific resume changes. Personal data stays in `~/job-scout/`. Needs a Gmail connector with send or compose scope. |

## Documents, slides and teaching

| Plugin | Author | What it does |
| --- | --- | --- |
| `critique@mgmt803` | Kerry Back | Reviews work Claude produced and says what to do about it, with located evidence behind every finding. Fans out several subagents, so it is not cheap. |
| `elegant-pdf@mgmt803` | Kerry Back | Flyers, programs, reports and handbooks as branded PDFs or JPEGs, rendered from a small HTML design system. |
| `shoji@mgmt803` | Kerry Back | A Quarto reveal.js slide theme in plum, pale gray and dusty blue, set small enough for text- and code-heavy decks. |
| `voiceover@mgmt803` | Kerry Back | Turns a slide PDF into a narrated MP4 plus a transcript, with a local app for editing the script and picking a voice. Needs an ElevenLabs API key. |
| `sn-lab@mgmt803` | Douglas Chesson | Animates SN1 and SN2 nucleophilic substitution. Pick a substrate, nucleophile and solvent from a curated textbook set; it predicts which mechanism dominates, explains why, and animates it beside a reaction-energy diagram. No dependencies. |
| `ai-flow-chart-explainer@mgmt803` | Kerry Back | A local interactive guide to how agents, skills, tools, plugins, connectors, APIs, and external systems connect. Click chart regions for explanations; open or download the original PNG. |
| `math-atelier@mgmt803` | Jennifer Lane | A self-contained page for math practice. One HTML file, nothing to install. |
| `piano-transcriber@mgmt803` | Caitlin Lorenz | Turns a song — a link, a search query, or an uploaded file — into piano sheet music at easy/medium/hard difficulty, with in-browser playback and a labeled PDF download. Runs entirely locally; no API key needed. |

## App scaffolds

These generate a working app in your project rather than doing something
themselves.

| Plugin | Author | What it scaffolds |
| --- | --- | --- |
| `sullivan-family-activities@mgmt803` | enjolisunshine | A local family organizer: FastAPI and SQLite behind a shared calendar, tasks and chores with point rewards and turn rotation, a prize shop, maintenance reminders, kid mode, a phone-link QR code, and a PIN-protected settings area. |
| `finance-app@mgmt803` | Jack Beathard | A loan payment calculator: FastAPI backend computing monthly payment, total paid and total interest from amount, rate and term, with a matching form. |
| `density-weight-converter@mgmt803` | HighLordLangford | A density-to-weight converter: g/cm³ and ft³ to pounds, with an optional tons-per-acre mode from thickness and acreage. |
| `childrens-book-generator@mgmt803` | John Poremski | A children's picture book generator: FastAPI app that turns a character, art style, and moral of the story into plot beats plus a matching illustration per page, kept consistent across pages, with an optional rhyming mode and a PDF download. |

## Games and chat

| Plugin | Author | What it does |
| --- | --- | --- |
| `penguoom@mgmt803` | tfensign | A Doom-style FPS starring a penguin across ten winter sectors. One self-contained HTML file: canvas raycaster, Web Audio sound and music, no build step. |
| `lizard-leap@mgmt803` | Hannah Wood | A pixel-art desert runner. Jump the rocks, duck the birds for a bonus, eat berries for a score multiplier. Also builds a standalone HTML page or a Windows exe. |
| `mario@mgmt803` | husaaa17 | World 1-1, a side-scrolling platformer served by a local FastAPI app. |
| `f1-racer@mgmt803` | Jack Peterson | A browser racing game served by a local FastAPI app. |
| `flappy-bird@mgmt803` | Jack Peterson | Sammy the Owl, a tap-to-fly arcade game in Rice blue. |
| `snark-bot@mgmt803` | Hannah Wood | A chat app that answers your question and roasts you while doing it. Needs an Anthropic API key. |

## Layout

Each plugin lives in a folder named for its author, and `marketplace.json` points
at it:

```
kerryback/critique
hannahwood/game_lizardleap
jack-peterson/f1-racer
...
```

Plugin names are flat — the author folder is organization only and never appears
in an install string. Avoid spaces in folder names, since they have to work as
`source` paths in `marketplace.json`.

## Adding a plugin

Three pieces. A plugin is a folder containing:

```
<your-folder>/<plugin-name>/
  .claude-plugin/plugin.json      name, description, version, author
  skills/<skill-name>/SKILL.md    frontmatter (name, description) + instructions
  ...                             your code, wherever it already lives
```

`plugin.json` is the manifest:

```json
{
  "name": "my-plugin",
  "description": "One or two sentences on what it does.",
  "version": "1.0.0",
  "author": { "name": "Your Name" }
}
```

`SKILL.md` is what Claude actually reads. Its frontmatter needs a `name` and a
`description`, and the description is what decides whether the skill triggers, so
write it as the situations it applies to rather than as a summary. The body is
instructions to Claude, not documentation for a human.

Then add an entry to `.claude-plugin/marketplace.json`:

```json
{
  "name": "my-plugin",
  "source": "./your-folder/my-plugin",
  "description": "Same description as the manifest."
}
```

A folder with code but no `plugin.json` and no `marketplace.json` entry is not a
plugin and can't be installed — it's just files in a repo. Open a pull request
against `main` when it's ready.
