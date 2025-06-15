#!/usr/bin/env python3
# =================================================================================================
# DEPLOYMENT SCRIPT FOR ERC-4626 ARBITRAGE VAULT
# =================================================================================================

import os
import json
import time
import logging
from web3 import Web3
from dotenv import load_dotenv
from eth_account import Account

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("VaultDeployer")

# Load environment variables
load_dotenv()

# Constants
# SECURITY: Private key handling disabled - use secure transaction signer
WEB3_PROVIDER_URI = os.getenv("WEB3_PROVIDER_URI")
EXECUTOR_ADDRESS = os.getenv("EXECUTOR_ADDRESS")
WETH_ADDRESS = os.getenv("WETH_ADDRESS", "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")  # Mainnet WETH

def load_abi(filename):
    """Load contract ABI from file"""
    with open(os.path.join("abi", filename)) as f:
        return json.load(f)

def deploy_vault():
    """Deploy the ERC-4626 Arbitrage Vault"""
    logger.info("Deploying ERC-4626 Arbitrage Vault...")
    
    # Initialize Web3
    w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URI))
    # SECURITY: Use secure transaction signer instead of private key
try:
    from secure_transaction_signer import SecureTransactionSigner
    signer = SecureTransactionSigner()
    account = signer.get_account()
except ImportError:
    raise RuntimeError("SECURITY ERROR: SecureTransactionSigner not available. Direct private key usage is prohibited.")
    logger.info(f"Deploying from address: {account.address}")
    
    # Check balance
    balance = w3.eth.get_balance(account.address)
    balance_eth = w3.from_wei(balance, 'ether')
    logger.info(f"Account balance: {balance_eth} ETH")
    
    if balance_eth < 0.1:
        logger.error("Insufficient balance for deployment")
        return
    
    # Load contract ABIs
    with open("contracts/ArbitrageVaultERC4626.sol", "r") as f:
        contract_source = f.read()
    
    # Compile contract (in a real scenario, you would use solc or hardhat)
    # For this example, we'll assume the contract is already compiled
    
    # Load contract bytecode and ABI
    try:
        with open("bytecode/ArbitrageVaultERC4626.bin", "r") as f:
            bytecode = f.read().strip()
        
        with open("abi/ArbitrageVaultERC4626.json", "r") as f:
            abi = json.load(f)
    except FileNotFoundError:
        logger.error("Contract bytecode or ABI not found. Please compile the contract first.")
        return
    
    # Initialize contract
    Vault = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    # Deployment parameters
    vault_name = "Arbitrage Profit Vault"
    vault_symbol = "APV"
    initial_performance_fee = 1000  # 10% in basis points
    fee_recipient = account.address
    withdrawal_cooldown = 86400  # 1 day in seconds
    
    # Estimate gas
    gas_estimate = Vault.constructor(
        WETH_ADDRESS,
        vault_name,
        vault_symbol,
        EXECUTOR_ADDRESS,
        account.address,
        initial_performance_fee,
        fee_recipient,
        withdrawal_cooldown
    ).estimate_gas({'from': account.address})
    
    logger.info(f"Estimated gas: {gas_estimate}")
    
    # Build transaction
    transaction = Vault.constructor(
        WETH_ADDRESS,
        vault_name,
        vault_symbol,
        EXECUTOR_ADDRESS,
        account.address,
        initial_performance_fee,
        fee_recipient,
        withdrawal_cooldown
    ).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': int(gas_estimate * 1.2),  # Add 20% buffer
        'gasPrice': w3.eth.gas_price
    })
    
    # Sign and send transaction
    signed_txn = w3.eth.account.sign_transaction(transaction, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    
    logger.info(f"Transaction sent: {tx_hash.hex()}")
    logger.info("Waiting for transaction receipt...")
    
    # Wait for transaction receipt
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    vault_address = tx_receipt.contractAddress
    
    logger.info(f"Vault deployed at: {vault_address}")
    logger.info(f"Transaction status: {'Success' if tx_receipt.status == 1 else 'Failed'}")
    
    # Save deployment info
    deployment_info = {
        'vault_address': vault_address,
        'executor_address': EXECUTOR_ADDRESS,
        'weth_address': WETH_ADDRESS,
        'deployer': account.address,
        'deployment_time': time.time(),
        'transaction_hash': tx_hash.hex(),
        'block_number': tx_receipt.blockNumber
    }
    
    with open('vault_deployment_info.json', 'w') as f:
        json.dump(deployment_info, f, indent=2)
    
    logger.info("Deployment info saved to vault_deployment_info.json")
    
    # Grant executor role to the executor contract
    try:
        vault_contract = w3.eth.contract(address=vault_address, abi=abi)
        executor_role = vault_contract.functions.EXECUTOR_ROLE().call()
        
        tx = vault_contract.functions.grantRole(
            executor_role,
            EXECUTOR_ADDRESS
        ).build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': 200000,
            'gasPrice': w3.eth.gas_price
        })
        
        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        logger.info(f"Granted EXECUTOR_ROLE to {EXECUTOR_ADDRESS}")
        logger.info(f"Transaction: {tx_hash.hex()}")
    except Exception as e:
        logger.error(f"Error granting executor role: {e}")
    
    return vault_address

if __name__ == "__main__":
    if not PRIVATE_KEY or not WEB3_PROVIDER_URI or not EXECUTOR_ADDRESS:
        logger.error("Missing required environment variables. Please check .env file.")
    else:
        deploy_vault()