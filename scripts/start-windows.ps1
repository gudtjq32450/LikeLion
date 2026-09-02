$ErrorActionPreference = 'Stop'

$projectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$backendDir = Join-Path $projectRoot 'backend'
$frontendDir = Join-Path $projectRoot 'frontend'
$runDir = Join-Path $projectRoot '.run'
$backendVenv = Join-Path $backendDir '.venv'
$backendPython = Join-Path $backendDir '.venv\Scripts\python.exe'

Write-Host '슬쩍 서버를 준비합니다...' -ForegroundColor Cyan

function Test-NativeCommand {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$Arguments = @()
    )

    $previousPreference = $ErrorActionPreference
    try {
        # A missing package is expected on first launch. Windows PowerShell can
        # otherwise turn Python's stderr into a terminating NativeCommandError.
        $ErrorActionPreference = 'SilentlyContinue'
        & $FilePath @Arguments *> $null
        return ($LASTEXITCODE -eq 0)
    }
    catch {
        return $false
    }
    finally {
        $ErrorActionPreference = $previousPreference
    }
}

function Invoke-NativeChecked {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$Arguments = @(),
        [Parameter(Mandatory = $true)][string]$FailureMessage
    )

    $previousPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & $FilePath @Arguments
        $exitCode = $LASTEXITCODE
    }
    catch {
        throw "$FailureMessage $($_.Exception.Message)"
    }
    finally {
        $ErrorActionPreference = $previousPreference
    }

    if ($exitCode -ne 0) { throw "$FailureMessage (종료 코드: $exitCode)" }
}

function New-BackendVenv {
    if (Get-Command py.exe -ErrorAction SilentlyContinue) {
        if (Test-NativeCommand -FilePath 'py.exe' -Arguments @('-3', '-c', 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)')) {
            Invoke-NativeChecked -FilePath 'py.exe' -Arguments @('-3', '-m', 'venv', $backendVenv) -FailureMessage 'Python 가상환경 생성에 실패했습니다.'
            return
        }
    }

    if (Get-Command python.exe -ErrorAction SilentlyContinue) {
        if (Test-NativeCommand -FilePath 'python.exe' -Arguments @('-c', 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)')) {
            Invoke-NativeChecked -FilePath 'python.exe' -Arguments @('-m', 'venv', $backendVenv) -FailureMessage 'Python 가상환경 생성에 실패했습니다.'
            return
        }
    }

    throw 'Python 3.10 이상이 필요합니다. https://python.org 에서 Python을 설치할 때 Add Python to PATH를 선택하세요.'
}

if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue) -or -not (Get-Command node.exe -ErrorAction SilentlyContinue)) {
    throw 'Node.js와 npm이 필요합니다. https://nodejs.org 에서 Node.js LTS를 설치하세요.'
}

if (-not (Test-Path -LiteralPath $backendPython) -or -not (Test-NativeCommand -FilePath $backendPython -Arguments @('-c', 'import sys'))) {
    Write-Host '[1/4] Python 가상환경을 만듭니다.'
    if (Test-Path -LiteralPath $backendVenv) {
        # Virtual environments contain absolute interpreter paths and cannot be
        # copied reliably between PCs. Recreate only this generated directory.
        Remove-Item -LiteralPath $backendVenv -Recurse -Force
    }
    New-BackendVenv
}
else {
    Write-Host '[1/4] Python 가상환경이 준비되어 있습니다.'
}

if (-not (Test-NativeCommand -FilePath $backendPython -Arguments @('-c', 'import fastapi, uvicorn'))) {
    Write-Host '[2/4] 백엔드 패키지를 설치합니다.'
    Invoke-NativeChecked -FilePath $backendPython -Arguments @('-m', 'pip', 'install', '--disable-pip-version-check', '-r', (Join-Path $backendDir 'requirements.txt')) -FailureMessage '백엔드 패키지 설치에 실패했습니다. 인터넷 연결을 확인하세요.'
}
else {
    Write-Host '[2/4] 백엔드 패키지가 준비되어 있습니다.'
}

