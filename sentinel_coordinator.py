#!/usr/bin/env python3
"""
Sentinel Coordinator
Coordinates between different sentinel components and manages alert flow
"""

import os
import sys
import time
import json
import yaml
import logging
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sentinel_coordinator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("sentinel_coordinator")

class SentinelCoordinator:
    """
    Coordinates between different sentinel components:
    - Receives alerts from sentinel agents
    - Routes alerts to appropriate channels via AlertRoutingEngine
    - Triggers emergency actions via SentinelContractManager when needed
    - Manages shared state between sentinel components
    """
    
    def __init__(
        self, 
        contract_manager=None, 
        websocket_broadcaster=None, 
        config_path="sentinel_config.yaml"
    ):
        """
        Initialize the Sentinel Coordinator
        
        Args:
            contract_manager: SentinelContractManager instance
            websocket_broadcaster: SentinelWebSocketBroadcaster instance
            config_path: Path to the sentinel configuration file
        """
        self.contract_manager = contract_manager
        self.websocket_broadcaster = websocket_broadcaster
        self.config_path = config_path
        self.alert_routing_engine = None
        self.sentinels = {}
        self.shared_state = {}
        
        # Load configuration
        self.load_config()
        
        # Initialize alert routing engine if not provided
        if self.config.get("integration", {}).get("alert_routing", {}).get("enabled", False):
            try:
                from alert_routing_engine import AlertRoutingEngine
                self.alert_routing_engine = AlertRoutingEngine(
                    config_path=self.config["integration"]["alert_routing"]["config_file"]
                )
                logger.info("Alert routing engine initialized")
            except ImportError as e:
                logger.error(f"Failed to import AlertRoutingEngine: {e}")
                logger.warning("Alert routing will be limited to WebSocket only")
        
        logger.info("Sentinel Coordinator initialized")
    
    def load_config(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, "r") as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self.config = {}
    
    def register_sentinel(self, sentinel_name: str, sentinel_instance: Any):
        """
        Register a sentinel agent with the coordinator
        
        Args:
            sentinel_name: Name of the sentinel agent
            sentinel_instance: Instance of the sentinel agent
        """
        self.sentinels[sentinel_name] = sentinel_instance
        logger.info(f"Registered sentinel: {sentinel_name}")
    
    def process_alert(self, alert: Dict[str, Any]):
        """
        Process an alert from a sentinel agent
        
        Args:
            alert: Alert data dictionary
        """
        logger.info(f"Processing alert: {alert.get('title')} [{alert.get('severity')}]")
        
        # Broadcast alert via WebSocket
        if self.websocket_broadcaster:
            try:
                self.websocket_broadcaster.broadcast_alert(alert)
                logger.info("Alert broadcasted via WebSocket")
            except Exception as e:
                logger.error(f"Failed to broadcast alert via WebSocket: {e}")
        
        # Route alert to appropriate channels
        if self.alert_routing_engine:
            try:
                self.alert_routing_engine.route_alert(alert)
                logger.info("Alert routed to appropriate channels")
            except Exception as e:
                logger.error(f"Failed to route alert: {e}")
        
        # Check if emergency action is needed
        if self._should_trigger_emergency_action(alert):
            self._execute_emergency_action(alert)
    
    def _should_trigger_emergency_action(self, alert: Dict[str, Any]) -> bool:
        """
        Determine if an alert should trigger an emergency action
        
        Args:
            alert: Alert data dictionary
            
        Returns:
            bool: True if emergency action should be triggered
        """
        # Get auto-pause threshold from config
        threshold = self.config.get("integration", {}).get("contract_interaction", {}).get("auto_pause_threshold", "CRITICAL")
        
        # Check if alert severity meets or exceeds threshold
        severity = alert.get("severity", "").upper()
        if severity == "EMERGENCY" or (severity == threshold):
            return True
            
        # Check for specific alert types that should trigger emergency action
        alert_type = alert.get("type", "").lower()
        if alert_type in ["sandwich_attack", "oracle_manipulation", "flash_loan_attack"]:
            return True
            
        return False
    
    def _execute_emergency_action(self, alert: Dict[str, Any]):
        """
        Execute emergency action based on alert
        
        Args:
            alert: Alert data dictionary
        """
        if not self.contract_manager:
            logger.error("Cannot execute emergency action: contract manager not initialized")
            return
            
        try:
            # Determine which contracts to pause based on alert source
            contracts_to_pause = self._get_contracts_to_pause(alert)
            
            # Execute pause action
            for contract_name in contracts_to_pause:
                self.contract_manager.pause_contract(contract_name)
                logger.info(f"Emergency pause executed for contract: {contract_name}")
                
            # Log emergency action
            logger.warning(
                f"EMERGENCY ACTION EXECUTED: Paused contracts {contracts_to_pause} "
                f"due to {alert.get('severity')} alert: {alert.get('title')}"
            )
        except Exception as e:
            logger.error(f"Failed to execute emergency action: {e}")
    
    def _get_contracts_to_pause(self, alert: Dict[str, Any]) -> List[str]:
        """
        Determine which contracts to pause based on alert
        
        Args:
            alert: Alert data dictionary
            
        Returns:
            List[str]: List of contract names to pause
        """
        sentinel = alert.get("sentinel", "").lower()
        severity = alert.get("severity", "").upper()
        
        # For EMERGENCY severity, pause all contracts
        if severity == "EMERGENCY":
            return list(self.config.get("integration", {}).get("contract_interaction", {}).get("contracts", {}).keys())
        
        # For specific sentinels, pause related contracts
        if sentinel == "oracle_sentinel":
            return ["arbitrage_executor", "ai_strategy"]
        elif sentinel == "mev_sentinel":
            return ["arbitrage_executor"]
        elif sentinel == "strategy_sentinel":
            return ["ai_strategy"]
            
        # Default to pausing arbitrage executor only
        return ["arbitrage_executor"]
    
    def get_shared_state(self, key: str) -> Any:
        """
        Get a value from shared state
        
        Args:
            key: State key
            
        Returns:
            Any: State value
        """
        return self.shared_state.get(key)
    
    def set_shared_state(self, key: str, value: Any):
        """
        Set a value in shared state
        
        Args:
            key: State key
            value: State value
        """
        self.shared_state[key] = value
        logger.debug(f"Set shared state: {key}")
    
    def shutdown(self):
        """Shutdown the coordinator and all components"""
        logger.info("Shutting down Sentinel Coordinator")
        
        # Close WebSocket broadcaster
        if self.websocket_broadcaster:
            try:
                self.websocket_broadcaster.close()
                logger.info("WebSocket broadcaster closed")
            except Exception as e:
                logger.error(f"Error closing WebSocket broadcaster: {e}")
        
        # Shutdown alert routing engine
        if self.alert_routing_engine:
            try:
                self.alert_routing_engine.shutdown()
                logger.info("Alert routing engine shut down")
            except Exception as e:
                logger.error(f"Error shutting down alert routing engine: {e}")
        
        logger.info("Sentinel Coordinator shutdown complete")

if __name__ == "__main__":
    # This block allows for standalone testing of the coordinator
    from sentinel_websocket_broadcaster import SentinelWebSocketBroadcaster
    from sentinel_contract_manager import SentinelContractManager
    
    # Initialize components
    websocket_broadcaster = SentinelWebSocketBroadcaster(
        websocket_url="ws://localhost:8080",
        reconnect_interval=5
    )
    
    contract_manager = SentinelContractManager(
        web3_provider="http://localhost:8545",
        abi_registry_path="contract_abi_registry.json"
    )
    
    # Initialize coordinator
    coordinator = SentinelCoordinator(
        contract_manager=contract_manager,
        websocket_broadcaster=websocket_broadcaster,
        config_path="sentinel_config.yaml"
    )
    
    # Test alert
    test_alert = {
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
    
    # Process test alert
    coordinator.process_alert(test_alert)
    
    # Shutdown
    coordinator.shutdown()