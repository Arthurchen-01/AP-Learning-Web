Heartbeat task loop for tonight:

1. Run `scripts/heartbeat-primary.ps1`.
2. If the primary checker fails, run `scripts/heartbeat-fallback.ps1`.
3. Read `C:\Users\25472\Desktop\需求.md`, `C:\Users\25472\Desktop\3.28已经分割好的任务.md`, and `C:\Users\25472\Desktop\memory for claw01\one-day\2026-03-28.md`.
4. Read `C:\Users\25472\projects\methods\mokaoai.com-private-upload\task-in-progress\task-status.json`.
5. If `task-status.json` shows `active=true`, continue that task instead of starting a new one.
6. If no task is in progress, pick the highest-value file in `task-todo` and start executing it in this repository.
7. Before editing any source file, compare it with the task goal and requirement.
8. If confidence is at least 80% that the new content is better than the current source, overwrite the source directly.
9. If confidence is below 80%, create a sibling review candidate beside the original instead of overwriting it.
10. Update `task-status.json` whenever task state changes.
11. Send a QQ work progress report to `qqbot:c2c:4193BD194E319F7E000AF005F82E06CE` every heartbeat using `scripts/send-qq-report.ps1`. Include current task, what changed, current confidence, and next step.
12. If the primary QQ send attempt fails, retry once. If it still fails, send a shorter fallback report with the same script and record the failure in the day memory file.
13. When a task file is fully completed, move it to `task-done`, write a short completion summary, then `git add`, `git commit`, and `git push`.
14. After each substantial change, append a short update to `C:\Users\25472\Desktop\memory for claw01\one-day\2026-03-28.md`.

If there is genuinely nothing actionable, reply `HEARTBEAT_OK`.
