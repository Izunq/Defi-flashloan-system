# Integration Tests Runner Script for Windows

# Check if .env.test file exists
if (-not (Test-Path .env.test)) {
    Write-Error "Error: .env.test file not found. Please create it with the required test environment variables."
    exit 1
}

# Load test environment variables
$envContent = Get-Content .env.test
foreach ($line in $envContent) {
    if ($line -match '^\s*([^#][^=]+)=(.*)$') {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim()
        [Environment]::SetEnvironmentVariable($key, $value, "Process")
    }
}

# Create results directory
$ResultsDir = "./integration_tests/results"
if (-not (Test-Path $ResultsDir)) {
    New-Item -ItemType Directory -Path $ResultsDir | Out-Null
    Write-Host "Created directory: $ResultsDir" -ForegroundColor Cyan
}

# Timestamp for result files
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

# Run blockchain integration tests
Write-Host "Running blockchain integration tests..." -ForegroundColor Green
node ./integration_tests/blockchain_integration_test.js
if ($LASTEXITCODE -ne 0) {
    Write-Error "Blockchain integration tests failed with exit code $LASTEXITCODE"
    # Continue with other tests even if this one fails
} else {
    Write-Host "Blockchain integration tests completed successfully!" -ForegroundColor Green
}

# Copy test results
if (Test-Path "./integration_tests/test-results.json") {
    Copy-Item "./integration_tests/test-results.json" "$ResultsDir/blockchain_test_results_$Timestamp.json"
}

# Run WebSocket communication tests
Write-Host "Running WebSocket communication tests..." -ForegroundColor Green
node ./integration_tests/blockchain_integration_test.js --websocket-only
if ($LASTEXITCODE -ne 0) {
    Write-Error "WebSocket communication tests failed with exit code $LASTEXITCODE"
    # Continue with other tests even if this one fails
} else {
    Write-Host "WebSocket communication tests completed successfully!" -ForegroundColor Green
}

# Run load tests
Write-Host "Running load tests..." -ForegroundColor Green
node ./integration_tests/load_test.js
if ($LASTEXITCODE -ne 0) {
    Write-Error "Load tests failed with exit code $LASTEXITCODE"
    # Continue with other tests even if this one fails
} else {
    Write-Host "Load tests completed successfully!" -ForegroundColor Green
}

# Copy load test results
if (Test-Path "./integration_tests/load-test-results.json") {
    Copy-Item "./integration_tests/load-test-results.json" "$ResultsDir/load_test_results_$Timestamp.json"
}

# Generate test report
Write-Host "Generating test report..." -ForegroundColor Green

$ReportContent = @"
# Integration Test Report
Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## Test Summary

"@

# Add blockchain test results if available
if (Test-Path "$ResultsDir/blockchain_test_results_$Timestamp.json") {
    $BlockchainResults = Get-Content "$ResultsDir/blockchain_test_results_$Timestamp.json" | ConvertFrom-Json
    $ReportContent += @"

### Blockchain Integration Tests
- Total: $($BlockchainResults.total)
- Passed: $($BlockchainResults.passed)
- Failed: $($BlockchainResults.failed)
- Skipped: $($BlockchainResults.skipped)

"@
}

# Add load test results if available
if (Test-Path "$ResultsDir/load_test_results_$Timestamp.json") {
    $LoadResults = Get-Content "$ResultsDir/load_test_results_$Timestamp.json" | ConvertFrom-Json
    $ReportContent += @"

### Load Tests
- Total Requests: $($LoadResults.totalRequests)
- Successful Requests: $($LoadResults.successfulRequests)
- Failed Requests: $($LoadResults.failedRequests)
- Requests Per Second: $($LoadResults.requestsPerSecond)
- Average Latency: $($LoadResults.averageLatency.ToString("F2"))ms
- Median Latency (P50): $($LoadResults.p50Latency)ms
- 95th Percentile Latency: $($LoadResults.p95Latency)ms
- 99th Percentile Latency: $($LoadResults.p99Latency)ms
- Maximum Latency: $($LoadResults.maxLatency)ms

"@
}

# Save report
$ReportContent | Out-File -FilePath "$ResultsDir/integration_test_report_$Timestamp.md" -Encoding utf8
Write-Host "Test report saved to $ResultsDir/integration_test_report_$Timestamp.md" -ForegroundColor Cyan

Write-Host "All integration tests completed!" -ForegroundColor Green