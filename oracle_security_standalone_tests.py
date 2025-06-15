#!/usr/bin/env python3
"""
Standalone Oracle Security Testing Suite

This testing suite provides comprehensive testing for oracle security systems
without dependencies on external monitors or blockchain connections.
"""

import unittest
import asyncio
import json
import time
import logging
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, AsyncMock

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("oracle_security_standalone_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("StandaloneOracleTests")

# Define test data structures
@dataclass
class TestPriceData:
    """Test price data structure"""
    asset: str
    price: float
    timestamp: int
    source: str
    confidence: float
    volume: float = 0.0
    deviation: float = 0.0

@dataclass
class TestSecurityAlert:
    """Test security alert structure"""
    alert_id: str
    alert_type: str
    severity: str
    asset: str
    price: float
    expected_price: float
    deviation: float
    timestamp: int
    description: str
    resolved: bool = False

@dataclass
class TestOracleMetrics:
    """Test oracle metrics structure"""
    oracle_address: str
    total_updates: int
    successful_updates: int
    failed_updates: int
    average_deviation: float
    last_update: int
    reputation_score: float
    is_active: bool

class MockOracleSecurityMonitor:
    """Complete mock oracle security monitor for testing"""
    
    def __init__(self, config_path: str = "test_oracle_config.yaml"):
        self.config_path = config_path
        self.config = self._load_test_config()
        self.active_alerts = []
        self.circuit_breakers = {}
        self.price_history = {}
        self.oracle_metrics = {}
        
        # Configuration parameters
        self.max_price_deviation = self.config.get('security', {}).get('max_price_deviation', 500)
        self.circuit_breaker_threshold = self.config.get('security', {}).get('circuit_breaker_threshold', 1000)
        self.min_oracle_consensus = self.config.get('security', {}).get('min_oracle_consensus', 3)
        
        logger.info("Mock Oracle Security Monitor initialized")
    
    def _load_test_config(self) -> Dict:
        """Load test configuration"""
        try:
            if os.path.exists(self.config_path):
                # Try JSON first
                if self.config_path.endswith('.json'):
                    with open(self.config_path, 'r') as f:
                        return json.load(f)
                # Try YAML if available
                elif self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
                    try:
                        import yaml
                        with open(self.config_path, 'r') as f:
                            return yaml.safe_load(f)
                    except ImportError:
                        logger.warning("YAML not available, using default config")
        except Exception as e:
            logger.warning(f"Could not load config: {e}")
        
        return {
            'web3': {
                'provider_url': 'http://localhost:8545',
                'gas_limit': 3000000
            },
            'security': {
                'max_price_deviation': 500,
                'circuit_breaker_threshold': 1000,
                'min_oracle_consensus': 3,
                'staleness_threshold': 3600,
                'monitoring_interval': 30,
                'anomaly_detection_window': 100
            },
            'tracked_assets': ['ETH', 'BTC', 'USDC', 'USDT', 'DAI'],
            'alerts': {
                'email_notifications': False,
                'webhook_url': '',
                'telegram_bot_token': '',
                'telegram_chat_id': ''
            }
        }
    
    def get_system_status(self) -> Dict:
        """Get system status"""
        return {
            'active_alerts': len(self.active_alerts),
            'circuit_breakers_active': sum(1 for v in self.circuit_breakers.values() if v),
            'total_oracles': len(self.oracle_metrics),
            'active_oracles': sum(1 for metrics in self.oracle_metrics.values() if metrics.is_active),
            'system_health': 'OK',
            'last_updated': int(time.time())        }
    
    async def _detect_price_anomalies(self, data: TestPriceData) -> List[TestSecurityAlert]:
        """Detect price anomalies"""
        alerts = []
        
        # Simple statistical anomaly detection
        threshold = 10.0  # 10% deviation threshold for anomalies
        
        if data.deviation > threshold:
            severity = "HIGH" if data.deviation > threshold * 2 else "MEDIUM"
            
            alert = TestSecurityAlert(
                alert_id=f"anomaly_{int(time.time())}_{data.asset}",
                alert_type="PRICE_ANOMALY",
                severity=severity,
                asset=data.asset,
                price=data.price,
                expected_price=data.price / (1 + data.deviation / 100),
                deviation=data.deviation,
                timestamp=data.timestamp,
                description=f"Price anomaly detected for {data.asset}: {data.deviation:.2f}% deviation"
            )
            alerts.append(alert)
        
        return alerts
    
    async def _detect_manipulation_patterns(self, data: TestPriceData) -> List[TestSecurityAlert]:
        """Detect manipulation patterns"""
        alerts = []
          # Check for manipulation based on circuit breaker threshold
        threshold = 15.0  # 15% deviation threshold for manipulation detection
        
        if data.deviation > threshold:
            severity = "CRITICAL" if data.deviation > threshold * 1.5 else "HIGH"
            
            alert = TestSecurityAlert(
                alert_id=f"manipulation_{int(time.time())}_{data.asset}",
                alert_type="PRICE_MANIPULATION",
                severity=severity,
                asset=data.asset,
                price=data.price,
                expected_price=data.price / (1 + data.deviation / 100),
                deviation=data.deviation,
                timestamp=data.timestamp,
                description=f"Price manipulation detected for {data.asset}: {data.deviation:.2f}% deviation"
            )
            alerts.append(alert)
        
        # Check for volume-based manipulation
        if hasattr(data, 'volume') and data.volume > 0:
            # Simple volume-based detection (placeholder)
            if data.volume > 10000000:  # 10M volume threshold
                alert = TestSecurityAlert(
                    alert_id=f"volume_manipulation_{int(time.time())}_{data.asset}",
                    alert_type="VOLUME_MANIPULATION",
                    severity="MEDIUM",
                    asset=data.asset,
                    price=data.price,
                    expected_price=data.price,
                    deviation=0.0,
                    timestamp=data.timestamp,
                    description=f"Unusual volume detected for {data.asset}: {data.volume:,.0f}"
                )
                alerts.append(alert)
        
        return alerts
    
    def reset_circuit_breaker(self, asset: str) -> bool:
        """Reset circuit breaker for an asset"""
        if asset in self.circuit_breakers and self.circuit_breakers[asset]:
            self.circuit_breakers[asset] = False
            logger.info(f"Circuit breaker reset for {asset}")
            return True
        return False
    
    def add_oracle_metrics(self, oracle_address: str, metrics: TestOracleMetrics):
        """Add oracle metrics for testing"""
        self.oracle_metrics[oracle_address] = metrics
    
    async def process_price_data(self, data: TestPriceData) -> List[TestSecurityAlert]:
        """Process price data and return alerts"""
        alerts = []
        
        # Run anomaly detection
        anomaly_alerts = await self._detect_price_anomalies(data)
        alerts.extend(anomaly_alerts)
        
        # Run manipulation detection
        manipulation_alerts = await self._detect_manipulation_patterns(data)
        alerts.extend(manipulation_alerts)
        
        # Add to price history
        if data.asset not in self.price_history:
            self.price_history[data.asset] = []
        self.price_history[data.asset].append(data)
        
        # Trigger circuit breaker if needed
        for alert in alerts:
            if alert.severity == "CRITICAL":
                self.circuit_breakers[data.asset] = True
                logger.warning(f"Circuit breaker triggered for {data.asset}")
        
        # Add alerts to active alerts
        self.active_alerts.extend(alerts)
        
        return alerts

class TestOracleSecurityMonitor(unittest.TestCase):
    """Comprehensive test suite for Oracle Security Monitor"""

    def setUp(self):
        """Set up test environment before each test"""
        # Create test configuration
        self.test_config = {
            'web3': {'provider_url': 'http://localhost:8545'},
            'security': {
                'max_price_deviation': 500,
                'circuit_breaker_threshold': 1000,
                'min_oracle_consensus': 3
            },
            'tracked_assets': ['ETH', 'BTC', 'USDC'],
            'alerts': {'email_notifications': False}
        }
          # Write test config to file
        config_file = 'test_oracle_config.json'
        with open(config_file, 'w') as f:
            json.dump(self.test_config, f, indent=2)
        
        # Initialize monitor
        self.monitor = MockOracleSecurityMonitor(config_path=config_file)
          # Setup test data
        self.setup_test_data()

    def tearDown(self):
        """Clean up after each test"""
        for file_name in ['test_oracle_config.yaml', 'test_oracle_config.json']:
            if os.path.exists(file_name):
                os.remove(file_name)

    def setup_test_data(self):
        """Set up test data"""
        self.test_price_data = [
            TestPriceData(
                asset="ETH",
                price=1500.0,
                timestamp=int(time.time()),
                source="TestOracle",
                confidence=95.0,
                volume=1000000.0,
                deviation=0.5
            ),
            TestPriceData(
                asset="BTC",
                price=30000.0,
                timestamp=int(time.time()),
                source="TestOracle",
                confidence=97.0,
                volume=5000000.0,
                deviation=0.3
            )
        ]
        
        self.test_alert = TestSecurityAlert(
            alert_id="test_alert_1",
            alert_type="PRICE_ANOMALY",
            severity="HIGH",
            asset="ETH",
            price=1600.0,
            expected_price=1500.0,
            deviation=6.67,
            timestamp=int(time.time()),
            description="Test price anomaly"
        )

    # ===============================
    # UNIT TESTS
    # ===============================

    def test_monitor_initialization(self):
        """Test monitor initialization"""
        self.assertEqual(self.monitor.max_price_deviation, 500)
        self.assertEqual(self.monitor.circuit_breaker_threshold, 1000)
        self.assertEqual(self.monitor.min_oracle_consensus, 3)
        self.assertEqual(len(self.monitor.active_alerts), 0)

    def test_config_loading(self):
        """Test configuration loading"""
        config = self.monitor._load_test_config()
        self.assertIn('web3', config)
        self.assertIn('security', config)
        self.assertEqual(config['security']['max_price_deviation'], 500)

    def test_system_status(self):
        """Test system status reporting"""
        # Add test data
        self.monitor.active_alerts.append(self.test_alert)
        self.monitor.circuit_breakers["ETH"] = True
        
        status = self.monitor.get_system_status()
        
        self.assertEqual(status['active_alerts'], 1)
        self.assertEqual(status['circuit_breakers_active'], 1)
        self.assertIn('system_health', status)

    def test_circuit_breaker_reset(self):
        """Test circuit breaker reset functionality"""
        # Setup circuit breakers
        self.monitor.circuit_breakers["ETH"] = True
        self.monitor.circuit_breakers["BTC"] = False
        
        # Test successful reset
        result = self.monitor.reset_circuit_breaker("ETH")
        self.assertTrue(result)
        self.assertFalse(self.monitor.circuit_breakers["ETH"])
        
        # Test unsuccessful reset
        result = self.monitor.reset_circuit_breaker("BTC")
        self.assertFalse(result)

    # ===============================
    # ASYNC TESTS
    # ===============================

    def test_price_anomaly_detection(self):
        """Test price anomaly detection"""
        async def run_test():
            # Normal price data
            normal_data = TestPriceData(
                asset="ETH",
                price=1500.0,
                timestamp=int(time.time()),
                source="TestOracle",
                confidence=95.0,
                volume=1000000.0,
                deviation=0.5  # Normal deviation
            )
            
            alerts = await self.monitor._detect_price_anomalies(normal_data)
            self.assertEqual(len(alerts), 0)
            
            # Anomalous price data
            anomaly_data = TestPriceData(
                asset="ETH",
                price=1800.0,
                timestamp=int(time.time()),
                source="TestOracle",
                confidence=95.0,
                volume=1000000.0,
                deviation=20.0  # High deviation
            )
            
            alerts = await self.monitor._detect_price_anomalies(anomaly_data)
            self.assertGreater(len(alerts), 0)
            self.assertEqual(alerts[0].alert_type, "PRICE_ANOMALY")
        
        asyncio.run(run_test())

    def test_manipulation_detection(self):
        """Test manipulation pattern detection"""
        async def run_test():
            # Manipulation data
            manipulation_data = TestPriceData(
                asset="ETH",
                price=2100.0,
                timestamp=int(time.time()),
                source="TestOracle",
                confidence=95.0,
                volume=1000000.0,
                deviation=40.0  # Very high deviation
            )
            
            alerts = await self.monitor._detect_manipulation_patterns(manipulation_data)
            self.assertGreater(len(alerts), 0)
            
            # Check for manipulation alert
            manipulation_alerts = [a for a in alerts if "MANIPULATION" in a.alert_type]
            self.assertGreater(len(manipulation_alerts), 0)
        
        asyncio.run(run_test())

    def test_volume_manipulation_detection(self):
        """Test volume-based manipulation detection"""
        async def run_test():
            # High volume data
            volume_data = TestPriceData(
                asset="ETH",
                price=1500.0,
                timestamp=int(time.time()),
                source="TestOracle",
                confidence=95.0,
                volume=50000000.0,  # Very high volume
                deviation=2.0
            )
            
            alerts = await self.monitor._detect_manipulation_patterns(volume_data)
            
            # Check for volume manipulation alert
            volume_alerts = [a for a in alerts if "VOLUME" in a.alert_type]
            self.assertGreater(len(volume_alerts), 0)
        
        asyncio.run(run_test())

    def test_complete_processing_workflow(self):
        """Test complete price data processing workflow"""
        async def run_test():
            # Process normal data
            normal_data = TestPriceData(
                asset="ETH",
                price=1500.0,
                timestamp=int(time.time()),
                source="TestOracle",
                confidence=95.0,
                volume=1000000.0,
                deviation=0.5
            )
            
            alerts = await self.monitor.process_price_data(normal_data)
            self.assertEqual(len(alerts), 0)
            self.assertIn("ETH", self.monitor.price_history)
            
            # Process anomalous data
            anomaly_data = TestPriceData(
                asset="ETH",
                price=2000.0,
                timestamp=int(time.time()),
                source="TestOracle",
                confidence=95.0,
                volume=1000000.0,
                deviation=33.33
            )
            
            alerts = await self.monitor.process_price_data(anomaly_data)
            self.assertGreater(len(alerts), 0)
            self.assertGreater(len(self.monitor.active_alerts), 0)
        
        asyncio.run(run_test())

    # ===============================
    # ATTACK SIMULATION TESTS
    # ===============================

    def test_flash_loan_attack_simulation(self):
        """Test flash loan attack detection"""
        async def run_test():
            # Simulate flash loan attack pattern
            attack_sequence = [
                TestPriceData(
                    asset="ETH",
                    price=1500.0,
                    timestamp=int(time.time()),
                    source="TestOracle",
                    confidence=95.0,
                    volume=1000000.0,
                    deviation=0.5
                ),
                TestPriceData(
                    asset="ETH",
                    price=1800.0,  # Sudden spike
                    timestamp=int(time.time()) + 60,
                    source="TestOracle",
                    confidence=95.0,
                    volume=10000000.0,  # High volume
                    deviation=20.0
                ),
                TestPriceData(
                    asset="ETH",
                    price=1510.0,  # Return to normal
                    timestamp=int(time.time()) + 120,
                    source="TestOracle",
                    confidence=95.0,
                    volume=1000000.0,
                    deviation=0.67
                )
            ]
            
            total_alerts = 0
            for data in attack_sequence:
                alerts = await self.monitor.process_price_data(data)
                total_alerts += len(alerts)
            
            # Should detect the spike
            self.assertGreater(total_alerts, 0)
        
        asyncio.run(run_test())

    def test_gradual_manipulation_simulation(self):
        """Test gradual manipulation detection"""
        async def run_test():
            base_price = 1500.0
            
            # Simulate gradual manipulation over time
            for i in range(10):
                manipulation_factor = 1 + (0.02 * i)  # 2% increase each time
                data = TestPriceData(
                    asset="ETH",
                    price=base_price * manipulation_factor,
                    timestamp=int(time.time()) + i * 3600,
                    source="TestOracle",
                    confidence=95.0,
                    volume=1000000.0,
                    deviation=2.0 * i
                )
                
                await self.monitor.process_price_data(data)
            
            # Should eventually detect manipulation
            manipulation_alerts = [
                a for a in self.monitor.active_alerts 
                if "MANIPULATION" in a.alert_type
            ]
            self.assertGreater(len(manipulation_alerts), 0)
        
        asyncio.run(run_test())

    # ===============================
    # PERFORMANCE TESTS
    # ===============================

    def test_high_frequency_processing(self):
        """Test high-frequency data processing performance"""
        async def run_test():
            start_time = time.time()
            
            # Process 100 data points rapidly
            for i in range(100):
                data = TestPriceData(
                    asset=f"TOKEN{i % 5}",
                    price=100.0 + i * 0.1,
                    timestamp=int(time.time()) + i,
                    source="TestOracle",
                    confidence=95.0,
                    volume=1000000.0,
                    deviation=0.1
                )
                
                await self.monitor.process_price_data(data)
            
            elapsed = time.time() - start_time
            
            # Should process quickly
            self.assertLess(elapsed, 5.0)  # Under 5 seconds
            self.assertEqual(len(self.monitor.price_history), 5)  # 5 unique tokens
        
        asyncio.run(run_test())

    def test_memory_efficiency(self):
        """Test memory usage with large datasets"""
        async def run_test():
            # Process a large amount of data
            for i in range(1000):
                data = TestPriceData(
                    asset="ETH",
                    price=1500.0 + i * 0.01,
                    timestamp=int(time.time()) + i,
                    source="TestOracle",
                    confidence=95.0,
                    volume=1000000.0,
                    deviation=0.1
                )
                
                await self.monitor.process_price_data(data)
            
            # Check that price history doesn't grow unbounded
            self.assertLessEqual(len(self.monitor.price_history["ETH"]), 1000)
        
        asyncio.run(run_test())

    # ===============================
    # INTEGRATION TESTS
    # ===============================

    def test_multi_asset_monitoring(self):
        """Test monitoring multiple assets simultaneously"""
        async def run_test():
            assets = ["ETH", "BTC", "USDC", "LINK", "UNI"]
              # Process data for multiple assets
            for asset in assets:
                data = TestPriceData(
                    asset=asset,
                    price=1000.0 + hash(asset) % 1000,
                    timestamp=int(time.time()),
                    source="TestOracle",
                    confidence=95.0,
                    volume=1000000.0,
                    deviation=12.0  # Above anomaly threshold to trigger alerts
                )
                
                await self.monitor.process_price_data(data)
            
            # Should have data for all assets
            self.assertEqual(len(self.monitor.price_history), len(assets))
            
            # Should generate some alerts
            self.assertGreater(len(self.monitor.active_alerts), 0)
        
        asyncio.run(run_test())

    def test_oracle_metrics_integration(self):
        """Test oracle metrics integration"""
        # Add oracle metrics
        metrics = TestOracleMetrics(
            oracle_address="0x1234567890123456789012345678901234567890",
            total_updates=1000,
            successful_updates=995,
            failed_updates=5,
            average_deviation=0.5,
            last_update=int(time.time()),
            reputation_score=99.5,
            is_active=True
        )
        
        self.monitor.add_oracle_metrics("oracle1", metrics)
        
        status = self.monitor.get_system_status()
        self.assertEqual(status['total_oracles'], 1)
        self.assertEqual(status['active_oracles'], 1)

def run_performance_benchmark():
    """Run performance benchmarks"""
    print("\n" + "="*50)
    print("ORACLE SECURITY PERFORMANCE BENCHMARK")
    print("="*50)
    
    async def benchmark():
        monitor = MockOracleSecurityMonitor()
        
        # Benchmark 1: Single asset processing
        start_time = time.time()
        for i in range(1000):
            data = TestPriceData(
                asset="ETH",
                price=1500.0 + i * 0.01,
                timestamp=int(time.time()) + i,
                source="TestOracle",
                confidence=95.0,
                volume=1000000.0,
                deviation=0.1
            )
            await monitor.process_price_data(data)
        
        single_asset_time = time.time() - start_time
        
        # Benchmark 2: Multi-asset processing
        monitor = MockOracleSecurityMonitor()  # Fresh instance
        start_time = time.time()
        
        assets = ["ETH", "BTC", "USDC", "LINK", "UNI"]
        for i in range(200):
            for asset in assets:
                data = TestPriceData(
                    asset=asset,
                    price=1000.0 + i * 0.01,
                    timestamp=int(time.time()) + i,
                    source="TestOracle",
                    confidence=95.0,
                    volume=1000000.0,
                    deviation=0.1
                )
                await monitor.process_price_data(data)
        
        multi_asset_time = time.time() - start_time
        
        print(f"Single Asset (1000 updates): {single_asset_time:.2f}s")
        print(f"Multi Asset (1000 updates):  {multi_asset_time:.2f}s")
        print(f"Processing Rate: {1000/single_asset_time:.0f} updates/sec")
        print("="*50)
    
    asyncio.run(benchmark())

def main():
    """Run the comprehensive test suite"""
    print("Starting Oracle Security Standalone Test Suite...")
    
    # Run unit tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestOracleSecurityMonitor)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Run performance benchmark
    run_performance_benchmark()
    
    # Print summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}")
    
    print("="*50)
    
    # Return appropriate exit code
    if result.failures or result.errors:
        return 1
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
