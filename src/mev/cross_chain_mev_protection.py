"""
Cross-Chain MEV Protection

This module implements advanced protection against Miner/Maximal Extractable Value (MEV)
attacks across multiple blockchain networks. It provides monitoring, detection,
and prevention mechanisms for cross-chain MEV.

Features:
- MEV attack detection
- Transaction privacy mechanisms
- Frontrunning protection
- Sandwich attack prevention
- Cross-chain MEV monitoring
"""

import json
import time
import random
import hashlib
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Union, Callable, Set
from enum import Enum
from dataclasses import dataclass
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("cross_chain_mev")

class MEVAttackType(Enum):
    """Types of MEV attacks"""
    FRONTRUNNING = "frontrunning"
    BACKRUNNING = "backrunning"
    SANDWICH = "sandwich"
    LIQUIDATION = "liquidation"
    ARBITRAGE = "arbitrage"
    TIME_BANDIT = "time_bandit"
    CROSS_DOMAIN = "cross_domain"


class ProtectionLevel(Enum):
    """Protection levels for MEV mitigation"""
    MINIMAL = 1
    STANDARD = 2
    ENHANCED = 3
    MAXIMUM = 4


class PrivacyMechanism(Enum):
    """Privacy mechanisms for transaction protection"""
    NONE = "none"
    COMMIT_REVEAL = "commit_reveal"
    ENCRYPTED_MEMPOOL = "encrypted_mempool"
    PRIVATE_RELAY = "private_relay"
    TIMELOCK = "timelock"
    BATCH_AUCTION = "batch_auction"


@dataclass
class MEVThreat:
    """MEV threat information"""
    threat_id: str
    attack_type: MEVAttackType
    source_chain_id: int
    target_chain_id: Optional[int]
    severity: int  # 1-10
    confidence: float  # 0.0-1.0
    description: str
    affected_assets: List[str]
    detection_time: int
    raw_data: Dict[str, Any]
    mitigations: List[str]


@dataclass
class ChainMEVStats:
    """MEV statistics for a blockchain"""
    chain_id: int
    chain_name: str
    total_mev_detected: float  # In USD
    attack_counts: Dict[MEVAttackType, int]
    top_extractors: List[Dict[str, Any]]
    common_targets: List[Dict[str, Any]]
    historical_data: List[Dict[str, Any]]
    last_updated: int


