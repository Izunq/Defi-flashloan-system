#!/usr/bin/env python3
"""
Sentinel Testing Framework
Provides comprehensive testing for the sentinel integration system
"""

import os
import sys
import time
import json
import yaml
import logging
import unittest
import threading
import requests
from typing import Dict, List, Any, Optional, Union
from unittest.mock import MagicMock, patch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sentinel_testing.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("sentinel_testing_framework")

class SentinelTestingFramework:
    """
    Comprehensive testing framework for the sentinel integration system
    - Unit tests for individual components
    - Integration tests for component interactions
    - End-to-end tests for full system functionality
    - Load tests for performance under stress
    - Mock services for external dependencies
    """
    
    def __init__(self, config_path="sentinel_config.yaml"):
        """
        Initialize the Sentinel Testing Framework
        
        Args:
            config_path: Path to the sentinel configuration file
        """
        self.config_path = config_path
        self.mock_services = {}
        self.test_results = {}
        
        # Load configuration
        self.load_config()
        
        logger.info("Sentinel Testing Framework initialized")
    
    def load_config(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, "r") as f:
                self.config = yaml.safe_load(f)
                
            logger.info(f"Loaded configuration from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self.config = {}
    
    def run_unit_tests(self):
        """Run unit tests for individual components"""
        logger.info("Running unit tests")
        
        # Create test suite
        suite = unittest.TestSuite()
        
        # Add test cases
        suite.addTest(unittest.makeSuite(SentinelCoordinatorTests))
        suite.addTest(unittest.makeSuite(AlertRoutingEngineTests))
        suite.addTest(unittest.makeSuite(SentinelContractManagerTests))
        suite.addTest(unittest.makeSuite(SentinelWebSocketBroadcasterTests))
        suite.addTest(unittest.makeSuite(AlertChannelManagerTests))
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Store results
        self.test_results["unit_tests"] = {
            "total": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped),
            "success": result.wasSuccessful()
        }
        
        logger.info(f"Unit tests completed: {result.testsRun} tests, {len(result.failures)} failures, {len(result.errors)} errors")
        
        return result.wasSuccessful()
    
    def run_integration_tests(self):
        """Run integration tests for component interactions"""
        logger.info("Running integration tests")
        
        # Create test suite
        suite = unittest.TestSuite()
        
        # Add test cases
        suite.addTest(unittest.makeSuite(SentinelIntegrationTests))
        suite.addTest(unittest.makeSuite(AlertRoutingIntegrationTests))
        suite.addTest(unittest.makeSuite(WebSocketIntegrationTests))
        suite.addTest(unittest.makeSuite(ContractInteractionIntegrationTests))
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Store results
        self.test_results["integration_tests"] = {
            "total": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped),
            "success": result.wasSuccessful()
        }
        
        logger.info(f"Integration tests completed: {result.testsRun} tests, {len(result.failures)} failures, {len(result.errors)} errors")
        
        return result.wasSuccessful()
    
    def run_end_to_end_tests(self):
        """Run end-to-end tests for full system functionality"""
        logger.info("Running end-to-end tests")
        
        # Start mock services
        self._start_mock_services()
        
        try:
            # Create test suite
            suite = unittest.TestSuite()
            
            # Add test cases
            suite.addTest(unittest.makeSuite(SentinelEndToEndTests))
            
            # Run tests
            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(suite)
            
            # Store results
            self.test_results["end_to_end_tests"] = {
                "total": result.testsRun,
                "failures": len(result.failures),
                "errors": len(result.errors),
                "skipped": len(result.skipped),
                "success": result.wasSuccessful()
            }
            
            logger.info(f"End-to-end tests completed: {result.testsRun} tests, {len(result.failures)} failures, {len(result.errors)} errors")
            
            return result.wasSuccessful()
        finally:
            # Stop mock services
            self._stop_mock_services()
    
    def run_load_tests(self):
        """Run load tests for performance under stress"""
        logger.info("Running load tests")
        
        # Start mock services
        self._start_mock_services()
        
        try:
            # Create test suite
            suite = unittest.TestSuite()
            
            # Add test cases
            suite.addTest(unittest.makeSuite(SentinelLoadTests))
            
            # Run tests
            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(suite)
            
            # Store results
            self.test_results["load_tests"] = {
                "total": result.testsRun,
                "failures": len(result.failures),
                "errors": len(result.errors),
                "skipped": len(result.skipped),
                "success": result.wasSuccessful()
            }
            
            logger.info(f"Load tests completed: {result.testsRun} tests, {len(result.failures)} failures, {len(result.errors)} errors")
            
            return result.wasSuccessful()
        finally:
            # Stop mock services
            self._stop_mock_services()
    
    def _start_mock_services(self):
        """Start mock services for testing"""
        logger.info("Starting mock services")
        
        # Start mock Web3 provider
        self.mock_services["web3"] = MockWeb3Service()
        self.mock_services["web3"].start()
        
        # Start mock WebSocket server
        self.mock_services["websocket"] = MockWebSocketService()
        self.mock_services["websocket"].start()
        
        # Start mock SMTP server
        self.mock_services["smtp"] = MockSMTPService()
        self.mock_services["smtp"].start()
        
        # Start mock HTTP server
        self.mock_services["http"] = MockHTTPService()
        self.mock_services["http"].start()
        
        logger.info("Mock services started")
    
    def _stop_mock_services(self):
        """Stop mock services"""
        logger.info("Stopping mock services")
        
        for service_name, service in self.mock_services.items():
            try:
                service.stop()
                logger.info(f"Stopped {service_name} service")
            except Exception as e:
                logger.error(f"Error stopping {service_name} service: {e}")
                
        self.mock_services = {}
        
        logger.info("Mock services stopped")
    
    def run_all_tests(self):
        """Run all tests"""
        logger.info("Running all tests")
        
        # Run unit tests
        unit_success = self.run_unit_tests()
        
        # Run integration tests
        integration_success = self.run_integration_tests()
        
        # Run end-to-end tests
        e2e_success = self.run_end_to_end_tests()
        
        # Run load tests
        load_success = self.run_load_tests()
        
        # Overall success
        success = unit_success and integration_success and e2e_success and load_success
        
        # Store overall results
        self.test_results["overall"] = {
            "unit_tests": unit_success,
            "integration_tests": integration_success,
            "end_to_end_tests": e2e_success,
            "load_tests": load_success,
            "success": success
        }
        
        logger.info(f"All tests completed: {'SUCCESS' if success else 'FAILURE'}")
        
        return success
    
    def generate_report(self, output_file="sentinel_test_report.json"):
        """
        Generate a test report
        
        Args:
            output_file: Output file path
        """
        logger.info("Generating test report")
        
        # Create report
        report = {
            "timestamp": time.time(),
            "results": self.test_results,
            "summary": {
                "total_tests": sum(r.get("total", 0) for r in self.test_results.values() if isinstance(r, dict) and "total" in r),
                "total_failures": sum(r.get("failures", 0) for r in self.test_results.values() if isinstance(r, dict) and "failures" in r),
                "total_errors": sum(r.get("errors", 0) for r in self.test_results.values() if isinstance(r, dict) and "errors" in r),
                "success": self.test_results.get("overall", {}).get("success", False)
            }
        }
        
        # Write report to file
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"Test report generated: {output_file}")
        
        return report

