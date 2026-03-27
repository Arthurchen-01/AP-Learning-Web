param(
  [string]$Cookie,
  [string]$OutputRoot = 'C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\ap_dump'
)

$ErrorActionPreference = 'Stop'

$base = 'https://mkapi.testdaily.cn'
$secret = '测试点点模考小助手'

if ([string]::IsNullOrWhiteSpace($Cookie)) {
  throw 'Cookie is required.'
}

$authorization = [regex]::Match($Cookie, 'authorization=([^;]+)').Groups[1].Value
$uniqueId = [regex]::Match($Cookie, 'uniqueId=([^;]+)').Groups[1].Value

if ([string]::IsNullOrWhiteSpace($authorization) -or [string]::IsNullOrWhiteSpace($uniqueId)) {
  throw 'authorization or uniqueId not found in cookie.'
}

$dirs = @(
  $OutputRoot,
  (Join-Path $OutputRoot 'subjects'),
  (Join-Path $OutputRoot 'exam_lists'),
  (Join-Path $OutputRoot 'exam_info'),
  (Join-Path $OutputRoot 'errors')
)

foreach ($dir in $dirs) {
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

function Get-Signature([string]$urlPath, [string]$timestamp) {
  $payload = ($urlPath.Split('?')[0]) + '.' + $timestamp
  $hmac = [System.Security.Cryptography.HMACSHA256]::new([System.Text.Encoding]::UTF8.GetBytes($secret))
  try {
    (($hmac.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($payload)) | ForEach-Object {
      $_.ToString('x2')
    }) -join '')
  } finally {
    $hmac.Dispose()
  }
}

function New-Headers([string]$urlPath) {
  $ts = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds().ToString()
  $sig = Get-Signature $urlPath $ts
  @{
    'authorization' = $authorization
    'uniqueId' = $uniqueId
    'Cookie' = $Cookie
    'X-TD-sec-timestamp' = $ts
    'X-TD-sec-signature' = $sig
    'preferred-lang' = 'zh-CN'
    'Accept' = 'application/json, text/plain, */*'
    'User-Agent' = 'Mozilla/5.0'
  }
}

function Invoke-TDJson([string]$method, [string]$path, [string]$body = '') {
  $headers = New-Headers $path
  if ($method -eq 'GET') {
    Invoke-RestMethod -Uri ($base + $path) -Method Get -Headers $headers
  } else {
    Invoke-RestMethod -Uri ($base + $path) -Method $method -Headers $headers -ContentType 'application/json;charset=UTF-8' -Body $body
  }
}

function Save-Json($obj, [string]$path, [int]$depth = 12) {
  $obj | ConvertTo-Json -Depth $depth | Set-Content -LiteralPath $path -Encoding UTF8
}

$subjectsRes = Invoke-TDJson 'GET' '/api/v1/ap/listAllSubject'
Save-Json $subjectsRes (Join-Path $OutputRoot 'subjects\list_all_subjects.json')
$subjects = $subjectsRes.data

$allExams = @()
$examFailures = @()

foreach ($subject in $subjects) {
  $subjectSlug = ($subject.enSubName.Trim().ToLower() -replace '[^a-z0-9]+', '_').Trim('_')
  $listPath = "/api/v1/ap/page?pageNum=1&pageSize=100&subjectId=$($subject.subId)"
  $listRes = Invoke-TDJson 'GET' $listPath
  $listFile = Join-Path $OutputRoot ("exam_lists\{0}_{1}.json" -f $subject.subId, $subjectSlug)
  Save-Json $listRes $listFile

  foreach ($exam in $listRes.data) {
    $allExams += [PSCustomObject]@{
      subjectId = $subject.subId
      subName = $subject.subName
      enSubName = $subject.enSubName
      subjectSlug = $subjectSlug
      examId = $exam.id
      examName = $exam.examName
      examNameEn = $exam.examNameEn
      unlockFlag = $exam.unlockFlag
      listFile = [System.IO.Path]::GetFileName($listFile)
    }

    $body = @{ id = $exam.id; timekeepingModeOn = $true; type = 0 } | ConvertTo-Json -Compress
    try {
      $examRes = Invoke-TDJson 'POST' '/api/v1/ap/getExamInfo' $body
      $examFile = Join-Path $OutputRoot ("exam_info\{0}_{1}.json" -f $exam.id, $subjectSlug)
      Save-Json $examRes $examFile
      Start-Sleep -Milliseconds 250
    } catch {
      $examFailures += [PSCustomObject]@{
        subjectId = $subject.subId
        subjectSlug = $subjectSlug
        examId = $exam.id
        examName = $exam.examName
        unlockFlag = $exam.unlockFlag
        error = $_.Exception.Message
      }
      Start-Sleep -Milliseconds 250
    }
  }
}

Save-Json $allExams (Join-Path $OutputRoot 'all_exams_index.json')
Save-Json $examFailures (Join-Path $OutputRoot 'errors\get_exam_info_failures.json')

$summary = [PSCustomObject]@{
  subjectCount = $subjects.Count
  examCount = $allExams.Count
  examInfoSuccessCount = (Get-ChildItem -LiteralPath (Join-Path $OutputRoot 'exam_info') -File -Filter '*.json').Count
  examInfoFailureCount = $examFailures.Count
  generatedAt = (Get-Date).ToString('s')
}

Save-Json $summary (Join-Path $OutputRoot 'summary.json')
$summary | ConvertTo-Json -Depth 4
