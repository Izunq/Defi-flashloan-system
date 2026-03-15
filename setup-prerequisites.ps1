#!/usr/bin/env pwsh
# 🔧 System Prerequisites Setup Script
# Installs all required dependencies for the arbitrage system

param(
    [switch]$SkipPython,
    [switch]$SkipDocker,
    [switch]$SkipNode
)

Write-Host "🔧 SYSTEM PREREQUISITES SETUP" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan

# Check if running as administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Install Chocolatey if not present
function Install-Chocolatey {
    if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
        Write-Host "📦 Installing Chocolatey package manager..." -ForegroundColor Yellow
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
        Write-Host "✅ Chocolatey installed" -ForegroundColor Green
    } else {
        Write-Host "✅ Chocolatey already installed" -ForegroundColor Green
    }
}

# Install Python
function Install-Python {
    if ($SkipPython) {
        Write-Host "⏭️  Skipping Python installation" -ForegroundColor Yellow
        return
    }
    
    try {
        $pythonVersion = python --version 2>$null
        if ($pythonVersion) {
            Write-Host "✅ Python already installed: $pythonVersion" -ForegroundColor Green
            return
        }
    } catch {}
    
    Write-Host "🐍 Installing Python..." -ForegroundColor Yellow
    choco install python -y
    refreshenv
    
    # Verify installation
    try {
        $pythonVersion = python --version
        Write-Host "✅ Python installed: $pythonVersion" -ForegroundColor Green
    } catch {
        Write-Host "❌ Python installation failed. Please install manually from https://python.org" -ForegroundColor Red
    }
}

# Install Node.js
function Install-NodeJS {
    if ($SkipNode) {
        Write-Host "⏭️  Skipping Node.js installation" -ForegroundColor Yellow
        return
    }
    
    try {
        $nodeVersion = node --version 2>$null
        if ($nodeVersion) {
            Write-Host "✅ Node.js already installed: $nodeVersion" -ForegroundColor Green
            return
        }
    } catch {}
    
    Write-Host "📦 Installing Node.js..." -ForegroundColor Yellow
    choco install nodejs -y
    refreshenv
    
    # Verify installation
    try {
        $nodeVersion = node --version
        Write-Host "✅ Node.js installed: $nodeVersion" -ForegroundColor Green
    } catch {
        Write-Host "❌ Node.js installation failed. Please install manually from https://nodejs.org" -ForegroundColor Red
    }
}

# Install Docker Desktop
function Install-Docker {
    if ($SkipDocker) {
        Write-Host "⏭️  Skipping Docker installation" -ForegroundColor Yellow
        return
    }
    
    try {
        $dockerVersion = docker --version 2>$null
        if ($dockerVersion) {
            Write-Host "✅ Docker already installed: $dockerVersion" -ForegroundColor Green
            return
        }
    } catch {}
    
    Write-Host "🐳 Installing Docker Desktop..." -ForegroundColor Yellow
    choco install docker-desktop -y
    
    Write-Host "⚠️  Docker Desktop requires a restart. Please restart your computer and run Docker Desktop manually." -ForegroundColor Yellow
}

# Install Git
function Install-Git {
    try {
        $gitVersion = git --version 2>$null
        if ($gitVersion) {
            Write-Host "✅ Git already installed: $gitVersion" -ForegroundColor Green
            return
        }
    } catch {}
    
    Write-Host "📚 Installing Git..." -ForegroundColor Yellow
    choco install git -y
    refreshenv
}

# Install Google Cloud CLI
function Install-GCloudCLI {
    try {
        $gcloudVersion = gcloud version --format="value(Google Cloud SDK)" 2>$null
        if ($gcloudVersion) {
            Write-Host "✅ Google Cloud CLI already installed: $gcloudVersion" -ForegroundColor Green
            return
        }
    } catch {}
    
    Write-Host "☁️  Installing Google Cloud CLI..." -ForegroundColor Yellow
    choco install gcloudsdk -y
    refreshenv
}

# Install Terraform
function Install-Terraform {
    try {
        $terraformVersion = terraform version -json | ConvertFrom-Json | Select-Object -ExpandProperty terraform_version
        if ($terraformVersion) {
            Write-Host "✅ Terraform already installed: $terraformVersion" -ForegroundColor Green
            return
        }
    } catch {}
    
    Write-Host "🏗️  Installing Terraform..." -ForegroundColor Yellow
    choco install terraform -y
    refreshenv
}

# Install VS Code (optional but recommended)
function Install-VSCode {
    try {
        $codeVersion = code --version 2>$null
        if ($codeVersion) {
            Write-Host "✅ VS Code already installed" -ForegroundColor Green
            return
        }
    } catch {}
    
    Write-Host "📝 Installing VS Code..." -ForegroundColor Yellow
    choco install vscode -y
}

# Install Python packages
function Install-PythonPackages {
    Write-Host "🐍 Installing Python packages..." -ForegroundColor Yellow
    
    # Upgrade pip first
    python -m pip install --upgrade pip
    
    # Install core packages
    $packages = @(
        "fastapi",
        "uvicorn[standard]",
        "asyncpg",
        "psycopg2-binary",
        "python-dotenv",
        "pydantic",
        "websockets",
        "aiohttp",
        "web3",
        "requests",
        "pandas",
        "numpy",
        "prometheus-client"
    )
    
    foreach ($package in $packages) {
        try {
            python -m pip install $package
            Write-Host "✅ Installed $package" -ForegroundColor Green
        } catch {
            Write-Host "⚠️  Failed to install $package" -ForegroundColor Yellow
        }
    }
}

