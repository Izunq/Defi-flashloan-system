#!/usr/bin/env python3
"""
Enhanced Oracle Security Implementation for Single Dependency Risk Mitigation
Comprehensive multi-oracle framework with advanced manipulation detection
"""

import asyncio
import json
import time
import logging
import statistics
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from web3 import Web3
from collections import defaultdict, deque
import yaml
import threading
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("enhanced_oracle_security.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("EnhancedOracleSecurity")

class OracleSourceType(Enum):
    """Types of oracle data sources"""
    CHAINLINK = "CHAINLINK"
    BAND_PROTOCOL = "BAND_PROTOCOL"
    API3 = "API3"
    TELLOR = "TELLOR"
    DIA = "DIA"
    UNISWAP_V3_TWAP = "UNISWAP_V3_TWAP"
    SUSHISWAP = "SUSHISWAP"
    BALANCER = "BALANCER"
    CURVE = "CURVE"
    CUSTOM_DEX = "CUSTOM_DEX"

class ManipulationThreatLevel(Enum):
    """Threat levels for manipulation detection"""
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"

@dataclass
class OracleSource:
    """Oracle source configuration"""
    source_id: str
    source_type: OracleSourceType
    address: str
    weight: float
    reliability_score: float
    data_source_group: str  # To prevent correlated sources
    api_endpoint: str = ""
    is_active: bool = True
    last_update: int = 0
    successful_updates: int = 0
    failed_updates: int = 0
    latency_ms: float = 0.0
    confidence_score: float = 0.0

@dataclass
class PriceDataPoint:
    """Enhanced price data point"""
    price: float
    timestamp: int
    source_id: str
    confidence: float
    volume: float = 0.0
    gas_used: int = 0
    block_number: int = 0
    transaction_hash: str = ""
    deviation_from_median: float = 0.0
    is_outlier: bool = False

@dataclass
class ManipulationAlert:
    """Manipulation detection alert"""
    alert_id: str
    asset: str
    threat_level: ManipulationThreatLevel
    manipulation_type: str
    confidence: float
    affected_sources: List[str]
    price_impact: float
    timestamp: int
    description: str
    mitigation_actions: List[str] = field(default_factory=list)
    is_resolved: bool = False

class EnhancedOracleSecurityManager:
    """Enhanced oracle security manager for single dependency risk mitigation"""
    
    def __init__(self, config_path: str = "enhanced_oracle_config.yaml"):
        self.config = self._load_config(config_path)
        self.oracle_sources: Dict[str, OracleSource] = {}
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.manipulation_alerts: List[ManipulationAlert] = []
        self.circuit_breakers: Dict[str, bool] = {}
        self.source_group_weights: Dict[str, float] = defaultdict(float)
        
        # Security thresholds
        self.MAX_SOURCE_GROUP_WEIGHT = 0.4  # 40% max weight per source group
        self.MIN_ORACLES_REQUIRED = 5  # Minimum 5 oracles for consensus
        self.MAX_PRICE_DEVIATION = 0.05  # 5% maximum deviation
        self.MANIPULATION_THRESHOLD = 0.8  # 80% confidence for alerts
        self.OUTLIER_Z_SCORE = 2.5  # Z-score threshold for outlier detection
        
        self._initialize_oracle_sources()
        logger.info("Enhanced Oracle Security Manager initialized")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from file"""
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Default configuration for enhanced oracle security"""
        return {
            'oracles': {
                'chainlink_eth_usd': {
                    'type': 'CHAINLINK',
                    'address': '${CONTRACT_ADDRESS}',
                    'weight': 0.25,
                    'data_source_group': 'centralized_price_feeds'
                },
                'band_eth_usd': {
                    'type': 'BAND_PROTOCOL',
                    'address': '${CONTRACT_ADDRESS}',
                    'weight': 0.20,
                    'data_source_group': 'centralized_price_feeds'
                },
                'api3_eth_usd': {
                    'type': 'API3',
                    'address': '${CONTRACT_ADDRESS}',
                    'weight': 0.15,
                    'data_source_group': 'centralized_price_feeds'
                },
                'uniswap_v3_eth_usdc': {
                    'type': 'UNISWAP_V3_TWAP',
                    'address': '${CONTRACT_ADDRESS}',
                    'weight': 0.25,
                    'data_source_group': 'dex_price_feeds'
                },
                'sushiswap_eth_usdc': {
                    'type': 'SUSHISWAP',
                    'address': '${CONTRACT_ADDRESS}',
                    'weight': 0.15,
                    'data_source_group': 'dex_price_feeds'
                }
            },
            'security': {
                'min_oracles': 5,
                'max_deviation': 0.05,
                'manipulation_threshold': 0.8,
                'circuit_breaker_threshold': 0.10
            }
        }
    
    def _initialize_oracle_sources(self):
        """Initialize oracle sources from configuration"""
        for oracle_id, config in self.config.get('oracles', {}).items():
            source = OracleSource(
                source_id=oracle_id,
                source_type=OracleSourceType(config['type']),
                address=config['address'],
                weight=config['weight'],
                reliability_score=1.0,
                data_source_group=config['data_source_group']
            )
            
            self.oracle_sources[oracle_id] = source
            self.source_group_weights[source.data_source_group] += source.weight
            
            # Validate source group weight limits
            if self.source_group_weights[source.data_source_group] > self.MAX_SOURCE_GROUP_WEIGHT:
                logger.warning(
                    f"Source group {source.data_source_group} exceeds maximum weight "
                    f"({self.source_group_weights[source.data_source_group]:.2f} > {self.MAX_SOURCE_GROUP_WEIGHT})"
                )
    
    async def collect_price_data(self, asset: str) -> List[PriceDataPoint]:
        """Collect price data from all active oracle sources"""
        price_points = []
        
        for source_id, source in self.oracle_sources.items():
            if not source.is_active:
                continue
                
            try:
                price_data = await self._fetch_price_from_source(source, asset)
                if price_data:
                    price_points.append(price_data)
                    source.successful_updates += 1
                    source.last_update = int(time.time())
            except Exception as e:
                logger.error(f"Failed to fetch price from {source_id}: {e}")
                source.failed_updates += 1
        
        return price_points
    
    async def _fetch_price_from_source(self, source: OracleSource, asset: str) -> Optional[PriceDataPoint]:
        """Fetch price data from a specific oracle source"""
        try:
            if source.source_type == OracleSourceType.CHAINLINK:
                return await self._fetch_chainlink_price(source, asset)
            elif source.source_type == OracleSourceType.UNISWAP_V3_TWAP:
                return await self._fetch_uniswap_v3_price(source, asset)
            elif source.source_type == OracleSourceType.BAND_PROTOCOL:
                return await self._fetch_band_protocol_price(source, asset)
            else:
                # Mock implementation for other sources
                return await self._fetch_mock_price(source, asset)
        except Exception as e:
            logger.error(f"Error fetching price from {source.source_id}: {e}")
            return None
    
    async def _fetch_chainlink_price(self, source: OracleSource, asset: str) -> PriceDataPoint:
        """Fetch price from Chainlink oracle"""
        # Mock implementation - in production, use actual Chainlink price feed
        import random
        base_price = 1500.0  # ETH base price
        price = base_price * (1 + random.uniform(-0.02, 0.02))  # ±2% variation
        
        return PriceDataPoint(
            price=price,
            timestamp=int(time.time()),
            source_id=source.source_id,
            confidence=0.95,
            volume=random.uniform(1000000, 5000000)
        )
    
    async def _fetch_uniswap_v3_price(self, source: OracleSource, asset: str) -> PriceDataPoint:
        """Fetch TWAP price from Uniswap V3"""
        # Mock implementation - in production, calculate actual TWAP
        import random
        base_price = 1498.0  # Slightly different base price
        price = base_price * (1 + random.uniform(-0.03, 0.03))  # ±3% variation
        
        return PriceDataPoint(
            price=price,
            timestamp=int(time.time()),
            source_id=source.source_id,
            confidence=0.90,
            volume=random.uniform(500000, 2000000)
        )
    
    async def _fetch_band_protocol_price(self, source: OracleSource, asset: str) -> PriceDataPoint:
        """Fetch price from Band Protocol"""
        # Mock implementation
        import random
        base_price = 1501.0
        price = base_price * (1 + random.uniform(-0.025, 0.025))
        
        return PriceDataPoint(
            price=price,
            timestamp=int(time.time()),
            source_id=source.source_id,
            confidence=0.92,
            volume=random.uniform(800000, 3000000)
        )
    
    async def _fetch_mock_price(self, source: OracleSource, asset: str) -> PriceDataPoint:
        """Mock price fetch for testing"""
        import random
        base_price = 1500.0
        price = base_price * (1 + random.uniform(-0.04, 0.04))
        
        return PriceDataPoint(
            price=price,
            timestamp=int(time.time()),
            source_id=source.source_id,
            confidence=random.uniform(0.8, 0.95),
            volume=random.uniform(100000, 1000000)
        )
    
    def calculate_consensus_price(self, price_points: List[PriceDataPoint]) -> Tuple[float, float]:
        """Calculate consensus price with advanced outlier detection"""
        if len(price_points) < self.MIN_ORACLES_REQUIRED:
            raise ValueError(f"Insufficient oracles: {len(price_points)} < {self.MIN_ORACLES_REQUIRED}")
        
        # Calculate weighted median
        weighted_prices = []
        total_weight = 0.0
        
        for point in price_points:
            source = self.oracle_sources[point.source_id]
            weight = source.weight * source.reliability_score
            weighted_prices.extend([point.price] * int(weight * 100))
            total_weight += weight
        
        weighted_prices.sort()
        median_price = statistics.median(weighted_prices)
        
        # Detect outliers using Z-score
        prices = [point.price for point in price_points]
        mean_price = statistics.mean(prices)
        std_price = statistics.stdev(prices) if len(prices) > 1 else 0
        
        for point in price_points:
            if std_price > 0:
                z_score = abs(point.price - mean_price) / std_price
                point.is_outlier = z_score > self.OUTLIER_Z_SCORE
                point.deviation_from_median = abs(point.price - median_price) / median_price
        
        # Calculate confidence based on consensus
        outlier_count = sum(1 for point in price_points if point.is_outlier)
        consensus_strength = 1.0 - (outlier_count / len(price_points))
        
        return median_price, consensus_strength
    
    def detect_manipulation(self, asset: str, price_points: List[PriceDataPoint]) -> List[ManipulationAlert]:
        """Advanced manipulation detection using multiple algorithms"""
        alerts = []
        
        # 1. Price deviation analysis
        deviation_alert = self._detect_price_deviation(asset, price_points)
        if deviation_alert:
            alerts.append(deviation_alert)
        
        # 2. Volume correlation analysis
        volume_alert = self._detect_volume_anomaly(asset, price_points)
        if volume_alert:
            alerts.append(volume_alert)
        
        # 3. Source correlation analysis
        correlation_alert = self._detect_source_correlation(asset, price_points)
        if correlation_alert:
            alerts.append(correlation_alert)
        
        # 4. Historical pattern analysis
        pattern_alert = self._detect_historical_patterns(asset, price_points)
        if pattern_alert:
            alerts.append(pattern_alert)
        
        return alerts
    
    def _detect_price_deviation(self, asset: str, price_points: List[PriceDataPoint]) -> Optional[ManipulationAlert]:
        """Detect excessive price deviations"""
        if len(price_points) < 2:
            return None
        
        prices = [point.price for point in price_points]
        max_price = max(prices)
        min_price = min(prices)
        deviation = (max_price - min_price) / min_price
        
        if deviation > self.MAX_PRICE_DEVIATION:
            threat_level = ManipulationThreatLevel.HIGH if deviation > 0.10 else ManipulationThreatLevel.MEDIUM
            
            return ManipulationAlert(
                alert_id=f"deviation_{asset}_{int(time.time())}",
                asset=asset,
                threat_level=threat_level,
                manipulation_type="PRICE_DEVIATION",
                confidence=min(0.9, deviation / self.MAX_PRICE_DEVIATION),
                affected_sources=[point.source_id for point in price_points if point.is_outlier],
                price_impact=deviation,
                timestamp=int(time.time()),
                description=f"Excessive price deviation detected: {deviation:.2%}",
                mitigation_actions=["ACTIVATE_CIRCUIT_BREAKER", "INCREASE_MONITORING", "VALIDATE_SOURCES"]
            )
        
        return None
    
    def _detect_volume_anomaly(self, asset: str, price_points: List[PriceDataPoint]) -> Optional[ManipulationAlert]:
        """Detect volume anomalies that might indicate manipulation"""
        volumes = [point.volume for point in price_points if point.volume > 0]
        if len(volumes) < 3:
            return None
        
        mean_volume = statistics.mean(volumes)
        max_volume = max(volumes)
        
        # Check for unusual volume spikes
        volume_ratio = max_volume / mean_volume if mean_volume > 0 else 0
        
        if volume_ratio > 5.0:  # 5x normal volume
            return ManipulationAlert(
                alert_id=f"volume_{asset}_{int(time.time())}",
                asset=asset,
                threat_level=ManipulationThreatLevel.MEDIUM,
                manipulation_type="VOLUME_ANOMALY",
                confidence=min(0.8, volume_ratio / 10.0),
                affected_sources=[point.source_id for point in price_points if point.volume == max_volume],
                price_impact=0.0,
                timestamp=int(time.time()),
                description=f"Unusual volume spike detected: {volume_ratio:.1f}x normal",
                mitigation_actions=["MONITOR_TRADING_ACTIVITY", "CHECK_LIQUIDITY"]
            )
        
        return None
    
    def _detect_source_correlation(self, asset: str, price_points: List[PriceDataPoint]) -> Optional[ManipulationAlert]:
        """Detect suspicious correlation between oracle sources"""
        # Group by source group
        group_prices = defaultdict(list)
        for point in price_points:
            source = self.oracle_sources[point.source_id]
            group_prices[source.data_source_group].append(point.price)
        
        # Check if sources in same group are too correlated with outliers
        for group, prices in group_prices.items():
            if len(prices) > 1:
                if all(abs(p - prices[0]) / prices[0] < 0.001 for p in prices):  # Too similar
                    return ManipulationAlert(
                        alert_id=f"correlation_{asset}_{int(time.time())}",
                        asset=asset,
                        threat_level=ManipulationThreatLevel.MEDIUM,
                        manipulation_type="SOURCE_CORRELATION",
                        confidence=0.7,
                        affected_sources=[point.source_id for point in price_points 
                                        if self.oracle_sources[point.source_id].data_source_group == group],
                        price_impact=0.0,
                        timestamp=int(time.time()),
                        description=f"Suspicious correlation in source group: {group}",
                        mitigation_actions=["DIVERSIFY_SOURCES", "INVESTIGATE_GROUP"]
                    )
        
        return None
    
    def _detect_historical_patterns(self, asset: str, price_points: List[PriceDataPoint]) -> Optional[ManipulationAlert]:
        """Detect manipulation patterns based on historical data"""
        history = self.price_history[asset]
        if len(history) < 10:
            return None
        
        # Simple pattern: check for sudden price movements
        recent_prices = [point.price for point in list(history)[-5:]]
        current_prices = [point.price for point in price_points]
        
        if recent_prices and current_prices:
            recent_avg = statistics.mean(recent_prices)
            current_avg = statistics.mean(current_prices)
            change = abs(current_avg - recent_avg) / recent_avg
            
            if change > 0.05:  # 5% sudden change
                return ManipulationAlert(
                    alert_id=f"pattern_{asset}_{int(time.time())}",
                    asset=asset,
                    threat_level=ManipulationThreatLevel.MEDIUM,
                    manipulation_type="HISTORICAL_PATTERN",
                    confidence=min(0.8, change / 0.10),
                    affected_sources=[point.source_id for point in price_points],
                    price_impact=change,
                    timestamp=int(time.time()),
                    description=f"Sudden price change detected: {change:.2%}",
                    mitigation_actions=["VALIDATE_SOURCES", "CHECK_MARKET_CONDITIONS"]
                )
        
        return None
    
    def activate_circuit_breaker(self, asset: str, reason: str):
        """Activate circuit breaker for an asset"""
        self.circuit_breakers[asset] = True
        logger.critical(f"Circuit breaker activated for {asset}: {reason}")
        
        # In production, this would pause trading or limit operations
        self._notify_emergency_team(asset, reason)
    
    def _notify_emergency_team(self, asset: str, reason: str):
        """Notify emergency response team"""
        logger.critical(f"EMERGENCY NOTIFICATION - Asset: {asset}, Reason: {reason}")
        # In production, this would send alerts via multiple channels
    
    async def monitor_asset(self, asset: str) -> Dict[str, Any]:
        """Monitor a specific asset for manipulation"""
        try:
            # Collect price data
            price_points = await self.collect_price_data(asset)
            
            if len(price_points) < self.MIN_ORACLES_REQUIRED:
                logger.warning(f"Insufficient oracle data for {asset}: {len(price_points)} sources")
                return {
                    "asset": asset,
                    "status": "INSUFFICIENT_DATA",
                    "oracle_count": len(price_points),
                    "required": self.MIN_ORACLES_REQUIRED
                }
            
            # Calculate consensus price
            consensus_price, confidence = self.calculate_consensus_price(price_points)
            
            # Detect manipulation
            alerts = self.detect_manipulation(asset, price_points)
            
            # Store in history
            for point in price_points:
                self.price_history[asset].append(point)
            
            # Handle alerts
            for alert in alerts:
                self.manipulation_alerts.append(alert)
                if alert.threat_level in [ManipulationThreatLevel.HIGH, ManipulationThreatLevel.CRITICAL]:
                    self.activate_circuit_breaker(asset, alert.description)
            
            return {
                "asset": asset,
                "status": "MONITORED",
                "consensus_price": consensus_price,
                "confidence": confidence,
                "oracle_count": len(price_points),
                "outliers": sum(1 for p in price_points if p.is_outlier),
                "alerts": len(alerts),
                "circuit_breaker_active": self.circuit_breakers.get(asset, False),
                "timestamp": int(time.time())
            }
            
        except Exception as e:
            logger.error(f"Error monitoring asset {asset}: {e}")
            return {
                "asset": asset,
                "status": "ERROR",
                "error": str(e),
                "timestamp": int(time.time())
            }
    
    async def run_monitoring_cycle(self, assets: List[str]):
        """Run complete monitoring cycle for all assets"""
        logger.info(f"Starting monitoring cycle for {len(assets)} assets")
        
        monitoring_results = []
        for asset in assets:
            result = await self.monitor_asset(asset)
            monitoring_results.append(result)
            
            # Brief pause between assets
            await asyncio.sleep(0.1)
        
        # Log summary
        total_alerts = sum(result.get("alerts", 0) for result in monitoring_results)
        active_breakers = sum(1 for result in monitoring_results 
                             if result.get("circuit_breaker_active", False))
        
        logger.info(f"Monitoring cycle complete: {total_alerts} alerts, {active_breakers} circuit breakers active")
        
        return monitoring_results
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get overall security status"""
        active_oracles = sum(1 for source in self.oracle_sources.values() if source.is_active)
        recent_alerts = [alert for alert in self.manipulation_alerts 
                        if time.time() - alert.timestamp < 3600]  # Last hour
        
        return {
            "active_oracles": active_oracles,
            "total_oracles": len(self.oracle_sources),
            "circuit_breakers_active": sum(1 for active in self.circuit_breakers.values() if active),
            "recent_alerts": len(recent_alerts),
            "source_groups": len(set(source.data_source_group for source in self.oracle_sources.values())),
            "system_health": "HEALTHY" if active_oracles >= self.MIN_ORACLES_REQUIRED else "DEGRADED"
        }

async def main():
    """Main function for testing the enhanced oracle security"""
    # Initialize the security manager
    manager = EnhancedOracleSecurityManager()
    
    # Test assets
    test_assets = ["ETH", "BTC", "USDC", "DAI"]
    
    # Run monitoring cycles
    for cycle in range(5):
        logger.info(f"--- Monitoring Cycle {cycle + 1} ---")
        
        results = await manager.run_monitoring_cycle(test_assets)
        
        # Display results
        for result in results:
            print(f"Asset: {result['asset']}")
            print(f"  Status: {result['status']}")
            if result['status'] == 'MONITORED':
                print(f"  Price: ${result['consensus_price']:.2f}")
                print(f"  Confidence: {result['confidence']:.2%}")
                print(f"  Oracles: {result['oracle_count']}")
                print(f"  Alerts: {result['alerts']}")
                print(f"  Circuit Breaker: {result['circuit_breaker_active']}")
            print()
        
        # Security status
        status = manager.get_security_status()
        print("=== Security Status ===")
        print(f"System Health: {status['system_health']}")
        print(f"Active Oracles: {status['active_oracles']}/{status['total_oracles']}")
        print(f"Recent Alerts: {status['recent_alerts']}")
        print(f"Circuit Breakers: {status['circuit_breakers_active']}")
        print()
        
        # Wait before next cycle
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
