---
name: lizard-leap
description: >-
  Launch Lizard Leap, a pixel-art desert runner served by a local FastAPI app —
  jump the rocks, duck the birds for a bonus, eat berries for a score multiplier.
  Use when the user says "/lizard-leap", "play lizard leap", "start the lizard
  game", or wants a quick endless runner. Can also build a standalone HTML page or
  a Windows executable.
---

# /lizard-leap

A pixel-art endless runner. You are a lizard. `<plugin-dir>` is this plugin's
directory.

## Launching

1. Install dependencies if needed: `pip install fastapi uvicorn`
2. Run it in the background, from `<plugin-dir>`:

   ```
   python game.py
   ```

`game.py` picks a free port itself, prints the URL, and opens the browser after
about a second and a half, so don't open a second tab — read the port from its
output. It blocks while serving and then waits on `input()`, so it must run in the
background.

For editing, `uvicorn game:app --reload` works instead.

## How to play

| Key | Action |
|---|---|
| Space | Jump (also starts and restarts) |
| Down arrow or S | Duck (hold); in mid-air it drops you fast |
| Phone | Tap the top half to jump, hold the bottom half to duck |

Rocks come in three sizes and must be jumped. Birds swoop at head height after 250
points — ducking under one earns +100, jumping it earns nothing. Berries overhead
give a x2 multiplier for six seconds, stacking to x4. The game speeds up the longer
you survive, and follows the system light or dark setting.

## Building the shareable versions

```
python build.py        # both
python build.py html   # dist/LizardLeap.html + docs/index.html
python build.py exe    # dist/LizardLeap.exe  (Windows; needs pyinstaller and pillow)
```

The HTML build keeps the best score in the browser instead of on the server, so it
runs anywhere without Python; `docs/index.html` is what GitHub Pages serves.

## What it exposes

- `GET /api/highscore` returns the saved best score
- `POST /api/highscore` with `{"score": 123}` saves it if it beats the old best

`game.py` is the only source file — everything else is generated from it, so edit
it rather than the build outputs.
