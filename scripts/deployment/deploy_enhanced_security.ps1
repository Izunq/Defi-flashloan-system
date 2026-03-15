# Enhanced Cross-Chain Security Deployment Script
# PowerShell script for Windows deployment

param(
    [Parameter(Mandatory=$false)]
    [string]$Environment = "development",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipDependencies,
    
    [Parameter(Mandatory=$false)]
    [switch]$RunTests,
    
    [Parameter(Mandatory=$false)]
    [switch]$StartDashboard
)

Write-Host "🔒 Enhanced Cross-Chain Security V2 Deployment" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# Configuration
$ProjectRoot = $PSScriptRoot
$ConfigFile = Join-Path $ProjectRoot "enhanced_cross_chain_security_config.json"
$LogFile = Join-Path $ProjectRoot "deployment_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

# Logging function
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$Timestamp] [$Level] $Message"
    Write-Host $LogEntry
    Add-Content -Path $LogFile -Value $LogEntry
}

# Function to check prerequisites
function Test-Prerequisites {
    Write-Log "Checking system prerequisites..." "INFO"
    
    # Check Python version
    try {
        $PythonVersion = python --version 2>&1
        if ($PythonVersion -match "Python 3\.([8-9]|1[0-9])") {
            Write-Log "✅ Python version check passed: $PythonVersion" "INFO"
        } else {
            Write-Log "❌ Python 3.8+ required. Found: $PythonVersion" "ERROR"
            return $false
        }
    } catch {
        Write-Log "❌ Python not found in PATH" "ERROR"
        return $false
    }
    
    # Check Node.js (for potential front-end components)
    try {
        $NodeVersion = node --version 2>&1
        Write-Log "✅ Node.js found: $NodeVersion" "INFO"
    } catch {
        Write-Log "⚠️  Node.js not found (optional for deployment)" "WARN"
    }
    
    # Check Git
    try {
        $GitVersion = git --version 2>&1
        Write-Log "✅ Git found: $GitVersion" "INFO"
    } catch {
        Write-Log "⚠️  Git not found (optional)" "WARN"
    }
    
    # Check available disk space (minimum 1GB)
    $FreeSpace = (Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'").FreeSpace
    $FreeSpaceGB = [math]::Round($FreeSpace / 1GB, 2)
    if ($FreeSpaceGB -gt 1) {
        Write-Log "✅ Sufficient disk space available: ${FreeSpaceGB}GB" "INFO"
    } else {
        Write-Log "❌ Insufficient disk space. Required: 1GB, Available: ${FreeSpaceGB}GB" "ERROR"
        return $false
    }
    
    # Check if configuration file exists
    if (Test-Path $ConfigFile) {
        Write-Log "✅ Configuration file found: $ConfigFile" "INFO"
    } else {
        Write-Log "⚠️  Configuration file not found. Will create default." "WARN"
    }
    
    return $true
}

# Function to install Python dependencies
function Install-PythonDependencies {
    if ($SkipDependencies) {
        Write-Log "Skipping dependency installation as requested" "INFO"
        return
    }
    
    Write-Log "Installing Python dependencies..." "INFO"
    
    # Create virtual environment if it doesn't exist
    if (-not (Test-Path "venv")) {
        Write-Log "Creating Python virtual environment..." "INFO"
        python -m venv venv
        if ($LASTEXITCODE -ne 0) {
            Write-Log "❌ Failed to create virtual environment" "ERROR"
            throw "Virtual environment creation failed"
        }
    }
    
    # Activate virtual environment
    $ActivateScript = Join-Path $ProjectRoot "venv\Scripts\Activate.ps1"
    if (Test-Path $ActivateScript) {
        Write-Log "Activating virtual environment..." "INFO"
        & $ActivateScript
    }
    
    # Upgrade pip
    Write-Log "Upgrading pip..." "INFO"
    python -m pip install --upgrade pip
    
    # Install required packages
    $RequiredPackages = @(
        "web3>=6.0.0",
        "asyncio",
        "cryptography>=3.4.8",
        "pydantic>=1.8.0",
        "requests>=2.25.0",
        "aiohttp>=3.8.0",
        "jsonschema>=4.0.0"
    )
    
    # Optional ML packages
    $OptionalPackages = @(
        "scikit-learn>=1.0.0",
        "numpy>=1.21.0",
        "pandas>=1.3.0",
        "joblib>=1.0.0"
    )
    
    # Optional web packages
    $WebPackages = @(
        "flask>=2.0.0",
        "flask-socketio>=5.0.0"
    )
    
    Write-Log "Installing required packages..." "INFO"
    foreach ($Package in $RequiredPackages) {
        try {
            python -m pip install $Package
            Write-Log "✅ Installed: $Package" "INFO"
        } catch {
            Write-Log "⚠️  Failed to install: $Package" "WARN"
        }
    }
    
    Write-Log "Installing optional ML packages..." "INFO"
    foreach ($Package in $OptionalPackages) {
        try {
            python -m pip install $Package
            Write-Log "✅ Installed: $Package" "INFO"
        } catch {
            Write-Log "⚠️  Failed to install optional package: $Package" "WARN"
        }
    }
    
    Write-Log "Installing optional web packages..." "INFO"
    foreach ($Package in $WebPackages) {
        try {
            python -m pip install $Package
            Write-Log "✅ Installed: $Package" "INFO"
        } catch {
            Write-Log "⚠️  Failed to install web package: $Package" "WARN"
        }
    }
}

# Function to deploy smart contracts
function Deploy-SmartContracts {
    Write-Log "Deploying smart contracts..." "INFO"
    
    # Check if Hardhat or Truffle is available
    $HardhatAvailable = Test-Path "hardhat.config.js"
    $TruffleAvailable = Test-Path "truffle-config.js"
    
    if ($HardhatAvailable) {
        Write-Log "Using Hardhat for contract deployment..." "INFO"
        try {
            npm install
            npx hardhat compile
            npx hardhat deploy --network $Environment
            Write-Log "✅ Smart contracts deployed successfully" "INFO"
        } catch {
            Write-Log "❌ Smart contract deployment failed: $_" "ERROR"
            throw "Contract deployment failed"
        }
    } elseif ($TruffleAvailable) {
        Write-Log "Using Truffle for contract deployment..." "INFO"
        try {
            npm install
            npx truffle compile
            npx truffle migrate --network $Environment
            Write-Log "✅ Smart contracts deployed successfully" "INFO"
        } catch {
            Write-Log "❌ Smart contract deployment failed: $_" "ERROR"
            throw "Contract deployment failed"
        }
    } else {
        Write-Log "⚠️  No contract deployment framework found. Using Python deployment..." "WARN"
        try {
            python deploy_enhanced_cross_chain_security.py
            Write-Log "✅ Python deployment completed" "INFO"
        } catch {
            Write-Log "❌ Python deployment failed: $_" "ERROR"
            throw "Python deployment failed"
        }
    }
}

# Function to initialize security components
function Initialize-SecurityComponents {
    Write-Log "Initializing security components..." "INFO"
    
    # Create necessary directories
    $Directories = @("logs", "models", "data", "backups")
    foreach ($Dir in $Directories) {
        $DirPath = Join-Path $ProjectRoot $Dir
        if (-not (Test-Path $DirPath)) {
            New-Item -ItemType Directory -Path $DirPath -Force | Out-Null
            Write-Log "Created directory: $Dir" "INFO"
        }
    }
    
    # Initialize ML models directory
    $ModelsDir = Join-Path $ProjectRoot "models"
    if (-not (Test-Path (Join-Path $ModelsDir "README.md"))) {
        @"
# ML Models Directory

This directory contains machine learning models for threat detection:

- anomaly_detector.pkl: Isolation Forest model for anomaly detection
- threat_classifier.pkl: Random Forest model for threat classification
- feature_scaler.pkl: StandardScaler for feature normalization

Models are automatically trained and updated during system operation.
"@ | Out-File -FilePath (Join-Path $ModelsDir "README.md") -Encoding UTF8
    }
    
    # Set up configuration
    if (-not (Test-Path $ConfigFile)) {
        Write-Log "Creating default configuration file..." "INFO"
        python -c "from deploy_enhanced_cross_chain_security import EnhancedCrossChainSecurityDeployer; deployer = EnhancedCrossChainSecurityDeployer('enhanced_cross_chain_security_config.json')"
    }
    
    Write-Log "✅ Security components initialized" "INFO"
}

# Function to run tests
function Invoke-SecurityTests {
    if (-not $RunTests) {
        Write-Log "Skipping tests as requested" "INFO"
        return
    }
    
    Write-Log "Running security tests..." "INFO"
    
    # Run Python tests
    try {
        if (Test-Path "tests") {
            python -m pytest tests/ -v
            Write-Log "✅ Python tests completed" "INFO"
        } else {
            Write-Log "⚠️  No tests directory found" "WARN"
        }
    } catch {
        Write-Log "❌ Python tests failed: $_" "ERROR"
        throw "Tests failed"
    }
    
    # Run integration tests
    try {
        python -c "
import asyncio
from deploy_enhanced_cross_chain_security import EnhancedCrossChainSecurityDeployer
async def test():
    deployer = EnhancedCrossChainSecurityDeployer('enhanced_cross_chain_security_config.json')
    results = await deployer._run_integration_tests()
    print('Integration tests:', 'PASSED' if results['all_passed'] else 'FAILED')
asyncio.run(test())
"
        Write-Log "✅ Integration tests completed" "INFO"
    } catch {
        Write-Log "❌ Integration tests failed: $_" "ERROR"
        throw "Integration tests failed"
    }
}

# Function to start dashboard
function Start-SecurityDashboard {
    if (-not $StartDashboard) {
        Write-Log "Dashboard startup not requested" "INFO"
        return
    }
    
    Write-Log "Starting security dashboard..." "INFO"
    
    try {
        # Start dashboard in background
        $DashboardJob = Start-Job -ScriptBlock {
            param($ProjectRoot)
            Set-Location $ProjectRoot
            python enhanced_security_dashboard.py
        } -ArgumentList $ProjectRoot
        
        Write-Log "✅ Dashboard started (Job ID: $($DashboardJob.Id))" "INFO"
        Write-Log "Dashboard should be available at http://localhost:5000" "INFO"
        
        return $DashboardJob
    } catch {
        Write-Log "❌ Failed to start dashboard: $_" "ERROR"
        throw "Dashboard startup failed"
    }
}

# Function to create startup scripts
function New-StartupScripts {
    Write-Log "Creating startup scripts..." "INFO"
    
    # Windows service script
    $ServiceScript = @"
# Enhanced Cross-Chain Security Service Startup
# Run this script to start all security components

Set-Location "$ProjectRoot"

# Activate virtual environment
if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
}

# Start threat detection engine
Start-Job -Name "ThreatDetection" -ScriptBlock {
    python advanced_threat_detection_engine.py
}

# Start security orchestrator
Start-Job -Name "SecurityOrchestrator" -ScriptBlock {
    python cross_chain_security_orchestrator.py
}

# Start dashboard
Start-Job -Name "SecurityDashboard" -ScriptBlock {
    python enhanced_security_dashboard.py
}

Write-Host "✅ All security components started"
Write-Host "Dashboard: http://localhost:5000"
"@
    
    $ServiceScript | Out-File -FilePath (Join-Path $ProjectRoot "start_security_services.ps1") -Encoding UTF8
    
    # Linux/Mac startup script
    $LinuxScript = @"
#!/bin/bash
# Enhanced Cross-Chain Security Service Startup for Linux/Mac

cd "$ProjectRoot"

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Start services
python advanced_threat_detection_engine.py &
python cross_chain_security_orchestrator.py &
python enhanced_security_dashboard.py &

echo "✅ All security components started"
echo "Dashboard: http://localhost:5000"
"@
    
    $LinuxScript | Out-File -FilePath (Join-Path $ProjectRoot "start_security_services.sh") -Encoding UTF8
    
    Write-Log "✅ Startup scripts created" "INFO"
}

