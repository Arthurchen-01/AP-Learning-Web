param(
    [string]$RepoRoot = "C:\Users\25472\projects\methods\mokaoai.com-private-upload"
)

$ErrorActionPreference = "Stop"

$taskStatusPath = Join-Path $RepoRoot "task-in-progress\task-status.json"
$todoPath = Join-Path $RepoRoot "task-todo"

$todoFiles = @()
if (Test-Path $todoPath) {
    $todoFiles = @(Get-ChildItem $todoPath -File | Where-Object { $_.Name -ne "README.md" })
}

$taskStatusRaw = "{}"
if (Test-Path $taskStatusPath) {
    $taskStatusRaw = [string](Get-Content -Raw $taskStatusPath)
}

$result = [ordered]@{
    checker = "fallback"
    ok = $true
    timestamp = (Get-Date).ToString("s")
    repoRoot = $RepoRoot
    taskStatusRaw = $taskStatusRaw
    taskCount = $todoFiles.Count
    nextTask = if ($todoFiles.Count -gt 0) { $todoFiles[0].Name } else { "" }
}

$result | ConvertTo-Json -Depth 5
