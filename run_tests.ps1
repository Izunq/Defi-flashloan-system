# Flash Loan System - Comprehensive Test Runner
# PowerShell script for running tests on Windows

param(
    [string]$TestType = "all",
    [switch]$Coverage,
    [switch]$Parallel,
    [switch]$Smoke,
    [switch]$Quick,
    [switch]$Verbose,
    [switch]$Install,
    [switch]$Report,
    [string]$OutputDir = "test_results"
)

# Color output functions
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Error { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }
function Write-Info { param($Message) Write-Host "ℹ️  $Message" -ForegroundColor Blue }
function Write-Warning { param($Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }

# Banner
Write-Host @"
╔══════════════════════════════════════════════════════════════════╗
║                   🧪 Flash Loan Test Runner 🧪                   ║
║                     Comprehensive Testing Suite                  ║
╚══════════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

# Check Python installation
try {
    $pythonVersion = python --version 2>&1
    Write-Success "Python found: $pythonVersion"
} catch {
    Write-Error "Python is not installed or not in PATH"
    exit 1
}

# Create output directory
if (!(Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    Write-Info "Created output directory: $OutputDir"
}

# Install dependencies if requested
if ($Install) {
    Write-Info "Installing test dependencies..."
    
    $requirementFiles = @(
        "requirements.txt",
        "requirements_test.txt",
        "requirements_fixed.txt"
    )
    
    foreach ($reqFile in $requirementFiles) {
        if (Test-Path $reqFile) {
            Write-Info "Installing from $reqFile..."
            try {
                python -m pip install -r $reqFile
                Write-Success "Installed dependencies from $reqFile"
            } catch {
                Write-Warning "Failed to install from $reqFile"
            }
        }
    }
}

# Build pytest command based on test type
$pytestArgs = @("python", "-m", "pytest")

# Test file selection based on type
switch ($TestType.ToLower()) {
    "unit" {
        $pytestArgs += @(
            "test_input_validation.py",
            "test_enhanced_oracle_security.py",
            "test_enhanced_oracle_security_fixed.py"
        )
        $pytestArgs += @("-m", "unit")
        Write-Info "Running Unit Tests"
    }
    "integration" {
        $pytestArgs += @(
            "test_oracle_security_integration.py",
            "test_oracle_security_integration_fixed.py",
            "test_distributed_agents.py",
            "test_cross_chain_security.py"
        )
        $pytestArgs += @("-m", "integration")
        Write-Info "Running Integration Tests"
    }
    "security" {
        $pytestArgs += @(
            "security_test_suite.py",
            "test_gas_griefing_protection.py",
            "test_oracle_attack_scenarios.py",
            "test_oracle_attack_scenarios_fixed.py"
        )
        $pytestArgs += @("-m", "security")
        Write-Info "Running Security Tests"
    }
    "performance" {
        $pytestArgs += @(
            "oracle_security_testing_suite.py",
            "test_advanced_oracle_security.py"
        )
        $pytestArgs += @("-m", "slow or performance")
        Write-Info "Running Performance Tests"
    }
    "emergency" {
        $pytestArgs += @("test_emergency_monitoring.py")
        $pytestArgs += @("-m", "emergency")
        Write-Info "Running Emergency Tests"
    }
    "smoke" {
        $pytestArgs += @(
            "test_input_validation.py::InputValidationTestSuite::test_string_validation_normal",
            "test_enhanced_oracle_security_fixed.py::TestEnhancedOracleSecurityMonitor::test_initialization"
        )
        Write-Info "Running Smoke Tests"
    }
    "all" {
        $pytestArgs += @(".")
        Write-Info "Running All Tests"
    }
    default {
        Write-Error "Unknown test type: $TestType"
        Write-Info "Available types: unit, integration, security, performance, emergency, smoke, all"
        exit 1
    }
}

# Add common pytest options
$pytestArgs += @("--verbose", "--tb=short")

# Add coverage if requested
if ($Coverage) {
    $pytestArgs += @(
        "--cov=.",
        "--cov-report=term-missing",
        "--cov-report=html:$OutputDir/htmlcov",
        "--cov-report=xml:$OutputDir/coverage.xml",
        "--cov-fail-under=70"
    )
    Write-Info "Coverage reporting enabled"
}

# Add parallel execution if requested
if ($Parallel) {
    $pytestArgs += @("-n", "auto")
    Write-Info "Parallel execution enabled"
}

# Add output formatting
$pytestArgs += @(
    "--junitxml=$OutputDir/junit.xml",
    "--html=$OutputDir/report.html",
    "--self-contained-html"
)

# Add timeout
if ($Quick) {
    $pytestArgs += @("--timeout=60")
    Write-Info "Quick mode: 60s timeout per test"
} else {
    $pytestArgs += @("--timeout=300")
}

# Add verbosity
if ($Verbose) {
    $pytestArgs += @("-v", "-s")
}

# Add other useful options
$pytestArgs += @(
    "--strict-markers",
    "--strict-config",
    "--durations=10",
    "--maxfail=10"
)

# Display command being run
Write-Info "Running command:"
Write-Host ($pytestArgs -join " ") -ForegroundColor Gray

# Record start time
$startTime = Get-Date

# Run the tests
try {
    Write-Info "Starting test execution..."
    
    # Execute pytest
    $process = Start-Process -FilePath "python" -ArgumentList ($pytestArgs[1..($pytestArgs.Length-1)]) -Wait -PassThru -NoNewWindow
    
    $endTime = Get-Date
    $duration = $endTime - $startTime
    
    Write-Info "Test execution completed in $($duration.TotalSeconds.ToString('F2')) seconds"
    
    # Check results
    if ($process.ExitCode -eq 0) {
        Write-Success "All tests passed! 🎉"
        
        # Display coverage summary if available
        if ($Coverage -and (Test-Path "$OutputDir/coverage.xml")) {
            Write-Info "Coverage report generated at: $OutputDir/htmlcov/index.html"
        }
        
        # Display HTML report location
        if (Test-Path "$OutputDir/report.html") {
            Write-Info "Test report generated at: $OutputDir/report.html"
        }
        
    } elseif ($process.ExitCode -eq 1) {
        Write-Error "Some tests failed"
        Write-Info "Check the detailed report at: $OutputDir/report.html"
    } else {
        Write-Error "Test execution encountered errors (Exit code: $($process.ExitCode))"
    }
    
    # Run additional analysis if specified
    if ($Report) {
        Write-Info "Generating comprehensive test report..."
        try {
            python test_runner.py --project-root . --no-coverage
            Write-Success "Comprehensive report generated"
        } catch {
            Write-Warning "Failed to generate comprehensive report"
        }
    }
    
    exit $process.ExitCode
    
} catch {
    Write-Error "Failed to run tests: $($_.Exception.Message)"
    exit 1
}

# Helper functions for test management
function Show-TestHelp {
    Write-Host @"

Flash Loan Test Runner - Usage Examples:

Basic Usage:
  .\run_tests.ps1                           # Run all tests
  .\run_tests.ps1 -TestType unit           # Run unit tests only
  .\run_tests.ps1 -TestType security       # Run security tests only
  .\run_tests.ps1 -Smoke                   # Run quick smoke tests

With Options:
  .\run_tests.ps1 -Coverage                # Run with coverage reporting
  .\run_tests.ps1 -Parallel               # Run tests in parallel
  .\run_tests.ps1 -Quick                  # Run with shorter timeouts
  .\run_tests.ps1 -Verbose                # Verbose output
  .\run_tests.ps1 -Install                # Install dependencies first

Combined:
  .\run_tests.ps1 -TestType unit -Coverage -Parallel -Install

Available Test Types:
  - unit         : Unit tests for individual components
  - integration  : Integration tests for system interaction
  - security     : Security-focused tests and vulnerability checks
  - performance  : Performance and load tests
  - emergency    : Emergency monitoring and response tests
  - smoke        : Quick validation tests
  - all          : All test suites (default)

Output:
  - Test results are saved to the 'test_results' directory
  - HTML reports are generated for easy viewing
  - Coverage reports are available when -Coverage is used
  - JUnit XML files are generated for CI/CD integration

"@ -ForegroundColor Yellow
}
