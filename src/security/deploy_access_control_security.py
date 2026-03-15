"""
Emergency Access Control Security Deployment Script
Deploy access control fixes for identified vulnerabilities
"""

import json
import time
from web3 import Web3
from eth_account import Account
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AccessControlSecurityDeployer:
    def __init__(self, web3_provider_url, private_key, network_id=1):
        """
        Initialize the security deployer
        
        Args:
            web3_provider_url: Web3 provider URL
            private_key: Private key for deployment
            network_id: Network ID (1 for mainnet, 11155111 for sepolia)
        """
        self.w3 = Web3(Web3.HTTPProvider(web3_provider_url))
        self.account = Account.from_key(private_key)
        self.network_id = network_id
        
        # Verify connection
        if not self.w3.is_connected():
            raise Exception("Failed to connect to Web3 provider")
        
        logger.info(f"Connected to network {network_id}")
        logger.info(f"Deployer address: {self.account.address}")
        logger.info(f"Balance: {self.w3.from_wei(self.w3.eth.get_balance(self.account.address), 'ether')} ETH")
    
    def deploy_access_control_fix(self):
        """Deploy the AccessControlSecurityFix contract"""
        
        # Read the compiled contract (this would be from your build artifacts)
        with open('artifacts/contracts/AccessControlSecurityFix.sol/AccessControlSecurityFix.json', 'r') as f:
            contract_data = json.load(f)
        
        # Contract deployment
        contract = self.w3.eth.contract(
            abi=contract_data['abi'],
            bytecode=contract_data['bytecode']
        )
        
        # Constructor arguments
        constructor_args = [self.account.address]  # admin address
        
        # Build transaction
        transaction = contract.constructor(*constructor_args).build_transaction({
            'from': self.account.address,
            'gas': 3000000,
            'gasPrice': self.w3.to_wei('20', 'gwei'),
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
        })
        
        # Sign and send transaction
        signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        logger.info(f"AccessControlSecurityFix deployment transaction: {tx_hash.hex()}")
        
        # Wait for transaction receipt
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            logger.info(f"AccessControlSecurityFix deployed successfully at: {receipt.contractAddress}")
            return receipt.contractAddress
        else:
            raise Exception("AccessControlSecurityFix deployment failed")
    
    def deploy_security_patches(self):
        """Deploy the SecurityPatches contract"""
        
        # Read the compiled contract
        with open('artifacts/contracts/SecurityPatches.sol/SecurityPatches.json', 'r') as f:
            contract_data = json.load(f)
        
        # Contract deployment
        contract = self.w3.eth.contract(
            abi=contract_data['abi'],
            bytecode=contract_data['bytecode']
        )
        
        # Build transaction
        transaction = contract.constructor().build_transaction({
            'from': self.account.address,
            'gas': 4000000,
            'gasPrice': self.w3.to_wei('20', 'gwei'),
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
        })
        
        # Sign and send transaction
        signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        logger.info(f"SecurityPatches deployment transaction: {tx_hash.hex()}")
        
        # Wait for transaction receipt
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            logger.info(f"SecurityPatches deployed successfully at: {receipt.contractAddress}")
            return receipt.contractAddress
        else:
            raise Exception("SecurityPatches deployment failed")
    
    def setup_access_control_roles(self, access_control_address, role_assignments):
        """
        Setup initial access control roles
        
        Args:
            access_control_address: Address of the deployed AccessControlSecurityFix contract
            role_assignments: Dictionary of role assignments
        """
        
        # Load contract ABI
        with open('artifacts/contracts/AccessControlSecurityFix.sol/AccessControlSecurityFix.json', 'r') as f:
            contract_data = json.load(f)
        
        contract = self.w3.eth.contract(
            address=access_control_address,
            abi=contract_data['abi']
        )
        
        for role_name, addresses in role_assignments.items():
            role_hash = self.w3.keccak(text=role_name).hex()
            
            for address in addresses:
                # Grant role
                transaction = contract.functions.grantRole(role_hash, address).build_transaction({
                    'from': self.account.address,
                    'gas': 100000,
                    'gasPrice': self.w3.to_wei('20', 'gwei'),
                    'nonce': self.w3.eth.get_transaction_count(self.account.address),
                })
                
                signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                
                if receipt.status == 1:
                    logger.info(f"Granted {role_name} to {address}")
                else:
                    logger.error(f"Failed to grant {role_name} to {address}")
    
    def approve_strategy_proposers(self, access_control_address, proposer_addresses):
        """
        Approve strategy proposers
        
        Args:
            access_control_address: Address of the AccessControlSecurityFix contract
            proposer_addresses: List of addresses to approve as proposers
        """
        
        # Load contract ABI
        with open('artifacts/contracts/AccessControlSecurityFix.sol/AccessControlSecurityFix.json', 'r') as f:
            contract_data = json.load(f)
        
        contract = self.w3.eth.contract(
            address=access_control_address,
            abi=contract_data['abi']
        )
        
        # Batch approve proposers
        approvals = [True] * len(proposer_addresses)
        
        transaction = contract.functions.batchSetProposerApproval(
            proposer_addresses, 
            approvals
        ).build_transaction({
            'from': self.account.address,
            'gas': 500000,
            'gasPrice': self.w3.to_wei('20', 'gwei'),
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
        })
        
        signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            logger.info(f"Batch approved {len(proposer_addresses)} proposers")
        else:
            logger.error("Failed to batch approve proposers")

