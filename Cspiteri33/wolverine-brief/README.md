# wolverine-brief

A weekly cross-asset market brief, delivered by Wolverine.

Ask Claude for a Wolverine market brief and it pulls the last six trading days of
prices for five ETFs from Yahoo Finance, then gives a short, blunt recap in Logan's
voice: the biggest winners and losers, standout days, how stocks, bonds, the dollar,
gold and oil moved against each other, and what to watch next.

| Ticker | Market |
| --- | --- |
| SPY | S&P 500 stocks |
| IEF | 7-10 year US Treasuries |
| UUP | US dollar |
| GLD | Gold |
| USO | Oil |

## Install

```
/plugin marketplace add kerryback/mgmt803-plugins
/plugin install wolverine-brief@mgmt803
```

Start a fresh session, then ask something like "give me the Wolverine market brief".

## Requirements

- Python 3.9 or newer (`python3`) and an internet connection.
- No API key. The first run sets up a private Python environment at
  `~/.wolverine-brief/venv` with yfinance and pandas; your system Python is untouched.
  Delete that folder to remove it.

The brief is entertainment and education, not investment advice.
