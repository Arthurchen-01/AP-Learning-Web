# AP真题PDF批量下载脚本
$baseDir = "C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\pdfs"
$examList = Get-Content "C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\apmaster-exam-list.json" -Encoding UTF8 | ConvertFrom-Json
$buildId = $examList.buildId

$subjectFolders = @{
    "计算机科学A" = "csa"
    "统计学" = "statistics"
    "心理学" = "psychology"
    "物理C力学" = "physics-c-mechanics"
    "物理C电磁" = "physics-c-em"
    "微积分BC" = "calculus-bc"
    "宏观经济" = "macroeconomics"
    "微观经济" = "microeconomics"
}

if (!(Test-Path $baseDir)) { New-Item -ItemType Directory -Path $baseDir -Force | Out-Null }

$success = 0; $failed = 0; $skipped = 0

foreach ($exam in $examList.exams) {
    $folder = $subjectFolders[$exam.subject]
    if (!$folder) { $skipped++; continue }
    
    $subjectDir = Join-Path $baseDir $folder
    if (!(Test-Path $subjectDir)) { New-Item -ItemType Directory -Path $subjectDir -Force | Out-Null }
    
    $fileName = "$($exam.title_en).pdf"
    $filePath = Join-Path $subjectDir $fileName
    
    if (Test-Path $filePath) { Write-Host "[SKIP] $($exam.title_en)"; $skipped++; continue }
    
    $apiUrl = "https://apmaster.cn/_next/data/$buildId/exam/$($exam.slug).json"
    try {
        $response = Invoke-RestMethod -Uri $apiUrl -TimeoutSec 15
        $fileUrl = $response.pageProps.exam.file_url
        if ([string]::IsNullOrEmpty($fileUrl)) { Write-Host "[WARN] $($exam.title_en) no url"; $failed++; continue }
        
        Write-Host "[DL] $($exam.title_en)"
        Invoke-WebRequest -Uri $fileUrl -OutFile $filePath -TimeoutSec 60
        $size = [math]::Round((Get-Item $filePath).Length / 1MB, 1)
        Write-Host "  -> OK (${size} MB)"
        $success++
        Start-Sleep -Milliseconds 500
    }
    catch { Write-Host "[ERR] $($exam.title_en) - $($_.Exception.Message)"; $failed++ }
}

Write-Host "=== DONE: Success=$success Failed=$failed Skipped=$skipped ==="