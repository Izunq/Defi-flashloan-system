#!/usr/bin/env python3
"""
Contract Deployment Script for Flash Loan Arbitrage System
=========================================================

This script deploys all necessary contracts for the arbitrage system:
1. StrategyIncubatorV33
2. ArbitrageExecutorV33
3. StrategyFactoryV33

Usage:
    python deploy_contracts.py --network mainnet
    python deploy_contracts.py --network testnet --dry-run

Requirements:
    - .env file with RPC_URL and PRIVATE_KEY
    - Sufficient ETH for gas fees
    - Contract bytecode files
"""

import os
import json
import argparse
import time
from typing import Dict, Any, Optional
from web3 import Web3
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ContractDeployer:
    """Contract deployment manager"""
    
    def __init__(self, network: str = 'mainnet', dry_run: bool = False):
        load_dotenv()
        self.network = network
        self.dry_run = dry_run
        self.deployment_results = {}
        
        # Initialize Web3
        self.web3 = self._setup_web3()
        # SECURITY: Use secure transaction signer instead of private key
        try:
            from secure_transaction_signer import SecureTransactionSigner
            self.signer = SecureTransactionSigner()
            self.account = self.signer.get_account()
        except ImportError:
            raise RuntimeError("SECURITY ERROR: SecureTransactionSigner not available. Direct private key usage is prohibited.")
        self.web3.eth.default_account = self.account.address
        
        logger.info(f"Deployer initialized for {network}")
        logger.info(f"Deployer address: {self.account.address}")
        logger.info(f"Balance: {self.web3.from_wei(self.web3.eth.get_balance(self.account.address), 'ether')} ETH")
    
    def _setup_web3(self) -> Web3:
        """Setup Web3 connection"""
        rpc_url = os.getenv('RPC_URL')
        if not rpc_url:
            raise ValueError("RPC_URL not found in environment variables")
        
        web3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if not web3.is_connected():
            raise ConnectionError(f"Could not connect to {rpc_url}")
        
        logger.info(f"Connected to {rpc_url}")
        logger.info(f"Chain ID: {web3.eth.chain_id}")
        
        return web3
    
    def load_contract_data(self, contract_name: str) -> Dict[str, Any]:
        """Load contract ABI and bytecode"""
        try:
            # Load ABI
            abi_path = os.path.join('abi', f'{contract_name}.json')
            with open(abi_path, 'r') as f:
                abi = json.load(f)
            
            # Load bytecode
            bytecode_path = os.path.join('bytecode', f'{contract_name}.bin')
            if os.path.exists(bytecode_path):
                with open(bytecode_path, 'r') as f:
                    bytecode = f.read().strip()
            else:
                # Try to extract from compiled contracts
                bytecode = self._extract_bytecode_from_solc(contract_name)
            
            return {'abi': abi, 'bytecode': bytecode}
            
        except Exception as e:
            logger.error(f"Error loading contract data for {contract_name}: {e}")
            raise
    
    def _extract_bytecode_from_solc(self, contract_name: str) -> str:
        """Extract bytecode from Solidity compilation output"""
        # This would integrate with your Solidity compilation process
        # For now, return a placeholder
        logger.warning(f"Bytecode file not found for {contract_name}, using placeholder")
        return "0x608060405234801561001057600080fd5b50"
    
    def estimate_deployment_gas(self, contract_data: Dict[str, Any], constructor_args: list = None) -> int:
        """Estimate gas for contract deployment"""
        try:
            contract = self.web3.eth.contract(
                abi=contract_data['abi'],
                bytecode=contract_data['bytecode']
            )
            
            if constructor_args:
                constructor_tx = contract.constructor(*constructor_args)
            else:
                constructor_tx = contract.constructor()
            
            gas_estimate = constructor_tx.estimate_gas({'from': self.account.address})
            return int(gas_estimate * 1.2)  # Add 20% buffer
            
        except Exception as e:
            logger.warning(f"Gas estimation failed: {e}, using default")
            return 2000000  # Default gas limit
    
    def deploy_contract(self, contract_name: str, constructor_args: list = None, 
                       contract_alias: str = None) -> Optional[str]:
        """Deploy a single contract"""
        try:
            logger.info(f"Deploying {contract_name}...")
            
            if self.dry_run:
                logger.info(f"DRY RUN: Would deploy {contract_name} with args {constructor_args}")
                return "0x" + "0" * 40  # Mock address
            
            # Load contract data
            contract_data = self.load_contract_data(contract_name)
            
            # Create contract instance
            contract = self.web3.eth.contract(
                abi=contract_data['abi'],
                bytecode=contract_data['bytecode']
            )
            
            # Estimate gas
            gas_limit = self.estimate_deployment_gas(contract_data, constructor_args)
            logger.info(f"Estimated gas: {gas_limit}")
            
            # Build transaction
            if constructor_args:
                constructor_tx = contract.constructor(*constructor_args).build_transaction({
                    'from': self.account.address,
                    'gas': gas_limit,
                    'nonce': self.web3.eth.get_transaction_count(self.account.address),
                })
            else:
                constructor_tx = contract.constructor().build_transaction({
                    'from': self.account.address,
                    'gas': gas_limit,
                    'nonce': self.web3.eth.get_transaction_count(self.account.address),
                })
            
            # Add EIP-1559 gas pricing
            latest_block = self.web3.eth.get_block('latest')
            base_fee = latest_block.get('baseFeePerGas', 0)
            max_priority_fee = self.web3.to_wei('2', 'gwei')
            constructor_tx['maxFeePerGas'] = base_fee + max_priority_fee
            constructor_tx['maxPriorityFeePerGas'] = max_priority_fee
              # Sign and send transaction
            # SECURITY: Use secure transaction signer instead of private key
            signed_tx = self.signer.sign_transaction(constructor_tx)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            logger.info(f"Transaction sent: {tx_hash.hex()}")
            logger.info("Waiting for confirmation...")
            
            # Wait for receipt
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt['status'] == 1:
                contract_address = receipt['contractAddress']
                logger.info(f"✅ {contract_name} deployed at: {contract_address}")
                logger.info(f"Gas used: {receipt['gasUsed']}")
                
                # Store deployment result
                alias = contract_alias or contract_name
                self.deployment_results[alias] = {
                    'address': contract_address,
                    'tx_hash': tx_hash.hex(),
                    'gas_used': receipt['gasUsed'],
                    'block_number': receipt['blockNumber']
                }
                
                return contract_address
            else:
                logger.error(f"❌ {contract_name} deployment failed")
                return None
                
        except Exception as e:
            logger.error(f"Error deploying {contract_name}: {e}")
            return None
    
    def deploy_all_contracts(self):
        """Deploy all contracts in the correct order"""
        logger.info("🚀 Starting contract deployment sequence...")
        
        # 1. Deploy StrategyIncubator
        incubator_address = self.deploy_contract(
            'StrategyIncubatorV33',
            constructor_args=[self.account.address],  # initialOwner
            contract_alias='incubator'
        )
        
        if not incubator_address:
            logger.error("Failed to deploy StrategyIncubator, aborting")
            return False
        
        # 2. Deploy ArbitrageExecutor
        # Assuming we need AAVE pool address and WETH address
        mudarabah_flash_swap = os.getenv('MUDARABAH_FLASH_SWAP_ADDRESS', '')  # Will be deployed if empty
        weth_address = os.getenv('WETH_ADDRESS', '${CONTRACT_ADDRESS}')  # Mainnet
        
        executor_address = self.deploy_contract(
            'ArbitrageExecutorV33',
            constructor_args=[aave_pool, weth_address, self.account.address],
            contract_alias='executor'
        )
        
        if not executor_address:
            logger.error("Failed to deploy ArbitrageExecutor, aborting")
            return False
        
        # 3. Deploy StrategyFactory
        factory_address = self.deploy_contract(
            'StrategyFactoryV33',
            constructor_args=[self.account.address],  # Only needs owner
            contract_alias='factory'
        )
        
        if not factory_address:
            logger.error("Failed to deploy StrategyFactory")
            return False
        
        # 4. Configure contracts (set permissions, etc.)
        if not self.dry_run:
            self._configure_contracts()
        
        logger.info("✅ All contracts deployed successfully!")
        return True
    
    def _configure_contracts(self):
        """Configure deployed contracts"""
        try:
            logger.info("Configuring contracts...")
            
            # Load contract instances
            incubator_data = self.load_contract_data('StrategyIncubatorV33')
            executor_data = self.load_contract_data('ArbitrageExecutorV33')
            
            incubator = self.web3.eth.contract(
                address=self.deployment_results['incubator']['address'],
                abi=incubator_data['abi']
            )
            
            executor = self.web3.eth.contract(
                address=self.deployment_results['executor']['address'],
                abi=executor_data['abi']
            )
            
            # Grant STRATEGY_ROLE to incubator on executor
            strategy_role = self.web3.keccak(text="STRATEGY_ROLE")
            
            tx = executor.functions.grantRole(
                strategy_role,
                self.deployment_results['incubator']['address']
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.web3.eth.get_transaction_count(self.account.address),
            })
            
            # Add gas settings
            latest_block = self.web3.eth.get_block('latest')
            base_fee = latest_block.get('baseFeePerGas', 0)
            max_priority_fee = self.web3.to_wei('2', 'gwei')
            tx['maxFeePerGas'] = base_fee + max_priority_fee
            tx['maxPriorityFeePerGas'] = max_priority_fee
            tx['gas'] = 100000
              # SECURITY: Use secure transaction signer instead of private key
            signed_tx = self.signer.sign_transaction(tx)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt['status'] == 1:
                logger.info("✅ Contracts configured successfully")
            else:
                logger.error("❌ Contract configuration failed")
                
        except Exception as e:
            logger.error(f"Error configuring contracts: {e}")
    
    def save_deployment_results(self):
        """Save deployment results to file"""
        try:
            filename = f"deployment_{self.network}_{int(time.time())}.json"
            
            deployment_info = {
                'network': self.network,
                'deployer': self.account.address,
                'timestamp': time.time(),
                'chain_id': self.web3.eth.chain_id,
                'contracts': self.deployment_results
            }
            
            with open(filename, 'w') as f:
                json.dump(deployment_info, f, indent=2)
            
            logger.info(f"Deployment results saved to {filename}")
            
            # Also create/update .env file with addresses
            self._update_env_file()
            
        except Exception as e:
            logger.error(f"Error saving deployment results: {e}")
    
    def _update_env_file(self):
        """Update .env file with deployed contract addresses"""
        try:
            env_updates = []
            
            if 'incubator' in self.deployment_results:
                env_updates.append(f"INCUBATOR_ADDRESS={self.deployment_results['incubator']['address']}")
            
            if 'executor' in self.deployment_results:
                env_updates.append(f"EXECUTOR_ADDRESS={self.deployment_results['executor']['address']}")
            
            if 'factory' in self.deployment_results:
                env_updates.append(f"FACTORY_ADDRESS={self.deployment_results['factory']['address']}")
            
            if env_updates:
                with open('.env.deployment', 'w') as f:
                    f.write("# Deployed Contract Addresses\n")
                    f.write(f"# Network: {self.network}\n")
                    f.write(f"# Deployed at: {time.ctime()}\n\n")
                    f.write('\n'.join(env_updates))
                
                logger.info("Contract addresses saved to .env.deployment")
                logger.info("Add these to your main .env file:")
                for update in env_updates:
                    logger.info(f"  {update}")
                    
        except Exception as e:
            logger.error(f"Error updating env file: {e}")

def main():
    parser = argparse.ArgumentParser(description='Deploy Flash Loan Arbitrage Contracts')
    parser.add_argument('--network', choices=['mainnet', 'testnet', 'local'], 
                       default='testnet', help='Network to deploy to')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Simulate deployment without sending transactions')
    parser.add_argument('--contract', type=str, 
                       help='Deploy specific contract only')
    
    args = parser.parse_args()
    
    try:
        deployer = ContractDeployer(network=args.network, dry_run=args.dry_run)
        
        if args.contract:
            # Deploy specific contract
            address = deployer.deploy_contract(args.contract)
            if address:
                logger.info(f"Contract {args.contract} deployed at {address}")
            else:
                logger.error(f"Failed to deploy {args.contract}")
                return 1
        else:
            # Deploy all contracts
            success = deployer.deploy_all_contracts()
            if not success:
                logger.error("Deployment failed")
                return 1
        
        # Save results
        deployer.save_deployment_results()
        
        logger.info("🎉 Deployment completed successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())