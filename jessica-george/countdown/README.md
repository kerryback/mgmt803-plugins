# countdown

A countdown page with no fixed look. Type what you're counting down to and a
date, and Claude designs the whole page for it, live: background colors, an
emoji, a heading font, and a particle effect (snow, confetti, floating,
sparkle) that all fit the occasion — a school's real colors, a holiday's
mood, a wedding's palette.

## Install

```
/plugin marketplace add kerryback/mgmt803-plugins
/plugin install countdown@mgmt803
```

Then `/countdown`, or just ask for a countdown page — it opens
<http://127.0.0.1:8030> in your browser.

## What you provide

| | |
| --- | --- |
| `ANTHROPIC_API_KEY` | the app calls Claude to design each theme. Get one at [console.anthropic.com](https://console.anthropic.com) |

That's the lot — no Node, no build step, nothing else to install.

## How it goes

Type an occasion ("my sister's wedding", "Rice vs. UT", "graduation") and a
date, and the page redesigns itself around it: real team/school colors when it
recognizes one, a holiday palette, a script font for a wedding, confetti for a
celebration. Everything after that is just a live day-count ticking down.

There's no file to hand back and nothing saved between occasions — it's a page
to leave open in a tab, not a deliverable.
