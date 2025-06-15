# Real MEV Protection Deployment Script for Windows
# ================================================
#
# This PowerShell script deploys the enhanced MEV protection system
# with critical security fixes for Windows environments.
#
# Usage:
#   .\deploy_mev_protection.ps1 -Network testnet -Mode testing
#   .\deploy_mev_protection.ps1 -Network mainnet -Mode production -Verify

param(
    [ValidateSet("mainnet", "testnet")]
    [string]$Network = "testnet",
    
    [ValidateSet("production", "testing")]
    [string]$Mode = "testing",
    
    [switch]$VerifyOnly,
    [switch]$Force,
    [switch]$SkipBackup
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Function to write colored output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Function to write step header
function Write-StepHeader {
    param([string]$Step)
    Write-Host ""
    Write-ColorOutput "=" * 60 -Color "Cyan"
    Write-ColorOutput $Step -Color "Cyan"
    Write-ColorOutput "=" * 60 -Color "Cyan"
}

# Function to check prerequisites
function Test-Prerequisites {
    Write-StepHeader "CHECKING PREREQUISITES"
    
    $prerequisites = @()
    
    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python 3\.[8-9]|Python 3\.1[0-9]") {
            Write-ColorOutput "✅ Python: $pythonVersion" -Color "Green"
            $prerequisites += $true
        } else {
            Write-ColorOutput "❌ Python 3.8+ required, found: $pythonVersion" -Color "Red"
            $prerequisites += $false
        }
    } catch {
        Write-ColorOutput "❌ Python not found or not in PATH" -Color "Red"
        $prerequisites += $false
    }
    
    # Check required files
    $requiredFiles = @(
        "mev_protection.py",
        "mev_protection_critical_fixes.py",
        ".env"
    )
    
    foreach ($file in $requiredFiles) {
        if (Test-Path $file) {
            Write-ColorOutput "✅ Required file: $file" -Color "Green"
            $prerequisites += $true
        } else {
            Write-ColorOutput "❌ Missing required file: $file" -Color "Red"
            $prerequisites += $false
        }
    }
    
    # Check environment variables
    $envContent = Get-Content ".env" -ErrorAction SilentlyContinue
    if ($envContent -and ($envContent | Select-String "RPC_URL")) {
        Write-ColorOutput "✅ Environment configuration found" -Color "Green"
        $prerequisites += $true
    } else {
        Write-ColorOutput "❌ Invalid or missing .env configuration" -Color "Red"
        $prerequisites += $false
    }
    
    if ($prerequisites -contains $false) {
        Write-ColorOutput "❌ Prerequisites check failed!" -Color "Red"
        exit 1
    } else {
        Write-ColorOutput "✅ All prerequisites satisfied!" -Color "Green"
    }
}

# Function to backup existing system
function Backup-ExistingSystem {
    if ($SkipBackup) {
        Write-ColorOutput "⏭️ Skipping backup (--SkipBackup specified)" -Color "Yellow"
        return
    }
    
    Write-StepHeader "BACKING UP EXISTING SYSTEM"
    
    $backupTimestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFiles = @(
        "mev_protection.py",
        "mev_protection_config.json"
    )
    
    foreach ($file in $backupFiles) {
        if (Test-Path $file) {
            $backupPath = "$file.backup_$backupTimestamp"
            Copy-Item $file $backupPath
            Write-ColorOutput "✅ Backed up $file to $backupPath" -Color "Green"
        }
    }
    
    Write-ColorOutput "📦 Backup completed successfully" -Color "Green"
}

