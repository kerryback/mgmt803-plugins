---
name: flappy-bird
description: >-
  Launch Sammy the Owl, a Flappy-Bird-style tap-to-fly game in Rice blue, served
  by a local FastAPI app. Use when the user says "/flappy-bird", "play Sammy the
  Owl", "start the flappy bird game", or wants a quick arcade game in the browser.
  One Python file, no build step, no configuration.
---

# /flappy-bird

A tap-to-fly arcade game starring Sammy the Owl, served by a small FastAPI app.
`<plugin-dir>` is this plugin's directory.

1. Install the two dependencies if they aren't present:

   ```
   pip install -r "<plugin-dir>/requirements.txt"
   ```

2. Start the server in the background on a free port:

   ```
   uvicorn flappy_bird:app --host 127.0.0.1 --port 8011
   ```

   Run it from `<plugin-dir>` so `flappy_bird` is importable. If 8011 is taken,
   pick another port.

3. Open `http://127.0.0.1:8011` in the browser and tell the user it is up.

Everything lives in `flappy_bird.py`: `GET /` returns the whole page, canvas game
and JavaScript inlined in the `PAGE` string. The page title is "Sammy the Owl" —
the folder name is the generic genre, not the game's name.
