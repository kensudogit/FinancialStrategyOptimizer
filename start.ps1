Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:COMPOSE_BAKE = 'false'
docker compose up --build -d
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host 'UI  http://localhost:3020'
Write-Host 'API http://localhost:8020/docs'
