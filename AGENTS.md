# AGENTS.md

This git repository is the active OpenClaw workspace.

## Startup Order

Before working, read these files in order:

1. `task-todo/current-requirement.md`
2. `task-todo/current-split-task.md`
3. `C:\Users\25472\Desktop\kioku\today.md`
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
- Work watchdog: `scripts/openclaw-work-watchdog.ps1`
- On each heartbeat, run the primary checker first.
- If the primary checker fails, times out, or returns invalid JSON, immediately run the fallback checker.
- If both checkers fail, do not guess. Record the failure in `C:\Users\25472\Desktop\kioku\today.md` and send a QQ warning with the failure reason.
- If the heartbeat replies `HEARTBEAT_OK` while there is still an active task or pending todo work, run `scripts/openclaw-work-watchdog.ps1` to force a new agent run.
- Before editing a source file, do at least two checks:
  - compare the current source against the active task and `需求.md`
  - verify the planned replacement is more aligned than the current source
- If the result is uncertain, keep the original source untouched and create a review candidate beside it.

## Memory Rules

- Read `C:\Users\25472\Desktop\kioku\today.md` before starting work.
- Append short updates to `C:\Users\25472\Desktop\kioku\today.md` after every substantial step.
- Put multi-session summaries in `C:\Users\25472\Desktop\kioku\three day.md`.
- Put lasting lessons and stable conventions in `C:\Users\25472\Desktop\kioku\long term.md`.

## Publishing Rule

- This repository is connected to GitHub. Completed work should be pushed upstream automatically.
- If there are only low-confidence review candidates and no high-confidence source edits, commit and push the review candidates as review material.
