#!/usr/bin/env python3
# =================================================================================================
# SECURE TRANSACTION SIGNER MODULE
# =================================================================================================

import os
import re
import json
import logging
import time
import hashlib
import base64
import subprocess
from typing import Dict, Any, Optional, Union
from web3 import Web3
from web3.types import TxParams, Wei, ChecksumAddress
from dotenv import load_dotenv
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("transaction_signer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SecureSigner")

# Load environment variables
load_dotenv()

class TransactionSigner(ABC):
    """Abstract base class for transaction signers"""
    
    @abstractmethod
    def sign_transaction(self, tx: TxParams) -> str:
        """Sign a transaction and return the signed transaction hash"""
        pass
    
    @abstractmethod
    def get_address(self) -> str:
        """Get the address associated with this signer"""
        pass

class HSMSigner(TransactionSigner):
    """Hardware Security Module transaction signer"""
    
    def __init__(self, provider: str, config_path: str):
        """
        Initialize HSM signer
        
        Args:
            provider: The HSM provider (aws, azure, hashicorp, fortanix)
            config_path: Path to the HSM configuration file
        """
        self.provider = provider
        self.config_path = config_path
        self.address = None
        self._initialize_hsm()
    
    def _initialize_hsm(self):
        """Initialize connection to the HSM"""
        logger.info(f"Initializing HSM with provider: {self.provider}")
        
        try:
            # Load HSM configuration
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            
            # Initialize provider-specific HSM client
            if self.provider == "aws":
                self._init_aws_hsm()
            elif self.provider == "azure":
                self._init_azure_hsm()
            elif self.provider == "hashicorp":
                self._init_hashicorp_hsm()
            elif self.provider == "fortanix":
                self._init_fortanix_hsm()
            else:
                # No local fallback - enforce HSM-only operation
                raise ValueError(f"Unsupported HSM provider: {self.provider}. Must use a valid HSM provider.")
            
            # Add HSM health monitoring
            self._monitor_hsm_health()
            
            logger.info(f"HSM initialized successfully. Address: {self.address}")
        except Exception as e:
            logger.error(f"Failed to initialize HSM: {e}")
            raise
    
    def _init_aws_hsm(self):
        """Initialize AWS CloudHSM"""
        try:
            import boto3
            from botocore.config import Config
            
            # AWS KMS configuration
            region = self.config.get("region", "us-east-1")
            key_id = self.config.get("key_id")
            
            if not key_id:
                raise ValueError("AWS KMS key_id is required")
            
            # Initialize KMS client
            self.kms = boto3.client(
                'kms',
                region_name=region,
                config=Config(
                    retries=dict(
                        max_attempts=10
                    )
                )
            )
            
            # Get public key to derive address
            response = self.kms.get_public_key(
                KeyId=key_id
            )
            
            # Derive Ethereum address from public key
            # This is a simplified example - in production, you would properly derive the address
            # from the public key using the appropriate cryptographic operations
            self.address = "0x" + self.config.get("address", "")
            self.key_id = key_id
            
            logger.info(f"AWS KMS initialized with key ID: {key_id}")
        except Exception as e:
            logger.error(f"Failed to initialize AWS HSM: {e}")
            raise
    
    def _init_azure_hsm(self):
        """Initialize Azure Key Vault"""
        try:
            from azure.identity import DefaultAzureCredential
            from azure.keyvault.keys import KeyClient
            from azure.keyvault.keys.crypto import CryptographyClient
            
            # Azure Key Vault configuration
            vault_url = self.config.get("vault_url")
            key_name = self.config.get("key_name")
            
            if not vault_url or not key_name:
                raise ValueError("Azure Key Vault URL and key name are required")
            
            # Initialize Key Vault client
            credential = DefaultAzureCredential()
            key_client = KeyClient(vault_url=vault_url, credential=credential)
            key = key_client.get_key(key_name)
            
            # Initialize cryptography client
            self.crypto_client = CryptographyClient(key, credential=credential)
            
            # Set address from config
            self.address = "0x" + self.config.get("address", "")
            
            logger.info(f"Azure Key Vault initialized with key: {key_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Azure HSM: {e}")
            raise
    
    def _init_hashicorp_hsm(self):
        """Initialize HashiCorp Vault"""
        try:
            import hvac
            
            # HashiCorp Vault configuration
            vault_url = self.config.get("vault_url")
            token = self.config.get("token")
            secret_path = self.config.get("secret_path")
            
            if not vault_url or not token or not secret_path:
                raise ValueError("Vault URL, token, and secret path are required")
            
            # Initialize Vault client
            self.vault_client = hvac.Client(
                url=vault_url,
                token=token
            )
            
            # Verify authentication
            if not self.vault_client.is_authenticated():
                raise ValueError("Failed to authenticate with Vault")
            
            # Set address from config
            self.address = "0x" + self.config.get("address", "")
            self.secret_path = secret_path
            
            logger.info(f"HashiCorp Vault initialized with secret path: {secret_path}")
        except Exception as e:
            logger.error(f"Failed to initialize HashiCorp Vault: {e}")
            raise
    
    def _init_fortanix_hsm(self):
        """Initialize Fortanix DSM"""
        try:
            # Fortanix configuration
            api_endpoint = self.config.get("api_endpoint")
            api_key = self.config.get("api_key")
            key_name = self.config.get("key_name")
            
            if not api_endpoint or not api_key or not key_name:
                raise ValueError("Fortanix API endpoint, API key, and key name are required")
            
            # In a real implementation, you would initialize the Fortanix client here
            # For this example, we'll just set the address from config
            self.address = "0x" + self.config.get("address", "")
            
            logger.info(f"Fortanix DSM initialized with key: {key_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Fortanix HSM: {e}")
            raise
    
