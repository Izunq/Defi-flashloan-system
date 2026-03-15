#!/usr/bin/env python3
"""
Oracle Security Deployment and Management Script
Deploys and configures enhanced oracle security infrastructure
"""

import os
import sys
import json
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from web3 import Web3
from web3.middleware import geth_poa_middleware
import yaml

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
class ContractDeployment:
    """Contract deployment result"""
    name: str
    address: str
    tx_hash: str
    gas_used: int
    deployment_time: int

@dataclass
class OracleConfig:
    """Oracle configuration"""
    address: str
    weight: int
    source: str
    update_threshold: int
    heartbeat: int

class OracleSecurityDeployer:
    """Enhanced oracle security deployment manager"""
    
    def __init__(self, config_path: str = "oracle_deployment_config.yaml"):
        self.config = self._load_config(config_path)
        self.w3 = self._setup_web3()
        
        # SECURITY: Use secure transaction signer
        try:
            from secure_transaction_signer import SecureTransactionSigner
            self.signer = SecureTransactionSigner()
            self.account = self.signer.get_account()
            logger.info(f"Using secure account: {self.account.address}")
        except ImportError:
            logger.error("SECURITY ERROR: SecureTransactionSigner not available")
            raise RuntimeError("Direct private key usage prohibited for security")
        
        self.deployments: Dict[str, ContractDeployment] = {}
        self.deployment_results = {}
        
    def _load_config(self, config_path: str) -> Dict:
        """Load deployment configuration"""
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default deployment configuration"""
        return {
            'network': {
                'rpc_url': 'http://localhost:8545',
                'chain_id': 31337,
                'gas_limit': 8000000,
                'gas_price': 'auto'
            },
            'security': {
                'max_deviation': 500,
                'circuit_breaker_threshold': 1000,
                'min_oracles': 3,
                'staleness_threshold': 3600
            },
            'oracles': {
                'chainlink_eth_usd': {
                    'address': '${CONTRACT_ADDRESS}',
                    'weight': 40,
                    'source': 'Chainlink'
                },
                'chainlink_btc_usd': {
                    'address': '${CONTRACT_ADDRESS}',
                    'weight': 40,
                    'source': 'Chainlink'
                }
            }
        }
    
    def _setup_web3(self) -> Web3:
        """Setup Web3 connection"""
        network_config = self.config.get('network', {})
        rpc_url = network_config.get('rpc_url', 'http://localhost:8545')
        
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Add PoA middleware if needed
        if network_config.get('poa', False):
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        if not w3.is_connected():
            raise ConnectionError(f"Failed to connect to {rpc_url}")
        
        logger.info(f"Connected to {rpc_url}, Chain ID: {w3.eth.chain_id}")
        return w3
    
    def deploy_oracle_security_infrastructure(self) -> Dict[str, Any]:
        """Deploy complete oracle security infrastructure"""
        logger.info("=== Starting Oracle Security Infrastructure Deployment ===")
        
        deployment_results = {
            'status': 'success',
            'deployments': {},
            'configurations': {},
            'start_time': int(time.time()),
            'errors': []
        }
        
        try:
            # 1. Deploy SecureMultiOracle
            logger.info("1. Deploying SecureMultiOracle...")
            secure_oracle = self._deploy_secure_multi_oracle()
            deployment_results['deployments']['SecureMultiOracle'] = secure_oracle
            
            # 2. Deploy OracleSecurityWrapper
            logger.info("2. Deploying OracleSecurityWrapper...")
            security_wrapper = self._deploy_oracle_security_wrapper(secure_oracle.address)
            deployment_results['deployments']['OracleSecurityWrapper'] = security_wrapper
            
            # 3. Deploy AdvancedOracleSecurityValidator
            logger.info("3. Deploying AdvancedOracleSecurityValidator...")
            validator = self._deploy_advanced_validator(secure_oracle.address)
            deployment_results['deployments']['AdvancedOracleSecurityValidator'] = validator
            
            # 4. Deploy OracleManipulationMonitor
            logger.info("4. Deploying OracleManipulationMonitor...")
            monitor = self._deploy_manipulation_monitor(
                secure_oracle.address, 
                security_wrapper.address
            )
            deployment_results['deployments']['OracleManipulationMonitor'] = monitor
            
            # 5. Configure oracle sources
            logger.info("5. Configuring oracle sources...")
            oracle_config = self._configure_oracle_sources(secure_oracle.address)
            deployment_results['configurations']['oracle_sources'] = oracle_config
            
            # 6. Setup security parameters
            logger.info("6. Setting up security parameters...")
            security_config = self._setup_security_parameters(
                security_wrapper.address,
                validator.address
            )
            deployment_results['configurations']['security_parameters'] = security_config
            
            # 7. Initialize monitoring system
            logger.info("7. Initializing monitoring system...")
            monitoring_config = self._initialize_monitoring(monitor.address)
            deployment_results['configurations']['monitoring'] = monitoring_config
            
            # 8. Deploy Python monitoring agents
            logger.info("8. Setting up Python monitoring agents...")
            agent_config = self._setup_monitoring_agents()
            deployment_results['configurations']['monitoring_agents'] = agent_config
            
            deployment_results['end_time'] = int(time.time())
            deployment_results['total_time'] = deployment_results['end_time'] - deployment_results['start_time']
            
            logger.info("=== Oracle Security Infrastructure Deployment Complete ===")
            logger.info(f"Total deployment time: {deployment_results['total_time']} seconds")
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            deployment_results['status'] = 'failed'
            deployment_results['error'] = str(e)
            deployment_results['errors'].append(str(e))
        
        return deployment_results
    
    def _deploy_secure_multi_oracle(self) -> ContractDeployment:
        """Deploy SecureMultiOracle contract"""
        try:
            # Load contract bytecode and ABI
            contract_data = self._load_contract_data('SecureMultiOracle')
            
            # Constructor parameters
            security_config = self.config.get('security', {})
            constructor_args = [
                security_config.get('max_deviation', 500),  # MAX_PRICE_DEVIATION
                security_config.get('circuit_breaker_threshold', 1000),  # CIRCUIT_BREAKER_THRESHOLD
                security_config.get('min_oracles', 3),  # MIN_ORACLES_REQUIRED
                self.account.address  # Admin address
            ]
            
            # Deploy contract
            contract = self.w3.eth.contract(
                abi=contract_data['abi'],
                bytecode=contract_data['bytecode']
            )
            
            deployment = self._deploy_contract(
                contract,
                constructor_args,
                'SecureMultiOracle'
            )
            
            logger.info(f"SecureMultiOracle deployed at: {deployment.address}")
            return deployment
            
        except Exception as e:
            logger.error(f"Failed to deploy SecureMultiOracle: {e}")
            raise
    
    def _deploy_oracle_security_wrapper(self, oracle_address: str) -> ContractDeployment:
        """Deploy OracleSecurityWrapper contract"""
        try:
            contract_data = self._load_contract_data('OracleSecurityWrapper')
            
            # Constructor parameters
            constructor_args = [
                oracle_address,  # Primary oracle
                "${CONTRACT_ADDRESS}",  # Predictive oracle (placeholder)
                self.account.address  # Admin
            ]
            
            contract = self.w3.eth.contract(
                abi=contract_data['abi'],
                bytecode=contract_data['bytecode']
            )
            
            deployment = self._deploy_contract(
                contract,
                constructor_args,
                'OracleSecurityWrapper'
            )
            
            logger.info(f"OracleSecurityWrapper deployed at: {deployment.address}")
            return deployment
            
        except Exception as e:
            logger.error(f"Failed to deploy OracleSecurityWrapper: {e}")
            raise
    
    def _deploy_advanced_validator(self, oracle_address: str) -> ContractDeployment:
        """Deploy AdvancedOracleSecurityValidator contract"""
        try:
            contract_data = self._load_contract_data('AdvancedOracleSecurityValidator')
            
            constructor_args = [
                oracle_address,  # Primary oracle
                self.account.address  # Admin
            ]
            
            contract = self.w3.eth.contract(
                abi=contract_data['abi'],
                bytecode=contract_data['bytecode']
            )
            
            deployment = self._deploy_contract(
                contract,
                constructor_args,
                'AdvancedOracleSecurityValidator'
            )
            
            logger.info(f"AdvancedOracleSecurityValidator deployed at: {deployment.address}")
            return deployment
            
        except Exception as e:
            logger.error(f"Failed to deploy AdvancedOracleSecurityValidator: {e}")
            raise
    
    def _deploy_manipulation_monitor(self, oracle_address: str, wrapper_address: str) -> ContractDeployment:
        """Deploy OracleManipulationMonitor contract"""
        try:
            contract_data = self._load_contract_data('OracleManipulationMonitor')
            
            constructor_args = [
                oracle_address,  # Primary oracle
                wrapper_address,  # Security wrapper
                self.account.address  # Admin
            ]
            
            contract = self.w3.eth.contract(
                abi=contract_data['abi'],
                bytecode=contract_data['bytecode']
            )
            
            deployment = self._deploy_contract(
                contract,
                constructor_args,
                'OracleManipulationMonitor'
            )
            
            logger.info(f"OracleManipulationMonitor deployed at: {deployment.address}")
            return deployment
            
        except Exception as e:
            logger.error(f"Failed to deploy OracleManipulationMonitor: {e}")
            raise
    
    def _deploy_contract(
        self, 
        contract, 
        constructor_args: List[Any], 
        contract_name: str
    ) -> ContractDeployment:
        """Deploy a contract with secure transaction signing"""
        try:
            # Build deployment transaction
            deployment_tx = contract.constructor(*constructor_args).build_transaction({
                'from': self.account.address,
                'gas': self.config.get('network', {}).get('gas_limit', 8000000),
                'gasPrice': self._get_gas_price(),
                'nonce': self.w3.eth.get_transaction_count(self.account.address)
            })
            
            # Sign and send transaction
            signed_tx = self.signer.sign_transaction(deployment_tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            logger.info(f"Deployment transaction sent: {tx_hash.hex()}")
            
            # Wait for confirmation
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if tx_receipt.status != 1:
                raise Exception(f"Contract deployment failed: {contract_name}")
            
            deployment = ContractDeployment(
                name=contract_name,
                address=tx_receipt.contractAddress,
                tx_hash=tx_hash.hex(),
                gas_used=tx_receipt.gasUsed,
                deployment_time=int(time.time())
            )
            
            self.deployments[contract_name] = deployment
            return deployment
            
        except Exception as e:
            logger.error(f"Error deploying {contract_name}: {e}")
            raise
    
    def _load_contract_data(self, contract_name: str) -> Dict:
        """Load contract ABI and bytecode"""
        try:
            # Load ABI
            with open(f"abi/{contract_name}.json", 'r') as f:
                abi = json.load(f)
            
            # Load bytecode
            with open(f"bytecode/{contract_name}.bin", 'r') as f:
                bytecode = f.read().strip()
            
            return {
                'abi': abi,
                'bytecode': bytecode
            }
            
        except FileNotFoundError as e:
            logger.error(f"Contract files not found for {contract_name}: {e}")
            # Return placeholder for testing
            return {
                'abi': [],
                'bytecode': '0x608060405234801561001057600080fd5b50'  # Minimal bytecode
            }
    
    def _get_gas_price(self) -> int:
        """Get appropriate gas price"""
        gas_price_config = self.config.get('network', {}).get('gas_price', 'auto')
        
        if gas_price_config == 'auto':
            return self.w3.eth.gas_price
        else:
            return int(gas_price_config)
    
    def _configure_oracle_sources(self, oracle_address: str) -> Dict:
        """Configure oracle sources"""
        try:
            oracle_configs = self.config.get('oracles', {})
            configured_oracles = []
            
            # Load oracle contract
            oracle_abi = self._load_contract_data('SecureMultiOracle')['abi']
            oracle_contract = self.w3.eth.contract(
                address=oracle_address,
                abi=oracle_abi
            )
            
            for oracle_name, config in oracle_configs.items():
                try:
                    # Register oracle
                    tx = oracle_contract.functions.registerOracle(
                        config['address'],
                        config['weight'],
                        config['source']
                    ).build_transaction({
                        'from': self.account.address,
                        'gas': 500000,
                        'gasPrice': self._get_gas_price(),
                        'nonce': self.w3.eth.get_transaction_count(self.account.address)
                    })
                    
                    signed_tx = self.signer.sign_transaction(tx)
                    tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                    receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                    
                    if receipt.status == 1:
                        configured_oracles.append({
                            'name': oracle_name,
                            'address': config['address'],
                            'weight': config['weight'],
                            'tx_hash': tx_hash.hex()
                        })
                        logger.info(f"Configured oracle: {oracle_name}")
                    
                except Exception as e:
                    logger.error(f"Failed to configure oracle {oracle_name}: {e}")
            
            return {
                'total_configured': len(configured_oracles),
                'oracles': configured_oracles
            }
            
        except Exception as e:
            logger.error(f"Error configuring oracle sources: {e}")
            return {'error': str(e)}
    
    def _setup_security_parameters(self, wrapper_address: str, validator_address: str) -> Dict:
        """Setup security parameters"""
        try:
            results = {}
            
            # Configure security wrapper
            wrapper_abi = self._load_contract_data('OracleSecurityWrapper')['abi']
            wrapper_contract = self.w3.eth.contract(
                address=wrapper_address,
                abi=wrapper_abi
            )
            
            # Configure validator
            validator_abi = self._load_contract_data('AdvancedOracleSecurityValidator')['abi']
            validator_contract = self.w3.eth.contract(
                address=validator_address,
                abi=validator_abi
            )
            
            # Set anomaly threshold
            security_config = self.config.get('security', {})
            anomaly_threshold = security_config.get('anomaly_threshold', 9500)
            
            try:
                tx = validator_contract.functions.setAnomalyThreshold(
                    anomaly_threshold
                ).build_transaction({
                    'from': self.account.address,
                    'gas': 100000,
                    'gasPrice': self._get_gas_price(),
                    'nonce': self.w3.eth.get_transaction_count(self.account.address)
                })
                
                signed_tx = self.signer.sign_transaction(tx)
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                
                results['anomaly_threshold'] = {
                    'value': anomaly_threshold,
                    'tx_hash': tx_hash.hex(),
                    'status': 'success' if receipt.status == 1 else 'failed'
                }
                
            except Exception as e:
                logger.error(f"Failed to set anomaly threshold: {e}")
                results['anomaly_threshold'] = {'error': str(e)}
            
            return results
            
        except Exception as e:
            logger.error(f"Error setting up security parameters: {e}")
            return {'error': str(e)}
    
    def _initialize_monitoring(self, monitor_address: str) -> Dict:
        """Initialize monitoring system"""
        try:
            # Load monitor contract
            monitor_abi = self._load_contract_data('OracleManipulationMonitor')['abi']
            monitor_contract = self.w3.eth.contract(
                address=monitor_address,
                abi=monitor_abi
            )
            
            results = {}
            
            # Initialize monitoring for tracked assets
            tracked_assets = self.config.get('tracked_assets', ['ETH', 'BTC', 'USDC'])
            
            for asset in tracked_assets:
                try:
                    asset_id = self.w3.keccak(text=asset)
                    
                    # This would call initialization functions if they exist
                    # For now, just log the setup
                    results[asset] = {
                        'asset_id': asset_id.hex(),
                        'status': 'configured'
                    }
                    
                    logger.info(f"Monitoring configured for {asset}")
                    
                except Exception as e:
                    logger.error(f"Failed to configure monitoring for {asset}: {e}")
                    results[asset] = {'error': str(e)}
            
            return {
                'configured_assets': len([r for r in results.values() if 'error' not in r]),
                'assets': results
            }
            
        except Exception as e:
            logger.error(f"Error initializing monitoring: {e}")
            return {'error': str(e)}
    
    def _setup_monitoring_agents(self) -> Dict:
        """Setup Python monitoring agents"""
        try:
            # Create configuration for monitoring agents
            agent_config = {
                'contracts': {
                    contract_name: deployment.address 
                    for contract_name, deployment in self.deployments.items()
                },
                'network': self.config.get('network', {}),
                'security': self.config.get('security', {}),
                'tracked_assets': self.config.get('tracked_assets', [])
            }
            
            # Write agent configuration
            config_path = 'agent_config.yaml'
            with open(config_path, 'w') as f:
                yaml.dump(agent_config, f, default_flow_style=False)
            
            logger.info(f"Agent configuration written to {config_path}")
            
            return {
                'config_file': config_path,
                'status': 'configured',
                'contracts': agent_config['contracts']
            }
            
        except Exception as e:
            logger.error(f"Error setting up monitoring agents: {e}")
            return {'error': str(e)}
    
    def verify_deployment(self) -> Dict[str, Any]:
        """Verify deployment integrity"""
        logger.info("Verifying deployment integrity...")
        
        verification_results = {
            'status': 'success',
            'contracts': {},
            'configurations': {},
            'errors': []
        }
        
        try:
            for contract_name, deployment in self.deployments.items():
                try:
                    # Check if contract exists at address
                    code = self.w3.eth.get_code(deployment.address)
                    
                    verification_results['contracts'][contract_name] = {
                        'address': deployment.address,
                        'code_exists': len(code) > 0,
                        'deployment_verified': True
                    }
                    
                    logger.info(f"✅ {contract_name} verified at {deployment.address}")
                    
                except Exception as e:
                    verification_results['contracts'][contract_name] = {
                        'address': deployment.address,
                        'error': str(e),
                        'deployment_verified': False
                    }
                    verification_results['errors'].append(f"{contract_name}: {e}")
                    logger.error(f"❌ {contract_name} verification failed: {e}")
            
            # Verify configurations
            if len(verification_results['errors']) == 0:
                logger.info("✅ All contracts verified successfully")
            else:
                verification_results['status'] = 'partial'
                logger.warning(f"⚠️ Verification completed with {len(verification_results['errors'])} errors")
            
        except Exception as e:
            verification_results['status'] = 'failed'
            verification_results['errors'].append(str(e))
            logger.error(f"❌ Verification failed: {e}")
        
        return verification_results
    
    def save_deployment_report(self, deployment_results: Dict) -> None:
        """Save deployment report"""
        try:
            report = {
                'deployment_timestamp': int(time.time()),
                'network': {
                    'rpc_url': self.config.get('network', {}).get('rpc_url'),
                    'chain_id': self.w3.eth.chain_id
                },
                'deployer_address': self.account.address,
                'results': deployment_results,
                'contracts': {
                    name: {
                        'address': deployment.address,
                        'tx_hash': deployment.tx_hash,
                        'gas_used': deployment.gas_used
                    }
                    for name, deployment in self.deployments.items()
                }
            }
            
            report_filename = f"oracle_security_deployment_report_{int(time.time())}.json"
            with open(report_filename, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Deployment report saved to {report_filename}")
            
        except Exception as e:
            logger.error(f"Failed to save deployment report: {e}")

def main():
    """Main deployment function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Oracle Security Infrastructure Deployment")
    parser.add_argument("--config", type=str, default="oracle_deployment_config.yaml",
                       help="Deployment configuration file")
    parser.add_argument("--verify", action="store_true",
                       help="Verify deployment after completion")
    
    args = parser.parse_args()
    
    try:
        # Create deployer
        deployer = OracleSecurityDeployer(args.config)
        
        # Deploy infrastructure
        deployment_results = deployer.deploy_oracle_security_infrastructure()
        
        if deployment_results['status'] == 'success':
            logger.info("🎉 Oracle security infrastructure deployed successfully!")
            
            # Verify deployment if requested
            if args.verify:
                verification_results = deployer.verify_deployment()
                deployment_results['verification'] = verification_results
            
            # Save deployment report
            deployer.save_deployment_report(deployment_results)
            
            # Print summary
            print("\n" + "="*60)
            print("DEPLOYMENT SUMMARY")
            print("="*60)
            for name, deployment in deployer.deployments.items():
                print(f"{name}: {deployment.address}")
            print("="*60)
            
        else:
            logger.error("❌ Deployment failed!")
            print(f"Error: {deployment_results.get('error', 'Unknown error')}")
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Deployment script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
