param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173,
    [switch]$SkipMigrate
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$backendPath = Join-Path $repoRoot "backend"
$frontendPath = Join-Path $repoRoot "frontend"
$logPath = Join-Path $repoRoot ".run-logs"

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $Name"
    }
}

function Ensure-PortFree {
    param([int]$Port)

    $listeners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $listeners) {
        return
    }

    $pids = $listeners | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($pid in $pids) {
        try {
            Stop-Process -Id $pid -Force -ErrorAction Stop
            Write-Host "Stopped existing process $pid on port $Port."
        }
        catch {
            Write-Warning "Could not stop process $pid on port ${Port}: $($_.Exception.Message)"
        }
    }
}

Require-Command -Name "python"
Require-Command -Name "npm"

if (-not (Test-Path $logPath)) {
    New-Item -ItemType Directory -Path $logPath | Out-Null
}

$pgService = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $pgService -or $pgService.Status -ne "Running") {
    throw "PostgreSQL service is not running. Start your local PostgreSQL service first."
}

if (-not $SkipMigrate) {
    Push-Location $backendPath
    try {
        Write-Host "Applying database migrations..."
        python -m alembic upgrade head
    }
    finally {
        Pop-Location
    }
}

Ensure-PortFree -Port $BackendPort
Ensure-PortFree -Port $FrontendPort

$env:APP_NAME = "Workflow Orchestrator API"
$env:APP_ENV = "development"
$env:APP_DEBUG = "true"
$env:APP_LOG_LEVEL = "INFO"
$env:DATABASE_URL = "postgresql+psycopg2://workflow:workflow@localhost:5432/workflow"
$env:CORS_ORIGINS = "http://localhost:$FrontendPort,http://127.0.0.1:$FrontendPort"
$env:VITE_API_BASE_URL = "http://127.0.0.1:$BackendPort/api/v1"

Write-Host "Starting backend on http://127.0.0.1:$BackendPort ..."
$backendOut = Join-Path $logPath "backend.out.log"
$backendErr = Join-Path $logPath "backend.err.log"
$backendProc = Start-Process -FilePath "python" -WorkingDirectory $backendPath -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "$BackendPort" -RedirectStandardOutput $backendOut -RedirectStandardError $backendErr -PassThru

Write-Host "Starting frontend on http://127.0.0.1:$FrontendPort ..."
$frontendOut = Join-Path $logPath "frontend.out.log"
$frontendErr = Join-Path $logPath "frontend.err.log"
$frontendProc = Start-Process -FilePath "npm.cmd" -WorkingDirectory $frontendPath -ArgumentList "run", "dev", "--", "--host", "127.0.0.1", "--port", "$FrontendPort" -RedirectStandardOutput $frontendOut -RedirectStandardError $frontendErr -PassThru

$backendReady = $false
for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Seconds 1
    try {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:$BackendPort/api/v1/health" -UseBasicParsing -TimeoutSec 2
        if ($resp.StatusCode -eq 200) {
            $backendReady = $true
            break
        }
    }
    catch {
    }
}

if ($backendReady) {
    Write-Host "Backend is ready."
} else {
    Write-Warning "Backend health check did not pass yet. Check spawned backend terminal logs."
}

Start-Sleep -Seconds 1
if ($backendProc.HasExited) {
    Write-Warning "Backend process exited early. See $backendErr and $backendOut"
}
if ($frontendProc.HasExited) {
    Write-Warning "Frontend process exited early. See $frontendErr and $frontendOut"
}

Write-Host "Start complete."
Write-Host "Backend PID:  $($backendProc.Id)"
Write-Host "Frontend PID: $($frontendProc.Id)"
Write-Host "Logs:     $logPath"
Write-Host "Backend:  http://127.0.0.1:$BackendPort/api/v1/health"
Write-Host "Frontend: http://127.0.0.1:$FrontendPort"
