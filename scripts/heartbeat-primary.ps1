param(
    [string]$RepoRoot = "C:\Users\25472\projects\methods\mokaoai.com-private-upload"
)

$ErrorActionPreference = "Stop"

$taskStatusPath = Join-Path $RepoRoot "task-in-progress\task-status.json"
$todoPath = Join-Path $RepoRoot "task-todo"
$desktopPath = [Environment]::GetFolderPath("Desktop")
$todayMemoryPath = Join-Path $desktopPath "memory for claw01\one-day\2026-03-28.md"
$splitTask = Get-ChildItem $desktopPath -File | Where-Object { $_.Name -like "3.28*.md" } | Select-Object -First 1
$requirement = Get-ChildItem $desktopPath -File | Where-Object { $_.Extension -eq ".md" -and $_.Name.Length -le 6 -and $_.Name -notlike "3.28*" } | Select-Object -First 1

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
    requirementExists = $null -ne $requirement
    requirementFile = if ($null -ne $requirement) { $requirement.FullName } else { "" }
    splitTaskExists = $null -ne $splitTask
    splitTaskFile = if ($null -ne $splitTask) { $splitTask.FullName } else { "" }
    todayMemoryExists = Test-Path $todayMemoryPath
    todayMemoryLastWrite = Get-LastWriteIso $todayMemoryPath
}

$result | ConvertTo-Json -Depth 10
