# Git Repository Initialization Script for Windows PowerShell
# Run this script after installing Git

Write-Host "Initializing Advanced DeFi System Repository..." -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green

# Navigate to script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Check if Git is available
try {
    $gitVersion = git --version
    Write-Host "Git found: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "Git not found in PATH. Please install Git or restart your terminal." -ForegroundColor Red
    Write-Host "Download Git from: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

# Initialize git repository
Write-Host "Initializing Git repository..." -ForegroundColor Cyan
git init

# Set up Git configuration (optional - customize with your details)
Write-Host "Setting up Git configuration..." -ForegroundColor Cyan
Write-Host "Tip: Configure your Git username and email:" -ForegroundColor Yellow
Write-Host '   git config user.name "Your Name"' -ForegroundColor DarkGray
Write-Host '   git config user.email "your.email@example.com"' -ForegroundColor DarkGray

# Add all files to staging
Write-Host "Adding files to Git staging..." -ForegroundColor Cyan
git add .

# Create initial commit
Write-Host "Creating initial commit..." -ForegroundColor Cyan
$commitMessage = "Initial commit: Advanced DeFi Flashloan and Arbitrage System

Features:
- Sentinel Agent Architecture (Oracle, MEV, Strategy monitoring)
- AI-powered trading strategies with ML models
- Cross-chain security and bridge monitoring
- MEV protection and oracle manipulation defense
- Real-time WebSocket alerts and dashboard integration
- Emergency response system with contract pause capabilities
- Comprehensive testing framework
- Production-ready deployment scripts
- Multi-chain support (Ethereum, Polygon, Arbitrum, Optimism)
- ZK proof integration and formal verification
- Enterprise-grade security and observability"

git commit -m $commitMessage

# Create development branches
Write-Host "Creating development branches..." -ForegroundColor Cyan
git branch development
git branch feature/sentinel-integration
git branch feature/ai-strategies
git branch feature/cross-chain-security

# Display repository status
Write-Host "Repository Status:" -ForegroundColor Green
Write-Host "====================" -ForegroundColor Green
git status

Write-Host ""
Write-Host "Git repository initialized successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Set up remote repository: git remote add origin YOUR-REPO-URL" -ForegroundColor White
Write-Host "2. Push to remote: git push -u origin main" -ForegroundColor White
Write-Host "3. Configure branch protection rules" -ForegroundColor White
Write-Host "4. Set up CI/CD pipelines" -ForegroundColor White
Write-Host ""
Write-Host "Available Branches:" -ForegroundColor Yellow
Write-Host "- main: Production-ready code" -ForegroundColor White
Write-Host "- development: Development integration" -ForegroundColor White
Write-Host "- feature/sentinel-integration: Sentinel system features" -ForegroundColor White
Write-Host "- feature/ai-strategies: AI trading strategies" -ForegroundColor White
Write-Host "- feature/cross-chain-security: Cross-chain security features" -ForegroundColor White
Write-Host ""
Write-Host "Security Reminder:" -ForegroundColor Red
Write-Host "- Never commit private keys or sensitive data" -ForegroundColor White
Write-Host "- Use .env files for configuration" -ForegroundColor White
Write-Host "- Review .gitignore before commits" -ForegroundColor White
Write-Host "- Enable signed commits for security" -ForegroundColor White
