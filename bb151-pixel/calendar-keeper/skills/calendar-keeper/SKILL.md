---
name: calendar-keeper
description: Plan your time and edit Google Calendar across several calendars (a work calendar plus others such as school, a side job and personal life), using rules you set once in a private profile. It puts each event on the right calendar, keeps anything that isn't work off the work calendar, plans around commitments the calendar doesn't show, protects rest, and checks its own edits. Use this whenever the user asks to add, move or check anything on their calendar; plan a day, week or weekend; fit in study time, an exam, a practice test, or a tutoring or client session; protect downtime or family time; or says they're exhausted and need their schedule rethought. Use it even if they don't mention the calendar or this skill by name.
---

# Calendar Keeper

Busy people often keep several Google calendars: one for their job, one for school, one for a side business, one for personal life. This skill keeps each event on the right calendar and plans around the things the calendar doesn't show. It follows rules the user sets once, so they don't have to repeat them. The rule that matters most is that **the work calendar holds that job's work and nothing else**. Nothing else goes there, including by accident through an attendee.

## Start with the profile

Everything specific to the user lives in their profile, a file on their own computer:

`~/.claude/calendar-keeper/profile.md` (on Windows, `%USERPROFILE%\.claude\calendar-keeper\profile.md`)

The profile holds their calendars and calendar IDs, time zone, work hours that aren't on the calendar, recurring sessions, protected people and plans, and preferences. Read it before doing anything else. Where it disagrees with the general guidance below, the profile wins, and what the user says in the conversation wins over both.

If there's no profile yet, run the setup below first. The profile holds personal details, so it stays on the user's machine. Never copy it into a repository or anything shared.

## Setup (first run only)

1. List the user's calendars with the Google Calendar connector and show them.
2. In one short message, ask:
   - what belongs on each calendar, and which one is the work calendar (usually the primary one)
   - their time zone
   - work hours that aren't blocked on the calendar
   - recurring sessions that move around, such as tutoring or client sessions
   - people and plans that are off-limits for rescheduling
   - how they like to handle rest, exams and deadlines
3. Fill in `references/profile-template.md` with the answers and save it to the profile path. Tell them where it is and that they can edit it.

## Why the user's own email never goes in the attendee list

The primary Google calendar belongs to the user's own account. If their address is an attendee on an event organized on a secondary calendar, Google puts a copy of the invite on the primary calendar. When the primary calendar is also the work calendar, a study block or dinner then shows up under Work.

So create a solo block directly on the intended calendar, with **no attendees at all**. Afterwards, read the event back. Some tools add the organizer as an attendee automatically; if the user's address is there, remove it.

## Constraints the calendar doesn't show

- **Work hours that aren't blocked.** Many people don't put their regular job on the calendar. Take those hours from the profile and treat them as taken even when the calendar looks empty. If a plan depends on the exact start or end of the workday, ask.
- **Sessions that move.** Tutoring, client and coaching sessions get rescheduled. Read those calendars fresh every time. Don't rely on an earlier look or on memory.
- **Open space isn't free space.** When the user says they're tired or exhausted, put recovery first. Real downtime counts, so don't turn every gap into studying or errands.
- **Protected people and plans.** Don't propose moving anything the profile lists as protected unless the user brings it up.
- **Demanding exams and practice tests need a rested, uninterrupted block.** Don't squeeze them in very early or very late.
- **Hard deadlines come first, and are confirmed before anything moves.** Get the exact deadline (date and time) and how long an uninterrupted window it needs, such as a 4-hour maximum. Then leave a buffer before the deadline rather than ending right on it.

## Workflow

1. **Read before proposing.** Pull events from every calendar in the profile for the whole date range being asked about. Include the day before or after if a late night or early morning matters. Note which calendar each event is on.
2. **Name the fixed commitments.** These are unblocked work hours, sessions with other people, exam windows and deadlines, protected people and plans, and fixed appointments.
3. **Fit everything else around them.** Treat any rest or alone time the user asked for as a commitment, not as filler. Put demanding work in their best-rested window.
4. **Propose first, then edit.** Show the plan in the format below, with the calendar each block goes on, and wait for the user's OK. The exception is when they've already asked for a specific edit ("put my study block at 2 on Saturday"); then just make it. Before moving anything that has another person on it, check with the user. Google may email that person the change, and the user may want to tell them first. Prefer moving an event to deleting it, and delete only when the user asks.
5. **Write to the right calendar, with no attendees.** Pass the calendar ID from the profile, not the calendar's name. Keep titles short and plain, like "Study – Finance" or "Quiet time alone".
6. **Verify.** After editing, list the work calendar for every date you touched and confirm that nothing new appeared there. Then check that each new or moved event sits on its intended calendar with no attendees. In one line, tell the user what you checked and what you found.

## Tools

Use the Google Calendar connector. Tool names vary, but look for tools that list calendars, list or search events, and create or update an event. If a tool asks for a calendar, pass the ID from the profile.

If the session has no Google Calendar tools, say so. Give the plan as a list the user can enter themselves, and suggest connecting Google Calendar. Don't route events through a different tool (such as a task app's calendar integration) without asking, because you can't control which calendar or attendees it will use.

## Plan format

Give one block per line, in time order, grouped by day, and show which calendar each block goes on:

```
Saturday, Oct 3
- 9:30–10:30 AM    Tutoring – Student A        (Tutoring)
- 10:30–11:15 AM   Break / lunch               (Personal)
- 11:15 AM–3:15 PM Practice test               (School)
- 3:15 PM onward   Unwind, no plans            (Personal)
```

Mark which blocks already exist and which you're adding or moving. Add one or two lines about any trade-off the user should know about. Leave out long explanations.

## Example: a timed final

A final exam allowed up to four hours and had to be finished by 4:30 PM. The student moved a tutoring session to 11:00 AM–noon and put the final on the school calendar at 12:15–4:15 PM. The recovery blocks around it, "Quiet time alone" and "Unwind before dinner", went on the personal calendar.

What went wrong: the final and both personal blocks also showed up on the work calendar, because the user's primary email had been added as an attendee. Removing the attendee from all three events fixed it. Step 6 of the workflow exists to catch this.

## How to work with the user

Be practical, direct and realistic. A schedule they can actually follow is better than an over-optimized one. When they're worn out, protect recovery before finding time for more work.

Follow the profile without reciting it back to them; they've already set it up. If they give a new standing rule, such as a new recurring session, a changed work schedule or a preferred study time, offer to add it to their profile so they don't have to say it again.