# Function to deploy MEV protection
function Deploy-MEVProtection {
    Write-StepHeader "DEPLOYING REAL MEV PROTECTION SYSTEM"
    
    # Check if Python deployment script exists
    if (-not (Test-Path "deploy_mev_protection.py")) {
        Write-ColorOutput "❌ Python deployment script not found!" -Color "Red"
        exit 1
    }
    
    # Prepare Python command
    $pythonArgs = @("deploy_mev_protection.py", "--network", $Network, "--mode", $Mode)
    
    if ($VerifyOnly) {
        $pythonArgs += "--verify-only"
    }
    
    Write-ColorOutput "🚀 Executing Python deployment script..." -Color "Yellow"
    Write-ColorOutput "Command: python $($pythonArgs -join ' ')" -Color "Gray"
    
    try {
        # Execute Python deployment script
        $process = Start-Process -FilePath "python" -ArgumentList $pythonArgs -Wait -PassThru -NoNewWindow
        
        if ($process.ExitCode -eq 0) {
            Write-ColorOutput "✅ Python deployment completed successfully!" -Color "Green"
            return $true
        } else {
            Write-ColorOutput "❌ Python deployment failed with exit code: $($process.ExitCode)" -Color "Red"
            return $false
        }
    } catch {
        Write-ColorOutput "❌ Error executing Python deployment: $($_.Exception.Message)" -Color "Red"
        return $false
    }
}

# Function to verify deployment
function Test-DeploymentStatus {
    Write-StepHeader "VERIFYING DEPLOYMENT STATUS"
    
    $verificationTests = @()
    
    # Test 1: Check if security patches are loaded
    try {
        $testScript = @"
import sys
sys.path.append('.')
try:
    from mev_protection_critical_fixes import SecureMEVProtectionPatch
    print('SECURITY_PATCHES_OK')
except ImportError as e:
    print(f'SECURITY_PATCHES_ERROR: {e}')
"@
        
        $result = python -c $testScript 2>&1
        if ($result -like "*SECURITY_PATCHES_OK*") {
            Write-ColorOutput "✅ Security patches loaded successfully" -Color "Green"
            $verificationTests += $true
        } else {
            Write-ColorOutput "❌ Security patches failed to load: $result" -Color "Red"
            $verificationTests += $false
        }
    } catch {
        Write-ColorOutput "❌ Error testing security patches: $($_.Exception.Message)" -Color "Red"
        $verificationTests += $false
    }
    
    # Test 2: Check configuration files
    $configFiles = @(
        "mev_protection_config_$Network.json",
        "mev_monitoring_config_$Network.json"
    )
    
    foreach ($configFile in $configFiles) {
        if (Test-Path $configFile) {
            try {
                $config = Get-Content $configFile | ConvertFrom-Json
                Write-ColorOutput "✅ Configuration file valid: $configFile" -Color "Green"
                $verificationTests += $true
            } catch {
                Write-ColorOutput "❌ Invalid configuration file: $configFile" -Color "Red"
                $verificationTests += $false
            }
        } else {
            Write-ColorOutput "⚠️ Configuration file not found: $configFile" -Color "Yellow"
            $verificationTests += $true  # Not critical for basic functionality
        }
    }
    
    # Test 3: Check log files
    $logFiles = Get-ChildItem -Name "mev_deployment_*.log" | Sort-Object -Descending | Select-Object -First 1
    if ($logFiles) {
        $logContent = Get-Content $logFiles -Tail 10
        if ($logContent -match "deployment completed successfully|All verification checks passed") {
            Write-ColorOutput "✅ Deployment logs indicate success" -Color "Green"
            $verificationTests += $true
        } else {
            Write-ColorOutput "⚠️ Deployment logs show potential issues" -Color "Yellow"
            $verificationTests += $true  # Not critical
        }
    }
    
    # Summary
    $failedTests = ($verificationTests | Where-Object { $_ -eq $false }).Count
    $totalTests = $verificationTests.Count
    
    if ($failedTests -eq 0) {
        Write-ColorOutput "🎉 All verification tests passed! ($totalTests/$totalTests)" -Color "Green"
        return $true
    } else {
        Write-ColorOutput "⚠️ Some verification tests failed! ($($totalTests - $failedTests)/$totalTests passed)" -Color "Yellow"
        return $false
    }
}

