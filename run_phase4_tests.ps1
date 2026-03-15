# Phase 4 Testing & Verification PowerShell Script
# Executes the complete Phase 4 testing suite for Windows environments

param(
    [int]$LoadDuration = 60,
    [int]$LoadUsers = 10,
    [string]$Suite = "all"
)

Write-Host "🚀 Phase 4 Testing & Verification" -ForegroundColor Green
Write-Host "=" * 60

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Create reports directory
$reportsDir = "reports"
if (!(Test-Path $reportsDir)) {
    New-Item -ItemType Directory -Path $reportsDir | Out-Null
    Write-Host "📁 Created reports directory" -ForegroundColor Green
}

# Install dependencies
Write-Host "🔧 Installing testing dependencies..." -ForegroundColor Yellow
if (Test-Path "requirements_testing.txt") {
    python -m pip install -r requirements_testing.txt
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "⚠️ requirements_testing.txt not found, skipping dependency installation" -ForegroundColor Yellow
}

# Function to run pytest with proper formatting
function Run-PytestSuite {
    param(
        [string]$TestPath,
        [string]$SuiteName,
        [string]$Marker = "",
        [string]$ReportName
    )
    
    Write-Host "🧪 Running $SuiteName..." -ForegroundColor Cyan
    
    $pytestArgs = @(
        "-m", "pytest",
        $TestPath,
        "-v",
        "--html=reports/$ReportName.html",
        "--junitxml=reports/$ReportName.xml"
    )
    
    if ($Marker) {
        $pytestArgs += @("-m", $Marker)
    }
    
    if ($SuiteName -eq "unit tests") {
        $pytestArgs += @(
            "--cov=.",
            "--cov-report=html:reports/coverage",
            "--cov-report=term"
        )
    }
    
    $result = & python @pytestArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ $SuiteName completed successfully" -ForegroundColor Green
    } else {
        Write-Host "⚠️ $SuiteName completed with issues" -ForegroundColor Yellow
    }
    
    return $LASTEXITCODE
}

# Function to run load tests
function Run-LoadTests {
    param(
        [int]$Duration,
        [int]$Users
    )
    
    Write-Host "⚡ Running load tests (Duration: ${Duration}s, Users: $Users)..." -ForegroundColor Cyan
    
    $locustFile = "tests\load\locustfile.py"
    if (Test-Path $locustFile) {
        $result = python -m locust -f $locustFile --headless --users $Users --spawn-rate 2 --run-time "${Duration}s" --html reports/load_test_report.html --csv reports/load_test
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Load tests completed successfully" -ForegroundColor Green
        } else {
            Write-Host "⚠️ Load tests completed with issues" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⏭️ Locust file not found, skipping load tests" -ForegroundColor Yellow
    }
    
    return $LASTEXITCODE
}

# Execute test suites based on parameter
$testResults = @{}
$totalStart = Get-Date