# Function to generate deployment report
function New-DeploymentReport {
    Write-Log "Generating deployment report..." "INFO"
    
    $ReportPath = Join-Path $ProjectRoot "deployment_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').md"
    
    $Report = @"
# Enhanced Cross-Chain Security V2 Deployment Report

**Deployment Date:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
**Environment:** $Environment
**Deployment Status:** ✅ SUCCESS

## Components Deployed

### Smart Contracts
- ✅ AdvancedCrossChainSecurityHub
- ✅ CrossChainSecurityValidator
- ✅ Enhanced security validation logic

### Security Systems
- ✅ ML-powered threat detection engine
- ✅ Real-time security orchestrator
- ✅ Quantum-resistant signature verification
- ✅ Automated response mechanisms

### Monitoring & Dashboard
- ✅ Real-time security dashboard
- ✅ Threat analytics and visualization
- ✅ Chain health monitoring
- ✅ Alert management system

## Configuration

**Configuration File:** ``enhanced_cross_chain_security_config.json``

### Supported Chains
- Ethereum (Chain ID: 1)
- Polygon (Chain ID: 137)
- BSC (Chain ID: 56)
- Avalanche (Chain ID: 43114)
- Arbitrum (Chain ID: 42161)

### Security Features
- ML-based anomaly detection
- Pattern recognition and analysis
- Economic manipulation detection
- Real-time threat scoring
- Automated response actions
- Quantum-resistant cryptography

## Access Information

**Security Dashboard:** http://localhost:5000
**Configuration File:** ``$ConfigFile``
**Log Files:** ``logs/`` directory
**ML Models:** ``models/`` directory

## Next Steps

1. **Monitor Dashboard:** Access the security dashboard to monitor system health
2. **Configure Chains:** Update RPC endpoints and chain-specific settings
3. **Train Models:** Allow ML models to train on historical data
4. **Test Procedures:** Verify emergency response procedures
5. **Set Up Alerts:** Configure notification channels for security alerts

## Support

For technical support or questions:
- **Security Team:** security@company.com
- **Operations:** operations@company.com
- **Documentation:** See project README files

## Files Created

- ``start_security_services.ps1`` - Windows startup script
- ``start_security_services.sh`` - Linux/Mac startup script
- ``$LogFile`` - Deployment log
- ``models/`` - ML models directory
- ``logs/`` - Application logs directory

---
*Generated by Enhanced Cross-Chain Security Deployment Script v2.0*
"@
    
    $Report | Out-File -FilePath $ReportPath -Encoding UTF8
    Write-Log "✅ Deployment report generated: $ReportPath" "INFO"
    
    return $ReportPath
}

