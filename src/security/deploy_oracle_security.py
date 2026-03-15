#!/usr/bin/env python3
"""
Oracle Security Enhancement Deployment Script
Deploys enhanced oracle security infrastructure to prevent manipulation attacks
"""

import json
import os
import sys
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from web3 import Web3
from web3.middleware import geth_poa_middleware
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('oracle_security_deployment.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class OracleConfig:
    """Oracle configuration for deployment"""
    address: str
    weight: int
    source: str
    update_threshold: int
    heartbeat: int

@dataclass
class SecurityConfig:
    """Security configuration for oracle system"""
    max_deviation: int = 500  # 5% in basis points
    min_oracles: int = 3
    circuit_breaker_threshold: int = 1000  # 10% in basis points
    staleness_threshold: int = 3600  # 1 hour in seconds
    emergency_timeout: int = 86400  # 24 hours
    
class OracleSecurityDeployer:
    """Deploys and configures oracle security infrastructure"""
    
    def __init__(self, network_config: Dict[str, Any]):
        self.network_config = network_config
        self.w3 = self._setup_web3()
        self.account = self._setup_account()
        self.contracts = {}
        self.deployment_results = {}
        
    def _setup_web3(self) -> Web3:
        """Setup Web3 connection"""
        rpc_url = self.network_config.get('rpc_url')
        if not rpc_url:
            raise ValueError("RPC URL not provided in network config")
            
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Add PoA middleware if needed
        if self.network_config.get('poa', False):
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
        if not w3.is_connected():
            raise ConnectionError(f"Failed to connect to {rpc_url}")
            
        logger.info(f"Connected to {rpc_url}, Chain ID: {w3.eth.chain_id}")
        return w3
        
    def _setup_account(self):
        """Setup deployment account"""
        private_key = os.environ.get('DEPLOYER_PRIVATE_KEY')
        if not private_key:
            raise ValueError("DEPLOYER_PRIVATE_KEY environment variable not set")
            
        account = self.w3.eth.account.from_key(private_key)
        logger.info(f"Deployment account: {account.address}")
        
        # Check balance
        balance = self.w3.eth.get_balance(account.address)
        balance_eth = self.w3.from_wei(balance, 'ether')
        logger.info(f"Account balance: {balance_eth:.4f} ETH")
        
        if balance_eth < 0.1:
            logger.warning("Low account balance - ensure sufficient funds for deployment")
            
        return account
        
    def deploy_oracle_infrastructure(self) -> Dict[str, str]:
        """Deploy complete oracle security infrastructure"""
        
        logger.info("=== Starting Oracle Security Infrastructure Deployment ===")
        
        try:
            # 1. Deploy SecureMultiOracle
            logger.info("1. Deploying SecureMultiOracle...")
            multi_oracle_address = self._deploy_secure_multi_oracle()
            
            # 2. Deploy PreCognitiveOracle
            logger.info("2. Deploying PreCognitiveOracle...")
            predictive_oracle_address = self._deploy_precognitive_oracle()
            
            # 3. Deploy OracleSecurityWrapper
            logger.info("3. Deploying OracleSecurityWrapper...")
            security_wrapper_address = self._deploy_oracle_security_wrapper(
                multi_oracle_address,
                predictive_oracle_address
            )
            
            # 4. Deploy SecureArbitrageExecutorV42
            logger.info("4. Deploying SecureArbitrageExecutorV42...")
            arbitrage_executor_address = self._deploy_secure_arbitrage_executor(
                multi_oracle_address,
                predictive_oracle_address,
                security_wrapper_address
            )
            
            # 5. Configure oracle sources
            logger.info("5. Configuring oracle sources...")
            self._configure_oracle_sources(multi_oracle_address)
            
            # 6. Setup security parameters
            logger.info("6. Setting up security parameters...")
            self._setup_security_parameters(security_wrapper_address)
            
            # 7. Configure arbitrage executor
            logger.info("7. Configuring arbitrage executor...")
            self._configure_arbitrage_executor(arbitrage_executor_address)
            
            # 8. Run security validation
            logger.info("8. Running security validation...")
            self._validate_deployment()
            
            deployment_summary = {
                'SecureMultiOracle': multi_oracle_address,
                'PreCognitiveOracle': predictive_oracle_address,
                'OracleSecurityWrapper': security_wrapper_address,
                'SecureArbitrageExecutorV42': arbitrage_executor_address,
                'deployment_timestamp': int(time.time()),
                'deployer': self.account.address,
                'network': self.network_config.get('name', 'unknown')
            }
            
            # Save deployment results
            self._save_deployment_results(deployment_summary)
            
            logger.info("=== Oracle Security Infrastructure Deployment Complete ===")
            return deployment_summary
            
        except Exception as e:
            logger.error(f"Deployment failed: {str(e)}")
            raise
            
    def _deploy_secure_multi_oracle(self) -> str:
        """Deploy SecureMultiOracle contract"""
        
        # Load contract ABI and bytecode
        contract_data = self._load_contract_data('SecureMultiOracle')
        
        # Constructor parameters
        constructor_args = [self.account.address]  # admin address
        
        # Deploy contract
        contract_address = self._deploy_contract(
            'SecureMultiOracle',
            contract_data['abi'],
            contract_data['bytecode'],
            constructor_args
        )
        
        logger.info(f"SecureMultiOracle deployed at: {contract_address}")
        return contract_address
        
    def _deploy_precognitive_oracle(self) -> str:
        """Deploy PreCognitiveOracle contract"""
        
        contract_data = self._load_contract_data('PreCognitiveOracle')
        
        # Deploy contract (constructor takes no parameters)
        contract_address = self._deploy_contract(
            'PreCognitiveOracle',
            contract_data['abi'],
            contract_data['bytecode'],
            []
        )
        
        logger.info(f"PreCognitiveOracle deployed at: {contract_address}")
        return contract_address
        
    def _deploy_oracle_security_wrapper(self, multi_oracle: str, predictive_oracle: str) -> str:
        """Deploy OracleSecurityWrapper contract"""
        
        contract_data = self._load_contract_data('OracleSecurityWrapper')
        
        constructor_args = [
            multi_oracle,
            predictive_oracle,
            self.account.address
        ]
        
        contract_address = self._deploy_contract(
            'OracleSecurityWrapper',
            contract_data['abi'],
            contract_data['bytecode'],
            constructor_args
        )
        
        logger.info(f"OracleSecurityWrapper deployed at: {contract_address}")
        return contract_address
        
    def _deploy_secure_arbitrage_executor(self, multi_oracle: str, predictive_oracle: str, security_wrapper: str) -> str:
        """Deploy SecureArbitrageExecutorV42 contract"""
        
        contract_data = self._load_contract_data('SecureArbitrageExecutorV42')
        
        # Get Aave pool address for the network
        aave_pool = self.network_config.get('aave_pool_address')
        if not aave_pool:
            raise ValueError("Aave pool address not configured for this network")
            
        # Treasury address (can be multisig)
        treasury = self.network_config.get('treasury_address', self.account.address)
        
        constructor_args = [
            aave_pool,
            multi_oracle,
            predictive_oracle,
            treasury,
            self.account.address
        ]
        
        contract_address = self._deploy_contract(
            'SecureArbitrageExecutorV42',
            contract_data['abi'],
            contract_data['bytecode'],
            constructor_args
        )
        
        logger.info(f"SecureArbitrageExecutorV42 deployed at: {contract_address}")
        return contract_address
        
    def _configure_oracle_sources(self, multi_oracle_address: str) -> None:
        """Configure oracle sources for the SecureMultiOracle"""
        
        # Load oracle configurations
        oracle_configs = self._get_oracle_configurations()
        
        multi_oracle = self.w3.eth.contract(
            address=multi_oracle_address,
            abi=self._load_contract_data('SecureMultiOracle')['abi']
        )
        
        for config in oracle_configs:
            try:
                logger.info(f"Adding oracle: {config.source} at {config.address}")
                
                # Add oracle
                tx_hash = self._send_transaction(
                    multi_oracle.functions.addOracle(
                        config.address,
                        config.weight,
                        config.source
                    )
                )
                
                logger.info(f"Oracle {config.source} added. Tx: {tx_hash.hex()}")
                
            except Exception as e:
                logger.error(f"Failed to add oracle {config.source}: {str(e)}")
                
    def _setup_security_parameters(self, security_wrapper_address: str) -> None:
        """Setup security parameters for the oracle security wrapper"""
        
        security_wrapper = self.w3.eth.contract(
            address=security_wrapper_address,
            abi=self._load_contract_data('OracleSecurityWrapper')['abi']
        )
        
        # Configure trusted price feeds
        trusted_feeds = self.network_config.get('trusted_price_feeds', [])
        
        for feed in trusted_feeds:
            try:
                logger.info(f"Configuring trusted price feed: {feed}")
                
                # This would call appropriate configuration functions
                # Implementation depends on specific wrapper interface
                
            except Exception as e:
                logger.error(f"Failed to configure price feed {feed}: {str(e)}")
                
    def _configure_arbitrage_executor(self, executor_address: str) -> None:
        """Configure the secure arbitrage executor"""
        
        executor = self.w3.eth.contract(
            address=executor_address,
            abi=self._load_contract_data('SecureArbitrageExecutorV42')['abi']
        )
        
        # Configure supported tokens
        supported_tokens = self.network_config.get('supported_tokens', [])
        
        for token_config in supported_tokens:
            try:
                logger.info(f"Configuring token: {token_config['symbol']}")
                
                # Configure token for oracle-secured trading
                tx_hash = self._send_transaction(
                    executor.functions.configureToken(
                        token_config['address'],
                        token_config['price_id'],
                        token_config['max_trade_size'],
                        token_config['min_liquidity'],
                        token_config['approved_dexes']
                    )
                )
                
                logger.info(f"Token {token_config['symbol']} configured. Tx: {tx_hash.hex()}")
                
            except Exception as e:
                logger.error(f"Failed to configure token {token_config['symbol']}: {str(e)}")
                
    def _validate_deployment(self) -> None:
        """Validate the deployment by running security checks"""
        
        logger.info("Running deployment validation...")
        
        # Test oracle health
        multi_oracle = self.contracts.get('SecureMultiOracle')
        if multi_oracle:
            try:
                health = multi_oracle.functions.getSystemHealth().call()
                logger.info(f"Oracle system health: {health}")
                
                if health[0] < 3:  # activeOracles
                    logger.warning("Insufficient active oracles for production use")
                    
            except Exception as e:
                logger.error(f"Failed to check oracle health: {str(e)}")
                
        # Test security wrapper
        security_wrapper = self.contracts.get('OracleSecurityWrapper')
        if security_wrapper:
            try:
                security_health = security_wrapper.functions.getSystemSecurityHealth().call()
                logger.info(f"Security system health: {security_health}")
                
            except Exception as e:
                logger.error(f"Failed to check security health: {str(e)}")
                
        logger.info("Validation complete")
        
    def _get_oracle_configurations(self) -> List[OracleConfig]:
        """Get oracle configurations for the network"""
        
        # This would be loaded from configuration files or environment
        default_configs = [
            OracleConfig(
                address="${CONTRACT_ADDRESS}",  # Placeholder
                weight=40,
                source="Chainlink",
                update_threshold=60,
                heartbeat=3600
            ),
            OracleConfig(
                address="${CONTRACT_ADDRESS}",  # Placeholder
                weight=30,
                source="Band Protocol",
                update_threshold=60,
                heartbeat=3600
            ),
            OracleConfig(
                address="${CONTRACT_ADDRESS}",  # Placeholder
                weight=30,
                source="API3",
                update_threshold=60,
                heartbeat=3600
            )
        ]
        
        return default_configs
        
    def _load_contract_data(self, contract_name: str) -> Dict[str, Any]:
        """Load contract ABI and bytecode"""
        
        # This would load from compiled contract artifacts
        # For now, return placeholder structure
        return {
            'abi': [],  # Contract ABI would be loaded here
            'bytecode': '0x',  # Contract bytecode would be loaded here
        }
        
    def _deploy_contract(self, name: str, abi: List, bytecode: str, constructor_args: List) -> str:
        """Deploy a contract and return its address"""
        
        contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)
        
        # Build constructor transaction
        constructor_tx = contract.constructor(*constructor_args).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 5000000,  # Adjust based on contract
            'gasPrice': self.w3.to_wei('20', 'gwei')
        })
        
        # Sign and send transaction
        signed_tx = self.w3.eth.account.sign_transaction(constructor_tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        logger.info(f"Deploying {name}... Tx: {tx_hash.hex()}")
        
        # Wait for transaction receipt
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        
        if tx_receipt.status != 1:
            raise RuntimeError(f"Contract deployment failed: {name}")
            
        contract_address = tx_receipt.contractAddress
        
        # Store contract instance
        self.contracts[name] = self.w3.eth.contract(
            address=contract_address,
            abi=abi
        )
        
        logger.info(f"{name} deployed successfully at: {contract_address}")
        return contract_address
        
    def _send_transaction(self, function_call) -> bytes:
        """Send a transaction and wait for confirmation"""
        
        # Build transaction
        tx = function_call.build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 300000,
            'gasPrice': self.w3.to_wei('20', 'gwei')
        })
        
        # Sign and send
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        # Wait for confirmation
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if tx_receipt.status != 1:
            raise RuntimeError(f"Transaction failed: {tx_hash.hex()}")
            
        return tx_hash
        
    def _save_deployment_results(self, results: Dict[str, Any]) -> None:
        """Save deployment results to file"""
        
        filename = f"oracle_security_deployment_{int(time.time())}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
            
        logger.info(f"Deployment results saved to: {filename}")

