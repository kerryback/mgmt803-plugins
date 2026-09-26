# syllabus-to-trello

Turn a syllabus into Trello cards and calendar reminders you can trust.

Syllabi give deadlines in relative time, such as "Week 3" or "24 hours before
the live session", and often come in draft form. This skill works out real
dates from the anchors you confirm, and sets a personal target ahead of each
official deadline. Before anything is created, it shows you the whole plan:
every card, every assumption, every missing date, and the weeks where
deadlines pile up.

## Install

```
/plugin marketplace add kerryback/mgmt803-plugins
/plugin install syllabus-to-trello@mgmt803
```

You also need the Trello and Google Calendar connectors turned on in Claude.

## How it works

1. **Plan.** Give Claude one or more syllabi. You get a proposal: cards with
   official deadlines and personal targets, a list of confirmations ordered by
   how much depends on each, and the undated graded items held for your call.
2. **Create.** Once you approve, it adds one Trello list per course with dated
   cards, plus a short reminder marker for each target on your school calendar.
3. **Verify and hand off.** It re-reads both sides to check, then writes a
   short handoff covering what was set up, what couldn't be, what dates to
   confirm, and the course's AI-use rules.

When a date changes, it updates the card and the calendar marker together, and
keeps the official deadline separate from your target.

## Your profile

The first time you use it, Claude asks for your Trello board, school calendar,
time zone and reminder preferences. It saves them at
`~/.claude/syllabus-to-trello/profile.md`. That file stays on your computer;
don't commit it anywhere.

Pairs well with `calendar-keeper@mgmt803`, which keeps events on the right
calendar.
