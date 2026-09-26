---
name: piano-transcriber
description: >-
  Turn a song into piano sheet music: separate the melody/bass out of a mix,
  transcribe the notes, and arrange them for two hands at easy/medium/hard
  difficulty. Use when someone wants to "turn this song into piano sheet
  music", "make me a piano arrangement of X", "transcribe this track", or
  invokes /piano-transcriber with a link, a search query, or an audio file —
  and when they invoke it bare, with nothing named. Runs entirely locally: no
  API key, no external service beyond fetching the audio itself.
---

# piano-transcriber

A local app that turns a song into piano sheet music. Runs on the user's own
machine; there is no student/instructor split like some other skills here —
whoever launches it is the one using it.

## Two ways in

- With a song named: a link (`/piano-transcriber https://soundcloud.com/...`),
  a search query ("transcribe moonlight sonata"), or a local audio file path.
  Launch (step 2) and let them watch it process.
- Bare `/piano-transcriber`, or "make me some piano sheet music": launch with
  nothing pre-filled. The app's own search box and upload button handle
  finding a song from there — you don't need to do anything further.

## What to do

`<skill-dir>` is the "Base directory for this skill" reported when the skill
is invoked; use that absolute path. `<port>` defaults to 8020.

1. Launch the app in the background from the user's current directory (so any
   files that matter land there — though normally nothing needs to leave the
   app; the library and downloads live inside it):

   ```
   python3 "<skill-dir>/scripts/skill_launch.py"
   ```

   Run it in the background — it starts a long-lived local server. The first
   launch creates a Python environment and installs the ML dependencies
   (demucs, basic-pitch, torch), which takes a few minutes; later launches are
   fast. It prints `Open: http://127.0.0.1:<port>/`.

2. Tell the user the app is open at that URL and what to do there: search for
   the song or paste a link, or upload a file, then watch the status line
   (acquiring audio → analyzing tempo → separating instruments → transcribing
   notes → generating previews). When it says done, they pick a difficulty and
   the sheet music renders; download gives them the PDF.

3. You don't do any of the actual work — no narration to draft, nothing to
   poll and write back. This skill's only job is getting the app open; the
   rest happens in the browser. Don't start describing or predicting what the
   transcription will sound like before it's run.

4. If the server does not come up (port already in use), rerun with a
   different port, e.g. `--port 8021`, and use that port when telling the user
   where to go.

## Prerequisites

None beyond Python (already present, since it runs the launcher). No API key.
First launch is slow — it installs ML libraries and downloads model weights —
say so up front so a quiet minute or two doesn't look like it hung.
