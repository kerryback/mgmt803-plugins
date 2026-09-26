#!/usr/bin/env python3
"""Launch the SN1/SN2 Reaction Lab and open it in the browser.

The app is a static, client-side page: every substrate/nucleophile/solvent and
the mechanism-decision logic live in frontend/chemistry.js, and the animation
in frontend/app.js. There is no backend and nothing to install -- this script
just serves that folder over HTTP (stdlib only) and opens a browser tab.

Usage:
  python3 scripts/skill_launch.py [--port 8030]

Runs in the foreground and keeps the server alive; stop it with Ctrl-C.
"""
import argparse
import http.server
import sys
import webbrowser
from pathlib import Path

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"


def log(msg):
    print(f"[sn-lab] {msg}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8030)
    args = ap.parse_args()

    if not (FRONTEND / "index.html").exists():
        raise SystemExit(f"Frontend not found at {FRONTEND}")

    handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(
        *a, directory=str(FRONTEND), **kw
    )

    try:
        server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    except OSError as e:
        raise SystemExit(
            f"Could not start on port {args.port} ({e}). Rerun with a different "
            f"port, e.g. --port {args.port + 1}."
        )

    url = f"http://127.0.0.1:{args.port}/"
    log(f"Serving the reaction lab at {url}")
    webbrowser.open(url)
    log("Leave this running while you use the app. Press Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("Stopping.")
        server.shutdown()


if __name__ == "__main__":
    sys.exit(main())
