# Piano Transcriber — API & data layout

FastAPI backend (`backend/app.py` + `backend/pipeline.py`), static single-file
frontend (`backend/static/index.html`). No auth — runs locally, one user.

## Directory layout

```
backend/
  app.py             FastAPI app: job queue, library, render/download endpoints
  pipeline.py        the actual audio -> sheet music pipeline (no FastAPI deps)
  requirements.txt
  static/index.html  the whole frontend, one file
scripts/
  skill_launch.py    start the app

<PIANO_TRANSCRIBER_JOBS_DIR (default: backend/jobs)>/
  <job_id>/
    input.wav             downloaded/converted source audio
    transcribed.mid        raw transcription
    preview_easy.mid       per-difficulty arrangements (generated once, cached)
    preview_medium.mid
    preview_hard.mid
    render.musicxml        last-rendered arrangement (overwritten per render)
    sheet.pdf               "                          "
    meta.json              {job_id, title, uploader, webpage_url, source_url,
                            created_at, bpm, phase}
```

`jobs/` **is** the library — `GET /api/library` lists it by scanning every
`meta.json`, the same folder-is-the-registry pattern as this marketplace's
`voiceover` plugin. There is no database.

## Env

`PIANO_TRANSCRIBER_JOBS_DIR` — where the library lives. The launcher points
this outside the skill directory (a plugin update/reinstall replaces the skill
directory's contents, so a library stored inside it would be wiped — the exact
mistake `voiceover`'s CLAUDE.md documents fixing). Defaults to `backend/jobs`
if unset, for running the backend standalone outside the plugin.

No API keys. `pipeline.acquire_audio_from_url` uses `yt-dlp` (SoundCloud /
YouTube), which needs network access but no credentials.

## REST API (all JSON except download/preview; all under /api)

- `GET  /api/search?q=` → `{results: [...]}` — SoundCloud search (yt-dlp).
- `GET  /api/library` → `{library: [meta, ...]}`, newest first.
- `POST /api/transcribe` (multipart) `{source_url?, source_title?,
  source_uploader?, source_webpage_url?, file?}` → `{job_id}` (or
  `{job_id, reused: true}` if this exact source was already transcribed — keyed
  by `webpage_url`/`source_url`, see `find_existing_job_by_source`). Starts the
  pipeline in a background thread; poll status from here.
- `GET  /api/status/{job_id}` → `{status, error?}`. `status` is one of
  `queued | acquiring audio | analyzing tempo | separating instruments |
  transcribing notes | generating difficulty previews | done | error`.
- `POST /api/rename/{job_id}` `{title}` → `{title}`.
- `POST /api/render/{job_id}` `{difficulty, label_key_signature?,
  show_note_names?}` → `{svgs, pages, pdf_url, title, difficulty, source_url}`.
  Re-renders `render.musicxml` / `sheet.pdf` for the requested difficulty each
  call — these two files hold only the last render, not one per difficulty.
- `GET  /api/download/{job_id}` → the last-rendered `sheet.pdf`.
- `GET  /api/preview/{job_id}/{difficulty}` → that difficulty's MIDI, for
  in-browser playback. `ensure_job_loaded` reconstructs `events`/`bpm` from
  `transcribed.mid` + `meta.json` on demand, so a library entry opened after a
  server restart works without re-running the pipeline.

## Pipeline stages (`pipeline.py`)

`acquire_audio` (yt-dlp or file upload) → `separate_stems` (demucs, drops the
drum stem) → `transcribe_to_midi` (basic-pitch) → `arrange_for_piano`
(music21: split hands, quantize, simplify per difficulty) → key signature /
note-name labels → `render_musicxml_to_svg_and_pdf` (verovio → svglib/reportlab
for the PDF). ffmpeg comes from the `imageio-ffmpeg` pip wheel, same pattern as
`voiceover` — no system ffmpeg needed.
