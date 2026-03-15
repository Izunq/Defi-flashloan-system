"""
Global test configuration and fixtures for the Flash Loan System
"""

import pytest
import asyncio
import tempfile
import shutil
import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, Generator, Optional
from unittest.mock import Mock, patch, MagicMock
from web3 import Web3
from datetime import datetime, timedelta

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Load test configuration."""
    config_path = PROJECT_ROOT / "test_config.json"
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)
    
    # Default test configuration
    return {
        "security": {
            "price_deviation_threshold": 0.15,
            "volume_anomaly_threshold": 3.0,
            "correlation_threshold": 0.8,
            "confidence_threshold": 0.85,
            "circuit_breaker_threshold": 0.25
        },
        "ml_security": {
            "anomaly_threshold": 0.7,
            "correlation_threshold": 0.6,
            "prediction_window": 300,
            "feature_importance": 0.1,
            "training_data_size": 1000
        },
        "web3": {
            "provider_url": "http://localhost:8545",
            "timeout": 30,
            "retry_attempts": 3
        },
        "database": {
            "path": ":memory:",  # Use in-memory DB for tests
            "max_history_days": 1
        }
    }

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def mock_web3():
    """Mock Web3 instance for testing."""
    mock_w3 = Mock(spec=Web3)
    mock_w3.is_connected.return_value = True
    
    # Create a proper eth mock
    mock_eth = Mock()
    mock_eth.accounts = [f'0x{i:040x}' for i in range(10)]
    mock_eth.get_balance.return_value = 1000 * 10**18  # 1000 ETH
    mock_eth.gas_price = 20 * 10**9  # 20 Gwei
    mock_eth.block_number = 18000000
    mock_w3.eth = mock_eth
    
    mock_w3.to_checksum_address = Web3.to_checksum_address
    mock_w3.keccak = Web3.keccak
    return mock_w3

@pytest.fixture
def mock_oracle_data():
    """Mock oracle price data for testing."""
    base_price = 2000.0  # ETH price in USD
    return {
        'ETH': {
            'price': base_price,
            'timestamp': int(time.time()),
            'source': 'test_oracle',
            'confidence': 0.95,
            'volume_24h': 1000000.0
        },
        'BTC': {
            'price': base_price * 30,  # ~60k USD
            'timestamp': int(time.time()),
            'source': 'test_oracle',
            'confidence': 0.98,
            'volume_24h': 500000.0
        },
        'USDC': {
            'price': 1.0,
            'timestamp': int(time.time()),
            'source': 'test_oracle',
            'confidence': 0.99,
            'volume_24h': 2000000.0
        }
    }

@pytest.fixture
def mock_contract():
    """Mock smart contract for testing."""
    mock_contract = Mock()
    
    # Mock contract functions
    mock_contract.functions.getPrice.return_value.call.return_value = (
        2000 * 10**18,  # price in wei
        int(time.time()),  # timestamp
        500,  # deviation in basis points (5%)
        True  # is valid
    )
    
    mock_contract.functions.checkCircuitBreaker.return_value.call.return_value = False
    mock_contract.functions.getOracleData.return_value.call.return_value = (
        [2000 * 10**18, 2010 * 10**18, 1990 * 10**18],  # prices
        [int(time.time()) - 60, int(time.time()) - 30, int(time.time())],  # timestamps
        [True, True, True]  # validity flags
    )
    
    return mock_contract

# Flash loan test fixtures removed for Sharia compliance
# Interest-based flash loan testing is not permitted in Islamic finance

@pytest.fixture
def sample_arbitrage_opportunity():
    """Sample arbitrage opportunity for testing."""
    return {
        'token_a': 'ETH',
        'token_b': 'USDC',
        'exchange_1': 'uniswap',
        'exchange_2': 'sushiswap',
        'price_1': 2000.0,
        'price_2': 2010.0,
        'profit_percentage': 0.5,
        'estimated_profit': 500.0,
        'gas_cost': 50.0,
        'net_profit': 450.0,
        'confidence': 0.85,
        'expiry': int(time.time()) + 300  # 5 minutes
    }

@pytest.fixture
def security_test_payloads():
    """Security test payloads for validation testing."""
    return {
        'sql_injection': [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM passwords --",
            "admin'--",
            "1' OR 1=1 LIMIT 1 --"
        ],
        'xss': [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert('xss')",
            "<iframe src='javascript:alert(1)'></iframe>",
            "<svg onload=alert(1)>"
        ],
        'command_injection': [
            "; rm -rf /",
            "| cat /etc/passwd",
            "&& echo vulnerable",
            "|| ping -c 1 google.com",
            "`cat /etc/passwd`",
            "$(cat /etc/passwd)"
        ],
        'path_traversal': [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ]
    }

@pytest.fixture
def mock_emergency_system():
    """Mock emergency monitoring system."""
    mock_system = Mock()
    mock_system.is_active = True
    mock_system.alert_count = 0
    mock_system.last_alert_time = None
    mock_system.system_health = 'healthy'
    mock_system.monitoring_status = 'active'
    
    def trigger_alert(alert_type, message):
        mock_system.alert_count += 1
        mock_system.last_alert_time = datetime.now()
        return {'status': 'sent', 'alert_id': f'alert_{mock_system.alert_count}'}
    
    mock_system.trigger_alert.side_effect = trigger_alert
    mock_system.get_system_status.return_value = {
        'health': mock_system.system_health,
        'monitoring': mock_system.monitoring_status,
        'alerts_today': mock_system.alert_count,
        'uptime': '99.9%'
    }
    
    return mock_system

@pytest.fixture
def performance_monitor():
    """Performance monitoring fixture."""
    class PerformanceMonitor:
        def __init__(self):
            self.start_times = {}
            self.measurements = {}
        
        def start(self, operation_name: str):
            self.start_times[operation_name] = time.time()
        
        def end(self, operation_name: str):
            if operation_name in self.start_times:
                duration = time.time() - self.start_times[operation_name]
                if operation_name not in self.measurements:
                    self.measurements[operation_name] = []
                self.measurements[operation_name].append(duration)
                return duration
            return None
        
        def get_average(self, operation_name: str) -> Optional[float]:
            if operation_name in self.measurements:
                return sum(self.measurements[operation_name]) / len(self.measurements[operation_name])
            return None
        
        def get_stats(self) -> Dict[str, Dict[str, float]]:
            stats = {}
            for op_name, times in self.measurements.items():
                stats[op_name] = {
                    'count': len(times),
                    'total': sum(times),
                    'average': sum(times) / len(times),
                    'min': min(times),
                    'max': max(times)
                }
            return stats
    
    return PerformanceMonitor()

@pytest.fixture
def test_database(temp_dir):
    """Test database fixture."""
    db_path = temp_dir / "test.db"
    
    # Mock database operations
    class TestDatabase:
        def __init__(self, path):
            self.path = path
            self.data = {}
            self.connected = True
        
        def store_price_data(self, asset, price_data):
            if asset not in self.data:
                self.data[asset] = []
            self.data[asset].append(price_data)
        
        def get_price_history(self, asset, limit=100):
            return self.data.get(asset, [])[-limit:]
        
        def store_alert(self, alert_data):
            if 'alerts' not in self.data:
                self.data['alerts'] = []
            self.data['alerts'].append(alert_data)
        
        def close(self):
            self.connected = False
    
    return TestDatabase(str(db_path))

@pytest.fixture(autouse=True)
def setup_test_environment(test_config):
    """Setup test environment before each test."""
    # Set environment variables for testing
    os.environ['TESTING'] = 'true'
    os.environ['TEST_MODE'] = 'unit'
    
    # Mock external dependencies
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'price': 2000.0}
        yield
    
    # Cleanup
    if 'TESTING' in os.environ:
        del os.environ['TESTING']
    if 'TEST_MODE' in os.environ:
        del os.environ['TEST_MODE']

# Pytest hooks for test reporting
def pytest_runtest_logreport(report):
    """Custom test reporting."""
    if report.when == "call":
        test_name = report.nodeid.split("::")[-1]
        if report.outcome == "passed":
            print(f"[PASS] {test_name}")
        elif report.outcome == "failed":
            print(f"[FAIL] {test_name}")
        elif report.outcome == "skipped":
            print(f"[SKIP] {test_name}")

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as security test"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add security marker to security-related tests
        if "security" in item.nodeid.lower() or "validation" in item.nodeid.lower():
            item.add_marker(pytest.mark.security)
        
        # Add integration marker to integration tests
        if "integration" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)
        
        # Add oracle marker to oracle-related tests
        if "oracle" in item.nodeid.lower():
            item.add_marker(pytest.mark.oracle)
        
        # Add slow marker to tests that might be slow
        if any(keyword in item.nodeid.lower() for keyword in ["performance", "load", "stress"]):
            item.add_marker(pytest.mark.slow)
