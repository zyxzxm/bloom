$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host ''
Write-Host '  BLOOM — GERADOR DE VERSAO PARA WINDOWS' -ForegroundColor Cyan
Write-Host '  Uma execucao aqui; o jogador recebe o instalador e nao precisa de Python.' -ForegroundColor DarkCyan
Write-Host ''

$DefaultApiUrl = 'https://bloom-world.onrender.com'
$ApiInput = $env:BLOOM_API_URL
if ([string]::IsNullOrWhiteSpace($ApiInput)) {
    $ApiInput = Read-Host "URL HTTPS publica da API (Enter usa $DefaultApiUrl)"
}
if ([string]::IsNullOrWhiteSpace($ApiInput)) {
    $ApiUrl = $DefaultApiUrl
} else {
    $ApiUrl = $ApiInput.Trim().TrimEnd('/')
}
if (-not $ApiUrl.StartsWith('https://')) {
    throw 'A URL precisa comecar com https://. Publique o BLOOM WORLD antes de gerar a versao distribuivel.'
}

Write-Host 'A API gratuita do Render pode levar cerca de 50 segundos para acordar apos ficar sem uso.' -ForegroundColor DarkYellow
for ($Attempt = 1; $Attempt -le 7; $Attempt++) {
    try {
        $health = Invoke-RestMethod -Uri "$ApiUrl/health" -TimeoutSec 15
        if ($health.status -ne 'ok') { throw 'Resposta de health inesperada.' }
        Write-Host "API online: $($health.service) $($health.version)" -ForegroundColor Green
        break
    } catch {
        $HealthError = $_.Exception.Message
        if ($Attempt -eq 7) {
            throw "Nao consegui confirmar $ApiUrl/health apos varias tentativas. Detalhe: $HealthError"
        }
        Write-Host "API iniciando; nova tentativa em 5 segundos ($Attempt/7)..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
    }
}

$VenvPython = Join-Path $Root '.venv-build\Scripts\python.exe'
if (-not (Test-Path $VenvPython)) {
    Write-Host 'Preparando ferramentas de compilacao (somente neste PC de desenvolvimento)...' -ForegroundColor Yellow
    py -3.12 -m venv (Join-Path $Root '.venv-build')
}
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -r (Join-Path $Root 'requirements-client.txt')
if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar ferramentas de build.' }

$Generated = @"
"""Gerado por build_windows.ps1; URL publica, sem credenciais."""
API_URL = "$ApiUrl"
"@
$BuildConfigPath = Join-Path $Root 'bloom_app\build_config.py'
$OriginalBuildConfig = [System.IO.File]::ReadAllBytes($BuildConfigPath)
Set-Content -Path $BuildConfigPath -Value $Generated -Encoding UTF8

Write-Host 'Compilando aplicativo BLOOM...' -ForegroundColor Yellow
try {
    & $VenvPython -m PyInstaller --noconfirm --clean --windowed --onefile --name BLOOM --icon (Join-Path $Root 'assets\bloom.ico') --paths $Root --hidden-import bloom_safe.scanner --hidden-import bloom_safe.installer --hidden-import bloom_maker.editor --hidden-import bloom_app.localization --collect-all pygame --collect-all PIL bloom_app\main.py
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller falhou.' }
} finally {
    [System.IO.File]::WriteAllBytes($BuildConfigPath, $OriginalBuildConfig)
}

$Iscc = Get-Command ISCC.exe -ErrorAction SilentlyContinue
if (-not $Iscc) {
    $Candidates = @("${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe", "$env:ProgramFiles\Inno Setup 6\ISCC.exe")
    foreach ($Candidate in $Candidates) { if (Test-Path $Candidate) { $Iscc = @{ Source = $Candidate }; break } }
}
if ($Iscc) {
    Write-Host 'Criando instalador BLOOM-Setup.exe...' -ForegroundColor Yellow
    & $Iscc.Source (Join-Path $Root 'installer\BLOOM.iss')
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao criar o instalador.' }
    Write-Host "PRONTO: $Root\release\BLOOM-Setup.exe" -ForegroundColor Green
} else {
    New-Item -ItemType Directory -Force (Join-Path $Root 'release') | Out-Null
    Copy-Item (Join-Path $Root 'dist\BLOOM.exe') (Join-Path $Root 'release\BLOOM.exe') -Force
    Write-Host 'EXE pronto. Inno Setup nao encontrado; instale-o para gerar o instalador recomendado.' -ForegroundColor Yellow
    Write-Host "Arquivo: $Root\release\BLOOM.exe" -ForegroundColor Green
}
Write-Host 'Teste a instalacao em um Windows limpo antes de publicar.' -ForegroundColor Cyan