# Local signer has been removed for security reasons
    
    def sign_transaction(self, tx: TxParams) -> str:
        """
        Sign a transaction using the HSM
        
        Args:
            tx: The transaction parameters
            
        Returns:
            The signed transaction hash
        """
        logger.info(f"Signing transaction with HSM ({self.provider})")
        
        try:
            # Provider-specific signing logic
            if self.provider == "aws":
                return self._sign_with_aws(tx)
            elif self.provider == "azure":
                return self._sign_with_azure(tx)
            elif self.provider == "hashicorp":
                return self._sign_with_hashicorp(tx)
            elif self.provider == "fortanix":
                return self._sign_with_fortanix(tx)
            else:
                raise ValueError(f"Unsupported HSM provider: {self.provider}")
        except Exception as e:
            logger.error(f"Failed to sign transaction: {e}")
            raise
    
    def _sign_with_aws(self, tx: TxParams) -> str:
        """Sign transaction with AWS KMS"""
        try:
            import boto3
            from eth_account._utils.legacy_transactions import serializable_unsigned_transaction_from_dict
            from eth_utils import keccak
            
            # 1. Serialize the transaction
            unsigned_tx = serializable_unsigned_transaction_from_dict(tx)
            serialized_tx = unsigned_tx.serialize()
            
            # 2. Hash the serialized transaction
            tx_hash = keccak(serialized_tx)
            
            # 3. Sign the hash with KMS
            kms_client = boto3.client('kms', region_name=self.region)
            sign_response = kms_client.sign(
                KeyId=self.key_id,
                Message=tx_hash,
                MessageType='DIGEST',
                SigningAlgorithm='ECDSA_SHA_256'
            )
            
            # 4. Extract R, S values from the signature
            signature = sign_response['Signature']
            r = int.from_bytes(signature[:32], byteorder='big')
            s = int.from_bytes(signature[32:64], byteorder='big')
            
            # 5. Determine the recovery ID (v)
            # This is a simplified approach - in production, you'd need to try both v=0 and v=1
            # and check which one recovers to your expected address
            for v in range(2):
                recovered_address = self.web3.eth.account.recoverHash(tx_hash, vrs=(v, r, s))
                if recovered_address.lower() == self.address.lower():
                    break
            else:
                raise ValueError("Could not determine the correct recovery ID")
            
            # 6. Create the signed transaction
            chain_id = tx.get('chainId', None)
            if chain_id is not None:
                v += chain_id * 2 + 35
            
            from eth_account.datastructures import SignedTransaction
            signed_tx = SignedTransaction(
                rawTransaction=unsigned_tx.with_signature(vrs=(v, r, s)).serialize(),
                hash=keccak(unsigned_tx.with_signature(vrs=(v, r, s)).serialize()),
                r=r,
                s=s,
                v=v
            )
            
            logger.info(f"Transaction signed with AWS KMS key: {self.key_id}")
            return Web3.to_hex(signed_tx.rawTransaction)
        except Exception as e:
            logger.error(f"AWS KMS signing failed: {e}")
            raise
    
    def _sign_with_azure(self, tx: TxParams) -> str:
        """Sign transaction with Azure Key Vault"""
        try:
            from azure.identity import ClientSecretCredential
            from azure.keyvault.keys.crypto import CryptographyClient
            from eth_account._utils.legacy_transactions import serializable_unsigned_transaction_from_dict
            from eth_utils import keccak
            
            # 1. Serialize the transaction
            unsigned_tx = serializable_unsigned_transaction_from_dict(tx)
            serialized_tx = unsigned_tx.serialize()
            
            # 2. Hash the serialized transaction
            tx_hash = keccak(serialized_tx)
            
            # 3. Get client secret from environment variable
            client_secret = os.getenv(self.client_secret_env_var)
            if not client_secret:
                raise ValueError(f"Environment variable {self.client_secret_env_var} not set")
            
            # 4. Create Azure Key Vault client
            credential = ClientSecretCredential(
                tenant_id=self.tenant_id,
                client_id=self.client_id,
                client_secret=client_secret
            )
            
            # 5. Create cryptography client
            key_url = f"{self.vault_url}/keys/{self.key_name}"
            crypto_client = CryptographyClient(key_url, credential)
            
            # 6. Sign the hash with Azure Key Vault
            sign_result = crypto_client.sign(
                algorithm="ES256K",
                digest=tx_hash
            )
            
            # 7. Extract R, S values from the signature
            signature = sign_result.signature
            r = int.from_bytes(signature[:32], byteorder='big')
            s = int.from_bytes(signature[32:64], byteorder='big')
            
            # 8. Determine the recovery ID (v)
            for v in range(2):
                recovered_address = self.web3.eth.account.recoverHash(tx_hash, vrs=(v, r, s))
                if recovered_address.lower() == self.address.lower():
                    break
            else:
                raise ValueError("Could not determine the correct recovery ID")
            
            # 9. Create the signed transaction
            chain_id = tx.get('chainId', None)
            if chain_id is not None:
                v += chain_id * 2 + 35
            
            from eth_account.datastructures import SignedTransaction
            signed_tx = SignedTransaction(
                rawTransaction=unsigned_tx.with_signature(vrs=(v, r, s)).serialize(),
                hash=keccak(unsigned_tx.with_signature(vrs=(v, r, s)).serialize()),
                r=r,
                s=s,
                v=v
            )
            
            logger.info(f"Transaction signed with Azure Key Vault: {self.key_name}")
            return Web3.to_hex(signed_tx.rawTransaction)
        except Exception as e:
            logger.error(f"Azure Key Vault signing failed: {e}")
            raise
    
    def _sign_with_hashicorp(self, tx: TxParams) -> str:
        """Sign transaction with HashiCorp Vault"""
        # Similar to AWS implementation
        logger.info(f"Transaction would be signed with HashiCorp Vault path: {self.secret_path}")
        return "0x" + "0" * 64
    
    def _sign_with_fortanix(self, tx: TxParams) -> str:
        """Sign transaction with Fortanix DSM"""
        # Similar to AWS implementation
        logger.info("Transaction would be signed with Fortanix DSM")
        return "0x" + "0" * 64
    
