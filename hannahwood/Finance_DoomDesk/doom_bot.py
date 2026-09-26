import os
import uuid
from pathlib import Path

import anthropic
import yfinance as yf
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

HERE = Path(__file__).resolve().parent
KEY_FILES = [HERE / "env.txt", HERE.parent / "env.txt"]  # checked in this order
MODEL = "claude-sonnet-5"
EFFORT = "low"
TICKERS = {
    "SPY": "S&P 500 (US stocks)",
    "IEF": "7-10yr US Treasuries",
    "UUP": "US Dollar index",
    "GLD": "Gold",
    "USO": "Crude oil",
}
DAYS = 6
SYSTEM_PROMPT = """You are the Doom Desk: a financial market commentator who describes the week's market \
events in the most pessimistic, dark-humored way possible. Every rally is a dead-cat bounce, every \
dip is the first domino, and every flat line is the calm before the storm. Think gallows humor from \
a burned-out trader who has seen too much.

Rules:
- Ground every claim in the actual numbers provided. Cite the real returns; never invent prices or news.
- Cover all five assets (stocks, Treasuries, the dollar, gold, oil) and what their moves "together" \
ominously imply (e.g. flight to safety, inflation fears, dollar strength crushing everyone).
- Be bleak and funny, not cruel toward real people or groups. Doom the markets, not humans.
- Keep it punchy: a headline, then a few short paragraphs or bullets.
- End with a one-line "Outlook" that is hilariously grim.
- If the user asks follow-ups, stay in character and keep using the data."""


