# 🧪 Flash Loan System - Comprehensive Testing Guide

## Overview

This guide provides complete instructions for testing the Flash Loan System, including unit tests, integration tests, security tests, and performance tests.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Test Environment Setup](#test-environment-setup)
3. [Test Categories](#test-categories)
4. [Running Tests](#running-tests)
5. [Test Configuration](#test-configuration)
6. [Continuous Integration](#continuous-integration)
7. [Test Reports](#test-reports)
8. [Troubleshooting](#troubleshooting)

## Quick Start

### For Windows Users

1. **Simple Test Execution:**
   ```cmd
   run_tests.bat
   ```
   This will show an interactive menu with test options.

2. **Direct Commands:**
   ```cmd
   run_tests.bat smoke        # Quick validation tests
   run_tests.bat unit         # Unit tests with coverage
   run_tests.bat security     # Security tests
   run_tests.bat all          # Complete test suite
   ```

3. **PowerShell (Advanced):**
   ```powershell
   .\run_tests.ps1 -TestType unit -Coverage -Parallel
   ```

### For Python Users

1. **Using Test Runner:**
   ```bash
   python test_runner.py --suites unit security
   ```

2. **Direct pytest:**
   ```bash
   pytest test_input_validation.py -v --cov=.
   ```

## Test Environment Setup

### Automatic Setup

```bash
# Setup complete test environment
python setup_test_environment.py --setup

# Check environment status
python setup_test_environment.py --check

# Cleanup test environment
python setup_test_environment.py --cleanup
```

### Manual Setup

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements_test.txt
   ```

2. **Create Test Directories:**
   ```bash
   mkdir test_data test_results test_logs
   ```

3. **Set Environment Variables:**
   ```bash
   export TESTING=true
   export TEST_MODE=unit
   export WEB3_PROVIDER_URL=http://localhost:8545
   ```

## Test Categories

### 1. Unit Tests
- **Purpose:** Test individual components in isolation
- **Files:** `test_input_validation.py`, `test_enhanced_oracle_security.py`
- **Duration:** ~5-10 minutes
- **Command:** `pytest -m unit`

**Key Features:**
- Input validation testing
- Oracle security component testing
- Mock external dependencies
- Fast execution
- High code coverage

### 2. Integration Tests
- **Purpose:** Test system component interactions
- **Files:** `test_oracle_security_integration.py`, `test_distributed_agents.py`
- **Duration:** ~15-30 minutes
- **Command:** `pytest -m integration`

**Key Features:**
- End-to-end workflow testing
- Real blockchain interaction (Ganache)
- Cross-component communication
- Contract deployment testing

### 3. Security Tests
- **Purpose:** Validate security measures and vulnerability resistance
- **Files:** `security_test_suite.py`, `test_gas_griefing_protection.py`
- **Duration:** ~10-15 minutes
- **Command:** `pytest -m security`

**Key Features:**
- SQL injection prevention
- XSS attack resistance
- Command injection detection
- Path traversal protection
- Gas griefing protection
- Oracle manipulation detection

### 4. Performance Tests
- **Purpose:** Validate system performance and scalability
- **Files:** `oracle_security_testing_suite.py`, `test_advanced_oracle_security.py`
- **Duration:** ~30-60 minutes
- **Command:** `pytest -m "performance or slow"`

**Key Features:**
- Load testing
- Stress testing
- Memory usage validation
- Response time measurement
- Throughput testing

### 5. Emergency Tests
- **Purpose:** Test emergency monitoring and response systems
- **Files:** `test_emergency_monitoring.py`
- **Duration:** ~5-10 minutes
- **Command:** `pytest -m emergency`

**Key Features:**
- Alert system testing
- Recovery mechanism validation
- Health monitoring
- Failover testing

## Running Tests

### Using Batch Files (Windows)

```cmd
# Interactive menu
run_tests.bat

# Specific test types
run_tests.bat smoke
run_tests.bat unit
run_tests.bat security
run_tests.bat integration
run_tests.bat all

# Install dependencies
run_tests.bat install
```

### Using PowerShell (Windows)

```powershell
# Basic usage
.\run_tests.ps1 -TestType unit

# With options
.\run_tests.ps1 -TestType security -Coverage -Verbose

# Parallel execution
.\run_tests.ps1 -TestType all -Parallel -Coverage

# Quick smoke tests
.\run_tests.ps1 -Smoke

# Generate comprehensive report
.\run_tests.ps1 -TestType all -Report
```

### Using Python Test Runner

```bash
# Run all tests
python test_runner.py

# Specific test suites
python test_runner.py --suites unit security

# Smoke tests only
python test_runner.py --smoke

# With coverage and reporting
python test_runner.py --suites all --coverage --report
```

### Using pytest Directly

```bash
# Run all tests
pytest

# Specific test files
pytest test_input_validation.py test_enhanced_oracle_security.py

# With markers
pytest -m "unit and not slow"
pytest -m "security or integration"

# With coverage
pytest --cov=. --cov-report=html

# Parallel execution
pytest -n auto

# Verbose output
pytest -v -s

# Stop on first failure
pytest -x

# Run only failed tests from last run
pytest --lf
```

## Test Configuration

### pytest.ini
The main pytest configuration file controls:
- Test discovery patterns
- Markers for test categorization
- Coverage settings
- Timeout configurations
- Logging configuration

### conftest.py
Global test configuration including:
- Test fixtures
- Mock objects
- Test data
- Environment setup
- Performance monitoring

### Test-specific Configuration Files

1. **test_config.json:** Test runtime configuration
2. **test_data/mock_price_data.json:** Mock oracle data
3. **test_data/security_payloads.json:** Security test payloads
4. **test_data/.env.test:** Test environment variables

## Continuous Integration

### GitHub Actions Workflow

The CI pipeline includes:

1. **Smoke Tests:** Quick validation on multiple Python versions
2. **Unit Tests:** Comprehensive unit testing with coverage
3. **Security Tests:** Security scanning and vulnerability testing
4. **Integration Tests:** Full system integration testing
5. **Performance Tests:** Load and performance testing (scheduled)
6. **Reporting:** Comprehensive test result reporting

### Local CI Simulation

```bash
# Run CI pipeline locally
python test_runner.py --suites smoke unit security integration
```

## Test Reports

### HTML Reports
- **Location:** `test_results/report.html`
- **Content:** Test results, coverage, performance metrics
- **Generated:** Automatically after test runs

### Coverage Reports
- **Location:** `test_results/htmlcov/index.html`
- **Content:** Code coverage analysis
- **Threshold:** 70% minimum coverage

### JSON Reports
- **Location:** `test_report.json`
- **Content:** Machine-readable test results
- **Usage:** CI/CD integration, metrics tracking

### Performance Reports
- **Location:** `performance_reports/`
- **Content:** Performance metrics, benchmarks
- **Generated:** During performance test runs

## Test Data Management

### Mock Data
- **Price Data:** Realistic oracle price feeds
- **Contract ABIs:** Mock smart contract interfaces
- **Security Payloads:** Known attack vectors for testing

### Test Databases
- **Unit Tests:** In-memory SQLite databases
- **Integration Tests:** Temporary test databases
- **Cleanup:** Automatic cleanup after test runs

## Troubleshooting

### Common Issues

1. **Import Errors:**
   ```bash
   # Install missing dependencies
   pip install -r requirements_test.txt
   
   # Check Python path
   echo $PYTHONPATH
   ```

2. **Web3 Connection Errors:**
   ```bash
   # Start Ganache CLI
   ganache-cli --port 8545 --deterministic
   
   # Check connection
   curl http://localhost:8545
   ```

3. **Test Timeouts:**
   ```bash
   # Increase timeout
   pytest --timeout=600
   
   # Run without timeout
   pytest --timeout=0
   ```

4. **Memory Issues:**
   ```bash
   # Run tests sequentially
   pytest --maxfail=1
   
   # Reduce parallel workers
   pytest -n 2
   ```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
pytest -v -s --tb=long

# Run single test with debugging
pytest test_input_validation.py::test_specific_function -v -s
```

### Performance Debugging

```bash
# Profile test execution
pytest --profile --profile-svg

# Memory profiling
pytest --memory-profile

# Generate performance report
python test_runner.py --suites performance --report
```

## Best Practices

### Writing Tests

1. **Use descriptive test names**
2. **Follow AAA pattern (Arrange, Act, Assert)**
3. **Use appropriate markers**
4. **Mock external dependencies**
5. **Test both success and failure cases**
6. **Include security test cases**

### Test Organization

1. **Group related tests in classes**
2. **Use fixtures for common setup**
3. **Keep tests independent**
4. **Use parameterized tests for multiple inputs**
5. **Separate unit and integration tests**

### Performance Testing

1. **Set realistic performance targets**
2. **Test under load**
3. **Monitor memory usage**
4. **Profile critical paths**
5. **Validate scalability**

## Support

For issues or questions about testing:

1. **Check the logs:** `test_logs/` directory
2. **Review test reports:** `test_results/report.html`
3. **Run environment check:** `python setup_test_environment.py --check`
4. **Enable debug mode:** Set `LOG_LEVEL=DEBUG`

---

## Example Test Execution

### Complete Test Suite

```bash
# 1. Setup environment
python setup_test_environment.py --setup

# 2. Run smoke tests first
python test_runner.py --smoke

# 3. Run comprehensive tests
python test_runner.py --suites all --coverage --report

# 4. Check results
open test_results/report.html
```

### Quick Development Testing

```bash
# Test specific component
pytest test_input_validation.py -v

# Test with coverage
pytest test_enhanced_oracle_security.py --cov=enhanced_oracle_security_monitor

# Security testing
pytest -m security -v
```

This comprehensive testing framework ensures the Flash Loan System is thoroughly validated across all components and use cases.