# _sign_with_local method has been removed for security reasons
    
    def _monitor_hsm_health(self):
        """Monitor HSM health and set up automatic failover"""
        logger.info(f"Setting up HSM health monitoring for {self.provider}")
        
        # Set up health check interval (in seconds)
        self.health_check_interval = self.config.get("health_check_interval", 60)
        
        # Set up backup HSM provider if available
        self.backup_provider = self.config.get("backup_provider")
        self.backup_config_path = self.config.get("backup_config_path")
        
        if self.backup_provider and self.backup_config_path:
            logger.info(f"Configured backup HSM: {self.backup_provider}")
            
            # Start health monitoring in a background thread
            import threading
            self.monitoring_thread = threading.Thread(
                target=self._health_monitoring_loop,
                daemon=True
            )
            self.monitoring_thread.start()
    
    def _health_monitoring_loop(self):
        """Background thread for continuous HSM health monitoring"""
        import time
        
        while True:
            try:
                # Perform health check on primary HSM
                if not self._check_hsm_health():
                    logger.warning(f"Primary HSM {self.provider} health check failed, attempting failover")
                    self._perform_hsm_failover()
                
                # Wait for next check interval
                time.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"Error in HSM health monitoring: {e}")
                time.sleep(self.health_check_interval)
    
    def _check_hsm_health(self) -> bool:
        """Check if the HSM is healthy and responsive"""
        try:
            # Perform a simple signing operation to test HSM connectivity
            test_message = b"HSM health check"
            
            if self.provider == "aws":
                # AWS KMS health check
                self.kms_client.sign(
                    KeyId=self.config["key_id"],
                    Message=test_message,
                    MessageType="RAW",
                    SigningAlgorithm="ECDSA_SHA_256"
                )
            elif self.provider == "azure":
                # Azure Key Vault health check
                self.key_client.sign(
                    algorithm="ES256",
                    digest=hashlib.sha256(test_message).digest()
                )
            elif self.provider == "hashicorp":
                # Hashicorp Vault health check
                self.vault_client.transit.sign(
                    name=self.config["key_name"],
                    input_data=base64.b64encode(test_message).decode()
                )
            elif self.provider == "fortanix":
                # Fortanix DSM health check
                self.fortanix_client.sign(
                    key_id=self.config["key_id"],
                    data=test_message,
                    hash_algorithm="SHA256"
                )
            
            return True
        except Exception as e:
            logger.error(f"HSM health check failed: {e}")
            return False
    
    def _perform_hsm_failover(self):
        """Perform failover to backup HSM"""
        if not self.backup_provider or not self.backup_config_path:
            logger.error("No backup HSM configured for failover")
            return
        
        try:
            logger.info(f"Performing failover from {self.provider} to {self.backup_provider}")
            
            # Store current provider info for potential recovery
            old_provider = self.provider
            old_config_path = self.config_path
            
            # Switch to backup provider
            self.provider = self.backup_provider
            self.config_path = self.backup_config_path
            
            # Initialize the backup HSM
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            
            # Initialize provider-specific HSM client
            if self.provider == "aws":
                self._init_aws_hsm()
            elif self.provider == "azure":
                self._init_azure_hsm()
            elif self.provider == "hashicorp":
                self._init_hashicorp_hsm()
            elif self.provider == "fortanix":
                self._init_fortanix_hsm()
            else:
                raise ValueError(f"Unsupported backup HSM provider: {self.provider}")
            
            # Update backup configuration
            self.backup_provider = old_provider
            self.backup_config_path = old_config_path
            
            logger.info(f"Failover to {self.provider} successful. New address: {self.address}")
        except Exception as e:
            logger.error(f"HSM failover failed: {e}")
            raise
    
    def get_address(self) -> str:
        """Get the address associated with this signer"""
        return self.address

