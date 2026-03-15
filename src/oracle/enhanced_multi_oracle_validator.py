#!/usr/bin/env python3
"""
Enhanced Multi-Oracle Validator
==============================

Implements robust multi-oracle signature consensus system for cross-chain
bridge operations with advanced validation and Byzantine fault tolerance.
"""

import asyncio
import json
import logging
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
from web3 import Web3
from eth_account import Account
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OracleStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    COMPROMISED = "compromised"

class SignatureValidation(Enum):
    VALID = "valid"
    INVALID = "invalid"
    EXPIRED = "expired"
    REPLAYED = "replayed"
    UNAUTHORIZED = "unauthorized"

@dataclass
class OracleNode:
    """Enhanced oracle node configuration"""
    address: str
    public_key: str
    endpoint: str
    reputation_score: float
    status: OracleStatus
    last_seen: datetime
    signatures_submitted: int
    signatures_verified: int
    response_time_avg: float
    geographic_region: str
    stake_amount: int
    slashing_count: int

@dataclass
class SignatureAttestation:
    """Enhanced signature attestation with metadata"""
    oracle_address: str
    signature: str
    message_hash: str
    state_root: str
    block_height: int
    timestamp: datetime
    nonce: int
    confidence_score: float
    validation_status: SignatureValidation
    attestation_data: Dict[str, Any]

@dataclass
class ConsensusRound:
    """Consensus round tracking"""
    round_id: str
    operation_id: str
    start_time: datetime
    deadline: datetime
    target_signatures: int
    collected_signatures: List[SignatureAttestation]
    consensus_achieved: bool
    final_state_root: Optional[str]
    participant_oracles: Set[str]

