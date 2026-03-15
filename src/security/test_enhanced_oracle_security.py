#!/usr/bin/env python3
"""
Comprehensive Testing Suite for Enhanced Oracle Security System

This testing suite provides extensive testing for the oracle security monitoring system,
including unit tests, integration tests, and simulation tests for various attack scenarios.
"""

import unittest
import asyncio
import json
import time
import logging
import os
import yaml
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from web3 import Web3
from web3.exceptions import ContractLogicError

# Import the system under test
from enhanced_oracle_security_monitor import (
    EnhancedOracleSecurityMonitor,
    PriceData,
    SecurityAlert,
    OracleMetrics
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_oracle_security.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("OracleSecurityTests")

class TestEnhancedOracleSecurityMonitor(unittest.TestCase):
    """Test suite for the Enhanced Oracle Security Monitor"""

    def setUp(self):
        """Set up test environment before each test"""
        # Create a test configuration
        self.test_config = {
            'web3': {
                'provider_url': 'http://localhost:8545',
                'gas_limit': 3000000
            },
            'contracts': {
                'secure_multi_oracle': '${CONTRACT_ADDRESS}',
                'oracle_security_wrapper': '${CONTRACT_ADDRESS}',
                'oracle_manipulation_monitor': '${CONTRACT_ADDRESS}'
            },
            'security': {
                'max_price_deviation': 500,  # 5%
                'circuit_breaker_threshold': 1000,  # 10%
                'min_oracle_consensus': 3,
                'staleness_threshold': 3600,  # 1 hour
                'monitoring_interval': 30,  # 30 seconds
                'anomaly_detection_window': 100  # 100 data points
            },
            'tracked_assets': ['ETH', 'BTC', 'USDC', 'USDT', 'DAI'],
            'alerts': {
                'email_notifications': False,
                'webhook_url': '',
                'telegram_bot_token': '',
                'telegram_chat_id': ''
            }
        }
        
        # Write test config to a temporary file
        with open('test_oracle_config.yaml', 'w') as f:
            yaml.dump(self.test_config, f)
        
        # Mock Web3 and contract interactions
        self.setup_mocks()
        
        # Initialize the monitor with test configuration
        self.monitor = EnhancedOracleSecurityMonitor(config_path='test_oracle_config.yaml')
        
        # Replace the real Web3 instance with our mock
        self.monitor.w3 = self.mock_w3
        self.monitor.contracts = self.mock_contracts
        
        # Initialize test data
        self.setup_test_data()

    def tearDown(self):
        """Clean up after each test"""
        # Remove temporary config file
        if os.path.exists('test_oracle_config.yaml'):
            os.remove('test_oracle_config.yaml')

    def setup_mocks(self):
        """Set up mock objects for Web3 and contracts"""
        # Mock Web3
        self.mock_w3 = MagicMock()
        self.mock_w3.is_connected.return_value = True
        self.mock_w3.to_checksum_address = lambda addr: addr
        
        # Mock contract functions
        self.mock_secure_multi_oracle = MagicMock()
        self.mock_oracle_security_wrapper = MagicMock()
        self.mock_oracle_manipulation_monitor = MagicMock()
        
        # Setup contract function returns
        self.mock_secure_multi_oracle.functions.getPrice.return_value.call.return_value = (
            100 * 10**18,  # price in wei
            int(time.time()),  # timestamp
            100,  # deviation (1%)
            True  # is_valid
        )
        
        # Mock contracts dictionary
        self.mock_contracts = {
            'secure_multi_oracle': self.mock_secure_multi_oracle,
            'oracle_security_wrapper': self.mock_oracle_security_wrapper,
            'oracle_manipulation_monitor': self.mock_oracle_manipulation_monitor
        }

    def setup_test_data(self):
        """Set up test data for the test cases"""
        # Sample price data
        self.test_price_data = [
            PriceData(
                asset="ETH",
                price=1500.0,
                timestamp=int(time.time()),
                source="SecureMultiOracle",
                confidence=95.0,
                volume=1000000.0,
                deviation=0.5
            ),
            PriceData(
                asset="BTC",
                price=30000.0,
                timestamp=int(time.time()),
                source="SecureMultiOracle",
                confidence=97.0,
                volume=5000000.0,
                deviation=0.3
            )
        ]
        
        # Sample alert
        self.test_alert = SecurityAlert(
            alert_id="test_alert_1",
            alert_type="PRICE_ANOMALY",
            severity="HIGH",
            asset="ETH",
            price=1600.0,
            expected_price=1500.0,
            deviation=6.67,  # (1600-1500)/1500 * 100
            timestamp=int(time.time()),
            description="Test price anomaly",
            resolved=False
        )

    # ===============================
    # UNIT TESTS
    # ===============================

    def test_initialization(self):
        """Test proper initialization of the monitor"""
        self.assertEqual(self.monitor.max_price_deviation, 500)
        self.assertEqual(self.monitor.circuit_breaker_threshold, 1000)
        self.assertEqual(self.monitor.min_oracle_consensus, 3)
        self.assertEqual(len(self.monitor.price_history), 0)
        self.assertEqual(len(self.monitor.oracle_metrics), 0)
        self.assertEqual(len(self.monitor.active_alerts), 0)

    def test_load_config(self):
        """Test configuration loading"""
        config = self.monitor._load_config('test_oracle_config.yaml')
        self.assertEqual(config['web3']['provider_url'], 'http://localhost:8545')
        self.assertEqual(config['security']['max_price_deviation'], 500)
        self.assertEqual(len(config['tracked_assets']), 5)

    def test_get_default_config(self):
        """Test default configuration generation"""
        default_config = self.monitor._get_default_config()
        self.assertIn('web3', default_config)
        self.assertIn('contracts', default_config)
        self.assertIn('security', default_config)
        self.assertIn('alerts', default_config)

    @patch('enhanced_oracle_security_monitor.Web3')
    def test_setup_web3(self, mock_web3_class):
        """Test Web3 setup"""
        # Setup mock
        mock_web3_instance = MagicMock()
        mock_web3_instance.is_connected.return_value = True
        mock_web3_class.HTTPProvider.return_value = "http_provider"
        mock_web3_class.return_value = mock_web3_instance
        
        # Call the method
        monitor = EnhancedOracleSecurityMonitor(config_path='test_oracle_config.yaml')
        
        # Assertions
        mock_web3_class.HTTPProvider.assert_called_once_with('http://localhost:8545')
        mock_web3_instance.is_connected.assert_called_once()

    def test_setup_contracts(self):
        """Test contract setup"""
        # Mock the open function to return a mock file
        mock_open = MagicMock()
        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        mock_file.read.return_value = '{"abi": []}'
        mock_open.return_value = mock_file
        
        with patch('builtins.open', mock_open):
            # Create a new monitor to test contract setup
            monitor = EnhancedOracleSecurityMonitor(config_path='test_oracle_config.yaml')
            monitor.w3 = self.mock_w3
            
            # Call the method
            contracts = monitor._setup_contracts()
            
            # Since we're mocking file operations, we expect no contracts to be loaded
            self.assertEqual(len(contracts), 0)

    # ===============================
    # FUNCTIONAL TESTS
    # ===============================

    @patch('enhanced_oracle_security_monitor.EnhancedOracleSecurityMonitor._collect_price_data')
    @patch('enhanced_oracle_security_monitor.EnhancedOracleSecurityMonitor._analyze_manipulation_patterns')
    @patch('enhanced_oracle_security_monitor.EnhancedOracleSecurityMonitor._update_oracle_metrics')
    @patch('enhanced_oracle_security_monitor.EnhancedOracleSecurityMonitor._check_circuit_breakers')
    @patch('enhanced_oracle_security_monitor.EnhancedOracleSecurityMonitor._process_alerts')
    async def test_monitor_oracle_security(self, mock_process_alerts, mock_check_circuit_breakers, 
                                          mock_update_metrics, mock_analyze_patterns, mock_collect_data):
        """Test the main monitoring loop"""
        # Setup mocks
        mock_collect_data.return_value = self.test_price_data
        mock_analyze_patterns.return_value = [self.test_alert]
        
        # Run one iteration of the monitoring loop
        # We'll use asyncio.wait_for to ensure it doesn't run indefinitely
        try:
            # Create a task for the monitoring function
            task = asyncio.create_task(self.monitor.monitor_oracle_security())
            
            # Wait for a short time to let it execute one iteration
            await asyncio.sleep(0.1)
            
            # Cancel the task
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            # Verify all the expected methods were called
            mock_collect_data.assert_called_once()
            mock_analyze_patterns.assert_called_once_with(self.test_price_data)
            mock_update_metrics.assert_called_once_with(self.test_price_data)
            mock_check_circuit_breakers.assert_called_once_with(self.test_price_data)
            mock_process_alerts.assert_called_once_with([self.test_alert])
            
        except asyncio.TimeoutError:
            self.fail("Monitoring loop did not complete in time")

    @patch('enhanced_oracle_security_monitor.EnhancedOracleSecurityMonitor._get_multi_oracle_data')
    @patch('enhanced_oracle_security_monitor.EnhancedOracleSecurityMonitor._get_external_oracle_data')
    async def test_collect_price_data(self, mock_external_data, mock_multi_oracle_data):
        """Test price data collection"""
        # Setup mocks
        mock_multi_oracle_data.return_value = [self.test_price_data[0]]
        mock_external_data.return_value = [self.test_price_data[1]]
        
        # Call the method
        result = await self.monitor._collect_price_data()
        
        # Assertions
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].asset, "ETH")
        self.assertEqual(result[1].asset, "BTC")
        mock_multi_oracle_data.assert_called_once()
        mock_external_data.assert_called_once()

    async def test_get_multi_oracle_data(self):
        """Test getting data from the SecureMultiOracle contract"""
        # Setup mock for the contract call
        price_id = self.mock_w3.keccak(text="ETH")
        self.mock_secure_multi_oracle.functions.getPrice.return_value.call.return_value = (
            1500 * 10**18,  # price in wei
            int(time.time()),  # timestamp
            50,  # deviation (0.5%)
            True  # is_valid
        )
        
        # Call the method
        result = await self.monitor._get_multi_oracle_data()
        
        # We expect no results since we're not actually calling the contract
        self.assertEqual(len(result), 0)

    async def test_analyze_manipulation_patterns(self):
        """Test analysis of price data for manipulation patterns"""
        # Setup test data in the monitor
        self.monitor.price_history = {
            "ETH": [self.test_price_data[0] for _ in range(20)]
        }
        
        # Create a price anomaly
        anomaly_data = PriceData(
            asset="ETH",
            price=2000.0,  # 33% increase
            timestamp=int(time.time()),
            source="SecureMultiOracle",
            confidence=95.0,
            volume=1000000.0,
            deviation=0.5
        )
        
        # Mock the detection methods
        with patch.object(self.monitor, '_detect_price_anomalies', return_value=[self.test_alert]), \
             patch.object(self.monitor, '_detect_manipulation_patterns', return_value=[]):
            
            # Call the method
            alerts = await self.monitor._analyze_manipulation_patterns([anomaly_data])
            
            # Assertions
            self.assertEqual(len(alerts), 1)
            self.assertEqual(alerts[0].alert_type, "PRICE_ANOMALY")
            self.assertEqual(alerts[0].asset, "ETH")

    async def test_detect_price_anomalies(self):
        """Test detection of price anomalies"""
        # Setup test data in the monitor
        self.monitor.price_history = {
            "ETH": [
                PriceData(
                    asset="ETH",
                    price=1500.0 + i * 10,  # Gradually increasing prices
                    timestamp=int(time.time()) - (20 - i) * 60,  # Every minute
                    source="SecureMultiOracle",
                    confidence=95.0,
                    volume=1000000.0,
                    deviation=0.5
                ) for i in range(20)
            ]
        }
        
        # Create a price anomaly (50% jump)
        anomaly_data = PriceData(
            asset="ETH",
            price=2250.0,
            timestamp=int(time.time()),
            source="SecureMultiOracle",
            confidence=95.0,
            volume=1000000.0,
            deviation=0.5
        )
        
        # Call the method
        alerts = await self.monitor._detect_price_anomalies(anomaly_data)
        
        # Assertions
        self.assertGreater(len(alerts), 0)
        self.assertEqual(alerts[0].alert_type, "PRICE_ANOMALY")
        self.assertEqual(alerts[0].asset, "ETH")
        self.assertGreater(alerts[0].deviation, 0)

    # ===============================
    # INTEGRATION TESTS
    # ===============================

    @patch('enhanced_oracle_security_monitor.EnhancedOracleSecurityMonitor._send_alert_notifications')
    async def test_process_alerts(self, mock_send_notifications):
        """Test alert processing"""
        # Setup mock
        mock_send_notifications.return_value = None
        
        # Call the method
        await self.monitor._process_alerts([self.test_alert])
        
        # Assertions
        self.assertEqual(len(self.monitor.active_alerts), 1)
        self.assertEqual(self.monitor.active_alerts[0].alert_id, "test_alert_1")
        mock_send_notifications.assert_called_once_with(self.test_alert)

    @patch('enhanced_oracle_security_monitor.EnhancedOracleSecurityMonitor._send_email_alert')
    @patch('enhanced_oracle_security_monitor.EnhancedOracleSecurityMonitor._send_webhook_alert')
    @patch('enhanced_oracle_security_monitor.EnhancedOracleSecurityMonitor._send_telegram_alert')
    async def test_send_alert_notifications(self, mock_telegram, mock_webhook, mock_email):
        """Test sending alert notifications"""
        # Setup test alert with critical severity
        critical_alert = SecurityAlert(
            alert_id="critical_alert",
            alert_type="PRICE_MANIPULATION",
            severity="CRITICAL",
            asset="ETH",
            price=2000.0,
            expected_price=1500.0,
            deviation=33.33,
            timestamp=int(time.time()),
            description="Critical price manipulation detected",
            resolved=False
        )
        
        # Enable notifications in config
        self.monitor.config['alerts']['email_notifications'] = True
        self.monitor.config['alerts']['webhook_url'] = 'https://example.com/webhook'
        self.monitor.config['alerts']['telegram_bot_token'] = 'test_token'
        self.monitor.config['alerts']['telegram_chat_id'] = 'test_chat_id'
        
        # Call the method
        await self.monitor._send_alert_notifications(critical_alert)
        
        # Assertions
        mock_email.assert_called_once_with(critical_alert)
        mock_webhook.assert_called_once()
        mock_telegram.assert_called_once_with(critical_alert)

    def test_get_system_status(self):
        """Test getting system status"""
        # Setup test data
        self.monitor.active_alerts = [self.test_alert]
        self.monitor.circuit_breakers = {"ETH": True, "BTC": False}
        self.monitor.oracle_metrics = {
            "Oracle1": OracleMetrics(
                oracle_address="${CONTRACT_ADDRESS}",
                total_updates=100,
                successful_updates=95,
                failed_updates=5,
                average_deviation=0.5,
                last_update=int(time.time()),
                reputation_score=90.0,
                is_active=True
            )
        }
        
        # Call the method
        status = self.monitor.get_system_status()
        
        # Assertions
        self.assertEqual(status['active_alerts'], 1)
        self.assertEqual(status['circuit_breakers_active'], 1)
        self.assertEqual(status['total_oracles'], 1)
        self.assertEqual(status['active_oracles'], 1)

    def test_reset_circuit_breaker(self):
        """Test resetting a circuit breaker"""
        # Setup test data
        self.monitor.circuit_breakers = {"ETH": True, "BTC": False}
        
        # Call the method
        result = self.monitor.reset_circuit_breaker("ETH")
        
        # Assertions
        self.assertTrue(result)
        self.assertFalse(self.monitor.circuit_breakers["ETH"])
        
        # Test resetting a non-active circuit breaker
        result = self.monitor.reset_circuit_breaker("BTC")
        self.assertFalse(result)

    # ===============================
    # ATTACK SIMULATION TESTS
    # ===============================

    async def test_flash_loan_attack_simulation(self):
        """Test detection of a simulated flash loan attack"""
        # Setup normal price history
        self.monitor.price_history = {
            "ETH": [
                PriceData(
                    asset="ETH",
                    price=1500.0 + i * 2,  # Gradually increasing prices
                    timestamp=int(time.time()) - (20 - i) * 60,  # Every minute
                    source="SecureMultiOracle",
                    confidence=95.0,
                    volume=1000000.0,
                    deviation=0.5
                ) for i in range(20)
            ]
        }
        
        # Simulate flash loan attack - sudden price spike followed by return to normal
        attack_data = [
            PriceData(
                asset="ETH",
                price=1800.0,  # 20% spike
                timestamp=int(time.time()),
                source="SecureMultiOracle",
                confidence=95.0,
                volume=5000000.0,  # Higher volume
                deviation=0.5
            ),
            PriceData(
                asset="ETH",
                price=1540.0,  # Back to normal trend
                timestamp=int(time.time()) + 60,
                source="SecureMultiOracle",
                confidence=95.0,
                volume=1000000.0,
                deviation=0.5
            )
        ]
        
        # Process the attack data
        alerts = []
        for data in attack_data:
            result = await self.monitor._detect_price_anomalies(data)
            alerts.extend(result)
            
            # Update price history
            if data.asset not in self.monitor.price_history:
                self.monitor.price_history[data.asset] = []
            self.monitor.price_history[data.asset].append(data)
        
        # Assertions
        self.assertGreater(len(alerts), 0)
        self.assertEqual(alerts[0].alert_type, "PRICE_ANOMALY")
        self.assertGreater(alerts[0].deviation, 0)

    async def test_gradual_manipulation_attack(self):
        """Test detection of a gradual price manipulation attack"""
        # Setup normal price history
        self.monitor.price_history = {
            "ETH": [
                PriceData(
                    asset="ETH",
                    price=1500.0,  # Stable price
                    timestamp=int(time.time()) - (20 - i) * 3600,  # Every hour
                    source="SecureMultiOracle",
                    confidence=95.0,
                    volume=1000000.0,
                    deviation=0.5
                ) for i in range(20)
            ]
        }
        
        # Simulate gradual manipulation - small consistent increases
        attack_data = [
            PriceData(
                asset="ETH",
                price=1500.0 * (1 + 0.02 * i),  # 2% increase each time
                timestamp=int(time.time()) + i * 3600,  # Every hour
                source="SecureMultiOracle",
                confidence=95.0,
                volume=1000000.0,
                deviation=0.5
            ) for i in range(1, 6)  # 5 hours of manipulation
        ]
        
        # Process the attack data
        alerts = []
        for data in attack_data:
            result = await self.monitor._detect_price_anomalies(data)
            alerts.extend(result)
            
            # Update price history
            self.monitor.price_history[data.asset].append(data)
            
            # Also check for manipulation patterns
            pattern_alerts = await self.monitor._detect_manipulation_patterns(data)
            alerts.extend(pattern_alerts)
        
        # Assertions - by the end, we should have detected the manipulation
        self.assertGreater(len(alerts), 0)

    # ===============================
    # PERFORMANCE TESTS
    # ===============================

    async def test_monitoring_performance(self):
        """Test the performance of the monitoring system"""
        # Generate a large dataset
        large_dataset = [
            PriceData(
                asset=f"TOKEN{i % 10}",
                price=100.0 + i * 0.01,
                timestamp=int(time.time()) - (1000 - i),
                source="SecureMultiOracle",
                confidence=95.0,
                volume=1000000.0,
                deviation=0.5
            ) for i in range(1000)
        ]
        
        # Measure time to process
        start_time = time.time()
        
        # Mock the methods to avoid actual external calls
        with patch.object(self.monitor, '_detect_price_anomalies', return_value=[]), \
             patch.object(self.monitor, '_detect_manipulation_patterns', return_value=[]):
            
            for data in large_dataset:
                await self.monitor._analyze_manipulation_patterns([data])
                
                # Update price history
                if data.asset not in self.monitor.price_history:
                    self.monitor.price_history[data.asset] = []
                self.monitor.price_history[data.asset].append(data)
        
        elapsed_time = time.time() - start_time
        
        # Assertions - processing should be reasonably fast
        self.assertLess(elapsed_time, 5.0)  # Should process 1000 items in under 5 seconds

    # ===============================
    # STRESS TESTS
    # ===============================

    async def test_high_frequency_updates(self):
        """Test system behavior with high-frequency price updates"""
        # Generate rapid price updates (100 updates in 1 second)
        rapid_updates = [
            PriceData(
                asset="ETH",
                price=1500.0 + i * 0.1,
                timestamp=int(time.time()) + i // 100,  # 100 updates per second
                source="SecureMultiOracle",
                confidence=95.0,
                volume=1000000.0,
                deviation=0.5
            ) for i in range(1000)
        ]
        
        # Process the updates
        alerts = []
        
        # Mock the methods to avoid actual external calls
        with patch.object(self.monitor, '_detect_price_anomalies', return_value=[]), \
             patch.object(self.monitor, '_detect_manipulation_patterns', return_value=[]):
            
            for data in rapid_updates:
                result = await self.monitor._analyze_manipulation_patterns([data])
                alerts.extend(result)
                
                # Update price history
                if data.asset not in self.monitor.price_history:
                    self.monitor.price_history[data.asset] = []
                self.monitor.price_history[data.asset].append(data)
        
        # Assertions - system should handle high frequency updates
        self.assertEqual(len(self.monitor.price_history["ETH"]), 100)  # Should be limited by deque maxlen

    async def test_multiple_simultaneous_alerts(self):
        """Test handling multiple simultaneous alerts"""
        # Generate multiple alerts for different assets
        multi_alerts = [
            SecurityAlert(
                alert_id=f"alert_{i}",
                alert_type="PRICE_ANOMALY",
                severity="HIGH",
                asset=f"TOKEN{i}",
                price=100.0 * (1 + 0.1 * i),
                expected_price=100.0,
                deviation=10.0 * i,
                timestamp=int(time.time()),
                description=f"Test alert {i}",
                resolved=False
            ) for i in range(50)
        ]
        
        # Mock the notification methods
        with patch.object(self.monitor, '_send_alert_notifications', return_value=None):
            # Process the alerts
            await self.monitor._process_alerts(multi_alerts)
        
        # Assertions
        self.assertEqual(len(self.monitor.active_alerts), 50)

def main():
    """Run the test suite"""
    unittest.main()

if __name__ == "__main__":
    main()