"""
Quantum Security Manager
Provides a unified interface for quantum-resistant security features.
"""
import os
import json
import logging
import datetime
from typing import Dict, Any, List, Optional, Tuple, Union

from quantum_security.quantum_crypto import (
    DilithiumSignature,
    SPHINCSPlusSignature,
    QuantumKeyDistribution,
    QuantumResistantEncryption,
    GnuPGQuantumExtensions
)
from quantum_security.gnupg_quantum import GnuPGQuantumConfig
from quantum_security.gnupg_integration import (
    GnuPGTransactionSigner,
    GnuPGEncryption
)
from quantum_security.hardware_token import HardwareTokenManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QuantumSecurityManager:
    """
    Unified manager for quantum-resistant security features.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the quantum security manager.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.dilithium = DilithiumSignature(
            security_level=self.config.get("dilithium_security_level", 3)
        )
        self.sphincs = SPHINCSPlusSignature(
            security_level=self.config.get("sphincs_security_level", 192)
        )
        self.qkd = QuantumKeyDistribution(
            simulation_mode=self.config.get("qkd_simulation_mode", True)
        )
        self.encryption = QuantumResistantEncryption(
            algorithm=self.config.get("encryption_algorithm", "AES256-GCM-SIV")
        )
        self.gnupg = GnuPGQuantumExtensions()
        self.gnupg_config = GnuPGQuantumConfig(
            gnupg_home=self.config.get("gnupg_home", None)
        )
        
        # Initialize GnuPG integration components
        gnupghome = self.config.get("gnupg_home", os.path.expanduser("~/.gnupg"))
        required_signatures = self.config.get("required_signatures", 3)
        try:
            self.transaction_signer = GnuPGTransactionSigner(
                gnupghome=gnupghome,
                required_signatures=required_signatures
            )
            self.gpg_encryption = GnuPGEncryption(gnupghome=gnupghome)
            self.hardware_token = HardwareTokenManager(gnupghome=gnupghome)
            logger.info("GnuPG integration components initialized")
        except ImportError as e:
            logger.warning(f"GnuPG integration not available: {e}")
            self.transaction_signer = None
            self.gpg_encryption = None
            self.hardware_token = None
        
        logger.info("Initialized Quantum Security Manager")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """
        Load configuration from file or use defaults.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        default_config = {
            "dilithium_security_level": 3,
            "sphincs_security_level": 192,
            "qkd_simulation_mode": True,
            "encryption_algorithm": "AES256-GCM-SIV",
            "gnupg_home": None,
            "key_storage_path": "quantum_keys",
            "auto_rotate_keys": True,
            "key_rotation_interval_days": 30
        }
        
        if not config_path or not os.path.exists(config_path):
            logger.info("Using default quantum security configuration")
            return default_config
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Merge with defaults for any missing keys
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            
            logger.info(f"Loaded quantum security configuration from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}")
            return default_config
    
    def save_config(self, config_path: str) -> bool:
        """
        Save current configuration to file.
        
        Args:
            config_path: Path to save configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info(f"Saved quantum security configuration to {config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration to {config_path}: {e}")
            return False
    
    def setup_quantum_security(self) -> Dict[str, Any]:
        """
        Set up all quantum security features.
        
        Returns:
            Status dictionary
        """
        status = {}
        
        # Set up GnuPG quantum extensions
        try:
            self.gnupg_config.apply_quantum_resistant_settings()
            status["gnupg_quantum_config"] = "success"
        except Exception as e:
            logger.error(f"Error setting up GnuPG quantum extensions: {e}")
            status["gnupg_quantum_config"] = f"error: {str(e)}"
        
        # Generate initial keys
        try:
            dilithium_keys = self.generate_dilithium_keypair()
            status["dilithium_keys"] = "generated"
        except Exception as e:
            logger.error(f"Error generating Dilithium keys: {e}")
            status["dilithium_keys"] = f"error: {str(e)}"
        
        try:
            sphincs_keys = self.generate_sphincs_keypair()
            status["sphincs_keys"] = "generated"
        except Exception as e:
            logger.error(f"Error generating SPHINCS+ keys: {e}")
            status["sphincs_keys"] = f"error: {str(e)}"
        
        # Test QKD
        try:
            qkd_key = self.qkd.generate_quantum_key()
            status["qkd_test"] = "success"
        except Exception as e:
            logger.error(f"Error testing QKD: {e}")
            status["qkd_test"] = f"error: {str(e)}"
        
        logger.info("Quantum security setup completed")
        return status
    
    def generate_dilithium_keypair(self) -> Dict[str, bytes]:
        """
        Generate a new Dilithium keypair.
        
        Returns:
            Dictionary containing public and private keys
        """
        public_key, private_key = self.dilithium.generate_keypair()
        
        # Store keys if storage path is configured
        if "key_storage_path" in self.config:
            self._store_keypair("dilithium", public_key, private_key)
        
        return {
            "public_key": public_key,
            "private_key": private_key
        }
    
    def generate_sphincs_keypair(self) -> Dict[str, bytes]:
        """
        Generate a new SPHINCS+ keypair.
        
        Returns:
            Dictionary containing public and private keys
        """
        public_key, private_key = self.sphincs.generate_keypair()
        
        # Store keys if storage path is configured
        if "key_storage_path" in self.config:
            self._store_keypair("sphincs", public_key, private_key)
        
        return {
            "public_key": public_key,
            "private_key": private_key
        }
    
    def _store_keypair(self, key_type: str, public_key: bytes, private_key: bytes) -> None:
        """
        Store a keypair securely.
        
        Args:
            key_type: Type of key (e.g., "dilithium", "sphincs")
            public_key: Public key bytes
            private_key: Private key bytes
        """
        storage_path = self.config["key_storage_path"]
        os.makedirs(storage_path, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Store public key
        public_key_path = os.path.join(storage_path, f"{key_type}_public_{timestamp}.key")
        with open(public_key_path, 'wb') as f:
            f.write(public_key)
        
        # Store private key (in a real implementation, this would be encrypted)
        private_key_path = os.path.join(storage_path, f"{key_type}_private_{timestamp}.key")
        with open(private_key_path, 'wb') as f:
            f.write(private_key)
        
        logger.info(f"Stored {key_type} keypair with timestamp {timestamp}")
    
    def sign_data(self, data: bytes, key_type: str = "dilithium", private_key: Optional[bytes] = None) -> bytes:
        """
        Sign data using a quantum-resistant signature algorithm.
        
        Args:
            data: Data to sign
            key_type: Type of key to use ("dilithium" or "sphincs")
            private_key: Private key to use (if None, will attempt to load from storage)
            
        Returns:
            Signature bytes
        """
        if private_key is None:
            private_key = self._load_latest_private_key(key_type)
        
        if key_type.lower() == "dilithium":
            signature = self.dilithium.sign(data, private_key)
        elif key_type.lower() == "sphincs":
            signature = self.sphincs.sign(data, private_key)
        else:
            raise ValueError(f"Unsupported key type: {key_type}")
        
        logger.info(f"Signed data using {key_type}")
        return signature
    
    def verify_signature(self, data: bytes, signature: bytes, key_type: str, public_key: bytes) -> bool:
        """
        Verify a signature using a quantum-resistant signature algorithm.
        
        Args:
            data: Original data
            signature: Signature to verify
            key_type: Type of key used ("dilithium" or "sphincs")
            public_key: Public key to use for verification
            
        Returns:
            True if signature is valid, False otherwise
        """
        if key_type.lower() == "dilithium":
            result = self.dilithium.verify(data, signature, public_key)
        elif key_type.lower() == "sphincs":
            result = self.sphincs.verify(data, signature, public_key)
        else:
            raise ValueError(f"Unsupported key type: {key_type}")
        
        logger.info(f"Verified {key_type} signature: {'valid' if result else 'invalid'}")
        return result
    
    def _load_latest_private_key(self, key_type: str) -> bytes:
        """
        Load the latest private key of the specified type from storage.
        
        Args:
            key_type: Type of key to load
            
        Returns:
            Private key bytes
        """
        storage_path = self.config["key_storage_path"]
        if not os.path.exists(storage_path):
            raise FileNotFoundError(f"Key storage path does not exist: {storage_path}")
        
        # Find the latest private key file
        private_key_files = [
            f for f in os.listdir(storage_path)
            if f.startswith(f"{key_type}_private_") and f.endswith(".key")
        ]
        
        if not private_key_files:
            raise FileNotFoundError(f"No {key_type} private keys found in {storage_path}")
        
        # Sort by timestamp (which is part of the filename)
        latest_key_file = sorted(private_key_files)[-1]
        key_path = os.path.join(storage_path, latest_key_file)
        
        with open(key_path, 'rb') as f:
            private_key = f.read()
        
        logger.info(f"Loaded latest {key_type} private key: {latest_key_file}")
        return private_key
    
    def encrypt_data(self, data: bytes, key: Optional[bytes] = None) -> Dict[str, bytes]:
        """
        Encrypt data using quantum-resistant encryption.
        
        Args:
            data: Data to encrypt
            key: Encryption key (if None, will generate a new quantum key)
            
        Returns:
            Dictionary containing ciphertext and nonce
        """
        if key is None:
            key = self.qkd.generate_quantum_key()
        
        ciphertext, nonce = self.encryption.encrypt(data, key)
        
        logger.info(f"Encrypted {len(data)} bytes of data")
        return {
            "ciphertext": ciphertext,
            "nonce": nonce,
            "key": key
        }
    
    def decrypt_data(self, ciphertext: bytes, key: bytes, nonce: bytes) -> bytes:
        """
        Decrypt data using quantum-resistant encryption.
        
        Args:
            ciphertext: Data to decrypt
            key: Decryption key
            nonce: Nonce used during encryption
            
        Returns:
            Decrypted data
        """
        plaintext = self.encryption.decrypt(ciphertext, key, nonce)
        
        logger.info(f"Decrypted {len(ciphertext)} bytes of data")
        return plaintext
    
    def rotate_keys(self) -> Dict[str, Any]:
        """
        Rotate all quantum-resistant keys.
        
        Returns:
            Status dictionary
        """
        status = {}
        
        # Rotate Dilithium keys
        try:
            dilithium_keys = self.generate_dilithium_keypair()
            status["dilithium"] = "rotated"
        except Exception as e:
            logger.error(f"Error rotating Dilithium keys: {e}")
            status["dilithium"] = f"error: {str(e)}"
        
        # Rotate SPHINCS+ keys
        try:
            sphincs_keys = self.generate_sphincs_keypair()
            status["sphincs"] = "rotated"
        except Exception as e:
            logger.error(f"Error rotating SPHINCS+ keys: {e}")
            status["sphincs"] = f"error: {str(e)}"
        
        logger.info("Rotated quantum-resistant keys")
        return status
    
    def check_key_rotation(self) -> bool:
        """
        Check if keys need to be rotated based on the configured interval.
        
        Returns:
            True if keys were rotated, False otherwise
        """
        if not self.config.get("auto_rotate_keys", True):
            logger.info("Automatic key rotation is disabled")
            return False
        
        storage_path = self.config["key_storage_path"]
        if not os.path.exists(storage_path):
            logger.warning(f"Key storage path does not exist: {storage_path}")
            return False
        
        # Check Dilithium keys
        dilithium_key_files = [
            f for f in os.listdir(storage_path)
            if f.startswith("dilithium_private_") and f.endswith(".key")
        ]
        
        if not dilithium_key_files:
            logger.info("No Dilithium keys found, generating new ones")
            self.rotate_keys()
            return True
        
        # Get the timestamp from the latest key file
        latest_key_file = sorted(dilithium_key_files)[-1]
        timestamp_str = latest_key_file.replace("dilithium_private_", "").replace(".key", "")
        
        try:
            timestamp = datetime.datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
            now = datetime.datetime.now()
            
            # Check if the key is older than the rotation interval
            rotation_interval = datetime.timedelta(days=self.config.get("key_rotation_interval_days", 30))
            
            if now - timestamp > rotation_interval:
                logger.info(f"Keys are older than {rotation_interval.days} days, rotating")
                self.rotate_keys()
                return True
            else:
                logger.info("Keys are still within the rotation interval")
                return False
                
        except ValueError:
            logger.warning(f"Could not parse timestamp from key file: {latest_key_file}")
            return False
    
    def get_security_status(self) -> Dict[str, Any]:
        """
        Get the current status of quantum security features.
        
        Returns:
            Status dictionary
        """
        storage_path = self.config.get("key_storage_path")
        
        # Count keys if storage path exists
        key_counts = {"dilithium": 0, "sphincs": 0}
        if storage_path and os.path.exists(storage_path):
            for key_type in key_counts:
                key_counts[key_type] = len([
                    f for f in os.listdir(storage_path)
                    if f.startswith(f"{key_type}_public_") and f.endswith(".key")
                ])
        
        status = {
            "dilithium_security_level": self.config.get("dilithium_security_level", 3),
            "sphincs_security_level": self.config.get("sphincs_security_level", 192),
            "qkd_simulation_mode": self.config.get("qkd_simulation_mode", True),
            "encryption_algorithm": self.config.get("encryption_algorithm", "AES256-GCM-SIV"),
            "auto_rotate_keys": self.config.get("auto_rotate_keys", True),
            "key_rotation_interval_days": self.config.get("key_rotation_interval_days", 30),
            "key_counts": key_counts,
            "gnupg_quantum_extensions": True,
            "gnupg_integration_available": self.transaction_signer is not None,
            "hardware_token_available": self.hardware_token is not None
        }
        
        # Add hardware token status if available
        if self.hardware_token is not None:
            try:
                token_status = self.hardware_token.get_token_status()
                status["hardware_token"] = {
                    "detected": token_status["detected"],
                    "has_keys": token_status["has_keys"]
                }
            except Exception as e:
                logger.warning(f"Error getting hardware token status: {e}")
                status["hardware_token"] = {
                    "detected": False,
                    "has_keys": False,
                    "error": str(e)
                }
        
        return status
        
    def create_multisig_transaction(self, transaction_data: Dict) -> str:
        """
        Create a transaction requiring multiple GPG signatures.
        
        Args:
            transaction_data: Transaction data dictionary
            
        Returns:
            JSON string containing transaction and signature collection
            
        Raises:
            ValueError: If GnuPG integration is not available
        """
        if self.transaction_signer is None:
            raise ValueError("GnuPG integration is not available")
        
        logger.info("Creating multi-signature transaction")
        return self.transaction_signer.create_multisig_transaction(transaction_data)
    
    def add_signature(self, signature_collection_json: str, signer_keyid: str) -> str:
        """
        Add a signature to a multi-signature transaction.
        
        Args:
            signature_collection_json: JSON string containing signature collection
            signer_keyid: Key ID of the signer
            
        Returns:
            Updated JSON string containing signature collection
            
        Raises:
            ValueError: If GnuPG integration is not available
        """
        if self.transaction_signer is None:
            raise ValueError("GnuPG integration is not available")
        
        logger.info(f"Adding signature from {signer_keyid} to transaction")
        return self.transaction_signer.add_signature(signature_collection_json, signer_keyid)
    
    def validate_and_execute_transaction(self, signature_collection_json: str) -> bool:
        """
        Validate all signatures and execute a transaction if threshold is met.
        
        Args:
            signature_collection_json: JSON string containing signature collection
            
        Returns:
            True if transaction was validated and executed, False otherwise
            
        Raises:
            ValueError: If GnuPG integration is not available
        """
        if self.transaction_signer is None:
            raise ValueError("GnuPG integration is not available")
        
        logger.info("Validating and executing multi-signature transaction")
        return self.transaction_signer.validate_and_execute(signature_collection_json)
    
    def get_authorized_keys(self) -> List[Dict[str, str]]:
        """
        Get information about authorized GPG keys.
        
        Returns:
            List of dictionaries containing key information
            
        Raises:
            ValueError: If GnuPG integration is not available
        """
        if self.transaction_signer is None:
            raise ValueError("GnuPG integration is not available")
        
        logger.info("Getting authorized keys")
        return self.transaction_signer.get_authorized_keys_info()
    
    def add_authorized_key(self, keyid: str) -> bool:
        """
        Add a key to the authorized keys list.
        
        Args:
            keyid: Key ID to add
            
        Returns:
            True if key was added, False otherwise
            
        Raises:
            ValueError: If GnuPG integration is not available
        """
        if self.transaction_signer is None:
            raise ValueError("GnuPG integration is not available")
        
        logger.info(f"Adding {keyid} to authorized keys")
        return self.transaction_signer.add_authorized_key(keyid)
    
    def remove_authorized_key(self, keyid: str) -> bool:
        """
        Remove a key from the authorized keys list.
        
        Args:
            keyid: Key ID to remove
            
        Returns:
            True if key was removed, False otherwise
            
        Raises:
            ValueError: If GnuPG integration is not available
        """
        if self.transaction_signer is None:
            raise ValueError("GnuPG integration is not available")
        
        logger.info(f"Removing {keyid} from authorized keys")
        return self.transaction_signer.remove_authorized_key(keyid)
    
    def set_required_signatures(self, required: int) -> None:
        """
        Set the number of required signatures for multi-signature transactions.
        
        Args:
            required: Number of required signatures
            
        Raises:
            ValueError: If GnuPG integration is not available or required is invalid
        """
        if self.transaction_signer is None:
            raise ValueError("GnuPG integration is not available")
        
        logger.info(f"Setting required signatures to {required}")
        self.transaction_signer.set_required_signatures(required)
    
    def setup_hardware_token(self, name: str, email: str, backup_dir: Optional[str] = None) -> bool:
        """
        Set up a hardware token with GPG keys.
        
        Args:
            name: Name for the key
            email: Email for the key
            backup_dir: Directory to store key backups (optional)
            
        Returns:
            True if setup was successful, False otherwise
            
        Raises:
            ValueError: If hardware token integration is not available
        """
        if self.hardware_token is None:
            raise ValueError("Hardware token integration is not available")
        
        logger.info(f"Setting up hardware token for {name} <{email}>")
        return self.hardware_token.setup_token(name, email, backup_dir)
    
    def detect_hardware_tokens(self) -> List[Dict[str, Any]]:
        """
        Detect connected hardware tokens.
        
        Returns:
            List of dictionaries containing token information
            
        Raises:
            ValueError: If hardware token integration is not available
        """
        if self.hardware_token is None:
            raise ValueError("Hardware token integration is not available")
        
        logger.info("Detecting hardware tokens")
        return self.hardware_token.detect_tokens()
    
    def backup_gpg_keys(self, backup_dir: str) -> bool:
        """
        Backup GPG keys.
        
        Args:
            backup_dir: Directory to store key backups
            
        Returns:
            True if backup was successful, False otherwise
            
        Raises:
            ValueError: If hardware token integration is not available
        """
        if self.hardware_token is None:
            raise ValueError("Hardware token integration is not available")
        
        logger.info(f"Backing up GPG keys to {backup_dir}")
        return self.hardware_token.backup_keys(backup_dir)
    
    def restore_gpg_keys(self, backup_dir: str) -> bool:
        """
        Restore GPG keys from backup.
        
        Args:
            backup_dir: Directory containing key backups
            
        Returns:
            True if restore was successful, False otherwise
            
        Raises:
            ValueError: If hardware token integration is not available
        """
        if self.hardware_token is None:
            raise ValueError("Hardware token integration is not available")
        
        logger.info(f"Restoring GPG keys from {backup_dir}")
        return self.hardware_token.restore_keys(backup_dir)


if __name__ == "__main__":
    # Example usage
    manager = QuantumSecurityManager()
    status = manager.setup_quantum_security()
    print("Quantum security setup status:", json.dumps(status, indent=2))
    
    # Generate and verify a signature
    data = b"This is a test message"
    keys = manager.generate_dilithium_keypair()
    signature = manager.sign_data(data, "dilithium", keys["private_key"])
    is_valid = manager.verify_signature(data, signature, "dilithium", keys["public_key"])
    print(f"Signature verification: {is_valid}")
    
    # Encrypt and decrypt data
    encrypted = manager.encrypt_data(data)
    decrypted = manager.decrypt_data(encrypted["ciphertext"], encrypted["key"], encrypted["nonce"])
    print(f"Decryption successful: {decrypted == data}")
    print(f"Decrypted data: {decrypted.decode('utf-8')}")
    
    # Get security status
    security_status = manager.get_security_status()
    print("\nSecurity Status:")
    print(f"GnuPG Integration Available: {security_status.get('gnupg_integration_available', False)}")
    print(f"Hardware Token Available: {security_status.get('hardware_token_available', False)}")
    
    # Test GnuPG integration if available
    if security_status.get('gnupg_integration_available', False):
        print("\nTesting GnuPG Multi-Signature Transaction:")
        try:
            # Create a test transaction
            transaction = {
                "id": "tx123456",
                "amount": 100.0,
                "from_account": "0x1234567890abcdef",
                "to_account": "0xabcdef1234567890",
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            # Create multi-signature transaction
            multisig_tx = manager.create_multisig_transaction(transaction)
            print("Created multi-signature transaction")
            
            # Get authorized keys
            keys = manager.get_authorized_keys()
            print(f"Authorized keys: {len(keys)}")
            
            if len(keys) > 0:
                # Add another signature if we have more than one key
                if len(keys) > 1:
                    second_key = keys[1]["keyid"] if keys[0]["keyid"] != keys[1]["keyid"] else keys[0]["keyid"]
                    multisig_tx = manager.add_signature(multisig_tx, second_key)
                    print(f"Added signature from {second_key}")
                
                # Validate and execute transaction
                result = manager.validate_and_execute_transaction(multisig_tx)
                print(f"Transaction execution result: {result}")
        except Exception as e:
            print(f"Error testing GnuPG integration: {e}")
    
    # Test hardware token integration if available
    if security_status.get('hardware_token_available', False):
        print("\nTesting Hardware Token Integration:")
        try:
            # Detect tokens
            tokens = manager.detect_hardware_tokens()
            print(f"Detected {len(tokens)} hardware tokens")
            
            # Get token status
            if 'hardware_token' in security_status:
                token_status = security_status['hardware_token']
                print(f"Token detected: {token_status.get('detected', False)}")
                print(f"Token has keys: {token_status.get('has_keys', False)}")
        except Exception as e:
            print(f"Error testing hardware token integration: {e}")