class EnhancedMultiOracleValidator:
    """
    Enhanced multi-oracle validator with Byzantine fault tolerance
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.oracle_nodes: Dict[str, OracleNode] = {}
        self.active_consensus_rounds: Dict[str, ConsensusRound] = {}
        self.signature_history: Dict[str, List[SignatureAttestation]] = {}
        self.nonce_tracking: Dict[str, int] = {}
        
        # Consensus parameters
        self.min_signatures = config.get('min_signatures', 3)
        self.max_signatures = config.get('max_signatures', 7)
        self.consensus_threshold = config.get('consensus_threshold', 0.67)
        self.byzantine_tolerance = config.get('byzantine_tolerance', 1)  # f in 3f+1
        self.signature_timeout = config.get('signature_timeout', 300)
        self.reputation_threshold = config.get('reputation_threshold', 0.8)
        
        # Security parameters
        self.max_signature_age = config.get('max_signature_age', 600)
        self.replay_window = config.get('replay_window', 3600)
        self.slashing_threshold = config.get('slashing_threshold', 3)
        
        # Initialize oracle nodes
        self._initialize_oracle_nodes()
        
        # Start background tasks
        asyncio.create_task(self._monitor_oracle_health())
        asyncio.create_task(self._cleanup_expired_rounds())
    
    def _initialize_oracle_nodes(self):
        """Initialize oracle node configurations"""
        oracle_configs = self.config.get('oracles', {})
        
        for oracle_id, oracle_config in oracle_configs.items():
            node = OracleNode(
                address=oracle_config['address'],
                public_key=oracle_config['public_key'],
                endpoint=oracle_config['endpoint'],
                reputation_score=oracle_config.get('reputation_score', 1.0),
                status=OracleStatus.ACTIVE,
                last_seen=datetime.now(),
                signatures_submitted=0,
                signatures_verified=0,
                response_time_avg=0.0,
                geographic_region=oracle_config.get('region', 'unknown'),
                stake_amount=oracle_config.get('stake_amount', 0),
                slashing_count=0
            )
            
            self.oracle_nodes[node.address] = node
            self.nonce_tracking[node.address] = 0
        
        logger.info(f"Initialized {len(self.oracle_nodes)} oracle nodes")
    
    async def initiate_consensus_round(
        self,
        operation_id: str,
        message_data: Dict[str, Any],
        timeout_seconds: int = 300
    ) -> str:
        """
        Initiate a new consensus round for multi-oracle validation
        
        Returns:
            round_id: Unique identifier for the consensus round
        """
        round_id = hashlib.sha256(
            f"{operation_id}{time.time()}".encode()
        ).hexdigest()[:16]
        
        # Select participating oracles based on reputation and availability
        participating_oracles = self._select_participating_oracles()
        
        # Create consensus round
        consensus_round = ConsensusRound(
            round_id=round_id,
            operation_id=operation_id,
            start_time=datetime.now(),
            deadline=datetime.now() + timedelta(seconds=timeout_seconds),
            target_signatures=max(self.min_signatures, len(participating_oracles) * 2 // 3),
            collected_signatures=[],
            consensus_achieved=False,
            final_state_root=None,
            participant_oracles=participating_oracles
        )
        
        self.active_consensus_rounds[round_id] = consensus_round
        
        # Request signatures from participating oracles
        await self._request_signatures_from_oracles(
            round_id,
            message_data,
            participating_oracles
        )
        
        logger.info(f"Initiated consensus round {round_id} for operation {operation_id} "
                   f"with {len(participating_oracles)} oracles")
        
        return round_id
    
    def _select_participating_oracles(self) -> Set[str]:
        """
        Select oracles for consensus round based on reputation and availability
        """
        available_oracles = [
            (address, node) for address, node in self.oracle_nodes.items()
            if (node.status == OracleStatus.ACTIVE and
                node.reputation_score >= self.reputation_threshold and
                node.slashing_count < self.slashing_threshold)
        ]
        
        # Sort by reputation score and response time
        available_oracles.sort(
            key=lambda x: (x[1].reputation_score, -x[1].response_time_avg),
            reverse=True
        )
        
        # Select top oracles up to max_signatures
        selected_count = min(len(available_oracles), self.max_signatures)
        selected_oracles = {
            oracle[0] for oracle in available_oracles[:selected_count]
        }
        
        # Ensure minimum required oracles
        if len(selected_oracles) < self.min_signatures:
            raise ValueError(f"Insufficient oracles available: {len(selected_oracles)} < {self.min_signatures}")
        
        logger.info(f"Selected {len(selected_oracles)} oracles for consensus")
        return selected_oracles
    
    async def _request_signatures_from_oracles(
        self,
        round_id: str,
        message_data: Dict[str, Any],
        oracle_addresses: Set[str]
    ):
        """Request signatures from selected oracles"""
        signature_tasks = []
        
        for oracle_address in oracle_addresses:
            task = asyncio.create_task(
                self._request_oracle_signature(round_id, oracle_address, message_data)
            )
            signature_tasks.append(task)
        
        # Execute requests concurrently
        await asyncio.gather(*signature_tasks, return_exceptions=True)
    
    async def _request_oracle_signature(
        self,
        round_id: str,
        oracle_address: str,
        message_data: Dict[str, Any]
    ):
        """Request signature from a specific oracle"""
        oracle_node = self.oracle_nodes.get(oracle_address)
        if not oracle_node:
            logger.warning(f"Oracle node not found: {oracle_address}")
            return
        
        try:
            start_time = time.time()
            
            # Prepare signature request
            request_data = {
                'round_id': round_id,
                'message_data': message_data,
                'nonce': self.nonce_tracking[oracle_address] + 1,
                'timestamp': datetime.now().isoformat(),
                'required_confidence': 0.9
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{oracle_node.endpoint}/request_signature",
                    json=request_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        signature_data = await response.json()
                        
                        # Create signature attestation
                        attestation = SignatureAttestation(
                            oracle_address=oracle_address,
                            signature=signature_data['signature'],
                            message_hash=signature_data['message_hash'],
                            state_root=signature_data['state_root'],
                            block_height=signature_data['block_height'],
                            timestamp=datetime.fromisoformat(signature_data['timestamp']),
                            nonce=signature_data['nonce'],
                            confidence_score=signature_data.get('confidence_score', 1.0),
                            validation_status=SignatureValidation.VALID,
                            attestation_data=signature_data.get('attestation_data', {})
                        )
                        
                        # Validate signature
                        if await self._validate_signature_attestation(attestation, message_data):
                            await self._process_valid_signature(round_id, attestation)
                            
                            # Update oracle metrics
                            oracle_node.signatures_submitted += 1
                            oracle_node.signatures_verified += 1
                            oracle_node.response_time_avg = (
                                (oracle_node.response_time_avg * (oracle_node.signatures_submitted - 1) + response_time) /
                                oracle_node.signatures_submitted
                            )
                            oracle_node.last_seen = datetime.now()
                            
                            # Update nonce
                            self.nonce_tracking[oracle_address] = attestation.nonce
                            
                        else:
                            logger.warning(f"Invalid signature from oracle {oracle_address}")
                            await self._handle_invalid_signature(oracle_address, attestation)
                    
                    else:
                        logger.warning(f"Oracle {oracle_address} returned status {response.status}")
                        await self._handle_oracle_error(oracle_address, f"HTTP {response.status}")
                        
        except asyncio.TimeoutError:
            logger.warning(f"Timeout requesting signature from oracle {oracle_address}")
            await self._handle_oracle_error(oracle_address, "Request timeout")
            
        except Exception as e:
            logger.error(f"Error requesting signature from oracle {oracle_address}: {str(e)}")
            await self._handle_oracle_error(oracle_address, str(e))
    
    async def _validate_signature_attestation(
        self,
        attestation: SignatureAttestation,
        original_message: Dict[str, Any]
    ) -> bool:
        """
        Comprehensive validation of signature attestation
        """
        try:
            oracle_node = self.oracle_nodes.get(attestation.oracle_address)
            if not oracle_node:
                logger.warning(f"Unknown oracle: {attestation.oracle_address}")
                return False
            
            # Check oracle status
            if oracle_node.status != OracleStatus.ACTIVE:
                logger.warning(f"Oracle not active: {attestation.oracle_address}")
                return False
            
            # Check signature age
            signature_age = (datetime.now() - attestation.timestamp).total_seconds()
            if signature_age > self.max_signature_age:
                logger.warning(f"Signature too old: {signature_age}s")
                attestation.validation_status = SignatureValidation.EXPIRED
                return False
            
            # Check for replay attacks
            if await self._check_replay_attack(attestation):
                logger.warning(f"Replay attack detected from {attestation.oracle_address}")
                attestation.validation_status = SignatureValidation.REPLAYED
                return False
            
            # Validate nonce sequence
            expected_nonce = self.nonce_tracking[attestation.oracle_address] + 1
            if attestation.nonce != expected_nonce:
                logger.warning(f"Invalid nonce from {attestation.oracle_address}: "
                              f"expected {expected_nonce}, got {attestation.nonce}")
                return False
            
            # Cryptographic signature verification
            if not await self._verify_cryptographic_signature(attestation, original_message):
                logger.warning(f"Cryptographic verification failed for {attestation.oracle_address}")
                attestation.validation_status = SignatureValidation.INVALID
                return False
            
            # Validate state root consistency
            if not await self._validate_state_root(attestation):
                logger.warning(f"State root validation failed for {attestation.oracle_address}")
                return False
            
            # Check confidence score
            if attestation.confidence_score < 0.8:
                logger.warning(f"Low confidence score from {attestation.oracle_address}: "
                              f"{attestation.confidence_score}")
                return False
            
            attestation.validation_status = SignatureValidation.VALID
            return True
            
        except Exception as e:
            logger.error(f"Error validating signature attestation: {str(e)}")
            attestation.validation_status = SignatureValidation.INVALID
            return False
    
    async def _check_replay_attack(self, attestation: SignatureAttestation) -> bool:
        """Check for replay attacks by examining signature history"""
        oracle_history = self.signature_history.get(attestation.oracle_address, [])
        
        # Check recent signatures
        cutoff_time = datetime.now() - timedelta(seconds=self.replay_window)
        recent_signatures = [
            sig for sig in oracle_history 
            if sig.timestamp > cutoff_time
        ]
        
        # Look for duplicate signatures
        for historical_sig in recent_signatures:
            if (historical_sig.signature == attestation.signature or
                historical_sig.message_hash == attestation.message_hash):
                return True
        
        return False
    
    async def _verify_cryptographic_signature(
        self,
        attestation: SignatureAttestation,
        original_message: Dict[str, Any]
    ) -> bool:
        """
        Verify cryptographic signature using oracle's public key
        """
        try:
            oracle_node = self.oracle_nodes[attestation.oracle_address]
            
            # Reconstruct message hash
            message_components = [
                str(original_message.get('operation_id', '')),
                str(original_message.get('source_chain_id', '')),
                str(original_message.get('target_chain_id', '')),
                str(original_message.get('payload_hash', '')),
                str(attestation.nonce)
            ]
            
            reconstructed_hash = hashlib.sha256(
                ''.join(message_components).encode()
            ).hexdigest()
            
            # Verify hash matches
            if reconstructed_hash != attestation.message_hash:
                logger.warning(f"Message hash mismatch for {attestation.oracle_address}")
                return False
            
            # In production, this would perform actual cryptographic verification
            # using the oracle's public key. For this implementation, we'll simulate it.
            
            # Simulate signature verification
            await asyncio.sleep(0.01)  # Simulate crypto computation
            
            # Check signature format
            if len(attestation.signature) < 128:  # Minimum signature length
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error in cryptographic verification: {str(e)}")
            return False
    
    async def _validate_state_root(self, attestation: SignatureAttestation) -> bool:
        """Validate the provided state root against known chain state"""
        try:
            # In production, this would verify the state root against
            # the actual blockchain state. For simulation, we'll do basic checks.
            
            # Check state root format
            if not attestation.state_root or len(attestation.state_root) != 66:
                return False
            
            # Check block height consistency
            if attestation.block_height <= 0:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating state root: {str(e)}")
            return False
    
    async def _process_valid_signature(
        self,
        round_id: str,
        attestation: SignatureAttestation
    ):
        """Process a valid signature and check for consensus"""
        consensus_round = self.active_consensus_rounds.get(round_id)
        if not consensus_round:
            logger.warning(f"Consensus round not found: {round_id}")
            return
        
        # Add signature to round
        consensus_round.collected_signatures.append(attestation)
        
        # Add to signature history
        oracle_address = attestation.oracle_address
        if oracle_address not in self.signature_history:
            self.signature_history[oracle_address] = []
        self.signature_history[oracle_address].append(attestation)
        
        # Keep only recent history
        cutoff_time = datetime.now() - timedelta(seconds=self.replay_window * 2)
        self.signature_history[oracle_address] = [
            sig for sig in self.signature_history[oracle_address]
            if sig.timestamp > cutoff_time
        ]
        
        logger.info(f"Valid signature received from {oracle_address} for round {round_id} "
                   f"({len(consensus_round.collected_signatures)}/{consensus_round.target_signatures})")
        
        # Check if consensus is achieved
        await self._check_consensus_achievement(round_id)
    
    async def _check_consensus_achievement(self, round_id: str):
        """Check if consensus has been achieved for the round"""
        consensus_round = self.active_consensus_rounds.get(round_id)
        if not consensus_round or consensus_round.consensus_achieved:
            return
        
        signatures = consensus_round.collected_signatures
        
        # Check if we have enough signatures
        if len(signatures) < consensus_round.target_signatures:
            return
        
        # Group signatures by state root
        state_root_groups = {}
        for sig in signatures:
            state_root = sig.state_root
            if state_root not in state_root_groups:
                state_root_groups[state_root] = []
            state_root_groups[state_root].append(sig)
        
        # Find the most supported state root
        max_support = 0
        consensus_state_root = None
        
        for state_root, supporting_sigs in state_root_groups.items():
            support_count = len(supporting_sigs)
            weighted_support = sum(sig.confidence_score for sig in supporting_sigs)
            
            if support_count > max_support:
                max_support = support_count
                consensus_state_root = state_root
        
        # Check if consensus threshold is met
        total_signatures = len(signatures)
        consensus_ratio = max_support / total_signatures
        
        if (consensus_ratio >= self.consensus_threshold and
            max_support >= consensus_round.target_signatures):
            
            # Consensus achieved!
            consensus_round.consensus_achieved = True
            consensus_round.final_state_root = consensus_state_root
            
            logger.info(f"Consensus achieved for round {round_id}! "
                       f"State root: {consensus_state_root} "
                       f"({max_support}/{total_signatures} signatures)")
            
            # Update oracle reputations
            await self._update_oracle_reputations(round_id, consensus_state_root)
            
        else:
            logger.info(f"Consensus not yet achieved for round {round_id} "
                       f"({max_support}/{total_signatures}, ratio: {consensus_ratio:.2f})")
    
    async def _update_oracle_reputations(self, round_id: str, consensus_state_root: str):
        """Update oracle reputation scores based on consensus participation"""
        consensus_round = self.active_consensus_rounds.get(round_id)
        if not consensus_round:
            return
        
        for signature in consensus_round.collected_signatures:
            oracle_address = signature.oracle_address
            oracle_node = self.oracle_nodes.get(oracle_address)
            
            if oracle_node:
                # Positive reputation for correct consensus
                if signature.state_root == consensus_state_root:
                    reputation_boost = 0.01 * signature.confidence_score
                    oracle_node.reputation_score = min(1.0, oracle_node.reputation_score + reputation_boost)
                    
                # Negative reputation for incorrect state root
                else:
                    reputation_penalty = 0.02
                    oracle_node.reputation_score = max(0.0, oracle_node.reputation_score - reputation_penalty)
                    
                    # Track potential misbehavior
                    if oracle_node.reputation_score < 0.5:
                        oracle_node.slashing_count += 1
                        logger.warning(f"Oracle {oracle_address} slashing count increased to {oracle_node.slashing_count}")
                        
                        if oracle_node.slashing_count >= self.slashing_threshold:
                            oracle_node.status = OracleStatus.SUSPENDED
                            logger.warning(f"Oracle {oracle_address} suspended due to excessive slashing")
        
        logger.info(f"Updated oracle reputations for consensus round {round_id}")
    
    async def _handle_invalid_signature(
        self,
        oracle_address: str,
        attestation: SignatureAttestation
    ):
        """Handle invalid signature from oracle"""
        oracle_node = self.oracle_nodes.get(oracle_address)
        if oracle_node:
            # Decrease reputation
            oracle_node.reputation_score = max(0.0, oracle_node.reputation_score - 0.05)
            oracle_node.signatures_submitted += 1  # Count as attempt
            
            # Check if oracle should be suspended
            if oracle_node.reputation_score < 0.3:
                oracle_node.status = OracleStatus.SUSPENDED
                logger.warning(f"Oracle {oracle_address} suspended due to low reputation")
    
    async def _handle_oracle_error(self, oracle_address: str, error_message: str):
        """Handle oracle communication errors"""
        oracle_node = self.oracle_nodes.get(oracle_address)
        if oracle_node:
            # Mark as potentially inactive
            if "timeout" in error_message.lower():
                oracle_node.response_time_avg += 10.0  # Penalty for timeouts
                
            # Multiple consecutive errors may indicate oracle issues
            logger.warning(f"Oracle error for {oracle_address}: {error_message}")
    
    async def _monitor_oracle_health(self):
        """Monitor oracle health and update statuses"""
        while True:
            try:
                current_time = datetime.now()
                
                for oracle_address, oracle_node in self.oracle_nodes.items():
                    # Check if oracle has been seen recently
                    time_since_seen = (current_time - oracle_node.last_seen).total_seconds()
                    
                    if time_since_seen > 3600:  # 1 hour
                        if oracle_node.status == OracleStatus.ACTIVE:
                            oracle_node.status = OracleStatus.INACTIVE
                            logger.warning(f"Oracle {oracle_address} marked as inactive")
                    
                    # Check reputation recovery for suspended oracles
                    if (oracle_node.status == OracleStatus.SUSPENDED and
                        oracle_node.reputation_score > 0.8):
                        oracle_node.status = OracleStatus.ACTIVE
                        oracle_node.slashing_count = 0
                        logger.info(f"Oracle {oracle_address} reactivated after reputation recovery")
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in oracle health monitoring: {str(e)}")
                await asyncio.sleep(300)
    
    async def _cleanup_expired_rounds(self):
        """Clean up expired consensus rounds"""
        while True:
            try:
                current_time = datetime.now()
                expired_rounds = []
                
                for round_id, consensus_round in self.active_consensus_rounds.items():
                    if current_time > consensus_round.deadline:
                        expired_rounds.append(round_id)
                
                for round_id in expired_rounds:
                    logger.info(f"Cleaning up expired consensus round: {round_id}")
                    del self.active_consensus_rounds[round_id]
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in consensus round cleanup: {str(e)}")
                await asyncio.sleep(60)
    
    def get_consensus_status(self, round_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed status of a consensus round"""
        consensus_round = self.active_consensus_rounds.get(round_id)
        if not consensus_round:
            return None
        
        return {
            'round_id': round_id,
            'operation_id': consensus_round.operation_id,
            'start_time': consensus_round.start_time.isoformat(),
            'deadline': consensus_round.deadline.isoformat(),
            'target_signatures': consensus_round.target_signatures,
            'collected_signatures': len(consensus_round.collected_signatures),
            'consensus_achieved': consensus_round.consensus_achieved,
            'final_state_root': consensus_round.final_state_root,
            'participating_oracles': list(consensus_round.participant_oracles),
            'signature_details': [
                {
                    'oracle': sig.oracle_address,
                    'state_root': sig.state_root,
                    'confidence_score': sig.confidence_score,
                    'validation_status': sig.validation_status.value
                }
                for sig in consensus_round.collected_signatures
            ]
        }
    
    def get_oracle_statistics(self) -> Dict[str, Any]:
        """Get comprehensive oracle network statistics"""
        active_oracles = sum(1 for node in self.oracle_nodes.values() if node.status == OracleStatus.ACTIVE)
        inactive_oracles = sum(1 for node in self.oracle_nodes.values() if node.status == OracleStatus.INACTIVE)
        suspended_oracles = sum(1 for node in self.oracle_nodes.values() if node.status == OracleStatus.SUSPENDED)
        
        avg_reputation = sum(node.reputation_score for node in self.oracle_nodes.values()) / len(self.oracle_nodes)
        
        total_signatures = sum(node.signatures_submitted for node in self.oracle_nodes.values())
        total_verified = sum(node.signatures_verified for node in self.oracle_nodes.values())
        
        return {
            'total_oracles': len(self.oracle_nodes),
            'active_oracles': active_oracles,
            'inactive_oracles': inactive_oracles,
            'suspended_oracles': suspended_oracles,
            'average_reputation': avg_reputation,
            'total_signatures_submitted': total_signatures,
            'total_signatures_verified': total_verified,
            'verification_rate': (total_verified / total_signatures * 100) if total_signatures > 0 else 0,
            'active_consensus_rounds': len(self.active_consensus_rounds),
            'oracle_details': [
                {
                    'address': address,
                    'status': node.status.value,
                    'reputation_score': node.reputation_score,
                    'signatures_submitted': node.signatures_submitted,
                    'signatures_verified': node.signatures_verified,
                    'response_time_avg': node.response_time_avg,
                    'slashing_count': node.slashing_count
                }
                for address, node in self.oracle_nodes.items()
            ]
        }

