# Job Scout: a Claude skill

Job Scout searches current job postings every day and scores each one against your resume and target jobs. It emails you the best matches with the key details: company, title, pay, location, date posted, link, why it fits, and the gaps. It also tells you exactly how to adjust your resume to compete better.

## What you need
- Claude Code or the Claude desktop app (Code tab)
- The **Gmail connector** turned on, so it can email you. Without it, reports are saved locally instead.
- Your resume (PDF, Word, or text)

## Install
Register the marketplace once, then install the plugin:

```
/plugin marketplace add kerryback/mgmt803-plugins
/plugin install job-scout@mgmt803
```

Start a fresh session so the skill loads.

## First run
Tell Claude:

> Set up job scout

It will ask you to:
1. **Upload your resume** (a file path, drag-and-drop, or pasted text)
2. **List your target jobs and locations**, plus optional details such as seniority, industries, target companies, salary floor, and deal-breakers
3. Give the **email address** for the daily digest

It then builds your profile, shows you a summary to confirm, and offers a test run and a daily schedule.

## Privacy
Your resume, profile, and reports are stored in `~/job-scout/` in your home folder, **not** in the skill folder. That means you can share the skill folder without sharing your personal data. Emails go only to the address you give it.

## Everyday use
- "Run job scout": run it now
- "Update my job scout profile" or "I have a new resume": change your targets or replace your resume
- The daily schedule runs only while the Claude desktop app is open. After you create the schedule, click **Run now** once in the Scheduled sidebar to pre-approve its tools.
