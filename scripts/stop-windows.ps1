param([switch]$Quiet)

$projectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$runDir = Join-Path $projectRoot '.run'
$stopped = $false

function Stop-ProcessTree {
    param([int]$RootProcessId)
    $children = Get-CimInstance Win32_Process -Filter "ParentProcessId = $RootProcessId" -ErrorAction SilentlyContinue
    foreach ($child in $children) {
        Stop-ProcessTree -RootProcessId ([int]$child.ProcessId)
    }
    Stop-Process -Id $RootProcessId -Force -ErrorAction SilentlyContinue
}

foreach ($name in 'backend', 'frontend') {
    $pidFile = Join-Path $runDir "$name.pid"
    if (-not (Test-Path -LiteralPath $pidFile)) { continue }
    $rawPid = (Get-Content -LiteralPath $pidFile -Raw).Trim()
    $processId = 0
    if ([int]::TryParse($rawPid, [ref]$processId) -and $processId -gt 0) {
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($process) {
            Stop-ProcessTree -RootProcessId $processId
            $stopped = $true
        }
    }
    Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
}

if (-not $Quiet) {
    if ($stopped) { Write-Host '슬쩍 서버를 종료했습니다.' -ForegroundColor Green }
    else { Write-Host '실행 중인 슬쩍 서버를 찾지 못했습니다.' }
}