class GnuPGSigner(TransactionSigner):
    """GnuPG-based transaction signer with hardware token support"""
    
    def __init__(self, key_id: str, gnupg_home: str = None):
        """
        Initialize GnuPG signer
        
        Args:
            key_id: GnuPG key ID to use for signing
            gnupg_home: Path to GnuPG home directory (default: ~/.gnupg)
        """
        self.key_id = key_id
        self.gnupg_home = gnupg_home
        self.address = None
        
        # Initialize GnuPG
        self._initialize_gnupg()
    
    def _initialize_gnupg(self):
        """Initialize GnuPG"""
        try:
            import gnupg
            
            # Initialize GnuPG
            self.gpg = gnupg.GPG(gnupghome=self.gnupg_home)
            
            # Verify key exists
            keys = self.gpg.list_keys(True)  # True for private keys
            key_found = False
            
            for key in keys:
                if key['keyid'] == self.key_id or key['fingerprint'].endswith(self.key_id):
                    key_found = True
                    logger.info(f"Found GnuPG key: {key['keyid']} for {key['uids']}")
                    
                    # Extract Ethereum address from key UID if available
                    for uid in key['uids']:
                        # Look for Ethereum address in UID (format: "Name <email> (0x...)")
                        match = re.search(r'\(0x[0-9a-fA-F]{40}\)', uid)
                        if match:
                            self.address = match.group(0)[1:-1]  # Remove parentheses
                            logger.info(f"Extracted Ethereum address from key UID: {self.address}")
                            break
                    
                    break
            
            if not key_found:
                raise ValueError(f"GnuPG key with ID {self.key_id} not found")
            
            # If address wasn't found in UIDs, generate a deterministic one from the public key
            if not self.address:
                public_key = self.gpg.export_keys(self.key_id)
                self.address = self._derive_address_from_public_key(public_key)
                logger.info(f"Generated deterministic Ethereum address: {self.address}")
            
            # Check if hardware token is available
            self._check_hardware_token()
            
            logger.info(f"GnuPG signer initialized with key ID: {self.key_id}")
        except ImportError:
            logger.error("python-gnupg package not installed. Install with: pip install python-gnupg")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize GnuPG: {e}")
            raise
    
    def _check_hardware_token(self):
        """Check if a hardware token (YubiKey/Nitrokey) is available"""
        try:
            # Check for hardware token by looking at card status
            result = subprocess.run(
                ["gpg", "--card-status"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0 and "Serial number" in result.stdout:
                logger.info("Hardware token detected")
                self.has_hardware_token = True
                
                # Extract token type
                if "Yubikey" in result.stdout or "YubiKey" in result.stdout:
                    self.token_type = "YubiKey"
                elif "Nitrokey" in result.stdout:
                    self.token_type = "Nitrokey"
                else:
                    self.token_type = "Unknown"
                
                logger.info(f"Using {self.token_type} hardware token for signing")
            else:
                logger.warning("No hardware token detected, using software-based GnuPG")
                self.has_hardware_token = False
                self.token_type = None
        except Exception as e:
            logger.warning(f"Failed to check for hardware token: {e}")
            self.has_hardware_token = False
            self.token_type = None
    
    def _derive_address_from_public_key(self, public_key: str) -> str:
        """Derive Ethereum address from GnuPG public key"""
        import hashlib
        from eth_utils import to_checksum_address
        
        # Hash the public key
        key_hash = hashlib.sha256(public_key.encode()).digest()
        
        # Take the last 20 bytes and convert to Ethereum address
        address = "0x" + key_hash[-20:].hex()
        
        # Convert to checksum address
        return to_checksum_address(address)
    
    def sign_transaction(self, tx: TxParams) -> str:
        """
        Sign a transaction using GnuPG
        
        Args:
            tx: The transaction parameters
            
        Returns:
            The signed transaction hash
        """
        logger.info(f"Signing transaction with GnuPG (key ID: {self.key_id})")
        
        try:
            from eth_account import Account
            from eth_account.messages import encode_structured_data
            
            # Convert transaction to EIP-712 typed data
            typed_data = self._convert_tx_to_typed_data(tx)
            
            # Serialize the typed data
            message = json.dumps(typed_data, sort_keys=True)
            
            # Sign the message with GnuPG
            signature = self.gpg.sign(
                message,
                keyid=self.key_id,
                detach=True,
                clearsign=False
            )
            
            if not signature:
                raise ValueError("Failed to sign transaction with GnuPG")
            
            # Extract R, S, V components from the signature
            sig_bytes = signature.data
            
            # For multi-signature schemes, we return the signature data
            # that will be submitted to the multi-sig contract
            return {
                "message": message,
                "signature": sig_bytes.hex(),
                "signer": self.address
            }
        except Exception as e:
            logger.error(f"Failed to sign transaction: {e}")
            raise
    
    def _convert_tx_to_typed_data(self, tx: TxParams) -> dict:
        """Convert Ethereum transaction to EIP-712 typed data"""
        # Create EIP-712 typed data structure
        typed_data = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                ],
                "Transaction": [
                    {"name": "to", "type": "address"},
                    {"name": "value", "type": "uint256"},
                    {"name": "gas", "type": "uint256"},
                    {"name": "gasPrice", "type": "uint256"},
                    {"name": "nonce", "type": "uint256"},
                    {"name": "data", "type": "bytes"},
                ]
            },
            "primaryType": "Transaction",
            "domain": {
                "name": "Secure Transaction",
                "version": "1",
                "chainId": tx.get("chainId", 1),
            },
            "message": {
                "to": tx.get("to", "${CONTRACT_ADDRESS}"),
                "value": tx.get("value", 0),
                "gas": tx.get("gas", 21000),
                "gasPrice": tx.get("gasPrice", 0),
                "nonce": tx.get("nonce", 0),
                "data": tx.get("data", "0x"),
            }
        }
        
        return typed_data
    
    def get_address(self) -> str:
        """Get the address associated with this signer"""
        return self.address


