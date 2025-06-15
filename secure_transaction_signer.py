#!/usr/bin/env python3
# =================================================================================================
# SECURE TRANSACTION SIGNER MODULE
# =================================================================================================

import os
import json
import logging
import time
from typing import Dict, Any, Optional, Union
from web3 import Web3
from web3.types import TxParams, Wei
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
            elif self.provider == "local_signer":
                self._init_local_signer()
            else:
                raise ValueError(f"Unsupported HSM provider: {self.provider}")
            
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
    
    def _init_local_signer(self):
        """Initialize local signer (for development/testing only)"""
        logger.warning("Using local signer - THIS IS NOT SECURE FOR PRODUCTION")
        
        try:
            from eth_account import Account
            
            # Local signer configuration
            keyfile_path = self.config.get("keyfile_path")
            password = self.config.get("password")
            
            if not keyfile_path:
                raise ValueError("Keyfile path is required for local signer")
            
            # Load keyfile
            with open(keyfile_path, 'r') as f:
                keyfile_json = json.load(f)
            
            # Decrypt keyfile
            private_key = Account.decrypt(keyfile_json, password)
            self.account = Account.from_key(private_key)
            self.address = self.account.address
            
            logger.info(f"Local signer initialized with address: {self.address}")
        except Exception as e:
            logger.error(f"Failed to initialize local signer: {e}")
            raise
    
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
            elif self.provider == "local_signer":
                return self._sign_with_local(tx)
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
    
    def _sign_with_local(self, tx: TxParams) -> str:
        """Sign transaction with local signer (for development/testing only)"""
        from eth_account.messages import encode_defunct
        
        # Sign transaction with local account
        signed_tx = self.account.sign_transaction(tx)
        return Web3.to_hex(signed_tx.rawTransaction)
    
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

def get_transaction_signer() -> TransactionSigner:
    """
    Factory function to get the appropriate transaction signer based on configuration
    
    Returns:
        A TransactionSigner instance
    """
    # Check if HSM is enabled
    hsm_enabled = os.getenv("HSM_ENABLED", "false").lower() == "true"
    multisig_enabled = os.getenv("MULTISIG_ENABLED", "false").lower() == "true"
    
    if hsm_enabled:
        # Initialize HSM signer
        hsm_provider = os.getenv("HSM_PROVIDER", "aws")
        hsm_config_path = os.getenv("HSM_CONFIG_PATH", "hsm_config.json")
        
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
    else:
        raise ValueError("No secure transaction signing method enabled. Enable either HSM_ENABLED or MULTISIG_ENABLED in .env")