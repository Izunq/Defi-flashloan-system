#!/usr/bin/env python3
"""
Sentinel Contract Manager
Manage all contract interactions from sentinels
"""

import os
import sys
import json
import time
import yaml
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union, Tuple
from web3 import Web3
from web3.exceptions import ContractLogicError, TransactionNotFound
from web3.middleware import geth_poa_middleware
from eth_account import Account
from eth_account.signers.local import LocalAccount

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sentinel_contract_manager.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SentinelContractManager")

class SentinelContractManager:
    """
    Manage all contract interactions from sentinels
    """
    
    def __init__(self, config_path: str = "sentinel_config.yaml"):
        """Initialize the contract manager"""
        self.config = self._load_config(config_path)
        self.contract_config = self.config.get("integration", {}).get("contract_interaction", {})
        
        # Check if contract interaction is enabled
        if not self.contract_config.get("enabled", False):
            logger.warning("Contract interaction is disabled in config")
            return
        
        # Initialize Web3 connection
        self.web3 = self._initialize_web3()
        
        # Load contract ABIs
        self.abi_registry = self._load_abi_registry()
        
        # Initialize emergency wallet
        self.emergency_wallet = self._initialize_emergency_wallet()
        
        # Transaction settings
        self.gas_limit = self.contract_config.get("gas_limit", 500000)
        self.gas_price_multiplier = self.contract_config.get("gas_price_multiplier", 1.2)
        
        # Auto-pause threshold
        self.auto_pause_threshold = self.contract_config.get("auto_pause_threshold", "CRITICAL")
        
        # Transaction history
        self.transaction_history = []
        self.max_history_size = 100
        
        logger.info("Sentinel Contract Manager initialized")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Config file {config_path} not found")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            sys.exit(1)
    
    def _initialize_web3(self) -> Web3:
        """Initialize Web3 connection"""
        provider_url = self.contract_config.get("web3_provider", "http://localhost:8545")
        
        try:
            if provider_url.startswith("http"):
                web3 = Web3(Web3.HTTPProvider(provider_url))
            elif provider_url.startswith("ws"):
                web3 = Web3(Web3.WebsocketProvider(provider_url))
            else:
                logger.error(f"Unsupported provider URL: {provider_url}")
                sys.exit(1)
            
            # Add PoA middleware for networks like BSC, Polygon, etc.
            web3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            if not web3.is_connected():
                logger.error(f"Failed to connect to Web3 provider at {provider_url}")
                sys.exit(1)
            
            logger.info(f"Connected to Web3 provider at {provider_url}")
            logger.info(f"Current block number: {web3.eth.block_number}")
            
            return web3
        
        except Exception as e:
            logger.error(f"Error initializing Web3: {e}")
            sys.exit(1)
    
    def _load_abi_registry(self) -> Dict[str, Any]:
        """Load contract ABI registry"""
        abi_registry_path = self.contract_config.get("abi_registry", "contract_abi_registry.json")
        
        try:
            with open(abi_registry_path, 'r') as f:
                abi_registry = json.load(f)
            logger.info(f"Loaded ABI registry from {abi_registry_path}")
            return abi_registry
        except FileNotFoundError:
            logger.error(f"ABI registry file {abi_registry_path} not found")
            # Create an empty registry
            return {"contracts": {}}
        except Exception as e:
            logger.error(f"Error loading ABI registry: {e}")
            return {"contracts": {}}
    
    def _initialize_emergency_wallet(self) -> Optional[LocalAccount]:
        """Initialize emergency wallet for contract interactions"""
        wallet_address = self.contract_config.get("emergency_wallet")
        private_key = self.contract_config.get("emergency_private_key")
        
        # Check if wallet is configured with environment variables
        if wallet_address and wallet_address.startswith("${") and wallet_address.endswith("}"):
            env_var = wallet_address[2:-1]
            wallet_address = os.environ.get(env_var)
        
        if private_key and private_key.startswith("${") and private_key.endswith("}"):
            env_var = private_key[2:-1]
            private_key = os.environ.get(env_var)
        
        if not wallet_address or not private_key:
            logger.warning("Emergency wallet not configured. Contract interactions will be read-only.")
            return None
        
        try:
            account = Account.from_key(private_key)
            if account.address.lower() != wallet_address.lower():
                logger.error("Private key does not match wallet address")
                return None
            
            logger.info(f"Emergency wallet initialized: {account.address}")
            return account
        
        except Exception as e:
            logger.error(f"Error initializing emergency wallet: {e}")
            return None
    
    def get_contract(self, contract_name: str) -> Optional[Any]:
        """Get contract instance by name"""
        if contract_name not in self.contract_config.get("contracts", {}):
            logger.error(f"Contract {contract_name} not found in config")
            return None
        
        contract_config = self.contract_config["contracts"][contract_name]
        contract_address = contract_config.get("address")
        
        # Check if address is configured with environment variables
        if contract_address and contract_address.startswith("${") and contract_address.endswith("}"):
            env_var = contract_address[2:-1]
            contract_address = os.environ.get(env_var)
        
        if not contract_address:
            logger.error(f"Address for contract {contract_name} not found")
            return None
        
        # Get ABI from registry
        if contract_name not in self.abi_registry.get("contracts", {}):
            logger.error(f"ABI for contract {contract_name} not found in registry")
            return None
        
        contract_abi = self.abi_registry["contracts"][contract_name].get("abi")
        
        if not contract_abi:
            logger.error(f"ABI for contract {contract_name} is empty")
            return None
        
        try:
            contract = self.web3.eth.contract(address=contract_address, abi=contract_abi)
            return contract
        
        except Exception as e:
            logger.error(f"Error creating contract instance for {contract_name}: {e}")
            return None
    
    async def emergency_pause(self, contract_name: str, reason: str) -> Dict[str, Any]:
        """
        Emergency pause a contract
        
        Args:
            contract_name: Name of the contract to pause
            reason: Reason for pausing
            
        Returns:
            Dict with transaction status and details
        """
        if not self.emergency_wallet:
            return {
                "success": False,
                "error": "Emergency wallet not configured",
                "transaction_hash": None
            }
        
        contract = self.get_contract(contract_name)
        if not contract:
            return {
                "success": False,
                "error": f"Contract {contract_name} not found",
                "transaction_hash": None
            }
        
        # Get pause function name from config
        pause_function = self.contract_config["contracts"][contract_name].get("pause_function")
        if not pause_function:
            return {
                "success": False,
                "error": f"Pause function for contract {contract_name} not defined",
                "transaction_hash": None
            }
        
        # Check if contract has the pause function
        if not hasattr(contract.functions, pause_function):
            return {
                "success": False,
                "error": f"Contract {contract_name} does not have function {pause_function}",
                "transaction_hash": None
            }
        
        try:
            # Check if contract is already paused
            if hasattr(contract.functions, "paused"):
                paused = contract.functions.paused().call()
                if paused:
                    return {
                        "success": True,
                        "message": f"Contract {contract_name} is already paused",
                        "transaction_hash": None
                    }
            
            # Get current gas price and apply multiplier
            gas_price = int(self.web3.eth.gas_price * self.gas_price_multiplier)
            
            # Build transaction
            pause_function = getattr(contract.functions, pause_function)
            
            # Check function signature to determine arguments
            function_params = []
            if "reason" in str(pause_function):
                function_params.append(reason)
            
            transaction = pause_function(*function_params).build_transaction({
                'from': self.emergency_wallet.address,
                'gas': self.gas_limit,
                'gasPrice': gas_price,
                'nonce': self.web3.eth.get_transaction_count(self.emergency_wallet.address)
            })
            
            # Sign and send transaction
            signed_tx = self.emergency_wallet.sign_transaction(transaction)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for transaction receipt
            receipt = await self._wait_for_transaction(tx_hash)
            
            # Add to transaction history
            self._add_to_transaction_history({
                "contract_name": contract_name,
                "function": pause_function.__name__,
                "transaction_hash": tx_hash.hex(),
                "status": "success" if receipt["status"] == 1 else "failed",
                "timestamp": int(time.time()),
                "gas_used": receipt["gasUsed"],
                "block_number": receipt["blockNumber"]
            })
            
            if receipt["status"] == 1:
                logger.info(f"Successfully paused contract {contract_name}: {tx_hash.hex()}")
                return {
                    "success": True,
                    "message": f"Contract {contract_name} paused successfully",
                    "transaction_hash": tx_hash.hex(),
                    "block_number": receipt["blockNumber"],
                    "gas_used": receipt["gasUsed"]
                }
            else:
                logger.error(f"Failed to pause contract {contract_name}: {tx_hash.hex()}")
                return {
                    "success": False,
                    "error": f"Transaction failed",
                    "transaction_hash": tx_hash.hex()
                }
        
        except ContractLogicError as e:
            error_message = str(e)
            logger.error(f"Contract logic error when pausing {contract_name}: {error_message}")
            return {
                "success": False,
                "error": f"Contract logic error: {error_message}",
                "transaction_hash": None
            }
        
        except Exception as e:
            logger.error(f"Error pausing contract {contract_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "transaction_hash": None
            }
    
    async def emergency_unpause(self, contract_name: str, reason: str) -> Dict[str, Any]:
        """
        Emergency unpause a contract
        
        Args:
            contract_name: Name of the contract to unpause
            reason: Reason for unpausing
            
        Returns:
            Dict with transaction status and details
        """
        if not self.emergency_wallet:
            return {
                "success": False,
                "error": "Emergency wallet not configured",
                "transaction_hash": None
            }
        
        contract = self.get_contract(contract_name)
        if not contract:
            return {
                "success": False,
                "error": f"Contract {contract_name} not found",
                "transaction_hash": None
            }
        
        # Get unpause function name from config
        unpause_function = self.contract_config["contracts"][contract_name].get("unpause_function")
        if not unpause_function:
            return {
                "success": False,
                "error": f"Unpause function for contract {contract_name} not defined",
                "transaction_hash": None
            }
        
        # Check if contract has the unpause function
        if not hasattr(contract.functions, unpause_function):
            return {
                "success": False,
                "error": f"Contract {contract_name} does not have function {unpause_function}",
                "transaction_hash": None
            }
        
        try:
            # Check if contract is already unpaused
            if hasattr(contract.functions, "paused"):
                paused = contract.functions.paused().call()
                if not paused:
                    return {
                        "success": True,
                        "message": f"Contract {contract_name} is already unpaused",
                        "transaction_hash": None
                    }
            
            # Get current gas price and apply multiplier
            gas_price = int(self.web3.eth.gas_price * self.gas_price_multiplier)
            
            # Build transaction
            unpause_function = getattr(contract.functions, unpause_function)
            
            # Check function signature to determine arguments
            function_params = []
            if "reason" in str(unpause_function):
                function_params.append(reason)
            
            transaction = unpause_function(*function_params).build_transaction({
                'from': self.emergency_wallet.address,
                'gas': self.gas_limit,
                'gasPrice': gas_price,
                'nonce': self.web3.eth.get_transaction_count(self.emergency_wallet.address)
            })
            
            # Sign and send transaction
            signed_tx = self.emergency_wallet.sign_transaction(transaction)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for transaction receipt
            receipt = await self._wait_for_transaction(tx_hash)
            
            # Add to transaction history
            self._add_to_transaction_history({
                "contract_name": contract_name,
                "function": unpause_function.__name__,
                "transaction_hash": tx_hash.hex(),
                "status": "success" if receipt["status"] == 1 else "failed",
                "timestamp": int(time.time()),
                "gas_used": receipt["gasUsed"],
                "block_number": receipt["blockNumber"]
            })
            
            if receipt["status"] == 1:
                logger.info(f"Successfully unpaused contract {contract_name}: {tx_hash.hex()}")
                return {
                    "success": True,
                    "message": f"Contract {contract_name} unpaused successfully",
                    "transaction_hash": tx_hash.hex(),
                    "block_number": receipt["blockNumber"],
                    "gas_used": receipt["gasUsed"]
                }
            else:
                logger.error(f"Failed to unpause contract {contract_name}: {tx_hash.hex()}")
                return {
                    "success": False,
                    "error": f"Transaction failed",
                    "transaction_hash": tx_hash.hex()
                }
        
        except ContractLogicError as e:
            error_message = str(e)
            logger.error(f"Contract logic error when unpausing {contract_name}: {error_message}")
            return {
                "success": False,
                "error": f"Contract logic error: {error_message}",
                "transaction_hash": None
            }
        
        except Exception as e:
            logger.error(f"Error unpausing contract {contract_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "transaction_hash": None
            }
    
    async def execute_contract_function(
        self, 
        contract_name: str, 
        function_name: str, 
        args: List[Any] = None,
        value: int = 0
    ) -> Dict[str, Any]:
        """
        Execute a contract function
        
        Args:
            contract_name: Name of the contract
            function_name: Name of the function to call
            args: Function arguments
            value: ETH value to send with the transaction
            
        Returns:
            Dict with transaction status and details
        """
        if not self.emergency_wallet:
            return {
                "success": False,
                "error": "Emergency wallet not configured",
                "transaction_hash": None
            }
        
        contract = self.get_contract(contract_name)
        if not contract:
            return {
                "success": False,
                "error": f"Contract {contract_name} not found",
                "transaction_hash": None
            }
        
        # Check if contract has the function
        if not hasattr(contract.functions, function_name):
            return {
                "success": False,
                "error": f"Contract {contract_name} does not have function {function_name}",
                "transaction_hash": None
            }
        
        try:
            # Get current gas price and apply multiplier
            gas_price = int(self.web3.eth.gas_price * self.gas_price_multiplier)
            
            # Build transaction
            function = getattr(contract.functions, function_name)
            args = args or []
            
            transaction = function(*args).build_transaction({
                'from': self.emergency_wallet.address,
                'gas': self.gas_limit,
                'gasPrice': gas_price,
                'nonce': self.web3.eth.get_transaction_count(self.emergency_wallet.address),
                'value': value
            })
            
            # Sign and send transaction
            signed_tx = self.emergency_wallet.sign_transaction(transaction)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for transaction receipt
            receipt = await self._wait_for_transaction(tx_hash)
            
            # Add to transaction history
            self._add_to_transaction_history({
                "contract_name": contract_name,
                "function": function_name,
                "args": str(args),
                "value": value,
                "transaction_hash": tx_hash.hex(),
                "status": "success" if receipt["status"] == 1 else "failed",
                "timestamp": int(time.time()),
                "gas_used": receipt["gasUsed"],
                "block_number": receipt["blockNumber"]
            })
            
            if receipt["status"] == 1:
                logger.info(f"Successfully executed {function_name} on {contract_name}: {tx_hash.hex()}")
                return {
                    "success": True,
                    "message": f"Function {function_name} executed successfully",
                    "transaction_hash": tx_hash.hex(),
                    "block_number": receipt["blockNumber"],
                    "gas_used": receipt["gasUsed"]
                }
            else:
                logger.error(f"Failed to execute {function_name} on {contract_name}: {tx_hash.hex()}")
                return {
                    "success": False,
                    "error": f"Transaction failed",
                    "transaction_hash": tx_hash.hex()
                }
        
        except ContractLogicError as e:
            error_message = str(e)
            logger.error(f"Contract logic error when executing {function_name} on {contract_name}: {error_message}")
            return {
                "success": False,
                "error": f"Contract logic error: {error_message}",
                "transaction_hash": None
            }
        
        except Exception as e:
            logger.error(f"Error executing {function_name} on {contract_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "transaction_hash": None
            }
    
    async def read_contract_function(
        self, 
        contract_name: str, 
        function_name: str, 
        args: List[Any] = None
    ) -> Dict[str, Any]:
        """
        Read a contract function (view/pure)
        
        Args:
            contract_name: Name of the contract
            function_name: Name of the function to call
            args: Function arguments
            
        Returns:
            Dict with function result
        """
        contract = self.get_contract(contract_name)
        if not contract:
            return {
                "success": False,
                "error": f"Contract {contract_name} not found"
            }
        
        # Check if contract has the function
        if not hasattr(contract.functions, function_name):
            return {
                "success": False,
                "error": f"Contract {contract_name} does not have function {function_name}"
            }
        
        try:
            # Call function
            function = getattr(contract.functions, function_name)
            args = args or []
            
            result = function(*args).call()
            
            return {
                "success": True,
                "result": result
            }
        
        except ContractLogicError as e:
            error_message = str(e)
            logger.error(f"Contract logic error when reading {function_name} on {contract_name}: {error_message}")
            return {
                "success": False,
                "error": f"Contract logic error: {error_message}"
            }
        
        except Exception as e:
            logger.error(f"Error reading {function_name} on {contract_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def check_contract_status(self, contract_name: str) -> Dict[str, Any]:
        """
        Check contract status (paused, owner, etc.)
        
        Args:
            contract_name: Name of the contract
            
        Returns:
            Dict with contract status
        """
        contract = self.get_contract(contract_name)
        if not contract:
            return {
                "success": False,
                "error": f"Contract {contract_name} not found"
            }
        
        status = {
            "contract_name": contract_name,
            "address": contract.address,
            "success": True
        }
        
        # Check if contract is pausable
        if hasattr(contract.functions, "paused"):
            try:
                status["paused"] = contract.functions.paused().call()
            except Exception as e:
                logger.error(f"Error checking paused status for {contract_name}: {e}")
                status["paused"] = "unknown"
        
        # Check if contract has an owner
        if hasattr(contract.functions, "owner"):
            try:
                status["owner"] = contract.functions.owner().call()
            except Exception as e:
                logger.error(f"Error checking owner for {contract_name}: {e}")
                status["owner"] = "unknown"
        
        # Check if contract has implementation (for proxies)
        if hasattr(contract.functions, "implementation"):
            try:
                status["implementation"] = contract.functions.implementation().call()
            except Exception as e:
                logger.error(f"Error checking implementation for {contract_name}: {e}")
                status["implementation"] = "unknown"
        
        return status
    
    async def _wait_for_transaction(self, tx_hash, timeout: int = 120) -> Dict[str, Any]:
        """
        Wait for transaction to be mined
        
        Args:
            tx_hash: Transaction hash
            timeout: Timeout in seconds
            
        Returns:
            Transaction receipt
        """
        start_time = time.time()
        while True:
            try:
                receipt = self.web3.eth.get_transaction_receipt(tx_hash)
                if receipt:
                    return receipt
            except TransactionNotFound:
                pass
            
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Transaction {tx_hash.hex()} not mined within {timeout} seconds")
            
            await asyncio.sleep(2)
    
    def _add_to_transaction_history(self, transaction: Dict[str, Any]):
        """Add transaction to history"""
        self.transaction_history.append(transaction)
        
        # Trim history if needed
        if len(self.transaction_history) > self.max_history_size:
            self.transaction_history = self.transaction_history[-self.max_history_size:]
    
    def get_transaction_history(self) -> List[Dict[str, Any]]:
        """Get transaction history"""
        return self.transaction_history
    
    def should_auto_pause(self, threat_level: str) -> bool:
        """
        Check if a threat level should trigger auto-pause
        
        Args:
            threat_level: Threat level (LOW, MEDIUM, HIGH, CRITICAL, EMERGENCY)
            
        Returns:
            True if auto-pause should be triggered
        """
        threat_levels = {
            "LOW": 1,
            "MEDIUM": 2,
            "HIGH": 3,
            "CRITICAL": 4,
            "EMERGENCY": 5
        }
        
        auto_pause_level = threat_levels.get(self.auto_pause_threshold, 4)  # Default to CRITICAL
        threat_level_value = threat_levels.get(threat_level, 0)
        
        return threat_level_value >= auto_pause_level

async def main():
    """Main entry point for testing"""
    contract_manager = SentinelContractManager()
    
    # Example: Check contract status
    status = await contract_manager.check_contract_status("arbitrage_executor")
    print(f"Contract status: {status}")
    
    # Example: Read contract function
    result = await contract_manager.read_contract_function("arbitrage_executor", "paused")
    print(f"Paused status: {result}")
    
    # Example: Emergency pause
    # pause_result = await contract_manager.emergency_pause("arbitrage_executor", "Emergency pause due to security alert")
    # print(f"Pause result: {pause_result}")

if __name__ == "__main__":
    asyncio.run(main())