class CrossChainMEVProtection:
    """
    Cross-Chain MEV Protection system.
    
    This class provides advanced protection against MEV attacks across
    multiple blockchain networks.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the Cross-Chain MEV Protection system.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config = self._load_config(config_path)
        self.protection_level = ProtectionLevel.STANDARD
        self.chain_configs: Dict[int, Dict[str, Any]] = {}
        self.privacy_mechanisms: Dict[int, PrivacyMechanism] = {}
        self.detected_threats: List[MEVThreat] = []
        self.chain_stats: Dict[int, ChainMEVStats] = {}
        self.protected_addresses: Dict[int, Set[str]] = {}  # Chain ID -> Set of addresses
        self.callbacks: Dict[str, List[Callable]] = {
            "threat_detected": [],
            "protection_applied": [],
            "status_update": []
        }
        
        # Initialize chain configurations
        self._initialize_chain_configs()
        
        # Start background tasks
        self.running = True
        self.background_tasks = [
            asyncio.create_task(self._monitor_mev_activity()),
            asyncio.create_task(self._update_chain_statistics()),
            asyncio.create_task(self._clean_old_threats())
        ]
        
        logger.info(f"Cross-Chain MEV Protection initialized with {len(self.chain_configs)} chains")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Configuration dictionary
        """
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            # Use default configuration as fallback
            return {
                "chains": [],
                "global_settings": {
                    "default_protection_level": "STANDARD",
                    "monitoring_interval_seconds": 30,
                    "stats_update_interval_seconds": 300,
                    "threat_retention_days": 7,
                    "min_threat_severity": 3,
                    "min_threat_confidence": 0.6
                }
            }
    
    def _initialize_chain_configs(self):
        """Initialize chain configurations from the loaded config"""
        for chain_config in self.config.get("chains", []):
            try:
                chain_id = chain_config["chain_id"]
                self.chain_configs[chain_id] = chain_config
                
                # Set default privacy mechanism
                privacy_mechanism = chain_config.get("privacy_mechanism", "none")
                self.privacy_mechanisms[chain_id] = PrivacyMechanism(privacy_mechanism)
                
                # Initialize protected addresses set
                self.protected_addresses[chain_id] = set()
                
                # Initialize chain stats
                self.chain_stats[chain_id] = ChainMEVStats(
                    chain_id=chain_id,
                    chain_name=chain_config["name"],
                    total_mev_detected=0.0,
                    attack_counts={attack_type: 0 for attack_type in MEVAttackType},
                    top_extractors=[],
                    common_targets=[],
                    historical_data=[],
                    last_updated=int(time.time())
                )
                
                logger.info(f"Initialized MEV protection for chain ID {chain_id} ({chain_config['name']})")
            except Exception as e:
                logger.error(f"Failed to initialize chain config: {e}")
    
    async def _monitor_mev_activity(self):
        """Background task to monitor MEV activity across chains"""
        interval = self.config["global_settings"]["monitoring_interval_seconds"]
        while self.running:
            try:
                for chain_id, config in self.chain_configs.items():
                    # Skip chains that are disabled for monitoring
                    if not config.get("monitoring_enabled", True):
                        continue
                    
                    # Detect MEV threats on this chain
                    threats = await self._detect_mev_threats(chain_id)
                    
                    # Process detected threats
                    for threat in threats:
                        self._process_threat(threat)
            
            except Exception as e:
                logger.error(f"Error in MEV monitoring: {e}")
            
            await asyncio.sleep(interval)
    
    async def _detect_mev_threats(self, chain_id: int) -> List[MEVThreat]:
        """
        Detect MEV threats on a specific chain.
        
        Args:
            chain_id: Chain ID to monitor
            
        Returns:
            List of detected MEV threats
        """
        # In a real implementation, this would analyze mempool transactions,
        # block data, and other on-chain information to detect MEV activity.
        # For demonstration, we'll simulate threat detection.
        
        # Simulated threat detection
        threats = []
        
        # Only generate threats occasionally to simulate realistic detection
        if random.random() < 0.3:  # 30% chance of detecting a threat
            # Generate a random threat
            attack_types = list(MEVAttackType)
            attack_type = random.choice(attack_types)
            
            # Higher chance of cross-domain attacks for cross-chain MEV
            if random.random() < 0.4:
                attack_type = MEVAttackType.CROSS_DOMAIN
            
            # For cross-domain attacks, include a target chain
            target_chain_id = None
            if attack_type == MEVAttackType.CROSS_DOMAIN:
                other_chains = [cid for cid in self.chain_configs.keys() if cid != chain_id]
                if other_chains:
                    target_chain_id = random.choice(other_chains)
            
            # Generate severity and confidence
            severity = random.randint(1, 10)
            confidence = round(random.uniform(0.5, 1.0), 2)
            
            # Only include threats that meet minimum thresholds
            min_severity = self.config["global_settings"]["min_threat_severity"]
            min_confidence = self.config["global_settings"]["min_threat_confidence"]
            
            if severity >= min_severity and confidence >= min_confidence:
                threat = MEVThreat(
                    threat_id=str(uuid.uuid4()),
                    attack_type=attack_type,
                    source_chain_id=chain_id,
                    target_chain_id=target_chain_id,
                    severity=severity,
                    confidence=confidence,
                    description=self._generate_threat_description(attack_type, chain_id, target_chain_id),
                    affected_assets=self._generate_affected_assets(chain_id),
                    detection_time=int(time.time()),
                    raw_data={"simulated": True},
                    mitigations=self._generate_mitigations(attack_type)
                )
                threats.append(threat)
        
        return threats
    
    def _generate_threat_description(self, attack_type: MEVAttackType, source_chain_id: int, target_chain_id: Optional[int]) -> str:
        """Generate a description for a threat"""
        chain_name = self.chain_configs[source_chain_id]["name"]
        
        if attack_type == MEVAttackType.FRONTRUNNING:
            return f"Potential frontrunning attack detected on {chain_name}. Transaction ordering manipulation observed."
        
        elif attack_type == MEVAttackType.BACKRUNNING:
            return f"Backrunning activity detected on {chain_name}. Transactions positioned to execute after large trades."
        
        elif attack_type == MEVAttackType.SANDWICH:
            return f"Sandwich attack pattern identified on {chain_name}. Price manipulation through surrounding transactions."
        
        elif attack_type == MEVAttackType.LIQUIDATION:
            return f"MEV from liquidation opportunities detected on {chain_name}. Competitive racing for liquidation rewards."
        
        elif attack_type == MEVAttackType.ARBITRAGE:
            return f"Arbitrage MEV activity observed on {chain_name}. Price discrepancies being exploited."
        
        elif attack_type == MEVAttackType.TIME_BANDIT:
            return f"Potential time bandit attack on {chain_name}. Block reorganization risk for MEV extraction."
        
        elif attack_type == MEVAttackType.CROSS_DOMAIN:
            if target_chain_id:
                target_chain_name = self.chain_configs[target_chain_id]["name"]
                return f"Cross-domain MEV activity between {chain_name} and {target_chain_name}. Bridge transactions being targeted."
            else:
                return f"Cross-domain MEV activity originating from {chain_name}. Bridge transactions being targeted."
        
        return f"Unknown MEV activity detected on {chain_name}."
    
    def _generate_affected_assets(self, chain_id: int) -> List[str]:
        """Generate a list of affected assets for a threat"""
        # In a real implementation, this would identify the specific assets being targeted
        # For demonstration, we'll use placeholder assets
        
        chain_assets = {
            1: ["ETH", "USDC", "USDT", "DAI", "WBTC"],  # Ethereum
            56: ["BNB", "BUSD", "CAKE", "XVS"],         # BSC
            137: ["MATIC", "AAVE", "QUICK", "SUSHI"],   # Polygon
            42161: ["ETH", "ARB", "GMX", "DPX"],        # Arbitrum
            10: ["ETH", "OP", "SNX", "PERP"]            # Optimism
        }
        
        # Get assets for this chain, or use default list
        assets = chain_assets.get(chain_id, ["UNKNOWN"])
        
        # Select 1-3 random assets
        num_assets = random.randint(1, min(3, len(assets)))
        return random.sample(assets, num_assets)
    
    def _generate_mitigations(self, attack_type: MEVAttackType) -> List[str]:
        """Generate mitigation strategies for a threat"""
        common_mitigations = [
            "Use private transaction relays",
            "Implement timelock mechanisms",
            "Set appropriate slippage tolerance"
        ]
        
        specific_mitigations = {
            MEVAttackType.FRONTRUNNING: [
                "Use commit-reveal schemes",
                "Implement batch auctions"
            ],
            MEVAttackType.BACKRUNNING: [
                "Use flash bundles",
                "Implement transaction bundling"
            ],
            MEVAttackType.SANDWICH: [
                "Set strict slippage limits",
                "Use DEX aggregators with MEV protection"
            ],
            MEVAttackType.LIQUIDATION: [
                "Maintain higher collateralization ratios",
                "Use gradual liquidation mechanisms"
            ],
            MEVAttackType.ARBITRAGE: [
                "Implement price impact fees",
                "Use concentrated liquidity positions"
            ],
            MEVAttackType.TIME_BANDIT: [
                "Wait for more confirmations",
                "Use chains with faster finality"
            ],
            MEVAttackType.CROSS_DOMAIN: [
                "Use secure bridge protocols",
                "Implement cross-chain message verification",
                "Wait for sufficient confirmations before finalizing cross-chain transactions"
            ]
        }
        
        # Combine common mitigations with specific ones
        mitigations = common_mitigations.copy()
        if attack_type in specific_mitigations:
            mitigations.extend(specific_mitigations[attack_type])
        
        # Return 3-5 random mitigations
        num_mitigations = min(5, len(mitigations))
        return random.sample(mitigations, num_mitigations)
    
    def _process_threat(self, threat: MEVThreat):
        """
        Process a detected MEV threat.
        
        Args:
            threat: The detected threat
        """
        # Add to detected threats
        self.detected_threats.append(threat)
        
        # Update chain statistics
        if threat.source_chain_id in self.chain_stats:
            stats = self.chain_stats[threat.source_chain_id]
            stats.attack_counts[threat.attack_type] = stats.attack_counts.get(threat.attack_type, 0) + 1
            
            # Estimate MEV value (simplified)
            estimated_value = threat.severity * 1000  # $1000 per severity point
            stats.total_mev_detected += estimated_value
        
        # Apply protection measures based on threat
        self._apply_protection_measures(threat)
        
        # Trigger callbacks
        self._trigger_callbacks("threat_detected", threat)
        
        logger.warning(
            f"MEV threat detected: {threat.attack_type.value} on chain {threat.source_chain_id} "
            f"(Severity: {threat.severity}/10, Confidence: {threat.confidence:.2f})"
        )
    
    def _apply_protection_measures(self, threat: MEVThreat):
        """
        Apply protection measures for a detected threat.
        
        Args:
            threat: The detected threat
        """
        # Determine appropriate protection measures based on threat type and severity
        protection_measures = []
        
        # Basic protection for all threats
        protection_measures.append({
            "type": "alert",
            "description": f"MEV threat alert: {threat.attack_type.value}",
            "severity": threat.severity
        })
        
        # Apply specific protections based on attack type
        if threat.attack_type == MEVAttackType.FRONTRUNNING:
            protection_measures.append({
                "type": "privacy",
                "mechanism": PrivacyMechanism.COMMIT_REVEAL.value,
                "description": "Enable commit-reveal scheme for sensitive transactions"
            })
        
        elif threat.attack_type == MEVAttackType.SANDWICH:
            protection_measures.append({
                "type": "slippage",
                "value": "0.5%",
                "description": "Tighten slippage tolerance to prevent sandwich attacks"
            })
        
        elif threat.attack_type == MEVAttackType.CROSS_DOMAIN:
            protection_measures.append({
                "type": "delay",
                "value": "5 minutes",
                "description": "Add timelock delay for cross-chain transactions"
            })
            
            if threat.target_chain_id:
                protection_measures.append({
                    "type": "verification",
                    "description": f"Enhanced verification for transactions to chain {threat.target_chain_id}"
                })
        
        # Apply additional measures for high-severity threats
        if threat.severity >= 8:
            protection_measures.append({
                "type": "pause",
                "duration": "30 minutes",
                "description": "Temporarily pause non-essential operations"
            })
        
        # Log and trigger callbacks for each protection measure
        for measure in protection_measures:
            logger.info(f"Applying protection measure: {measure['description']}")
            self._trigger_callbacks("protection_applied", {
                "threat_id": threat.threat_id,
                "measure": measure
            })
    
    async def _update_chain_statistics(self):
        """Background task to update chain statistics"""
        interval = self.config["global_settings"]["stats_update_interval_seconds"]
        while self.running:
            try:
                current_time = int(time.time())
                
                for chain_id, stats in self.chain_stats.items():
                    # Update last updated timestamp
                    stats.last_updated = current_time
                    
                    # Update historical data (simplified)
                    historical_entry = {
                        "timestamp": current_time,
                        "total_mev": stats.total_mev_detected,
                        "attack_counts": {k.value: v for k, v in stats.attack_counts.items()}
                    }
                    
                    stats.historical_data.append(historical_entry)
                    
                    # Keep only the last 100 entries
                    if len(stats.historical_data) > 100:
                        stats.historical_data = stats.historical_data[-100:]
                    
                    # Update top extractors (simplified simulation)
                    stats.top_extractors = self._simulate_top_extractors(chain_id)
                    
                    # Update common targets (simplified simulation)
                    stats.common_targets = self._simulate_common_targets(chain_id)
                
                # Trigger status update callback
                self._trigger_callbacks("status_update", {
                    "timestamp": current_time,
                    "chain_stats": {cid: self._serialize_chain_stats(stats) for cid, stats in self.chain_stats.items()}
                })
            
            except Exception as e:
                logger.error(f"Error updating chain statistics: {e}")
            
            await asyncio.sleep(interval)
    
    def _serialize_chain_stats(self, stats: ChainMEVStats) -> Dict[str, Any]:
        """Convert ChainMEVStats to a serializable dictionary"""
        return {
            "chain_id": stats.chain_id,
            "chain_name": stats.chain_name,
            "total_mev_detected": stats.total_mev_detected,
            "attack_counts": {k.value: v for k, v in stats.attack_counts.items()},
            "top_extractors": stats.top_extractors,
            "common_targets": stats.common_targets,
            "last_updated": stats.last_updated
        }
    
    def _simulate_top_extractors(self, chain_id: int) -> List[Dict[str, Any]]:
        """Simulate top MEV extractors for a chain"""
        # In a real implementation, this would analyze on-chain data
        # For demonstration, we'll generate simulated data
        
        num_extractors = random.randint(3, 8)
        extractors = []
        
        for i in range(num_extractors):
            address = f"0x{hashlib.sha256(f'extractor{i}{chain_id}'.encode()).hexdigest()[:40]}"
            value = random.uniform(10000, 1000000)
            attack_types = random.sample([t.value for t in MEVAttackType], k=random.randint(1, 3))
            
            extractors.append({
                "address": address,
                "extracted_value": round(value, 2),
                "attack_types": attack_types,
                "first_seen": int(time.time()) - random.randint(86400, 2592000)  # 1-30 days ago
            })
        
        # Sort by extracted value
        extractors.sort(key=lambda x: x["extracted_value"], reverse=True)
        
        return extractors
    
    def _simulate_common_targets(self, chain_id: int) -> List[Dict[str, Any]]:
        """Simulate common MEV targets for a chain"""
        # In a real implementation, this would analyze on-chain data
        # For demonstration, we'll generate simulated data
        
        # Common DeFi protocols that might be MEV targets
        defi_protocols = [
            "Uniswap", "SushiSwap", "Curve", "Balancer", "Aave", "Compound",
            "MakerDAO", "PancakeSwap", "QuickSwap", "Trader Joe", "GMX"
        ]
        
        num_targets = random.randint(3, 6)
        targets = []
        
        for i in range(num_targets):
            protocol = random.choice(defi_protocols)
            address = f"0x{hashlib.sha256(f'target{protocol}{chain_id}'.encode()).hexdigest()[:40]}"
            value = random.uniform(5000, 500000)
            vulnerability = random.choice([
                "Price oracle manipulation",
                "Flash loan attack surface",
                "Sandwich attack vulnerability",
                "Frontrunning opportunity",
                "Liquidation race condition"
            ])
            
            targets.append({
                "name": protocol,
                "address": address,
                "estimated_value_at_risk": round(value, 2),
                "vulnerability": vulnerability
            })
        
        # Sort by value at risk
        targets.sort(key=lambda x: x["estimated_value_at_risk"], reverse=True)
        
        return targets
    
    async def _clean_old_threats(self):
        """Background task to clean old threats"""
        # Run once per day
        interval = 86400
        while self.running:
            try:
                current_time = int(time.time())
                retention_days = self.config["global_settings"]["threat_retention_days"]
                retention_seconds = retention_days * 86400
                
                # Remove threats older than retention period
                self.detected_threats = [
                    threat for threat in self.detected_threats
                    if current_time - threat.detection_time < retention_seconds
                ]
                
                logger.info(f"Cleaned old threats. {len(self.detected_threats)} threats retained.")
            
            except Exception as e:
                logger.error(f"Error cleaning old threats: {e}")
            
            await asyncio.sleep(interval)
    
    def _trigger_callbacks(self, event_type: str, data: Any):
        """
        Trigger registered callbacks for an event.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        for callback in self.callbacks.get(event_type, []):
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error in {event_type} callback: {e}")
    
    def register_callback(self, event_type: str, callback: Callable):
        """
        Register a callback for a specific event type.
        
        Args:
            event_type: Type of event to register for
            callback: Callback function
        """
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
            logger.info(f"Registered callback for event type '{event_type}'")
        else:
            logger.error(f"Unknown event type: {event_type}")
    
    def set_protection_level(self, level: ProtectionLevel):
        """
        Set the protection level for MEV mitigation.
        
        Args:
            level: New protection level
        """
        old_level = self.protection_level
        self.protection_level = level
        logger.info(f"Protection level changed from {old_level.name} to {level.name}")
        
        # Apply protection level changes
        self._apply_protection_level_settings(level)
    
    def _apply_protection_level_settings(self, level: ProtectionLevel):
        """
        Apply settings for a protection level.
        
        Args:
            level: Protection level to apply
        """
        # Update privacy mechanisms based on protection level
        for chain_id in self.chain_configs:
            if level == ProtectionLevel.MINIMAL:
                self.privacy_mechanisms[chain_id] = PrivacyMechanism.NONE
            
            elif level == ProtectionLevel.STANDARD:
                # Use chain's default or fallback to PRIVATE_RELAY
                default_mechanism = self.chain_configs[chain_id].get("privacy_mechanism", "private_relay")
                self.privacy_mechanisms[chain_id] = PrivacyMechanism(default_mechanism)
            
            elif level == ProtectionLevel.ENHANCED:
                # Use more secure mechanisms
                self.privacy_mechanisms[chain_id] = PrivacyMechanism.ENCRYPTED_MEMPOOL
            
            elif level == ProtectionLevel.MAXIMUM:
                # Use most secure mechanism
                self.privacy_mechanisms[chain_id] = PrivacyMechanism.BATCH_AUCTION
        
        # Log the changes
        logger.info(f"Applied {level.name} protection level settings")
    
    def protect_address(self, chain_id: int, address: str):
        """
        Add an address to the protected addresses list.
        
        Args:
            chain_id: Chain ID
            address: Address to protect
        """
        if chain_id in self.protected_addresses:
            self.protected_addresses[chain_id].add(address)
            logger.info(f"Added address {address} to protected addresses on chain {chain_id}")
        else:
            logger.error(f"Chain {chain_id} not configured")
    
    def unprotect_address(self, chain_id: int, address: str):
        """
        Remove an address from the protected addresses list.
        
        Args:
            chain_id: Chain ID
            address: Address to unprotect
        """
        if chain_id in self.protected_addresses and address in self.protected_addresses[chain_id]:
            self.protected_addresses[chain_id].remove(address)
            logger.info(f"Removed address {address} from protected addresses on chain {chain_id}")
        else:
            logger.warning(f"Address {address} not in protected addresses for chain {chain_id}")
    
    def get_protected_addresses(self, chain_id: int) -> List[str]:
        """
        Get the list of protected addresses for a chain.
        
        Args:
            chain_id: Chain ID
            
        Returns:
            List of protected addresses
        """
        if chain_id in self.protected_addresses:
            return list(self.protected_addresses[chain_id])
        else:
            logger.error(f"Chain {chain_id} not configured")
            return []
    
    def get_chain_mev_stats(self, chain_id: int) -> Dict[str, Any]:
        """
        Get MEV statistics for a specific chain.
        
        Args:
            chain_id: Chain ID
            
        Returns:
            Chain MEV statistics
        """
        if chain_id in self.chain_stats:
            return self._serialize_chain_stats(self.chain_stats[chain_id])
        else:
            logger.error(f"Chain {chain_id} not configured")
            return {}
    
    def get_recent_threats(self, limit: int = 10, min_severity: int = 0) -> List[Dict[str, Any]]:
        """
        Get recent MEV threats.
        
        Args:
            limit: Maximum number of threats to return
            min_severity: Minimum severity threshold
            
        Returns:
            List of recent threats
        """
        # Filter threats by severity
        filtered_threats = [
            threat for threat in self.detected_threats
            if threat.severity >= min_severity
        ]
        
        # Sort by detection time (newest first)
        sorted_threats = sorted(
            filtered_threats,
            key=lambda x: x.detection_time,
            reverse=True
        )
        
        # Limit the number of results
        limited_threats = sorted_threats[:limit]
        
        # Convert to serializable dictionaries
        return [
            {
                "threat_id": threat.threat_id,
                "attack_type": threat.attack_type.value,
                "source_chain_id": threat.source_chain_id,
                "target_chain_id": threat.target_chain_id,
                "severity": threat.severity,
                "confidence": threat.confidence,
                "description": threat.description,
                "affected_assets": threat.affected_assets,
                "detection_time": threat.detection_time,
                "mitigations": threat.mitigations
            }
            for threat in limited_threats
        ]
    
    def get_protection_status(self) -> Dict[str, Any]:
        """
        Get the current protection status.
        
        Returns:
            Protection status information
        """
        return {
            "protection_level": self.protection_level.name,
            "chains_protected": len(self.chain_configs),
            "privacy_mechanisms": {
                chain_id: mechanism.value
                for chain_id, mechanism in self.privacy_mechanisms.items()
            },
            "total_protected_addresses": sum(len(addresses) for addresses in self.protected_addresses.values()),
            "total_threats_detected": len(self.detected_threats),
            "recent_threats": len([
                threat for threat in self.detected_threats
                if time.time() - threat.detection_time < 86400  # Last 24 hours
            ])
        }
    
    async def shutdown(self):
        """Shutdown the MEV protection system"""
        logger.info("Shutting down Cross-Chain MEV Protection")
        self.running = False
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        logger.info("Cross-Chain MEV Protection shutdown complete")


async def main():
    """Example usage of the Cross-Chain MEV Protection system"""
    # Create MEV protection system
    mev_protection = CrossChainMEVProtection("mev_config.json")
    
    # Register callbacks
    mev_protection.register_callback("threat_detected", lambda threat: print(f"Threat detected: {threat.description}"))
    
    # Set protection level
    mev_protection.set_protection_level(ProtectionLevel.ENHANCED)
    
    # Protect some addresses
    mev_protection.protect_address(1, "${CONTRACT_ADDRESS}")
    mev_protection.protect_address(56, "${CONTRACT_ADDRESS}")
    
    # Run for a while to detect threats
    await asyncio.sleep(10)
    
    # Get recent threats
    threats = mev_protection.get_recent_threats(limit=5, min_severity=5)
    print(f"Recent threats: {threats}")
    
    # Get protection status
    status = mev_protection.get_protection_status()
    print(f"Protection status: {status}")
    
    # Shutdown
    await mev_protection.shutdown()


if __name__ == "__main__":
    asyncio.run(main())