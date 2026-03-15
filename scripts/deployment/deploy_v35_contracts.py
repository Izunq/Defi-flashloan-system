#!/usr/bin/env python3
"""
V35 Contracts Deployment Script - Cognitive Kernel (Proof-Aware)
This script deploys the V35 contracts for the proof-aware architecture.
"""

import json
import os
from web3 import Web3
from dotenv import load_dotenv
from eth_account import Account
import time

# Load environment variables
load_dotenv()

# Connect to the blockchain
RPC_URL = os.getenv("RPC_URL", "http://localhost:8545")
# SECURITY: Private key handling has been completely removed for security

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(RPC_URL))
# SECURITY: Use secure transaction signer instead of private key
try:
    from secure_transaction_signer import SecureTransactionSigner
    signer = SecureTransactionSigner()
    account = signer.get_account()
except ImportError:
    raise RuntimeError("SECURITY ERROR: SecureTransactionSigner not available. Direct private key usage is prohibited.")
    
print(f"Connected to network: {w3.net.version}")
print(f"Deployer address: {account.address}")
print(f"Deployer balance: {w3.from_wei(w3.eth.get_balance(account.address), 'ether')} ETH")

# Contract ABIs
def load_abi(contract_name):
    with open(f"abi/{contract_name}.json", "r") as f:
        return json.load(f)

# Contract bytecode
def load_bytecode(contract_name):
    with open(f"bytecode/{contract_name}.bin", "r") as f:
        return f.read().strip()

def deploy_contract(contract_name, abi, bytecode, *args):
    """Deploy a contract with the given arguments"""
    print(f"Deploying {contract_name}...")
    
    # Create contract object
    contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    # Build transaction
    construct_txn = contract.constructor(*args).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 5000000,
        'gasPrice': w3.eth.gas_price
    })
    
    # Sign transaction
    signed = account.sign_transaction(construct_txn)
    
    # Send transaction
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(f"Transaction sent: {tx_hash.hex()}")
    
    # Wait for transaction receipt
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    contract_address = tx_receipt.contractAddress
    
    print(f"{contract_name} deployed at: {contract_address}")
    return contract_address

def main():
    """Main deployment function"""
    print("Starting V35 contracts deployment...")
    
    # Load existing contract addresses if available
    try:
        with open("v35_contract_addresses.json", "r") as f:
            deployed_contracts = json.load(f)
    except FileNotFoundError:
        deployed_contracts = {}
    
    # Deploy TrustCurve
    trust_curve_abi = load_abi("TrustCurve")
    trust_curve_bytecode = load_bytecode("TrustCurve")
    trust_curve_address = deploy_contract("TrustCurve", trust_curve_abi, trust_curve_bytecode)
    deployed_contracts["TrustCurve"] = trust_curve_address
    
    # Get Aave lending pool address (use mock for testing)
    mudarabah_flash_swap_address = os.getenv("MUDARABAH_FLASH_SWAP_ADDRESS", "")
    
    # Deploy ProofAwareExecutorV35
    fee_collector = account.address  # Use deployer as fee collector for now
    executor_abi = load_abi("ProofAwareExecutorV35")
    executor_bytecode = load_bytecode("ProofAwareExecutorV35")
    executor_address = deploy_contract(
        "ProofAwareExecutorV35", 
        executor_abi, 
        executor_bytecode, 
        trust_curve_address, 
        aave_pool_address, 
        fee_collector
    )
    deployed_contracts["ProofAwareExecutorV35"] = executor_address
    
    # Deploy AIStrategyV35 (example)
    strategy_abi = load_abi("AIStrategyV35")
    strategy_bytecode = load_bytecode("AIStrategyV35")
    
    # Example strategy parameters
    strategy_id = 1
    strategy_name = "Flash Arbitrage V2 (Polygon)"
    strategy_description = "Cross-DEX arbitrage strategy on Polygon"
    base_max_capital = 5000  # 50% in basis points
    base_min_profit = 100    # 1% in basis points
    base_max_slippage = 50   # 0.5% in basis points
    base_max_gas_price = 100 # 100 gwei
    base_emergency_threshold = 1000  # 10% in basis points
    
    strategy_address = deploy_contract(
        "AIStrategyV35",
        strategy_abi,
        strategy_bytecode,
        trust_curve_address,
        strategy_id,
        strategy_name,
        strategy_description,
        base_max_capital,
        base_min_profit,
        base_max_slippage,
        base_max_gas_price,
        base_emergency_threshold
    )
    deployed_contracts["AIStrategyV35_Example"] = strategy_address
    
    # Save deployed contract addresses
    with open("v35_contract_addresses.json", "w") as f:
        json.dump(deployed_contracts, f, indent=2)
    
    print("V35 contracts deployment completed!")
    print(f"Contract addresses saved to v35_contract_addresses.json")

if __name__ == "__main__":
    main()