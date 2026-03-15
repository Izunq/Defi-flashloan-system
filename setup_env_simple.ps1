# Simple Environment Setup Script
param([string]$Environment = "development")

Write-Host "Setting up $Environment environment..." -ForegroundColor Green

# Copy template files
if ($Environment -eq "production") {
    Copy-Item ".env.production.template" ".env.production" -Force
    Write-Host "Created .env.production" -ForegroundColor Green
} elseif ($Environment -eq "test") {
    Copy-Item ".env.test.template" ".env.test" -Force  
    Write-Host "Created .env.test" -ForegroundColor Green
} else {
    Copy-Item ".env.test.template" ".env" -Force
    Write-Host "Created .env for development" -ForegroundColor Green
}

Write-Host "Environment setup complete!" -ForegroundColor Cyan
