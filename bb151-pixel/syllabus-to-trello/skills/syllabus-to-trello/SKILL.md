---
name: syllabus-to-trello
description: Turn course syllabi into a Trello card plan and matching Google Calendar reminders. It reads each syllabus and converts relative deadlines ("Week 3", "24 hours before the live session") into real dates from confirmed anchors. It sets personal targets ahead of the official deadlines, flags missing, stale or contradictory dates, and proposes every card for review before creating anything. Once the user approves, it creates the Trello cards and calendar markers, verifies both, and writes a handoff summary. Use this whenever the user shares a syllabus or course outline and wants its deadlines tracked, asks to put a course on Trello or their calendar, wants to plan a term, semester or intensive, set up assignment reminders, or update a course's dates after the syllabus changes. Use it even if they don't name Trello or this skill.
---

# Syllabus to Trello

A syllabus lists obligations in relative time: "Week 3", "24 hours before the live session", "10 days after the final session". This skill turns those into dated Trello cards and calendar reminders the user can rely on, without inventing dates they might trust by mistake.

Three ideas run through everything:

- **An official deadline and a personal target are different things.** Every item carries both: the deadline the course sets, and an earlier date the user aims for. Cards and calendar markers are dated to the target, and the official deadline is always written in their descriptions, so the two never get confused.
- **Nothing is written until the user approves the plan.** Build a proposal first. Creating thirty cards on a wrong assumption costs far more to undo than to review.
- **A derived date is labeled as derived.** When a date rests on an assumption, such as which weekday a class meets, say so. List every assumption up front, so that changing one recalculates everything that depends on it.

## Profile

User-specific settings live in a file on the user's own computer:

`~/.claude/syllabus-to-trello/profile.md` (on Windows, `%USERPROFILE%\.claude\syllabus-to-trello\profile.md`)

The profile holds their Trello board, school calendar ID, time zone, marker time and reminders, lead-time policy and submission naming convention. Read it first. If it's missing, ask for those settings in one short message, fill in `references/profile-template.md`, and save it there. It holds personal details, so it stays on the user's machine; never copy it into a repository.

Settings the user gives in the conversation override the profile for that run. If a setting looks permanent, offer to save it.

## Workflow

### 1. Read each syllabus in full

For each course, pull out:
- **The course:** code, name, term window and format (weekly, intensive or asynchronous), plus each live session's weekday, start time and end time.
- **Every deliverable:** name, individual or group, points or weight, length and format requirements, and the deadline exactly as written.
- **Other obligations:** readings, materials to buy, quizzes, discussion posts, exams and peer evaluations.
- **Policies that affect planning:** late work, attendance penalties, AI use and academic integrity, exam aids (such as note-sheet rules), file naming, and honor-code statements.

Watch for signs of a draft or outdated syllabus. Examples include dates from a previous year, obsolete tools or versions, contradictions (such as "five-week term" on one page and "ten-week" on another), and links the text mentions but doesn't include. Note each one for the confirmations list.

### 2. Anchor the dates

Relative deadlines need fixed points. Collect:
- the term's start and end
- each live session's weekday, start time and **end** time, because "72 hours after the session" runs from when it ends
- when course materials open, since a Week 1 assignment may be due before the first class

Check the user's calendar first: the class sessions may already be there, and an existing event is better evidence than a guess. For anything you can't confirm, choose a working assumption, state it, and flag it. Sanity-check the assumptions against each other. For example, two courses that run in the same weeks usually can't share a session slot.

### 3. Build the plan (a proposal only)

For each course, make one row per proposed card, with these columns: card name, type, official deadline (as written, plus the derived date), proposed personal target, and notes and flags.

**Personal targets.** Use the profile's lead-time policy. If the profile doesn't set one, use this default:

| Item | Target |
|---|---|
| Quizzes, discussion posts, short prep | 1 day before the deadline |
| Written cases, reports, papers | 3 days before |
| Major group deliverables, presentations, multi-week work | 5–7 days before, plus a separate start or draft card |

If the window is shorter than the buffer, as with an overnight assignment or a 72-hour group deck, shrink the buffer to what fits and flag it.

**Implied work.** Add a card for work the syllabus implies but doesn't list, when skipping it would sink a graded item. Examples include buying the textbook before Week 1 reading, recruiting interviewees, a team working session inside a short group window, or a draft before a presentation. Label each one "my addition, not a syllabus item" so the user can drop it.

