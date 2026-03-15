#!/usr/bin/env python3
# =================================================================================================
# ENHANCED ORACLE SECURITY MODULE
# =================================================================================================

import os
import json
import time
import hashlib
import logging
import base64
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from web3 import Web3
from dotenv import load_dotenv

# Try to import MATLAB Engine for Python
try:
    import matlab.engine
    MATLAB_AVAILABLE = True
except ImportError:
    MATLAB_AVAILABLE = False
    logging.warning("MATLAB Engine for Python not available. Advanced analytics will be disabled.")

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

try:
    from py_ecc.bls import G2ProofOfPossession as bls_pop
    BLS_AVAILABLE = True
except ImportError:
    BLS_AVAILABLE = False
    logging.warning("py_ecc not available. BLS signatures will be disabled.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("oracle_security.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("enhanced_oracle_security")

@dataclass
class OracleSignature:
    """Oracle signature data"""
    signature: bytes
    public_key: bytes
    timestamp: int
    algorithm: str


@dataclass
class PriceFeed:
    """Price feed data with cryptographic proofs"""
    asset: str
    price: float
    timestamp: int
    signatures: List[OracleSignature]
    merkle_proof: Optional[List[bytes]] = None
    bls_signature: Optional[bytes] = None


class MerkleTree:
    """Merkle tree implementation for price history proofs"""
    
    def __init__(self, leaves: List[bytes] = None):
        """
        Initialize Merkle tree
        
        Args:
            leaves: List of leaf node data (bytes)
        """
        self.leaves = leaves or []
        self.layers = []
        
        if leaves:
            self._build_tree()
    
    def _build_tree(self):
        """Build the Merkle tree from leaves"""
        self.layers = [self.leaves]
        
        # Build tree layers
        while len(self.layers[-1]) > 1:
            layer = self.layers[-1]
            next_layer = []
            
            # Process pairs of nodes
            for i in range(0, len(layer), 2):
                if i + 1 < len(layer):
                    # Hash pair of nodes
                    combined = layer[i] + layer[i + 1]
                    next_layer.append(hashlib.sha256(combined).digest())
                else:
                    # Odd number of nodes, duplicate the last one
                    next_layer.append(layer[i])
            
            self.layers.append(next_layer)
    
    def get_root(self) -> bytes:
        """Get the Merkle root hash"""
        if not self.layers:
            return hashlib.sha256(b"").digest()
        
        return self.layers[-1][0]
    
    def get_proof(self, index: int) -> List[bytes]:
        """
        Get the Merkle proof for a leaf node
        
        Args:
            index: Index of the leaf node
            
        Returns:
            List of proof hashes
        """
        if index >= len(self.leaves):
            raise ValueError(f"Index {index} out of range")
        
        proof = []
        
        for layer_idx, layer in enumerate(self.layers[:-1]):
            is_right = index % 2 == 0
            pair_idx = index + 1 if is_right else index - 1
            
            if pair_idx < len(layer):
                proof.append(layer[pair_idx])
            
            # Update index for next layer
            index = index // 2
        
        return proof
    
    def verify_proof(self, leaf: bytes, proof: List[bytes], root: bytes) -> bool:
        """
        Verify a Merkle proof
        
        Args:
            leaf: Leaf node data
            proof: Merkle proof
            root: Expected Merkle root
            
        Returns:
            True if proof is valid
        """
        current = leaf
        
        for proof_item in proof:
            if int.from_bytes(current, byteorder='big') < int.from_bytes(proof_item, byteorder='big'):
                current = hashlib.sha256(current + proof_item).digest()
            else:
                current = hashlib.sha256(proof_item + current).digest()
        
        return current == root


class Ed25519Signer:
    """Ed25519 signature implementation for oracle data"""
    
    def __init__(self, private_key: bytes = None):
        """
        Initialize Ed25519 signer
        
        Args:
            private_key: Ed25519 private key (generates a new one if None)
        """
        if not NACL_AVAILABLE:
            raise ImportError("PyNaCl library is required for Ed25519 signatures")
        
        if private_key:
            self.signing_key = nacl.signing.SigningKey(private_key)
        else:
            self.signing_key = nacl.signing.SigningKey.generate()
        
        self.verify_key = self.signing_key.verify_key
    
    def sign(self, message: bytes) -> bytes:
        """
        Sign a message with Ed25519
        
        Args:
            message: Message to sign
            
        Returns:
            Ed25519 signature
        """
        return self.signing_key.sign(message).signature
    
    def get_public_key(self) -> bytes:
        """Get the public key"""
        return bytes(self.verify_key)
    
    @staticmethod
    def verify(message: bytes, signature: bytes, public_key: bytes) -> bool:
        """
        Verify an Ed25519 signature
        
        Args:
            message: Original message
            signature: Ed25519 signature
            public_key: Ed25519 public key
            
        Returns:
            True if signature is valid
        """
        verify_key = nacl.signing.VerifyKey(public_key)
        
        try:
            verify_key.verify(message, signature)
            return True
        except nacl.exceptions.BadSignatureError:
            return False


class BLSThresholdSigner:
    """BLS threshold signature implementation for oracle consensus"""
    
    def __init__(self, private_key: int = None):
        """
        Initialize BLS signer
        
        Args:
            private_key: BLS private key (generates a new one if None)
        """
        if not BLS_AVAILABLE:
            raise ImportError("py_ecc library is required for BLS signatures")
        
        if private_key:
            self.private_key = private_key
        else:
            # Generate random private key
            import secrets
            self.private_key = secrets.randbelow(bls_pop.curve_order)
        
        # Derive public key
        self.public_key = bls_pop.SkToPk(self.private_key)
    
    def sign(self, message: bytes) -> bytes:
        """
        Sign a message with BLS
        
        Args:
            message: Message to sign
            
        Returns:
            BLS signature
        """
        return bls_pop.Sign(self.private_key, message)
    
    def get_public_key(self) -> bytes:
        """Get the public key"""
        return self.public_key
    
    @staticmethod
    def verify(message: bytes, signature: bytes, public_key: bytes) -> bool:
        """
        Verify a BLS signature
        
        Args:
            message: Original message
            signature: BLS signature
            public_key: BLS public key
            
        Returns:
            True if signature is valid
        """
        return bls_pop.Verify(public_key, message, signature)
    
    @staticmethod
    def aggregate_signatures(signatures: List[bytes]) -> bytes:
        """
        Aggregate multiple BLS signatures
        
        Args:
            signatures: List of BLS signatures
            
        Returns:
            Aggregated BLS signature
        """
        return bls_pop.Aggregate(signatures)
    
    @staticmethod
    def verify_aggregate(message: bytes, signature: bytes, public_keys: List[bytes]) -> bool:
        """
        Verify an aggregated BLS signature
        
        Args:
            message: Original message
            signature: Aggregated BLS signature
            public_keys: List of BLS public keys
            
        Returns:
            True if signature is valid
        """
        return bls_pop.FastAggregateVerify(public_keys, message, signature)


class MATLABAnalytics:
    """MATLAB integration for advanced analytics"""
    
    def __init__(self):
        """Initialize MATLAB Engine"""
        if not MATLAB_AVAILABLE:
            raise ImportError("MATLAB Engine for Python is required for advanced analytics")
        
        self.eng = matlab.engine.start_matlab()
        logger.info("MATLAB Engine started")
    
    def detect_anomalies(self, prices: List[float], timestamps: List[int]) -> List[int]:
        """
        Detect anomalies in price data using MATLAB
        
        Args:
            prices: List of price values
            timestamps: List of timestamps
            
        Returns:
            List of indices of anomalous prices
        """
        # Convert to MATLAB arrays
        m_prices = matlab.double(prices)
        m_timestamps = matlab.double(timestamps)
        
        # Run MATLAB anomaly detection
        result = self.eng.detectAnomalies(m_prices, m_timestamps, nargout=1)
        
        # Convert result to Python list
        return [int(idx) for idx in result]
    
    def correlation_analysis(self, asset_prices: Dict[str, List[float]]) -> Dict[str, Dict[str, float]]:
        """
        Perform correlation analysis on multiple asset prices
        
        Args:
            asset_prices: Dictionary of asset names to price lists
            
        Returns:
            Dictionary of correlation coefficients
        """
        # Convert to MATLAB structure
        assets = list(asset_prices.keys())
        m_prices = {}
        
        for asset, prices in asset_prices.items():
            m_prices[asset] = matlab.double(prices)
        
        # Run MATLAB correlation analysis
        result = self.eng.correlationAnalysis(m_prices, nargout=1)
        
        # Convert result to Python dictionary
        correlations = {}
        
        for i, asset1 in enumerate(assets):
            correlations[asset1] = {}
            
            for j, asset2 in enumerate(assets):
                correlations[asset1][asset2] = float(result[i][j])
        
        return correlations
    
    def close(self):
        """Close MATLAB Engine"""
        if hasattr(self, 'eng'):
            self.eng.quit()
            logger.info("MATLAB Engine closed")


class EnhancedOracleSecurity:
    """Enhanced Oracle Security with cryptographic proofs and consensus"""
    
    def __init__(self, config_path: str = None):
        """
        Initialize Enhanced Oracle Security
        
        Args:
            config_path: Path to configuration file
        """
        # Load environment variables
        load_dotenv()
        
        self.config_path = config_path or os.getenv("ORACLE_SECURITY_CONFIG", "oracle_security_config.json")
        self.config = self._load_config()
        
        # Initialize signers
        self.ed25519_signer = Ed25519Signer() if NACL_AVAILABLE else None
        self.bls_signer = BLSThresholdSigner() if BLS_AVAILABLE else None
        
        # Initialize MATLAB analytics if available
        self.matlab = None
        if MATLAB_AVAILABLE and self.config.get("use_matlab", False):
            try:
                self.matlab = MATLABAnalytics()
                logger.info("MATLAB analytics initialized")
            except Exception as e:
                logger.error(f"Failed to initialize MATLAB analytics: {e}")
        
        # Initialize price history for Merkle proofs
        self.price_history = {}
        
        # Initialize oracle registry
        self.oracle_registry = self._load_oracle_registry()
        
        logger.info("Enhanced Oracle Security initialized")
    
    def _load_config(self) -> Dict:
        """
        Load configuration from file
        
        Returns:
            Configuration dictionary
        """
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            logger.info(f"Loaded configuration from {self.config_path}")
            return config
        except Exception as e:
            logger.warning(f"Failed to load configuration: {e}, using defaults")
            return {
                "required_consensus": 3,
                "total_oracles": 5,
                "use_merkle_proofs": True,
                "use_bls_signatures": True,
                "use_matlab": False,
                "anomaly_threshold": 0.05,
                "price_history_length": 100
            }
    
    def _load_oracle_registry(self) -> Dict[str, Dict]:
        """
        Load oracle registry from configuration
        
        Returns:
            Dictionary of oracle information
        """
        registry = {}
        
        for oracle in self.config.get("oracles", []):
            oracle_id = oracle.get("id")
            
            if oracle_id:
                registry[oracle_id] = {
                    "name": oracle.get("name", f"Oracle {oracle_id}"),
                    "public_key_ed25519": bytes.fromhex(oracle.get("public_key_ed25519", "")),
                    "public_key_bls": bytes.fromhex(oracle.get("public_key_bls", "")),
                    "weight": oracle.get("weight", 1)
                }
        
        logger.info(f"Loaded {len(registry)} oracles from registry")
        return registry
    
    def sign_price_feed(self, asset: str, price: float) -> PriceFeed:
        """
        Sign a price feed with cryptographic proofs
        
        Args:
            asset: Asset symbol
            price: Asset price
            
        Returns:
            Signed price feed with proofs
        """
        timestamp = int(time.time())
        
        # Create message
        message = f"{asset}:{price}:{timestamp}".encode()
        
        # Sign with Ed25519
        ed25519_signature = None
        if self.ed25519_signer:
            ed25519_signature = self.ed25519_signer.sign(message)
            logger.info(f"Signed {asset} price feed with Ed25519")
        
        # Create oracle signature
        signatures = []
        if ed25519_signature:
            signatures.append(OracleSignature(
                signature=ed25519_signature,
                public_key=self.ed25519_signer.get_public_key(),
                timestamp=timestamp,
                algorithm="ed25519"
            ))
        
        # Generate Merkle proof if enabled
        merkle_proof = None
        if self.config.get("use_merkle_proofs", True):
            merkle_proof = self._generate_merkle_proof(asset, price, timestamp)
        
        # Generate BLS signature if enabled
        bls_signature = None
        if self.config.get("use_bls_signatures", True) and self.bls_signer:
            bls_signature = self.bls_signer.sign(message)
            logger.info(f"Generated BLS signature for {asset} price feed")
        
        # Create price feed
        price_feed = PriceFeed(
            asset=asset,
            price=price,
            timestamp=timestamp,
            signatures=signatures,
            merkle_proof=merkle_proof,
            bls_signature=bls_signature
        )
        
        # Update price history
        self._update_price_history(asset, price, timestamp)
        
        return price_feed
    
    def _generate_merkle_proof(self, asset: str, price: float, timestamp: int) -> List[bytes]:
        """
        Generate Merkle proof for a price feed
        
        Args:
            asset: Asset symbol
            price: Asset price
            timestamp: Timestamp
            
        Returns:
            Merkle proof
        """
        # Get price history for the asset
        history = self.price_history.get(asset, [])
        
        if not history:
            logger.warning(f"No price history for {asset}, cannot generate Merkle proof")
            return []
        
        # Create leaf nodes
        leaves = []
        for hist_price, hist_timestamp in history:
            leaf_data = f"{asset}:{hist_price}:{hist_timestamp}".encode()
            leaves.append(hashlib.sha256(leaf_data).digest())
        
        # Add current price
        current_leaf = f"{asset}:{price}:{timestamp}".encode()
        leaves.append(hashlib.sha256(current_leaf).digest())
        
        # Build Merkle tree
        merkle_tree = MerkleTree(leaves)
        
        # Get proof for the current price (last leaf)
        proof = merkle_tree.get_proof(len(leaves) - 1)
        
        logger.info(f"Generated Merkle proof for {asset} with {len(proof)} elements")
        return proof
    
    def _update_price_history(self, asset: str, price: float, timestamp: int):
        """
        Update price history for an asset
        
        Args:
            asset: Asset symbol
            price: Asset price
            timestamp: Timestamp
        """
        # Initialize history if needed
        if asset not in self.price_history:
            self.price_history[asset] = []
        
        # Add price to history
        self.price_history[asset].append((price, timestamp))
        
        # Limit history length
        max_length = self.config.get("price_history_length", 100)
        if len(self.price_history[asset]) > max_length:
            self.price_history[asset] = self.price_history[asset][-max_length:]
    
    def verify_price_feed(self, price_feed: PriceFeed) -> bool:
        """
        Verify a price feed with all available cryptographic proofs
        
        Args:
            price_feed: Price feed to verify
            
        Returns:
            True if price feed is valid
        """
        # Create message
        message = f"{price_feed.asset}:{price_feed.price}:{price_feed.timestamp}".encode()
        
        # Verify Ed25519 signatures
        valid_signatures = 0
        required_consensus = self.config.get("required_consensus", 3)
        
        for sig in price_feed.signatures:
            if sig.algorithm == "ed25519" and NACL_AVAILABLE:
                if Ed25519Signer.verify(message, sig.signature, sig.public_key):
                    # Check if the oracle is in our registry
                    for oracle_id, oracle_info in self.oracle_registry.items():
                        if oracle_info["public_key_ed25519"] == sig.public_key:
                            valid_signatures += oracle_info["weight"]
                            break
        
        # Verify BLS signature if available
        if price_feed.bls_signature and BLS_AVAILABLE:
            # Collect public keys from registry
            public_keys = [
                oracle_info["public_key_bls"]
                for oracle_id, oracle_info in self.oracle_registry.items()
                if oracle_info["public_key_bls"]
            ]
            
            if BLSThresholdSigner.verify_aggregate(message, price_feed.bls_signature, public_keys):
                logger.info(f"BLS aggregate signature verified for {price_feed.asset}")
                valid_signatures = required_consensus  # BLS threshold signature implies consensus
        
        # Verify Merkle proof if available
        merkle_valid = False
        if price_feed.merkle_proof:
            # Get price history for the asset
            history = self.price_history.get(price_feed.asset, [])
            
            if history:
                # Create leaf nodes
                leaves = []
                for hist_price, hist_timestamp in history:
                    leaf_data = f"{price_feed.asset}:{hist_price}:{hist_timestamp}".encode()
                    leaves.append(hashlib.sha256(leaf_data).digest())
                
                # Build Merkle tree
                merkle_tree = MerkleTree(leaves)
                
                # Get Merkle root
                root = merkle_tree.get_root()
                
                # Create leaf for the current price
                current_leaf = hashlib.sha256(message).digest()
                
                # Verify proof
                merkle_valid = merkle_tree.verify_proof(current_leaf, price_feed.merkle_proof, root)
                
                if merkle_valid:
                    logger.info(f"Merkle proof verified for {price_feed.asset}")
        
        # Check if we have enough valid signatures
        consensus_reached = valid_signatures >= required_consensus
        
        # Perform anomaly detection if MATLAB is available
        anomaly_detected = False
        if self.matlab and self.config.get("use_matlab", False):
            try:
                # Get price history for the asset
                history = self.price_history.get(price_feed.asset, [])
                
                if history:
                    prices = [p for p, _ in history]
                    timestamps = [t for _, t in history]
                    
                    # Add current price
                    prices.append(price_feed.price)
                    timestamps.append(price_feed.timestamp)
                    
                    # Detect anomalies
                    anomalies = self.matlab.detect_anomalies(prices, timestamps)
                    
                    # Check if the current price is anomalous
                    if len(prices) - 1 in anomalies:
                        logger.warning(f"Anomaly detected in {price_feed.asset} price feed")
                        anomaly_detected = True
            except Exception as e:
                logger.error(f"Failed to perform anomaly detection: {e}")
        
        # Price feed is valid if consensus is reached, no anomalies detected, and Merkle proof is valid (if provided)
        is_valid = consensus_reached and not anomaly_detected
        if price_feed.merkle_proof:
            is_valid = is_valid and merkle_valid
        
        logger.info(f"Price feed verification result for {price_feed.asset}: {is_valid}")
        return is_valid
    
    def perform_multi_oracle_consensus(self, price_feeds: List[PriceFeed]) -> Optional[PriceFeed]:
        """
        Perform consensus among multiple oracle price feeds
        
        Args:
            price_feeds: List of price feeds from different oracles
            
        Returns:
            Consensus price feed or None if consensus not reached
        """
        if not price_feeds:
            logger.warning("No price feeds provided for consensus")
            return None
        
        # Group price feeds by asset
        feeds_by_asset = {}
        for feed in price_feeds:
            if feed.asset not in feeds_by_asset:
                feeds_by_asset[feed.asset] = []
            feeds_by_asset[feed.asset].append(feed)
        
        # Process each asset
        consensus_feeds = []
        
        for asset, feeds in feeds_by_asset.items():
            # Skip if we don't have enough feeds
            required_consensus = self.config.get("required_consensus", 3)
            if len(feeds) < required_consensus:
                logger.warning(f"Not enough price feeds for {asset} consensus: {len(feeds)}/{required_consensus}")
                continue
            
            # Verify each feed
            valid_feeds = [feed for feed in feeds if self.verify_price_feed(feed)]
            
            if len(valid_feeds) < required_consensus:
                logger.warning(f"Not enough valid price feeds for {asset} consensus: {len(valid_feeds)}/{required_consensus}")
                continue
            
            # Calculate weighted average price
            total_weight = 0
            weighted_price = 0
            
            for feed in valid_feeds:
                # Find oracle weight
                weight = 1  # Default weight
                
                for sig in feed.signatures:
                    for oracle_id, oracle_info in self.oracle_registry.items():
                        if oracle_info["public_key_ed25519"] == sig.public_key:
                            weight = oracle_info["weight"]
                            break
                
                weighted_price += feed.price * weight
                total_weight += weight
            
            if total_weight > 0:
                consensus_price = weighted_price / total_weight
                
                # Create consensus feed
                consensus_feed = PriceFeed(
                    asset=asset,
                    price=consensus_price,
                    timestamp=int(time.time()),
                    signatures=[],  # No signatures for consensus feed
                    merkle_proof=None,
                    bls_signature=None
                )
                
                consensus_feeds.append(consensus_feed)
                logger.info(f"Consensus reached for {asset}: {consensus_price}")
            else:
                logger.warning(f"Failed to calculate weighted average for {asset}")
        
        # Return the first consensus feed or None
        return consensus_feeds[0] if consensus_feeds else None
    
    def close(self):
        """Close resources"""
        if self.matlab:
            self.matlab.close()
            logger.info("MATLAB analytics closed")


# Example usage
if __name__ == "__main__":
    # Initialize Enhanced Oracle Security
    oracle_security = EnhancedOracleSecurity()
    
    # Sign a price feed
    price_feed = oracle_security.sign_price_feed("ETH-USD", 2500.0)
    
    # Verify the price feed
    is_valid = oracle_security.verify_price_feed(price_feed)
    
    print(f"Price feed valid: {is_valid}")
    
    # Clean up
    oracle_security.close()