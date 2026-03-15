"""
GnuPG Integration Module
Provides integration with GnuPG for secure transaction signing and verification.
"""
import os
import json
import hashlib
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    import gnupg
except ImportError:
    logger.warning("python-gnupg package not installed. GnuPG integration will not be available.")
    gnupg = None

class GnuPGTransactionSigner:
    """
    Provides multi-signature transaction security using GnuPG.
    """
    
    def __init__(self, gnupghome: str = None, required_signatures: int = 3):
        """
        Initialize GnuPG transaction signer.
        
        Args:
            gnupghome: Path to GnuPG home directory
            required_signatures: Number of required signatures (default: 3)
        """
        if gnupg is None:
            raise ImportError("python-gnupg package is required for GnuPGTransactionSigner")
        
        self.gnupghome = gnupghome or os.path.expanduser('~/.gnupg')
        self.gpg = gnupg.GPG(gnupghome=self.gnupghome)
        self.required_signatures = required_signatures
        self.authorized_keys = self._load_authorized_keys()
        
        logger.info(f"Initialized GnuPG Transaction Signer with {len(self.authorized_keys)} authorized keys")
    
    def _load_authorized_keys(self) -> List[str]:
        """
        Load authorized GPG keys.
        
        Returns:
            List of authorized key IDs
        """
        # Get all keys in the keyring
        keys = self.gpg.list_keys()
        authorized_keys = [key['keyid'] for key in keys]
        
        # Check if we have a configuration file with authorized keys
        config_path = os.path.join(self.gnupghome, 'authorized_keys.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                if 'authorized_keys' in config and isinstance(config['authorized_keys'], list):
                    authorized_keys = config['authorized_keys']
            except Exception as e:
                logger.error(f"Error loading authorized keys configuration: {e}")
        
        logger.info(f"Loaded {len(authorized_keys)} authorized keys")
        return authorized_keys
    
    def create_multisig_transaction(self, transaction_data: Dict) -> str:
        """
        Create transaction requiring multiple GPG signatures.
        
        Args:
            transaction_data: Transaction data dictionary
            
        Returns:
            JSON string containing transaction and signature collection
        """
        # 1. Serialize transaction data
        transaction_json = json.dumps(transaction_data, sort_keys=True)
        
        # 2. Create signature collection structure
        signature_collection = {
            'transaction': transaction_data,
            'transaction_hash': hashlib.sha3_256(transaction_json.encode()).hexdigest(),
            'required_signatures': self.required_signatures,
            'signatures': [],
            'created_at': datetime.now().isoformat()
        }
        
        # 3. Initial signature by transaction creator
        creator_signature = self._sign_data(transaction_json)
        signature_collection['signatures'].append({
            'signer': self.gpg.list_keys()[0]['keyid'],
            'signature': creator_signature,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"Created multi-signature transaction requiring {self.required_signatures} signatures")
        return json.dumps(signature_collection)
    
    def add_signature(self, signature_collection_json: str, signer_keyid: str) -> str:
        """
        Add a signature to the collection.
        
        Args:
            signature_collection_json: JSON string containing signature collection
            signer_keyid: Key ID of the signer
            
        Returns:
            Updated JSON string containing signature collection
            
        Raises:
            ValueError: If signer is unauthorized or transaction has been tampered with
        """
        collection = json.loads(signature_collection_json)
        
        # Verify signer is authorized
        if signer_keyid not in self.authorized_keys:
            logger.error(f"Unauthorized signer: {signer_keyid}")
            raise ValueError(f"Unauthorized signer: {signer_keyid}")
        
        # Verify transaction hasn't been tampered with
        transaction_json = json.dumps(collection['transaction'], sort_keys=True)
        expected_hash = hashlib.sha3_256(transaction_json.encode()).hexdigest()
        if collection['transaction_hash'] != expected_hash:
            logger.error("Transaction data has been tampered with")
            raise ValueError("Transaction data has been tampered with")
        
        # Add signature
        signature = self._sign_data(transaction_json, signer_keyid)
        collection['signatures'].append({
            'signer': signer_keyid,
            'signature': signature,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"Added signature from {signer_keyid} to transaction")
        return json.dumps(collection)
    
    def validate_and_execute(self, signature_collection_json: str) -> bool:
        """
        Validate all signatures and execute if threshold met.
        
        Args:
            signature_collection_json: JSON string containing signature collection
            
        Returns:
            True if transaction was validated and executed, False otherwise
        """
        collection = json.loads(signature_collection_json)
        
        # Check if we have enough signatures
        if len(collection['signatures']) < collection['required_signatures']:
            logger.warning(f"Insufficient signatures: {len(collection['signatures'])}/{collection['required_signatures']}")
            return False
        
        # Validate each signature
        transaction_json = json.dumps(collection['transaction'], sort_keys=True)
        valid_signatures = 0
        
        for sig_data in collection['signatures']:
            if self._verify_signature(transaction_json, sig_data['signature'], sig_data['signer']):
                valid_signatures += 1
                logger.info(f"Validated signature from {sig_data['signer']}")
            else:
                logger.warning(f"Invalid signature from {sig_data['signer']}")
        
        if valid_signatures >= collection['required_signatures']:
            # Execute the transaction
            logger.info(f"Threshold met with {valid_signatures}/{collection['required_signatures']} valid signatures")
            return self._execute_transaction(collection['transaction'])
        
        logger.warning(f"Threshold not met: {valid_signatures}/{collection['required_signatures']} valid signatures")
        return False
    
    def _sign_data(self, data: str, keyid: str = None) -> str:
        """
        Sign data with GPG key.
        
        Args:
            data: Data to sign
            keyid: Key ID to use for signing (default: first key in keyring)
            
        Returns:
            Signature string
        """
        signed_data = self.gpg.sign(data, keyid=keyid, detach=True)
        return str(signed_data)
    
    def _verify_signature(self, data: str, signature: str, keyid: str) -> bool:
        """
        Verify GPG signature.
        
        Args:
            data: Original data
            signature: Signature to verify
            keyid: Key ID that created the signature
            
        Returns:
            True if signature is valid, False otherwise
        """
        verified = self.gpg.verify_data(signature, data.encode())
        return verified.valid and verified.key_id == keyid
    
    def _execute_transaction(self, transaction: Dict) -> bool:
        """
        Execute a validated transaction.
        
        Args:
            transaction: Transaction data dictionary
            
        Returns:
            True if transaction was executed successfully, False otherwise
        """
        # This is a placeholder for actual transaction execution logic
        # In a real implementation, this would interact with the blockchain or other systems
        logger.info(f"Executing transaction: {transaction.get('id', 'unknown')}")
        
        # Log transaction details at debug level
        logger.debug(f"Transaction details: {json.dumps(transaction)}")
        
        # Simulate successful execution
        return True
    
    def get_authorized_keys_info(self) -> List[Dict[str, str]]:
        """
        Get information about authorized keys.
        
        Returns:
            List of dictionaries containing key information
        """
        keys_info = []
        all_keys = self.gpg.list_keys()
        
        for key in all_keys:
            if key['keyid'] in self.authorized_keys:
                keys_info.append({
                    'keyid': key['keyid'],
                    'uids': key['uids'],
                    'expires': key['expires'],
                    'length': key['length'],
                    'algo': key['algo']
                })
        
        return keys_info
    
    def add_authorized_key(self, keyid: str) -> bool:
        """
        Add a key to the authorized keys list.
        
        Args:
            keyid: Key ID to add
            
        Returns:
            True if key was added, False otherwise
        """
        # Check if key exists in keyring
        keys = self.gpg.list_keys()
        key_exists = any(key['keyid'] == keyid for key in keys)
        
        if not key_exists:
            logger.error(f"Key {keyid} not found in keyring")
            return False
        
        # Add to authorized keys if not already present
        if keyid not in self.authorized_keys:
            self.authorized_keys.append(keyid)
            self._save_authorized_keys()
            logger.info(f"Added {keyid} to authorized keys")
            return True
        
        logger.info(f"Key {keyid} already in authorized keys")
        return False
    
    def remove_authorized_key(self, keyid: str) -> bool:
        """
        Remove a key from the authorized keys list.
        
        Args:
            keyid: Key ID to remove
            
        Returns:
            True if key was removed, False otherwise
        """
        if keyid in self.authorized_keys:
            self.authorized_keys.remove(keyid)
            self._save_authorized_keys()
            logger.info(f"Removed {keyid} from authorized keys")
            return True
        
        logger.info(f"Key {keyid} not in authorized keys")
        return False
    
    def _save_authorized_keys(self) -> None:
        """Save authorized keys to configuration file."""
        config_path = os.path.join(self.gnupghome, 'authorized_keys.json')
        try:
            with open(config_path, 'w') as f:
                json.dump({'authorized_keys': self.authorized_keys}, f, indent=2)
            logger.info(f"Saved {len(self.authorized_keys)} authorized keys to {config_path}")
        except Exception as e:
            logger.error(f"Error saving authorized keys configuration: {e}")
    
    def set_required_signatures(self, required: int) -> None:
        """
        Set the number of required signatures.
        
        Args:
            required: Number of required signatures
            
        Raises:
            ValueError: If required is less than 1 or greater than the number of authorized keys
        """
        if required < 1:
            raise ValueError("Required signatures must be at least 1")
        
        if required > len(self.authorized_keys):
            raise ValueError(f"Required signatures ({required}) cannot exceed the number of authorized keys ({len(self.authorized_keys)})")
        
        self.required_signatures = required
        logger.info(f"Set required signatures to {required}")


class GnuPGEncryption:
    """
    Provides encryption and decryption using GnuPG.
    """
    
    def __init__(self, gnupghome: str = None):
        """
        Initialize GnuPG encryption.
        
        Args:
            gnupghome: Path to GnuPG home directory
        """
        if gnupg is None:
            raise ImportError("python-gnupg package is required for GnuPGEncryption")
        
        self.gnupghome = gnupghome or os.path.expanduser('~/.gnupg')
        self.gpg = gnupg.GPG(gnupghome=self.gnupghome)
        
        logger.info("Initialized GnuPG Encryption")
    
    def encrypt_data(self, data: Union[str, bytes], recipients: List[str]) -> str:
        """
        Encrypt data for specified recipients.
        
        Args:
            data: Data to encrypt
            recipients: List of recipient key IDs or email addresses
            
        Returns:
            Encrypted data as ASCII-armored string
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        encrypted_data = self.gpg.encrypt(data, recipients, always_trust=True)
        
        if not encrypted_data.ok:
            logger.error(f"Encryption failed: {encrypted_data.status}")
            raise ValueError(f"Encryption failed: {encrypted_data.status}")
        
        logger.info(f"Encrypted data for {len(recipients)} recipients")
        return str(encrypted_data)
    
    def decrypt_data(self, encrypted_data: str, passphrase: Optional[str] = None) -> str:
        """
        Decrypt data.
        
        Args:
            encrypted_data: Encrypted data as ASCII-armored string
            passphrase: Passphrase for private key (optional)
            
        Returns:
            Decrypted data as string
        """
        decrypted_data = self.gpg.decrypt(encrypted_data, passphrase=passphrase)
        
        if not decrypted_data.ok:
            logger.error(f"Decryption failed: {decrypted_data.status}")
            raise ValueError(f"Decryption failed: {decrypted_data.status}")
        
        logger.info("Decrypted data successfully")
        return str(decrypted_data)
    
    def encrypt_file(self, input_path: str, output_path: str, recipients: List[str]) -> bool:
        """
        Encrypt a file for specified recipients.
        
        Args:
            input_path: Path to input file
            output_path: Path to output file
            recipients: List of recipient key IDs or email addresses
            
        Returns:
            True if encryption was successful, False otherwise
        """
        with open(input_path, 'rb') as f:
            status = self.gpg.encrypt_file(f, recipients, output=output_path, always_trust=True)
        
        if status.ok:
            logger.info(f"Encrypted file {input_path} to {output_path}")
            return True
        
        logger.error(f"File encryption failed: {status.status}")
        return False
    
    def decrypt_file(self, input_path: str, output_path: str, passphrase: Optional[str] = None) -> bool:
        """
        Decrypt a file.
        
        Args:
            input_path: Path to encrypted input file
            output_path: Path to output file
            passphrase: Passphrase for private key (optional)
            
        Returns:
            True if decryption was successful, False otherwise
        """
        with open(input_path, 'rb') as f:
            status = self.gpg.decrypt_file(f, output=output_path, passphrase=passphrase)
        
        if status.ok:
            logger.info(f"Decrypted file {input_path} to {output_path}")
            return True
        
        logger.error(f"File decryption failed: {status.status}")
        return False
    
    def list_keys(self, secret: bool = False) -> List[Dict[str, Any]]:
        """
        List keys in the keyring.
        
        Args:
            secret: Whether to list secret keys (default: False)
            
        Returns:
            List of dictionaries containing key information
        """
        if secret:
            return self.gpg.list_keys(True)
        return self.gpg.list_keys()
    
    def import_key(self, key_data: str) -> Dict[str, Any]:
        """
        Import a key into the keyring.
        
        Args:
            key_data: Key data as ASCII-armored string
            
        Returns:
            Import result
        """
        result = self.gpg.import_keys(key_data)
        logger.info(f"Imported {result.count} keys")
        return result.results
    
    def export_key(self, keyid: str, secret: bool = False) -> str:
        """
        Export a key from the keyring.
        
        Args:
            keyid: Key ID to export
            secret: Whether to export secret key (default: False)
            
        Returns:
            Key data as ASCII-armored string
        """
        if secret:
            key_data = self.gpg.export_keys(keyid, True)
            logger.info(f"Exported secret key {keyid}")
        else:
            key_data = self.gpg.export_keys(keyid)
            logger.info(f"Exported public key {keyid}")
        
        return key_data


if __name__ == "__main__":
    # Example usage
    if gnupg is not None:
        # Initialize GnuPG transaction signer
        signer = GnuPGTransactionSigner()
        
        # Create a test transaction
        transaction = {
            "id": "tx123456",
            "amount": 100.0,
            "from_account": "0x1234567890abcdef",
            "to_account": "0xabcdef1234567890",
            "timestamp": datetime.now().isoformat()
        }
        
        # Create multi-signature transaction
        multisig_tx = signer.create_multisig_transaction(transaction)
        print(f"Created multi-signature transaction: {multisig_tx}")
        
        # Initialize GnuPG encryption
        encryption = GnuPGEncryption()
        
        # List keys
        keys = encryption.list_keys()
        print(f"Available keys: {len(keys)}")
        for key in keys:
            print(f"- {key['keyid']}: {key['uids']}")
    else:
        print("python-gnupg package not installed. Examples cannot be run.")