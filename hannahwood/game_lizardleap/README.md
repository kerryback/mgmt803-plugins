# Lizard Leap

A tiny pixel-art desert runner. You're a lizard. Jump the rocks, duck the birds, eat the berries.

**▶ Play in your browser:** https://thehgremlin.github.io/LizardLeap/

**⬇ Windows app:** grab `LizardLeap.exe` from the [latest release](https://github.com/TheHGremlin/LizardLeap/releases/latest). No Python needed. Windows will say "Windows protected your PC" because the app isn't signed; click **More info → Run anyway**.

## How to play

| Key | Action |
|---|---|
| **Space** | Jump (also starts / restarts) |
| **↓** or **S** | Duck (hold). In mid-air, drops you fast |
| Phone | Tap the top half to jump, hold the bottom half to duck |

- **Rocks** come in pebble, rock and boulder sizes. Jump them. Hit one: *Bonk!*
- **Birds** swoop in at head height once you pass 250 points. Duck under them for a **+100 bonus** (jumping works, but earns nothing). Get caught: *Nom!*
- **Berries** float overhead. Jump into one for a **×2 score multiplier** for 6 seconds; eat more while it's active to stack up to **×4**.
- The game speeds up the longer you survive.

Plays in light (desert day) or dark (desert night) mode, following your system setting.

## How it's built

The whole game is one Python file, [`game.py`](game.py): a small [FastAPI](https://fastapi.tiangolo.com/) server that serves the game page (HTML + canvas + JavaScript, all pixel art drawn in code) and a best-score API:

- `GET /api/highscore` returns the saved best score
- `POST /api/highscore` with `{"score": 123}` saves it if it's a new best

### Run it locally

Needs Python 3 with `fastapi` and `uvicorn`:

```bash
pip install fastapi uvicorn
python game.py
```

That starts the server and opens the game in your browser. Or use `uvicorn game:app --reload` while editing.

### Build the shareable versions

```bash
python build.py        # both
python build.py html   # dist/LizardLeap.html + docs/index.html
python build.py exe    # dist/LizardLeap.exe  (Windows, needs: pip install pyinstaller pillow)
```

(or double-click `build.bat`)

- **HTML** – the same page with the best score kept in the browser instead of the server, so it runs anywhere with no Python. `docs/index.html` is what GitHub Pages serves.
- **EXE** – PyInstaller bundles Python, FastAPI and the game into one Windows app that starts the server and opens the browser. It saves the best score to `%APPDATA%\LizardLeap`.

`game.py` is the only source file; everything else is generated from it.
