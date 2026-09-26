# density-weight-converter

A density-to-weight unit converter: a single-file FastAPI app and form UI
that converts a density (g/cm3) and a volume (ft3) into a weight in pounds,
with an optional mode that converts a thickness and an acreage into tons per
acre.

## Install

```
/plugin marketplace add kerryback/mgmt803-plugins
/plugin install density-weight-converter@mgmt803
```

Then ask Claude to scaffold the app, or to adapt it (different units,
different formula, extra modes, etc.).

## What it bundles

- `app.py` — FastAPI app with `GET /` (serves the form, HTML inlined) and
  `POST /calculate` (density/volume math, plus a tons-per-acre mode).
- `requirements.txt` — fastapi, uvicorn.

Run it with `uvicorn app:app --host 0.0.0.0 --port 8000` from the copied
folder.
