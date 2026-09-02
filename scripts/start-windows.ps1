$ErrorActionPreference = 'Stop'

$projectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$backendDir = Join-Path $projectRoot 'backend'
$frontendDir = Join-Path $projectRoot 'frontend'
$runDir = Join-Path $projectRoot '.run'
$backendPython = Join-Path $backendDir '.venv\Scripts\python.exe'

Write-Host '슬쩍 서버를 준비합니다...' -ForegroundColor Cyan

if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue) -or -not (Get-Command node.exe -ErrorAction SilentlyContinue)) {
    throw 'Node.js와 npm이 필요합니다. https://nodejs.org 에서 Node.js LTS를 설치하세요.'
}

if (-not (Test-Path -LiteralPath $backendPython)) {
    Write-Host '[1/4] Python 가상환경을 만듭니다.'
    if (Get-Command python.exe -ErrorAction SilentlyContinue) {
        & python.exe -m venv (Join-Path $backendDir '.venv')
    }
    elseif (Get-Command py.exe -ErrorAction SilentlyContinue) {
        & py.exe -3 -m venv (Join-Path $backendDir '.venv')
    }
    else {
        throw 'Python 3가 필요합니다. https://python.org 에서 Python을 설치하세요.'
    }
}

& $backendPython -c 'import fastapi, uvicorn' 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host '[2/4] 백엔드 패키지를 설치합니다.'
    & $backendPython -m pip install -r (Join-Path $backendDir 'requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw '백엔드 패키지 설치에 실패했습니다.' }
}
else {
    Write-Host '[2/4] 백엔드 패키지가 준비되어 있습니다.'
}

$vitePath = Join-Path $frontendDir 'node_modules\.bin\vite.cmd'
if (-not (Test-Path -LiteralPath $vitePath)) {
    Write-Host '[3/4] 프런트엔드 패키지를 설치합니다.'
    Push-Location $frontendDir
    try { & npm.cmd install --no-audit --no-fund }
    finally { Pop-Location }
    if ($LASTEXITCODE -ne 0) { throw '프런트엔드 패키지 설치에 실패했습니다.' }
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
$nodePath = (Get-Command node.exe).Source
$viteScript = Join-Path $frontendDir 'node_modules\vite\bin\vite.js'
$frontendProcess = Start-Process -FilePath $nodePath -ArgumentList @($viteScript,'--host','127.0.0.1') -WorkingDirectory $frontendDir -WindowStyle Hidden -PassThru

Set-Content -LiteralPath (Join-Path $runDir 'backend.pid') -Value $backendProcess.Id
Set-Content -LiteralPath (Join-Path $runDir 'frontend.pid') -Value $frontendProcess.Id

$ready = $false
for ($attempt = 0; $attempt -lt 40; $attempt++) {
    try {
        $response = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/api/health' -UseBasicParsing -TimeoutSec 1
        if ($response.StatusCode -eq 200) { $ready = $true; break }
    }
    catch { Start-Sleep -Milliseconds 500 }
}

if (-not $ready) {
    & (Join-Path $PSScriptRoot 'stop-windows.ps1') -Quiet
    throw '백엔드가 제한 시간 안에 시작되지 않았습니다.'
}

Start-Sleep -Seconds 1
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
