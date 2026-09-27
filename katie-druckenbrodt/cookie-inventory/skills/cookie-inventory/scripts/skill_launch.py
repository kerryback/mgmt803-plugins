#!/usr/bin/env python3
"""Launch the troop cookie inventory manager and open it in the browser.

Invoked by the `cookie-inventory` skill. It:
  1. ensures a small Python environment exists (built once, in the user's home),
  2. starts the FastAPI app on http://127.0.0.1:<port> (default 8032),
  3. opens it in the browser.

The troop's records live in ~/.cookie-inventory/cookie_inventory.db, outside the
plugin directory, so updating or reinstalling the plugin never touches them.
The app holds no state Claude Code needs to poll: once it is open, the troop
leader works in the browser and there is nothing to hand back.

Usage:
  python3 scripts/skill_launch.py [--port 8032]

Runs in the foreground and keeps the server alive; stop it with Ctrl-C.
"""
import argparse
import hashlib
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
BACKEND = SKILL / "backend"

# The Python environment and the database live outside the skill directory so
# that updating the plugin never has to touch either one.
HOME_DIR = Path(os.environ.get("COOKIE_INVENTORY_HOME", Path.home() / ".cookie-inventory")).expanduser()
VENV_DIR = HOME_DIR / "venv"


def log(msg):
    print(f"[cookie-inventory] {msg}", flush=True)


def _requirements_sha() -> str:
    return hashlib.sha256((BACKEND / "requirements.txt").read_bytes()).hexdigest()


def ensure_venv() -> Path:
    py = VENV_DIR / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    stamp = VENV_DIR / "requirements.sha"
    want = _requirements_sha()
    if py.exists() and stamp.exists() and stamp.read_text().strip() == want:
        return py
    if not py.exists():
        log("Creating the app environment + installing requirements (first run only)…")
        VENV_DIR.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
        subprocess.run([str(py), "-m", "pip", "install", "-q", "--upgrade", "pip"], check=True)
    else:
        log("Updating the app environment…")
    subprocess.run([str(py), "-m", "pip", "install", "-q", "-r",
                    str(BACKEND / "requirements.txt")], check=True)
    stamp.write_text(want)
    return py


def preflight():
    db = HOME_DIR / "cookie_inventory.db"
    if db.exists():
        log(f"Using the existing troop database at {db}")
    else:
        log(f"No database yet — a fresh one will be created at {db}, seeded with "
            "27 numbered scouts and the ABC Bakers varieties at $6 a box.")
    has_file = (HOME_DIR / "env.txt").exists() or (HOME_DIR / ".env").exists()
    if not os.environ.get("OPENROUTER_API_KEY") and not has_file:
        log("NOTE: no OpenRouter key found, so the 'Ask Tony' chatbot tab will say "
            "it has no phone line. Every other page works without one. To enable it, "
            "get a key at openrouter.ai and write OPENROUTER_API_KEY=sk-or-... into "
            f"{HOME_DIR / 'env.txt'}, then relaunch. An OpenAI key will not work — "
            "the requests go to OpenRouter.")


def wait_up(base: str, timeout: float = 30.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(base + "/", timeout=2)
            return True
        except urllib.error.HTTPError:
            return True  # server answered (any status) = up
        except Exception:
            time.sleep(0.5)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8032)
    args = ap.parse_args()

    py = ensure_venv()
    preflight()

    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    base = f"http://127.0.0.1:{args.port}"
    log(f"Starting the app on {base} …")
    server = subprocess.Popen(
        [str(py), "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", str(args.port)],
        cwd=BACKEND, env=env)
    try:
        if not wait_up(base):
            raise SystemExit(
                f"Server did not come up on port {args.port}. If that port is in "
                "use, rerun with a different one, e.g. --port 8033.")
        webbrowser.open(base + "/")
        log(f"Open: {base}/")
        log("Leave this running while you use it. Press Ctrl-C to stop the app.")
        server.wait()
    finally:
        if server.poll() is None:
            server.terminate()


if __name__ == "__main__":
    main()
