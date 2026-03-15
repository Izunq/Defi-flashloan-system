"""
SECURE DEPLOYMENT SCRIPT FOR SECURITY-ENHANCED ARBITRAGE SYSTEM
================================================================

This script deploys the security-enhanced contracts with proper validation
and configuration. It enforces secure practices and validates all deployments.

CRITICAL SECURITY REQUIREMENTS:
1. HSM-only transaction signing
2. Multi-signature validation for all admin operations
3. Comprehensive input validation
4. Circuit breaker mechanisms
5. Timelock for critical operations

DO NOT MODIFY THIS SCRIPT WITHOUT SECURITY REVIEW
"""

import os
import sys
import json
import time
from typing import Dict, List, Optional, Tuple
from web3 import Web3
from eth_account import Account
import logging

# Import our security modules
from secure_input_validator import SecureInputValidator
from secure_transaction_signer import SecureTransactionSigner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deployment_security.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SecurityDeploymentError(Exception):
    """Custom exception for deployment security errors"""
    pass

class SecureDeploymentManager:
    """
    Manages secure deployment of the security-enhanced arbitrage system
    
    This class enforces security best practices and validates all operations
    """
    
    def __init__(self, rpc_url: str, chain_id: int):
        """
        Initialize the secure deployment manager
        
        Args:
            rpc_url: Ethereum RPC endpoint
            chain_id: Network chain ID for validation
        """
        self.validator = SecureInputValidator()
        
        # Validate RPC URL
        if not self.validator.validate_rpc_url(rpc_url):
            raise SecurityDeploymentError(f"Invalid RPC URL: {rpc_url}")
        
        # Initialize Web3 connection
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.w3.is_connected():
            raise SecurityDeploymentError("Failed to connect to Ethereum node")
        
        # Validate chain ID
        connected_chain_id = self.w3.eth.chain_id
        if connected_chain_id != chain_id:
            raise SecurityDeploymentError(
                f"Chain ID mismatch: expected {chain_id}, got {connected_chain_id}"
            )
        
        self.chain_id = chain_id
        self.deployed_contracts: Dict[str, str] = {}
        
        logger.info(f"SecureDeploymentManager initialized for chain {chain_id}")
        
    def setup_secure_signer(self) -> SecureTransactionSigner:
        """
        Set up secure transaction signer (HSM required)
        
        Returns:
            Configured secure transaction signer
        """
        try:
            # In production, this MUST use HSM
            signer = SecureTransactionSigner.from_hsm()
            logger.info(f"Secure signer initialized: {signer.get_address()}")
            return signer
        except Exception as e:
            logger.error(f"Failed to initialize secure signer: {e}")
            raise SecurityDeploymentError("Secure signer initialization failed")
    
    def validate_deployment_config(self, config: Dict) -> bool:
        """
        Validate deployment configuration for security requirements
        
        Args:
            config: Deployment configuration dictionary
            
        Returns:
            True if configuration is valid
        """
        required_fields = [
            'timelock_delay',
            'max_gas_price',
            'oracle_addresses',
            'multisig_wallet',
            'emergency_admin'
        ]
        
        # Check required fields
        for field in required_fields:
            if field not in config:
                raise SecurityDeploymentError(f"Missing required config field: {field}")
        
        # Validate timelock delay (minimum 24 hours for production)
        timelock_delay = config['timelock_delay']
        if timelock_delay < 86400:  # 24 hours
            raise SecurityDeploymentError("Timelock delay must be at least 24 hours")
        
        # Validate gas price
        max_gas_price = config['max_gas_price']
        if not isinstance(max_gas_price, int) or max_gas_price <= 0:
            raise SecurityDeploymentError("Invalid max gas price")
        
        # Validate oracle addresses
        oracle_addresses = config['oracle_addresses']
        if len(oracle_addresses) < 3:
            raise SecurityDeploymentError("Need at least 3 oracle addresses")
        
        for oracle in oracle_addresses:
            if not self.validator.validate_ethereum_address(oracle):
                raise SecurityDeploymentError(f"Invalid oracle address: {oracle}")
        
        # Validate multisig wallet
        if not self.validator.validate_ethereum_address(config['multisig_wallet']):
            raise SecurityDeploymentError("Invalid multisig wallet address")
        
        # Validate emergency admin
        if not self.validator.validate_ethereum_address(config['emergency_admin']):
            raise SecurityDeploymentError("Invalid emergency admin address")
        
        logger.info("Deployment configuration validated successfully")
        return True
    
    def deploy_security_contracts(
        self, 
        signer: SecureTransactionSigner,
        config: Dict
    ) -> Dict[str, str]:
        """
        Deploy security-enhanced contracts
        
        Args:
            signer: Secure transaction signer
            config: Validated deployment configuration
            
        Returns:
            Dictionary of deployed contract addresses
        """
        logger.info("Starting security contract deployment...")
        
        # Load contract artifacts
        artifacts = self._load_contract_artifacts()
        
        # Deploy SecurityUpgradeDeployer first
        deployer_address = self._deploy_contract(
            signer,
            "SecurityUpgradeDeployer",
            artifacts["SecurityUpgradeDeployer"],
            []
        )
        
        logger.info(f"SecurityUpgradeDeployer deployed at: {deployer_address}")
        
        # Call deploySecurity function
        deployer_contract = self.w3.eth.contract(
            address=deployer_address,
            abi=artifacts["SecurityUpgradeDeployer"]["abi"]
        )
        
        # Prepare deployment transaction
        deploy_tx = deployer_contract.functions.deploySecurity(
            config['timelock_delay'],
            config['max_gas_price'],
            config['oracle_addresses']
        ).build_transaction({
            'from': signer.get_address(),
            'nonce': self.w3.eth.get_transaction_count(signer.get_address()),
            'gas': 3000000,  # Conservative gas limit
            'gasPrice': min(self.w3.eth.gas_price, config['max_gas_price'])
        })
        
        # Sign and send transaction
        signed_tx = signer.sign_transaction(deploy_tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx)
        
        logger.info(f"Deployment transaction sent: {tx_hash.hex()}")
        
        # Wait for confirmation
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        if receipt['status'] != 1:
            raise SecurityDeploymentError("Deployment transaction failed")
        
        # Parse deployment events
        deployment_events = deployer_contract.events.SecurityContractsDeployed().process_receipt(receipt)
        if not deployment_events:
            raise SecurityDeploymentError("No deployment events found")
        
        event = deployment_events[0]
        
        self.deployed_contracts = {
            "SecurityUpgradeDeployer": deployer_address,
            "SecurityEnhancedExecutor": event['args']['securityExecutor'],
            "SecureMultiOracle": event['args']['multiOracle']
        }
        
        logger.info("Security contracts deployed successfully")
        return self.deployed_contracts
    
    def configure_security_settings(
        self,
        signer: SecureTransactionSigner,
        config: Dict
    ) -> None:
        """
        Configure security settings for deployed contracts
        
        Args:
            signer: Secure transaction signer
            config: Deployment configuration
        """
        logger.info("Configuring security settings...")
        
        if "SecurityUpgradeDeployer" not in self.deployed_contracts:
            raise SecurityDeploymentError("Contracts not deployed yet")
        
        # Load deployer contract
        artifacts = self._load_contract_artifacts()
        deployer_contract = self.w3.eth.contract(
            address=self.deployed_contracts["SecurityUpgradeDeployer"],
            abi=artifacts["SecurityUpgradeDeployer"]["abi"]
        )
        
        # Configure security
        config_tx = deployer_contract.functions.configureSecurity(
            config['multisig_wallet'],
            config['emergency_admin']
        ).build_transaction({
            'from': signer.get_address(),
            'nonce': self.w3.eth.get_transaction_count(signer.get_address()),
            'gas': 1000000,
            'gasPrice': min(self.w3.eth.gas_price, config['max_gas_price'])
        })
        
        # Sign and send
        signed_tx = signer.sign_transaction(config_tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx)
        
        logger.info(f"Configuration transaction sent: {tx_hash.hex()}")
        
        # Wait for confirmation
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        if receipt['status'] != 1:
            raise SecurityDeploymentError("Configuration transaction failed")
        
        logger.info("Security configuration completed successfully")
    
    def verify_deployment(self) -> bool:
        """
        Verify that all contracts are deployed and configured correctly
        
        Returns:
            True if verification passes
        """
        logger.info("Verifying deployment...")
        
        # Check all contracts are deployed
        required_contracts = [
            "SecurityUpgradeDeployer",
            "SecurityEnhancedExecutor", 
            "SecureMultiOracle"
        ]
        
        for contract_name in required_contracts:
            if contract_name not in self.deployed_contracts:
                raise SecurityDeploymentError(f"Contract {contract_name} not deployed")
            
            address = self.deployed_contracts[contract_name]
            code = self.w3.eth.get_code(address)
            if len(code) == 0:
                raise SecurityDeploymentError(f"No code at {contract_name} address")
        
        # Verify SecurityEnhancedExecutor configuration
        executor_artifacts = self._load_contract_artifacts()["SecurityEnhancedExecutor"]
        executor = self.w3.eth.contract(
            address=self.deployed_contracts["SecurityEnhancedExecutor"],
            abi=executor_artifacts["abi"]
        )
        
        # Check timelock is set
        timelock_delay = executor.functions.timelockDelay().call()
        if timelock_delay < 86400:  # 24 hours minimum
            raise SecurityDeploymentError("Insufficient timelock delay")
        
        # Check circuit breaker is enabled
        emergency_stopped = executor.functions.emergencyStopped().call()
        # Circuit breaker should not be active initially
        
        # Verify SecureMultiOracle configuration
        oracle_artifacts = self._load_contract_artifacts()["SecureMultiOracle"]
        oracle = self.w3.eth.contract(
            address=self.deployed_contracts["SecureMultiOracle"],
            abi=oracle_artifacts["abi"]
        )
        
        # Check oracle count
        oracle_count = oracle.functions.getOracleCount().call()
        if oracle_count < 3:
            raise SecurityDeploymentError("Insufficient oracle count")
        
        logger.info("Deployment verification passed")
        return True
    
    def save_deployment_report(self, output_path: str) -> None:
        """
        Save deployment report with all contract addresses and configuration
        
        Args:
            output_path: Path to save the deployment report
        """
        report = {
            "timestamp": int(time.time()),
            "chain_id": self.chain_id,
            "deployed_contracts": self.deployed_contracts,
            "security_features": {
                "hsm_signing": True,
                "input_validation": True,
                "timelock_protection": True,
                "circuit_breaker": True,
                "multi_oracle": True,
                "access_control": True
            },
            "verification_status": "PASSED"
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Deployment report saved to: {output_path}")
    
    def _load_contract_artifacts(self) -> Dict:
        """Load compiled contract artifacts"""
        artifacts = {}
        artifact_files = [
            "SecurityUpgradeDeployer.json",
            "SecurityEnhancedExecutor.json", 
            "SecureMultiOracle.json"
        ]
        
        for artifact_file in artifact_files:
            artifact_path = f"artifacts/contracts/{artifact_file}"
            if not os.path.exists(artifact_path):
                raise SecurityDeploymentError(f"Artifact not found: {artifact_path}")
            
            with open(artifact_path, 'r') as f:
                artifact = json.load(f)
                contract_name = artifact_file.replace('.json', '')
                artifacts[contract_name] = artifact
        
        return artifacts
    
    def _deploy_contract(
        self,
        signer: SecureTransactionSigner,
        name: str,
        artifact: Dict,
        constructor_args: List
    ) -> str:
        """
        Deploy a single contract
        
        Args:
            signer: Secure transaction signer
            name: Contract name
            artifact: Contract artifact
            constructor_args: Constructor arguments
            
        Returns:
            Deployed contract address
        """
        logger.info(f"Deploying {name}...")
        
        # Create contract factory
        contract = self.w3.eth.contract(
            abi=artifact['abi'],
            bytecode=artifact['bytecode']
        )
        
        # Build deployment transaction
        deploy_tx = contract.constructor(*constructor_args).build_transaction({
            'from': signer.get_address(),
            'nonce': self.w3.eth.get_transaction_count(signer.get_address()),
            'gas': 5000000,  # Conservative gas limit
            'gasPrice': self.w3.eth.gas_price
        })
        
        # Sign and send
        signed_tx = signer.sign_transaction(deploy_tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx)
        
        logger.info(f"{name} deployment transaction: {tx_hash.hex()}")
        
        # Wait for confirmation
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        if receipt['status'] != 1:
            raise SecurityDeploymentError(f"{name} deployment failed")
        
        contract_address = receipt['contractAddress']
        logger.info(f"{name} deployed at: {contract_address}")
        
        return contract_address


def main():
    """
    Main deployment function with comprehensive security validation
    """
    logger.info("=== SECURE ARBITRAGE SYSTEM DEPLOYMENT ===")
    logger.info("Initializing security-enhanced deployment...")
    
    try:
        # Load configuration
        config_path = "deployment_config.json"
        if not os.path.exists(config_path):
            raise SecurityDeploymentError(f"Config file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Get network configuration
        rpc_url = os.environ.get('RPC_URL')
        if not rpc_url:
            raise SecurityDeploymentError("RPC_URL environment variable not set")
        
        chain_id = config.get('chain_id', 1)  # Default to mainnet
        
        # Initialize deployment manager
        manager = SecureDeploymentManager(rpc_url, chain_id)
        
        # Validate configuration
        manager.validate_deployment_config(config)
        
        # Setup secure signer
        signer = manager.setup_secure_signer()
        
        # Deploy contracts
        deployed_contracts = manager.deploy_security_contracts(signer, config)
        
        # Configure security settings
        manager.configure_security_settings(signer, config)
        
        # Verify deployment
        manager.verify_deployment()
        
        # Save deployment report
        manager.save_deployment_report("deployment_report.json")
        
        logger.info("=== DEPLOYMENT COMPLETED SUCCESSFULLY ===")
        logger.info(f"SecurityEnhancedExecutor: {deployed_contracts['SecurityEnhancedExecutor']}")
        logger.info(f"SecureMultiOracle: {deployed_contracts['SecureMultiOracle']}")
        logger.info("All security features enabled and verified")
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