def find_api_key():
    """ANTHROPIC_API_KEY from the environment, else from an env.txt (KEY=value lines)."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return os.environ["ANTHROPIC_API_KEY"]
    for path in KEY_FILES:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            key, sep, value = line.partition("=")
            if sep and key.strip() == "ANTHROPIC_API_KEY":
                return value.strip().strip('"').strip("'")
    return None


def get_market_data():
    """Last DAYS trading-day closes for TICKERS, plus daily and period returns."""
    # threads=False avoids yfinance's "database is locked" cache error on Windows/OneDrive
    closes = yf.download(list(TICKERS), period="1mo", auto_adjust=True,
                         progress=False, threads=False)["Close"].dropna().tail(DAYS)
    if len(closes) < 2:
        raise RuntimeError("Not enough price data returned from Yahoo Finance.")
    daily = closes.pct_change().dropna() * 100
    total = (closes.iloc[-1] / closes.iloc[0] - 1) * 100

    dates = [d.strftime("%Y-%m-%d") for d in closes.index]
    assets = []
    for t, name in TICKERS.items():
        assets.append({
            "ticker": t,
            "name": name,
            "closes": [round(float(x), 2) for x in closes[t]],
            "daily_returns_pct": [round(float(x), 2) for x in daily[t]],
            "period_return_pct": round(float(total[t]), 2),
        })
    return {"dates": dates, "assets": assets}


def format_for_prompt(data):
    d = data["dates"]
    lines = [f"Market data: {len(d)} trading days of closes, {d[0]} to {d[-1]}.", ""]
    for a in data["assets"]:
        daily = ", ".join(f"{dt}: {r:+.2f}%" for dt, r in zip(d[1:], a["daily_returns_pct"]))
        lines.append(f"{a['ticker']} ({a['name']}): {a['closes'][0]} -> {a['closes'][-1]}, "
                     f"period return {a['period_return_pct']:+.2f}%")
        lines.append(f"  daily returns: {daily}")
    lines += ["", "Describe this week's market events."]
    return "\n".join(lines)


app = FastAPI(title="Doom Desk")
_client = None

# session_id -> list of {"role", "content"} messages (in-memory, resets on restart)
sessions: dict[str, list[dict]] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str


class DoomResponse(BaseModel):
    reply: str
    session_id: str
    data: dict


def get_client():
    global _client
    if _client is None:
        key = find_api_key()
        if not key:
            raise HTTPException(500, "No Anthropic API key found. Put ANTHROPIC_API_KEY=... in env.txt next to doom_bot.py.")
        _client = anthropic.Anthropic(api_key=key)
    return _client


def ask_claude(history: list[dict]) -> str:
    client = get_client()
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            output_config={"effort": EFFORT},
            messages=history,
        )
    except anthropic.AuthenticationError:
        history.pop()
        raise HTTPException(502, "Anthropic rejected the API key. Check the key in env.txt.")
    except anthropic.APIStatusError as e:
        history.pop()
        raise HTTPException(502, f"Anthropic API error ({e.status_code}): {e.message}")
    except anthropic.APIConnectionError:
        history.pop()
        raise HTTPException(502, "Could not reach the Anthropic API.")

    if response.stop_reason == "refusal":
        history.pop()
        return "(The model declined to respond to that.)"

    reply = "".join(b.text for b in response.content if b.type == "text")
    history.append({"role": "assistant", "content": reply})
    return reply


@app.get("/market")
def market():
    """Raw prices and returns, no commentary."""
    try:
        return get_market_data()
    except Exception as e:
        raise HTTPException(502, f"Market data error: {e}")


@app.post("/doom", response_model=DoomResponse)
def doom():
    """Fetch fresh data and start a new session with the week's doom report."""
    try:
        data = get_market_data()
    except Exception as e:
        raise HTTPException(502, f"Market data error: {e}")

    session_id = str(uuid.uuid4())
    history = sessions.setdefault(session_id, [])
    history.append({"role": "user", "content": format_for_prompt(data)})
    reply = ask_claude(history)
    return DoomResponse(reply=reply, session_id=session_id, data=data)


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Follow-up questions. Without a session, starts one seeded with fresh market data."""
    if not req.message.strip():
        raise HTTPException(400, "Message is empty. Like your portfolio will be.")

    session_id = req.session_id if req.session_id in sessions else str(uuid.uuid4())
    history = sessions.setdefault(session_id, [])
    content = req.message
    if not history:
        try:
            content = format_for_prompt(get_market_data()) + "\n\nUser question: " + req.message
        except Exception as e:
            raise HTTPException(502, f"Market data error: {e}")
    history.append({"role": "user", "content": content})
    return ChatResponse(reply=ask_claude(history), session_id=session_id)


@app.delete("/chat/{session_id}")
def reset(session_id: str):
    sessions.pop(session_id, None)
    return {"ok": True}


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Doom Desk</title>
<style>
  :root { --bg:#fafafa; --fg:#1a1a1a; --muted:#666; --me:#7f1d1d; --bot:#e9e9ee; --border:#ddd;
          --up:#15803d; --down:#b91c1c; }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#111113; --fg:#eee; --muted:#999; --me:#991b1b; --bot:#232329; --border:#333;
            --up:#4ade80; --down:#f87171; }
  }
  * { box-sizing: border-box; }
  body { margin:0; font-family: system-ui, sans-serif; background:var(--bg); color:var(--fg);
         display:flex; flex-direction:column; height:100vh; max-width:820px; margin-inline:auto; padding:16px; }
  header { display:flex; justify-content:space-between; align-items:center; gap:8px; margin-bottom:12px; flex-wrap:wrap; }
  h1 { font-size:1.3rem; margin:0; }
  .sub { color:var(--muted); font-size:.85rem; }
  #tiles { display:grid; grid-template-columns:repeat(5, 1fr); gap:8px; margin-bottom:12px; }
  .tile { border:1px solid var(--border); border-radius:10px; padding:8px 10px; }
  .tile b { display:block; font-size:.95rem; }
  .tile span { font-size:1.1rem; font-variant-numeric:tabular-nums; }
  .tile small { display:block; color:var(--muted); font-size:.72rem; }
  .up { color:var(--up); } .down { color:var(--down); }
  @media (max-width:560px) { #tiles { grid-template-columns:repeat(3, 1fr); } }
  #log { flex:1; overflow-y:auto; display:flex; flex-direction:column; gap:10px; padding:4px; }
  .msg { max-width:85%; padding:10px 14px; border-radius:14px; white-space:pre-wrap; line-height:1.45; }
  .me { align-self:flex-end; background:var(--me); color:#fff; }
  .bot { align-self:flex-start; background:var(--bot); }
  .err { align-self:center; color:var(--down); font-size:.9rem; }
  form { display:flex; gap:8px; margin-top:12px; }
  input { flex:1; min-width:0; padding:12px; border-radius:10px; border:1px solid var(--border); background:var(--bg); color:var(--fg); font-size:1rem; }
  button { padding:0 18px; border-radius:10px; border:0; background:var(--me); color:#fff; font-size:1rem; cursor:pointer; }
  button:disabled { opacity:.5; }
  #doom { padding:8px 14px; }
</style>
</head>
<body>
<header>
  <div><h1>Doom Desk</h1><div class="sub">SPY · IEF · UUP · GLD · USO, last 6 trading days. Abandon hope.</div></div>
  <button id="doom">Generate this week's doom</button>
</header>
<div id="tiles"></div>
<div id="log"></div>
<form id="f"><input id="q" placeholder="Ask a follow-up. The answer will be worse than you think." autocomplete="off"><button id="send">Send</button></form>
<script>
let sessionId = null;
const log = document.getElementById('log'), q = document.getElementById('q'),
      send = document.getElementById('send'), doomBtn = document.getElementById('doom'),
      tiles = document.getElementById('tiles');
function add(text, cls) {
  const d = document.createElement('div'); d.className = 'msg ' + cls; d.textContent = text;
  log.appendChild(d); log.scrollTop = log.scrollHeight; return d;
}
function setReply(el, text) {
  // Escape HTML first, then render **bold** and *italic* only
  const esc = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  el.innerHTML = esc.replace(/\\*\\*(.+?)\\*\\*/g, '<b>$1</b>').replace(/\\*(\\S.*?)\\*/g, '<i>$1</i>');
}
function busy(on) { send.disabled = on; doomBtn.disabled = on; }
function renderTiles(data) {
  tiles.innerHTML = '';
  for (const a of data.assets) {
    const r = a.period_return_pct, t = document.createElement('div');
    t.className = 'tile';
    t.innerHTML = `<b>${a.ticker}</b><span class="${r >= 0 ? 'up' : 'down'}">${r >= 0 ? '+' : ''}${r.toFixed(2)}%</span><small>${a.name}</small>`;
    tiles.appendChild(t);
  }
}
async function post(url, body) {
  const r = await fetch(url, { method:'POST', headers:{'Content-Type':'application/json'},
                               body: body ? JSON.stringify(body) : undefined });
  const data = await r.json();
  if (!r.ok) throw new Error(data.detail || r.statusText);
  return data;
}
doomBtn.onclick = async () => {
  if (sessionId) fetch('/chat/' + sessionId, { method:'DELETE' });
  sessionId = null; log.innerHTML = ''; busy(true);
  const pending = add('Consulting the abyss...', 'bot');
  try {
    const data = await post('/doom');
    sessionId = data.session_id; renderTiles(data.data); setReply(pending, data.reply);
  } catch (err) { pending.remove(); add('Error: ' + err.message, 'err'); }
  busy(false); q.focus();
};
document.getElementById('f').onsubmit = async (e) => {
  e.preventDefault();
  const message = q.value.trim(); if (!message) return;
  add(message, 'me'); q.value = ''; busy(true);
  const pending = add('...', 'bot');
  try {
    const data = await post('/chat', { message, session_id: sessionId });
    sessionId = data.session_id; setReply(pending, data.reply);
  } catch (err) { pending.remove(); add('Error: ' + err.message, 'err'); }
  busy(false); q.focus();
};
fetch('/market').then(r => r.ok ? r.json() : null).then(d => d && renderTiles(d));
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def home():
    return PAGE


if __name__ == "__main__":
    # Lets you double-click this file: starts the server and opens the chat in your browser.
    import threading
    import webbrowser

    import uvicorn

    if not find_api_key():
        print("Doom Desk needs an Anthropic API key (get one at https://console.anthropic.com/).")
        key = input("Paste your key here and press Enter: ").strip()
        if key:
            (HERE / "env.txt").write_text(f"ANTHROPIC_API_KEY={key}\n", encoding="utf-8")
            print(f"Saved to {HERE / 'env.txt'} so you won't be asked again.\n")

    PORT = 8003
    url = f"http://localhost:{PORT}"
    print(f"Doom Desk running at {url}  (close this window to stop it)")
    threading.Timer(1.5, webbrowser.open, args=[url]).start()
    try:
        uvicorn.run(app, host="127.0.0.1", port=PORT)
    except Exception as e:
        print(f"\nFailed to start: {e}")
    input("\nServer stopped. Press Enter to close...")
