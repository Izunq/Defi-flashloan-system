#!/usr/bin/env python3
"""
End-to-End Integration Test for Sentinel Agent System
This script tests the complete integration of all sentinel components:
- WebSocket Broadcasting
- Alert Routing
- Contract Interaction
- Monitoring Bridge
"""

import os
import sys
import time
import json
import logging
import unittest
import requests
import websocket
from web3 import Web3
from unittest.mock import patch, MagicMock

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sentinel_integration_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("sentinel_integration_test")

# Import sentinel components
try:
    from sentinel_coordinator import SentinelCoordinator
    from sentinel_websocket_broadcaster import SentinelWebSocketBroadcaster
    from sentinel_contract_manager import SentinelContractManager
    from emergency_action_executor import EmergencyActionExecutor
    from monitoring_bridge_orchestrator import MonitoringBridgeOrchestrator
    from oracle_sentinel import OracleSentinel
    from mev_sentinel import MEVSentinel
    from strategy_sentinel import StrategySentinel
except ImportError as e:
    logger.error(f"Failed to import sentinel components: {e}")
    sys.exit(1)

class SentinelIntegrationTest(unittest.TestCase):
    """Test suite for end-to-end sentinel integration testing"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests"""
        logger.info("Setting up sentinel integration test environment")
        
        # Load configuration
        try:
            with open("sentinel_config.yaml", "r") as f:
                import yaml
                cls.config = yaml.safe_load(f)
            
            with open("contract_abi_registry.json", "r") as f:
                cls.contract_registry = json.load(f)
                
            with open("alert_routing_config.yaml", "r") as f:
                import yaml
                cls.alert_config = yaml.safe_load(f)
                
            with open("unified_monitoring_config.yaml", "r") as f:
                import yaml
                cls.monitoring_config = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
            
        # Initialize mock components
        cls.web3 = MagicMock()
        cls.websocket_client = MagicMock()
        
        # Initialize sentinel components with mocks
        cls.contract_manager = SentinelContractManager(
            web3_provider=cls.web3,
            abi_registry_path="contract_abi_registry.json"
        )
        
        cls.websocket_broadcaster = SentinelWebSocketBroadcaster(
            websocket_url=cls.config["integration"]["websocket"]["endpoint"],
            reconnect_interval=cls.config["integration"]["websocket"]["reconnect_interval"]
        )
        
        # Replace actual websocket connection with mock
        cls.websocket_broadcaster.ws = cls.websocket_client
        
        # Initialize coordinator with mocked components
        cls.coordinator = SentinelCoordinator(
            contract_manager=cls.contract_manager,
            websocket_broadcaster=cls.websocket_broadcaster,
            config_path="sentinel_config.yaml"
        )
        
    def setUp(self):
        """Set up before each test"""
        # Reset mock call counts
        self.websocket_client.reset_mock()
        self.web3.reset_mock()
    
    def test_oracle_sentinel_alert_flow(self):
        """Test alert flow from Oracle Sentinel to all components"""
        logger.info("Testing Oracle Sentinel alert flow")
        
        # Create a mock oracle price deviation alert
        mock_alert = {
            "sentinel": "oracle_sentinel",
            "timestamp": time.time(),
            "severity": "HIGH",
            "title": "Oracle Price Deviation",
            "description": "ETH/USD price deviation of 5% detected",
            "data": {
                "asset": "ETH/USD",
                "expected_price": 2000.00,
                "actual_price": 2100.00,
                "deviation_percent": 5.0
            }
        }
        
        # Patch the alert detection method to return our mock alert
        with patch.object(OracleSentinel, 'detect_price_deviation', return_value=mock_alert):
            # Initialize oracle sentinel with mocked components
            oracle_sentinel = OracleSentinel(
                coordinator=self.coordinator,
                config_path="oracle_sentinel_config.yaml"
            )
            
            # Trigger the alert
            oracle_sentinel.run_single_check()
            
            # Verify alert was broadcasted to WebSocket
            self.websocket_client.send.assert_called_once()
            sent_data = json.loads(self.websocket_client.send.call_args[0][0])
            self.assertEqual(sent_data["sentinel"], "oracle_sentinel")
            self.assertEqual(sent_data["severity"], "HIGH")
            
            # Verify contract manager was not called (HIGH severity doesn't trigger contract action)
            self.web3.eth.contract.return_value.functions.emergencyPause.assert_not_called()
    
    def test_mev_sentinel_emergency_alert(self):
        """Test emergency alert from MEV Sentinel triggering contract pause"""
        logger.info("Testing MEV Sentinel emergency alert")
        
        # Create a mock MEV attack alert with EMERGENCY severity
        mock_alert = {
            "sentinel": "mev_sentinel",
            "timestamp": time.time(),
            "severity": "EMERGENCY",
            "title": "Sandwich Attack Detected",
            "description": "Large scale sandwich attack affecting multiple pools",
            "data": {
                "affected_pools": ["USDC/ETH", "DAI/ETH"],
                "attack_tx_hash": "0x1234567890abcdef",
                "estimated_loss": 50000.00
            }
        }
        
        # Patch the alert detection method to return our mock alert
        with patch.object(MEVSentinel, 'detect_sandwich_attacks', return_value=mock_alert):
            # Initialize MEV sentinel with mocked components
            mev_sentinel = MEVSentinel(
                coordinator=self.coordinator,
                config_path="mev_sentinel_config.yaml"
            )
            
            # Trigger the alert
            mev_sentinel.run_single_check()
            
            # Verify alert was broadcasted to WebSocket
            self.websocket_client.send.assert_called_once()
            
            # Verify contract manager was called to pause contracts
            # This verifies the emergency action executor was triggered
            self.web3.eth.contract.return_value.functions.emergencyPause.assert_called()
    
    def test_monitoring_bridge_data_flow(self):
        """Test data flow through monitoring bridge orchestrator"""
        logger.info("Testing monitoring bridge data flow")
        
        # Mock the legacy monitoring data
        mock_emergency_data = {
            "system_health": "degraded",
            "active_alerts": 3,
            "metrics": {
                "gas_price": 50,
                "network_congestion": "high"
            }
        }
        
        # Patch the adapter to return mock data
        with patch('emergency_monitoring_adapter.EmergencyMonitoringAdapter.get_data', 
                  return_value=mock_emergency_data):
            
            # Initialize monitoring bridge
            bridge = MonitoringBridgeOrchestrator(
                config_path="unified_monitoring_config.yaml"
            )
            
            # Get aggregated data
            aggregated_data = bridge.get_aggregated_monitoring_data()
            
            # Verify data was properly aggregated
            self.assertIn("emergency_monitoring", aggregated_data)
            self.assertEqual(
                aggregated_data["emergency_monitoring"]["system_health"], 
                "degraded"
            )
    
    def test_alert_delivery_validation(self):
        """Test alert delivery to all configured channels"""
        logger.info("Testing alert delivery validation")
        
        # Create a test alert
        test_alert = {
            "sentinel": "strategy_sentinel",
            "timestamp": time.time(),
            "severity": "CRITICAL",
            "title": "Strategy Performance Degradation",
            "description": "AI Strategy performance below threshold",
            "data": {
                "strategy_id": "AIStrategyV35",
                "expected_return": 0.05,
                "actual_return": 0.01
            }
        }
        
        # Mock the alert routing engine's send methods
        with patch('alert_routing_engine.AlertRoutingEngine.send_to_slack') as mock_slack, \
             patch('alert_routing_engine.AlertRoutingEngine.send_to_email') as mock_email, \
             patch('alert_routing_engine.AlertRoutingEngine.send_to_websocket') as mock_ws:
            
            # Initialize strategy sentinel with mocked components
            strategy_sentinel = StrategySentinel(
                coordinator=self.coordinator,
                config_path="strategy_sentinel_config.yaml"
            )
            
            # Process the alert through the coordinator
            self.coordinator.process_alert(test_alert)
            
            # Verify alert was routed to all expected channels for CRITICAL severity
            mock_ws.assert_called_once()
            mock_slack.assert_called_once()
            mock_email.assert_called_once()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        logger.info("Tearing down sentinel integration test environment")
        # Close any open connections
        try:
            cls.websocket_broadcaster.close()
        except:
            pass

if __name__ == "__main__":
    unittest.main()