# AGENTS.md

This git repository is the active OpenClaw workspace.

## Startup Order

Before working, read these files in order:

1. `C:\Users\25472\Desktop\需求.md`
2. `C:\Users\25472\Desktop\3.28已经分割好的任务.md`
3. `C:\Users\25472\Desktop\memory for claw01\one-day\2026-03-28.md`
4. `MEMORY.md`
5. `USER.md`

If context compacts, a new session starts, or a handoff happens, reread items 1-3 before doing anything else.

## Working Rules

- Primary work area: this repository only.
- Task inbox: `C:\Users\25472\projects\methods\mokaoai.com-private-upload\task-todo`
- Task done folder: `C:\Users\25472\projects\methods\mokaoai.com-private-upload\task-done`
- In-progress state file: `C:\Users\25472\projects\methods\mokaoai.com-private-upload\task-in-progress\task-status.json`
- If a task is already active, continue it on the next heartbeat instead of starting a different one.
- Always consult `task-status.json` before starting a new task. If `active=true`, resume that task first.
- Before changing any source file, compare the current file with the task goal and requirement files.
- If confidence is at least 80% that the new content is better aligned with the requirement than the current source, overwrite the source file directly.
- If confidence is below 80%, do not overwrite the source. Create a sibling review candidate beside the original instead.
- Sibling review candidate naming:
  - file: `<original-name>.review<original-ext>`
  - directory: `<original-name>__review`
- When a task is fully completed, move the task file from `task-todo` to `task-done`, write a short result summary there, then `git add`, `git commit`, and `git push`.
- Commit messages should be short and task-based.
- Every 30 minutes, send a QQ progress update to `qqbot:c2c:4193BD194E319F7E000AF005F82E06CE`.

## Script Reliability Rules

- Primary heartbeat checker: `scripts/heartbeat-primary.ps1`
- Fallback heartbeat checker: `scripts/heartbeat-fallback.ps1`
- QQ report sender: `scripts/send-qq-report.ps1`
- On each heartbeat, run the primary checker first.
- If the primary checker fails, times out, or returns invalid JSON, immediately run the fallback checker.
- If both checkers fail, do not guess. Record the failure in the day memory file and send a QQ warning with the failure reason.
- Before editing a source file, do at least two checks:
  - compare the current source against the active task and `需求.md`
  - verify the planned replacement is more aligned than the current source
- If the result is uncertain, keep the original source untouched and create a review candidate beside it.

## Memory Rules

- Update `C:\Users\25472\Desktop\memory for claw01\one-day\2026-03-28.md` after every substantial step.
- Update `C:\Users\25472\Desktop\memory for claw01\three-day\rolling-3d.md` when there is a meaningful change spanning multiple sessions.
- Put lasting lessons and stable conventions in `MEMORY.md`.

## Publishing Rule

- This repository is connected to GitHub. Completed work should be pushed upstream automatically.
- If there are only low-confidence review candidates and no high-confidence source edits, commit and push the review candidates as review material.