async def main():
    """Test the enhanced multi-oracle validator"""
    config = {
        'min_signatures': 3,
        'max_signatures': 5,
        'consensus_threshold': 0.67,
        'byzantine_tolerance': 1,
        'signature_timeout': 300,
        'reputation_threshold': 0.8,
        'max_signature_age': 600,
        'replay_window': 3600,
        'slashing_threshold': 3,
        'oracles': {
            'oracle1': {
                'address': '${CONTRACT_ADDRESS}',
                'public_key': 'pubkey1',
                'endpoint': 'https://oracle1.example.com',
                'reputation_score': 1.0,
                'region': 'us-east'
            },
            'oracle2': {
                'address': '${CONTRACT_ADDRESS}',
                'public_key': 'pubkey2',
                'endpoint': 'https://oracle2.example.com',
                'reputation_score': 1.0,
                'region': 'eu-west'
            },
            'oracle3': {
                'address': '${CONTRACT_ADDRESS}',
                'public_key': 'pubkey3',
                'endpoint': 'https://oracle3.example.com',
                'reputation_score': 1.0,
                'region': 'asia-east'
            }
        }
    }
    
    validator = EnhancedMultiOracleValidator(config)
    
    # Test consensus round
    message_data = {
        'operation_id': 'test_operation_123',
        'source_chain_id': 1,
        'target_chain_id': 137,
        'payload_hash': '${CONTRACT_ADDRESS}34567890abcdef1234567890'
    }
    
    round_id = await validator.initiate_consensus_round('test_operation_123', message_data)
    
    # Wait for consensus
    await asyncio.sleep(5)
    
    # Get status
    status = validator.get_consensus_status(round_id)
    if status:
        print(f"Consensus status: {json.dumps(status, indent=2)}")
    
    # Get oracle statistics
    stats = validator.get_oracle_statistics()
    print(f"Oracle statistics: {json.dumps(stats, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())