# Mock services for testing

class MockWeb3Service:
    """Mock Web3 service for testing"""
    
    def __init__(self, port=8545):
        """
        Initialize the Mock Web3 service
        
        Args:
            port: Port to listen on
        """
        self.port = port
        self.server = None
        self.thread = None
        self.running = False
    
    def start(self):
        """Start the mock service"""
        self.running = True
        self.thread = threading.Thread(target=self._run_server)
        self.thread.daemon = True
        self.thread.start()
    
    def _run_server(self):
        """Run the mock server"""
        # In a real implementation, this would start a mock Ethereum node
        # For this example, we'll just simulate it
        logger.info(f"Mock Web3 service running on port {self.port}")
        
        while self.running:
            time.sleep(0.1)
    
    def stop(self):
        """Stop the mock service"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)

class MockWebSocketService:
    """Mock WebSocket service for testing"""
    
    def __init__(self, port=8080):
        """
        Initialize the Mock WebSocket service
        
        Args:
            port: Port to listen on
        """
        self.port = port
        self.server = None
        self.thread = None
        self.running = False
        self.clients = []
        self.messages = []
    
    def start(self):
        """Start the mock service"""
        self.running = True
        self.thread = threading.Thread(target=self._run_server)
        self.thread.daemon = True
        self.thread.start()
    
    def _run_server(self):
        """Run the mock server"""
        # In a real implementation, this would start a WebSocket server
        # For this example, we'll just simulate it
        logger.info(f"Mock WebSocket service running on port {self.port}")
        
        while self.running:
            time.sleep(0.1)
    
    def broadcast(self, message):
        """
        Broadcast a message to all clients
        
        Args:
            message: Message to broadcast
        """
        self.messages.append(message)
    
    def stop(self):
        """Stop the mock service"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)

class MockSMTPService:
    """Mock SMTP service for testing"""
    
    def __init__(self, port=1025):
        """
        Initialize the Mock SMTP service
        
        Args:
            port: Port to listen on
        """
        self.port = port
        self.server = None
        self.thread = None
        self.running = False
        self.messages = []
    
    def start(self):
        """Start the mock service"""
        self.running = True
        self.thread = threading.Thread(target=self._run_server)
        self.thread.daemon = True
        self.thread.start()
    
    def _run_server(self):
        """Run the mock server"""
        # In a real implementation, this would start an SMTP server
        # For this example, we'll just simulate it
        logger.info(f"Mock SMTP service running on port {self.port}")
        
        while self.running:
            time.sleep(0.1)
    
    def stop(self):
        """Stop the mock service"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)

class MockHTTPService:
    """Mock HTTP service for testing"""
    
    def __init__(self, port=8081):
        """
        Initialize the Mock HTTP service
        
        Args:
            port: Port to listen on
        """
        self.port = port
        self.server = None
        self.thread = None
        self.running = False
        self.requests = []
        self.responses = {}
    
    def start(self):
        """Start the mock service"""
        self.running = True
        self.thread = threading.Thread(target=self._run_server)
        self.thread.daemon = True
        self.thread.start()
    
    def _run_server(self):
        """Run the mock server"""
        # In a real implementation, this would start an HTTP server
        # For this example, we'll just simulate it
        logger.info(f"Mock HTTP service running on port {self.port}")
        
        while self.running:
            time.sleep(0.1)
    
    def add_response(self, path, response, status_code=200):
        """
        Add a mock response
        
        Args:
            path: URL path
            response: Response data
            status_code: HTTP status code
        """
        self.responses[path] = {
            "data": response,
            "status_code": status_code
        }
    
    def stop(self):
        """Stop the mock service"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)

