import os
import json
import yaml
import time
import logging
import asyncio
import hashlib
from typing import Dict, List, Tuple, Optional, Any, Set
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
from eth_account.messages import encode_defunct
from dotenv import load_dotenv
import aiohttp
import numpy as np

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("interchain_mesh.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("InterChainCognitiveMesh")

class ChainConnection:
    """
    Represents a connection to a specific blockchain.
    """
    
    def __init__(self, chain_id: int, name: str, rpc_url: str, mesh_address: str):
        """
        Initialize a chain connection.
        
        Args:
            chain_id: Chain ID
            name: Chain name
            rpc_url: RPC URL
            mesh_address: Address of the InterChainCognitiveMesh contract
        """
        self.chain_id = chain_id
        self.name = name
        self.rpc_url = rpc_url
        self.mesh_address = mesh_address
        self.w3 = None
        self.mesh_contract = None
        self.is_connected = False
        self.last_block = 0
        self.gas_price = 0
        self.nonce = 0
    
    async def connect(self, abi: List) -> bool:
        """
        Connect to the chain.
        
        Args:
            abi: ABI of the InterChainCognitiveMesh contract
            
        Returns:
            bool: Success
        """
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            if not self.w3.is_connected():
                logger.error(f"Failed to connect to {self.name} (Chain ID: {self.chain_id})")
                return False
            
            self.mesh_contract = self.w3.eth.contract(address=self.mesh_address, abi=abi)
            self.last_block = self.w3.eth.block_number
            self.gas_price = self.w3.eth.gas_price
            self.is_connected = True
            
            logger.info(f"Connected to {self.name} (Chain ID: {self.chain_id})")
            return True
        
        except Exception as e:
            logger.error(f"Error connecting to {self.name} (Chain ID: {self.chain_id}): {e}")
            return False
    
    async def update_status(self) -> bool:
        """
        Update chain status.
        
        Returns:
            bool: Success
        """
        try:
            if not self.is_connected:
                return False
            
            self.last_block = self.w3.eth.block_number
            self.gas_price = self.w3.eth.gas_price
            
            return True
        
        except Exception as e:
            logger.error(f"Error updating status for {self.name} (Chain ID: {self.chain_id}): {e}")
            self.is_connected = False
            return False

class GlobalState:
    """
    Represents the unified global state across all chains.
    """
    
    def __init__(self):
        """
        Initialize the global state.
        """
        self.state = {}
        self.versions = {}
        self.last_updated = {}
        self.update_chain = {}
    
    def update(self, key: str, value: Any, chain_id: int) -> bool:
        """
        Update a state entry.
        
        Args:
            key: State key
            value: State value
            chain_id: Chain ID
            
        Returns:
            bool: Whether the state was updated
        """
        # Convert key to string if it's bytes
        if isinstance(key, bytes):
            key = key.hex()
        
        # Get current version
        current_version = self.versions.get(key, 0)
        
        # Update state
        self.state[key] = value
        self.versions[key] = current_version + 1
        self.last_updated[key] = time.time()
        self.update_chain[key] = chain_id
        
        return True
    
    def get(self, key: str) -> Tuple[Any, int, int, int]:
        """
        Get a state entry.
        
        Args:
            key: State key
            
        Returns:
            Tuple[Any, int, int, int]: (value, last_updated, update_chain, version)
        """
        # Convert key to string if it's bytes
        if isinstance(key, bytes):
            key = key.hex()
        
        if key not in self.state:
            return None, 0, 0, 0
        
        return (
            self.state[key],
            self.last_updated[key],
            self.update_chain[key],
            self.versions[key]
        )
    
    def get_all_keys(self) -> List[str]:
        """
        Get all state keys.
        
        Returns:
            List[str]: List of state keys
        """
        return list(self.state.keys())

class PendingOperation:
    """
    Represents a pending cross-chain operation.
    """
    
    def __init__(
        self,
        operation_id: str,
        source_chain_id: int,
        target_chain_id: int,
        initiator: str,
        payload: bytes,
        gas_limit: int,
        value: int,
        deadline: int
    ):
        """
        Initialize a pending operation.
        
        Args:
            operation_id: Operation ID
            source_chain_id: Source chain ID
            target_chain_id: Target chain ID
            initiator: Initiator address
            payload: Operation payload
            gas_limit: Gas limit
            value: Value in wei
            deadline: Deadline timestamp
        """
        self.operation_id = operation_id
        self.source_chain_id = source_chain_id
        self.target_chain_id = target_chain_id
        self.initiator = initiator
        self.payload = payload
        self.gas_limit = gas_limit
        self.value = value
        self.deadline = deadline
        self.created_at = time.time()
        self.status = "Pending"
        self.executed_at = 0
        self.result = None
        self.retries = 0
        self.max_retries = 3
    
    def to_dict(self) -> Dict:
        """
        Convert to dictionary.
        
        Returns:
            Dict: Dictionary representation
        """
        return {
            "operation_id": self.operation_id,
            "source_chain_id": self.source_chain_id,
            "target_chain_id": self.target_chain_id,
            "initiator": self.initiator,
            "payload": self.payload.hex() if isinstance(self.payload, bytes) else self.payload,
            "gas_limit": self.gas_limit,
            "value": self.value,
            "deadline": self.deadline,
            "created_at": self.created_at,
            "status": self.status,
            "executed_at": self.executed_at,
            "result": self.result.hex() if isinstance(self.result, bytes) else self.result,
            "retries": self.retries,
            "max_retries": self.max_retries
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PendingOperation':
        """
        Create from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            PendingOperation: Created operation
        """
        operation = cls(
            data["operation_id"],
            data["source_chain_id"],
            data["target_chain_id"],
            data["initiator"],
            bytes.fromhex(data["payload"]) if isinstance(data["payload"], str) else data["payload"],
            data["gas_limit"],
            data["value"],
            data["deadline"]
        )
        
        operation.created_at = data["created_at"]
        operation.status = data["status"]
        operation.executed_at = data["executed_at"]
        operation.result = bytes.fromhex(data["result"]) if isinstance(data["result"], str) and data["result"] else None
        operation.retries = data["retries"]
        operation.max_retries = data["max_retries"]
        
        return operation

class InterChainCognitiveMesh:
    """
    The Inter-Chain Cognitive Mesh coordinates operations across multiple blockchains
    and maintains a unified global state.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the Inter-Chain Cognitive Mesh.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config = self._load_config(config_path or "interchain_mesh_config.yaml")
        self._setup_directories()
        self._init_account()
        self._load_contract_abi()
        self._init_chains()
        self.global_state = GlobalState()
        self.pending_operations = {}
        self.operation_history = {}
        self.running = False
        
        logger.info("Inter-Chain Cognitive Mesh initialized")
    
    def _load_config(self, config_path: str) -> Dict:
        """
        Load configuration from a YAML file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Dict: Configuration dictionary
        """
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            # Default configuration
            return {
                "account": {
                    "private_key": "DISABLED_FOR_SECURITY"  # Use SecureTransactionSigner instead
                },
                "chains": [
                    {
                        "chain_id": 1,
                        "name": "Ethereum Mainnet",
                        "rpc_url": os.getenv("ETH_RPC_URL", ""),
                        "mesh_address": os.getenv("ETH_MESH_ADDRESS", "")
                    },
                    {
                        "chain_id": 137,
                        "name": "Polygon",
                        "rpc_url": os.getenv("POLYGON_RPC_URL", ""),
                        "mesh_address": os.getenv("POLYGON_MESH_ADDRESS", "")
                    }
                ],
                "paths": {
                    "contract_abi": "./abi/InterChainCognitiveMesh.json",
                    "state_dir": "./mesh_state",
                    "operations_dir": "./mesh_operations"
                },
                "sync": {
                    "interval_seconds": 15,
                    "max_operations_per_batch": 10,
                    "max_retries": 3,
                    "retry_delay_seconds": 5
                }
            }
    
    def _setup_directories(self):
        """
        Create necessary directories if they don't exist.
        """
        for path_key in ["state_dir", "operations_dir"]:
            path = self.config["paths"].get(path_key)
            if path and not os.path.exists(path):
                os.makedirs(path)
                logger.info(f"Created directory: {path}")
    
    def _init_account(self):
        """
        Initialize the account.
        """
        try:
            private_key = self.config["account"]["private_key"]
            # SECURITY: Use secure transaction signer instead of private key
try:
    from secure_transaction_signer import SecureTransactionSigner
    self.signer = SecureTransactionSigner()
    self.account = self.signer.get_account()
except ImportError:
    raise RuntimeError("SECURITY ERROR: SecureTransactionSigner not available.")
            logger.info(f"Account initialized: {self.account.address}")
        except Exception as e:
            logger.error(f"Error initializing account: {e}")
            raise
    
    def _load_contract_abi(self):
        """
        Load the contract ABI.
        """
        try:
            abi_path = self.config["paths"]["contract_abi"]
            with open(abi_path, 'r') as file:
                self.contract_abi = json.load(file)
            logger.info(f"Contract ABI loaded from {abi_path}")
        except Exception as e:
            logger.error(f"Error loading contract ABI: {e}")
            raise
    
    def _init_chains(self):
        """
        Initialize chain connections.
        """
        self.chains = {}
        
        for chain_config in self.config["chains"]:
            chain_id = chain_config["chain_id"]
            name = chain_config["name"]
            rpc_url = chain_config["rpc_url"]
            mesh_address = chain_config["mesh_address"]
            
            self.chains[chain_id] = ChainConnection(chain_id, name, rpc_url, mesh_address)
            logger.info(f"Chain connection initialized: {name} (Chain ID: {chain_id})")
    
    async def connect_chains(self):
        """
        Connect to all chains.
        """
        logger.info("Connecting to chains...")
        
        for chain_id, chain in self.chains.items():
            await chain.connect(self.contract_abi)
    
    async def update_chain_status(self):
        """
        Update status for all chains.
        """
        for chain_id, chain in self.chains.items():
            if chain.is_connected:
                await chain.update_status()
    
    async def sync_global_state(self):
        """
        Synchronize global state across all chains.
        """
        logger.info("Synchronizing global state...")
        
        for chain_id, chain in self.chains.items():
            if not chain.is_connected:
                continue
            
            try:
                # Get all state keys from the chain
                state_keys = await self._get_state_keys(chain)
                
                for key in state_keys:
                    # Get state entry from the chain
                    value, last_updated, update_chain_id, version = await self._get_state_entry(chain, key)
                    
                    # Get current state entry
                    current_value, current_last_updated, current_update_chain, current_version = self.global_state.get(key)
                    
                    # Update global state if the chain has a newer version
                    if version > current_version:
                        self.global_state.update(key, value, chain_id)
                        logger.info(f"Updated global state: {key} (Chain ID: {chain_id}, Version: {version})")
            
            except Exception as e:
                logger.error(f"Error synchronizing global state from chain {chain_id}: {e}")
    
    async def _get_state_keys(self, chain: ChainConnection) -> List[str]:
        """
        Get all state keys from a chain.
        
        Args:
            chain: Chain connection
            
        Returns:
            List[str]: List of state keys
        """
        try:
            keys = await asyncio.to_thread(
                chain.mesh_contract.functions.getAllStateKeys().call
            )
            return keys
        except Exception as e:
            logger.error(f"Error getting state keys from {chain.name} (Chain ID: {chain.chain_id}): {e}")
            return []
    
    async def _get_state_entry(self, chain: ChainConnection, key: str) -> Tuple[Any, int, int, int]:
        """
        Get a state entry from a chain.
        
        Args:
            chain: Chain connection
            key: State key
            
        Returns:
            Tuple[Any, int, int, int]: (value, last_updated, update_chain, version)
        """
        try:
            value, last_updated, update_chain, version = await asyncio.to_thread(
                chain.mesh_contract.functions.getGlobalState(key).call
            )
            return value, last_updated, update_chain, version
        except Exception as e:
            logger.error(f"Error getting state entry from {chain.name} (Chain ID: {chain.chain_id}): {e}")
            return None, 0, 0, 0
    
    async def update_global_state(self, key: str, value: Any):
        """
        Update global state on all chains.
        
        Args:
            key: State key
            value: State value
        """
        logger.info(f"Updating global state: {key}")
        
        # Update local state first
        self.global_state.update(key, value, 0)
        
        # Create signature
        message_hash = Web3.solidity_keccak(
            ["bytes32", "bytes", "uint256", "uint256"],
            [key, value, 0, int(time.time())]
        )
        
        message = encode_defunct(message_hash)
        signed_message = self.account.sign_message(message)
        
        # Update state on all chains
        for chain_id, chain in self.chains.items():
            if not chain.is_connected:
                continue
            
            try:
                tx = chain.mesh_contract.functions.updateGlobalState(
                    key,
                    value,
                    signed_message.signature
                ).build_transaction({
                    'from': self.account.address,
                    'nonce': chain.w3.eth.get_transaction_count(self.account.address),
                    'gas': 500000,
                    'gasPrice': chain.gas_price
                })
                
                signed_tx = self.account.sign_transaction(tx)
                tx_hash = chain.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                
                receipt = chain.w3.eth.wait_for_transaction_receipt(tx_hash)
                
                if receipt.status == 1:
                    logger.info(f"Updated global state on {chain.name} (Chain ID: {chain.chain_id}): {key}")
                else:
                    logger.error(f"Failed to update global state on {chain.name} (Chain ID: {chain.chain_id}): {key}")
            
            except Exception as e:
                logger.error(f"Error updating global state on {chain.name} (Chain ID: {chain.chain_id}): {e}")
    
    async def create_operation(self, source_chain_id: int, target_chain_id: int, payload: bytes, 
                              gas_limit: int, value: int, deadline: int) -> Optional[str]:
        """
        Create a cross-chain operation.
        
        Args:
            source_chain_id: Source chain ID
            target_chain_id: Target chain ID
            payload: Operation payload
            gas_limit: Gas limit
            value: Value in wei
            deadline: Deadline timestamp
            
        Returns:
            Optional[str]: Operation ID or None if creation failed
        """
        logger.info(f"Creating operation: {source_chain_id} -> {target_chain_id}")
        
        source_chain = self.chains.get(source_chain_id)
        if not source_chain or not source_chain.is_connected:
            logger.error(f"Source chain not connected: {source_chain_id}")
            return None
        
        try:
            # Create operation on the source chain
            tx = source_chain.mesh_contract.functions.createOperation(
                target_chain_id,
                payload,
                gas_limit,
                deadline
            ).build_transaction({
                'from': self.account.address,
                'nonce': source_chain.w3.eth.get_transaction_count(self.account.address),
                'gas': 500000,
                'gasPrice': source_chain.gas_price,
                'value': value
            })
            
            signed_tx = self.account.sign_transaction(tx)
            tx_hash = source_chain.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            receipt = source_chain.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                # Get operation ID from event
                operation_id = None
                for log in source_chain.mesh_contract.events.OperationCreated().process_receipt(receipt):
                    operation_id = log.args.operationId.hex()
                
                if operation_id:
                    logger.info(f"Operation created: {operation_id}")
                    
                    # Create pending operation
                    operation = PendingOperation(
                        operation_id,
                        source_chain_id,
                        target_chain_id,
                        self.account.address,
                        payload,
                        gas_limit,
                        value,
                        deadline
                    )
                    
                    self.pending_operations[operation_id] = operation
                    
                    # Save operation to disk
                    self._save_operation(operation)
                    
                    return operation_id
                else:
                    logger.error("Failed to get operation ID from event")
                    return None
            else:
                logger.error(f"Operation creation failed: {tx_hash.hex()}")
                return None
        
        except Exception as e:
            logger.error(f"Error creating operation: {e}")
            return None
    
    async def execute_operation(self, operation_id: str):
        """
        Execute a cross-chain operation.
        
        Args:
            operation_id: Operation ID
        """
        logger.info(f"Executing operation: {operation_id}")
        
        operation = self.pending_operations.get(operation_id)
        if not operation:
            logger.error(f"Operation not found: {operation_id}")
            return
        
        target_chain = self.chains.get(operation.target_chain_id)
        if not target_chain or not target_chain.is_connected:
            logger.error(f"Target chain not connected: {operation.target_chain_id}")
            return
        
        try:
            # Create signature
            message_hash = Web3.solidity_keccak(
                ["bytes32", "uint256", "uint256", "address", "bytes", "uint256"],
                [
                    operation.operation_id,
                    operation.source_chain_id,
                    operation.target_chain_id,
                    operation.initiator,
                    operation.payload,
                    operation.value
                ]
            )
            
            message = encode_defunct(message_hash)
            signed_message = self.account.sign_message(message)
            
            # Execute operation on the target chain
            tx = target_chain.mesh_contract.functions.executeOperation(
                operation.operation_id,
                operation.source_chain_id,
                operation.initiator,
                operation.payload,
                operation.value,
                signed_message.signature
            ).build_transaction({
                'from': self.account.address,
                'nonce': target_chain.w3.eth.get_transaction_count(self.account.address),
                'gas': operation.gas_limit,
                'gasPrice': target_chain.gas_price,
                'value': operation.value
            })
            
            signed_tx = self.account.sign_transaction(tx)
            tx_hash = target_chain.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            receipt = target_chain.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                # Get result from event
                result = None
                for log in target_chain.mesh_contract.events.OperationExecuted().process_receipt(receipt):
                    if log.args.operationId.hex() == operation_id:
                        result = log.args.result
                
                # Update operation status
                operation.status = "Completed"
                operation.executed_at = time.time()
                operation.result = result
                
                # Move to history
                self.operation_history[operation_id] = operation
                del self.pending_operations[operation_id]
                
                # Save operation to disk
                self._save_operation(operation)
                
                logger.info(f"Operation executed successfully: {operation_id}")
            else:
                # Update operation status
                operation.status = "Failed"
                operation.retries += 1
                
                # Save operation to disk
                self._save_operation(operation)
                
                logger.error(f"Operation execution failed: {operation_id}")
        
        except Exception as e:
            # Update operation status
            operation.status = "Failed"
            operation.retries += 1
            
            # Save operation to disk
            self._save_operation(operation)
            
            logger.error(f"Error executing operation: {e}")
    
    def _save_operation(self, operation: PendingOperation):
        """
        Save an operation to disk.
        
        Args:
            operation: Operation to save
        """
        try:
            operations_dir = self.config["paths"]["operations_dir"]
            file_path = os.path.join(operations_dir, f"{operation.operation_id}.json")
            
            with open(file_path, 'w') as file:
                json.dump(operation.to_dict(), file, indent=2)
        
        except Exception as e:
            logger.error(f"Error saving operation: {e}")
    
    def _load_operations(self):
        """
        Load operations from disk.
        """
        try:
            operations_dir = self.config["paths"]["operations_dir"]
            
            if not os.path.exists(operations_dir):
                return
            
            for file_name in os.listdir(operations_dir):
                if file_name.endswith(".json"):
                    file_path = os.path.join(operations_dir, file_name)
                    
                    with open(file_path, 'r') as file:
                        data = json.load(file)
                        operation = PendingOperation.from_dict(data)
                        
                        if operation.status == "Pending":
                            self.pending_operations[operation.operation_id] = operation
                        else:
                            self.operation_history[operation.operation_id] = operation
        
        except Exception as e:
            logger.error(f"Error loading operations: {e}")
    
    async def process_pending_operations(self):
        """
        Process pending operations.
        """
        logger.info(f"Processing {len(self.pending_operations)} pending operations")
        
        operations_to_process = list(self.pending_operations.values())
        max_operations = self.config["sync"]["max_operations_per_batch"]
        
        # Sort by creation time (oldest first)
        operations_to_process.sort(key=lambda op: op.created_at)
        
        # Limit the number of operations to process
        operations_to_process = operations_to_process[:max_operations]
        
        for operation in operations_to_process:
            # Skip operations that have exceeded max retries
            if operation.retries >= operation.max_retries:
                logger.warning(f"Operation exceeded max retries: {operation.operation_id}")
                operation.status = "Failed"
                self.operation_history[operation.operation_id] = operation
                del self.pending_operations[operation.operation_id]
                self._save_operation(operation)
                continue
            
            # Skip operations that have expired
            if operation.deadline < time.time():
                logger.warning(f"Operation expired: {operation.operation_id}")
                operation.status = "Failed"
                self.operation_history[operation.operation_id] = operation
                del self.pending_operations[operation.operation_id]
                self._save_operation(operation)
                continue
            
            # Execute the operation
            await self.execute_operation(operation.operation_id)
    
    async def run(self):
        """
        Run the Inter-Chain Cognitive Mesh.
        """
        logger.info("Starting Inter-Chain Cognitive Mesh")
        
        self.running = True
        
        # Connect to chains
        await self.connect_chains()
        
        # Load operations from disk
        self._load_operations()
        
        # Main loop
        while self.running:
            try:
                # Update chain status
                await self.update_chain_status()
                
                # Synchronize global state
                await self.sync_global_state()
                
                # Process pending operations
                await self.process_pending_operations()
                
                # Sleep
                await asyncio.sleep(self.config["sync"]["interval_seconds"])
            
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(self.config["sync"]["retry_delay_seconds"])
        
        logger.info("Inter-Chain Cognitive Mesh stopped")
    
    def stop(self):
        """
        Stop the Inter-Chain Cognitive Mesh.
        """
        logger.info("Stopping Inter-Chain Cognitive Mesh")
        self.running = False

async def main():
    """
    Main function to run the Inter-Chain Cognitive Mesh.
    """
    try:
        mesh = InterChainCognitiveMesh()
        await mesh.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())