$nodePath = (Get-Command node.exe).Source
$viteScript = Join-Path $frontendDir 'node_modules\vite\bin\vite.js'
if (-not (Test-Path -LiteralPath $viteScript) -or -not (Test-NativeCommand -FilePath $nodePath -Arguments @($viteScript, '--version'))) {
    Write-Host '[3/4] 프런트엔드 패키지를 설치합니다.'
    Push-Location $frontendDir
    try {
        Invoke-NativeChecked -FilePath 'npm.cmd' -Arguments @('install', '--no-audit', '--no-fund') -FailureMessage '프런트엔드 패키지 설치에 실패했습니다. 인터넷 연결을 확인하세요.'
    }
    finally { Pop-Location }
}
else {
    Write-Host '[3/4] 프런트엔드 패키지가 준비되어 있습니다.'
}

New-Item -ItemType Directory -Force -Path $runDir | Out-Null

# Clean up servers left by a previous launcher run before checking the ports.
$hasPreviousRun = (Test-Path -LiteralPath (Join-Path $runDir 'backend.pid')) -or (Test-Path -LiteralPath (Join-Path $runDir 'frontend.pid'))
if ($hasPreviousRun) {
    Write-Host '이전 실행 서버를 정리하고 다시 시작합니다.'
    & (Join-Path $PSScriptRoot 'stop-windows.ps1') -Quiet
    Start-Sleep -Milliseconds 700
}

foreach ($port in 8000, 5173) {
    $connection = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($connection) {
        throw "포트 $port 가 이미 사용 중입니다. stop-windows.bat을 실행하거나 기존 서버를 종료하세요."
    }
}

Write-Host '[4/4] 백엔드와 프런트엔드를 시작합니다.'
$backendProcess = Start-Process -FilePath $backendPython -ArgumentList @('-m','uvicorn','main:app','--host','127.0.0.1','--port','8000') -WorkingDirectory $backendDir -WindowStyle Hidden -PassThru
# Use a path relative to WorkingDirectory. Start-Process joins ArgumentList into
# one string, so an absolute path would break when the project path has spaces.
$frontendProcess = Start-Process -FilePath $nodePath -ArgumentList @('node_modules\vite\bin\vite.js','--host','127.0.0.1') -WorkingDirectory $frontendDir -WindowStyle Hidden -PassThru

Set-Content -LiteralPath (Join-Path $runDir 'backend.pid') -Value $backendProcess.Id
Set-Content -LiteralPath (Join-Path $runDir 'frontend.pid') -Value $frontendProcess.Id

$backendReady = $false
for ($attempt = 0; $attempt -lt 40; $attempt++) {
    try {
        $response = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/api/health' -UseBasicParsing -TimeoutSec 1
        if ($response.StatusCode -eq 200) { $backendReady = $true; break }
    }
    catch { Start-Sleep -Milliseconds 500 }
}

if (-not $backendReady) {
    & (Join-Path $PSScriptRoot 'stop-windows.ps1') -Quiet
    throw '백엔드가 제한 시간 안에 시작되지 않았습니다.'
}

$frontendReady = $false
for ($attempt = 0; $attempt -lt 60; $attempt++) {
    try {
        $response = Invoke-WebRequest -Uri 'http://127.0.0.1:5173' -UseBasicParsing -TimeoutSec 1
        if ($response.StatusCode -eq 200) { $frontendReady = $true; break }
    }
    catch { Start-Sleep -Milliseconds 500 }
}

if (-not $frontendReady) {
    & (Join-Path $PSScriptRoot 'stop-windows.ps1') -Quiet
    throw '프런트엔드가 제한 시간 안에 시작되지 않았습니다.'
}

try {
    Start-Process -FilePath (Join-Path $env:SystemRoot 'explorer.exe') -ArgumentList 'http://localhost:5173' -ErrorAction Stop
}
catch {
    Write-Warning '브라우저를 자동으로 열 수 없습니다. http://localhost:5173 을 직접 여세요.'
}
Write-Host ''
Write-Host '슬쩍이 실행되었습니다: http://localhost:5173' -ForegroundColor Green
Write-Host '종료하려면 stop-windows.bat을 실행하세요.'
Write-Host '이 창은 닫아도 서버가 유지됩니다.'
