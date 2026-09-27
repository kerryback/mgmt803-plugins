# cookie-inventory

A local web app for running a Girl Scout cookie season: troop stock by variety,
boxes checked out to each of 27 scouts, booth sales, payments, and a full
transaction ledger. Built for an ABC Bakers troop.

Every box count and dollar figure on every page is recomputed from the
transaction ledger on load — there is no stored total to drift out of date.

## Install

```
/plugin marketplace add kerryback/mgmt803-plugins
/plugin install cookie-inventory@mgmt803
```

Start a fresh session, then say `/cookie-inventory` or ask to open the cookie
inventory. The first launch builds a private virtualenv at
`~/.cookie-inventory/venv` and serves the app at http://127.0.0.1:8032.

## The pages

| Page | What it does |
| --- | --- |
| Dashboard | Boxes on hand per variety, total boxes, outstanding owed by scouts, cash collected |
| Scouts | The roster with each scout's boxes out and balance; rename scouts |
| Cookie Varieties | Set the per-box price, add a variety |
| Receive Stock | Log a shipment arriving from the bakery |
| Checkout to Scout | Hand boxes to a scout, or take them back as a return |
| Booth Sale | Boxes sold straight from troop stock at a booth |
| Record Payment | Money a scout or parent turned in |
| Full Ledger | Every transaction, newest first |
| Ask Tony | A parent-facing chatbot (see below) |

## First run

The database is seeded with 27 scouts named `Scout 1` through `Scout 27` and the
ABC Bakers varieties at $6.00 a box. Put the real names in on the Scouts page and
the real prices on the Cookie Varieties page — the dashboard warns about any
variety still at $0.00, since a zero price understates what scouts owe.

## Ask Tony

The chatbot answers parents in Tony Soprano's voice — blunt, PG-rated. It has two
tools, `check_balance` and `request_cookies`, and it isn't allowed to state a
number that didn't come from one of them. `request_cookies` writes a real checkout
against troop stock and refuses when the boxes aren't there.

It needs an OpenRouter key: get one at openrouter.ai and put

```
OPENROUTER_API_KEY=sk-or-...
```

in `~/.cookie-inventory/env.txt`. That file overrides anything exported in your
shell. An OpenAI key won't work — the requests go to OpenRouter. Without a key the
chatbot says so and the rest of the app works normally.

## Your data

Records live in `~/.cookie-inventory/cookie_inventory.db`, outside the plugin
directory, so updating or reinstalling the plugin never touches them. Set
`COOKIE_INVENTORY_DB` to keep separate books for separate troops or to open a
previous season. Copy the file to back up a season.

## The mascot

The banner expects a square photo at `skills/cookie-inventory/backend/static/binx.jpeg`
— Binx, the troop's lop-eared rabbit. That photo is the troop's own and isn't
shipped here, so the banner runs without it; drop any square image in at that path
to bring it back.
