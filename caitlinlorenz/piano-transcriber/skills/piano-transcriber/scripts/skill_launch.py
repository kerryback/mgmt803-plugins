#!/usr/bin/env python3
"""Launch Piano Transcriber and open it in the browser.

Invoked by the `piano-transcriber` skill. It:
  1. ensures the app environment (venv) exists and its requirements are installed,
  2. starts the FastAPI app on http://127.0.0.1:<port> (default 8020),
  3. opens it in the browser.

Everything happens in the app from there: search or paste a song link, or
upload a file, and watch the pipeline run. No arguments are required — unlike
some other skills in this marketplace, there's no file to hand it up front.

The song library (one folder per transcribed song, holding the audio, MIDI,
and rendered PDF) lives under --jobs-dir (default: ~/.piano-transcriber/jobs),
OUTSIDE this skill's own directory, so reinstalling or updating the plugin
never wipes it.

Usage:
  python scripts/skill_launch.py [--jobs-dir DIR] [--port 8020]

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

REPO = Path(__file__).resolve().parent.parent
BACKEND = REPO / "backend"

# Runtime state lives OUTSIDE the skill directory so that (a) reinstalling or
# updating the skill never wipes a user's transcribed song library, and (b)
# the package source stays clean for repackaging. Override with
# PIANO_TRANSCRIBER_HOME in the environment. The Python environment is shared
# and built once, in the user's home — same pattern as this marketplace's
# `voiceover` plugin.
HOME_DIR = Path(os.environ.get("PIANO_TRANSCRIBER_HOME", Path.home() / ".piano-transcriber"))
VENV_DIR = HOME_DIR / "venv"


def log(msg):
    print(f"[piano-transcriber] {msg}", flush=True)


def _requirements_sha() -> str:
    import hashlib
    return hashlib.sha256((BACKEND / "requirements.txt").read_bytes()).hexdigest()


def ensure_backend_venv() -> Path:
    py = VENV_DIR / "bin" / "python"
    stamp = VENV_DIR / "requirements.sha"
    want = _requirements_sha()
    if py.exists() and stamp.exists() and stamp.read_text().strip() == want:
        return py
    if not py.exists():
        log("Creating the app environment (first run only)…")
        VENV_DIR.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
        subprocess.run([str(py), "-m", "pip", "install", "-q", "--upgrade", "pip"],
                       check=True)
    else:
        log("The skill updated and wants different packages — updating the app environment…")
    log("Installing dependencies, including ML libraries (torch, demucs, basic-pitch) "
        "and their model weights — this can take several minutes the first time.")
    subprocess.run([str(py), "-m", "pip", "install", "-q", "-r",
                    str(BACKEND / "requirements.txt")], check=True)
    stamp.write_text(want)
    return py


def wait_up(base: str, timeout: float = 60.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(base + "/api/library", timeout=2)
            return True
        except urllib.error.HTTPError:
            return True  # server answered (any status) = up
        except Exception:
            time.sleep(0.5)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs-dir", default=None,
                    help="where the transcribed-song library lives "
                         "(default: ~/.piano-transcriber/jobs)")
    ap.add_argument("--port", type=int, default=8020)
    args = ap.parse_args()

    jobs_dir = Path(args.jobs_dir).expanduser().resolve() if args.jobs_dir else HOME_DIR / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)

    py = ensure_backend_venv()

    env = dict(os.environ)
    env["PIANO_TRANSCRIBER_JOBS_DIR"] = str(jobs_dir)
    # Don't scatter __pycache__ into the (possibly read-only / packaged) skill dir.
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    base = f"http://127.0.0.1:{args.port}"
    log(f"Starting the app on {base} …")
    server = subprocess.Popen(
        [str(py), "-m", "uvicorn", "app:app", "--host", "127.0.0.1",
         "--port", str(args.port)],
        cwd=BACKEND, env=env)
    try:
        if not wait_up(base):
            raise SystemExit(
                f"Server did not come up on port {args.port}. If that port is in "
                "use, rerun with a different one, e.g. --port 8021.")
        log(f"Song library: {jobs_dir}")
        log(f"Open: {base}/")
        webbrowser.open(base + "/")
        log("Leave this running while you work. Press Ctrl-C to stop the app.")
        server.wait()
    finally:
        if server.poll() is None:
            server.terminate()


if __name__ == "__main__":
    main()
