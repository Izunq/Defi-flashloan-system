# Enhanced Cross-Chain Bridge Security Deployment Script
# =================================================
# PowerShell script for deploying enhanced cross-chain bridge security on Windows

param(
    [switch]$Test,
    [switch]$Verbose,
    [string]$ConfigPath = "enhanced_cross_chain_security_config.json"
)

Write-Host "🔒 Enhanced Cross-Chain Bridge Security Deployment" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

# Function to write colored output
function Write-Status {
    param(
        [string]$Message,
        [string]$Status = "INFO"
    )
    
    switch ($Status) {
        "SUCCESS" { Write-Host "✅ $Message" -ForegroundColor Green }
        "ERROR" { Write-Host "❌ $Message" -ForegroundColor Red }
        "WARNING" { Write-Host "⚠️ $Message" -ForegroundColor Yellow }
        "INFO" { Write-Host "ℹ️ $Message" -ForegroundColor Blue }
        default { Write-Host "$Message" }
    }
}

# Check Python installation
Write-Status "Checking Python installation..." "INFO"
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Python found: $pythonVersion" "SUCCESS"
    } else {
        Write-Status "Python not found. Please install Python 3.8+" "ERROR"
        exit 1
    }
} catch {
    Write-Status "Error checking Python: $_" "ERROR"
    exit 1
}

# Check required Python packages
Write-Status "Checking Python dependencies..." "INFO"
$requiredPackages = @(
    "asyncio",
    "aiohttp", 
    "web3",
    "eth-account",
    "cryptography"
)

foreach ($package in $requiredPackages) {
    try {
        python -c "import $package" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Status "Package ${package}: OK" "SUCCESS"
        } else {
            Write-Status "Installing $package..." "INFO"
            pip install $package
            if ($LASTEXITCODE -ne 0) {
                Write-Status "Failed to install $package" "ERROR"
                exit 1
            }
        }
    } catch {
        Write-Status "Error checking package $package" "WARNING"
    }
}

# Create deployment directory if it doesn't exist
$deploymentDir = "deployment_logs"
if (!(Test-Path $deploymentDir)) {
    New-Item -ItemType Directory -Path $deploymentDir | Out-Null
    Write-Status "Created deployment logs directory" "SUCCESS"
}

# Check for existing deployment files
Write-Status "Checking deployment environment..." "INFO"

$requiredFiles = @(
    "enhanced_cross_chain_security_orchestrator.py",
    "enhanced_multi_oracle_validator.py", 
    "deploy_enhanced_cross_chain_security_final.py",
    "contracts\EnhancedCrossChainBridge.sol"
)

$missingFiles = @()
foreach ($file in $requiredFiles) {
    if (!(Test-Path $file)) {
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Status "Missing required files:" "ERROR"
    foreach ($file in $missingFiles) {
        Write-Host "  - $file" -ForegroundColor Red
    }
    Write-Status "Please ensure all deployment files are present" "ERROR"
    exit 1
}

Write-Status "All required files found" "SUCCESS"

# Create configuration if it doesn't exist
if (!(Test-Path $ConfigPath)) {
    Write-Status "Creating default configuration..." "INFO"
    
    $defaultConfig = @{
        "version" = "2.0"
        "deployment_timestamp" = (Get-Date).ToString("o")
        "enhanced_security" = @{
            "multi_oracle_consensus" = $true
            "payload_validation" = $true
            "chain_state_verification" = $true
            "timeout_protection" = $true
            "byzantine_fault_tolerance" = $true
        }
        "supported_chains" = @(
            @{
                "id" = 1
                "name" = "Ethereum"
                "rpc" = ""
                "confirmation_blocks" = 12
                "average_block_time" = 13
            },
            @{
                "id" = 137
                "name" = "Polygon"
                "rpc" = ""
                "confirmation_blocks" = 256
                "average_block_time" = 2
            }
        )
        "multi_oracle" = @{
            "min_signatures" = 3
            "max_signatures" = 7
            "consensus_threshold" = 0.67
            "byzantine_tolerance" = 1
        }
    } | ConvertTo-Json -Depth 10
    
    $defaultConfig | Out-File -FilePath $ConfigPath -Encoding UTF8
    Write-Status "Default configuration created at $ConfigPath" "SUCCESS"
}

# Run deployment validation
Write-Status "Running pre-deployment validation..." "INFO"

try {
    $validationResult = python -c "
import json
import sys
import os

# Basic validation
config_path = '$ConfigPath'
if not os.path.exists(config_path):
    print('ERROR: Configuration file not found')
    sys.exit(1)

try:
    with open(config_path, 'r') as f:
        config = json.load(f)
        
    # Validate required sections
    required_sections = ['enhanced_security', 'supported_chains', 'multi_oracle']
    for section in required_sections:
        if section not in config:
            print(f'ERROR: Missing configuration section: {section}')
            sys.exit(1)
    
    # Validate chains
    chains = config.get('supported_chains', [])
    if len(chains) < 2:
        print('ERROR: At least 2 chains required for cross-chain operations')
        sys.exit(1)
        
    print('SUCCESS: Configuration validation passed')
    
except json.JSONDecodeError:
    print('ERROR: Invalid JSON in configuration file')
    sys.exit(1)
except Exception as e:
    print(f'ERROR: Validation failed: {str(e)}')
    sys.exit(1)
"

    if ($LASTEXITCODE -eq 0) {
        Write-Status "Pre-deployment validation passed" "SUCCESS"
    } else {
        Write-Status "Pre-deployment validation failed" "ERROR"
        Write-Status $validationResult "ERROR"
        exit 1
    }
} catch {
    Write-Status "Error during validation: $_" "ERROR"
    exit 1
}

# Test mode - run without full deployment
if ($Test) {
    Write-Status "Running in TEST mode - no actual deployment" "WARNING"
    
    Write-Status "Testing security orchestrator import..." "INFO"
    $testResult = python -c "
try:
    from enhanced_cross_chain_security_orchestrator import EnhancedCrossChainSecurityOrchestrator
    print('SUCCESS: Orchestrator import successful')
except ImportError as e:
    print(f'ERROR: Failed to import orchestrator: {str(e)}')
    exit(1)
except Exception as e:
    print(f'ERROR: Unexpected error: {str(e)}')
    exit(1)
"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Test completed successfully" "SUCCESS"
    } else {
        Write-Status "Test failed: $testResult" "ERROR"
    }
    
    return
}

