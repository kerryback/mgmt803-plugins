# Piano Transcriber — orientation for Claude

Read this first when working on this repo.

## What it is

A local, single-user app, launched as a Claude Code skill, that turns a song
into piano sheet music: paste a link or search for a song (or upload a file),
and it separates the mix, transcribes the notes, and arranges them for two
hands at easy/medium/hard.

There's no instructor/student split like `voiceover` — one person launches it
and uses it themselves. Claude's only job in the skill is starting the app;
the audio pipeline and the UI do the rest with no further LLM involvement.

## Architecture

- `backend/app.py` — FastAPI. Owns the job queue (in-memory dict + a folder
  per job on disk), runs the pipeline in a background thread per job, serves
  the SPA.
- `backend/pipeline.py` — the actual audio -> notation pipeline. No FastAPI
  imports; it's a plain library `app.py` calls into. See `CONTRACT.md` for the
  stage list.
- `backend/static/index.html` — the whole frontend, one file, no build step
  (unlike `voiceover`'s React/Vite frontend — this app has no reason for one).

## Design choices carried over from this app's standalone form

The library lives in a job folder per song (`meta.json` + the intermediate
files), and `GET /api/library` just scans that folder — no database. This
predates the plugin wrapping; it's `voiceover`'s folder-as-registry pattern,
arrived at independently.

`ensure_job_loaded` reconstructs a job's in-memory state from
`transcribed.mid` + `meta.json` rather than re-running the pipeline, so a
library entry still opens after the server restarts (or after `skill_launch.py`
is invoked fresh). Don't "simplify" this into requiring a live pipeline run —
that's the whole point of caching the MIDI.

`find_existing_job_by_source` matches a new transcribe request against
`webpage_url`/`source_url` in every existing job's `meta.json`, so
re-submitting the same link (maybe to try a different difficulty) reopens the
existing library entry instead of duplicating the download + pipeline run.

## The one change made when packaging this as a plugin

Originally `JOBS_DIR` was hardcoded to `<app dir>/jobs` — fine for a
standalone clone, wrong for a plugin, whose skill directory is package content
that a `/plugin update` or reinstall can replace. `app.py` now reads
`PIANO_TRANSCRIBER_JOBS_DIR` from the environment (falling back to
`backend/jobs` if unset), and `skill_launch.py` points it at
`~/.piano-transcriber/jobs` — outside the skill directory, so a plugin update
never touches a user's transcribed library. This is the same fix `voiceover`
made for its ElevenLabs key (see that plugin's `CLAUDE.md`) applied to this
app's library instead of a credential. Do not move it back to a path inside
`skill-dir`.

## Gotchas / operational notes

- First launch installs heavy ML dependencies (torch, tensorflow, demucs,
  basic-pitch) and downloads model weights — genuinely slow (a few minutes).
  `skill_launch.py` stamps a requirements hash so this only happens once, or
  again when `requirements.txt` changes (mirrors `voiceover`'s launcher).
- The pipeline is CPU-bound and a full song can take a couple of minutes to
  process; the frontend polls `/api/status/{job_id}` and shows the current
  stage, so this isn't silent, but don't imply anything is wrong just because
  it's not instant.
- ffmpeg comes from the `imageio-ffmpeg` pip wheel, not the system — do not
  add a system ffmpeg requirement.
- `backend/requirements.txt` pins an `--extra-index-url` for CPU-only PyTorch
  wheels; keep that line if the file is ever regenerated.