def main():
    """Main deployment function"""
    
    # Configuration
    WEB3_PROVIDER_URL = "YOUR_WEB3_PROVIDER_URL"  # Replace with your provider
    PRIVATE_KEY = "${PRIVATE_KEY}"  # Replace with your private key
    NETWORK_ID = 11155111  # Sepolia testnet
    
    # Initialize deployer
    deployer = AccessControlSecurityDeployer(WEB3_PROVIDER_URL, PRIVATE_KEY, NETWORK_ID)
    
    try:
        # Deploy contracts
        logger.info("Starting emergency access control security deployment...")
        
        # Deploy AccessControlSecurityFix
        access_control_address = deployer.deploy_access_control_fix()
        
        # Deploy SecurityPatches
        security_patches_address = deployer.deploy_security_patches()
        
        # Setup initial roles
        role_assignments = {
            "STRATEGY_PROPOSER_ROLE": [
                "${CONTRACT_ADDRESS}",  # Replace with actual addresses
                "${CONTRACT_ADDRESS}",
            ],
            "STRATEGY_EXECUTOR_ROLE": [
                "${CONTRACT_ADDRESS}",
            ],
            "SECURITY_MANAGER_ROLE": [
                "${CONTRACT_ADDRESS}",
            ],
            "EMERGENCY_ROLE": [
                deployer.account.address,  # Deployer as emergency admin
            ]
        }
        
        deployer.setup_access_control_roles(access_control_address, role_assignments)
        
        # Approve initial strategy proposers
        initial_proposers = [
            "${CONTRACT_ADDRESS}",
            "${CONTRACT_ADDRESS}",
        ]
        
        deployer.approve_strategy_proposers(access_control_address, initial_proposers)
        
        # Create deployment summary
        deployment_summary = {
            "timestamp": int(time.time()),
            "network_id": NETWORK_ID,
            "deployer": deployer.account.address,
            "contracts": {
                "AccessControlSecurityFix": access_control_address,
                "SecurityPatches": security_patches_address
            },
            "initial_roles": role_assignments,
            "approved_proposers": initial_proposers
        }
        
        # Save deployment summary
        with open('emergency_access_control_deployment.json', 'w') as f:
            json.dump(deployment_summary, f, indent=2)
        
        logger.info("Emergency access control security deployment completed successfully!")
        logger.info(f"Deployment summary saved to emergency_access_control_deployment.json")
        
        return deployment_summary
        
    except Exception as e:
        logger.error(f"Deployment failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
