# Flash Loan Arbitrage System - Windows Startup Script
# This script will start all necessary services for the dashboard

Write-Host "🚀 Starting Flash Loan Arbitrage System..." -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# Check for API key configuration
Write-Host "🔍 Checking API key configuration..." -ForegroundColor Blue
if (Test-Path "artemis_core\.env") {
    $envContent = Get-Content "artemis_core\.env" -Raw
    if ($envContent -match "OPENAI_API_KEY=your_openai_api_key_here") {
        Write-Host "⚠️  OpenAI API Key not configured!" -ForegroundColor Yellow
        Write-Host "   Please edit artemis_core\.env and add your OpenAI API key" -ForegroundColor Yellow
        Write-Host "   See API_KEYS_SETUP_GUIDE.md for instructions" -ForegroundColor Blue
        $continue = Read-Host "Continue anyway? (y/N)"
        if ($continue -ne "y" -and $continue -ne "Y") {
            exit 1
        }
    } else {
        Write-Host "✅ API keys configured" -ForegroundColor Green
    }
} else {
    Write-Host "❌ .env file not found in artemis_core/" -ForegroundColor Red
    Write-Host "   Run quick-setup.ps1 first" -ForegroundColor Yellow
    exit 1
}

# Function to check if a command exists
function Test-CommandExists {
    param($Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# Function to check if port is in use
function Test-PortInUse {
    param($Port)
    $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    return $connections.Count -gt 0
}

# Function to kill process on port
function Stop-ProcessOnPort {
    param($Port)
    if (Test-PortInUse $Port) {
        Write-Host "🔄 Stopping process on port $Port" -ForegroundColor Yellow
        $process = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess
        if ($process) {
            Stop-Process -Id $process -Force -ErrorAction SilentlyContinue
        }
    }
}

Write-Host "🔍 Checking dependencies..." -ForegroundColor Blue

# Check Node.js
if (-not (Test-CommandExists "node")) {
    Write-Host "❌ Node.js is not installed. Please install Node.js 16+ first." -ForegroundColor Red
    exit 1
}

# Check npm
if (-not (Test-CommandExists "npm")) {
    Write-Host "❌ npm is not installed. Please install npm first." -ForegroundColor Red
    exit 1
}

# Check Python
if (-not (Test-CommandExists "python")) {
    Write-Host "❌ Python is not installed. Please install Python 3.8+ first." -ForegroundColor Red
    exit 1
}

Write-Host "✅ All dependencies found" -ForegroundColor Green

# Kill existing processes
Write-Host "🧹 Cleaning up existing processes..." -ForegroundColor Blue
Stop-ProcessOnPort 3000  # Frontend
Stop-ProcessOnPort 8080  # Backend
Stop-ProcessOnPort 5000  # Security Dashboard
Stop-ProcessOnPort 8501  # Streamlit

# Install frontend dependencies
Write-Host "📦 Installing frontend dependencies..." -ForegroundColor Blue
if (-not (Test-Path "node_modules")) {
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install frontend dependencies" -ForegroundColor Red
        exit 1
    }
}

# Install backend dependencies
Write-Host "📦 Installing backend dependencies..." -ForegroundColor Blue
Push-Location backend
if (-not (Test-Path "node_modules")) {
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install backend dependencies" -ForegroundColor Red
        Pop-Location
        exit 1
    }
}
Pop-Location

# Install server dependencies
Write-Host "📦 Installing server dependencies..." -ForegroundColor Blue
Push-Location server
if (-not (Test-Path "node_modules")) {
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install server dependencies" -ForegroundColor Red
        Pop-Location
        exit 1
    }
}
Pop-Location

# Install Python dependencies
Write-Host "📦 Installing Python dependencies..." -ForegroundColor Blue
if (Test-Path "requirements.txt") {
    python -m pip install -r requirements.txt --quiet
}

Write-Host "✅ All dependencies installed" -ForegroundColor Green

# Start services
Write-Host "🚀 Starting services..." -ForegroundColor Blue

