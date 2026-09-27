---
name: weekly-battle-plan
description: >-
  Open the Weekly Battle Plan, a dark-mode drag-and-drop to-do list that shows one
  set of tasks either by section or by day. Use when the user says
  "/weekly-battle-plan", "open my battle plan", "open my to-do list", wants a weekly
  planner or task board they can keep, or asks to sync their to-do list across their
  phone and laptop. One self-contained HTML file: open it from disk for a
  browser-local list, or publish it as a private Claude artifact with the db and user
  capabilities to sync tasks across devices.
---

# /weekly-battle-plan

A single-file to-do list. `<plugin-dir>` is this plugin's directory; the app is
`<plugin-dir>/battle-plan.html`.

## Two ways to run it, and they are not interchangeable

The same file detects at startup whether a Claude artifact database is available.
Which mode the user ends up in decides where their tasks live, so ask before
choosing when it isn't already clear:

**Local** — open the file, tasks save to `localStorage`.

```
open "<plugin-dir>/battle-plan.html"
```

On Linux use `xdg-open`. Tasks live in that one browser on that one device. They
don't reach the user's phone, and clearing browser data erases them. Good for
trying it out; a poor place to keep a real week.

**Synced** — publish the user's own copy as a private artifact. Tasks live in the
artifact's database and follow them anywhere they're signed in to Claude. This is
what someone wants if they mentioned their phone, more than one computer, or
keeping the list.

## Publishing the synced copy

The app calls `window.claude.use('db')` for storage and `window.claude.use('user')`
to detect read-only viewers, so it has to be published with both the `db` and
`user` capabilities — without them it silently falls back to local mode and the
header will not say "Synced".

1. Load the `artifact-capabilities` skill first, to get the current config shape
   for `db` and `user`. Don't guess it.
2. Publish `<plugin-dir>/battle-plan.html` with those two capabilities. Publish the
   file as it stands; the page is complete.
3. Give the user the URL and tell them to open it — the header should read
   **Synced**, and the copy starts empty apart from the Done Dumpster.
4. Offer to set up their sections. A fresh copy has none, and `+ Add section` in
   the page works too.

Tell them once, plainly, not to share that link with anyone: the tasks are in that
artifact's database, so anyone who can open the link can read and change their
plan. Someone who wants their own copy should be handed `battle-plan.html` and
publish it themselves.

To change the app later, edit the local file and republish to the same URL — the
user's tasks are in the database, not the page, so they survive.

## What to tell them about the app

Only what they'll otherwise miss; the page is self-explanatory once open.

- **Sections / Days** toggle at the top shows the same tasks two ways. Every task
  has a section, and optionally a day. Check one off in either view and it's off in
  both.
- **Checkboxes have three states**: not started, in progress, done, back to the
  start.
- **Drag the ⠿ handle** to reorder, or to move a task to another section or day.
  Works on touch.
- **Overdue** collects unfinished tasks from past days and **No day yet** holds
  unscheduled ones, in the Days view. Each has a button that moves everything in
  it onto today, and tasks moved out of Overdue keep a "Moved from Thu 9/24"
  label.
- **Tags**: Work, School, Life, Hard Deadline are built in; `+ Tag` adds more and
  new ones get a color automatically.
- **Done Dumpster**: "Move N done to Dumpster" clears finished tasks aside while
  still counting them toward progress; "Empty dumpster" deletes them. A done task
  dragged back out resets to not started.

## Notes

Everything is inlined in `battle-plan.html` — no dependencies, no build step, no
server. Once it's open there is no API for you to drive and no session state to
poll, so adding or editing tasks is something the user does in the page, not
something you do for them.

Hannah also hosts a browser-local copy at
https://thehgremlin.github.io/WeeklyBattlePlan/, which is the fastest way to see
what it looks like. That copy can't sync — a published artifact is the only synced
option.
