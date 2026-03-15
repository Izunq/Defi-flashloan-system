"""
Contract filter for filtering transactions.
"""
import logging
from typing import Dict, Any, List, Optional, Set
from web3 import Web3

logger = logging.getLogger(__name__)

class ContractFilter:
    """Filter for contract interactions."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the contract filter."""
        self.enabled = config.get("enabled", False)
        self.contracts = {}
        self.transaction_types = set(config.get("transaction_types", []))
        
        # Process contract configurations
        for contract in config.get("contracts", []):
            address = contract.get("address", "").lower()
            if not address or not Web3.is_address(address):
                logger.warning(f"Invalid contract address: {address}")
                continue
            
            self.contracts[address] = {
                "name": contract.get("name", "Unknown Contract"),
                "events": {event.get("name", "Unknown Event") for event in contract.get("events", [])}
            }
        
        logger.info(f"Contract filter initialized with {len(self.contracts)} contracts")
    
    def is_contract_creation(self, transaction: Dict[str, Any]) -> bool:
        """Check if a transaction is a contract creation."""
        return transaction.get("to") is None and transaction.get("input", "0x") != "0x"
    
    def is_contract_interaction(self, transaction: Dict[str, Any]) -> bool:
        """Check if a transaction is a contract interaction."""
        to_address = transaction.get("to", "").lower()
        input_data = transaction.get("input", "0x")
        
        # Check if it's a contract interaction (has input data)
        return to_address and input_data and input_data != "0x"
    
    def is_token_transfer(self, transaction: Dict[str, Any]) -> bool:
        """Check if a transaction is a token transfer."""
        to_address = transaction.get("to", "").lower()
        input_data = transaction.get("input", "0x")
        
        # Check if it's a token transfer (ERC20 transfer function signature)
        if to_address and input_data and len(input_data) >= 10:
            # ERC20 transfer function signature: 0xa9059cbb
            return input_data.startswith("0xa9059cbb")
        
        return False
    
    def get_transaction_type(self, transaction: Dict[str, Any]) -> Optional[str]:
        """Get the type of a transaction."""
        if self.is_contract_creation(transaction):
            return "contract_creation"
        elif self.is_token_transfer(transaction):
            return "token_transfer"
        elif self.is_contract_interaction(transaction):
            return "contract_interaction"
        else:
            return "value_transfer"
    
    def get_function_signature(self, transaction: Dict[str, Any]) -> Optional[str]:
        """Get the function signature of a transaction."""
        input_data = transaction.get("input", "0x")
        
        if input_data and len(input_data) >= 10:
            return input_data[:10]
        
        return None
    
    def should_process_transaction(self, transaction: Dict[str, Any]) -> bool:
        """Check if a transaction should be processed."""
        if not self.enabled:
            return True
        
        # If no transaction types are specified, process all transactions
        if not self.transaction_types:
            return True
        
        # Get transaction type
        tx_type = self.get_transaction_type(transaction)
        
        # Check if transaction type is in the list of types to process
        return tx_type in self.transaction_types
    
    def should_process_contract(self, address: str) -> bool:
        """Check if a contract should be processed."""
        if not self.enabled:
            return True
        
        # If no contracts are specified, process all contracts
        if not self.contracts:
            return True
        
        # Check if contract is in the list of contracts to process
        return address.lower() in self.contracts
    
    def get_contracts_of_interest(self) -> List[str]:
        """Get the list of contracts of interest."""
        return list(self.contracts.keys())
    
    def get_contract_name(self, address: str) -> str:
        """Get the name of a contract."""
        contract = self.contracts.get(address.lower())
        if contract:
            return contract.get("name", "Unknown Contract")
        return "Unknown Contract"
    
    def get_contract_events(self, address: str) -> Set[str]:
        """Get the events of a contract."""
        contract = self.contracts.get(address.lower())
        if contract:
            return contract.get("events", set())
        return set()