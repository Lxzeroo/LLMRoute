param([switch]$ReuseExistingDb,[switch]$SkipModels)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
function Check-Exit($Message) { if ($LASTEXITCODE -ne 0) { throw $Message } }
if (!(Test-Path 'backend\app\main.py') -or !(Test-Path 'frontend\package.json')) { throw 'Incomplete archive. Extract the entire ZIP into a new directory.' }
docker info --format '{{.ServerVersion}}' | Out-Null
Check-Exit 'Start Docker Desktop first.'
if ($ReuseExistingDb) {
    $raw = docker inspect llmroute-db
    Check-Exit 'Existing llmroute-db container not found.'
    $container = ($raw | ConvertFrom-Json)[0]
    $password = ($container.Config.Env | Where-Object { $_ -like 'POSTGRES_PASSWORD=*' }) -replace '^POSTGRES_PASSWORD=', ''
    if ([string]::IsNullOrWhiteSpace($password)) { throw 'Cannot recover database credentials.' }
    docker start llmroute-db | Out-Null
    Check-Exit 'Could not start existing database.'
    $dbName = 'llmroute-db'; $dbPort = 5433
} else {
    if (!(Test-Path '.env')) { "DB_PASSWORD=$([guid]::NewGuid().ToString('N'))" | Set-Content .env -Encoding ASCII }
    $password = (Get-Content .env | Where-Object { $_ -match '^DB_PASSWORD=' }) -replace '^DB_PASSWORD=', ''
    if ([string]::IsNullOrWhiteSpace($password)) { throw 'DB_PASSWORD missing from root .env.' }
    docker compose -p llmroute-complete up -d --wait
    Check-Exit 'Database startup failed.'
    $dbName = 'llmroute-complete-db'; $dbPort = 5434
}
$ready = $false
for ($i=0; $i -lt 30; $i++) {
    docker exec $dbName pg_isready -U llmroute -d llmroute | Out-Null
    if ($LASTEXITCODE -eq 0) { $ready=$true; break }
    Start-Sleep -Seconds 2
}
if (!$ready) { throw 'Database not ready.' }
Get-Content schema.sql -Raw | docker exec -i $dbName psql -v ON_ERROR_STOP=1 -U llmroute -d llmroute
Check-Exit 'Schema initialization failed.'
if (!(Test-Path 'backend\.env')) {
    $escaped = [uri]::EscapeDataString($password)
    @"
DATABASE_URL=postgresql://llmroute:${escaped}@127.0.0.1:${dbPort}/llmroute
OLLAMA_BASE_URL=http://127.0.0.1:11434
MODEL_KEEP_ALIVE=0
MAX_CONCURRENT_REQUESTS=1
CONTEXT_WINDOW=2048
"@ | Set-Content backend\.env -Encoding ASCII
} else { Write-Host 'Existing backend .env preserved. Ensure it points to your selected database.' }
Remove-Variable password
Push-Location backend
try {
    if (!(Test-Path '.venv\Scripts\python.exe')) { python -m venv .venv; Check-Exit 'Virtual environment creation failed.' }
    & .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    Check-Exit 'Python dependencies failed.'
    & .\.venv\Scripts\python.exe -m pytest tests -q
    Check-Exit 'Tests failed.'
    & .\.venv\Scripts\python.exe -c "from app.core.database import check_database; print(check_database())"
    Check-Exit 'Database connection test failed.'
} finally { Pop-Location }
if (!$SkipModels) {
    foreach ($model in @('all-minilm:22m','qwen2.5:1.5b','qwen2.5:3b','qwen2.5:7b')) { ollama pull $model; Check-Exit "Ollama model unavailable: $model" }
}
Push-Location frontend
try { npm.cmd install; Check-Exit 'Frontend dependency installation failed.' } finally { Pop-Location }
Write-Host 'Setup complete. Run Start-Backend.ps1 and Start-Frontend.ps1 in separate terminals.'
