---
name: density-weight-converter
description: >-
  Scaffold a density-to-weight unit converter web app: a FastAPI backend and
  single-page form that converts a density (g/cm3) and a volume (ft3) into a
  weight in pounds, with an optional tons-per-acre mode from a thickness and
  an acreage. Trigger on "build a unit converter", "density to weight app",
  "tons per acre calculator", or when adapting this app to new units or
  formulas.
license: MIT
---

# density-weight-converter

Produce a single-file FastAPI app: one form, one calculation endpoint, no
templates or static assets needed.

- `app.py` — `GET /` renders the form (HTML is inlined in `HTML_PAGE`);
  `POST /calculate` takes a JSON body of `density` plus either `volume`, or
  `thickness` and `acres`, and returns the converted weight.
  - Plain mode: `pounds = density * volume * CM3_PER_FT3 / GRAMS_PER_POUND`.
  - Tons-per-acre mode: computes `volume_ft3 = thickness * acres *
    SQFT_PER_ACRE`, then weight and tons the same way, then divides tons by
    acres.
  - Conversion constants: `GRAMS_PER_POUND = 453.59237`,
    `CM3_PER_FT3 = 28316.846592`, `SQFT_PER_ACRE = 43560`,
    `POUNDS_PER_TON = 2000`.

## Workflow

1. **Copy the template** into the target project directory:
   ```
   cp -r "$SKILL_DIR/assets/." <target-dir>/
   ```
2. **Adapt the units** if asked for something beyond density/volume/weight
   (a different input unit, an extra conversion step, a new mode alongside
   tons-per-acre): edit the constants, the `/calculate` endpoint, and the
   matching fields/script in `HTML_PAGE` together — they're a matched set.
3. **Install and run**, following this workspace's web-app convention:
   ```
   pip install -r requirements.txt
   uvicorn app:app --host 0.0.0.0 --port 8000
   ```
   Bind `0.0.0.0`, not `127.0.0.1` — required for the app to be reachable
   outside the container.
4. **Verify** by loading the page and running both modes (plain volume, and
   tons-per-acre) with real numbers before calling it done.

## Notes

- The frontend calls `fetch("calculate", ...)` — no leading slash — so the
  app keeps working when served under a sub-path.
- Toggling "Convert to tons per acre" swaps which input fields are shown and
  which fields the POST body carries; keep that toggle logic and the two
  request shapes in sync if you add fields.
