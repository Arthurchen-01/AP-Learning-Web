param(
    [string]$RepoRoot = "C:\Users\25472\projects\methods\mokaoai.com-private-upload"
)

$ErrorActionPreference = "Stop"

$taskStatusPath = Join-Path $RepoRoot "task-in-progress\task-status.json"
$todoPath = Join-Path $RepoRoot "task-todo"
$currentRequirementPath = Join-Path $RepoRoot "task-todo\current-requirement.md"
$currentSplitTaskPath = Join-Path $RepoRoot "task-todo\current-split-task.md"
$desktopPath = [Environment]::GetFolderPath("Desktop")
$todayMemoryPath = Join-Path $desktopPath "kioku\today.md"

function Get-LastWriteIso([string]$Path) {
    if (Test-Path $Path) {
        return (Get-Item $Path).LastWriteTime.ToString("s")
    }
    return ""
}

$taskStatus = Get-Content -Raw $taskStatusPath | ConvertFrom-Json
$todoFiles = @(Get-ChildItem $todoPath -File | Where-Object { $_.Name -ne "README.md" })

$result = [ordered]@{
    checker = "primary"
    ok = $true
    timestamp = (Get-Date).ToString("s")
    repoRoot = $RepoRoot
    taskStatus = $taskStatus
    taskCount = $todoFiles.Count
    nextTask = if ($todoFiles.Count -gt 0) { $todoFiles[0].Name } else { "" }
    requirementExists = Test-Path $currentRequirementPath
    requirementFile = $currentRequirementPath
    splitTaskExists = Test-Path $currentSplitTaskPath
    splitTaskFile = $currentSplitTaskPath
    todayMemoryExists = Test-Path $todayMemoryPath
    todayMemoryLastWrite = Get-LastWriteIso $todayMemoryPath
}

$result | ConvertTo-Json -Depth 10
