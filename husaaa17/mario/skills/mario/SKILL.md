---
name: mario
description: >-
  Launch World 1-1, a side-scrolling platformer served by a local FastAPI app. Use
  when the user says "/mario", "play World 1-1", "start the platformer", or wants a
  quick jump-and-run game in the browser. The whole game page is inlined in one
  Python file, so there is nothing to build and nothing to configure.
---

# /mario

A side-scrolling platformer that runs in the browser, served by a small FastAPI
app. `<plugin-dir>` is this plugin's directory.

1. Install the two pinned dependencies if they aren't present:

   ```
   pip install -r "<plugin-dir>/requirements.txt"
   ```

   Note these are pinned exactly (`fastapi==0.141.1`, `uvicorn==0.53.0`), so
   install into a virtual environment if the versions would clash with the rest of
   the workspace.

2. Start the server in the background on a free port:

   ```
   uvicorn main:app --host 127.0.0.1 --port 8012
   ```

   Run it from `<plugin-dir>` so `main` is importable. If 8012 is taken, pick
   another port.

3. Open `http://127.0.0.1:8012` in the browser and tell the user it is up.

Everything lives in `main.py`: `GET /` returns `HTML_PAGE`, which holds the canvas
game and its JavaScript. The page title is "World 1-1".
