---
name: snark-bot
description: >-
  Launch Snark Bot, a local FastAPI chat app powered by Claude that answers the
  user's question and roasts them while doing it. Use when the user says
  "/snark-bot", "start snark bot", "launch the roast chatbot", or wants a sarcastic
  chat companion in the browser. Needs the user's own Anthropic API key; the app
  prompts for one on first run and saves it to a gitignored env.txt.
---

# /snark-bot

A chat app that answers questions with, in the author's words, "maximum irreverent
snark". `<plugin-dir>` is this plugin's directory.

## Before launching

The app needs an Anthropic API key, which it looks for in this order:

1. the `ANTHROPIC_API_KEY` environment variable
2. `env.txt` in `<plugin-dir>`, as a line like `ANTHROPIC_API_KEY=sk-ant-...`
3. `env.txt` in the parent folder

If none is set, the app asks for the key on stdin and writes it to `env.txt`, which
is gitignored. That prompt cannot be answered from a background process, so if no
key is configured, tell the user to run it once in their own terminal rather than
trying to supply the key yourself. Never paste a key you found elsewhere into this
app's env.txt.

## Launching

1. Install dependencies if needed: `pip install -r "<plugin-dir>/requirements.txt"`
2. Run it in the background, from `<plugin-dir>`:

   ```
   python chatbot.py
   ```

It serves on port 8002 and opens `http://localhost:8002` itself after about a
second and a half, so don't open a second tab. It blocks while serving and then
waits on `input()`, so it must run in the background.

## What it exposes

- `GET /` — the chat page
- `POST /chat` with `{"message": "...", "session_id": "..."}` returns
  `{"reply": "...", "session_id": "..."}`. Omit `session_id` to start a new
  conversation; send it back to continue one.
- `DELETE /chat/{session_id}` clears a conversation

Conversations live in memory only, so restarting the server loses them.