# Show deployment plan
Write-Host "`n🚀 DEPLOYMENT PLAN" -ForegroundColor Cyan
Write-Host "==================" -ForegroundColor Cyan
Write-Host "1. Deploy Enhanced Cross-Chain Bridge Contract"
Write-Host "2. Initialize Multi-Oracle Validator Network"
Write-Host "3. Configure Security Orchestrator"
Write-Host "4. Set up Chain Integrations"
Write-Host "5. Initialize Monitoring Systems"
Write-Host "6. Run Security Tests"
Write-Host "7. Generate Deployment Report"

# Confirm deployment
$confirmation = Read-Host "`nDo you want to proceed with the deployment? (y/N)"
if ($confirmation -ne "y") {
    Write-Status "Deployment cancelled by user" "WARNING"
    exit 0
}

# Run the main deployment
Write-Status "Starting enhanced cross-chain bridge security deployment..." "INFO"

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = "$deploymentDir\deployment_$timestamp.log"

try {
    Write-Status "Executing deployment script..." "INFO"
    
    # Run the Python deployment script
    $deploymentOutput = python deploy_enhanced_cross_chain_security_final.py 2>&1
    
    # Save output to log file
    $deploymentOutput | Out-File -FilePath $logFile -Encoding UTF8
    
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Deployment completed successfully!" "SUCCESS"
        Write-Status "Deployment log saved to: $logFile" "INFO"
        
        # Show deployment summary
        Write-Host "`n📊 DEPLOYMENT SUMMARY" -ForegroundColor Green
        Write-Host "=====================" -ForegroundColor Green
        Write-Host "✅ Status: SUCCESS"
        Write-Host "📅 Timestamp: $(Get-Date)"
        Write-Host "📋 Configuration: $ConfigPath"
        Write-Host "📊 Log File: $logFile"
        
        # Check if deployment report was generated
        $reportFiles = Get-ChildItem -Path . -Filter "*deployment_report*.json" | Sort-Object LastWriteTime -Descending
        if ($reportFiles.Count -gt 0) {
            $latestReport = $reportFiles[0].Name
            Write-Host "📄 Report: $latestReport"
        }
        
        Write-Host "`n🎉 Enhanced Cross-Chain Bridge Security is now deployed!" -ForegroundColor Green
        Write-Host "`n📋 NEXT STEPS:" -ForegroundColor Yellow
        Write-Host "1. Configure RPC endpoints for supported chains"
        Write-Host "2. Set up monitoring dashboards"
        Write-Host "3. Conduct security audit"
        Write-Host "4. Begin testnet validation"
        
    } else {
        Write-Status "Deployment failed!" "ERROR"
        Write-Status "Check the log file for details: $logFile" "ERROR"
        
        # Show last few lines of output for immediate feedback
        if ($deploymentOutput) {
            Write-Host "`n🔍 DEPLOYMENT OUTPUT (last 10 lines):" -ForegroundColor Red
            ($deploymentOutput -split "`n" | Select-Object -Last 10) | ForEach-Object {
                Write-Host $_ -ForegroundColor Red
            }
        }
        
        exit 1
    }
    
} catch {
    Write-Status "Error during deployment: $_" "ERROR"
    Write-Status "Check the log file for details: $logFile" "ERROR"
    exit 1
}

# Optional: Open deployment report
if (Test-Path $latestReport) {
    $openReport = Read-Host "`nWould you like to open the deployment report? (y/N)"
    if ($openReport -eq "y") {
        try {
            Start-Process $latestReport
        } catch {
            Write-Status "Could not open report file automatically" "WARNING"
            Write-Status "You can manually open: $latestReport" "INFO"
        }
    }
}

Write-Status "Enhanced Cross-Chain Bridge Security deployment completed!" "SUCCESS"