switch ($Suite.ToLower()) {
    "all" {
        Write-Host "🔄 Running all test suites..." -ForegroundColor Magenta
        
        # Formal Verification
        Write-Host "`n" + "=" * 20 + " Formal Verification " + "=" * 20
        $testResults["formal_verification"] = Run-PytestSuite -TestPath "tests\unit\test_formal_verification.py" -SuiteName "formal verification" -Marker "formal_verification" -ReportName "formal_verification"
        
        # Unit Tests
        Write-Host "`n" + "=" * 20 + " Unit Tests " + "=" * 20
        $testResults["unit_tests"] = Run-PytestSuite -TestPath "tests\unit" -SuiteName "unit tests" -ReportName "unit_tests"
        
        # Integration Tests
        Write-Host "`n" + "=" * 20 + " Integration Tests " + "=" * 20
        $testResults["integration_tests"] = Run-PytestSuite -TestPath "tests\integration" -SuiteName "integration tests" -Marker "integration" -ReportName "integration_tests"
        
        # Security Tests
        Write-Host "`n" + "=" * 20 + " Security Tests " + "=" * 20
        $testResults["security_tests"] = Run-PytestSuite -TestPath "tests\security" -SuiteName "security tests" -Marker "security" -ReportName "security_tests"
        
        # Load Tests
        Write-Host "`n" + "=" * 20 + " Load Tests " + "=" * 20
        $testResults["load_tests"] = Run-LoadTests -Duration $LoadDuration -Users $LoadUsers
    }
    "unit" {
        $testResults["unit_tests"] = Run-PytestSuite -TestPath "tests\unit" -SuiteName "unit tests" -ReportName "unit_tests"
    }
    "integration" {
        $testResults["integration_tests"] = Run-PytestSuite -TestPath "tests\integration" -SuiteName "integration tests" -Marker "integration" -ReportName "integration_tests"
    }
    "security" {
        $testResults["security_tests"] = Run-PytestSuite -TestPath "tests\security" -SuiteName "security tests" -Marker "security" -ReportName "security_tests"
    }
    "load" {
        $testResults["load_tests"] = Run-LoadTests -Duration $LoadDuration -Users $LoadUsers
    }
    "formal" {
        $testResults["formal_verification"] = Run-PytestSuite -TestPath "tests\unit\test_formal_verification.py" -SuiteName "formal verification" -Marker "formal_verification" -ReportName "formal_verification"
    }
    default {
        Write-Host "❌ Invalid suite: $Suite. Valid options: all, unit, integration, security, load, formal" -ForegroundColor Red
        exit 1
    }
}

# Calculate total duration
$totalDuration = (Get-Date) - $totalStart
$totalSeconds = $totalDuration.TotalSeconds

# Generate summary
Write-Host "`n" + "=" * 60
Write-Host "🏁 Phase 4 Testing Complete" -ForegroundColor Green
Write-Host "Total Duration: $([math]::Round($totalSeconds, 2)) seconds" -ForegroundColor Cyan

# Count results
$passed = ($testResults.Values | Where-Object { $_ -eq 0 }).Count
$total = $testResults.Count

if ($passed -eq $total) {
    Write-Host "🎉 All test suites passed successfully!" -ForegroundColor Green
} else {
    Write-Host "⚠️ $passed/$total test suites passed" -ForegroundColor Yellow
}

# Show individual results
Write-Host "`n📊 Test Suite Results:" -ForegroundColor Cyan
foreach ($suite in $testResults.GetEnumerator()) {
    $status = if ($suite.Value -eq 0) { "✅ PASSED" } else { "❌ FAILED" }
    $color = if ($suite.Value -eq 0) { "Green" } else { "Red" }
    Write-Host "  $($suite.Key): $status" -ForegroundColor $color
}

Write-Host "`n📁 Reports generated in: reports\" -ForegroundColor Cyan
Write-Host "📋 Available reports:" -ForegroundColor Cyan

# List generated reports
$reportFiles = @(
    "unit_tests.html",
    "integration_tests.html", 
    "security_tests.html",
    "formal_verification.html",
    "load_test_report.html",
    "coverage\index.html"
)

foreach ($reportFile in $reportFiles) {
    $fullPath = Join-Path "reports" $reportFile
    if (Test-Path $fullPath) {
        Write-Host "  ✓ $reportFile" -ForegroundColor Green
    }
}

# Create phase completion marker
$completionData = @{
    phase = "Phase 4 - Testing & Verification"
    completion_time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    duration_seconds = [math]::Round($totalSeconds, 2)
    test_results = $testResults
    passed_suites = $passed
    total_suites = $total
    success_rate = [math]::Round(($passed / $total) * 100, 2)
}

$completionData | ConvertTo-Json -Depth 3 | Out-File "reports\phase4_completion.json" -Encoding UTF8

Write-Host "`n✅ Phase 4 Testing & Verification completed!" -ForegroundColor Green
Write-Host "🔍 Review detailed reports in the reports\ directory" -ForegroundColor Cyan

# Exit with appropriate code
$overallSuccess = $passed -eq $total
exit $(if ($overallSuccess) { 0 } else { 1 })
