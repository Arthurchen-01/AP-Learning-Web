# AP Learning Web

Private repository copy of the current AP practice site frontend.

## What This Repo Contains

- Homepage, mock exam catalog, training page, dashboard, and profile page
- Local AP exam flow from catalog entry to:
  - `Choose Full-Length Practice`
  - `Preparing your test`
  - `AP Practice Test` entrance page
  - directions / break transitions
  - MCQ / FRQ test shell
  - review / module end / results
- Local `mock-data/` exam files used by the current frontend

## What Was Intentionally Left Out

These were excluded from this upload-ready copy:

- `database/`
- `AAAAAA/`
- `_next/`
- local logs
- local scratch / inspection files

## Main Routes

- `/` homepage
- `/mock/` full-length mock catalog
- `/training/` training hub
- `/dashboard/` learning dashboard
- `/profile/` profile page
- `/ap/start/` exam start flow
- `/ap/exam/` exam shell

## Local Run

If you want to run it locally from this repo copy, use any static server rooted at this folder.

PowerShell example:

```powershell
cd C:\Users\25472\projects\methods\mokaoai.com-private-upload
python -m http.server 4173
```

Then open:

`http://localhost:4173`

## Update Workflow

```powershell
cd C:\Users\25472\projects\methods\mokaoai.com-private-upload
git add .
git commit -m "update"
git push
```

## Current Limitations

- Many exam texts still contain raw-source encoding noise / MathType remnants
- Official answers and scoring are still missing for many papers
- Some tool panels in the exam shell are frontend placeholders only
- Dashboard and training still use partial mock data where backend logic is not ready

## Notes

- This repo is meant to stay cleaner than the original working directory
- The original project folder remains the main development workspace
- This copy is mainly for private backup, sharing, and future deployment