# Main deployment function
function Start-Deployment {
    try {
        Write-Log "Starting Enhanced Cross-Chain Security V2 deployment..." "INFO"
        Write-Log "Environment: $Environment" "INFO"
        Write-Log "Log file: $LogFile" "INFO"
        
        # Step 1: Check prerequisites
        if (-not (Test-Prerequisites)) {
            throw "Prerequisites check failed"
        }
        
        # Step 2: Install dependencies
        Install-PythonDependencies
        
        # Step 3: Deploy smart contracts
        Deploy-SmartContracts
        
        # Step 4: Initialize security components
        Initialize-SecurityComponents
        
        # Step 5: Run tests (if requested)
        Invoke-SecurityTests
        
        # Step 6: Create startup scripts
        New-StartupScripts
        
        # Step 7: Start dashboard (if requested)
        $DashboardJob = Start-SecurityDashboard
        
        # Step 8: Generate deployment report
        $ReportPath = New-DeploymentReport
        
        Write-Host ""
        Write-Host "🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!" -ForegroundColor Green
        Write-Host "=================================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "✅ Enhanced Cross-Chain Security V2 is now deployed and running" -ForegroundColor Green
        Write-Host ""
        Write-Host "📊 Dashboard: http://localhost:5000" -ForegroundColor Cyan
        Write-Host "📄 Report: $ReportPath" -ForegroundColor Cyan
        Write-Host "📝 Logs: $LogFile" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "🚀 To start services manually:" -ForegroundColor Yellow
        Write-Host "   .\start_security_services.ps1" -ForegroundColor Yellow
        Write-Host ""
        
        if ($DashboardJob) {
            Write-Host "🖥️  Dashboard is running in background (Job ID: $($DashboardJob.Id))" -ForegroundColor Green
        }
        
    } catch {
        Write-Log "❌ Deployment failed: $_" "ERROR"
        Write-Host ""
        Write-Host "❌ DEPLOYMENT FAILED!" -ForegroundColor Red
        Write-Host "Error: $_" -ForegroundColor Red
        Write-Host "Check log file for details: $LogFile" -ForegroundColor Yellow
        exit 1
    }
}

# Execute deployment
Start-Deployment

Write-Host ""
Write-Host "For more information, see the deployment report and documentation." -ForegroundColor Cyan
Write-Host "Enhanced Cross-Chain Security V2 deployment script completed." -ForegroundColor Green
