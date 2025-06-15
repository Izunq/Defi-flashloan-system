# ZK Circuit Formal Verification and Deployment Pipeline
# This script runs the complete formal verification process

param(
    [switch]$DryRun = $true,
    [switch]$UseHSM = $false,
    [string]$Network = "mainnet",
    [switch]$SkipTests = $false,
    [switch]$Verbose = $false
)

# Script configuration
$ErrorActionPreference = "Stop"
$InformationPreference = if ($Verbose) { "Continue" } else { "SilentlyContinue" }

# Color output functions
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Error { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }
function Write-Warning { param($Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Info { param($Message) Write-Host "ℹ️  $Message" -ForegroundColor Cyan }
function Write-Header { param($Message) Write-Host "`n🔒 $Message" -ForegroundColor Magenta; Write-Host ("=" * 80) -ForegroundColor Gray }

# Check prerequisites
function Test-Prerequisites {
    Write-Header "CHECKING PREREQUISITES"
    
    $prerequisites = @(
        @{ Name = "Node.js"; Command = "node --version"; Required = $true },
        @{ Name = "npm"; Command = "npm --version"; Required = $true },
        @{ Name = "circom"; Command = "circom --version"; Required = $true },
        @{ Name = "snarkjs"; Command = "snarkjs --version"; Required = $false },
        @{ Name = "Z3 SMT Solver"; Command = "z3 --version"; Required = $false },
        @{ Name = "Lean 4"; Command = "lean --version"; Required = $false }
    )
    
    $allGood = $true
    
    foreach ($prereq in $prerequisites) {
        try {
            $null = Invoke-Expression $prereq.Command 2>$null
            Write-Success "$($prereq.Name) is installed"
        }
        catch {
            if ($prereq.Required) {
                Write-Error "$($prereq.Name) is required but not found"
                $allGood = $false
            }
            else {
                Write-Warning "$($prereq.Name) not found (optional)"
            }
        }
    }
    
    if (-not $allGood) {
        Write-Error "Missing required prerequisites. Please install them first."
        exit 1
    }
}

# Install dependencies
function Install-Dependencies {
    Write-Header "INSTALLING DEPENDENCIES"
    
    if (-not (Test-Path "node_modules")) {
        Write-Info "Installing Node.js dependencies..."
        npm install
        Write-Success "Dependencies installed"
    }
    else {
        Write-Info "Dependencies already installed"
    }
    
    # Check for circomlib
    if (-not (Test-Path "node_modules/circomlib")) {
        Write-Info "Installing circomlib..."
        npm install circomlib
        Write-Success "circomlib installed"
    }
}

# Run formal verification
function Start-FormalVerification {
    Write-Header "FORMAL VERIFICATION PHASE"
    
    try {
        Write-Info "Running comprehensive formal verification..."
        node prover/formal_verifier_advanced.js
        
        if ($LASTEXITCODE -ne 0) {
            throw "Formal verification failed with exit code $LASTEXITCODE"
        }
        
        Write-Success "Formal verification completed successfully"
    }
    catch {
        Write-Error "Formal verification failed: $($_.Exception.Message)"
        exit 1
    }
}

# Run property-based testing
function Start-PropertyTesting {
    if ($SkipTests) {
        Write-Warning "Skipping property-based testing (--SkipTests specified)"
        return
    }
    
    Write-Header "PROPERTY-BASED TESTING PHASE"
    
    try {
        Write-Info "Running comprehensive property testing..."
        node prover/circuit_property_tester.js
        
        if ($LASTEXITCODE -ne 0) {
            throw "Property testing failed with exit code $LASTEXITCODE"
        }
        
        Write-Success "Property testing completed successfully"
    }
    catch {
        Write-Error "Property testing failed: $($_.Exception.Message)"
        exit 1
    }
}

# Compile circuits
function Start-CircuitCompilation {
    Write-Header "CIRCUIT COMPILATION PHASE"
    
    $circuits = @(
        @{ Path = "prover/circuit_formally_verified.circom"; Name = "Formally Verified Circuit" },
        @{ Path = "ComplianceCircuits/enhanced_compliance_circuit.circom"; Name = "Enhanced Compliance Circuit" }
    )
    
    foreach ($circuit in $circuits) {
        if (Test-Path $circuit.Path) {
            Write-Info "Compiling $($circuit.Name)..."
            
            try {
                $baseName = [System.IO.Path]::GetFileNameWithoutExtension($circuit.Path)
                $outputDir = [System.IO.Path]::GetDirectoryName($circuit.Path)
                
                circom $circuit.Path --r1cs --wasm --sym --c --json --O2 --output $outputDir
                
                if ($LASTEXITCODE -ne 0) {
                    throw "Circuit compilation failed"
                }
                
                # Verify compilation artifacts
                $expectedFiles = @(
                    "$outputDir/$baseName.r1cs",
                    "$outputDir/$baseName.sym"
                )
                
                foreach ($file in $expectedFiles) {
                    if (-not (Test-Path $file)) {
                        throw "Missing compilation artifact: $file"
                    }
                }
                
                Write-Success "$($circuit.Name) compiled successfully"
            }
            catch {
                Write-Error "Failed to compile $($circuit.Name): $($_.Exception.Message)"
                exit 1
            }
        }
        else {
            Write-Warning "$($circuit.Name) not found at $($circuit.Path)"
        }
    }
}

# Run deployment verification
function Start-DeploymentVerification {
    Write-Header "DEPLOYMENT VERIFICATION PHASE"
    
    # Set environment variables for deployment configuration
    $env:DRY_RUN = if ($DryRun) { "true" } else { "false" }
    $env:USE_HSM = if ($UseHSM) { "true" } else { "false" }
    $env:NETWORK_ID = $Network
    
    try {
        Write-Info "Running deployment verification..."
        node deploy_zk_formally_verified.js
        
        if ($LASTEXITCODE -ne 0) {
            throw "Deployment verification failed with exit code $LASTEXITCODE"
        }
        
        Write-Success "Deployment verification completed successfully"
    }
    catch {
        Write-Error "Deployment verification failed: $($_.Exception.Message)"
        exit 1
    }
}

# Generate deployment summary
function New-DeploymentSummary {
    Write-Header "DEPLOYMENT SUMMARY"
    
    $summaryData = @{
        Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss UTC"
        Network = $Network
        DryRun = $DryRun
        UseHSM = $UseHSM
        SkipTests = $SkipTests
        Status = "SUCCESS"
    }
    
    # Check for verification reports
    $verificationFiles = @(
        "prover/formal_verification_report.json",
        "prover/test_results/comprehensive_test_report.json",
        "prover/comprehensive_verification_report.json"
    )
    
    $summaryData.Reports = @()
    foreach ($file in $verificationFiles) {
        if (Test-Path $file) {
            $summaryData.Reports += @{
                File = $file
                Size = (Get-Item $file).Length
                LastModified = (Get-Item $file).LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
            }
        }
    }
    
    # Save summary
    $summaryPath = "deployment_summary_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    $summaryData | ConvertTo-Json -Depth 5 | Set-Content $summaryPath
    
    Write-Info "Deployment summary saved to: $summaryPath"
    
    # Display key information
    Write-Host "`n📊 DEPLOYMENT SUMMARY" -ForegroundColor Magenta
    Write-Host ("=" * 50) -ForegroundColor Gray
    Write-Host "Timestamp: $($summaryData.Timestamp)"
    Write-Host "Network: $($summaryData.Network)"
    Write-Host "Mode: $(if ($DryRun) { 'Dry Run' } else { 'Production' })"
    Write-Host "HSM: $(if ($UseHSM) { 'Enabled' } else { 'Disabled' })"
    Write-Host "Status: $($summaryData.Status)" -ForegroundColor Green
    Write-Host "Reports Generated: $($summaryData.Reports.Count)"
}

# Main execution
function Main {
    try {
        Write-Host "🚀 ZK CIRCUIT FORMAL VERIFICATION & DEPLOYMENT PIPELINE" -ForegroundColor Magenta
        Write-Host ("=" * 80) -ForegroundColor Gray
        Write-Host "Network: $Network"
        Write-Host "Mode: $(if ($DryRun) { 'Dry Run' } else { 'Production' })"
        Write-Host "HSM: $(if ($UseHSM) { 'Enabled' } else { 'Disabled' })"
        Write-Host "Skip Tests: $(if ($SkipTests) { 'Yes' } else { 'No' })"
        Write-Host ("=" * 80) -ForegroundColor Gray
        
        # Run pipeline phases
        Test-Prerequisites
        Install-Dependencies
        Start-FormalVerification
        Start-PropertyTesting
        Start-CircuitCompilation
        Start-DeploymentVerification
        New-DeploymentSummary
        
        Write-Success "`n🏁 PIPELINE COMPLETED SUCCESSFULLY"
        
        if ($DryRun) {
            Write-Info "This was a dry run. For production deployment:"
            Write-Info "  1. Configure secure deployment infrastructure (HSM/Multi-sig)"
            Write-Info "  2. Set required environment variables"
            Write-Info "  3. Run with -DryRun:`$false when ready"
        }
        
    }
    catch {
        Write-Error "Pipeline failed: $($_.Exception.Message)"
        exit 1
    }
}

# Script entry point
if ($MyInvocation.InvocationName -ne '.') {
    Main
}
