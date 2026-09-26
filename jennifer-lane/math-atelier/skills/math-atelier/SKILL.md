---
name: math-atelier
description: >-
  Launch The Math Atelier, a self-contained browser app for math practice. Use when
  the user says "/math-atelier", "open the math atelier", "give me math practice",
  or wants a drill page for arithmetic practice. A single HTML file with no
  dependencies and no build step.
---

# /math-atelier

A browser app for math practice. `<plugin-dir>` is this plugin's directory.

## Launching

One static HTML file, so there is nothing to install and no server needed:

```
open "<plugin-dir>/math-atelier.html"
```

On Linux use `xdg-open`. If anything is blocked on a `file://` URL, serve the folder
and open the printed URL instead:

```
python3 -m http.server 8015 --directory "<plugin-dir>"
```

## Notes

Everything is inlined in `math-atelier.html` (about 26 KB) — no API, no server, no
session state, so once it is open there is nothing further to do. Practice settings
are chosen in the page itself.
