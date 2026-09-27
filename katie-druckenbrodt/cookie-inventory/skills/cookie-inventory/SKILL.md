---
name: cookie-inventory
description: >-
  Launch the troop cookie inventory manager, a local app for running a Girl Scout
  cookie season on ABC Bakers varieties. Use when the user says "/cookie-inventory",
  "open the cookie inventory", "track troop cookie stock", or wants to receive a
  cookie shipment, check boxes out to a scout, record a booth sale or a parent's
  payment, see who owes what, or read the season ledger. Every box and dollar figure
  is computed live from a SQLite ledger — nothing is hardcoded. Also serves a
  parent-facing chatbot, in Tony Soprano's voice, that looks up a scout's balance and
  checks out more boxes using only that database.
argument-hint: "[what you want to do]"
---

# /cookie-inventory

A local web app for a 27-scout ABC Bakers troop: troop stock, per-scout checkouts,
booth sales, payments, and a full transaction ledger. `<skill-dir>` is the "Base
directory for this skill" reported when the skill is invoked; use that absolute
path.

## What to do

1. Launch the app in the background:

   ```
   python3 "<skill-dir>/scripts/skill_launch.py"
   ```

   On first run it builds a private virtualenv at `~/.cookie-inventory/venv` and
   installs FastAPI, uvicorn and the OpenAI client, then serves the app on
   `http://127.0.0.1:8032` and opens a browser tab. If the port is in use, rerun
   with `--port 8033`.

2. Say which page answers what the user asked for, and let them work in the
   browser. The app has no API for you to drive and keeps no session state you need
   to poll, so once it is open your job is to point, not to operate:

   - **Dashboard** (`/`) — boxes on hand per variety, total boxes, outstanding owed
     by scouts, and cash collected.
   - **Scouts** (`/scouts`) — the roster, each scout's boxes out and balance;
     rename a scout here.
   - **Cookie Varieties** (`/varieties`) — set the per-box price, add a variety.
   - **Receive Stock** (`/inventory`) — log a shipment arriving from the bakery.
   - **Checkout to Scout** (`/checkout`) — hand boxes to a scout, or take them
     back as a return.
   - **Booth Sale** (`/booth`) — boxes sold straight from troop stock at a booth.
   - **Record Payment** (`/payments`) — money a scout or parent turned in.
   - **Full Ledger** (`/ledger`) — every transaction, newest first.
   - **Ask Tony** (`/chatbot`) — the parent-facing chatbot.

3. On a first run, mention the two setup steps the app can't do for them: the
   varieties are seeded at **$6.00 a box** and the roster as **Scout 1 … Scout 27**,
   so real prices go on the Varieties page and real names on the Scouts page. The
   dashboard shows a warning for any variety still priced at $0.00, because a zero
   price silently understates what scouts owe.

## The ledger is the source of truth

There is no editable stock number anywhere. Boxes on hand and dollars owed are
recomputed from the transaction table on every page load, by transaction type:
`receive` and `return` add boxes to troop stock, `checkout` and `booth_sale`
subtract them, and `adjustment` is the escape hatch. A scout's balance is her
checkouts minus her returns minus her payments.

So corrections are made by recording the opposite transaction, not by editing a
total. If the user wants to undo a mistaken checkout, record the matching return;
if a count is off for a reason the ledger can't express, an `adjustment` row is
the honest way to say so. Don't offer to reach into the database to fix a number —
that breaks the one guarantee the app makes about its own figures.

## The chatbot

`/chatbot` answers parents in Tony Soprano's voice — blunt North Jersey, PG-rated,
because kids read over their parents' shoulders. It has exactly two tools,
`check_balance` and `request_cookies`, and its instructions forbid stating any
number that didn't come from one of them. `request_cookies` writes a real checkout
row against troop stock and refuses when the stock isn't there, so it is a working
part of the app, not a demo.

It needs an OpenRouter key (it calls `openai/gpt-4o-mini` through
`https://openrouter.ai/api/v1`). Without one, the chatbot says it has no phone line
and everything else in the app still works. To enable it: get a key at
openrouter.ai and write `OPENROUTER_API_KEY=sk-or-...` into
`~/.cookie-inventory/env.txt`, then relaunch.

An OpenAI key will not work here, whatever variable it's in — the requests go to
OpenRouter, not to OpenAI. `OPENROUTER_API_KEY` is read first for exactly that
reason, and `OPENAI_API_KEY` is only a fallback for someone who already set it up
that way. `~/.cookie-inventory/env.txt` overrides whatever is exported in the
shell, so an unrelated OpenAI key in the environment can't quietly shadow the
right one.

## Where the data lives

`~/.cookie-inventory/cookie_inventory.db` — deliberately outside the plugin
directory, so updating or reinstalling the plugin can't destroy a season's
records. `COOKIE_INVENTORY_HOME` moves that whole directory; `COOKIE_INVENTORY_DB`
moves just the database, which is the way to keep separate books for separate
troops or to open last season's file.

Because the file is the troop's real bookkeeping, treat it as such: back it up by
copying it before anything experimental, and never delete or recreate it to clear
a problem without asking first.

## Scope

The varieties are this troop's ABC Bakers lineup — Thin Mints, Caramel deLites,
Peanut Butter Patties, Peanut Butter Sandwich, Trefoils, Lemonades, Adventurefuls,
Exploremores. Little Brownie Bakers troops use different names for some of the same
cookies (Samoas for Caramel deLites, Tagalongs for Peanut Butter Patties); if a user
is on that lineup, the Varieties page is where they rename or add.

The app tracks boxes and money. It doesn't file with the council, produce the
council's own reports, or handle online (Digital Cookie) orders — those come back
into this app as a `receive` and a `booth_sale` or `checkout`, recorded by hand.

The header expects a square photo at `backend/static/binx.jpeg` — Binx, the troop's
lop-eared rabbit mascot. The photo is the troop's own and isn't distributed with the
plugin, so the banner simply runs without it. Dropping any square image in at that
path restores it.
