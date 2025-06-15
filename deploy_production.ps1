# V35 Production Deployment Script for Windows
# This script deploys the system to a production environment with enhanced security and monitoring

# Check if .env.production file exists
if (-not (Test-Path .env.production)) {
    Write-Error "Error: .env.production file not found. Please create it with the required production environment variables."
    exit 1
}

# Load production environment variables
$envContent = Get-Content .env.production
foreach ($line in $envContent) {
    if ($line -match '^\s*([^#][^=]+)=(.*)$') {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim()
        [Environment]::SetEnvironmentVariable($key, $value, "Process")
    }
}

# Check required environment variables
if (-not $env:RPC_URL -or -not $env:TRUST_CURVE_ADDRESS -or -not $env:PROOF_EXECUTOR_ADDRESS -or -not $env:API_KEY) {
    Write-Error "Error: Required environment variables are missing. Please check your .env.production file."
    exit 1
}

Write-Host "Starting V35 Production Deployment..." -ForegroundColor Green

# Create production docker-compose file
Write-Host "Creating production docker-compose configuration..." -ForegroundColor Cyan
Copy-Item -Path "docker-compose.yml" -Destination "docker-compose.production.yml"

# Build production images
Write-Host "Building production containers..." -ForegroundColor Cyan
docker-compose -f docker-compose.production.yml build

# Deploy to production environment
Write-Host "Deploying to production environment..." -ForegroundColor Cyan
docker-compose -f docker-compose.production.yml up -d

# Wait for services to start
Write-Host "Waiting for services to start..." -ForegroundColor Cyan
Start-Sleep -Seconds 15

# Check if services are running
Write-Host "Checking if services are running..." -ForegroundColor Cyan
docker-compose -f docker-compose.production.yml ps

# Run production health checks
Write-Host "Running production health checks..." -ForegroundColor Cyan
$backendHealth = Invoke-RestMethod -Uri "http://localhost:8080/health" -Method Get
$pythonAgentHealth = Invoke-RestMethod -Uri "http://localhost:5000/health" -Method Get

Write-Host "Backend Health: $($backendHealth.status)" -ForegroundColor Yellow
Write-Host "Python Agent Health: $($pythonAgentHealth.status)" -ForegroundColor Yellow

Write-Host "Production deployment completed successfully!" -ForegroundColor Green
Write-Host "Frontend: https://localhost:3000" -ForegroundColor Yellow
Write-Host "Backend API: https://localhost:8080" -ForegroundColor Yellow
Write-Host "Python Agent: https://localhost:5000" -ForegroundColor Yellow
Write-Host "MongoDB: mongodb://localhost:27017" -ForegroundColor Yellow

Write-Host "To stop the production services, run: docker-compose -f docker-compose.production.yml down" -ForegroundColor Cyan