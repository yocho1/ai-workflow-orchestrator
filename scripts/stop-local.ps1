param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173
)

$ErrorActionPreference = "Stop"

function Stop-PortListener {
    param([int]$Port)

    $listeners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $listeners) {
        Write-Host "Port $Port is already free."
        return
    }

    $pids = $listeners | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($pid in $pids) {
        try {
            Stop-Process -Id $pid -Force -ErrorAction Stop
            Write-Host "Stopped process $pid on port $Port."
        }
        catch {
            Write-Warning "Could not stop process $pid on port ${Port}: $($_.Exception.Message)"
        }
    }
}

Stop-PortListener -Port $BackendPort
Stop-PortListener -Port $FrontendPort

Write-Host "Stop complete."
