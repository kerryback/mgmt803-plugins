#!/usr/bin/env python3
"""Launch the countdown app and open it in the browser.

Invoked by the `countdown` skill. It:
  1. ensures a small Python environment exists (built once, in the user's home),
  2. starts the FastAPI app on http://127.0.0.1:<port> (default 8030),
  3. opens it in the browser.

The app holds no state and needs nothing from Claude Code after launch: it
calls Claude itself (via ANTHROPIC_API_KEY) to design a theme each time someone
types an occasion. There is nothing to hand back and no output file.

Usage:
  python3 scripts/skill_launch.py [--port 8030]

Runs in the foreground and keeps the server alive; stop it with Ctrl-C.
"""
import argparse
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

# The Python environment lives outside the skill directory so that updating
# the plugin never has to touch it, and it is shared across launches.
HOME_DIR = Path(os.environ.get("COUNTDOWN_HOME", Path.home() / ".countdown")).expanduser()
VENV_DIR = HOME_DIR / "venv"


def log(msg):
    print(f"[countdown] {msg}", flush=True)


def _requirements_sha() -> str:
    import hashlib
    return hashlib.sha256((BACKEND / "requirements.txt").read_bytes()).hexdigest()


def ensure_venv() -> Path:
    py = VENV_DIR / "bin" / "python"
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
    if not os.environ.get("ANTHROPIC_API_KEY"):
        log("NOTE: ANTHROPIC_API_KEY not found in the environment. The page will "
            "still load, but every countdown falls back to a plain default theme "
            "instead of one Claude designs. Get a key at console.anthropic.com and "
            "export it, e.g. `export ANTHROPIC_API_KEY=sk-ant-...` in your shell "
            "profile, then relaunch.")


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
    ap.add_argument("--port", type=int, default=8030)
    args = ap.parse_args()

    py = ensure_venv()
    preflight()

    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    base = f"http://127.0.0.1:{args.port}"
    log(f"Starting the app on {base} …")
    server = subprocess.Popen(
        [str(py), "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(args.port)],
        cwd=BACKEND, env=env)
    try:
        if not wait_up(base):
            raise SystemExit(
                f"Server did not come up on port {args.port}. If that port is in "
                "use, rerun with a different one, e.g. --port 8031.")
        webbrowser.open(base + "/")
        log(f"Open: {base}/")
        log("Leave this running while you use it. Press Ctrl-C to stop the app.")
        server.wait()
    finally:
        if server.poll() is None:
            server.terminate()


if __name__ == "__main__":
    main()