def main():
    """Main deployment function"""
    
    # Network configurations
    network_configs = {
        'mainnet': {
            'name': 'Ethereum Mainnet',
            'rpc_url': 'https://mainnet.infura.io/v3/YOUR_PROJECT_ID',
            'aave_pool_address': '${CONTRACT_ADDRESS}',
            'poa': False,
            'supported_tokens': [
                {
                    'symbol': 'WETH',
                    'address': '${CONTRACT_ADDRESS}',
                    'price_id': '0xETH_USD',
                    'max_trade_size': 10**18,  # 1 WETH
                    'min_liquidity': 10**19,   # 10 WETH
                    'approved_dexes': ['0x...']  # DEX addresses
                }
            ]
        },
        'polygon': {
            'name': 'Polygon',
            'rpc_url': 'https://polygon-rpc.com/',
            'aave_pool_address': '${CONTRACT_ADDRESS}',
            'poa': True,
            'supported_tokens': []
        }
    }
    
    # Select network
    network = os.environ.get('NETWORK', 'mainnet')
    
    if network not in network_configs:
        logger.error(f"Unknown network: {network}")
        sys.exit(1)
        
    config = network_configs[network]
    
    try:
        # Initialize deployer
        deployer = OracleSecurityDeployer(config)
        
        # Deploy infrastructure
        results = deployer.deploy_oracle_infrastructure()
        
        logger.info("Deployment Summary:")
        for contract_name, address in results.items():
            if contract_name not in ['deployment_timestamp', 'deployer', 'network']:
                logger.info(f"  {contract_name}: {address}")
                
        logger.info("🎉 Oracle security infrastructure deployed successfully!")
        
    except Exception as e:
        logger.error(f"Deployment failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
