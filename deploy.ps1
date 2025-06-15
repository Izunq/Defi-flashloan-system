# V35 Deployment Script for Windows

# Check if .env file exists
if (-not (Test-Path .env)) {
    Write-Error "Error: .env file not found. Please create it with the required environment variables."
    exit 1
}

# Load environment variables
$envContent = Get-Content .env
foreach ($line in $envContent) {
    if ($line -match '^\s*([^#][^=]+)=(.*)$') {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim()
        [Environment]::SetEnvironmentVariable($key, $value, "Process")
    }
}

# Check required environment variables
if (-not $env:RPC_URL -or -not $env:TRUST_CURVE_ADDRESS -or -not $env:PROOF_EXECUTOR_ADDRESS -or -not $env:API_KEY) {
    Write-Error "Error: Required environment variables are missing. Please check your .env file."
    exit 1
}

Write-Host "Starting V35 deployment..." -ForegroundColor Green

# Build and start the containers
Write-Host "Building and starting containers..." -ForegroundColor Cyan
docker-compose build
docker-compose up -d

# Wait for services to start
Write-Host "Waiting for services to start..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

# Check if services are running
Write-Host "Checking if services are running..." -ForegroundColor Cyan
docker-compose ps

# Test the API
Write-Host "Testing the API..." -ForegroundColor Cyan
Set-Location -Path backend
node test_api.js
Set-Location -Path ..

Write-Host "Deployment completed successfully!" -ForegroundColor Green
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Yellow
Write-Host "Backend API: http://localhost:8080" -ForegroundColor Yellow
Write-Host "Python Agent: http://localhost:5000" -ForegroundColor Yellow
Write-Host "MongoDB: mongodb://localhost:27017" -ForegroundColor Yellow

Write-Host "To stop the services, run: docker-compose down" -ForegroundColor Cyan