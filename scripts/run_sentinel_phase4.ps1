# Sentinel Integration Phase 4 - Testing & Optimization
# This script runs all Phase 4 components

Write-Host "Starting Sentinel Integration Phase 4 - Testing & Optimization" -ForegroundColor Cyan
Write-Host "=============================================================" -ForegroundColor Cyan

# Create logs directory if it doesn't exist
if (-not (Test-Path -Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
    Write-Host "Created logs directory" -ForegroundColor Green
}

# Create deployment directory if it doesn't exist
if (-not (Test-Path -Path "deployment")) {
    New-Item -ItemType Directory -Path "deployment" | Out-Null
    Write-Host "Created deployment directory" -ForegroundColor Green
}

# Step 1: Run End-to-End Integration Tests
Write-Host "`nStep 1: Running End-to-End Integration Tests" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Yellow
python test_sentinel_integration.py | Tee-Object -FilePath "logs/integration_test.log"

# Step 2: Run Performance Optimization
Write-Host "`nStep 2: Running Performance Optimization" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Yellow
python optimize_sentinel_performance.py | Tee-Object -FilePath "logs/performance_optimization.log"

# Step 3: Run Alert Delivery Validation
Write-Host "`nStep 3: Running Alert Delivery Validation" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Yellow
python validate_alert_delivery.py | Tee-Object -FilePath "logs/alert_validation.log"

# Step 4: Prepare for Production Deployment
Write-Host "`nStep 4: Preparing for Production Deployment" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Yellow
python prepare_sentinel_production.py | Tee-Object -FilePath "logs/deployment_preparation.log"

# Summary
Write-Host "`nPhase 4 Execution Summary" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan
Write-Host "Integration Test Results: Check logs/integration_test.log" -ForegroundColor White
Write-Host "Performance Report: Check sentinel_optimization_report.md" -ForegroundColor White
Write-Host "Alert Validation Report: Check alert_delivery_validation_report.md" -ForegroundColor White
Write-Host "Deployment Package: Check deployment directory" -ForegroundColor White
Write-Host "Deployment Documentation: Check SENTINEL_INTEGRATION_DOCUMENTATION.md" -ForegroundColor White

Write-Host "`nPhase 4 completed successfully!" -ForegroundColor Green