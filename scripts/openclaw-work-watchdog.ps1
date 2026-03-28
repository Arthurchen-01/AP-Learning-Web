param(
    [string]$RepoRoot = "C:\Users\25472\projects\methods\mokaoai.com-private-upload",
    [int]$StaleMinutes = 35
)

$ErrorActionPreference = "Stop"

$openclaw = "C:\Users\25472\AppData\Roaming\npm\openclaw.cmd"
$statusPath = Join-Path $RepoRoot "task-in-progress\task-status.json"
$todoPath = Join-Path $RepoRoot "task-todo"
$qqScript = Join-Path $RepoRoot "scripts\send-qq-report.ps1"

if (-not (Test-Path $statusPath)) {
    throw "Missing task status file: $statusPath"
}

$status = Get-Content -Raw $statusPath | ConvertFrom-Json
$todoFiles = @(Get-ChildItem $todoPath -File | Where-Object { $_.Name -ne "README.md" })
$now = Get-Date
$needsKick = $false
$reason = ""

if ($status.active) {
    $lastUpdated = if ($status.lastUpdatedAt) { [DateTimeOffset]::Parse($status.lastUpdatedAt).LocalDateTime } else { $now.AddYears(-1) }
    $idleMinutes = [math]::Round(($now - $lastUpdated).TotalMinutes, 1)
    if ($idleMinutes -ge $StaleMinutes) {
        $needsKick = $true
        $reason = "active task stale for $idleMinutes minutes"
    }
} elseif ($todoFiles.Count -gt 0) {
    $needsKick = $true
    $reason = "no active task and todo queue is not empty"
}

if (-not $needsKick) {
    Write-Output "WATCHDOG_OK"
    exit 0
}

$message = @"
Read `task-todo/current-requirement.md`, `task-todo/current-split-task.md`, and `C:\Users\25472\Desktop\kioku\today.md` first.
Then read `task-in-progress\task-status.json`.
Reason for watchdog trigger: $reason.
If task-status shows an active task, resume it immediately.
If no task is active, choose the highest-value task from `task-todo`.
Before overwriting any source file, only do so if you are at least 80% confident the new content is more aligned with the requirement. Otherwise create a sibling review candidate.
After any substantial step, update `task-status.json`, append a short note to `C:\Users\25472\Desktop\kioku\today.md`, and send a QQ progress report.
"@

& $openclaw agent --agent main --session-id main --message $message --thinking high | Out-Host
$agentExitCode = $LASTEXITCODE

if ($agentExitCode -eq 0) {
    & $qqScript -Message "Watchdog resumed OpenClaw work.`nReason: $reason`nRepo: $RepoRoot"
    Write-Output "WATCHDOG_TRIGGERED"
    exit 0
}

& $qqScript -Message "Watchdog failed to resume OpenClaw work.`nReason: $reason`nExit code: $agentExitCode"
throw "OpenClaw watchdog trigger failed with exit code $agentExitCode"
