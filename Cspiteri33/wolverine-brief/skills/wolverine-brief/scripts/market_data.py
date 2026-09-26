"""Fetch the last week of prices for five market ETFs and print them for the brief.

Tickers: SPY (stocks), IEF (7-10yr Treasuries), UUP (US dollar), GLD (gold), USO (oil).

Run with any Python 3.9+:  python3 market_data.py
On first use it creates a private virtualenv at ~/.wolverine-brief/venv with
yfinance and pandas, then re-runs itself there. Your system Python is not modified.
"""
import os
import subprocess
import sys
from pathlib import Path

VENV = Path.home() / ".wolverine-brief" / "venv"
VENV_PY = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

TICKERS = ["SPY", "IEF", "UUP", "GLD", "USO"]
NAMES = {
    "SPY": "S&P 500 ETF (SPY)",
    "IEF": "7-10yr Treasury ETF (IEF)",
    "UUP": "US Dollar ETF (UUP)",
    "GLD": "Gold ETF (GLD)",
    "USO": "Oil ETF (USO)",
}


def ensure_runtime() -> None:
    """Re-run inside the private venv, creating it on first use."""
    if Path(sys.prefix).resolve() == VENV.resolve():
        return
    if not VENV_PY.exists():
        print("First run: setting up ~/.wolverine-brief/venv (yfinance, pandas)...", file=sys.stderr)
        subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)
        subprocess.run([str(VENV_PY), "-m", "pip", "install", "-q", "--upgrade", "pip"], check=True)
        subprocess.run([str(VENV_PY), "-m", "pip", "install", "-q", "yfinance", "pandas"], check=True)
    os.execv(str(VENV_PY), [str(VENV_PY), __file__, *sys.argv[1:]])


def main() -> None:
    ensure_runtime()
    import yfinance as yf

    raw = yf.download(TICKERS, period="10d", auto_adjust=True, progress=False)
    prices = raw["Close"].dropna(how="all").tail(6)
    if prices.empty:
        sys.exit("No price data came back from Yahoo Finance. Try again in a minute.")
    returns = prices.pct_change().dropna(how="all")
    cumulative = (prices.iloc[-1] / prices.iloc[0] - 1) * 100

    print(f"Market data from {prices.index[0].date()} to {prices.index[-1].date()} "
          "(Yahoo Finance, adjusted closes)\n")
    print("CLOSING PRICES (USD):")
    print(prices[TICKERS].round(2).to_string())
    print("\nDAILY RETURNS (%):")
    print((returns[TICKERS] * 100).round(2).to_string())
    print("\nCUMULATIVE RETURN OVER THE PERIOD:")
    for t in TICKERS:
        if t in cumulative.index:
            print(f"  {NAMES[t]}: {cumulative[t]:+.2f}%")


if __name__ == "__main__":
    main()
