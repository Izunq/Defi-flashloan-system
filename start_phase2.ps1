# PowerShell script to start the Phase 2 system
# This script starts Redis, Celery worker, and the main application

Write-Host "=== Starting Phase 2 System ===" -ForegroundColor Cyan

# Check if Redis is running
$redisRunning = Get-Process -Name "redis-server" -ErrorAction SilentlyContinue
if (-not $redisRunning) {
    Write-Host "Starting Redis server..." -ForegroundColor Yellow
    Start-Process -FilePath "redis-server" -WindowStyle Minimized
    Start-Sleep -Seconds 2
} else {
    Write-Host "Redis server is already running." -ForegroundColor Green
}

# Start Celery worker in a new window
Write-Host "Starting Celery worker..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-Command `"cd '$PSScriptRoot'; celery -A pipelines.arbitrage_pipeline worker --loglevel=info`"" -WindowStyle Normal

# Wait for Celery to initialize
Start-Sleep -Seconds 3

# Start the main application
Write-Host "Starting main application..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-Command `"cd '$PSScriptRoot'; python main.py`"" -WindowStyle Normal

# Start the market data simulator
Write-Host "Starting market data simulator..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-Command `"cd '$PSScriptRoot'; python market_data_simulator.py`"" -WindowStyle Normal

# Open the monitoring dashboard
Write-Host "Opening monitoring dashboard..." -ForegroundColor Yellow
Start-Process "$PSScriptRoot\monitoring_dashboard.html"

Write-Host "=== Phase 2 System Started ===" -ForegroundColor Green
Write-Host "Press Ctrl+C in each window to stop the components when done." -ForegroundColor Yellow