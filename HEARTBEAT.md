Heartbeat task loop for tonight:

1. Check `C:\Users\25472\projects\methods\mokaoai.com-private-upload\task-todo`.
2. Read `C:\Users\25472\Desktop\需求.md`, `C:\Users\25472\Desktop\3.28已经分割好的任务.md`, `C:\Users\25472\Desktop\记忆\2026-03-28_今晚\01_短期记忆.md`, and `C:\Users\25472\Desktop\记忆\2026-03-28_今晚\02_交接摘要.md`.
3. If a task is already in progress, continue it instead of starting a new one.
4. If no task is in progress, pick the highest-value file in `task-todo` and start executing it in this repository.
5. Before editing any source file, compare it with the task goal and requirement.
6. If confidence is at least 80% that the new content is better than the current source, overwrite the source directly.
7. If confidence is below 80%, create a sibling review candidate beside the original instead of overwriting it.
8. When a task file is fully completed, move it to `task-done`, write a short completion summary, then `git add`, `git commit`, and `git push`.
9. After each substantial change, append a short update to `01_短期记忆.md` and refresh `02_交接摘要.md`.

If there is genuinely nothing actionable, reply `HEARTBEAT_OK`.
