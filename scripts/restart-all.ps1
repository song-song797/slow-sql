$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$stopScript = Join-Path $PSScriptRoot "stop-all.ps1"
$startScript = Join-Path $PSScriptRoot "start-all.ps1"

if (-not (Test-Path $stopScript)) {
  throw "未找到停止脚本: $stopScript"
}

if (-not (Test-Path $startScript)) {
  throw "未找到启动脚本: $startScript"
}

Write-Host "Stopping project services..."
& $stopScript

Start-Sleep -Seconds 2

Write-Host "Starting project services..."
& $startScript