class MultiSigSigner(TransactionSigner):
    """Multi-signature wallet transaction signer"""
    
    def __init__(self, web3: Web3, multisig_address: str, interface: str = "gnosis"):
        """
        Initialize multi-sig signer
        
        Args:
            web3: Web3 instance
            multisig_address: Address of the multi-sig wallet
            interface: Multi-sig interface type (gnosis, safe)
        """
        self.web3 = web3
        self.multisig_address = multisig_address
        self.interface = interface
        self._initialize_multisig()
    
    def _initialize_multisig(self):
        """Initialize connection to the multi-sig wallet"""
        logger.info(f"Initializing multi-sig wallet: {self.multisig_address}")
        
        try:
            # Load ABI based on interface type
            if self.interface == "gnosis":
                abi_path = "abi/GnosisSafe.json"
            elif self.interface == "safe":
                abi_path = "abi/Safe.json"
            else:
                raise ValueError(f"Unsupported multi-sig interface: {self.interface}")
            
            # Load ABI
            with open(abi_path, 'r') as f:
                abi = json.load(f)
            
            # Initialize contract
            self.multisig = self.web3.eth.contract(
                address=self.multisig_address,
                abi=abi
            )
            
            logger.info(f"Multi-sig wallet initialized: {self.multisig_address}")
        except Exception as e:
            logger.error(f"Failed to initialize multi-sig wallet: {e}")
            raise
    
    def sign_transaction(self, tx: TxParams) -> str:
        """
        Create a multi-sig transaction proposal
        
        Args:
            tx: The transaction parameters
            
        Returns:
            The transaction hash of the proposal
        """
        logger.info(f"Creating multi-sig transaction proposal")
        
        try:
            # Extract transaction details
            to = tx.get('to')
            value = tx.get('value', 0)
            data = tx.get('data', '0x')
            
            # Create transaction proposal
            if self.interface == "gnosis":
                return self._create_gnosis_proposal(to, value, data)
            elif self.interface == "safe":
                return self._create_safe_proposal(to, value, data)
            else:
                raise ValueError(f"Unsupported multi-sig interface: {self.interface}")
        except Exception as e:
            logger.error(f"Failed to create multi-sig transaction proposal: {e}")
            raise
    
    def _create_gnosis_proposal(self, to: str, value: int, data: str) -> str:
        """Create a Gnosis Safe transaction proposal"""
        # In a real implementation, you would:
        # 1. Create a transaction proposal
        # 2. Sign the proposal
        # 3. Submit the proposal to the Gnosis Safe
        
        # For this example, we'll just return a placeholder
        logger.info(f"Transaction proposal would be created for Gnosis Safe: {self.multisig_address}")
        return "0x" + "0" * 64
    
    def _create_safe_proposal(self, to: str, value: int, data: str) -> str:
        """Create a Safe transaction proposal"""
        # Similar to Gnosis implementation
        logger.info(f"Transaction proposal would be created for Safe: {self.multisig_address}")
        return "0x" + "0" * 64
    
    def get_address(self) -> str:
        """Get the address of the multi-sig wallet"""
        return self.multisig_address

