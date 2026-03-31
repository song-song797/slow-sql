$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $root "slow-sql-backend-main\slow-sql-backend-main"
$frontendDir = Join-Path $root "slow-sql-web-main\slow-sql-web-main"
$pythonExe = Join-Path $backendDir ".venv\Scripts\python.exe"
$mysqlExe = "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysqld.exe"
$mysqlIni = Join-Path $root "local-dev\mysql-runtime\my.ini"
$esHome = Join-Path $root "local-dev\elasticsearch\elasticsearch-8.15.3"

function Get-ProcessRecord {
  param([uint32]$ProcessId)

  return Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction SilentlyContinue
}

function Get-ListeningProcessRecords {
  param([int]$Port)

  $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
  if (-not $connections) {
    return @()
  }

  $records = @()
  foreach ($owningProcessId in ($connections | Select-Object -ExpandProperty OwningProcess -Unique)) {
    $record = Get-ProcessRecord -ProcessId $owningProcessId
    if ($record) {
      $records += $record
    }
  }

  return $records
}

function Stop-ProcessTree {
  param(
    [Parameter(Mandatory = $true)][uint32]$ProcessId,
    [Parameter(Mandatory = $true)][string]$Label
  )

  $record = Get-ProcessRecord -ProcessId $ProcessId
  if (-not $record) {
    return
  }

  $children = Get-CimInstance Win32_Process -Filter "ParentProcessId = $ProcessId" -ErrorAction SilentlyContinue
  foreach ($child in $children) {
    Stop-ProcessTree -ProcessId $child.ProcessId -Label $Label
  }

  try {
    Stop-Process -Id $ProcessId -Force -ErrorAction Stop
    Write-Host ("Stopped {0}: PID {1} ({2})" -f $Label, $ProcessId, $record.Name)
  } catch {
    Write-Warning ("停止 {0} 失败，PID {1}: {2}" -f $Label, $ProcessId, $_.Exception.Message)
  }
}

function Stop-MatchedListener {
  param(
    [Parameter(Mandatory = $true)][string]$Label,
    [Parameter(Mandatory = $true)][int]$Port,
    [Parameter(Mandatory = $true)][scriptblock]$Matcher
  )

  $records = Get-ListeningProcessRecords -Port $Port
  if (-not $records -or $records.Count -eq 0) {
    Write-Host ("{0}: port {1} 未监听，跳过" -f $Label, $Port)
    return
  }

  $matched = @($records | Where-Object { & $Matcher $_ })
  if (-not $matched -or $matched.Count -eq 0) {
    Write-Warning ("{0}: 发现 port {1} 有监听进程，但不符合本项目特征，未停止" -f $Label, $Port)
    foreach ($record in $records) {
      Write-Host ("  PID {0} Name={1}" -f $record.ProcessId, $record.Name)
      if ($record.ExecutablePath) {
        Write-Host ("    Path={0}" -f $record.ExecutablePath)
      }
      if ($record.CommandLine) {
        Write-Host ("    Cmd={0}" -f $record.CommandLine)
      }
    }
    return
  }

  foreach ($record in $matched) {
    Stop-ProcessTree -ProcessId $record.ProcessId -Label $Label
  }
}

Stop-MatchedListener -Label "Frontend" -Port 3000 -Matcher {
  return $_.CommandLine -and
    $_.CommandLine.Contains($frontendDir) -and
    $_.CommandLine.Contains("--port") -and
    $_.CommandLine.Contains("3000")
}

Stop-MatchedListener -Label "Backend" -Port 10800 -Matcher {
  return $_.ExecutablePath -and
    $_.ExecutablePath -ieq $pythonExe -and
    $_.CommandLine -and
    $_.CommandLine.Contains("uvicorn") -and
    $_.CommandLine.Contains("app.main:app") -and
    $_.CommandLine.Contains("10800")
}

Stop-MatchedListener -Label "Elasticsearch" -Port 9200 -Matcher {
  return $_.CommandLine -and
    $_.CommandLine.Contains($esHome)
}

Stop-MatchedListener -Label "MySQL" -Port 3307 -Matcher {
  return $_.ExecutablePath -and
    $_.ExecutablePath -ieq $mysqlExe -and
    $_.CommandLine -and
    $_.CommandLine.Contains($mysqlIni)
}
