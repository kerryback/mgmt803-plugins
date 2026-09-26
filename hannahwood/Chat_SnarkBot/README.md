# Snark Bot

A chatbot that answers your questions and roasts you while it does it. Built with FastAPI and Claude Sonnet 5 (low effort).

The system prompt is one line: *"speak with maximum irreverent snark and roast the user whenever possible"*.

## Run it

You need Python 3 and your own [Anthropic API key](https://console.anthropic.com/).

**Windows:** double-click `Start Snark Bot.bat`. It installs the requirements if needed, asks for your API key the first time, then opens the chat in your browser.

**Any OS:**

```bash
pip install -r requirements.txt
python chatbot.py
```

Then go to http://localhost:8002. Close the console window to stop it.

### Where the API key goes

The bot looks for `ANTHROPIC_API_KEY` in this order:

1. An environment variable
2. `env.txt` in this folder, as a line like `ANTHROPIC_API_KEY=sk-ant-...`
3. `env.txt` in the parent folder

If none is found, `python chatbot.py` asks for the key and saves it to `env.txt`. That file is in `.gitignore`, so it won't get committed.

## How it's built

Everything is in [`chatbot.py`](chatbot.py): a FastAPI server that serves the chat page and calls the Claude API.

- `GET /` is the chat page
- `POST /chat` with `{"message": "...", "session_id": "..."}` returns `{"reply": "...", "session_id": "..."}`. Leave out `session_id` to start a new conversation; send it back to continue one.
- `DELETE /chat/{session_id}` clears a conversation

Conversations are kept in memory, so they're gone when the server restarts.
