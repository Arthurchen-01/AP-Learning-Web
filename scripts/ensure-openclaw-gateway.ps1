param(
    [int]$Port = 18789
)

$ErrorActionPreference = "Stop"

$gatewayTaskName = "OpenClaw Gateway"
$openclaw = "C:\Users\25472\AppData\Roaming\npm\openclaw.cmd"
$qqScript = "C:\Users\25472\projects\methods\mokaoai.com-private-upload\scripts\send-qq-report.ps1"

function Test-GatewayListening {
    $listeners = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    return $null -ne $listeners
}

function Invoke-GatewayStart {
    schtasks /Run /TN $gatewayTaskName | Out-Null
    Start-Sleep -Seconds 8
    if (-not (Test-GatewayListening)) {
        Start-Process -FilePath $openclaw -ArgumentList @("gateway", "--port", "$Port", "--verbose") -WindowStyle Hidden
        Start-Sleep -Seconds 10
    }
}

$wasListening = Test-GatewayListening
if ($wasListening) {
    Write-Output "GATEWAY_OK"
    exit 0
}

Invoke-GatewayStart
$isListening = Test-GatewayListening

if ($isListening) {
    & $qqScript -Message "Gateway watchdog restarted OpenClaw.`nPort: $Port`nMode: service fallback start"
    Write-Output "GATEWAY_RESTARTED"
    exit 0
}

& $qqScript -Message "Gateway watchdog failed to recover OpenClaw.`nPort: $Port`nAction: manual check required"
throw "Gateway watchdog could not restart OpenClaw on port $Port"