**Undated items.** If a graded item has no date anywhere in the syllabus, don't guess. List it as **HOLD — not created without your approval**, with at most a placeholder date.

**Things that don't get their own card.** List these in a "Deliberately not carded" section:
- Class sessions and attendance go on the calendar or in a card description. Note any attendance penalties.
- Honor-code statements, file-naming rules and submission formats become checklist items inside the relevant card.
- Optional readings become a checklist inside the related card.
- Leave out things the user doesn't do, such as receiving instructor feedback, and ongoing participation.

**Workload collisions.** Then look across all courses for weeks where several graded deliverables land within a few days of each other. Name those weeks and what's in them.

Present the plan in the structure in `references/plan-format.md`. For more than one course, or more than about fifteen cards, write it as a Word document (use the docx skill if it's available) and summarize it in chat. Otherwise, tables in chat are fine.

### 4. Create the Trello cards (after approval)

- **Lists:** make one list per course on the board named in the profile, titled with the course name. If a matching list already exists, read it first. Update cards that are already there rather than creating duplicates.
- **Order:** create cards in chronological order, with `pos` set to 1, 2, 3 and so on.
- **Due dates:** use the personal target. Trello expects UTC, so convert from the user's time zone.
- **Descriptions:** include the official deadline and where it comes from (e.g., "Syllabus: 24h before the Week 3 live session → Tue Oct 20, 8:30 PM"), what to submit (length, format, points or weight), any flags, and the AI-use rule if it restricts this item.
- **Checklists:** use them for sub-items such as embedded quizzes, the honor-code statement, the file name and optional readings.
- **Tentative items:** add "(tentative)" to the card name.

Check whether the connector can set Trello's reminder field or add the user as a card member. If it can't, say so plainly in the handoff: without one of those, Trello may not send due-date notifications. The calendar markers in the next step cover that gap.

### 5. Add calendar markers (after approval)

For each personal target, create a short marker on the school calendar named in the profile:
- **Time:** at the marker time from the profile (default 6:00 PM local), 15 minutes long.
- **Reminders:** popup alerts from the profile (default one day and two hours before).
- **Title:** the card name, with "(tentative)" where it applies.
- **Description:** "Planning target, not the official deadline. Official deadline: …", plus the Trello card name or link.
- **No attendees.** Above all, don't add the user's own email. On a secondary calendar, that copies the event onto their primary calendar. If the calendar-keeper skill is installed, follow its profile for calendar IDs and rules.
- **No duplicates.** Skip class sessions that are already on the calendar. If a marker already exists, update it rather than adding a second.

Markers are reminders, not work sessions, so don't block out work time unless the user asks.

### 6. Verify

Re-read both sides:
- **Trello:** the list's card count matches the approved plan, and every due date is right after the time-zone conversion.
- **Calendar:** there's one marker per card, at the right time, with its reminders. None has attendees, none is duplicated, and none landed on a different calendar.

Fix anything that's off, then tell the user in a line or two what you checked.

### 7. Write the handoff

Summarize the result in the structure in `references/handoff-template.md`. Cover the schedule, the Trello setup (including anything that couldn't be set), the calendar setup with a table of targets, the dates still to confirm, and the academic-integrity notes. Offer to save it as a file next to the syllabus. A future session can pick up from it without re-reading everything.

## When dates change

Always update the Trello card and the calendar marker together. If an official deadline moves, recompute the target with the same lead-time rule. When a tentative date is confirmed, remove "(tentative)" from both. Syllabi marked as drafts change, so suggest re-checking every date against the final version in the first week of term rather than waiting to start tracking.

## Academic integrity

Record each course's AI policy in the handoff, and in the description of every card it affects. Many courses allow AI for studying concepts but not for quizzes, exams or the text of an exam note sheet. This skill plans and tracks the work. If the user later asks for help with an item the syllabus restricts, point to the rule rather than doing that part.

## Tools

Use the Trello connector (read boards, lists and cards; write lists, cards and checklists) and the Google Calendar connector. Tool names vary by connector.

If either connector is missing, still build the plan and the handoff. Tell the user which part couldn't be created, and give them what they need to enter it themselves.
