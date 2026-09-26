---
name: f1-racer
description: >-
  Launch F1 Racer, a browser racing game served by a local FastAPI app. Use when
  the user says "/f1-racer", "play F1 Racer", "start the racing game", or wants a
  quick driving game in the browser. One Python file holds both the server and the
  whole game page, so there is nothing to build and nothing to configure.
---

# /f1-racer

A racing game that runs in the browser, served by a small FastAPI app. `<plugin-dir>`
is this plugin's directory.

1. Install the two dependencies if they aren't present:

   ```
   pip install -r "<plugin-dir>/requirements.txt"
   ```

2. Start the server in the background on a free port:

   ```
   uvicorn f1_racing:app --host 127.0.0.1 --port 8010
   ```

   Run it from `<plugin-dir>` so `f1_racing` is importable. If 8010 is taken, pick
   another port.

3. Open `http://127.0.0.1:8010` in the browser and tell the user the game is up.

Everything lives in `f1_racing.py`: `GET /` returns the complete page, with the
canvas game and its JavaScript inlined in the `PAGE` string. There is no API to
drive from here and no session state, so once it is open there is nothing further
to do.
