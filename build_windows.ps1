$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host ''
Write-Host '  BLOOM — GERADOR DE VERSAO PARA WINDOWS' -ForegroundColor Cyan
Write-Host '  Uma execucao aqui; o jogador recebe o instalador e nao precisa de Python.' -ForegroundColor DarkCyan
Write-Host ''

$ApiUrl = Read-Host 'URL HTTPS publica da API (ex.: https://api.seudominio.com)'
$ApiUrl = $ApiUrl.Trim().TrimEnd('/')
if (-not $ApiUrl.StartsWith('https://')) {
    throw 'A URL precisa comecar com https://. Publique o BLOOM WORLD antes de gerar a versao distribuivel.'
}

try {
    $health = Invoke-RestMethod -Uri "$ApiUrl/health" -TimeoutSec 10
    if ($health.status -ne 'ok') { throw 'Resposta de health inesperada.' }
    Write-Host "API online: $($health.service) $($health.version)" -ForegroundColor Green
} catch {
    throw "Nao consegui confirmar $ApiUrl/health. Publique e teste a API antes de compilar. Detalhe: $($_.Exception.Message)"
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
Set-Content -Path (Join-Path $Root 'bloom_app\build_config.py') -Value $Generated -Encoding UTF8

Write-Host 'Compilando aplicativo BLOOM...' -ForegroundColor Yellow
& $VenvPython -m PyInstaller --noconfirm --clean --windowed --onefile --name BLOOM --icon (Join-Path $Root 'assets\bloom.ico') --paths $Root --hidden-import bloom_safe.scanner --hidden-import bloom_safe.installer --hidden-import bloom_maker.editor bloom_app\main.py
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller falhou.' }

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
