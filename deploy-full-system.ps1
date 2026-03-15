#!/usr/bin/env pwsh
# 🚀 Full System Deployment Script
# Deploys the entire arbitrage system to production

param(
    [string]$ProjectId = "",
    [string]$Region = "us-central1",
    [switch]$SkipInfrastructure,
    [switch]$SkipMonitoring,
    [switch]$DryRun
)

Write-Host "🚀 ARTEMIS ARBITRAGE SYSTEM - FULL DEPLOYMENT" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# Check prerequisites
function Test-Prerequisites {
    Write-Host "🔍 Checking prerequisites..." -ForegroundColor Yellow
    
    # Check if gcloud is installed
    try {
        $gcloudVersion = gcloud version --format="value(Google Cloud SDK)" 2>$null
        Write-Host "✅ Google Cloud SDK: $gcloudVersion" -ForegroundColor Green
    } catch {
        Write-Host "❌ Google Cloud SDK not found. Please install: https://cloud.google.com/sdk/docs/install" -ForegroundColor Red
        exit 1
    }
    
    # Check if terraform is installed
    try {
        $terraformVersion = terraform version -json | ConvertFrom-Json | Select-Object -ExpandProperty terraform_version
        Write-Host "✅ Terraform: $terraformVersion" -ForegroundColor Green
    } catch {
        Write-Host "❌ Terraform not found. Please install: https://www.terraform.io/downloads" -ForegroundColor Red
        exit 1
    }
    
    # Check if docker is installed
    try {
        $dockerVersion = docker --version
        Write-Host "✅ Docker: $dockerVersion" -ForegroundColor Green
    } catch {
        Write-Host "❌ Docker not found. Please install Docker Desktop" -ForegroundColor Red
        exit 1
    }
    
    # Check if kubectl is installed
    try {
        $kubectlVersion = kubectl version --client --short 2>$null
        Write-Host "✅ kubectl: $kubectlVersion" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  kubectl not found. Installing via gcloud..." -ForegroundColor Yellow
        gcloud components install kubectl
    }
}

# Set up GCP project and authentication
function Initialize-GCPProject {
    param([string]$ProjectId)
    
    Write-Host "🔧 Setting up GCP project..." -ForegroundColor Yellow
    
    if (-not $ProjectId) {
        Write-Host "Please provide a GCP Project ID:" -ForegroundColor Yellow
        $ProjectId = Read-Host "GCP Project ID"
    }
    
    # Set the project
    gcloud config set project $ProjectId
    
    # Authenticate if needed
    $currentAccount = gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>$null
    if (-not $currentAccount) {
        Write-Host "🔐 Authenticating with Google Cloud..." -ForegroundColor Yellow
        gcloud auth login
        gcloud auth application-default login
    }
    
    Write-Host "✅ GCP Project set to: $ProjectId" -ForegroundColor Green
    return $ProjectId
}

# Deploy infrastructure with Terraform
function Deploy-Infrastructure {
    param([string]$ProjectId, [string]$Region)
    
    Write-Host "🏗️  Deploying infrastructure to GCP..." -ForegroundColor Yellow
    
    Set-Location "infrastructure/gcp"
    
    # Initialize Terraform
    terraform init
    
    # Create terraform.tfvars
    @"
project_id = "$ProjectId"
region = "$Region"
zone = "$Region-a"
environment = "production"
"@ | Out-File -FilePath "terraform.tfvars" -Encoding UTF8
    
    # Plan deployment
    Write-Host "📋 Creating deployment plan..." -ForegroundColor Yellow
    terraform plan -out=tfplan
    
    if (-not $DryRun) {
        # Apply deployment
        Write-Host "🚀 Applying infrastructure deployment..." -ForegroundColor Yellow
        terraform apply tfplan
        
        # Get outputs
        $gkeCluster = terraform output -raw gke_cluster_name
        $cloudSqlInstance = terraform output -raw cloud_sql_instance_name
        $cloudRunService = terraform output -raw cloud_run_artemis_url
        
        Write-Host "✅ Infrastructure deployed successfully!" -ForegroundColor Green
        Write-Host "   GKE Cluster: $gkeCluster" -ForegroundColor Cyan
        Write-Host "   Cloud SQL: $cloudSqlInstance" -ForegroundColor Cyan
        Write-Host "   Artemis AI: $cloudRunService" -ForegroundColor Cyan
    }
    
    Set-Location "../.."
}

