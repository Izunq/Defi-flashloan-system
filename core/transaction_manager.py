"""
Transaction Manager Module
-------------------------
This module is responsible for securely sending transactions to the blockchain.
It interacts with the MyArbitrageContract we created in Phase 1.
"""

from web3 import Web3
import os
import json
from dotenv import load_dotenv

load_dotenv()

class TransactionManager:
    def __init__(self):
        self.node_url = os.getenv("INFURA_URL")
        self.private_key = os.getenv("EXECUTOR_PRIVATE_KEY")
        self.contract_address = os.getenv("ARBITRAGE_CONTRACT_ADDRESS")
        
        if not all([self.node_url, self.private_key, self.contract_address]):
            raise ValueError("Missing required environment variables for TransactionManager")

        self.w3 = Web3(Web3.HTTPProvider(self.node_url))
        self.account = self.w3.eth.account.from_key(self.private_key)
        
        # Load Contract ABI - Using the MyArbitrageContract we created in Phase 1
        try:
            # Try to load from a standard location
            with open('contracts/MyArbitrageContract.json', 'r') as f:
                contract_abi = json.load(f)['abi']
        except (FileNotFoundError, json.JSONDecodeError):
            # Fallback to a hardcoded minimal ABI with just the executeFlashLoan function
            contract_abi = [
                {
                    "inputs": [
                        {"internalType": "address", "name": "asset", "type": "address"},
                        {"internalType": "uint256", "name": "amount", "type": "uint256"}
                    ],
                    "name": "executeFlashLoan",
                    "outputs": [],
                    "stateMutability": "nonpayable",
                    "type": "function"
                }
            ]
        
        self.contract = self.w3.eth.contract(address=self.contract_address, abi=contract_abi)

    def execute_flashloan_trade(self, asset: str, amount: int):
        """
        Execute a flash loan trade through our secure contract.
        
        Args:
            asset: Address of the token to borrow
            amount: Amount to borrow (in smallest units, e.g., wei)
        """
        from core.event_bus import event_bus # Local import to avoid circular dependency
        print(f"[TX_MANAGER] Preparing to execute flash loan for {amount} of {asset}")
        
        try:
            # Build transaction
            tx_params = {
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gasPrice': self.w3.eth.gas_price,
            }

            # Build the contract function call
            # This calls the executeFlashLoan function we implemented in MyArbitrageContract
            flashloan_tx = self.contract.functions.executeFlashLoan(asset, amount).build_transaction(tx_params)

            # Sign transaction
            signed_tx = self.w3.eth.account.sign_transaction(flashloan_tx, self.private_key)

            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            print(f"[TX_MANAGER] Transaction sent! Hash: {tx_hash.hex()}")
            event_bus.publish('monitoring-events', {'status': 'success', 'message': f'Trade submitted', 'tx_hash': tx_hash.hex()})

            # Wait for receipt
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if tx_receipt['status'] == 1:
                print(f"[TX_MANAGER] Transaction successful!")
                event_bus.publish('monitoring-events', {'status': 'success', 'message': f'Trade confirmed!', 'tx_hash': tx_hash.hex()})
            else:
                print(f"[TX_MANAGER] Transaction failed!")
                event_bus.publish('monitoring-events', {'status': 'error', 'message': f'On-chain transaction failed!', 'tx_hash': tx_hash.hex()})

        except Exception as e:
            print(f"[TX_MANAGER] Error executing transaction: {e}")
            event_bus.publish('monitoring-events', {'status': 'error', 'message': f'Transaction manager failure: {e}'})

# Singleton instance
transaction_manager = TransactionManager()