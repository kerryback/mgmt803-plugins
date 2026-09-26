---
name: countdown
description: >-
  Launch a local countdown page that Claude themes live for whatever occasion
  you type in (a wedding, a game, graduation, a trip) -- picking colors, an
  emoji, a heading font, and a particle effect (snow/confetti/floating/sparkle)
  that fit the occasion. Use when invoked via /countdown, or on "make a
  countdown to X", "how many days until X", "countdown page for my
  wedding/graduation/trip". Opens http://127.0.0.1:8030 in the browser; the
  occasion and date are typed right there, and the app calls Claude itself
  (ANTHROPIC_API_KEY) to design each theme -- there is nothing for Claude Code
  to do after launching it.
---

# countdown

A one-page countdown timer with no fixed look. Type what you're counting down
to and a date, and the app calls Claude to design the whole page for it, live:
background colors, an emoji, a heading font, and a falling/rising/twinkling
particle effect that all fit the occasion — a school's real colors, a
holiday's mood, a wedding's palette.

## What to do

1. Check `ANTHROPIC_API_KEY` is set (`printenv ANTHROPIC_API_KEY`). It isn't
   required to launch — the page still loads and falls back to a plain default
   theme without it — but mention it up front if it's missing: get a key at
   console.anthropic.com and export it, e.g. `export ANTHROPIC_API_KEY=sk-ant-...`
   in the shell profile.
2. Launch in the background from `<skill-dir>` (the base directory this skill
   reports when invoked):
   ```
   python3 "<skill-dir>/scripts/skill_launch.py"
   ```
   Run it in the background — it starts a long-lived local server. First run
   creates a small venv and installs requirements, so it takes a few extra
   seconds; later launches are instant.
3. It opens http://127.0.0.1:8030 automatically. Tell them to type an occasion
   and pick a date right there — that's it. There is nothing for you to do
   after launch; the app talks to Claude itself for each theme.
4. If port 8030 is already in use, rerun with `--port 8031` (or any free port).

There's no output file and nothing to hand back — the countdown just runs live
in that browser tab for as long as the server is up.
