#!/usr/bin/env python3
# =================================================================================================
# CRYPTOGRAPHIC INPUT VALIDATION MODULE
# =================================================================================================

import os
import json
import time
import hmac
import hashlib
import logging
import base64
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from web3 import Web3
from dotenv import load_dotenv

# Try to import cryptographic libraries
try:
    import nacl.signing
    import nacl.encoding
    from nacl.public import PrivateKey, PublicKey, Box
    from nacl.bindings import crypto_sign_ed25519_sk_to_curve25519
    NACL_AVAILABLE = True
except ImportError:
    NACL_AVAILABLE = False
    logging.warning("PyNaCl not available. Ed25519 signatures will be disabled.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("crypto_validation.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("cryptographic_input_validator")

@dataclass
class ValidationContext:
    """Context for validation operations"""
    field_name: str
    source_ip: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: Optional[int] = None
    signature: Optional[str] = None
    public_key: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of a validation operation"""
    is_valid: bool
    value: Any
    error_message: Optional[str] = None
    context: Optional[ValidationContext] = None
    signature: Optional[str] = None


class CryptographicInputValidator:
    """Cryptographic input validator for secure input validation"""
    
    def __init__(self, secret_key: str = None):
        """
        Initialize cryptographic validator
        
        Args:
            secret_key: Secret key for HMAC signatures (if None, generates a random one)
        """
        # Load environment variables
        load_dotenv()
        
        # Initialize secret key
        self.secret_key = secret_key or os.getenv("CRYPTO_VALIDATOR_SECRET")
        
        if not self.secret_key:
            # Generate random secret key
            import secrets
            self.secret_key = secrets.token_hex(32)
            logger.warning("No secret key provided, generated random one")
        
        # Initialize Ed25519 signer if available
        self.ed25519_signer = None
        if NACL_AVAILABLE:
            try:
                # Load or generate Ed25519 key
                private_key_hex = os.getenv("ED25519_PRIVATE_KEY")
                
                if private_key_hex:
                    private_key = bytes.fromhex(private_key_hex)
                    self.ed25519_signer = nacl.signing.SigningKey(private_key)
                else:
                    # Generate new key
                    self.ed25519_signer = nacl.signing.SigningKey.generate()
                    logger.warning("No Ed25519 private key provided, generated random one")
                
                # Get public key
                self.ed25519_public_key = self.ed25519_signer.verify_key
                logger.info(f"Ed25519 public key: {self.ed25519_public_key.encode(encoder=nacl.encoding.HexEncoder).decode()}")
            except Exception as e:
                logger.error(f"Failed to initialize Ed25519 signer: {e}")
        
        # Initialize trusted public keys
        self.trusted_public_keys = self._load_trusted_public_keys()
        
        logger.info("Cryptographic Input Validator initialized")
    
    def _load_trusted_public_keys(self) -> Dict[str, bytes]:
        """
        Load trusted public keys from environment
        
        Returns:
            Dictionary of trusted public keys
        """
        trusted_keys = {}
        
        # Load from environment
        trusted_keys_json = os.getenv("TRUSTED_PUBLIC_KEYS")
        
        if trusted_keys_json:
            try:
                keys_data = json.loads(trusted_keys_json)
                
                for key_id, key_hex in keys_data.items():
                    trusted_keys[key_id] = bytes.fromhex(key_hex)
                
                logger.info(f"Loaded {len(trusted_keys)} trusted public keys")
            except Exception as e:
                logger.error(f"Failed to load trusted public keys: {e}")
        
        return trusted_keys
    
    def sign_input(self, value: Any, context: ValidationContext) -> ValidationResult:
        """
        Sign input data with cryptographic signatures
        
        Args:
            value: Input data to sign
            context: Validation context
            
        Returns:
            Validation result with signature
        """
        # Convert value to string if needed
        if not isinstance(value, str):
            try:
                if isinstance(value, dict) or isinstance(value, list):
                    value_str = json.dumps(value, sort_keys=True)
                else:
                    value_str = str(value)
            except Exception as e:
                logger.error(f"Failed to convert value to string: {e}")
                return ValidationResult(
                    is_valid=False,
                    value=None,
                    error_message=f"Failed to convert value to string: {e}",
                    context=context
                )
        else:
            value_str = value
        
        # Add timestamp if not provided
        timestamp = context.timestamp or int(time.time())
        
        # Create message to sign
        message = f"{context.field_name}:{value_str}:{timestamp}"
        
        # Sign with HMAC-SHA256
        hmac_signature = self._sign_hmac(message.encode())
        
        # Sign with Ed25519 if available
        ed25519_signature = None
        if NACL_AVAILABLE and self.ed25519_signer:
            ed25519_signature = self._sign_ed25519(message.encode())
        
        # Create signature object
        signature = {
            "timestamp": timestamp,
            "hmac": hmac_signature,
            "ed25519": ed25519_signature.hex() if ed25519_signature else None,
            "public_key": self.ed25519_public_key.encode(encoder=nacl.encoding.HexEncoder).decode() if self.ed25519_public_key else None
        }
        
        # Convert signature to string
        signature_str = json.dumps(signature)
        
        logger.info(f"Signed input for {context.field_name}")
        
        return ValidationResult(
            is_valid=True,
            value=value,
            context=context,
            signature=signature_str
        )
    
    def verify_input(self, value: Any, context: ValidationContext) -> ValidationResult:
        """
        Verify input data with cryptographic signatures
        
        Args:
            value: Input data to verify
            context: Validation context with signature
            
        Returns:
            Validation result
        """
        # Check if signature is provided
        if not context.signature:
            logger.warning(f"No signature provided for {context.field_name}")
            return ValidationResult(
                is_valid=False,
                value=None,
                error_message="No signature provided",
                context=context
            )
        
        # Parse signature
        try:
            signature = json.loads(context.signature)
        except json.JSONDecodeError:
            logger.error(f"Invalid signature format for {context.field_name}")
            return ValidationResult(
                is_valid=False,
                value=None,
                error_message="Invalid signature format",
                context=context
            )
        
        # Check timestamp
        timestamp = signature.get("timestamp")
        if not timestamp:
            logger.error(f"No timestamp in signature for {context.field_name}")
            return ValidationResult(
                is_valid=False,
                value=None,
                error_message="No timestamp in signature",
                context=context
            )
        
        # Check for expired signatures (1 hour max)
        current_time = int(time.time())
        if current_time - timestamp > 3600:
            logger.error(f"Expired signature for {context.field_name}")
            return ValidationResult(
                is_valid=False,
                value=None,
                error_message="Signature expired",
                context=context
            )
        
        # Convert value to string if needed
        if not isinstance(value, str):
            try:
                if isinstance(value, dict) or isinstance(value, list):
                    value_str = json.dumps(value, sort_keys=True)
                else:
                    value_str = str(value)
            except Exception as e:
                logger.error(f"Failed to convert value to string: {e}")
                return ValidationResult(
                    is_valid=False,
                    value=None,
                    error_message=f"Failed to convert value to string: {e}",
                    context=context
                )
        else:
            value_str = value
        
        # Create message to verify
        message = f"{context.field_name}:{value_str}:{timestamp}"
        
        # Verify HMAC signature
        hmac_signature = signature.get("hmac")
        if hmac_signature:
            hmac_valid = self._verify_hmac(message.encode(), hmac_signature)
            
            if not hmac_valid:
                logger.error(f"Invalid HMAC signature for {context.field_name}")
                return ValidationResult(
                    is_valid=False,
                    value=None,
                    error_message="Invalid HMAC signature",
                    context=context
                )
        else:
            logger.warning(f"No HMAC signature provided for {context.field_name}")
        
        # Verify Ed25519 signature if available
        ed25519_signature = signature.get("ed25519")
        public_key_hex = signature.get("public_key") or context.public_key
        
        if ed25519_signature and public_key_hex and NACL_AVAILABLE:
            try:
                # Convert signature and public key to bytes
                signature_bytes = bytes.fromhex(ed25519_signature)
                public_key_bytes = bytes.fromhex(public_key_hex)
                
                # Create verify key
                verify_key = nacl.signing.VerifyKey(public_key_bytes)
                
                # Verify signature
                try:
                    verify_key.verify(message.encode(), signature_bytes)
                    ed25519_valid = True
                except nacl.exceptions.BadSignatureError:
                    ed25519_valid = False
                
                if not ed25519_valid:
                    logger.error(f"Invalid Ed25519 signature for {context.field_name}")
                    return ValidationResult(
                        is_valid=False,
                        value=None,
                        error_message="Invalid Ed25519 signature",
                        context=context
                    )
                
                # Check if public key is trusted
                public_key_trusted = False
                for key_id, trusted_key in self.trusted_public_keys.items():
                    if trusted_key == public_key_bytes:
                        public_key_trusted = True
                        break
                
                if not public_key_trusted and self.trusted_public_keys:
                    logger.warning(f"Untrusted public key for {context.field_name}")
            except Exception as e:
                logger.error(f"Failed to verify Ed25519 signature: {e}")
                return ValidationResult(
                    is_valid=False,
                    value=None,
                    error_message=f"Failed to verify Ed25519 signature: {e}",
                    context=context
                )
        
        logger.info(f"Verified input for {context.field_name}")
        
        return ValidationResult(
            is_valid=True,
            value=value,
            context=context
        )
    
    def _sign_hmac(self, message: bytes) -> str:
        """
        Sign a message with HMAC-SHA256
        
        Args:
            message: Message to sign
            
        Returns:
            HMAC signature as hex string
        """
        h = hmac.new(self.secret_key.encode(), message, hashlib.sha256)
        return h.hexdigest()
    
    def _verify_hmac(self, message: bytes, signature: str) -> bool:
        """
        Verify an HMAC-SHA256 signature
        
        Args:
            message: Original message
            signature: HMAC signature as hex string
            
        Returns:
            True if signature is valid
        """
        h = hmac.new(self.secret_key.encode(), message, hashlib.sha256)
        expected_signature = h.hexdigest()
        return hmac.compare_digest(expected_signature, signature)
    
    def _sign_ed25519(self, message: bytes) -> bytes:
        """
        Sign a message with Ed25519
        
        Args:
            message: Message to sign
            
        Returns:
            Ed25519 signature
        """
        if not NACL_AVAILABLE or not self.ed25519_signer:
            raise ValueError("Ed25519 signing not available")
        
        return self.ed25519_signer.sign(message).signature
    
    def sign_ethereum_address(self, address: str) -> ValidationResult:
        """
        Sign an Ethereum address with cryptographic signatures
        
        Args:
            address: Ethereum address to sign
            
        Returns:
            Validation result with signature
        """
        # Validate address format
        if not Web3.is_address(address):
            return ValidationResult(
                is_valid=False,
                value=None,
                error_message="Invalid Ethereum address format",
                context=ValidationContext(field_name="ethereum_address")
            )
        
        # Convert to checksum address
        checksum_address = Web3.to_checksum_address(address)
        
        # Create context
        context = ValidationContext(
            field_name="ethereum_address",
            timestamp=int(time.time())
        )
        
        # Sign address
        return self.sign_input(checksum_address, context)
    
    def verify_ethereum_address(self, address: str, signature: str) -> ValidationResult:
        """
        Verify an Ethereum address with cryptographic signatures
        
        Args:
            address: Ethereum address to verify
            signature: Cryptographic signature
            
        Returns:
            Validation result
        """
        # Validate address format
        if not Web3.is_address(address):
            return ValidationResult(
                is_valid=False,
                value=None,
                error_message="Invalid Ethereum address format",
                context=ValidationContext(field_name="ethereum_address")
            )
        
        # Convert to checksum address
        checksum_address = Web3.to_checksum_address(address)
        
        # Create context
        context = ValidationContext(
            field_name="ethereum_address",
            signature=signature
        )
        
        # Verify address
        return self.verify_input(checksum_address, context)
    
    def sign_transaction_data(self, tx_data: Dict[str, Any]) -> ValidationResult:
        """
        Sign transaction data with cryptographic signatures
        
        Args:
            tx_data: Transaction data to sign
            
        Returns:
            Validation result with signature
        """
        # Validate basic transaction format
        if not isinstance(tx_data, dict):
            return ValidationResult(
                is_valid=False,
                value=None,
                error_message="Transaction data must be a dictionary",
                context=ValidationContext(field_name="transaction_data")
            )
        
        # Check required fields
        required_fields = {'to', 'value'}
        for field in required_fields:
            if field not in tx_data:
                return ValidationResult(
                    is_valid=False,
                    value=None,
                    error_message=f"Missing required field: {field}",
                    context=ValidationContext(field_name="transaction_data")
                )
        
        # Validate 'to' address
        if not Web3.is_address(tx_data['to']):
            return ValidationResult(
                is_valid=False,
                value=None,
                error_message="Invalid 'to' address",
                context=ValidationContext(field_name="transaction_data")
            )
        
        # Convert 'to' to checksum address
        tx_data['to'] = Web3.to_checksum_address(tx_data['to'])
        
        # Create context
        context = ValidationContext(
            field_name="transaction_data",
            timestamp=int(time.time())
        )
        
        # Sign transaction data
        return self.sign_input(tx_data, context)
    
    def verify_transaction_data(self, tx_data: Dict[str, Any], signature: str) -> ValidationResult:
        """
        Verify transaction data with cryptographic signatures
        
        Args:
            tx_data: Transaction data to verify
            signature: Cryptographic signature
            
        Returns:
            Validation result
        """
        # Validate basic transaction format
        if not isinstance(tx_data, dict):
            return ValidationResult(
                is_valid=False,
                value=None,
                error_message="Transaction data must be a dictionary",
                context=ValidationContext(field_name="transaction_data")
            )
        
        # Check required fields
        required_fields = {'to', 'value'}
        for field in required_fields:
            if field not in tx_data:
                return ValidationResult(
                    is_valid=False,
                    value=None,
                    error_message=f"Missing required field: {field}",
                    context=ValidationContext(field_name="transaction_data")
                )
        
        # Validate 'to' address
        if not Web3.is_address(tx_data['to']):
            return ValidationResult(
                is_valid=False,
                value=None,
                error_message="Invalid 'to' address",
                context=ValidationContext(field_name="transaction_data")
            )
        
        # Convert 'to' to checksum address
        tx_data['to'] = Web3.to_checksum_address(tx_data['to'])
        
        # Create context
        context = ValidationContext(
            field_name="transaction_data",
            signature=signature
        )
        
        # Verify transaction data
        return self.verify_input(tx_data, context)
    
    def sign_json_data(self, json_data: Any) -> ValidationResult:
        """
        Sign JSON data with cryptographic signatures
        
        Args:
            json_data: JSON data to sign
            
        Returns:
            Validation result with signature
        """
        # Validate JSON format
        if isinstance(json_data, str):
            try:
                json_data = json.loads(json_data)
            except json.JSONDecodeError as e:
                return ValidationResult(
                    is_valid=False,
                    value=None,
                    error_message=f"Invalid JSON format: {e}",
                    context=ValidationContext(field_name="json_data")
                )
        
        # Create context
        context = ValidationContext(
            field_name="json_data",
            timestamp=int(time.time())
        )
        
        # Sign JSON data
        return self.sign_input(json_data, context)
    
    def verify_json_data(self, json_data: Any, signature: str) -> ValidationResult:
        """
        Verify JSON data with cryptographic signatures
        
        Args:
            json_data: JSON data to verify
            signature: Cryptographic signature
            
        Returns:
            Validation result
        """
        # Validate JSON format
        if isinstance(json_data, str):
            try:
                json_data = json.loads(json_data)
            except json.JSONDecodeError as e:
                return ValidationResult(
                    is_valid=False,
                    value=None,
                    error_message=f"Invalid JSON format: {e}",
                    context=ValidationContext(field_name="json_data")
                )
        
        # Create context
        context = ValidationContext(
            field_name="json_data",
            signature=signature
        )
        
        # Verify JSON data
        return self.verify_input(json_data, context)


# Helper functions for common validations
def sign_ethereum_address(address: str) -> ValidationResult:
    """Sign an Ethereum address with cryptographic signatures"""
    validator = CryptographicInputValidator()
    return validator.sign_ethereum_address(address)


def verify_ethereum_address(address: str, signature: str) -> ValidationResult:
    """Verify an Ethereum address with cryptographic signatures"""
    validator = CryptographicInputValidator()
    return validator.verify_ethereum_address(address, signature)


def sign_transaction_data(tx_data: Dict[str, Any]) -> ValidationResult:
    """Sign transaction data with cryptographic signatures"""
    validator = CryptographicInputValidator()
    return validator.sign_transaction_data(tx_data)


def verify_transaction_data(tx_data: Dict[str, Any], signature: str) -> ValidationResult:
    """Verify transaction data with cryptographic signatures"""
    validator = CryptographicInputValidator()
    return validator.verify_transaction_data(tx_data, signature)


def sign_json_data(json_data: Any) -> ValidationResult:
    """Sign JSON data with cryptographic signatures"""
    validator = CryptographicInputValidator()
    return validator.sign_json_data(json_data)


def verify_json_data(json_data: Any, signature: str) -> ValidationResult:
    """Verify JSON data with cryptographic signatures"""
    validator = CryptographicInputValidator()
    return validator.verify_json_data(json_data, signature)


# Example usage
if __name__ == "__main__":
    # Initialize cryptographic validator
    validator = CryptographicInputValidator()
    
    # Sign an Ethereum address
    address = "${CONTRACT_ADDRESS}"
    address_result = validator.sign_ethereum_address(address)
    print(f"Address signature: {address_result.signature}")
    
    # Verify the address
    verify_result = validator.verify_ethereum_address(address, address_result.signature)
    print(f"Address verification: {verify_result.is_valid}")
    
    # Sign transaction data
    tx_data = {
        "to": "${CONTRACT_ADDRESS}",
        "value": "1000000000000000000",
        "gas": 21000,
        "gasPrice": "5000000000",
        "nonce": 0,
        "data": "0x"
    }
    tx_result = validator.sign_transaction_data(tx_data)
    print(f"Transaction signature: {tx_result.signature}")
    
    # Verify the transaction data
    tx_verify_result = validator.verify_transaction_data(tx_data, tx_result.signature)
    print(f"Transaction verification: {tx_verify_result.is_valid}")