class KeePassXCClient:
    """KeePassXC client for secure secret management"""
    
    def __init__(self, database_path: str = None, keyfile_path: str = None):
        """
        Initialize KeePassXC client
        
        Args:
            database_path: Path to KeePassXC database file
            keyfile_path: Path to keyfile for database (optional)
        """
        self.database_path = database_path
        self.keyfile_path = keyfile_path
        self.connected = False
        
        # Initialize KeePassXC client
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize KeePassXC client"""
        try:
            # Check if KeePassXC is installed
            result = subprocess.run(
                ["keepassxc-cli", "--version"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                logger.error("KeePassXC CLI not found. Please install KeePassXC.")
                raise ValueError("KeePassXC CLI not found")
            
            logger.info(f"KeePassXC CLI found: {result.stdout.strip()}")
            
            # If database path is provided, verify it exists
            if self.database_path:
                if not os.path.exists(self.database_path):
                    raise ValueError(f"KeePassXC database not found: {self.database_path}")
                
                logger.info(f"KeePassXC database found: {self.database_path}")
                
                # If keyfile is provided, verify it exists
                if self.keyfile_path and not os.path.exists(self.keyfile_path):
                    raise ValueError(f"KeePassXC keyfile not found: {self.keyfile_path}")
            
            self.connected = True
            logger.info("KeePassXC client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize KeePassXC client: {e}")
            raise
    
    def get_secret(self, entry_path: str, field: str = "password") -> str:
        """
        Get a secret from KeePassXC
        
        Args:
            entry_path: Path to entry in KeePassXC database
            field: Field to retrieve (default: password)
            
        Returns:
            The secret value
        """
        if not self.connected or not self.database_path:
            raise ValueError("KeePassXC client not connected or database not specified")
        
        try:
            # Build command
            cmd = ["keepassxc-cli", "show", "--quiet"]
            
            # Add keyfile if provided
            if self.keyfile_path:
                cmd.extend(["--key-file", self.keyfile_path])
            
            # Add database and entry path
            cmd.extend([self.database_path, entry_path])
            
            # Run command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                input=os.environ.get("KEEPASSXC_PASSWORD", ""),
                check=False
            )
            
            if result.returncode != 0:
                raise ValueError(f"Failed to get secret: {result.stderr}")
            
            # Parse output to find the requested field
            lines = result.stdout.strip().split("\n")
            for line in lines:
                if line.startswith(f"{field}: "):
                    return line[len(f"{field}: "):]
            
            raise ValueError(f"Field '{field}' not found in entry '{entry_path}'")
        except Exception as e:
            logger.error(f"Failed to get secret from KeePassXC: {e}")
            raise
    
    def create_secret(self, entry_path: str, username: str, password: str, url: str = "", notes: str = "") -> bool:
        """
        Create a new secret in KeePassXC
        
        Args:
            entry_path: Path to entry in KeePassXC database
            username: Username for the entry
            password: Password for the entry
            url: URL for the entry (optional)
            notes: Notes for the entry (optional)
            
        Returns:
            True if successful
        """
        if not self.connected or not self.database_path:
            raise ValueError("KeePassXC client not connected or database not specified")
        
        try:
            # Build command
            cmd = ["keepassxc-cli", "add", "--quiet"]
            
            # Add keyfile if provided
            if self.keyfile_path:
                cmd.extend(["--key-file", self.keyfile_path])
            
            # Add database and entry path
            cmd.extend([self.database_path, entry_path])
            
            # Run command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                input=f"{os.environ.get('KEEPASSXC_PASSWORD', '')}\n{username}\n{password}\n{url}\n{notes}\n",
                check=False
            )
            
            if result.returncode != 0:
                raise ValueError(f"Failed to create secret: {result.stderr}")
            
            logger.info(f"Secret created successfully: {entry_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create secret in KeePassXC: {e}")
            raise
    
    def rotate_secret(self, entry_path: str, new_password: str = None) -> bool:
        """
        Rotate a secret in KeePassXC
        
        Args:
            entry_path: Path to entry in KeePassXC database
            new_password: New password (if None, generates a random one)
            
        Returns:
            True if successful
        """
        if not self.connected or not self.database_path:
            raise ValueError("KeePassXC client not connected or database not specified")
        
        try:
            # Get current entry details
            username = self.get_secret(entry_path, "UserName")
            url = self.get_secret(entry_path, "URL")
            notes = self.get_secret(entry_path, "Notes")
            
            # Generate random password if not provided
            if new_password is None:
                import secrets
                import string
                alphabet = string.ascii_letters + string.digits + string.punctuation
                new_password = ''.join(secrets.choice(alphabet) for _ in range(32))
            
            # Delete existing entry
            self._delete_secret(entry_path)
            
            # Create new entry with rotated password
            self.create_secret(entry_path, username, new_password, url, notes)
            
            logger.info(f"Secret rotated successfully: {entry_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to rotate secret in KeePassXC: {e}")
            raise
    
    def _delete_secret(self, entry_path: str) -> bool:
        """
        Delete a secret from KeePassXC
        
        Args:
            entry_path: Path to entry in KeePassXC database
            
        Returns:
            True if successful
        """
        if not self.connected or not self.database_path:
            raise ValueError("KeePassXC client not connected or database not specified")
        
        try:
            # Build command
            cmd = ["keepassxc-cli", "rm", "--quiet"]
            
            # Add keyfile if provided
            if self.keyfile_path:
                cmd.extend(["--key-file", self.keyfile_path])
            
            # Add database and entry path
            cmd.extend([self.database_path, entry_path])
            
            # Run command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                input=os.environ.get("KEEPASSXC_PASSWORD", ""),
                check=False
            )
            
            if result.returncode != 0:
                raise ValueError(f"Failed to delete secret: {result.stderr}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to delete secret from KeePassXC: {e}")
            raise


class EnterpriseKeyManager:
    """Enterprise-grade key management system with multiple secure backends"""
    
    def __init__(self):
        """Initialize the Enterprise Key Manager with multiple secure backends"""
        # Initialize HSM signers
        self.hsm_primary = HSMSigner("aws", os.getenv("AWS_HSM_CONFIG_PATH", "aws_hsm_config.json"))
        self.hsm_backup = HSMSigner("azure", os.getenv("AZURE_HSM_CONFIG_PATH", "azure_hsm_config.json"))
        
        # Initialize GnuPG signer
        gnupg_key_id = os.getenv("GNUPG_KEY_ID")
        gnupg_home = os.getenv("GNUPG_HOME", os.path.expanduser("~/.gnupg"))
        self.gnupg_signer = GnuPGSigner(gnupg_key_id, gnupg_home)
        
        # Initialize KeePassXC client
        keepass_db = os.getenv("KEEPASSXC_DATABASE")
        keepass_keyfile = os.getenv("KEEPASSXC_KEYFILE")
        self.keepass_client = KeePassXCClient(keepass_db, keepass_keyfile)
        
        # NO LOCAL FALLBACK - EVER
        logger.info("Enterprise Key Manager initialized with secure backends only")
    
    def sign_transaction(self, tx: TxParams, signer_type: str = "hsm_primary") -> str:
        """
        Sign a transaction using the specified signer
        
        Args:
            tx: The transaction parameters
            signer_type: The type of signer to use (hsm_primary, hsm_backup, gnupg)
            
        Returns:
            The signed transaction
        """
        logger.info(f"Signing transaction with {signer_type}")
        
        if signer_type == "hsm_primary":
            return self.hsm_primary.sign_transaction(tx)
        elif signer_type == "hsm_backup":
            return self.hsm_backup.sign_transaction(tx)
        elif signer_type == "gnupg":
            return self.gnupg_signer.sign_transaction(tx)
        else:
            raise ValueError(f"Unknown signer type: {signer_type}")
    
    def get_secret(self, entry_path: str, field: str = "password") -> str:
        """
        Get a secret from KeePassXC
        
        Args:
            entry_path: Path to entry in KeePassXC database
            field: Field to retrieve (default: password)
            
        Returns:
            The secret value
        """
        return self.keepass_client.get_secret(entry_path, field)
    
    def rotate_secret(self, entry_path: str, new_password: str = None) -> bool:
        """
        Rotate a secret in KeePassXC
        
        Args:
            entry_path: Path to entry in KeePassXC database
            new_password: New password (if None, generates a random one)
            
        Returns:
            True if successful
        """
        return self.keepass_client.rotate_secret(entry_path, new_password)
    
    def get_primary_address(self) -> str:
        """Get the address of the primary HSM signer"""
        return self.hsm_primary.get_address()
    
    def get_backup_address(self) -> str:
        """Get the address of the backup HSM signer"""
        return self.hsm_backup.get_address()
    
    def get_gnupg_address(self) -> str:
        """Get the address of the GnuPG signer"""
        return self.gnupg_signer.get_address()


def get_transaction_signer() -> TransactionSigner:
    """
    Factory function to get the appropriate transaction signer based on configuration
    
    Returns:
        A TransactionSigner instance
    """
    # Check if HSM is enabled
    hsm_enabled = os.getenv("HSM_ENABLED", "false").lower() == "true"
    multisig_enabled = os.getenv("MULTISIG_ENABLED", "false").lower() == "true"
    gnupg_enabled = os.getenv("GNUPG_ENABLED", "false").lower() == "true"
    
    if hsm_enabled:
        # Initialize HSM signer
        hsm_provider = os.getenv("HSM_PROVIDER", "aws")
        hsm_config_path = os.getenv("HSM_CONFIG_PATH", "hsm_config.json")
        
        # Validate HSM provider
        valid_providers = ["aws", "azure", "hashicorp", "fortanix"]
        if hsm_provider not in valid_providers:
            raise ValueError(f"Invalid HSM provider: {hsm_provider}. Must be one of: {', '.join(valid_providers)}")
        
        logger.info(f"Using HSM signer with provider: {hsm_provider}")
        return HSMSigner(hsm_provider, hsm_config_path)
    elif multisig_enabled:
        # Initialize multi-sig signer
        rpc_url = os.getenv("RPC_URL")
        multisig_address = os.getenv("MULTISIG_ADDRESS")
        multisig_interface = os.getenv("MULTISIG_INTERFACE", "gnosis")
        
        if not rpc_url or not multisig_address:
            raise ValueError("RPC_URL and MULTISIG_ADDRESS are required for multi-sig signer")
        
        web3 = Web3(Web3.HTTPProvider(rpc_url))
        
        logger.info(f"Using multi-sig signer with address: {multisig_address}")
        return MultiSigSigner(web3, multisig_address, multisig_interface)
    elif gnupg_enabled:
        # Initialize GnuPG signer
        gnupg_key_id = os.getenv("GNUPG_KEY_ID")
        gnupg_home = os.getenv("GNUPG_HOME", os.path.expanduser("~/.gnupg"))
        
        if not gnupg_key_id:
            raise ValueError("GNUPG_KEY_ID is required for GnuPG signer")
        
        logger.info(f"Using GnuPG signer with key ID: {gnupg_key_id}")
        return GnuPGSigner(gnupg_key_id, gnupg_home)
    else:
        raise ValueError("No secure transaction signing method enabled. Enable either HSM_ENABLED, MULTISIG_ENABLED, or GNUPG_ENABLED in .env")