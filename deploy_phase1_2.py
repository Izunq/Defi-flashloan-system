"""
Deployment Script for Phase 1 & 2
-------------------------------
This script deploys the Phase 1 smart contracts and configures the Phase 2 backend.
"""

import os
import json
import time
from dotenv import load_dotenv
from web3 import Web3

# Load environment variables
load_dotenv()

# Connect to Ethereum node
INFURA_URL = os.getenv("INFURA_URL")
PRIVATE_KEY = os.getenv("DEPLOYER_PRIVATE_KEY")

if not INFURA_URL or not PRIVATE_KEY:
    print("❌ Missing required environment variables. Please check your .env file.")
    exit(1)

w3 = Web3(Web3.HTTPProvider(INFURA_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)
print(f"Connected to network: {w3.net.version}")
print(f"Deployer address: {account.address}")
print(f"Deployer balance: {w3.from_wei(w3.eth.get_balance(account.address), 'ether')} ETH")

# Contract deployment function
def deploy_contract(contract_name, abi, bytecode, constructor_args=None):
    """
    Deploy a contract to the blockchain.
    
    Args:
        contract_name: Name of the contract
        abi: Contract ABI
        bytecode: Contract bytecode
        constructor_args: Constructor arguments (optional)
    
    Returns:
        Deployed contract address
    """
    print(f"\n=== Deploying {contract_name} ===")
    
    # Create contract object
    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    # Build constructor transaction
    if constructor_args:
        tx_constructor = Contract.constructor(*constructor_args).build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': 5000000,
            'gasPrice': w3.eth.gas_price
        })
    else:
        tx_constructor = Contract.constructor().build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': 5000000,
            'gasPrice': w3.eth.gas_price
        })
    
    # Sign and send transaction
    signed_tx = w3.eth.account.sign_transaction(tx_constructor, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    
    print(f"Transaction sent: {tx_hash.hex()}")
    print("Waiting for confirmation...")
    
    # Wait for transaction receipt
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    contract_address = tx_receipt.contractAddress
    
    print(f"✅ {contract_name} deployed at: {contract_address}")
    return contract_address

# Load contract data
def load_contract_data(file_path):
    """
    Load contract ABI and bytecode from a JSON file.
    
    Args:
        file_path: Path to the JSON file
    
    Returns:
        Tuple of (abi, bytecode)
    """
    try:
        with open(file_path, 'r') as f:
            contract_data = json.load(f)
        return contract_data['abi'], contract_data['bytecode']
    except Exception as e:
        print(f"❌ Error loading contract data: {e}")
        return None, None

# Main deployment function
def deploy_phase1_contracts():
    """
    Deploy all Phase 1 contracts.
    
    Returns:
        Dictionary with deployed contract addresses
    """
    deployed_contracts = {}
    
    # Deploy SystemAccessControl
    system_access_control_abi, system_access_control_bytecode = load_contract_data('build/contracts/SystemAccessControl.json')
    if system_access_control_abi and system_access_control_bytecode:
        # Deploy with initial admin, executor, and pauser (all set to deployer for now)
        deployed_contracts['SystemAccessControl'] = deploy_contract(
            'SystemAccessControl',
            system_access_control_abi,
            system_access_control_bytecode,
            [account.address, account.address, account.address]
        )
    
    # Deploy SecurePriceOracle
    secure_price_oracle_abi, secure_price_oracle_bytecode = load_contract_data('build/contracts/SecurePriceOracle.json')
    if secure_price_oracle_abi and secure_price_oracle_bytecode:
        deployed_contracts['SecurePriceOracle'] = deploy_contract(
            'SecurePriceOracle',
            secure_price_oracle_abi,
            secure_price_oracle_bytecode
        )
    
    # Deploy MyArbitrageContract
    my_arbitrage_contract_abi, my_arbitrage_contract_bytecode = load_contract_data('build/contracts/MyArbitrageContract.json')
    if my_arbitrage_contract_abi and my_arbitrage_contract_bytecode:
        # Use a placeholder for lending pool provider if not available
        lending_pool_provider = os.getenv("LENDING_POOL_PROVIDER", "${CONTRACT_ADDRESS}")  # Aave V2 on Mainnet
        
        deployed_contracts['MyArbitrageContract'] = deploy_contract(
            'MyArbitrageContract',
            my_arbitrage_contract_abi,
            my_arbitrage_contract_bytecode,
            [
                lending_pool_provider,
                deployed_contracts.get('SecurePriceOracle', '${CONTRACT_ADDRESS}'),
                account.address,  # initialAdmin
                account.address,  # initialExecutor
                account.address   # initialPauser
            ]
        )
    
    return deployed_contracts

# Update .env file with deployed contract addresses
def update_env_file(deployed_contracts):
    """
    Update the .env file with deployed contract addresses.
    
    Args:
        deployed_contracts: Dictionary with deployed contract addresses
    """
    print("\n=== Updating .env File ===")
    
    # Read existing .env file
    env_content = ""
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            env_content = f.read()
    
    # Update contract addresses
    for contract_name, address in deployed_contracts.items():
        env_var_name = f"{contract_name.upper()}_ADDRESS"
        
        # Check if variable already exists
        if f"{env_var_name}=" in env_content:
            # Replace existing value
            env_content = env_content.replace(
                f"{env_var_name}=0x{env_var_name.lower()}_address_here",
                f"{env_var_name}={address}"
            )
            env_content = env_content.replace(
                f"{env_var_name}=0x{env_var_name}_ADDRESS_HERE",
                f"{env_var_name}={address}"
            )
            env_content = env_content.replace(
                f"{env_var_name}=0xYOUR_DEPLOYED_{env_var_name}_HERE",
                f"{env_var_name}={address}"
            )
        else:
            # Add new variable
            env_content += f"\n{env_var_name}={address}"
    
    # Special case for ARBITRAGE_CONTRACT_ADDRESS
    if 'MyArbitrageContract' in deployed_contracts:
        if "ARBITRAGE_CONTRACT_ADDRESS=" in env_content:
            env_content = env_content.replace(
                "ARBITRAGE_CONTRACT_ADDRESS=0xYOUR_DEPLOYED_CONTRACT_ADDRESS",
                f"ARBITRAGE_CONTRACT_ADDRESS={deployed_contracts['MyArbitrageContract']}"
            )
        else:
            env_content += f"\nARBITRAGE_CONTRACT_ADDRESS={deployed_contracts['MyArbitrageContract']}"
    
    # Write updated content back to .env file
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ .env file updated with deployed contract addresses")

# Main function
if __name__ == "__main__":
    print("=== Phase 1 & 2 Deployment Script ===")
    
    # Check if build directory exists
    if not os.path.exists('build/contracts'):
        print("❌ Contract build files not found. Please compile contracts first.")
        print("Run: truffle compile")
        exit(1)
    
    # Deploy Phase 1 contracts
    deployed_contracts = deploy_phase1_contracts()
    
    if deployed_contracts:
        # Update .env file
        update_env_file(deployed_contracts)
        
        print("\n=== Deployment Complete ===")
        print("Phase 1 contracts have been deployed and .env file has been updated.")
        print("You can now run the Phase 2 backend with: python main.py")
    else:
        print("\n❌ Deployment failed. Please check the errors above.")