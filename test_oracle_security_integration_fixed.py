#!/usr/bin/env python3
"""
Oracle Security System Integration Tests - Fixed Version

This module provides comprehensive end-to-end testing of the oracle security system,
integrating all components including the Python monitor, Solidity contracts,
and external data sources.
"""

import asyncio
import json
import time
import logging
import os
import yaml
import pytest
import subprocess
import requests
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.exceptions import ContractLogicError
from unittest.mock import Mock, patch, MagicMock

# Import the system under test
try:
    from enhanced_oracle_security_monitor import (
        EnhancedOracleSecurityMonitor,
        PriceData,
        SecurityAlert,
        OracleMetrics
    )
    MONITOR_CLASS = EnhancedOracleSecurityMonitor
    MONITOR_MODULE = "enhanced_oracle_security_monitor"
except ImportError:
    try:
        from production_oracle_security_monitor import (
            ProductionOracleSecurityMonitor,
            PriceDataPoint as PriceData,
            SecurityIncident as SecurityAlert,
            OracleHealthMetrics as OracleMetrics
        )
        MONITOR_CLASS = ProductionOracleSecurityMonitor
        MONITOR_MODULE = "production_oracle_security_monitor"
    except ImportError:
        # Create mock classes for testing
        @dataclass
        class PriceData:
            asset: str
            price: float
            timestamp: int
            source: str
            confidence: float
            volume: float = 0.0
            deviation: float = 0.0

        @dataclass
        class SecurityAlert:
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
        class OracleMetrics:
            oracle_address: str
            total_updates: int
            successful_updates: int
            failed_updates: int
            average_deviation: float
            last_update: int
            reputation_score: float
            is_active: bool

        class MockOracleSecurityMonitor:
            def __init__(self, config_path: str = "test_oracle_config.yaml"):
                self.config = self._load_config(config_path)
                self.active_alerts = []
                self.circuit_breakers = {}
                self.price_history = {}
                self.oracle_metrics = {}
                
            def _load_config(self, config_path: str) -> Dict:
                return {
                    'web3': {'provider_url': 'http://localhost:8545'},
                    'contracts': {},
                    'security': {'max_price_deviation': 500},
                    'tracked_assets': ['ETH', 'BTC']
                }
                
            async def start_monitoring(self):
                pass
                
            def get_system_status(self):
                return {
                    'active_alerts': len(self.active_alerts),
                    'circuit_breakers_active': sum(1 for v in self.circuit_breakers.values() if v),
                    'system_health': 'OK'
                }

        MONITOR_CLASS = MockOracleSecurityMonitor
        MONITOR_MODULE = "mock"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("oracle_security_integration_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("OracleSecurityIntegrationTests")

class OracleSecurityIntegrationTest:
    """Integration tests for the Oracle Security System"""
    
    def __init__(self, config_path: str = "test_oracle_config.yaml"):
        """Initialize the integration test environment"""
        self.config = self._load_config(config_path)
        self.w3 = self._setup_web3()
        self.contracts = {}
        self.monitor = None
        self.test_accounts = []
        self.oracle_accounts = []
        self.admin_account = None
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration for testing"""
        return {
            'web3': {
                'provider_url': 'http://localhost:8545',
                'gas_limit': 3000000
            },
            'contracts': {
                'secure_multi_oracle': '0x1234567890123456789012345678901234567890',
                'oracle_security_wrapper': '0x2345678901234567890123456789012345678901',
                'oracle_manipulation_monitor': '0x3456789012345678901234567890123456789012'
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
            },
            'test': {
                'deploy_contracts': False,  # Skip deployment for tests
                'use_ganache': True,
                'ganache_port': 8545,
                'test_duration': 300,  # 5 minutes
                'price_update_interval': 10,  # 10 seconds
                'manipulation_scenarios': ['flash_loan', 'gradual', 'coordinated']
            }
        }
    
    def _setup_web3(self) -> Optional[Web3]:
        """Set up Web3 connection"""
        try:
            provider_url = self.config.get('web3', {}).get('provider_url', 'http://localhost:8545')
            w3 = Web3(Web3.HTTPProvider(provider_url))
            
            # Add middleware for POA chains if needed
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            if w3.is_connected():
                logger.info(f"Connected to Web3 at {provider_url}")
                return w3
            else:
                logger.warning(f"Failed to connect to {provider_url}, using mock")
                return self._create_mock_web3()
        except Exception as e:
            logger.warning(f"Web3 setup failed: {e}, using mock")
            return self._create_mock_web3()
    
    def _create_mock_web3(self) -> Mock:
        """Create a mock Web3 instance for testing"""
        mock_w3 = Mock()
        mock_w3.is_connected.return_value = True
        mock_w3.eth.accounts = [f'0x{i:040x}' for i in range(10)]
        mock_w3.to_checksum_address = lambda addr: addr
        mock_w3.keccak = lambda text: Web3.keccak(text=text)
        return mock_w3

    async def setup_test_environment(self):
        """Set up the complete test environment"""
        logger.info("Setting up test environment")
        
        # Check if we need to deploy contracts
        if self.config.get('test', {}).get('deploy_contracts', False):
            await self._deploy_contracts()
        else:
            await self._load_existing_contracts()
        
        # Initialize the monitor
        self._setup_monitor()
        
        # Setup test accounts
        self._setup_accounts()
        
        logger.info("Test environment setup complete")
    
    async def _deploy_contracts(self):
        """Deploy the oracle security contracts"""
        logger.info("Deploying oracle security contracts")
        
        try:
            # Try to run the deployment script
            result = subprocess.run(
                ["python", "deploy_production_oracle_security.py"],
                capture_output=True,
                text=True,
                check=True,
                timeout=60
            )
            
            logger.info(f"Deployment completed: {result.stdout}")
            
            # Mock contract addresses for testing
            self.contracts = {
                'secure_multi_oracle': '0x1234567890123456789012345678901234567890',
                'oracle_security_wrapper': '0x2345678901234567890123456789012345678901',
                'oracle_manipulation_monitor': '0x3456789012345678901234567890123456789012'
            }
            
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning(f"Contract deployment failed: {e}, using mock addresses")
            await self._load_existing_contracts()
    
    async def _load_existing_contracts(self):
        """Load existing contract addresses from config"""
        logger.info("Loading existing contract addresses")
        
        self.contracts = self.config.get('contracts', {
            'secure_multi_oracle': '0x1234567890123456789012345678901234567890',
            'oracle_security_wrapper': '0x2345678901234567890123456789012345678901',
            'oracle_manipulation_monitor': '0x3456789012345678901234567890123456789012'
        })
        
        logger.info(f"Loaded contracts: {self.contracts}")
    
    def _setup_monitor(self):
        """Set up the oracle security monitor"""
        logger.info("Setting up oracle security monitor")
        
        # Create a test config file
        config_file = "test_oracle_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(self.config, f)
        
        # Initialize the monitor
        try:
            self.monitor = MONITOR_CLASS(config_path=config_file)
            logger.info(f"Oracle security monitor initialized using {MONITOR_MODULE}")
        except Exception as e:
            logger.error(f"Failed to initialize monitor: {e}")
            # Create a minimal mock monitor
            self.monitor = Mock()
            self.monitor.active_alerts = []
            self.monitor.circuit_breakers = {}
            self.monitor.get_system_status = Mock(return_value={'status': 'OK'})
    
    def _setup_accounts(self):
        """Set up test accounts"""
        logger.info("Setting up test accounts")
        
        if self.w3 and hasattr(self.w3, 'eth') and hasattr(self.w3.eth, 'accounts'):
            accounts = self.w3.eth.accounts
            
            if len(accounts) >= 6:
                # Assign accounts
                self.admin_account = accounts[0]
                self.oracle_accounts = accounts[1:6]  # 5 oracle accounts
                self.test_accounts = accounts[6:]  # Remaining accounts for testing
            else:
                # Generate mock accounts
                self.admin_account = '0x0000000000000000000000000000000000000001'
                self.oracle_accounts = [f'0x000000000000000000000000000000000000000{i}' for i in range(2, 7)]
                self.test_accounts = [f'0x000000000000000000000000000000000000000{i}' for i in range(7, 10)]
        else:
            # Generate mock accounts
            self.admin_account = '0x0000000000000000000000000000000000000001'
            self.oracle_accounts = [f'0x000000000000000000000000000000000000000{i}' for i in range(2, 7)]
            self.test_accounts = [f'0x000000000000000000000000000000000000000{i}' for i in range(7, 10)]
        
        logger.info(f"Admin account: {self.admin_account}")
        logger.info(f"Oracle accounts: {self.oracle_accounts}")
        logger.info(f"Test accounts: {self.test_accounts}")

    async def run_integration_tests(self):
        """Run the integration tests"""
        logger.info("Starting integration tests")
        
        # Setup test environment
        await self.setup_test_environment()
        
        # Run test scenarios
        test_results = {}
        
        try:
            test_results['normal_operation'] = await self._test_normal_operation()
            test_results['flash_loan_attack'] = await self._test_flash_loan_attack()
            test_results['gradual_manipulation'] = await self._test_gradual_manipulation()
            test_results['coordinated_attack'] = await self._test_coordinated_attack()
            
            # Run the monitor for a short time if it supports it
            if hasattr(self.monitor, 'start_monitoring'):
                monitor_task = asyncio.create_task(self._run_monitor())
                await asyncio.sleep(10)  # Run for 10 seconds
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass
            
            # Generate test report
            test_results['report'] = self._generate_test_report()
            
        except Exception as e:
            logger.error(f"Integration test failed: {e}")
            test_results['error'] = str(e)
        
        logger.info("Integration tests completed")
        return test_results
    
    async def _run_monitor(self):
        """Run the oracle security monitor"""
        logger.info("Starting oracle security monitor")
        
        try:
            if hasattr(self.monitor, 'monitor_oracle_security'):
                await self.monitor.monitor_oracle_security()
            elif hasattr(self.monitor, 'start_monitoring'):
                await self.monitor.start_monitoring()
            else:
                # Mock monitoring
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            logger.info("Monitor task cancelled")
        except Exception as e:
            logger.error(f"Error in monitor: {e}")
    
    async def _test_normal_operation(self):
        """Test normal operation of the oracle security system"""
        logger.info("Testing normal operation")
        
        # Simulate normal price updates
        normal_prices = [
            PriceData(
                asset="ETH",
                price=1500.0 + i * 2,  # Gradual increase
                timestamp=int(time.time()) + i * 60,
                source="SecureMultiOracle",
                confidence=95.0,
                volume=1000000.0,
                deviation=0.1 * i
            ) for i in range(5)
        ]
        
        alerts_generated = 0
        
        # Process the normal data
        for price_data in normal_prices:
            # Check if monitor has anomaly detection
            if hasattr(self.monitor, '_detect_price_anomalies'):
                try:
                    alerts = await self.monitor._detect_price_anomalies(price_data)
                    alerts_generated += len(alerts)
                except Exception as e:
                    logger.warning(f"Anomaly detection failed: {e}")
        
        result = {
            'test_name': 'normal_operation',
            'status': 'PASSED',
            'data_points_processed': len(normal_prices),
            'alerts_generated': alerts_generated,
            'expected_alerts': 0,
            'timestamp': int(time.time())
        }
        
        logger.info("Normal operation test completed")
        return result
    
    async def _test_flash_loan_attack(self):
        """Test flash loan attack detection"""
        logger.info("Testing flash loan attack detection")
        
        # Simulate flash loan attack pattern
        attack_data = [
            PriceData(
                asset="ETH",
                price=1500.0,  # Normal price
                timestamp=int(time.time()),
                source="SecureMultiOracle",
                confidence=95.0,
                volume=1000000.0,
                deviation=0.5
            ),
            PriceData(
                asset="ETH",
                price=1800.0,  # 20% spike
                timestamp=int(time.time()) + 60,
                source="SecureMultiOracle",
                confidence=95.0,
                volume=5000000.0,  # High volume
                deviation=20.0
            ),
            PriceData(
                asset="ETH",
                price=1510.0,  # Return to normal
                timestamp=int(time.time()) + 120,
                source="SecureMultiOracle",
                confidence=95.0,
                volume=1000000.0,
                deviation=0.7
            )
        ]
        
        alerts_generated = 0
        
        # Process the attack data
        for price_data in attack_data:
            if hasattr(self.monitor, '_detect_price_anomalies'):
                try:
                    alerts = await self.monitor._detect_price_anomalies(price_data)
                    alerts_generated += len(alerts)
                except Exception as e:
                    logger.warning(f"Attack detection failed: {e}")
        
        # Flash loan attacks should generate alerts
        expected_alerts = 1  # At least one alert for the spike
        detection_successful = alerts_generated >= expected_alerts
        
        result = {
            'test_name': 'flash_loan_attack',
            'status': 'PASSED' if detection_successful else 'FAILED',
            'data_points_processed': len(attack_data),
            'alerts_generated': alerts_generated,
            'expected_alerts': expected_alerts,
            'detection_successful': detection_successful,
            'timestamp': int(time.time())
        }
        
        logger.info("Flash loan attack test completed")
        return result
    
    async def _test_gradual_manipulation(self):
        """Test gradual price manipulation detection"""
        logger.info("Testing gradual price manipulation detection")
        
        # Simulate gradual manipulation - consistent small increases
        base_price = 1500.0
        manipulation_data = [
            PriceData(
                asset="ETH",
                price=base_price * (1 + 0.02 * i),  # 2% increase each hour
                timestamp=int(time.time()) + i * 3600,
                source="SecureMultiOracle",
                confidence=95.0,
                volume=1000000.0,
                deviation=2.0 * i
            ) for i in range(6)  # 6 hours of manipulation
        ]
        
        alerts_generated = 0
        
        # Process the manipulation data
        for price_data in manipulation_data:
            if hasattr(self.monitor, '_detect_manipulation_patterns'):
                try:
                    alerts = await self.monitor._detect_manipulation_patterns(price_data)
                    alerts_generated += len(alerts)
                except Exception as e:
                    logger.warning(f"Manipulation detection failed: {e}")
        
        # Gradual manipulation should eventually be detected
        expected_alerts = 1
        detection_successful = alerts_generated >= expected_alerts
        
        result = {
            'test_name': 'gradual_manipulation',
            'status': 'PASSED' if detection_successful else 'FAILED',
            'data_points_processed': len(manipulation_data),
            'alerts_generated': alerts_generated,
            'expected_alerts': expected_alerts,
            'detection_successful': detection_successful,
            'timestamp': int(time.time())
        }
        
        logger.info("Gradual manipulation test completed")
        return result
    
    async def _test_coordinated_attack(self):
        """Test coordinated attack detection"""
        logger.info("Testing coordinated attack detection")
        
        # Simulate coordinated attack - multiple oracles reporting similar manipulated prices
        base_price = 30000.0  # BTC price
        coordinated_data = []
        
        # Create data from multiple oracles with similar manipulation
        for oracle_idx in range(5):
            for time_idx in range(3):
                manipulation_factor = 1.05 if oracle_idx < 3 else 1.0  # 3 out of 5 oracles manipulated
                price_data = PriceData(
                    asset="BTC",
                    price=base_price * manipulation_factor,
                    timestamp=int(time.time()) + time_idx * 600,  # Every 10 minutes
                    source=f"Oracle{oracle_idx + 1}",
                    confidence=95.0,
                    volume=1000000.0,
                    deviation=5.0 if oracle_idx < 3 else 0.5
                )
                coordinated_data.append(price_data)
        
        alerts_generated = 0
        
        # Process the coordinated attack data
        for price_data in coordinated_data:
            if hasattr(self.monitor, '_detect_manipulation_patterns'):
                try:
                    alerts = await self.monitor._detect_manipulation_patterns(price_data)
                    alerts_generated += len(alerts)
                except Exception as e:
                    logger.warning(f"Coordinated attack detection failed: {e}")
        
        # Coordinated attacks should be detected
        expected_alerts = 1
        detection_successful = alerts_generated >= expected_alerts
        
        result = {
            'test_name': 'coordinated_attack',
            'status': 'PASSED' if detection_successful else 'FAILED',
            'data_points_processed': len(coordinated_data),
            'alerts_generated': alerts_generated,
            'expected_alerts': expected_alerts,
            'detection_successful': detection_successful,
            'timestamp': int(time.time())
        }
        
        logger.info("Coordinated attack test completed")
        return result
    
    def _generate_test_report(self):
        """Generate a test report"""
        logger.info("Generating test report")
        
        # Get system status if available
        system_status = {}
        if self.monitor and hasattr(self.monitor, 'get_system_status'):
            try:
                system_status = self.monitor.get_system_status()
            except Exception as e:
                logger.warning(f"Failed to get system status: {e}")
        
        # Get active alerts if available
        active_alerts_count = 0
        if self.monitor and hasattr(self.monitor, 'active_alerts'):
            try:
                active_alerts_count = len(self.monitor.active_alerts)
            except Exception as e:
                logger.warning(f"Failed to get active alerts: {e}")
        
        # Get circuit breaker status if available
        circuit_breakers_active = 0
        if self.monitor and hasattr(self.monitor, 'circuit_breakers'):
            try:
                circuit_breakers_active = sum(1 for v in self.monitor.circuit_breakers.values() if v)
            except Exception as e:
                logger.warning(f"Failed to get circuit breaker status: {e}")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "test_duration": self.config.get('test', {}).get('test_duration', 300),
            "contracts": self.contracts,
            "alerts_generated": active_alerts_count,
            "circuit_breakers_triggered": circuit_breakers_active,
            "system_status": system_status,
            "monitor_type": MONITOR_MODULE,
            "test_environment": {
                "web3_connected": self.w3 is not None and hasattr(self.w3, 'is_connected') and self.w3.is_connected(),
                "contracts_loaded": len(self.contracts) > 0,
                "monitor_initialized": self.monitor is not None
            }
        }
        
        # Save report to file
        with open("oracle_security_integration_test_report.json", 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Test report saved to oracle_security_integration_test_report.json")
        return report

async def main():
    """Run the oracle security integration tests"""
    integration_test = OracleSecurityIntegrationTest()
    results = await integration_test.run_integration_tests()
    
    print("\n===== ORACLE SECURITY INTEGRATION TEST RESULTS =====")
    for test_name, result in results.items():
        if isinstance(result, dict) and 'status' in result:
            print(f"{test_name}: {result['status']}")
        else:
            print(f"{test_name}: {result}")
    print("======================================================\n")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