# Deploy monitoring stack
function Deploy-Monitoring {
    Write-Host "📊 Deploying monitoring stack..." -ForegroundColor Yellow
    
    # Create monitoring namespace in Kubernetes
    kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy Prometheus and Grafana
    Set-Location "config"
    
    if (-not $DryRun) {
        docker-compose -f docker-compose.monitoring.yml up -d
        
        Write-Host "✅ Monitoring stack deployed!" -ForegroundColor Green
        Write-Host "   Prometheus: http://localhost:9090" -ForegroundColor Cyan
        Write-Host "   Grafana: http://localhost:3001 (admin/admin)" -ForegroundColor Cyan
    }
    
    Set-Location ".."
}

# Start Artemis AI Core
function Start-ArtemisCore {
    Write-Host "🧠 Starting Artemis AI Core..." -ForegroundColor Yellow
    
    Set-Location "artemis_core"
    
    # Install dependencies
    pip install -r requirements.txt
    
    # Check environment configuration
    if (-not (Test-Path ".env")) {
        Write-Host "⚠️  .env file not found. Creating template..." -ForegroundColor Yellow
        @"
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Database Configuration  
DATABASE_URL=postgresql://user:password@localhost:5432/flashloan_db

# Service Configuration
ARTEMIS_PORT=8082
ARTEMIS_HOST=0.0.0.0

# Security
SECRET_KEY=your_secret_key_here
AI_PROVIDER=gemini
GEMINI_MODEL=gemini-1.5-pro
"@ | Out-File -FilePath ".env" -Encoding UTF8
        
        Write-Host "📝 Please configure .env file with your API keys" -ForegroundColor Yellow
    }
    
    if (-not $DryRun) {
        # Start Artemis AI Core in background
        Start-Process -FilePath "python" -ArgumentList "artemis_ai_core.py" -NoNewWindow
        Start-Sleep 3
        
        # Test the service
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:8082/health" -Method Get
            Write-Host "✅ Artemis AI Core is running!" -ForegroundColor Green
            Write-Host "   Health: $($response.status)" -ForegroundColor Cyan
        } catch {
            Write-Host "⚠️  Artemis AI Core may not be fully ready yet" -ForegroundColor Yellow
        }
    }
    
    Set-Location ".."
}

# Start data ingestion services
function Start-DataIngestion {
    Write-Host "📡 Starting data ingestion services..." -ForegroundColor Yellow
    
    Set-Location "backend"
    
    # Install Python dependencies
    pip install -r requirements.txt
    
    if (-not $DryRun) {
        # Start DataIngestionService
        Start-Process -FilePath "python" -ArgumentList "-m", "src.services.DataIngestionService" -NoNewWindow
        
        Write-Host "✅ Data ingestion services started!" -ForegroundColor Green
    }
    
    Set-Location ".."
}

# Main execution
function Main {
    Test-Prerequisites
    
    $ProjectId = Initialize-GCPProject -ProjectId $ProjectId
    
    if (-not $SkipInfrastructure) {
        Deploy-Infrastructure -ProjectId $ProjectId -Region $Region
    }
    
    if (-not $SkipMonitoring) {
        Deploy-Monitoring
    }
    
    Start-ArtemisCore
    Start-DataIngestion
    
    Write-Host ""
    Write-Host "🎉 DEPLOYMENT COMPLETE!" -ForegroundColor Green
    Write-Host "========================" -ForegroundColor Green
    Write-Host "🧠 Artemis AI Core: http://localhost:8082" -ForegroundColor Cyan
    Write-Host "📊 Grafana: http://localhost:3001" -ForegroundColor Cyan
    Write-Host "📈 Prometheus: http://localhost:9090" -ForegroundColor Cyan
    Write-Host "🌐 Frontend: http://localhost:3000" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Configure API keys in artemis_core/.env" -ForegroundColor White
    Write-Host "2. Set up database connections" -ForegroundColor White
    Write-Host "3. Configure exchange API credentials" -ForegroundColor White
    Write-Host "4. Monitor system health via Grafana" -ForegroundColor White
}

# Execute main function
Main
