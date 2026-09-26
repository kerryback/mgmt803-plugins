# Doom Desk

A market-recap chatbot that describes the week in the most pessimistic, dark-humored way possible. It pulls the last 6 trading days of prices for five ETFs from Yahoo Finance, computes the returns, and asks Claude Sonnet 5 (low effort) to narrate the carnage. Built with FastAPI.

| Ticker | Asset |
| --- | --- |
| SPY | S&P 500 (US stocks) |
| IEF | 7-10yr US Treasuries |
| UUP | US Dollar index |
| GLD | Gold |
| USO | Crude oil |

The system prompt tells Claude to cite only the real numbers (no invented news), cover all five assets and what they "ominously imply" together, and end with a grim one-line outlook. Every rally is a dead-cat bounce.

## Run it

You need Python 3 and your own [Anthropic API key](https://console.anthropic.com/).

**Windows:** double-click `Start Doom Desk.bat`. It installs the requirements if needed, asks for your API key the first time, then opens the page in your browser.

**Any OS:**

```bash
pip install -r requirements.txt
python doom_bot.py
```

Then go to http://localhost:8003 and click **Generate this week's doom**. Ask follow-up questions in the box below. Close the console window to stop it.

### Where the API key goes

The app looks for `ANTHROPIC_API_KEY` in this order:

1. An environment variable
2. `env.txt` in this folder, as a line like `ANTHROPIC_API_KEY=sk-ant-...`
3. `env.txt` in the parent folder

If none is found, `python doom_bot.py` asks for the key and saves it to `env.txt`. That file is in `.gitignore`, so it won't get committed.

## How it's built

Everything is in [`doom_bot.py`](doom_bot.py): a FastAPI server that fetches prices with `yfinance`, serves the page, and calls the Claude API.

- `GET /` is the page: one tile per asset with its period return, the doom report, and a follow-up chat
- `GET /market` returns the raw closes, daily returns, and period returns as JSON (no commentary)
- `POST /doom` fetches fresh data and starts a new conversation with the week's report. Returns `{"reply", "session_id", "data"}`
- `POST /chat` with `{"message": "...", "session_id": "..."}` asks a follow-up. Without a `session_id`, it starts a new conversation seeded with fresh market data
- `DELETE /chat/{session_id}` clears a conversation

"Past 6 days" means the last 6 trading-day closes, so you get 5 daily returns plus the return over the whole period. Prices are adjusted closes. Conversations are kept in memory, so they're gone when the server restarts.

Not financial advice. Obviously.
