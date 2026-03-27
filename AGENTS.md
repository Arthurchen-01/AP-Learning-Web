# AGENTS.md

This git repository is the active OpenClaw workspace.

## Startup Order

Before working, read these files in order:

1. `C:\Users\25472\Desktop\需求.md`
2. `C:\Users\25472\Desktop\3.28已经分割好的任务.md`
3. `C:\Users\25472\Desktop\记忆\2026-03-28_今晚\01_短期记忆.md`
4. `C:\Users\25472\Desktop\记忆\2026-03-28_今晚\02_交接摘要.md`
5. `MEMORY.md`
6. `USER.md`

If context compacts, a new session starts, or a handoff happens, reread items 1-4 before doing anything else.

## Working Rules

- Primary work area: this repository only.
- Task inbox: `C:\Users\25472\projects\methods\mokaoai.com-private-upload\task-todo`
- Task done folder: `C:\Users\25472\projects\methods\mokaoai.com-private-upload\task-done`
- If a task is already active, continue it on the next heartbeat instead of starting a different one.
- Before changing any source file, compare the current file with the task goal and requirement files.
- If confidence is at least 80% that the new content is better aligned with the requirement than the current source, overwrite the source file directly.
- If confidence is below 80%, do not overwrite the source. Create a sibling review candidate beside the original instead.
- Sibling review candidate naming:
  - file: `<original-name>.review<original-ext>`
  - directory: `<original-name>__review`
- When a task is fully completed, move the task file from `task-todo` to `task-done`, write a short result summary there, then `git add`, `git commit`, and `git push`.
- Commit messages should be short and task-based.

## Memory Rules

- Update `C:\Users\25472\Desktop\记忆\2026-03-28_今晚\01_短期记忆.md` after every substantial step.
- Keep `C:\Users\25472\Desktop\记忆\2026-03-28_今晚\02_交接摘要.md` short and current so a new session can resume fast.
- Put lasting lessons and stable conventions in `MEMORY.md`.

## Publishing Rule

- This repository is connected to GitHub. Completed work should be pushed upstream automatically.
- If there are only low-confidence review candidates and no high-confidence source edits, commit and push the review candidates as review material.
