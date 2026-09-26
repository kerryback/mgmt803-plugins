# sullivan-family-activities

A local family organizer: FastAPI + SQLite backend with a shared calendar,
tasks and chores (point rewards, sticker charts, turn rotation for kids), a
prize shop, home maintenance reminders, kid mode, and a phone-link QR code
so a phone on the same Wi-Fi can open the app. Settings are PIN-protected.

## Install

```
/plugin marketplace add kerryback/mgmt803-plugins
/plugin install sullivan-family-activities@mgmt803
```

Then ask Claude to scaffold the app, or to adapt it for a different family,
different chores/prizes, or a new page (meal plan, shopping list, etc.).

## What it bundles

- `app/main.py` — FastAPI routes: pages (`/`, `/calendar`, `/tasks`,
  `/chores`, `/maintenance`, `/rewards`, `/family`, `/settings`, `/kids`)
  plus a `/api/*` JSON API.
- `app/services.py` — CRUD, point/reward math, chore rotation, recurrence.
- `app/schemas.py` — Pydantic request models.
- `app/db.py` — SQLite schema and connection (stdlib `sqlite3`).
- `app/seed.py` — seeds the family and a starter prize shop on first run.
- `app/qr.py` — self-contained QR code generator for the phone-link page.
- `app/icons.py` — shared SVG icon set.
- `app/templates/`, `app/static/` — Jinja2 templates, CSS, and JS.
- `requirements.txt` — fastapi, uvicorn, jinja2.

Run it with `uvicorn app.main:app --host 0.0.0.0 --port 8000` from the
copied folder.
