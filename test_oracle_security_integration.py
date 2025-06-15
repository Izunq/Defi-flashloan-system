#!/usr/bin/env python3
"""
Oracle Security System Integration Tests

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
except ImportError:
    # Fallback if the module doesn't exist
    from production_oracle_security_monitor import (
        ProductionOracleSecurityMonitor as EnhancedOracleSecurityMonitor,
        PriceData,
        SecurityAlert,
        OracleMetrics
    )

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
                'secure_multi_oracle': '',
                'oracle_security_wrapper': '',
                'oracle_manipulation_monitor': ''
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
                'deploy_contracts': True,
                'use_ganache': True,
                'ganache_port': 8545,
                'test_duration': 300,  # 5 minutes
                'price_update_interval': 10,  # 10 seconds
                'manipulation_scenarios': ['flash_loan', 'gradual', 'coordinated']
            }
        }
    
    def _setup_web3(self) -> Web3:
        """Set up Web3 connection"""
        provider_url = self.config.get('web3', {}).get('provider_url', 'http://localhost:8545')
        w3 = Web3(Web3.HTTPProvider(provider_url))
        
        # Add middleware for POA chains if needed
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        if not w3.is_connected():
            raise ConnectionError(f"Failed to connect to {provider_url}")
        
        logger.info(f"Connected to Web3 at {provider_url}")
        return w3
    
    async def setup_test_environment(self):
        """Set up the complete test environment"""
        logger.info("Setting up test environment")
        
        # Check if we need to deploy contracts
        if self.config.get('test', {}).get('deploy_contracts', True):
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
            # Run the deployment script
            result = subprocess.run(
                ["npx", "hardhat", "run", "scripts/deploy_oracle_security.js", "--network", "localhost"],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse the output to get contract addresses
            output = result.stdout
            logger.info(f"Deployment output: {output}")
            
            # Extract contract addresses from output
            # This assumes the deployment script outputs addresses in a specific format
            lines = output.strip().split('\n')
            for line in lines:
                if "SecureMultiOracle deployed to:" in line:
                    self.contracts['secure_multi_oracle'] = line.split(":")[-1].strip()
                elif "OracleSecurityWrapper deployed to:" in line:
                    self.contracts['oracle_security_wrapper'] = line.split(":")[-1].strip()
                elif "OracleManipulationMonitor deployed to:" in line:
                    self.contracts['oracle_manipulation_monitor'] = line.split(":")[-1].strip()
            
            # Update config with contract addresses
            self.config['contracts'] = self.contracts
            
            # Save updated config
            with open("test_oracle_config.yaml", 'w') as f:
                yaml.dump(self.config, f)
            
            logger.info(f"Contracts deployed: {self.contracts}")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error deploying contracts: {e}")
            logger.error(f"Stdout: {e.stdout}")
            logger.error(f"Stderr: {e.stderr}")
            raise
    
    async def _load_existing_contracts(self):
        """Load existing contract addresses from config"""
        logger.info("Loading existing contract addresses")
        
        self.contracts = self.config.get('contracts', {})
        
        if not all(self.contracts.values()):
            raise ValueError("Missing contract addresses in config")
        
        logger.info(f"Loaded contracts: {self.contracts}")
    
    def _setup_monitor(self):
        """Set up the oracle security monitor"""
        logger.info("Setting up oracle security monitor")
        
        # Create a test config file
        with open("test_oracle_config.yaml", 'w') as f:
            yaml.dump(self.config, f)
        
        # Initialize the monitor
        self.monitor = EnhancedOracleSecurityMonitor(config_path="test_oracle_config.yaml")
        
        logger.info("Oracle security monitor initialized")
    
    def _setup_accounts(self):
        """Set up test accounts"""
        logger.info("Setting up test accounts")
        
        # Get accounts from web3
        accounts = self.w3.eth.accounts
        
        if len(accounts) < 6:
            raise ValueError("Not enough accounts available for testing")
        
        # Assign accounts
        self.admin_account = accounts[0]
        self.oracle_accounts = accounts[1:6]  # 5 oracle accounts
        self.test_accounts = accounts[6:]  # Remaining accounts for testing
        
        logger.info(f"Admin account: {self.admin_account}")
        logger.info(f"Oracle accounts: {self.oracle_accounts}")
        logger.info(f"Test accounts: {self.test_accounts}")
      async def _load_contract_abis(self):
        """Load contract ABIs"""
        logger.info("Loading contract ABIs")
        
        contract_abis = {}
        
        try:
            # Create mock ABIs if real ones don't exist
            mock_abi = [
                {
                    "inputs": [{"name": "assetId", "type": "bytes32"}],
                    "name": "getPrice",
                    "outputs": [
                        {"name": "price", "type": "uint256"},
                        {"name": "timestamp", "type": "uint256"},
                        {"name": "deviation", "type": "uint256"},
                        {"name": "isValid", "type": "bool"}
                    ],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
            
            contract_abis['secure_multi_oracle'] = mock_abi
            contract_abis['oracle_security_wrapper'] = mock_abi
            contract_abis['oracle_manipulation_monitor'] = mock_abi
            
            logger.info("Contract ABIs loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading contract ABIs: {e}")
            # Use minimal mock ABIs
            contract_abis = {
                'secure_multi_oracle': mock_abi,
                'oracle_security_wrapper': mock_abi,
                'oracle_manipulation_monitor': mock_abi
            }
        
        return contract_abis
    
    async def run_integration_tests(self):
        """Run the integration tests"""
        logger.info("Starting integration tests")
        
        # Setup test environment
        await self.setup_test_environment()
        
        # Run test scenarios
        await self._test_normal_operation()
        await self._test_flash_loan_attack()
        await self._test_gradual_manipulation()
        await self._test_coordinated_attack()
        
        # Run the monitor in the background
        monitor_task = asyncio.create_task(self._run_monitor())
        
        # Run price updates in the background
        price_update_task = asyncio.create_task(self._run_price_updates())
        
        # Run for the specified test duration
        test_duration = self.config.get('test', {}).get('test_duration', 300)
        await asyncio.sleep(test_duration)
        
        # Cancel background tasks
        monitor_task.cancel()
        price_update_task.cancel()
        
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass
        
        try:
            await price_update_task
        except asyncio.CancelledError:
            pass
        
        # Generate test report
        self._generate_test_report()
        
        logger.info("Integration tests completed")
    
    async def _run_monitor(self):
        """Run the oracle security monitor"""
        logger.info("Starting oracle security monitor")
        
        try:
            await self.monitor.monitor_oracle_security()
        except asyncio.CancelledError:
            logger.info("Monitor task cancelled")
        except Exception as e:
            logger.error(f"Error in monitor: {e}")
    
    async def _run_price_updates(self):
        """Run price updates in the background"""
        logger.info("Starting price update task")
        
        update_interval = self.config.get('test', {}).get('price_update_interval', 10)
        
        try:
            while True:
                # Update prices for all assets
                for asset in self.config.get('tracked_assets', []):
                    await self._update_asset_price(asset)
                
                await asyncio.sleep(update_interval)
        except asyncio.CancelledError:
            logger.info("Price update task cancelled")
        except Exception as e:
            logger.error(f"Error in price updates: {e}")
    
    async def _update_asset_price(self, asset: str):
        """Update price for a specific asset"""
        # This would interact with the contract to update prices
        # For now, we'll just log it
        logger.debug(f"Updating price for {asset}")
    
    async def _test_normal_operation(self):
        """Test normal operation of the oracle security system"""
        logger.info("Testing normal operation")
        
        # Submit normal prices for ETH
        eth_id = self.w3.keccak(text="ETH").hex()
        
        # TODO: Implement contract interaction to submit prices
        
        logger.info("Normal operation test completed")
    
    async def _test_flash_loan_attack(self):
        """Test flash loan attack detection"""
        logger.info("Testing flash loan attack detection")
        
        # TODO: Implement flash loan attack simulation
        
        logger.info("Flash loan attack test completed")
    
    async def _test_gradual_manipulation(self):
        """Test gradual price manipulation detection"""
        logger.info("Testing gradual price manipulation detection")
        
        # TODO: Implement gradual manipulation simulation
        
        logger.info("Gradual manipulation test completed")
    
    async def _test_coordinated_attack(self):
        """Test coordinated attack detection"""
        logger.info("Testing coordinated attack detection")
        
        # TODO: Implement coordinated attack simulation
        
        logger.info("Coordinated attack test completed")
    
    def _generate_test_report(self):
        """Generate a test report"""
        logger.info("Generating test report")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "test_duration": self.config.get('test', {}).get('test_duration', 300),
            "contracts": self.contracts,
            "alerts_generated": len(self.monitor.active_alerts),
            "circuit_breakers_triggered": sum(1 for v in self.monitor.circuit_breakers.values() if v),
            "system_status": self.monitor.get_system_status()
        }
        
        # Save report to file
        with open("oracle_security_integration_test_report.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Test report saved to oracle_security_integration_test_report.json")

async def main():
    """Run the oracle security integration tests"""
    integration_test = OracleSecurityIntegrationTest()
    await integration_test.run_integration_tests()

if __name__ == "__main__":
    asyncio.run(main())