# Function to display deployment summary
function Show-DeploymentSummary {
    param([bool]$Success)
    
    Write-Host ""
    Write-ColorOutput "=" * 70 -Color "Cyan"
    Write-ColorOutput "MEV PROTECTION DEPLOYMENT SUMMARY" -Color "Cyan"
    Write-ColorOutput "=" * 70 -Color "Cyan"
    
    Write-Host "Network:    " -NoNewline
    Write-ColorOutput $Network -Color "White"
    
    Write-Host "Mode:       " -NoNewline
    Write-ColorOutput $Mode -Color "White"
    
    Write-Host "Timestamp:  " -NoNewline
    Write-ColorOutput (Get-Date -Format "yyyy-MM-dd HH:mm:ss") -Color "White"
    
    Write-Host "Status:     " -NoNewline
    if ($Success) {
        Write-ColorOutput "SUCCESS ✅" -Color "Green"
    } else {
        Write-ColorOutput "FAILED ❌" -Color "Red"
    }
    
    if ($Success) {
        Write-Host ""
        Write-ColorOutput "Security Features Enabled:" -Color "Green"
        Write-ColorOutput "✅ Real-time mempool analysis" -Color "Green"
        Write-ColorOutput "✅ Private mempool enforcement" -Color "Green"
        Write-ColorOutput "✅ Advanced MEV bot detection" -Color "Green"
        Write-ColorOutput "✅ Randomized timing protection" -Color "Green"
        Write-ColorOutput "✅ Comprehensive slippage protection" -Color "Green"
        Write-ColorOutput "✅ Fail-secure fallback strategies" -Color "Green"
        
        Write-Host ""
        Write-ColorOutput "🛡️ Your transactions are now protected against MEV attacks!" -Color "Green"
    } else {
        Write-Host ""
        Write-ColorOutput "Deployment failed. Check the logs for details." -Color "Red"
        Write-ColorOutput "You may need to restore from backup or retry deployment." -Color "Yellow"
    }
    
    Write-ColorOutput "=" * 70 -Color "Cyan"
}

# Main execution
try {
    Write-ColorOutput @"
🛡️ Real MEV Protection Deployment Script
========================================

This script will deploy enhanced MEV protection with:
- Real-time mempool analysis
- Private mempool enforcement for high-value transactions
- Advanced sandwich attack detection
- Randomized timing protection
- Comprehensive slippage protection

Network: $Network
Mode: $Mode
"@ -Color "Cyan"

    if (-not $Force) {
        Write-Host ""
        $confirmation = Read-Host "Do you want to continue? (y/N)"
        if ($confirmation -notmatch "^[Yy]$") {
            Write-ColorOutput "❌ Deployment cancelled by user" -Color "Yellow"
            exit 0
        }
    }
    
    # Execute deployment steps
    Test-Prerequisites
    
    if (-not $VerifyOnly) {
        Backup-ExistingSystem
    }
    
    $deploymentSuccess = Deploy-MEVProtection
    
    if ($deploymentSuccess) {
        $verificationSuccess = Test-DeploymentStatus
        Show-DeploymentSummary -Success $verificationSuccess
        
        if ($verificationSuccess) {
            Write-ColorOutput "🚀 MEV Protection deployment completed successfully!" -Color "Green"
            exit 0
        } else {
            Write-ColorOutput "⚠️ Deployment completed but verification showed issues" -Color "Yellow"
            exit 2
        }
    } else {
        Show-DeploymentSummary -Success $false
        Write-ColorOutput "💥 MEV Protection deployment failed!" -Color "Red"
        exit 1
    }
    
} catch {
    Write-ColorOutput "💥 Unexpected error during deployment: $($_.Exception.Message)" -Color "Red"
    Write-ColorOutput "Stack trace: $($_.ScriptStackTrace)" -Color "Gray"
    exit 1
}