# Test cases

class SentinelCoordinatorTests(unittest.TestCase):
    """Unit tests for SentinelCoordinator"""
    
    def setUp(self):
        """Set up test case"""
        # Mock dependencies
        self.mock_contract_manager = MagicMock()
        self.mock_websocket_broadcaster = MagicMock()
        
        # Import SentinelCoordinator
        from sentinel_coordinator import SentinelCoordinator
        
        # Create coordinator
        self.coordinator = SentinelCoordinator(
            contract_manager=self.mock_contract_manager,
            websocket_broadcaster=self.mock_websocket_broadcaster,
            config_path="sentinel_config.yaml"
        )
    
    def test_process_alert(self):
        """Test processing an alert"""
        # Create test alert
        alert = {
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
        
        # Process alert
        self.coordinator.process_alert(alert)
        
        # Check that WebSocket broadcaster was called
        self.mock_websocket_broadcaster.broadcast_alert.assert_called_once()
    
    def test_emergency_action(self):
        """Test emergency action execution"""
        # Create test alert with EMERGENCY severity
        alert = {
            "sentinel": "oracle_sentinel",
            "timestamp": time.time(),
            "severity": "EMERGENCY",
            "title": "Oracle Price Manipulation",
            "description": "ETH/USD price manipulation detected",
            "data": {
                "asset": "ETH/USD",
                "expected_price": 2000.00,
                "actual_price": 2500.00,
                "deviation_percent": 25.0
            }
        }
        
        # Process alert
        self.coordinator.process_alert(alert)
        
        # Check that contract manager was called to pause contracts
        self.mock_contract_manager.pause_contract.assert_called()
    
    def test_shared_state(self):
        """Test shared state management"""
        # Set shared state
        self.coordinator.set_shared_state("test_key", "test_value")
        
        # Get shared state
        value = self.coordinator.get_shared_state("test_key")
        
        # Check value
        self.assertEqual(value, "test_value")
    
    def tearDown(self):
        """Clean up after test"""
        self.coordinator.shutdown()

class AlertRoutingEngineTests(unittest.TestCase):
    """Unit tests for AlertRoutingEngine"""
    
    def setUp(self):
        """Set up test case"""
        # Import AlertRoutingEngine
        from alert_routing_engine import AlertRoutingEngine
        
        # Create engine
        self.engine = AlertRoutingEngine(config_path="alert_routing_config.yaml")
        
        # Mock methods
        self.engine.send_to_websocket = MagicMock()
        self.engine.send_to_slack = MagicMock()
        self.engine.send_to_email = MagicMock()
        self.engine.send_to_sms = MagicMock()
        self.engine.send_to_webhook = MagicMock()
    
    def test_route_alert(self):
        """Test routing an alert"""
        # Create test alert
        alert = {
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
        
        # Route alert
        self.engine.route_alert(alert)
        
        # Check that WebSocket method was called
        self.engine.send_to_websocket.assert_called_once()
    
    def test_deduplication(self):
        """Test alert deduplication"""
        # Create test alert
        alert = {
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
        
        # Route alert twice
        self.engine.route_alert(alert)
        
        # Reset mock
        self.engine.send_to_websocket.reset_mock()
        
        # Route same alert again
        self.engine.route_alert(alert)
        
        # Check that WebSocket method was not called again
        self.engine.send_to_websocket.assert_not_called()
    
    def test_throttling(self):
        """Test alert throttling"""
        # Create test alert
        alert1 = {
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
        
        # Create second alert with same sentinel and severity
        alert2 = {
            "sentinel": "oracle_sentinel",
            "timestamp": time.time() + 1,
            "severity": "HIGH",
            "title": "Oracle Price Deviation",
            "description": "ETH/USD price deviation of 6% detected",
            "data": {
                "asset": "ETH/USD",
                "expected_price": 2000.00,
                "actual_price": 2120.00,
                "deviation_percent": 6.0
            }
        }
        
        # Mock throttle time
        self.engine._should_throttle_alert = lambda a, c: c == "slack"
        
        # Route first alert
        self.engine.route_alert(alert1)
        
        # Check that WebSocket and Email methods were called but Slack was throttled
        self.engine.send_to_websocket.assert_called_once()
        self.engine.send_to_slack.assert_not_called()
    
    def tearDown(self):
        """Clean up after test"""
        self.engine.shutdown()

class SentinelContractManagerTests(unittest.TestCase):
    """Unit tests for SentinelContractManager"""
    
    def setUp(self):
        """Set up test case"""
        # Import SentinelContractManager
        from sentinel_contract_manager import SentinelContractManager
        
        # Mock Web3
        with patch("sentinel_contract_manager.Web3") as mock_web3:
            # Create manager
            self.manager = SentinelContractManager(
                web3_provider="http://localhost:8545",
                abi_registry_path="contract_abi_registry.json"
            )
            
            # Store mock
            self.mock_web3 = mock_web3
    
    def test_pause_contract(self):
        """Test pausing a contract"""
        # Mock contract
        mock_contract = MagicMock()
        self.manager.get_contract = MagicMock(return_value=mock_contract)
        
        # Pause contract
        self.manager.pause_contract("arbitrage_executor")
        
        # Check that contract method was called
        mock_contract.functions.emergencyPause.assert_called_once()
    
    def test_unpause_contract(self):
        """Test unpausing a contract"""
        # Mock contract
        mock_contract = MagicMock()
        self.manager.get_contract = MagicMock(return_value=mock_contract)
        
        # Unpause contract
        self.manager.unpause_contract("arbitrage_executor")
        
        # Check that contract method was called
        mock_contract.functions.emergencyUnpause.assert_called_once()
    
    def tearDown(self):
        """Clean up after test"""
        pass

class SentinelWebSocketBroadcasterTests(unittest.TestCase):
    """Unit tests for SentinelWebSocketBroadcaster"""
    
    def setUp(self):
        """Set up test case"""
        # Import SentinelWebSocketBroadcaster
        from sentinel_websocket_broadcaster import SentinelWebSocketBroadcaster
        
        # Mock WebSocket
        with patch("sentinel_websocket_broadcaster.websocket.create_connection") as mock_create_connection:
            # Create broadcaster
            self.broadcaster = SentinelWebSocketBroadcaster(
                websocket_url="ws://localhost:8080",
                reconnect_interval=5
            )
            
            # Store mock
            self.mock_create_connection = mock_create_connection
    
    def test_broadcast_alert(self):
        """Test broadcasting an alert"""
        # Create test alert
        alert = {
            "sentinel": "oracle_sentinel",
            "timestamp": time.time(),
            "severity": "HIGH",
            "title": "Oracle Price Deviation",
            "description": "ETH/USD price deviation of 5% detected"
        }
        
        # Mock WebSocket
        mock_ws = MagicMock()
        self.broadcaster.ws = mock_ws
        self.broadcaster.connected = True
        
        # Broadcast alert
        self.broadcaster.broadcast_alert(alert)
        
        # Check that WebSocket send was called
        mock_ws.send.assert_called_once()
    
    def test_reconnect(self):
        """Test reconnection logic"""
        # Mock WebSocket
        mock_ws = MagicMock()
        self.mock_create_connection.return_value = mock_ws
        
        # Simulate disconnection
        self.broadcaster.connected = False
        
        # Trigger reconnect
        self.broadcaster._reconnect()
        
        # Check that connection was attempted
        self.mock_create_connection.assert_called_once()
    
    def tearDown(self):
        """Clean up after test"""
        self.broadcaster.close()

class AlertChannelManagerTests(unittest.TestCase):
    """Unit tests for alert channel managers"""
    
    def setUp(self):
        """Set up test case"""
        # Import alert channel managers
        from email_alert_manager import EmailAlertManager
        from slack_alert_manager import SlackAlertManager
        from sms_alert_manager import SMSAlertManager
        from webhook_alert_manager import WebhookAlertManager
        
        # Create managers
        self.email_manager = EmailAlertManager(config_path="alert_routing_config.yaml")
        self.slack_manager = SlackAlertManager(config_path="alert_routing_config.yaml")
        self.sms_manager = SMSAlertManager(config_path="alert_routing_config.yaml")
        self.webhook_manager = WebhookAlertManager(config_path="alert_routing_config.yaml")
        
        # Mock methods
        self.email_manager._check_rate_limit = MagicMock(return_value=True)
        self.slack_manager._check_rate_limit = MagicMock(return_value=True)
        self.sms_manager._check_rate_limit = MagicMock(return_value=True)
        self.webhook_manager._check_rate_limit = MagicMock(return_value=True)
        
        # Create test alert
        self.test_alert = {
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
    
    def test_email_alert_manager(self):
        """Test EmailAlertManager"""
        # Mock SMTP
        with patch("email_alert_manager.smtplib.SMTP") as mock_smtp:
            # Mock SMTP instance
            mock_smtp_instance = MagicMock()
            mock_smtp.return_value = mock_smtp_instance
            
            # Override config
            self.email_manager.config = {
                "enabled": True,
                "smtp_server": "localhost",
                "smtp_port": 25,
                "username": "test",
                "password": "test",
                "from_address": "test@example.com",
                "to_addresses": ["recipient@example.com"]
            }
            
            # Send alert
            result = self.email_manager.send_alert(self.test_alert)
            
            # Check result
            self.assertTrue(result)
            
            # Check that SMTP methods were called
            mock_smtp_instance.starttls.assert_called_once()
            mock_smtp_instance.login.assert_called_once()
            mock_smtp_instance.send_message.assert_called_once()
            mock_smtp_instance.quit.assert_called_once()
    
    def test_slack_alert_manager(self):
        """Test SlackAlertManager"""
        # Mock requests
        with patch("slack_alert_manager.requests.post") as mock_post:
            # Mock response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            # Override config
            self.slack_manager.config = {
                "enabled": True,
                "webhook_url": "https://hooks.slack.com/services/xxx/yyy/zzz"
            }
            
            # Send alert
            result = self.slack_manager.send_alert(self.test_alert)
            
            # Check result
            self.assertTrue(result)
            
            # Check that requests.post was called
            mock_post.assert_called_once()
    
    def test_webhook_alert_manager(self):
        """Test WebhookAlertManager"""
        # Mock requests
        with patch("webhook_alert_manager.requests.post") as mock_post:
            # Mock response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            # Override config
            self.webhook_manager.config = {
                "enabled": True,
                "url": "https://example.com/webhook",
                "method": "POST",
                "headers": {"Content-Type": "application/json"}
            }
            
            # Send alert
            result = self.webhook_manager.send_alert(self.test_alert)
            
            # Check result
            self.assertTrue(result)
            
            # Check that requests.post was called
            mock_post.assert_called_once()
    
    def tearDown(self):
        """Clean up after test"""
        self.email_manager.shutdown()
        self.slack_manager.shutdown()
        self.sms_manager.shutdown()
        self.webhook_manager.shutdown()

class SentinelIntegrationTests(unittest.TestCase):
    """Integration tests for sentinel components"""
    
    def setUp(self):
        """Set up test case"""
        # Import components
        from sentinel_coordinator import SentinelCoordinator
        from alert_routing_engine import AlertRoutingEngine
        from sentinel_contract_manager import SentinelContractManager
        from sentinel_websocket_broadcaster import SentinelWebSocketBroadcaster
        
        # Mock Web3
        with patch("sentinel_contract_manager.Web3") as mock_web3:
            # Create contract manager
            self.contract_manager = SentinelContractManager(
                web3_provider="http://localhost:8545",
                abi_registry_path="contract_abi_registry.json"
            )
        
        # Mock WebSocket
        with patch("sentinel_websocket_broadcaster.websocket.create_connection") as mock_create_connection:
            # Create broadcaster
            self.websocket_broadcaster = SentinelWebSocketBroadcaster(
                websocket_url="ws://localhost:8080",
                reconnect_interval=5
            )
        
        # Create alert routing engine
        self.alert_routing_engine = AlertRoutingEngine(config_path="alert_routing_config.yaml")
        
        # Mock methods
        self.alert_routing_engine.send_to_websocket = MagicMock()
        self.alert_routing_engine.send_to_slack = MagicMock()
        self.alert_routing_engine.send_to_email = MagicMock()
        
        # Create coordinator
        self.coordinator = SentinelCoordinator(
            contract_manager=self.contract_manager,
            websocket_broadcaster=self.websocket_broadcaster,
            config_path="sentinel_config.yaml"
        )
        
        # Set alert routing engine
        self.coordinator.alert_routing_engine = self.alert_routing_engine
    
    def test_alert_flow(self):
        """Test alert flow through the system"""
        # Create test alert
        alert = {
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
        
        # Process alert
        self.coordinator.process_alert(alert)
        
        # Check that alert was routed
        self.alert_routing_engine.send_to_websocket.assert_called_once()
    
    def test_emergency_flow(self):
        """Test emergency alert flow"""
        # Mock contract manager
        self.contract_manager.pause_contract = MagicMock()
        
        # Create test alert with EMERGENCY severity
        alert = {
            "sentinel": "oracle_sentinel",
            "timestamp": time.time(),
            "severity": "EMERGENCY",
            "title": "Oracle Price Manipulation",
            "description": "ETH/USD price manipulation detected",
            "data": {
                "asset": "ETH/USD",
                "expected_price": 2000.00,
                "actual_price": 2500.00,
                "deviation_percent": 25.0
            }
        }
        
        # Process alert
        self.coordinator.process_alert(alert)
        
        # Check that contract was paused
        self.contract_manager.pause_contract.assert_called()
        
        # Check that alert was routed
        self.alert_routing_engine.send_to_websocket.assert_called_once()
    
    def tearDown(self):
        """Clean up after test"""
        self.coordinator.shutdown()
        self.alert_routing_engine.shutdown()
        self.websocket_broadcaster.close()

class AlertRoutingIntegrationTests(unittest.TestCase):
    """Integration tests for alert routing"""
    
    def setUp(self):
        """Set up test case"""
        # Import components
        from alert_routing_engine import AlertRoutingEngine
        from email_alert_manager import EmailAlertManager
        from slack_alert_manager import SlackAlertManager
        
        # Create alert routing engine
        self.alert_routing_engine = AlertRoutingEngine(config_path="alert_routing_config.yaml")
        
        # Create alert managers
        self.email_manager = EmailAlertManager(config_path="alert_routing_config.yaml")
        self.slack_manager = SlackAlertManager(config_path="alert_routing_config.yaml")
        
        # Mock methods
        self.alert_routing_engine.send_to_websocket = MagicMock()
        self.alert_routing_engine.send_to_slack = MagicMock()
        self.alert_routing_engine.send_to_email = MagicMock()
        
        self.email_manager.send_alert = MagicMock(return_value=True)
        self.slack_manager.send_alert = MagicMock(return_value=True)
    
    def test_routing_by_severity(self):
        """Test routing based on severity"""
        # Create test alerts with different severities
        low_alert = {
            "sentinel": "oracle_sentinel",
            "timestamp": time.time(),
            "severity": "LOW",
            "title": "Oracle Price Deviation",
            "description": "ETH/USD price deviation of 1% detected"
        }
        
        high_alert = {
            "sentinel": "oracle_sentinel",
            "timestamp": time.time(),
            "severity": "HIGH",
            "title": "Oracle Price Deviation",
            "description": "ETH/USD price deviation of 5% detected"
        }
        
        critical_alert = {
            "sentinel": "oracle_sentinel",
            "timestamp": time.time(),
            "severity": "CRITICAL",
            "title": "Oracle Price Deviation",
            "description": "ETH/USD price deviation of 10% detected"
        }
        
        # Route alerts
        self.alert_routing_engine.route_alert(low_alert)
        self.alert_routing_engine.route_alert(high_alert)
        self.alert_routing_engine.route_alert(critical_alert)
        
        # Check routing
        # Low severity should only go to WebSocket
        self.assertEqual(self.alert_routing_engine.send_to_websocket.call_count, 3)
        
        # High severity should go to WebSocket and Slack
        self.assertEqual(self.alert_routing_engine.send_to_slack.call_count, 2)
        
        # Critical severity should go to all channels
        self.assertEqual(self.alert_routing_engine.send_to_email.call_count, 1)
    
    def test_batch_alerts(self):
        """Test batching alerts"""
        # Override batch settings
        self.alert_routing_engine.config = {
            "global_settings": {
                "batch_size": 3,
                "batch_timeout": 30
            },
            "routing_rules": {
                "oracle_sentinel": {
                    "LOW": {
                        "batch_enabled": True,
                        "channels": ["websocket"]
                    }
                }
            }
        }
        
        # Create test alerts
        alerts = []
        for i in range(5):
            alert = {
                "alert_id": f"oracle-{i}",
                "sentinel": "oracle_sentinel",
                "timestamp": time.time() + i,
                "severity": "LOW",
                "title": f"Oracle Price Deviation {i}",
                "description": f"ETH/USD price deviation of {i}% detected"
            }
            alerts.append(alert)
        
        # Add to batch queue
        for alert in alerts[:3]:
            self.alert_routing_engine._add_to_batch_queue(alert, ["websocket"])
            
        # Send batch
        self.alert_routing_engine._send_batch("oracle_sentinel_LOW")
        
        # Check that batch was sent
        self.alert_routing_engine.send_to_websocket.assert_called_once()
    
    def tearDown(self):
        """Clean up after test"""
        self.alert_routing_engine.shutdown()
        self.email_manager.shutdown()
        self.slack_manager.shutdown()

class WebSocketIntegrationTests(unittest.TestCase):
    """Integration tests for WebSocket communication"""
    
    def setUp(self):
        """Set up test case"""
        # Import components
        from sentinel_websocket_broadcaster import SentinelWebSocketBroadcaster
        
        # Mock WebSocket
        with patch("sentinel_websocket_broadcaster.websocket.create_connection") as mock_create_connection:
            # Create mock WebSocket
            self.mock_ws = MagicMock()
            mock_create_connection.return_value = self.mock_ws
            
            # Create broadcaster
            self.broadcaster = SentinelWebSocketBroadcaster(
                websocket_url="ws://localhost:8080",
                reconnect_interval=5
            )
    
    def test_alert_broadcast(self):
        """Test broadcasting alerts"""
        # Create test alert
        alert = {
            "sentinel": "oracle_sentinel",
            "timestamp": time.time(),
            "severity": "HIGH",
            "title": "Oracle Price Deviation",
            "description": "ETH/USD price deviation of 5% detected"
        }
        
        # Broadcast alert
        self.broadcaster.broadcast_alert(alert)
        
        # Check that WebSocket send was called
        self.mock_ws.send.assert_called_once()
        
        # Check message format
        call_args = self.mock_ws.send.call_args[0][0]
        self.assertIn("oracle_sentinel", call_args)
        self.assertIn("HIGH", call_args)
        self.assertIn("Oracle Price Deviation", call_args)
    
    def test_reconnection(self):
        """Test reconnection logic"""
        # Simulate disconnection
        self.broadcaster.connected = False
        
        # Create mock WebSocket for reconnection
        new_mock_ws = MagicMock()
        with patch("sentinel_websocket_broadcaster.websocket.create_connection", return_value=new_mock_ws):
            # Trigger reconnect
            self.broadcaster._reconnect()
            
            # Check that new connection was established
            self.assertTrue(self.broadcaster.connected)
            self.assertEqual(self.broadcaster.ws, new_mock_ws)
    
    def tearDown(self):
        """Clean up after test"""
        self.broadcaster.close()

class ContractInteractionIntegrationTests(unittest.TestCase):
    """Integration tests for contract interactions"""
    
    def setUp(self):
        """Set up test case"""
        # Import components
        from sentinel_contract_manager import SentinelContractManager
        
        # Mock Web3
        with patch("sentinel_contract_manager.Web3") as mock_web3:
            # Create mock contract
            self.mock_contract = MagicMock()
            
            # Mock functions
            mock_functions = MagicMock()
            mock_emergencyPause = MagicMock()
            mock_emergencyUnpause = MagicMock()
            
            # Set up function call chain
            mock_functions.emergencyPause.return_value = mock_emergencyPause
            mock_functions.emergencyUnpause.return_value = mock_emergencyUnpause
            
            # Set up contract
            self.mock_contract.functions = mock_functions
            
            # Create manager
            self.manager = SentinelContractManager(
                web3_provider="http://localhost:8545",
                abi_registry_path="contract_abi_registry.json"
            )
            
            # Mock get_contract
            self.manager.get_contract = MagicMock(return_value=self.mock_contract)
    
    def test_pause_contract(self):
        """Test pausing a contract"""
        # Pause contract
        self.manager.pause_contract("arbitrage_executor")
        
        # Check that contract function was called
        self.mock_contract.functions.emergencyPause.assert_called_once()
    
    def test_unpause_contract(self):
        """Test unpausing a contract"""
        # Unpause contract
        self.manager.unpause_contract("arbitrage_executor")
        
        # Check that contract function was called
        self.mock_contract.functions.emergencyUnpause.assert_called_once()
    
    def test_execute_transaction(self):
        """Test executing a custom transaction"""
        # Mock transaction
        mock_tx = MagicMock()
        self.mock_contract.functions.customFunction.return_value = mock_tx
        
        # Execute transaction
        self.manager.execute_transaction("arbitrage_executor", "customFunction", [123, "test"])
        
        # Check that contract function was called
        self.mock_contract.functions.customFunction.assert_called_once_with(123, "test")
    
    def tearDown(self):
        """Clean up after test"""
        pass

class SentinelEndToEndTests(unittest.TestCase):
    """End-to-end tests for the sentinel system"""
    
    def setUp(self):
        """Set up test case"""
        # Import components
        from sentinel_coordinator import SentinelCoordinator
        from alert_routing_engine import AlertRoutingEngine
        from sentinel_contract_manager import SentinelContractManager
        from sentinel_websocket_broadcaster import SentinelWebSocketBroadcaster
        
        # Mock Web3
        with patch("sentinel_contract_manager.Web3") as mock_web3:
            # Create contract manager
            self.contract_manager = SentinelContractManager(
                web3_provider="http://localhost:8545",
                abi_registry_path="contract_abi_registry.json"
            )
        
        # Mock WebSocket
        with patch("sentinel_websocket_broadcaster.websocket.create_connection") as mock_create_connection:
            # Create broadcaster
            self.websocket_broadcaster = SentinelWebSocketBroadcaster(
                websocket_url="ws://localhost:8080",
                reconnect_interval=5
            )
        
        # Create alert routing engine
        self.alert_routing_engine = AlertRoutingEngine(config_path="alert_routing_config.yaml")
        
        # Mock methods
        self.alert_routing_engine.send_to_websocket = MagicMock()
        self.alert_routing_engine.send_to_slack = MagicMock()
        self.alert_routing_engine.send_to_email = MagicMock()
        
        # Create coordinator
        self.coordinator = SentinelCoordinator(
            contract_manager=self.contract_manager,
            websocket_broadcaster=self.websocket_broadcaster,
            config_path="sentinel_config.yaml"
        )
        
        # Set alert routing engine
        self.coordinator.alert_routing_engine = self.alert_routing_engine
    
    def test_end_to_end_flow(self):
        """Test end-to-end alert flow"""
        # Mock contract manager
        self.contract_manager.pause_contract = MagicMock()
        
        # Create test alerts with different severities
        alerts = [
            {
                "sentinel": "oracle_sentinel",
                "timestamp": time.time(),
                "severity": "LOW",
                "title": "Oracle Price Deviation",
                "description": "ETH/USD price deviation of 1% detected",
                "data": {
                    "asset": "ETH/USD",
                    "expected_price": 2000.00,
                    "actual_price": 2020.00,
                    "deviation_percent": 1.0
                }
            },
            {
                "sentinel": "mev_sentinel",
                "timestamp": time.time(),
                "severity": "HIGH",
                "title": "MEV Attack Detected",
                "description": "Sandwich attack detected on ETH/USDC pair",
                "data": {
                    "pair": "ETH/USDC",
                    "attack_type": "sandwich",
                    "profit": 0.5,
                    "attacker": "0x1234..."
                }
            },
            {
                "sentinel": "oracle_sentinel",
                "timestamp": time.time(),
                "severity": "CRITICAL",
                "title": "Oracle Price Manipulation",
                "description": "ETH/USD price manipulation detected",
                "data": {
                    "asset": "ETH/USD",
                    "expected_price": 2000.00,
                    "actual_price": 2300.00,
                    "deviation_percent": 15.0
                }
            }
        ]
        
        # Process alerts
        for alert in alerts:
            self.coordinator.process_alert(alert)
        
        # Check WebSocket broadcasts
        self.assertEqual(self.alert_routing_engine.send_to_websocket.call_count, 3)
        
        # Check Slack alerts
        self.assertEqual(self.alert_routing_engine.send_to_slack.call_count, 2)
        
        # Check Email alerts
        self.assertEqual(self.alert_routing_engine.send_to_email.call_count, 1)
        
        # Check contract pauses
        self.contract_manager.pause_contract.assert_called()
    
    def tearDown(self):
        """Clean up after test"""
        self.coordinator.shutdown()
        self.alert_routing_engine.shutdown()
        self.websocket_broadcaster.close()

class SentinelLoadTests(unittest.TestCase):
    """Load tests for the sentinel system"""
    
    def setUp(self):
        """Set up test case"""
        # Import components
        from sentinel_coordinator import SentinelCoordinator
        from alert_routing_engine import AlertRoutingEngine
        from sentinel_contract_manager import SentinelContractManager
        from sentinel_websocket_broadcaster import SentinelWebSocketBroadcaster
        
        # Mock Web3
        with patch("sentinel_contract_manager.Web3") as mock_web3:
            # Create contract manager
            self.contract_manager = SentinelContractManager(
                web3_provider="http://localhost:8545",
                abi_registry_path="contract_abi_registry.json"
            )
        
        # Mock WebSocket
        with patch("sentinel_websocket_broadcaster.websocket.create_connection") as mock_create_connection:
            # Create broadcaster
            self.websocket_broadcaster = SentinelWebSocketBroadcaster(
                websocket_url="ws://localhost:8080",
                reconnect_interval=5
            )
        
        # Create alert routing engine
        self.alert_routing_engine = AlertRoutingEngine(config_path="alert_routing_config.yaml")
        
        # Mock methods
        self.alert_routing_engine.send_to_websocket = MagicMock()
        self.alert_routing_engine.send_to_slack = MagicMock()
        self.alert_routing_engine.send_to_email = MagicMock()
        
        # Create coordinator
        self.coordinator = SentinelCoordinator(
            contract_manager=self.contract_manager,
            websocket_broadcaster=self.websocket_broadcaster,
            config_path="sentinel_config.yaml"
        )
        
        # Set alert routing engine
        self.coordinator.alert_routing_engine = self.alert_routing_engine
    
    def test_high_volume_alerts(self):
        """Test handling high volume of alerts"""
        # Create test alerts
        alerts = []
        for i in range(100):
            alert = {
                "alert_id": f"test-{i}",
                "sentinel": "oracle_sentinel" if i % 3 == 0 else "mev_sentinel" if i % 3 == 1 else "strategy_sentinel",
                "timestamp": time.time() + i,
                "severity": "LOW" if i % 5 < 3 else "MEDIUM" if i % 5 == 3 else "HIGH",
                "title": f"Test Alert {i}",
                "description": f"This is test alert {i}",
                "data": {
                    "test_id": i,
                    "value": i * 10
                }
            }
            alerts.append(alert)
        
        # Process alerts and measure time
        start_time = time.time()
        
        for alert in alerts:
            self.coordinator.process_alert(alert)
            
        end_time = time.time()
        
        # Calculate processing time
        processing_time = end_time - start_time
        alerts_per_second = len(alerts) / processing_time
        
        # Log performance
        logger.info(f"Processed {len(alerts)} alerts in {processing_time:.2f} seconds ({alerts_per_second:.2f} alerts/sec)")
        
        # Check that all alerts were processed
        self.assertEqual(self.alert_routing_engine.send_to_websocket.call_count, 100)
        
        # Assert reasonable performance (adjust threshold as needed)
        self.assertGreater(alerts_per_second, 10, "Alert processing rate too low")
    
    def test_concurrent_alerts(self):
        """Test handling concurrent alerts"""
        # Create test alerts
        alerts = []
        for i in range(50):
            alert = {
                "alert_id": f"test-{i}",
                "sentinel": "oracle_sentinel" if i % 3 == 0 else "mev_sentinel" if i % 3 == 1 else "strategy_sentinel",
                "timestamp": time.time() + i,
                "severity": "LOW" if i % 5 < 3 else "MEDIUM" if i % 5 == 3 else "HIGH",
                "title": f"Test Alert {i}",
                "description": f"This is test alert {i}",
                "data": {
                    "test_id": i,
                    "value": i * 10
                }
            }
            alerts.append(alert)
        
        # Process alerts concurrently
        import concurrent.futures
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self.coordinator.process_alert, alert) for alert in alerts]
            concurrent.futures.wait(futures)
            
        end_time = time.time()
        
        # Calculate processing time
        processing_time = end_time - start_time
        alerts_per_second = len(alerts) / processing_time
        
        # Log performance
        logger.info(f"Processed {len(alerts)} concurrent alerts in {processing_time:.2f} seconds ({alerts_per_second:.2f} alerts/sec)")
        
        # Check that all alerts were processed
        self.assertEqual(self.alert_routing_engine.send_to_websocket.call_count, 50)
    
    def tearDown(self):
        """Clean up after test"""
        self.coordinator.shutdown()
        self.alert_routing_engine.shutdown()
        self.websocket_broadcaster.close()

if __name__ == "__main__":
    # Create and run testing framework
    framework = SentinelTestingFramework(config_path="sentinel_config.yaml")
    
    # Run all tests
    success = framework.run_all_tests()
    
    # Generate report
    report = framework.generate_report()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)