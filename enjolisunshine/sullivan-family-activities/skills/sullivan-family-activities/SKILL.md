---
name: sullivan-family-activities
description: >-
  Scaffold a local family organizer web app: a FastAPI + SQLite backend with
  a shared calendar, tasks and chores (point rewards, sticker charts, turn
  rotation for kids), a prize shop kids redeem points against, home
  maintenance reminders, a PIN-protected parent settings area, kid mode, and
  a QR code for linking a phone on the same Wi-Fi. Trigger on "build a family
  organizer app", "family chore chart / rewards app", "family calendar and
  tasks app", or when adapting this app for a different family's members,
  chores, or prizes.
license: MIT
---

# sullivan-family-activities

Produces a full local-first family organizer: FastAPI backend, Jinja2
templates, vanilla JS, SQLite storage (stdlib `sqlite3`, no ORM). Built
originally for one family (the Sullivans) — when scaffolding for someone
else, rename the family, database file, and prize shop to match.

Files worth knowing before you touch anything (all under `app/`):

- `main.py` — route table. Page routes (`/`, `/calendar`, `/tasks`,
  `/chores`, `/maintenance`, `/rewards`, `/family`, `/settings`, `/kids`,
  `/kids/{member_id}`) render templates; `/api/*` is the JSON API consumed
  by `static/js/app.js`. A catch-all `/{section}` (registered last, so it
  never shadows the routes above) renders `coming_soon.html` for nav items
  that don't have a real page yet (meal-plan, shopping, notes, birthdays,
  travel — add these the same way as the built pages when asked to).
- `services.py` — all the business logic (CRUD for members/events/tasks,
  point/reward math, chore rotation, recurrence expansion, summary/search).
  The biggest file; read the relevant function before changing behavior
  rather than guessing.
- `schemas.py` — Pydantic request bodies (`MemberIn`, `EventIn`, `TaskIn`,
  `PrizeIn`, `BonusIn`, `PinIn`, ...). `TaskIn` covers both plain tasks and
  chores (`category: task|chore`) — chores can carry a `rotation` list of
  member ids so the assignee rotates daily or weekly.
- `db.py` — schema + connection. `DB_PATH` reads from an env var
  (`SULLIVAN_DB`) with a default filename next to the app folder — rename
  both the env var and default filename to match a new family.
- `seed.py` — `seed_if_empty` creates the family members and a starter
  prize shop on a brand-new database (no sample events/tasks). Edit the
  `FAMILY` and `STARTER_PRIZES` lists here for a different family.
- `qr.py` — a self-contained QR encoder (no `qrcode` dependency, no
  internet needed) used by `/api/phone-link/qr.svg` so a phone on the same
  Wi-Fi can scan in.
- `icons.py` — a small SVG icon set (`ICONS` dict) used across templates.

## Workflow

1. **Copy the template** into the target project directory:
   ```
   cp -r "$SKILL_DIR/assets/." <target-dir>/
   ```
   This gives `<target-dir>/app/` (the package) and
   `<target-dir>/requirements.txt` side by side — `app/main.py` is run as
   `uvicorn app.main:app`, not `uvicorn main:app`.
2. **Rename the family** if scaffolding for someone other than the
   Sullivans: edit `FAMILY` and `STARTER_PRIZES` in `app/seed.py`, and
   rename the `SULLIVAN_DB` env var and default db filename in `app/db.py`
   to match (e.g. `<name>_family.db`). Delete any existing `.db` file
   before the next run so `seed_if_empty` re-seeds cleanly.
3. **Install and run**, following this workspace's web-app convention:
   ```
   pip install -r requirements.txt
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
   Bind `0.0.0.0`, not `127.0.0.1` — required for the app to be reachable
   outside the container, and for the phone-link QR code to resolve on the
   home Wi-Fi.
4. **Verify** by loading `/`, adding a family member, creating a task and a
   calendar event, and redeeming a prize, before calling it done.

## Notes

- Points/rewards: `BonusIn` gives ad-hoc points with a sticker; completing
  a task/chore awards its `points`; `RedeemIn` spends points against a
  `PrizeIn`, going through an approve/decline flow in `services.py` rather
  than deducting immediately.
- Chore rotation: a `TaskIn` with more than one id in `rotation` rotates the
  assignee `rotate_every` "day" or "week"; with exactly one id it collapses
  to a plain `member_id` (see the `_check` validator in `schemas.py`).
- Recurrence (`none|daily|weekdays|weekly|biweekly|monthly|quarterly|
  semiannual|yearly`) is shared by events and tasks — expand it in
  `services.py`, don't duplicate the logic per page.
- Settings are PIN-gated (`PinIn`/`PinCheck`, 4-digit). Forgetting the PIN
  is handled out-of-band: dropping a `RESET-PIN.txt` file in the app folder
  and restarting clears it (`seed.reset_pin_if_requested`).
- Photos upload as base64 JSON (`PhotoIn`), not multipart form data — no
  `python-multipart` dependency needed.
- Keep frontend URLs relative (no leading slash) so the app works when
  served under a sub-path.
