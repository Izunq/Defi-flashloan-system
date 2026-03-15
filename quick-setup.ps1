# Quick Setup Script for Artemis AI Core
# Run this script to quickly set up your development environment

Write-Host "🚀 Artemis AI Core - Quick Setup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Check if .env file exists
$envFile = "artemis_core\.env"
if (Test-Path $envFile) {
    Write-Host "✅ .env file already exists" -ForegroundColor Green
} else {
    Write-Host "❌ .env file not found. Please run from project root directory." -ForegroundColor Red
    exit 1
}

# Check for OpenAI API Key
$envContent = Get-Content $envFile -Raw
if ($envContent -match "OPENAI_API_KEY=your_openai_api_key_here") {
    Write-Host "⚠️  OpenAI API Key not configured!" -ForegroundColor Yellow
    Write-Host "   Please edit artemis_core\.env and add your OpenAI API key" -ForegroundColor Yellow
    Write-Host "   Get your key from: https://platform.openai.com/api-keys" -ForegroundColor Blue
    Write-Host ""
} else {
    Write-Host "✅ OpenAI API Key configured" -ForegroundColor Green
}

# Check Python installation
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Check Node.js installation
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✅ Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js not found. Please install Node.js 16+" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🔧 Setup Commands:" -ForegroundColor Cyan
Write-Host "==================" -ForegroundColor Cyan

Write-Host "1. Install Python dependencies:" -ForegroundColor White
Write-Host "   cd artemis_core && pip install -r requirements.txt" -ForegroundColor Gray

Write-Host ""
Write-Host "2. Install Node.js dependencies:" -ForegroundColor White
Write-Host "   npm install" -ForegroundColor Gray

Write-Host ""
Write-Host "3. Start Artemis AI Core (Backend):" -ForegroundColor White
Write-Host "   cd artemis_core && python artemis_ai_core.py" -ForegroundColor Gray

Write-Host ""
Write-Host "4. Start Frontend (in new terminal):" -ForegroundColor White
Write-Host "   npm run dev" -ForegroundColor Gray

Write-Host ""
Write-Host "5. Open browser to: http://localhost:5173" -ForegroundColor White

Write-Host ""
$install = Read-Host "Would you like to install dependencies now? (y/N)"

if ($install -eq "y" -or $install -eq "Y") {
    Write-Host ""
    Write-Host "📦 Installing Python dependencies..." -ForegroundColor Cyan
    Set-Location "artemis_core"
    try {
        pip install -r requirements.txt
        Write-Host "✅ Python dependencies installed" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to install Python dependencies" -ForegroundColor Red
    }
    Set-Location ".."

    Write-Host ""
    Write-Host "📦 Installing Node.js dependencies..." -ForegroundColor Cyan
    try {
        npm install
        Write-Host "✅ Node.js dependencies installed" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to install Node.js dependencies" -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "🎉 Setup complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Configure your OpenAI API key in artemis_core\.env" -ForegroundColor White
    Write-Host "2. Run: cd artemis_core && python artemis_ai_core.py" -ForegroundColor White
    Write-Host "3. In new terminal, run: npm run dev" -ForegroundColor White
    Write-Host "4. Open: http://localhost:5173" -ForegroundColor White
}

Write-Host ""
Write-Host "📋 For detailed setup instructions, see:" -ForegroundColor Blue
Write-Host "   - API_KEYS_SETUP_GUIDE.md" -ForegroundColor Gray
Write-Host "   - ARTEMIS_SETUP_GUIDE.md" -ForegroundColor Gray
