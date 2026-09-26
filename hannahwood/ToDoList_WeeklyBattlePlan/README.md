# Weekly Battle Plan

A dark-mode to-do list with drag and drop. It shows the same tasks two ways: by **section** (Things to Do, Things to Read/Grok, Things to Sync About) or by **day** (Monday to Sunday of this week). Check a task off in one view and it's checked off in the other.

**▶ Try it in your browser:** https://thehgremlin.github.io/WeeklyBattlePlan/

It's one HTML file, `battle-plan.html`, with nothing to install.

## Features

- **Two views of one list:** switch between **Sections** and **Days** at the top. Every task has a section and, optionally, a day. You set both in the add/edit form, which has shortcuts for Today, Tomorrow and No day.
- **Three-state checkboxes:** not started, then in progress, then done, then back to the start.
- **Drag and drop:** drag the ⠿ handle to reorder tasks or move them to another section or day. It works on phones too.
- **Overdue and No day yet:** in the Days view, unfinished tasks from past days collect in **Overdue**, and unscheduled tasks sit in **No day yet**. Each group has a button that moves all of its tasks onto today. Tasks moved from Overdue keep a "Moved from Thu 9/24" label.
- **Tags:** Work, School, Life and Hard Deadline are built in. Add your own with **+ Tag** in the key, or with **+ New tag** while editing a task. New tags get their own color automatically.
- **Done Dumpster:** **Move N done to Dumpster** clears finished tasks out of the way, and they still count toward your progress. **Empty dumpster** deletes them for good. A done task dragged back out of the Dumpster resets to not started.
- **Past days** in the Days view start collapsed, so the week in front of you stays front and center.

## Option 1: Just open it (no setup)

Open `battle-plan.html` in your browser, or use the link above.

Your tasks are saved **in that browser on that device only**. They won't show up on your phone or in another browser, and clearing your browser data erases them.

## Option 2: Sync across your devices (needs a Claude account)

Publish your own copy as a Claude artifact, and it will sync anywhere you're signed in to Claude.

1. Open Claude Code (desktop app or CLI) in a folder that has `battle-plan.html` in it.
2. Ask:
   > Publish battle-plan.html as a private artifact with the `db` and `user` capabilities.
3. Open the link Claude gives you. That's your personal, synced Battle Plan.

The header will say **Synced** once it's working. Your copy starts empty except for the Done Dumpster. Use **+ Add section** to create your sections, or ask Claude to set some up.

**Don't share your artifact link with classmates.** Your tasks live in that artifact's database, so anyone with access to the link can see and change your plan. Share this file instead, so each person gets their own copy.

## How it was built

It started as a one-off HTML to-do list in a Claude chat. Then it was rebuilt with Claude Code as a Claude artifact that keeps its tasks in the artifact's database, which is what makes it sync across devices. When there's no Claude database available, the same file falls back to the browser's local storage.
