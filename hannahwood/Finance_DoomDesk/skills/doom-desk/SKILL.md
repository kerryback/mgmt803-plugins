---
name: doom-desk
description: >-
  Launch Doom Desk, a local FastAPI market-recap app that pulls the last six
  trading days for SPY, IEF, UUP, GLD and USO from Yahoo Finance, computes the
  returns, and has Claude narrate them as pessimistically as possible. Use when the
  user says "/doom-desk", "start doom desk", "give me the grim market recap", or
  wants this week's returns with dark commentary. Needs the user's own Anthropic API
  key.
---

# /doom-desk

A market-recap app: real returns for five ETFs, narrated as grimly as possible.
`<plugin-dir>` is this plugin's directory.

| Ticker | Asset |
|---|---|
| SPY | S&P 500 |
| IEF | 7–10yr US Treasuries |
| UUP | US Dollar index |
| GLD | Gold |
| USO | Crude oil |

## Before launching

Needs an Anthropic API key, resolved in this order: the `ANTHROPIC_API_KEY`
environment variable, then `env.txt` in `<plugin-dir>`, then `env.txt` in the parent
folder. With none set, the app prompts on stdin and saves to the gitignored
`env.txt`. That prompt can't be answered from a background process, so if no key is
configured, have the user run it once in their own terminal.

## Launching

1. Install dependencies if needed: `pip install -r "<plugin-dir>/requirements.txt"`
   (this one pulls `yfinance` as well as `anthropic` and FastAPI).
2. Run it in the background, from `<plugin-dir>`:

   ```
   python doom_bot.py
   ```

It serves on port 8003 and opens `http://localhost:8003` itself, so don't open a
second tab. Tell the user to click "Generate this week's doom". It blocks while
serving, so it must run in the background.

## What it exposes

- `GET /` — one tile per asset with its period return, the report, and a follow-up chat
- `GET /market` — raw closes, daily returns and period returns as JSON, no commentary
- `POST /doom` — fetches fresh data and starts a new conversation with the report
- `POST /chat` — a follow-up question; without a `session_id` it seeds a new
  conversation with fresh market data
- `DELETE /chat/{session_id}` clears a conversation

"Past 6 days" means the last six trading-day closes, giving five daily returns plus
the whole-period return, on adjusted closes. The system prompt restricts Claude to
the real numbers, with no invented news. Not financial advice.