# Create environment template
function Create-EnvironmentTemplate {
    Write-Host "📝 Creating environment configuration template..." -ForegroundColor Yellow
    
    $envTemplate = @"
# 🚀 ARTEMIS ARBITRAGE SYSTEM - ENVIRONMENT CONFIGURATION

# ==============================================
# 🧠 AI CONFIGURATION
# ==============================================
AI_PROVIDER=gemini
GOOGLE_API_KEY=your_google_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_MODEL=gemini-1.5-pro
GEMINI_MAX_TOKENS=8192
GEMINI_TEMPERATURE=0.7

# ==============================================
# 🗄️  DATABASE CONFIGURATION
# ==============================================
DATABASE_URL=postgresql://artemis:artemis_password@localhost:5432/artemis_db
REDIS_URL=redis://localhost:6379

# ==============================================
# 🌐 SERVICE CONFIGURATION
# ==============================================
ARTEMIS_PORT=8082
ARTEMIS_HOST=0.0.0.0
BACKEND_PORT=8080
FRONTEND_PORT=3000

# ==============================================
# 🔐 SECURITY
# ==============================================
SECRET_KEY=your_super_secret_key_change_this_in_production
JWT_SECRET=your_jwt_secret_key
ENCRYPTION_KEY=your_encryption_key

# ==============================================
# ⛓️  BLOCKCHAIN CONFIGURATION
# ==============================================
ETHEREUM_MAINNET_RPC=https://eth-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
ARBITRUM_RPC=https://arb-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
POLYGON_RPC=https://polygon-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
BSC_RPC=https://bsc-dataseed.binance.org/

# Private keys for trading (use test keys first!)
TRADING_PRIVATE_KEY=your_trading_wallet_private_key
ARBITRAGE_WALLET_ADDRESS=your_arbitrage_wallet_address

# ==============================================
# 💱 EXCHANGE API CONFIGURATION
# ==============================================
# Binance
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_secret

# Coinbase
COINBASE_API_KEY=your_coinbase_key
COINBASE_API_SECRET=your_coinbase_secret
COINBASE_PASSPHRASE=your_coinbase_passphrase

# Kraken
KRAKEN_API_KEY=your_kraken_key
KRAKEN_API_SECRET=your_kraken_secret

# ==============================================
# 📊 MONITORING & LOGGING
# ==============================================
ENABLE_METRICS=true
METRICS_PORT=8090
LOG_LEVEL=INFO
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin

# ==============================================
# ☁️  CLOUD CONFIGURATION
# ==============================================
GCP_PROJECT_ID=your_gcp_project_id
GCP_REGION=us-central1
GCP_ZONE=us-central1-a

# ==============================================
# 🚨 TRADING CONFIGURATION
# ==============================================
MIN_PROFIT_THRESHOLD=0.1
MAX_TRADE_SIZE_USD=1000
GAS_PRICE_LIMIT_GWEI=50
ENABLE_LIVE_TRADING=false
TESTNET_MODE=true

# ==============================================
# 🔧 DEVELOPMENT
# ==============================================
DEBUG=false
ENVIRONMENT=development
"@
    
    $envTemplate | Out-File -FilePath ".env.template" -Encoding UTF8
    
    Write-Host "✅ Environment template created at .env.template" -ForegroundColor Green
    Write-Host "📝 Please copy to .env and configure with your actual values" -ForegroundColor Yellow
}

# Main execution
function Main {
    if (-not (Test-Administrator)) {
        Write-Host "⚠️  This script requires administrator privileges for some installations." -ForegroundColor Yellow
        Write-Host "   Please run PowerShell as Administrator for full functionality." -ForegroundColor Yellow
    }
    
    Install-Chocolatey
    Install-Python
    Install-NodeJS
    Install-Docker
    Install-Git
    Install-GCloudCLI
    Install-Terraform
    Install-VSCode
    
    # Install Python packages if Python is available
    try {
        python --version | Out-Null
        Install-PythonPackages
    } catch {
        Write-Host "⚠️  Skipping Python packages - Python not found in PATH" -ForegroundColor Yellow
    }
    
    Create-EnvironmentTemplate
    
    Write-Host ""
    Write-Host "🎉 PREREQUISITES SETUP COMPLETE!" -ForegroundColor Green
    Write-Host "=================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Copy .env.template to .env and configure your API keys" -ForegroundColor White
    Write-Host "2. Start Docker Desktop" -ForegroundColor White
    Write-Host "3. Run deploy-full-system.ps1 to deploy the system" -ForegroundColor White
    Write-Host "4. If Docker was just installed, restart your computer first" -ForegroundColor White
    Write-Host ""
    Write-Host "🔗 Important links:" -ForegroundColor Cyan
    Write-Host "   • Alchemy (RPC): https://alchemy.com" -ForegroundColor White
    Write-Host "   • Google AI Studio: https://makersuite.google.com/app/apikey" -ForegroundColor White
    Write-Host "   • OpenAI API: https://platform.openai.com/account/api-keys" -ForegroundColor White
    Write-Host "   • GCP Console: https://console.cloud.google.com" -ForegroundColor White
}

# Execute main function
Main
