$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $root "slow-sql-backend-main\slow-sql-backend-main"
$frontendDir = Join-Path $root "slow-sql-web-main\slow-sql-web-main"
$generatedDir = Join-Path $root "generated"

$pythonExe = Join-Path $backendDir ".venv\Scripts\python.exe"
$mysqlExe = "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysqld.exe"
$mysqlIni = Join-Path $root "local-dev\mysql-runtime\my.ini"
$mysqlWorkDir = Split-Path $mysqlIni
$mysqlOutLog = Join-Path $mysqlWorkDir "mysqld.stdout.log"
$mysqlErrLog = Join-Path $mysqlWorkDir "mysqld.stderr.log"

$esBat = Join-Path $root "local-dev\elasticsearch\elasticsearch-8.15.3\bin\elasticsearch.bat"
$esWorkDir = Split-Path $esBat
$esOutLog = Join-Path $root "local-dev\elasticsearch\es.stdout.log"
$esErrLog = Join-Path $root "local-dev\elasticsearch\es.stderr.log"

$backendOutLog = Join-Path $backendDir "backend.run.log"
$backendErrLog = Join-Path $backendDir "backend.stderr.current.log"
$frontendOutLog = Join-Path $frontendDir "frontend.run.log"
$frontendErrLog = Join-Path $frontendDir "frontend.stderr.current.log"
$backendEnvFiles = @(
  (Join-Path $backendDir ".env"),
  (Join-Path $backendDir ".env.local")
)

function Test-PortListening {
  param([int]$Port)

  return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Wait-PortListening {
  param(
    [int]$Port,
    [int]$TimeoutSeconds = 60
  )

  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  do {
    if (Test-PortListening -Port $Port) {
      return
    }
    Start-Sleep -Seconds 2
  } while ((Get-Date) -lt $deadline)

  throw "等待端口监听超时: $Port"
}

function Wait-HttpReady {
  param(
    [string]$Url,
    [int]$TimeoutSeconds = 60
  )

  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  do {
    Start-Sleep -Seconds 2
    try {
      $resp = Invoke-WebRequest -UseBasicParsing $Url -TimeoutSec 5
      if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) {
        return
      }
    } catch {
    }
  } while ((Get-Date) -lt $deadline)

  throw "等待服务超时: $Url"
}

function Start-BackgroundProcess {
  param(
    [Parameter(Mandatory = $true)][string]$FilePath,
    [Parameter(Mandatory = $true)][string[]]$ArgumentList,
    [Parameter(Mandatory = $true)][string]$WorkingDirectory,
    [string]$StdoutLog,
    [string]$StderrLog
  )

  $startArgs = @{
    FilePath         = $FilePath
    ArgumentList     = $ArgumentList
    WorkingDirectory = $WorkingDirectory
    WindowStyle      = "Hidden"
  }

  if ($StdoutLog) {
    $startArgs.RedirectStandardOutput = $StdoutLog
  }
  if ($StderrLog) {
    $startArgs.RedirectStandardError = $StderrLog
  }

  Start-Process @startArgs | Out-Null
}

function Get-EnvValue {
  param(
    [string[]]$Files,
    [string]$Key
  )

  $resolved = $null
  foreach ($file in $Files) {
    if (-not (Test-Path $file)) {
      continue
    }
    foreach ($line in Get-Content $file) {
      if ($line -match "^\s*$Key=(.*)$") {
        $resolved = $Matches[1].Trim()
      }
    }
  }
  return $resolved
}

if (-not (Test-Path $pythonExe)) {
  throw "未找到后端 Python: $pythonExe"
}

if (-not (Test-Path $mysqlExe)) {
  throw "未找到 MySQL 可执行文件: $mysqlExe"
}

if (-not (Test-Path $esBat)) {
  throw "未找到 Elasticsearch 启动脚本: $esBat"
}

if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
  throw "前端依赖未安装，请先在 $frontendDir 执行 npm install"
}

New-Item -ItemType Directory -Force -Path $generatedDir | Out-Null

$reportApiBaseUrl = Get-EnvValue -Files $backendEnvFiles -Key "REPORT_API_BASE_URL"

if (-not (Test-PortListening 3307)) {
  Start-BackgroundProcess `
    -FilePath $mysqlExe `
    -ArgumentList @("--defaults-file=$mysqlIni", "--console") `
    -WorkingDirectory $mysqlWorkDir `
    -StdoutLog $mysqlOutLog `
    -StderrLog $mysqlErrLog
}

Wait-PortListening -Port 3307 -TimeoutSeconds 20

if (-not (Test-PortListening 9200)) {
  Start-BackgroundProcess `
    -FilePath "cmd.exe" `
    -ArgumentList @("/c", $esBat) `
    -WorkingDirectory $esWorkDir `
    -StdoutLog $esOutLog `
    -StderrLog $esErrLog
}

Wait-HttpReady -Url "http://127.0.0.1:9200" -TimeoutSeconds 90

if (-not (Test-PortListening 10800)) {
  Push-Location $backendDir
  try {
    Start-BackgroundProcess `
      -FilePath $pythonExe `
      -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "10800") `
      -WorkingDirectory $backendDir
  } finally {
    Pop-Location
  }
}

Wait-HttpReady -Url "http://127.0.0.1:10800/health" -TimeoutSeconds 45

if (-not (Test-PortListening 3000)) {
  Push-Location $frontendDir
  try {
    Start-BackgroundProcess `
      -FilePath "npm.cmd" `
      -ArgumentList @("run", "dev", "--", "--host", "127.0.0.1", "--port", "3000") `
      -WorkingDirectory $frontendDir `
      -StdoutLog $frontendOutLog `
      -StderrLog $frontendErrLog
  } finally {
    Pop-Location
  }
}

Wait-HttpReady -Url "http://127.0.0.1:3000" -TimeoutSeconds 45

Write-Host "Frontend: http://127.0.0.1:3000"
Write-Host "Backend:  http://127.0.0.1:10800/docs"
Write-Host "Ready:    http://127.0.0.1:10800/ready"
if ($reportApiBaseUrl) {
  Write-Host "Workflow: $reportApiBaseUrl"
}
