# piano-transcriber

Turn a song into piano sheet music.

Give it a link (SoundCloud or YouTube), a search query, or an audio file. A
local app separates the melody and bass out of the mix, transcribes the notes,
and arranges them for two hands at three difficulty levels. Preview each
arrangement on screen, listen to a MIDI playback, and download a labeled PDF.

## Install

```
/plugin marketplace add kerryback/mgmt803-plugins
/plugin install piano-transcriber@mgmt803
```

Then `/piano-transcriber`, or just say "turn this song into piano sheet music" /
"transcribe this track for piano".

## What you provide

| | |
| --- | --- |
| a song | a SoundCloud/YouTube link, a search query ("moonlight sonata"), or an audio file you upload |

Nothing else — no API key. Everything (stem separation, note transcription,
notation, PDF rendering) runs locally.

## How it goes

The app opens at <http://127.0.0.1:8020>. Search or paste a link, or upload a
file, and the pipeline runs in stages you can watch: acquiring audio →
analyzing tempo → separating instruments → transcribing notes → generating
difficulty previews. Once it's done, pick easy / medium / hard, optionally
label the key signature or note names, and the sheet music renders on screen a
page at a time. Play the arrangement back, or press download for the PDF.

Every song you transcribe stays in a library inside the app, so reopening one
re-renders from the saved MIDI instead of re-running the (slow) audio pipeline.

## First run is slow

The pipeline uses real ML models for stem separation (demucs) and note
transcription (basic-pitch) — the first run downloads their weights, and every
run is CPU-bound, so a 3-4 minute song can take a couple of minutes to process.
That's normal; watch the status line in the app.

## Good source material

Cleaner mixes transcribe better. A solo piano recording or a simple pop song
comes out cleanest; dense, heavily produced tracks (lots of layered
percussion/synths) can confuse the note detector. If a transcription sounds
wrong, trying a different recording of the same song is often faster than
fighting the settings.
