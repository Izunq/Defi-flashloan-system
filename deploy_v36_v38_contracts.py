#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Deployment script for V36-V38 contracts
- IntentInterpreterV36
- StrategyGeneratorV37
- SwarmIntelligenceV38
"""

import os
import json
import time
import logging
from web3 import Web3
from eth_account import Account
from solcx import compile_source, install_solc
from typing import Dict, List, Tuple, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DeployV36V38")

# Constants
CONTRACTS_DIR = "contracts"
ABI_DIR = "abi"

def load_env_variables():
    """Load environment variables"""
    from dotenv import load_dotenv
    load_dotenv()
    
    # Required environment variables
    required_vars = ['PRIVATE_KEY', 'WEB3_PROVIDER']
    
    for var in required_vars:
        if not os.environ.get(var):
            raise ValueError(f"Missing required environment variable: {var}")
    
    return {
        'private_key': os.environ.get('PRIVATE_KEY'),
        'web3_provider': os.environ.get('WEB3_PROVIDER'),
        'trust_curve_address': os.environ.get('TRUST_CURVE_ADDRESS'),
        'strategy_incubator_address': os.environ.get('STRATEGY_INCUBATOR_ADDRESS')
    }

def init_web3(provider_url: str):
    """Initialize Web3 connection"""
    web3 = Web3(Web3.HTTPProvider(provider_url))
    
    if not web3.is_connected():
        raise ConnectionError(f"Failed to connect to Web3 provider at {provider_url}")
    
    logger.info(f"Connected to Web3 provider at {provider_url}")
    logger.info(f"Current block number: {web3.eth.block_number}")
    
    return web3

def compile_contract(contract_path: str, contract_name: str):
    """Compile a contract"""
    with open(contract_path, 'r') as f:
        source = f.read()
    
    # Ensure solc is installed
    try:
        install_solc('0.8.20')
    except Exception as e:
        logger.warning(f"Failed to install solc: {e}")
    
    # Compile contract
    compiled_sol = compile_source(
        source,
        output_values=['abi', 'bin'],
        solc_version='0.8.20'
    )
    
    # Get contract interface
    contract_id = f'<stdin>:{contract_name}'
    contract_interface = compiled_sol[contract_id]
    
    return contract_interface

def deploy_contract(web3: Web3, account: Account, contract_interface: Dict, constructor_args: List = None):
    """Deploy a contract"""
    # Create contract object
    Contract = web3.eth.contract(
        abi=contract_interface['abi'],
        bytecode=contract_interface['bin']
    )
    
    # Build constructor transaction
    constructor_kwargs = {'from': account.address}
    if constructor_args:
        tx = Contract.constructor(*constructor_args).build_transaction(constructor_kwargs)
    else:
        tx = Contract.constructor().build_transaction(constructor_kwargs)
    
    # Add gas parameters
    tx['maxFeePerGas'] = web3.to_wei(50, 'gwei')
    tx['maxPriorityFeePerGas'] = web3.to_wei(2, 'gwei')
    tx['nonce'] = web3.eth.get_transaction_count(account.address)
    
    # Sign and send transaction
    signed_tx = account.sign_transaction(tx)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    
    # Wait for transaction receipt
    logger.info(f"Waiting for transaction {tx_hash.hex()} to be mined...")
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    
    # Get contract address
    contract_address = tx_receipt.contractAddress
    
    return contract_address, contract_interface['abi']

def save_abi(abi: List, contract_name: str):
    """Save ABI to file"""
    os.makedirs(ABI_DIR, exist_ok=True)
    
    abi_path = os.path.join(ABI_DIR, f"{contract_name}.json")
    
    with open(abi_path, 'w') as f:
        json.dump(abi, f, indent=2)
    
    logger.info(f"Saved ABI to {abi_path}")

def deploy_intent_interpreter(web3: Web3, account: Account, trust_curve_address: str):
    """Deploy IntentInterpreterV36 contract"""
    logger.info("Deploying IntentInterpreterV36 contract...")
    
    # Compile contract
    contract_path = os.path.join(CONTRACTS_DIR, "IntentInterpreterV36.sol")
    contract_interface = compile_contract(contract_path, "IntentInterpreterV36")
    
    # Deploy contract
    constructor_args = [trust_curve_address]
    contract_address, abi = deploy_contract(web3, account, contract_interface, constructor_args)
    
    logger.info(f"IntentInterpreterV36 deployed at {contract_address}")
    
    # Save ABI
    save_abi(abi, "IntentInterpreterV36")
    
    return contract_address

def deploy_strategy_generator(web3: Web3, account: Account, trust_curve_address: str, incubator_address: str):
    """Deploy StrategyGeneratorV37 contract"""
    logger.info("Deploying StrategyGeneratorV37 contract...")
    
    # Compile contract
    contract_path = os.path.join(CONTRACTS_DIR, "StrategyGeneratorV37.sol")
    contract_interface = compile_contract(contract_path, "StrategyGeneratorV37")
    
    # Deploy contract
    constructor_args = [trust_curve_address, incubator_address]
    contract_address, abi = deploy_contract(web3, account, contract_interface, constructor_args)
    
    logger.info(f"StrategyGeneratorV37 deployed at {contract_address}")
    
    # Save ABI
    save_abi(abi, "StrategyGeneratorV37")
    
    return contract_address

def deploy_swarm_intelligence(web3: Web3, account: Account, trust_curve_address: str, incubator_address: str):
    """Deploy SwarmIntelligenceV38 contract"""
    logger.info("Deploying SwarmIntelligenceV38 contract...")
    
    # Compile contract
    contract_path = os.path.join(CONTRACTS_DIR, "SwarmIntelligenceV38.sol")
    contract_interface = compile_contract(contract_path, "SwarmIntelligenceV38")
    
    # Deploy contract
    constructor_args = [trust_curve_address, incubator_address]
    contract_address, abi = deploy_contract(web3, account, contract_interface, constructor_args)
    
    logger.info(f"SwarmIntelligenceV38 deployed at {contract_address}")
    
    # Save ABI
    save_abi(abi, "SwarmIntelligenceV38")
    
    return contract_address

def update_env_file(env_vars: Dict):
    """Update .env file with new contract addresses"""
    env_path = ".env"
    
    # Read existing .env file
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = f.readlines()
    else:
        lines = []
    
    # Update or add new variables
    for key, value in env_vars.items():
        env_var = f"{key.upper()}={value}"
        
        # Check if variable already exists
        found = False
        for i, line in enumerate(lines):
            if line.startswith(f"{key.upper()}="):
                lines[i] = f"{env_var}\n"
                found = True
                break
        
        # Add new variable if not found
        if not found:
            lines.append(f"{env_var}\n")
    
    # Write updated .env file
    with open(env_path, 'w') as f:
        f.writelines(lines)
    
    logger.info(f"Updated .env file with new contract addresses")

def main():
    """Main entry point"""
    try:
        # Load environment variables
        env_vars = load_env_variables()
        
        # Initialize Web3
        web3 = init_web3(env_vars['web3_provider'])
        
        # Initialize account
        # SECURITY: Use secure transaction signer instead of private key
try:
    from secure_transaction_signer import SecureTransactionSigner
    signer = SecureTransactionSigner()
    account = signer.get_account()
except ImportError:
    raise RuntimeError("SECURITY ERROR: SecureTransactionSigner not available. Direct private key usage is prohibited.")
        logger.info(f"Using account: {account.address}")
        
        # Check account balance
        balance = web3.eth.get_balance(account.address)
        logger.info(f"Account balance: {web3.from_wei(balance, 'ether')} ETH")
        
        if balance < web3.to_wei(0.1, 'ether'):
            logger.warning("Account balance is low, deployment may fail")
        
        # Deploy contracts
        intent_interpreter_address = deploy_intent_interpreter(
            web3, account, env_vars['trust_curve_address']
        )
        
        strategy_generator_address = deploy_strategy_generator(
            web3, account, env_vars['trust_curve_address'], env_vars['strategy_incubator_address']
        )
        
        swarm_intelligence_address = deploy_swarm_intelligence(
            web3, account, env_vars['trust_curve_address'], env_vars['strategy_incubator_address']
        )
        
        # Update .env file
        new_env_vars = {
            'intent_interpreter_address': intent_interpreter_address,
            'strategy_generator_address': strategy_generator_address,
            'swarm_intelligence_address': swarm_intelligence_address
        }
        update_env_file(new_env_vars)
        
        # Update config files
        update_config_files(
            intent_interpreter_address,
            strategy_generator_address,
            swarm_intelligence_address
        )
        
        logger.info("Deployment completed successfully!")
        logger.info(f"IntentInterpreterV36: {intent_interpreter_address}")
        logger.info(f"StrategyGeneratorV37: {strategy_generator_address}")
        logger.info(f"SwarmIntelligenceV38: {swarm_intelligence_address}")
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        raise

def update_config_files(intent_interpreter_address: str, strategy_generator_address: str, swarm_intelligence_address: str):
    """Update configuration files with new contract addresses"""
    import yaml
    
    # Update strategy generator config
    sg_config_path = "strategy_generator_config.yaml"
    if os.path.exists(sg_config_path):
        with open(sg_config_path, 'r') as f:
            sg_config = yaml.safe_load(f)
        
        sg_config['contract_addresses']['strategy_generator'] = strategy_generator_address
        
        with open(sg_config_path, 'w') as f:
            yaml.dump(sg_config, f, default_flow_style=False)
        
        logger.info(f"Updated {sg_config_path} with new contract address")
    
    # Update swarm intelligence config
    si_config_path = "swarm_intelligence_config.yaml"
    if os.path.exists(si_config_path):
        with open(si_config_path, 'r') as f:
            si_config = yaml.safe_load(f)
        
        si_config['contract_addresses']['swarm_intelligence'] = swarm_intelligence_address
        
        with open(si_config_path, 'w') as f:
            yaml.dump(si_config, f, default_flow_style=False)
        
        logger.info(f"Updated {si_config_path} with new contract address")

if __name__ == "__main__":
    main()