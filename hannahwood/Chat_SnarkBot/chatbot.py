import os
import uuid
from pathlib import Path

import anthropic
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

HERE = Path(__file__).resolve().parent
KEY_FILES = [HERE / "env.txt", HERE.parent / "env.txt"]  # checked in this order
MODEL = "claude-sonnet-5"
EFFORT = "low"
SYSTEM_PROMPT = "speak with maximum irreverent snark and roast the user whenever possible"


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


app = FastAPI(title="Snark Bot")
_client = None

# session_id -> list of {"role", "content"} messages (in-memory, resets on restart)
sessions: dict[str, list[dict]] = {}


def get_client():
    global _client
    if _client is None:
        key = find_api_key()
        if not key:
            raise HTTPException(500, "No Anthropic API key found. Put ANTHROPIC_API_KEY=... in env.txt next to chatbot.py.")
        _client = anthropic.Anthropic(api_key=key)
    return _client


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(400, "Message is empty. Much like your argument.")

    client = get_client()
    session_id = req.session_id or str(uuid.uuid4())
    history = sessions.setdefault(session_id, [])
    history.append({"role": "user", "content": req.message})

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
        return ChatResponse(reply="(The model declined to respond to that.)", session_id=session_id)

    reply = "".join(b.text for b in response.content if b.type == "text")
    history.append({"role": "assistant", "content": reply})
    return ChatResponse(reply=reply, session_id=session_id)


@app.delete("/chat/{session_id}")
def reset(session_id: str):
    sessions.pop(session_id, None)
    return {"ok": True}


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Snark Bot</title>
<style>
  :root { --bg:#fafafa; --fg:#1a1a1a; --muted:#666; --me:#2563eb; --bot:#e9e9ee; --border:#ddd; }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#16161a; --fg:#eee; --muted:#999; --me:#3b82f6; --bot:#2a2a31; --border:#333; }
  }
  * { box-sizing: border-box; }
  body { margin:0; font-family: system-ui, sans-serif; background:var(--bg); color:var(--fg);
         display:flex; flex-direction:column; height:100vh; max-width:760px; margin-inline:auto; padding:16px; }
  header { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; }
  h1 { font-size:1.3rem; margin:0; }
  #log { flex:1; overflow-y:auto; display:flex; flex-direction:column; gap:10px; padding:4px; }
  .msg { max-width:80%; padding:10px 14px; border-radius:14px; white-space:pre-wrap; line-height:1.4; }
  .me { align-self:flex-end; background:var(--me); color:#fff; }
  .bot { align-self:flex-start; background:var(--bot); }
  .err { align-self:center; color:#dc2626; font-size:.9rem; }
  form { display:flex; gap:8px; margin-top:12px; }
  input { flex:1; padding:12px; border-radius:10px; border:1px solid var(--border); background:var(--bg); color:var(--fg); font-size:1rem; }
  button { padding:0 18px; border-radius:10px; border:0; background:var(--me); color:#fff; font-size:1rem; cursor:pointer; }
  button:disabled { opacity:.5; }
  #reset { background:transparent; color:var(--muted); border:1px solid var(--border); padding:6px 12px; }
</style>
</head>
<body>
<header><h1>Snark Bot</h1><button id="reset">New chat</button></header>
<div id="log"></div>
<form id="f"><input id="q" placeholder="Say something. It'll be used against you." autocomplete="off" autofocus><button id="send">Send</button></form>
<script>
let sessionId = null;
const log = document.getElementById('log'), q = document.getElementById('q'), send = document.getElementById('send');
function add(text, cls) {
  const d = document.createElement('div'); d.className = 'msg ' + cls; d.textContent = text;
  log.appendChild(d); log.scrollTop = log.scrollHeight; return d;
}
document.getElementById('f').onsubmit = async (e) => {
  e.preventDefault();
  const message = q.value.trim(); if (!message) return;
  add(message, 'me'); q.value = ''; send.disabled = true;
  const pending = add('...', 'bot');
  try {
    const r = await fetch('/chat', { method:'POST', headers:{'Content-Type':'application/json'},
                                     body: JSON.stringify({ message, session_id: sessionId }) });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || r.statusText);
    sessionId = data.session_id; pending.textContent = data.reply;
  } catch (err) { pending.remove(); add('Error: ' + err.message, 'err'); }
  send.disabled = false; q.focus();
};
document.getElementById('reset').onclick = async () => {
  if (sessionId) await fetch('/chat/' + sessionId, { method:'DELETE' });
  sessionId = null; log.innerHTML = ''; q.focus();
};
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
        print("Snark Bot needs an Anthropic API key (get one at https://console.anthropic.com/).")
        key = input("Paste your key here and press Enter: ").strip()
        if key:
            (HERE / "env.txt").write_text(f"ANTHROPIC_API_KEY={key}\n", encoding="utf-8")
            print(f"Saved to {HERE / 'env.txt'} so you won't be asked again.\n")

    PORT = 8002
    url = f"http://localhost:{PORT}"
    print(f"Snark Bot running at {url}  (close this window to stop it)")
    threading.Timer(1.5, webbrowser.open, args=[url]).start()
    try:
        uvicorn.run(app, host="127.0.0.1", port=PORT)
    except Exception as e:
        print(f"\nFailed to start: {e}")
    input("\nServer stopped. Press Enter to close...")
