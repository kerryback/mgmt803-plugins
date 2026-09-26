---
name: penguoom
description: >-
  Launch Penguoom, a Doom-style first-person shooter starring a penguin across ten
  winter sectors, including a Christmas Village. Use when the user says
  "/penguoom", "play penguoom", "start the penguin shooter", or wants a retro FPS in
  the browser. A single self-contained HTML file — canvas raycaster, Web Audio sound
  and music, no dependencies and no build step.
---

# /penguoom

A retro raycaster FPS. Ten winter sectors, against penguins, polar bears, walruses
and stoats. `<plugin-dir>` is this plugin's directory.

## Launching

The whole game is one static HTML file, so there is nothing to install and no server
needed. Open it directly:

```
open "<plugin-dir>/index.html"
```

On Linux use `xdg-open`. If the browser blocks audio or pointer lock on a
`file://` URL, serve the folder instead and open the printed URL:

```
python3 -m http.server 8014 --directory "<plugin-dir>"
```

The author also hosts it at https://tfensign.github.io/Penguoom/, which is the
simplest option when local audio misbehaves.

## Notes

Works with keyboard and mouse or with touch. Everything — the raycaster, the sound
and music, the sprites — is inlined in `index.html` (about 120 KB), so there is no
API to drive from here and no session state. Once it is open there is nothing
further to do. Full source and history at https://github.com/tfensign/Penguoom.
