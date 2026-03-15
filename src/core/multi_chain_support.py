#!/usr/bin/env python3
"""
Multi-Chain Support Module
Provides support for monitoring and interacting with multiple blockchain networks
"""

import os
import sys
import time
import json
import yaml
import logging
import threading
from typing import Dict, List, Any, Optional, Union, Tuple
from web3 import Web3
from web3.middleware import geth_poa_middleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("multi_chain.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("multi_chain_support")

class MultiChainSupport:
    """
    Provides support for monitoring and interacting with multiple blockchain networks
    - Manages connections to multiple chains
    - Normalizes data across chains
    - Provides chain-specific thresholds and configurations
    - Supports cross-chain correlation of events
    """
    
    def __init__(self, config_path="sentinel_config.yaml"):
        """
        Initialize the Multi-Chain Support module
        
        Args:
            config_path: Path to the sentinel configuration file
        """
        self.config_path = config_path
        self.web3_instances = {}
        self.chain_data = {}
        self.event_listeners = {}
        self.cross_chain_events = []
        
        # Load configuration
        self.load_config()
        
        # Initialize web3 connections
        self._init_web3_connections()
        
        logger.info("Multi-Chain Support module initialized")
    
    def load_config(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
                
            # Extract multi-chain configuration
            self.config = config.get("advanced_features", {}).get("multi_chain", {})
            
            # Set defaults if not specified
            if not self.config:
                self.config = {
                    "enabled": True,
                    "networks": [
                        {
                            "name": "ethereum",
                            "rpc_url": "${ETH_RPC_URL}",
                            "chain_id": 1,
                            "enabled": True,
                            "priority": 1
                        }
                    ],
                    "cross_chain_correlation": {
                        "enabled": True,
                        "time_window": 300,
                        "similarity_threshold": 0.7
                    },
                    "chain_specific_thresholds": {
                        "ethereum": {
                            "gas_price_alert": 150,
                            "min_profit": 0.1
                        }
                    }
                }
                
            logger.info(f"Loaded configuration from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self.config = {}
    
    def _init_web3_connections(self):
        """Initialize Web3 connections to configured networks"""
        if not self.config.get("enabled", True):
            logger.info("Multi-chain support is disabled")
            return
            
        for network in self.config.get("networks", []):
            network_name = network.get("name", "").lower()
            
            if not network.get("enabled", True):
                logger.info(f"Network {network_name} is disabled")
                continue
                
            # Get RPC URL
            rpc_url = network.get("rpc_url", "")
            
            # Check for environment variable
            if rpc_url.startswith("${") and rpc_url.endswith("}"):
                env_var = rpc_url[2:-1]
                rpc_url = os.environ.get(env_var, "")
                
            if not rpc_url:
                logger.warning(f"No RPC URL configured for network: {network_name}")
                continue
                
            try:
                # Initialize Web3 connection
                web3 = Web3(Web3.HTTPProvider(rpc_url))
                
                # Add PoA middleware for networks that need it
                if network_name in ["polygon", "bsc", "optimism", "arbitrum"]:
                    web3.middleware_onion.inject(geth_poa_middleware, layer=0)
                    
                # Check connection
                if web3.is_connected():
                    # Store Web3 instance
                    self.web3_instances[network_name] = web3
                    
                    # Initialize chain data
                    self.chain_data[network_name] = {
                        "last_block": 0,
                        "gas_price": 0,
                        "sync_status": False,
                        "connected": True,
                        "chain_id": network.get("chain_id"),
                        "priority": network.get("priority", 999),
                        "last_update": time.time()
                    }
                    
                    logger.info(f"Connected to {network_name} network")
                else:
                    logger.warning(f"Failed to connect to {network_name} network")
            except Exception as e:
                logger.error(f"Error initializing Web3 connection for {network_name}: {e}")
    
    def get_web3(self, chain_name: str) -> Optional[Web3]:
        """
        Get Web3 instance for a specific chain
        
        Args:
            chain_name: Chain name
            
        Returns:
            Optional[Web3]: Web3 instance or None if not available
        """
        chain_name = chain_name.lower()
        return self.web3_instances.get(chain_name)
    
    def get_all_chains(self) -> List[str]:
        """
        Get list of all connected chains
        
        Returns:
            List[str]: List of chain names
        """
        return list(self.web3_instances.keys())
    
    def update_chain_data(self):
        """Update data for all connected chains"""
        for chain_name, web3 in self.web3_instances.items():
            try:
                # Get latest block number
                block_number = web3.eth.block_number
                
                # Get gas price
                gas_price = web3.eth.gas_price / 1e9  # Convert to gwei
                
                # Update chain data
                self.chain_data[chain_name].update({
                    "last_block": block_number,
                    "gas_price": gas_price,
                    "sync_status": not web3.eth.syncing,
                    "connected": web3.is_connected(),
                    "last_update": time.time()
                })
                
                # Check for gas price alerts
                self._check_gas_price_alert(chain_name, gas_price)
                
                logger.debug(f"Updated data for {chain_name}: block={block_number}, gas={gas_price:.2f} gwei")
            except Exception as e:
                logger.error(f"Error updating data for {chain_name}: {e}")
                self.chain_data[chain_name]["connected"] = False
    
    def _check_gas_price_alert(self, chain_name: str, gas_price: float):
        """
        Check if gas price exceeds threshold and generate alert if needed
        
        Args:
            chain_name: Chain name
            gas_price: Gas price in gwei
        """
        # Get threshold for this chain
        thresholds = self.config.get("chain_specific_thresholds", {}).get(chain_name, {})
        gas_price_threshold = thresholds.get("gas_price_alert", 150)  # Default 150 gwei
        
        if gas_price > gas_price_threshold:
            # Generate alert
            alert = {
                "alert_id": f"gas_price_{chain_name}_{int(time.time())}",
                "sentinel": "multi_chain_sentinel",
                "severity": "medium",
                "type": "gas_price_alert",
                "title": f"High Gas Price on {chain_name.capitalize()}",
                "message": f"Gas price on {chain_name.capitalize()} is {gas_price:.2f} gwei, exceeding threshold of {gas_price_threshold} gwei",
                "timestamp": time.time(),
                "data": {
                    "chain": chain_name,
                    "gas_price": gas_price,
                    "threshold": gas_price_threshold,
                    "block_number": self.chain_data[chain_name]["last_block"]
                }
            }
            
            # Emit alert
            self._emit_alert(alert)
    
    def _emit_alert(self, alert: Dict[str, Any]):
        """
        Emit an alert to the alert routing system
        
        Args:
            alert: Alert data
        """
        # In a real implementation, this would send the alert to the alert routing engine
        # For this example, we'll just log it
        logger.warning(f"MULTI-CHAIN ALERT: {alert['severity']} - {alert['title']} - {alert['message']}")
        
        # Try to import alert routing engine
        try:
            from alert_routing_engine import AlertRoutingEngine
            
            # Initialize engine
            routing_engine = AlertRoutingEngine()
            
            # Route alert
            routing_engine.route_alert(alert)
            
            logger.info("Alert sent to routing engine")
        except ImportError:
            logger.warning("Alert routing engine not available. Alert not routed.")
    
    def register_event_listener(self, chain_name: str, contract_address: str, event_name: str, callback):
        """
        Register a listener for contract events
        
        Args:
            chain_name: Chain name
            contract_address: Contract address
            event_name: Event name
            callback: Callback function to call when event is detected
        """
        chain_name = chain_name.lower()
        
        if chain_name not in self.web3_instances:
            logger.warning(f"Chain {chain_name} not connected")
            return
            
        # Create key for this listener
        key = f"{chain_name}:{contract_address}:{event_name}"
        
        # Store listener
        self.event_listeners[key] = {
            "chain": chain_name,
            "address": contract_address,
            "event": event_name,
            "callback": callback,
            "last_block": self.chain_data[chain_name]["last_block"]
        }
        
        logger.info(f"Registered event listener for {event_name} on {contract_address} ({chain_name})")
    
    def check_events(self):
        """Check for new events on all registered listeners"""
        for key, listener in self.event_listeners.items():
            chain_name = listener["chain"]
            
            if chain_name not in self.web3_instances:
                continue
                
            web3 = self.web3_instances[chain_name]
            
            try:
                # Get contract
                contract_address = listener["address"]
                event_name = listener["event"]
                last_block = listener["last_block"]
                current_block = self.chain_data[chain_name]["last_block"]
                
                # Skip if no new blocks
                if current_block <= last_block:
                    continue
                    
                # Get ABI for this contract
                # In a real implementation, this would load the ABI from a registry
                # For this example, we'll use a dummy ABI
                abi = [
                    {
                        "anonymous": False,
                        "inputs": [
                            {"indexed": True, "name": "from", "type": "address"},
                            {"indexed": True, "name": "to", "type": "address"},
                            {"indexed": False, "name": "value", "type": "uint256"}
                        ],
                        "name": "Transfer",
                        "type": "event"
                    }
                ]
                
                # Create contract instance
                contract = web3.eth.contract(address=contract_address, abi=abi)
                
                # Get event filter
                event_filter = getattr(contract.events, event_name).create_filter(
                    fromBlock=last_block + 1,
                    toBlock=current_block
                )
                
                # Get events
                events = event_filter.get_all_entries()
                
                for event in events:
                    # Process event
                    self._process_event(chain_name, contract_address, event_name, event)
                    
                    # Call callback
                    callback = listener["callback"]
                    callback(event)
                    
                # Update last block
                listener["last_block"] = current_block
                
                logger.debug(f"Checked events for {event_name} on {contract_address} ({chain_name}): {len(events)} events")
            except Exception as e:
                logger.error(f"Error checking events for {key}: {e}")
    
    def _process_event(self, chain_name: str, contract_address: str, event_name: str, event: Any):
        """
        Process a contract event
        
        Args:
            chain_name: Chain name
            contract_address: Contract address
            event_name: Event name
            event: Event data
        """
        # Add to cross-chain events
        cross_chain_event = {
            "chain": chain_name,
            "address": contract_address,
            "event": event_name,
            "data": dict(event.args),
            "block_number": event.blockNumber,
            "transaction_hash": event.transactionHash.hex(),
            "timestamp": time.time()
        }
        
        self.cross_chain_events.append(cross_chain_event)
        
        # Limit number of stored events
        max_events = 1000
        if len(self.cross_chain_events) > max_events:
            self.cross_chain_events = self.cross_chain_events[-max_events:]
            
        # Check for cross-chain correlations
        if self.config.get("cross_chain_correlation", {}).get("enabled", True):
            self._check_cross_chain_correlation(cross_chain_event)
    
    def _check_cross_chain_correlation(self, event: Dict[str, Any]):
        """
        Check for correlations between events across different chains
        
        Args:
            event: Event data
        """
        # Get correlation settings
        time_window = self.config.get("cross_chain_correlation", {}).get("time_window", 300)
        similarity_threshold = self.config.get("cross_chain_correlation", {}).get("similarity_threshold", 0.7)
        
        # Get event timestamp
        timestamp = event["timestamp"]
        
        # Find recent events on other chains
        correlated_events = []
        
        for other_event in self.cross_chain_events:
            # Skip same chain
            if other_event["chain"] == event["chain"]:
                continue
                
            # Check time window
            if abs(timestamp - other_event["timestamp"]) > time_window:
                continue
                
            # Check similarity
            similarity = self._calculate_event_similarity(event, other_event)
            
            if similarity >= similarity_threshold:
                correlated_events.append(other_event)
                
        # If correlated events found, generate alert
        if correlated_events:
            self._generate_cross_chain_alert(event, correlated_events)
    
    def _calculate_event_similarity(self, event1: Dict[str, Any], event2: Dict[str, Any]) -> float:
        """
        Calculate similarity between two events
        
        Args:
            event1: First event
            event2: Second event
            
        Returns:
            float: Similarity score (0-1)
        """
        # Simple similarity calculation
        # In a real implementation, this would be more sophisticated
        
        # Check if same event name
        if event1["event"] != event2["event"]:
            return 0.0
            
        # Check data fields
        data1 = event1["data"]
        data2 = event2["data"]
        
        # Count matching fields
        matching_fields = 0
        total_fields = 0
        
        for key in data1:
            if key in data2:
                total_fields += 1
                
                if data1[key] == data2[key]:
                    matching_fields += 1
                    
        # Calculate similarity
        if total_fields == 0:
            return 0.0
            
        return matching_fields / total_fields
    
    def _generate_cross_chain_alert(self, event: Dict[str, Any], correlated_events: List[Dict[str, Any]]):
        """
        Generate an alert for correlated cross-chain events
        
        Args:
            event: Primary event
            correlated_events: List of correlated events
        """
        # Get chains involved
        chains = [event["chain"]] + [e["chain"] for e in correlated_events]
        chains = sorted(set(chains))
        
        # Generate alert
        alert = {
            "alert_id": f"cross_chain_{int(time.time())}",
            "sentinel": "multi_chain_sentinel",
            "severity": "high",
            "type": "cross_chain_correlation",
            "title": f"Cross-Chain Activity Detected: {event['event']}",
            "message": f"Correlated {event['event']} events detected across {len(chains)} chains: {', '.join(chains)}",
            "timestamp": time.time(),
            "data": {
                "primary_chain": event["chain"],
                "primary_address": event["address"],
                "event_name": event["event"],
                "correlated_chains": [e["chain"] for e in correlated_events],
                "total_events": len(correlated_events) + 1
            }
        }
        
        # Emit alert
        self._emit_alert(alert)
    
    def execute_transaction(self, chain_name: str, contract_address: str, function_name: str, 
                           args: List[Any] = None, private_key: str = None) -> Optional[str]:
        """
        Execute a transaction on a specific chain
        
        Args:
            chain_name: Chain name
            contract_address: Contract address
            function_name: Function name
            args: Function arguments
            private_key: Private key for signing transaction
            
        Returns:
            Optional[str]: Transaction hash or None if transaction fails
        """
        chain_name = chain_name.lower()
        
        if chain_name not in self.web3_instances:
            logger.warning(f"Chain {chain_name} not connected")
            return None
            
        web3 = self.web3_instances[chain_name]
        
        try:
            # Get ABI for this contract
            # In a real implementation, this would load the ABI from a registry
            # For this example, we'll use a dummy ABI
            abi = [
                {
                    "constant": False,
                    "inputs": [],
                    "name": "emergencyPause",
                    "outputs": [],
                    "payable": False,
                    "stateMutability": "nonpayable",
                    "type": "function"
                }
            ]
            
            # Create contract instance
            contract = web3.eth.contract(address=contract_address, abi=abi)
            
            # Get function
            contract_function = getattr(contract.functions, function_name)
            
            # Build transaction
            if args:
                tx = contract_function(*args).build_transaction({
                    'from': web3.eth.account.from_key(private_key).address,
                    'nonce': web3.eth.get_transaction_count(web3.eth.account.from_key(private_key).address),
                    'gas': 2000000,
                    'gasPrice': web3.eth.gas_price
                })
            else:
                tx = contract_function().build_transaction({
                    'from': web3.eth.account.from_key(private_key).address,
                    'nonce': web3.eth.get_transaction_count(web3.eth.account.from_key(private_key).address),
                    'gas': 2000000,
                    'gasPrice': web3.eth.gas_price
                })
                
            # Sign transaction
            signed_tx = web3.eth.account.sign_transaction(tx, private_key)
            
            # Send transaction
            tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            logger.info(f"Transaction sent on {chain_name}: {tx_hash.hex()}")
            
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Error executing transaction on {chain_name}: {e}")
            return None
    
    def get_chain_status(self, chain_name: str = None) -> Dict[str, Any]:
        """
        Get status of all chains or a specific chain
        
        Args:
            chain_name: Chain name (optional)
            
        Returns:
            Dict[str, Any]: Chain status data
        """
        if chain_name:
            chain_name = chain_name.lower()
            return self.chain_data.get(chain_name, {})
            
        return self.chain_data
    
    def start_monitoring(self, interval: int = 60):
        """
        Start monitoring chains in a background thread
        
        Args:
            interval: Update interval in seconds
        """
        def monitor_chains():
            while True:
                try:
                    # Update chain data
                    self.update_chain_data()
                    
                    # Check events
                    self.check_events()
                    
                    # Sleep
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"Error in chain monitoring: {e}")
                    time.sleep(10)  # Sleep and retry
        
        # Start monitoring thread
        thread = threading.Thread(target=monitor_chains, daemon=True)
        thread.start()
        
        logger.info(f"Started chain monitoring with interval {interval} seconds")
    
    def shutdown(self):
        """Shutdown the multi-chain support module"""
        logger.info("Shutting down Multi-Chain Support module")
        
        # Clean up resources
        self.web3_instances = {}
        self.chain_data = {}
        self.event_listeners = {}
        self.cross_chain_events = []
        
        logger.info("Multi-Chain Support module shutdown complete")

if __name__ == "__main__":
    # This block allows for standalone testing of the multi-chain support module
    
    # Initialize module
    multi_chain = MultiChainSupport(config_path="sentinel_config.yaml")
    
    # Get connected chains
    chains = multi_chain.get_all_chains()
    print(f"Connected chains: {chains}")
    
    # Update chain data
    multi_chain.update_chain_data()
    
    # Print chain status
    for chain in chains:
        status = multi_chain.get_chain_status(chain)
        print(f"{chain} status: block={status.get('last_block')}, gas={status.get('gas_price'):.2f} gwei")
    
    # Start monitoring
    multi_chain.start_monitoring(interval=10)
    
    # Keep running for a while
    try:
        time.sleep(60)
    except KeyboardInterrupt:
        pass
    
    # Shutdown
    multi_chain.shutdown()