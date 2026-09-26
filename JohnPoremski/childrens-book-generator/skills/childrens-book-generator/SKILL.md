---
name: childrens-book-generator
description: >-
  Scaffold and run a FastAPI app that turns a main character, art style, and
  moral of the story into a short illustrated children's picture book: plot
  beats written page by page, a matching illustration generated for each page
  (kept consistent by chaining the first illustration back in as a reference
  for later pages), and an optional rhyming mode. Books can be saved, reopened,
  and downloaded as a PDF. Trigger on "children's book", "picture book",
  "illustrated story for kids", "generate a kids' story with pictures", or
  similar. Uses OpenRouter for both text and image generation -- needs
  OPENAI_API_KEY (an OpenRouter key) and, for illustrations specifically,
  OpenRouter account credits (chat completions alone do not need them).
license: MIT
---

# childrens-book-generator

A single-file FastAPI app (`assets/book_app.py`) with an inline HTML/JS
frontend -- no build step, no template engine. Copy it into a working folder
and run it; the form and viewer are already built in.

## What it does

- Takes character name/description, art style, moral, setting, age range,
  supporting characters, tone, page count (4-30), and a rhyming toggle.
- Writes plot beats as JSON via one OpenRouter chat-completions call
  (`openai/gpt-4o-mini`).
- Generates one illustration per page via OpenRouter's image endpoint
  (`POST https://openrouter.ai/api/v1/images`, model
  `google/gemini-3.1-flash-image`) -- this is a separate REST endpoint, not
  reachable through the `openai` client's `images.generate()`, so illustration
  calls go through `requests` instead. The first page's image is passed back
  in as an `input_reference` on every later page so the character and art
  style stay consistent instead of drifting page to page.
- Saves each finished book under `data/childrens_books/<book_id>/` (story
  JSON + PNGs) plus a `manifest.json`, so past books can be reopened without
  regenerating.
- Lets a book be downloaded as a paginated PDF (title page, each
  illustration + its text, closing moral page) via `reportlab` + `Pillow`.
- Runs long generations (1 text call + up to 30 image calls) in a background
  thread with a polling endpoint, since that can easily exceed a request
  timeout.

## Workflow

1. **Set up a working copy.** Make a project folder and copy the app in:
   ```
   mkdir -p childrens_book_app && cd childrens_book_app
   cp "$SKILL_DIR/assets/book_app.py" .
   cp "$SKILL_DIR/assets/requirements.txt" .
   ```
   (`$SKILL_DIR` = this skill's folder, i.e. where this SKILL.md lives.)

2. **Check for API keys.** This needs `OPENAI_API_KEY` set to an OpenRouter
   key (the `openai` client points at `https://openrouter.ai/api/v1`). If the
   student's workspace follows the course convention of an `env.txt` file at
   the workspace root, symlink it in so the app's relative
   `load_dotenv("env.txt", override=True)` call finds it:
   ```
   ln -s ../env.txt env.txt   # only if env.txt lives one level up
   ```
   Otherwise make sure `OPENAI_API_KEY` is exported in the environment before
   starting the app. Never print, log, or copy the key itself anywhere.

3. **Install dependencies.** `fastapi`, `uvicorn`, `openai`, and
   `python-dotenv` are commonly preinstalled; `requests`, `reportlab`, and
   `Pillow` may not be. Install what's missing:
   ```
   pip install -r requirements.txt
   ```

4. **Run it.** Bind `0.0.0.0` and use `$PORT` if the host sets one, otherwise
   8000:
   ```
   kill $(lsof -t -i:8000) 2>/dev/null
   uvicorn book_app:app --host 0.0.0.0 --port 8000
   ```
   Open it in the workspace's app-preview / View pane, or at
   `http://localhost:8000` if running locally.

5. **Flag the credits requirement.** Chat completions (the story text) work
   on a normal OpenRouter key. Image generation is a separate, paid endpoint
   -- if illustrations come back as `image_failed` with a `402` error, that's
   OpenRouter account credits, not a bug; point the student at
   https://openrouter.ai/settings/credits rather than trying to work around
   it.

## Notes for adapting it

- `IMAGE_MODEL` and `TEXT_MODEL` are single constants near the top of
  `book_app.py` -- swap them if a model is deprecated or a different one is
  preferred.
- Generated books live under a project-local `data/childrens_books/`, not the
  course's shared `~/data`, since they're app output rather than a dataset.
- If deploying (Koyeb, Railway, etc.) rather than running locally: the
  storage under `data/childrens_books/` is local disk and will not survive a
  redeploy; `OPENAI_API_KEY` should be set as a platform secret/environment
  variable, never committed.
