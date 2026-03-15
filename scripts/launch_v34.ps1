# =================================================================================================
# LAUNCHER FOR ADVANCED FLASH LOAN ARBITRAGE SYSTEM - V34
# =================================================================================================

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "ADVANCED FLASH LOAN ARBITRAGE SYSTEM - V34 (LIVE PROVING & HARDENED AGENT)" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

# Parse command line arguments
param (
    [string]$mode = "institutional",
    [switch]$setupOnly = $false
)

Write-Host "Mode: $mode" -ForegroundColor Yellow
Write-Host "================================================================================" -ForegroundColor Cyan

# Build arguments for the Python script
$pythonArgs = @("launch_v34_agent.py", "--mode", $mode)
if ($setupOnly) {
    $pythonArgs += "--setup-only"
}

# Run the launcher script
try {
    & python $pythonArgs
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ Agent launched successfully" -ForegroundColor Green
    } else {
        Write-Host "`n❌ Failed to launch agent" -ForegroundColor Red
    }
} catch {
    Write-Host "`n❌ Error: $_" -ForegroundColor Red
}

if ($setupOnly) {
    Write-Host "`nSetup completed. Agent not launched." -ForegroundColor Yellow
}

Write-Host ""
Read-Host "Press Enter to exit"