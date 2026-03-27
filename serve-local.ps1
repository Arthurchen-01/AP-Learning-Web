$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$port = 4173

Write-Host "Serving $root at http://localhost:$port/"
Write-Host "Target page: http://localhost:$port/ap/exam?examId=1902622411338911744&timekeepingModeOn=false&type=0"

Set-Location $root
python -m http.server $port