# Start backend API
Write-Host "⚡ Starting Backend API (Port 8080)..." -ForegroundColor Yellow
Push-Location backend
$backendJob = Start-Job -ScriptBlock { npm start }
Pop-Location

# Wait a moment for backend to start
Start-Sleep 3

# Start API proxy server
Write-Host "⚡ Starting API Proxy Server (Port 3001)..." -ForegroundColor Yellow
Push-Location server
$env:PORT = "3001"
$serverJob = Start-Job -ScriptBlock { npm start }
Pop-Location

# Wait a moment for server to start
Start-Sleep 2

# Start Streamlit dashboard
Write-Host "⚡ Starting Streamlit Dashboard (Port 8501)..." -ForegroundColor Yellow
if (Test-Path "streamlit_dashboard.py") {
    $streamlitJob = Start-Job -ScriptBlock { 
        python -m streamlit run streamlit_dashboard.py --server.port 8501 --server.headless true 
    }
}

# Start frontend
Write-Host "⚡ Starting Frontend (Port 3000)..." -ForegroundColor Yellow
$frontendJob = Start-Job -ScriptBlock { npm run dev }

# Wait for services to start
Write-Host "⏳ Waiting for services to initialize..." -ForegroundColor Blue
Start-Sleep 5

# Check if services are running
Write-Host "🔍 Checking service status..." -ForegroundColor Blue

if (Test-PortInUse 3000) {
    Write-Host "✅ Frontend running on http://localhost:3000" -ForegroundColor Green
} else {
    Write-Host "❌ Frontend failed to start" -ForegroundColor Red
}

if (Test-PortInUse 8080) {
    Write-Host "✅ Backend API running on http://localhost:8080" -ForegroundColor Green
} else {
    Write-Host "❌ Backend API failed to start" -ForegroundColor Red
}

if (Test-PortInUse 3001) {
    Write-Host "✅ API Proxy running on http://localhost:3001" -ForegroundColor Green
} else {
    Write-Host "❌ API Proxy failed to start" -ForegroundColor Red
}

if (Test-PortInUse 8501) {
    Write-Host "✅ Streamlit Dashboard running on http://localhost:8501" -ForegroundColor Green
} else {
    Write-Host "⚠️ Streamlit Dashboard not started (optional)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 Flash Loan Arbitrage System is running!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "📊 Main Dashboard:    http://localhost:3000" -ForegroundColor Blue
Write-Host "🔧 API Backend:       http://localhost:8080" -ForegroundColor Blue  
Write-Host "🛡️ API Proxy:         http://localhost:3001" -ForegroundColor Blue
Write-Host "📈 Streamlit:         http://localhost:8501" -ForegroundColor Blue
Write-Host ""
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow

# Function to cleanup on exit
function Stop-AllServices {
    Write-Host "`n🛑 Shutting down services..." -ForegroundColor Yellow
    
    if ($frontendJob) { Stop-Job $frontendJob -ErrorAction SilentlyContinue; Remove-Job $frontendJob -ErrorAction SilentlyContinue }
    if ($backendJob) { Stop-Job $backendJob -ErrorAction SilentlyContinue; Remove-Job $backendJob -ErrorAction SilentlyContinue }
    if ($serverJob) { Stop-Job $serverJob -ErrorAction SilentlyContinue; Remove-Job $serverJob -ErrorAction SilentlyContinue }
    if ($streamlitJob) { Stop-Job $streamlitJob -ErrorAction SilentlyContinue; Remove-Job $streamlitJob -ErrorAction SilentlyContinue }
    
    Stop-ProcessOnPort 3000
    Stop-ProcessOnPort 8080  
    Stop-ProcessOnPort 3001
    Stop-ProcessOnPort 8501
    
    Write-Host "✅ All services stopped" -ForegroundColor Green
}

# Register cleanup function
Register-EngineEvent PowerShell.Exiting -Action { Stop-AllServices }

try {
    # Keep script running
    Write-Host "🔄 System running... Press Ctrl+C to stop" -ForegroundColor Cyan
    while ($true) {
        Start-Sleep 1
    }
}
finally {
    Stop-AllServices
}
