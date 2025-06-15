#!/usr/bin/env python3
"""
Deployment script for the Halal-Compliant AI Trading & Investment Protocol
"""

import os
import json
import yaml
from web3 import Web3
from dotenv import load_dotenv
from eth_account import Account
from solcx import compile_standard, install_solc

# Load environment variables
load_dotenv()

# Connect to blockchain
RPC_URL = os.getenv("RPC_URL", "http://localhost:8545")
# SECURITY: Private key handling disabled - use secure transaction signer
CHAIN_ID = int(os.getenv("CHAIN_ID", "1"))

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(RPC_URL))
# SECURITY: Use secure transaction signer instead of private key
try:
    from secure_transaction_signer import SecureTransactionSigner
    signer = SecureTransactionSigner()
    account = signer.get_account()
except ImportError:
    raise RuntimeError("SECURITY ERROR: SecureTransactionSigner not available. Direct private key usage is prohibited.")
print(f"Deploying from account: {account.address}")

# Load configuration
with open("halal_config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Install solc
install_solc("0.8.20")

def compile_contract(contract_name):
    """Compile a contract and return the ABI and bytecode"""
    with open(f"contracts/{contract_name}.sol", "r") as f:
        contract_source = f.read()
    
    compiled_sol = compile_standard(
        {
            "language": "Solidity",
            "sources": {f"{contract_name}.sol": {"content": contract_source}},
            "settings": {
                "outputSelection": {
                    "*": {"*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]}
                }
            },
        },
        solc_version="0.8.20",
    )
    
    # Save ABI
    abi = compiled_sol["contracts"][f"{contract_name}.sol"][contract_name]["abi"]
    with open(f"abi/{contract_name}.json", "w") as f:
        json.dump(abi, f)
    
    # Get bytecode
    bytecode = compiled_sol["contracts"][f"{contract_name}.sol"][contract_name]["evm"]["bytecode"]["object"]
    
    return abi, bytecode

def deploy_contract(contract_name, *args):
    """Deploy a contract with arguments and return the contract instance"""
    abi, bytecode = compile_contract(contract_name)
    
    # Create contract
    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    # Build transaction
    nonce = w3.eth.get_transaction_count(account.address)
    transaction = Contract.constructor(*args).build_transaction(
        {
            "chainId": CHAIN_ID,
            "from": account.address,
            "nonce": nonce,
            "gasPrice": w3.eth.gas_price,
        }
    )
    
    # Sign transaction
    signed_txn = w3.eth.account.sign_transaction(transaction, private_key=PRIVATE_KEY)
    
    # Send transaction
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print(f"Deploying {contract_name}... (tx: {tx_hash.hex()})")
    
    # Wait for transaction receipt
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"{contract_name} deployed at: {tx_receipt.contractAddress}")
    
    # Create contract instance
    contract = w3.eth.contract(address=tx_receipt.contractAddress, abi=abi)
    
    # Save contract address
    with open(f"abi/{contract_name}_address.txt", "w") as f:
        f.write(tx_receipt.contractAddress)
    
    return contract

def main():
    """Deploy all contracts for the Halal-Compliant AI Trading & Investment Protocol"""
    print("Deploying Halal-Compliant AI Trading & Investment Protocol...")
    
    # Create directories if they don't exist
    os.makedirs("abi", exist_ok=True)
    
    # Deploy HalalAssetRegistry
    halal_registry = deploy_contract(
        "HalalAssetRegistry",
        account.address,  # admin
        account.address,  # shariah committee
    )
    
    # Deploy MudarabahFlashSwap
    mudarabah_flash_swap = deploy_contract(
        "MudarabahFlashSwap",
        halal_registry.address,  # halal registry
        account.address,  # mudarib treasury
        account.address,  # admin
    )
    
    # Deploy MudarabahInvestmentPool
    mudarabah_investment_pool = deploy_contract(
        "MudarabahInvestmentPool",
        halal_registry.address,  # halal registry
        account.address,  # admin
        account.address,  # mudarib
        account.address,  # shariah advisor
        account.address,  # risk manager
        account.address,  # zakat manager
        account.address,  # AI agent
        account.address,  # zakat treasury
    )
    
    # Deploy StrategyLeasingPlatform
    strategy_leasing_platform = deploy_contract(
        "StrategyLeasingPlatform",
        halal_registry.address,  # halal registry
        account.address,  # fee treasury
        account.address,  # admin
        account.address,  # shariah committee
    )
    
    # Deploy TakafulPool
    takaful_pool = deploy_contract(
        "TakafulPool",
        halal_registry.address,  # halal registry
        account.address,  # admin
        account.address,  # shariah committee
        account.address,  # claim manager
        "Halal Protocol Takaful Pool",  # name
        "Cooperative insurance for the Halal Protocol",  # description
        "0x0000000000000000000000000000000000000000",  # contribution token (placeholder)
        Web3.to_wei(50, "ether"),  # min contribution
    )
    
    # Deploy ZakatManager
    zakat_manager = deploy_contract(
        "ZakatManager",
        halal_registry.address,  # halal registry
        account.address,  # admin
        account.address,  # shariah committee
        account.address,  # zakat distributor
        account.address,  # treasury
        5000 * 10**6,  # gold nisab in USD (6 decimals)
        700 * 10**6,  # silver nisab in USD (6 decimals)
    )
    
    # Deploy SalamFactory
    salam_factory = deploy_contract(
        "SalamFactory",
        halal_registry.address,  # halal registry
        account.address,  # admin
        account.address,  # shariah committee
    )
    
    # Deploy IstisnaFactory
    istisna_factory = deploy_contract(
        "IstisnaFactory",
        halal_registry.address,  # halal registry
        account.address,  # admin
        account.address,  # shariah committee
        account.address,  # auditor
    )
    
    print("Halal-Compliant AI Trading & Investment Protocol deployed successfully!")
    
    # Save deployment information
    deployment_info = {
        "HalalAssetRegistry": halal_registry.address,
        "MudarabahFlashSwap": mudarabah_flash_swap.address,
        "MudarabahInvestmentPool": mudarabah_investment_pool.address,
        "StrategyLeasingPlatform": strategy_leasing_platform.address,
        "TakafulPool": takaful_pool.address,
        "ZakatManager": zakat_manager.address,
        "SalamFactory": salam_factory.address,
        "IstisnaFactory": istisna_factory.address,
    }
    
    with open("halal_deployment_info.json", "w") as f:
        json.dump(deployment_info, f, indent=2)

if __name__ == "__main__":
    main()