# calendar-keeper

Plan your week across several Google calendars without things landing in the
wrong place.

If you keep separate calendars for work, school, a side job and personal life,
this skill puts each event on the right one, plans around the hours you work
but never block, protects your downtime, and checks its own edits. It shows you
a plan before touching your calendar.

## Install

```
/plugin marketplace add kerryback/mgmt803-plugins
/plugin install calendar-keeper@mgmt803
```

You also need the Google Calendar connector turned on in Claude.

## First run

Ask Claude to plan your week. The first time, it lists your calendars and asks
a few questions: what goes on each calendar, which one is work, your
unblocked work hours, sessions that move around, and which people and plans are
off-limits for rescheduling. It saves the answers to a private profile at
`~/.claude/calendar-keeper/profile.md`.

That profile stays on your computer. It holds your calendar IDs and personal
details, so don't commit it anywhere. Edit it any time, or tell Claude a new
rule and it will offer to add it.

## The attendee trap

If your own email is added as an attendee to an event on a secondary calendar,
Google copies the invite onto your primary calendar. If your primary calendar
is your work calendar, your study blocks and dinners then show up there. The
skill never adds you as an attendee on your own solo blocks, and after every
edit it checks your work calendar to make sure nothing leaked.
