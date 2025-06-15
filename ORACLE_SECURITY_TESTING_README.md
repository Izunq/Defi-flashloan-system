# Oracle Security Testing Suite

This comprehensive testing suite is designed to validate the security, reliability, and effectiveness of the Oracle Security System. The suite includes unit tests, attack simulations, contract tests, and integration tests to ensure all components work correctly together.

## Overview

The Oracle Security Testing Suite consists of the following components:

1. **Unit Tests** - Tests individual components of the Enhanced Oracle Security Monitor
2. **Attack Simulations** - Simulates various oracle attack scenarios to test detection capabilities
3. **Contract Tests** - Tests the Solidity smart contracts that form the on-chain part of the system
4. **Integration Tests** - End-to-end tests of the entire system working together

## Prerequisites

Before running the tests, ensure you have the following installed:

- Python 3.8+
- Node.js 14+
- Hardhat
- Web3.py
- PyTest
- Matplotlib (for visualizations)
- A local Ethereum node or Ganache instance running

## Installation

1. Install Python dependencies:

```bash
pip install -r requirements.txt
```

2. Install Node.js dependencies:

```bash
npm install
```

3. Configure the test environment:

Edit the `test_oracle_config.yaml` file to match your testing environment, or let the test suite create a default configuration.

## Running the Tests

### Running All Tests

To run the complete test suite:

```bash
python run_oracle_security_tests.py --all
```

### Running Specific Test Categories

To run only specific categories of tests:

```bash
# Run only unit tests
python run_oracle_security_tests.py --unit

# Run only attack simulations
python run_oracle_security_tests.py --attack

# Run only contract tests
python run_oracle_security_tests.py --contract

# Run only integration tests
python run_oracle_security_tests.py --integration

# Run multiple categories
python run_oracle_security_tests.py --unit --attack
```

## Test Components

### Unit Tests (`test_enhanced_oracle_security.py`)

Tests the individual components and functions of the Enhanced Oracle Security Monitor, including:

- Initialization and configuration
- Price data collection
- Anomaly detection
- Manipulation pattern detection
- Circuit breaker mechanisms
- Alert generation and processing

### Attack Simulations (`test_oracle_attack_scenarios.py`)

Simulates various oracle attack scenarios to test the system's detection capabilities:

- Flash loan attacks
- Gradual price manipulation
- Oscillating manipulation
- Coordinated multi-oracle attacks
- Time-delayed attacks
- Volume-based manipulation
- Statistical anomaly evasion

The attack simulator generates visualizations and a detailed report of detection performance.

### Contract Tests (`test/oracle-security-contracts.js`)

Tests the Solidity smart contracts that form the on-chain part of the system:

- SecureMultiOracle
- OracleSecurityWrapper
- OracleManipulationMonitor
- PreCognitiveOracle

Tests include normal operations, attack scenarios, and stress tests.

### Integration Tests (`test_oracle_security_integration.py`)

End-to-end tests of the entire system working together:

- Normal operation
- Flash loan attack detection
- Gradual manipulation detection
- Coordinated attack detection
- System-wide emergency protocols

## Test Results

Test results are saved in the `test_results` directory with a timestamp. Each test run generates:

- Test output logs
- JSON reports with detailed results
- Visualizations of attack patterns and detection performance
- A summary report of all test results

## Customizing Tests

### Modifying Attack Scenarios

To add or modify attack scenarios, edit the `_load_attack_scenarios` method in `test_oracle_attack_scenarios.py`.

### Adjusting Security Thresholds

To test different security thresholds, modify the `security` section in `test_oracle_config.yaml`.

### Adding New Test Cases

- For unit tests: Add new test methods to the `TestEnhancedOracleSecurityMonitor` class in `test_enhanced_oracle_security.py`
- For contract tests: Add new test cases to `test/oracle-security-contracts.js`
- For integration tests: Add new test methods to `test_oracle_security_integration.py`

## Troubleshooting

### Common Issues

1. **Web3 Connection Errors**:
   - Ensure your local Ethereum node or Ganache is running
   - Check the provider URL in the configuration file

2. **Contract Deployment Failures**:
   - Check Hardhat configuration
   - Ensure you have sufficient ETH in the deployment account

3. **Test Failures**:
   - Check the test logs for detailed error messages
   - Verify that contract addresses in the configuration are correct

## Contributing

When adding new tests or modifying existing ones:

1. Follow the existing code structure and naming conventions
2. Add appropriate logging
3. Update this README if adding new test categories or major features
4. Ensure all tests can run independently and as part of the full suite

## License

This testing suite is released under the same license as the Oracle Security System.