# mgmt803-plugins

A Claude Code plugin marketplace for MGMT 803.

## Install

Register the marketplace once:

```
/plugin marketplace add kerryback/mgmt803-plugins
```

Then install whatever you need:

```
/plugin install voiceover@mgmt803
/plugin install shoji@mgmt803
```

Or type `/plugin` alone to browse and install from the menu. Start a fresh
session after installing so the plugin's skills load.

## What's in it

| Plugin | What it does |
| --- | --- |
| `calendar-keeper@mgmt803` | Plans your week across several Google calendars from rules you set once, and keeps anything that isn't work off your work calendar. Your calendar details stay in a private profile on your computer. |
| `syllabus-to-trello@mgmt803` | Turns syllabi into dated Trello cards and calendar reminders, with personal targets ahead of each official deadline. Shows you the full plan, assumptions and missing dates before creating anything. |
| `critique@mgmt803` | Reviews work Claude produced and says what to do about it, with located evidence for every finding. Fans out several subagents. |
| `elegant-pdf@mgmt803` | Flyers, programs, reports and handbooks as branded PDFs or JPEGs, rendered from a small HTML design system. |
| `shoji@mgmt803` | A Quarto reveal.js slide theme in plum, pale gray and dusty blue, set for text- and code-heavy decks. |
| `smithers@mgmt803` | A local email and calendar desk over Gmail and Calendar. Drafts replies for you to send; never sends or deletes anything itself. |
| `voiceover@mgmt803` | Turns a slide PDF into a narrated MP4 plus a transcript. Needs an ElevenLabs API key. |
| `countdown@mgmt803` | A countdown page with no fixed look — Claude designs the colors, emoji, font and particle effect live for whatever occasion you type in. Needs an Anthropic API key. |
| `sn-lab@mgmt803` | Animates SN1/SN2 nucleophilic substitution mechanisms in a local app. Pick a substrate, nucleophile, and solvent (or use a suggested example); it predicts the mechanism and animates it next to an energy diagram. |
| `sullivan-family-activities@mgmt803` | Scaffolds a local family organizer app: shared calendar, tasks and chores with point rewards and turn rotation, a prize shop, home maintenance reminders, kid mode, and a phone-link QR code, behind a PIN-protected settings area. |

## Layout

Each plugin lives in a folder named for its author, and `marketplace.json`
points at it:

```
kerryback/critique
kerryback/voiceover
jessica-george/countdown
...
```

Plugin names are flat — the folder is organization only and never appears in an
install string. To add someone else's plugin, put it in a folder under their
name and add an entry to `.claude-plugin/marketplace.json`.
