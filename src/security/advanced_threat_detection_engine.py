#!/usr/bin/env python3
"""
Advanced Cross-Chain Threat Detection System
==========================================

AI/ML-powered threat detection for cross-chain operations with real-time
anomaly detection, pattern recognition, and predictive security analysis.
"""

import asyncio
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
from collections import defaultdict, deque

# ML and data science imports
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import joblib
import warnings
warnings.filterwarnings('ignore')

# Web3 and blockchain imports
from web3 import Web3
from eth_account import Account

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ThreatLevel(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class ThreatType(Enum):
    ANOMALY = "anomaly"
    REPLAY_ATTACK = "replay_attack"
    ECONOMIC_MANIPULATION = "economic_manipulation"
    PATTERN_ABUSE = "pattern_abuse"
    VOLUME_SPIKE = "volume_spike"
    SUSPICIOUS_SEQUENCE = "suspicious_sequence"
    ORACLE_MANIPULATION = "oracle_manipulation"
    MEV_ATTACK = "mev_attack"

@dataclass
class OperationFeatures:
    """Features extracted from cross-chain operations for ML analysis"""
    operation_id: str
    timestamp: float
    source_chain_id: int
    target_chain_id: int
    value_eth: float
    gas_price: float
    payload_size: int
    function_selector: str
    operator_address: str
    time_since_last_op: float
    operations_in_window: int
    value_ratio_to_avg: float
    cross_chain_frequency: int
    payload_entropy: float
    gas_efficiency: float

@dataclass
class ThreatAlert:
    """Threat detection alert"""
    alert_id: str
    threat_type: ThreatType
    threat_level: ThreatLevel
    confidence_score: float
    operation_id: str
    affected_chains: List[int]
    description: str
    evidence: Dict[str, Any]
    timestamp: datetime
    recommended_actions: List[str]

class AdvancedThreatDetectionEngine:
    """
    Advanced ML-powered threat detection for cross-chain operations
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.operation_history = deque(maxlen=10000)
        self.threat_alerts = []
        self.feature_scaler = StandardScaler()
        
        # ML Models
        self.anomaly_detector = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        self.threat_classifier = RandomForestClassifier(
            n_estimators=200,
            random_state=42,
            max_depth=10
        )
        self.clustering_model = DBSCAN(eps=0.5, min_samples=5)
        
        # Pattern detection
        self.known_patterns = {}
        self.suspicious_patterns = set()
        self.operator_profiles = defaultdict(dict)
        self.chain_baselines = defaultdict(dict)
        
        # Real-time statistics
        self.operation_stats = defaultdict(list)
        self.hourly_volumes = defaultdict(float)
        self.daily_volumes = defaultdict(float)
        
        # Initialize models
        self._initialize_models()
        
    def _initialize_models(self):
        """Initialize ML models with baseline data"""
        logger.info("Initializing ML models for threat detection")
        
        # Try to load pre-trained models
        try:
            self.anomaly_detector = joblib.load('models/anomaly_detector.pkl')
            self.threat_classifier = joblib.load('models/threat_classifier.pkl')
            self.feature_scaler = joblib.load('models/feature_scaler.pkl')
            logger.info("Loaded pre-trained models successfully")
        except FileNotFoundError:
            logger.info("No pre-trained models found, will train on first batch")
            
    def extract_operation_features(self, operation: Dict[str, Any]) -> OperationFeatures:
        """Extract ML features from a cross-chain operation"""
        
        # Basic operation data
        operation_id = operation['operation_id']
        timestamp = operation['timestamp']
        source_chain = operation['source_chain_id']
        target_chain = operation['target_chain_id']
        value_eth = float(operation['value']) / 10**18
        gas_price = operation.get('gas_price', 0)
        payload = operation.get('payload', b'')
        operator = operation['operator_address']
        
        # Calculate derived features
        payload_size = len(payload)
        function_selector = payload[:4].hex() if len(payload) >= 4 else '0x00000000'
        
        # Time-based features
        current_time = datetime.now().timestamp()
        time_since_last = self._get_time_since_last_operation(operator)
        ops_in_window = self._get_operations_in_window(operator, 3600)  # 1 hour
        
        # Value analysis
        avg_value = self._get_average_value(operator)
        value_ratio = value_eth / avg_value if avg_value > 0 else 1.0
        
        # Cross-chain frequency
        cc_frequency = self._get_cross_chain_frequency(operator, source_chain, target_chain)
        
        # Payload entropy (measure of randomness/complexity)
        payload_entropy = self._calculate_entropy(payload)
        
        # Gas efficiency
        gas_efficiency = value_eth / (gas_price + 1)  # Avoid division by zero
        
        return OperationFeatures(
            operation_id=operation_id,
            timestamp=timestamp,
            source_chain_id=source_chain,
            target_chain_id=target_chain,
            value_eth=value_eth,
            gas_price=gas_price,
            payload_size=payload_size,
            function_selector=function_selector,
            operator_address=operator,
            time_since_last_op=time_since_last,
            operations_in_window=ops_in_window,
            value_ratio_to_avg=value_ratio,
            cross_chain_frequency=cc_frequency,
            payload_entropy=payload_entropy,
            gas_efficiency=gas_efficiency
        )
    
    async def analyze_operation(self, operation: Dict[str, Any]) -> List[ThreatAlert]:
        """Comprehensive threat analysis of a cross-chain operation"""
        alerts = []
        
        try:
            # Extract features
            features = self.extract_operation_features(operation)
            
            # Store operation in history
            self.operation_history.append(features)
            
            # Update statistics
            self._update_statistics(features)
            
            # Run multiple detection algorithms
            anomaly_alerts = await self._detect_anomalies(features)
            pattern_alerts = await self._detect_suspicious_patterns(features)
            volume_alerts = await self._detect_volume_anomalies(features)
            sequence_alerts = await self._detect_suspicious_sequences(features)
            economic_alerts = await self._detect_economic_manipulation(features)
            
            alerts.extend(anomaly_alerts)
            alerts.extend(pattern_alerts)
            alerts.extend(volume_alerts)
            alerts.extend(sequence_alerts)
            alerts.extend(economic_alerts)
            
            # Store alerts
            self.threat_alerts.extend(alerts)
            
            # Trigger real-time responses for high-severity alerts
            for alert in alerts:
                if alert.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                    await self._trigger_emergency_response(alert)
                    
        except Exception as e:
            logger.error(f"Error in threat analysis: {e}")
            
        return alerts
    
    async def _detect_anomalies(self, features: OperationFeatures) -> List[ThreatAlert]:
        """Detect anomalies using ML models"""
        alerts = []
        
        try:
            # Prepare feature vector
            feature_vector = self._features_to_vector(features)
            
            if len(self.operation_history) > 100:  # Need minimum data for anomaly detection
                # Reshape for prediction
                feature_array = np.array([feature_vector])
                feature_scaled = self.feature_scaler.transform(feature_array)
                
                # Anomaly detection
                anomaly_score = self.anomaly_detector.decision_function(feature_scaled)[0]
                is_anomaly = self.anomaly_detector.predict(feature_scaled)[0] == -1
                
                if is_anomaly:
                    confidence = abs(anomaly_score)
                    threat_level = self._score_to_threat_level(confidence)
                    
                    alert = ThreatAlert(
                        alert_id=self._generate_alert_id(),
                        threat_type=ThreatType.ANOMALY,
                        threat_level=threat_level,
                        confidence_score=confidence,
                        operation_id=features.operation_id,
                        affected_chains=[features.source_chain_id, features.target_chain_id],
                        description=f"Anomalous operation detected with score {anomaly_score:.3f}",
                        evidence={
                            "anomaly_score": anomaly_score,
                            "feature_deviations": self._identify_anomalous_features(feature_vector),
                            "historical_comparison": self._get_historical_context(features)
                        },
                        timestamp=datetime.now(),
                        recommended_actions=self._get_anomaly_recommendations(threat_level)
                    )
                    alerts.append(alert)
                    
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            
        return alerts
    
    async def _detect_suspicious_patterns(self, features: OperationFeatures) -> List[ThreatAlert]:
        """Detect known suspicious patterns"""
        alerts = []
        
        # Pattern 1: Rapid succession of small operations (potential dust attack)
        if (features.operations_in_window > 10 and 
            features.value_eth < 0.01 and 
            features.time_since_last_op < 60):
            
            alert = ThreatAlert(
                alert_id=self._generate_alert_id(),
                threat_type=ThreatType.PATTERN_ABUSE,
                threat_level=ThreatLevel.MEDIUM,
                confidence_score=0.75,
                operation_id=features.operation_id,
                affected_chains=[features.source_chain_id, features.target_chain_id],
                description="Potential dust attack pattern detected",
                evidence={
                    "operations_in_window": features.operations_in_window,
                    "operation_value": features.value_eth,
                    "time_interval": features.time_since_last_op
                },
                timestamp=datetime.now(),
                recommended_actions=[
                    "Monitor operator closely",
                    "Consider rate limiting",
                    "Verify legitimate use case"
                ]
            )
            alerts.append(alert)
        
        # Pattern 2: High-value operations with unusual timing
        if (features.value_eth > 100 and 
            features.time_since_last_op < 300 and  # Less than 5 minutes
            features.operations_in_window > 3):
            
            alert = ThreatAlert(
                alert_id=self._generate_alert_id(),
                threat_type=ThreatType.SUSPICIOUS_SEQUENCE,
                threat_level=ThreatLevel.HIGH,
                confidence_score=0.85,
                operation_id=features.operation_id,
                affected_chains=[features.source_chain_id, features.target_chain_id],
                description="Suspicious high-value operation sequence",
                evidence={
                    "value": features.value_eth,
                    "sequence_timing": features.time_since_last_op,
                    "recent_operations": features.operations_in_window
                },
                timestamp=datetime.now(),
                recommended_actions=[
                    "Require additional verification",
                    "Implement delayed execution",
                    "Alert security team"
                ]
            )
            alerts.append(alert)
            
        return alerts
    
    async def _detect_volume_anomalies(self, features: OperationFeatures) -> List[ThreatAlert]:
        """Detect volume-based anomalies"""
        alerts = []
        
        # Get current hourly volume for the operator
        current_hour = datetime.now().hour
        operator_key = f"{features.operator_address}_{current_hour}"
        self.hourly_volumes[operator_key] += features.value_eth
        
        # Check against operator's historical hourly average
        historical_avg = self._get_operator_hourly_average(features.operator_address)
        current_volume = self.hourly_volumes[operator_key]
        
        if historical_avg > 0 and current_volume > historical_avg * 5:  # 5x normal volume
            alert = ThreatAlert(
                alert_id=self._generate_alert_id(),
                threat_type=ThreatType.VOLUME_SPIKE,
                threat_level=ThreatLevel.HIGH,
                confidence_score=0.8,
                operation_id=features.operation_id,
                affected_chains=[features.source_chain_id, features.target_chain_id],
                description=f"Unusual volume spike: {current_volume:.2f} ETH vs avg {historical_avg:.2f} ETH",
                evidence={
                    "current_hourly_volume": current_volume,
                    "historical_average": historical_avg,
                    "spike_ratio": current_volume / historical_avg
                },
                timestamp=datetime.now(),
                recommended_actions=[
                    "Verify large volume operations",
                    "Check for account compromise",
                    "Consider temporary limits"
                ]
            )
            alerts.append(alert)
            
        return alerts
    
    async def _detect_suspicious_sequences(self, features: OperationFeatures) -> List[ThreatAlert]:
        """Detect suspicious operation sequences"""
        alerts = []
        
        # Get recent operations for the operator
        recent_ops = [op for op in self.operation_history 
                     if op.operator_address == features.operator_address 
                     and op.timestamp > datetime.now().timestamp() - 3600]
        
        if len(recent_ops) >= 5:
            # Check for patterns indicating potential attacks
            
            # Pattern: Ping-pong between same chains
            chain_pairs = [(op.source_chain_id, op.target_chain_id) for op in recent_ops[-5:]]
            if len(set(chain_pairs)) <= 2 and len(chain_pairs) == 5:
                alert = ThreatAlert(
                    alert_id=self._generate_alert_id(),
                    threat_type=ThreatType.SUSPICIOUS_SEQUENCE,
                    threat_level=ThreatLevel.MEDIUM,
                    confidence_score=0.7,
                    operation_id=features.operation_id,
                    affected_chains=[features.source_chain_id, features.target_chain_id],
                    description="Ping-pong pattern detected between chain pairs",
                    evidence={
                        "chain_pairs": chain_pairs,
                        "pattern_type": "ping_pong"
                    },
                    timestamp=datetime.now(),
                    recommended_actions=[
                        "Investigate business justification",
                        "Monitor for MEV exploitation"
                    ]
                )
                alerts.append(alert)
                
        return alerts
    
    async def _detect_economic_manipulation(self, features: OperationFeatures) -> List[ThreatAlert]:
        """Detect potential economic manipulation attacks"""
        alerts = []
        
        # Check for value manipulation patterns
        if features.value_ratio_to_avg > 10:  # 10x normal value
            alert = ThreatAlert(
                alert_id=self._generate_alert_id(),
                threat_type=ThreatType.ECONOMIC_MANIPULATION,
                threat_level=ThreatLevel.HIGH,
                confidence_score=0.75,
                operation_id=features.operation_id,
                affected_chains=[features.source_chain_id, features.target_chain_id],
                description="Potential economic manipulation: unusually high value operation",
                evidence={
                    "value_ratio": features.value_ratio_to_avg,
                    "operation_value": features.value_eth
                },
                timestamp=datetime.now(),
                recommended_actions=[
                    "Verify funding source",
                    "Check for price manipulation",
                    "Require additional approvals"
                ]
            )
            alerts.append(alert)
            
        return alerts
    
    def _features_to_vector(self, features: OperationFeatures) -> List[float]:
        """Convert features to numerical vector for ML"""
        return [
            features.value_eth,
            features.gas_price,
            features.payload_size,
            features.time_since_last_op,
            features.operations_in_window,
            features.value_ratio_to_avg,
            features.cross_chain_frequency,
            features.payload_entropy,
            features.gas_efficiency,
            features.source_chain_id,
            features.target_chain_id
        ]
    
    def _calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy of payload data"""
        if len(data) == 0:
            return 0.0
            
        # Count byte frequencies
        byte_counts = defaultdict(int)
        for byte in data:
            byte_counts[byte] += 1
            
        # Calculate entropy
        entropy = 0.0
        data_len = len(data)
        for count in byte_counts.values():
            p = count / data_len
            if p > 0:
                entropy -= p * np.log2(p)
                
        return entropy
    
    def _get_time_since_last_operation(self, operator: str) -> float:
        """Get time since operator's last operation"""
        current_time = datetime.now().timestamp()
        
        for op in reversed(self.operation_history):
            if op.operator_address == operator:
                return current_time - op.timestamp
                
        return 86400.0  # Default to 1 day if no previous operation
    
    def _get_operations_in_window(self, operator: str, window_seconds: int) -> int:
        """Count operations by operator in time window"""
        cutoff_time = datetime.now().timestamp() - window_seconds
        
        count = 0
        for op in self.operation_history:
            if op.operator_address == operator and op.timestamp > cutoff_time:
                count += 1
                
        return count
    
    def _get_average_value(self, operator: str) -> float:
        """Get operator's historical average operation value"""
        values = [op.value_eth for op in self.operation_history 
                 if op.operator_address == operator]
        
        return np.mean(values) if values else 1.0
    
    def _get_cross_chain_frequency(self, operator: str, source_chain: int, target_chain: int) -> int:
        """Get frequency of specific cross-chain route for operator"""
        count = 0
        for op in self.operation_history:
            if (op.operator_address == operator and 
                op.source_chain_id == source_chain and 
                op.target_chain_id == target_chain):
                count += 1
                
        return count
    
    def _update_statistics(self, features: OperationFeatures):
        """Update running statistics"""
        operator = features.operator_address
        
        # Update operator profile
        if operator not in self.operator_profiles:
            self.operator_profiles[operator] = {
                'total_operations': 0,
                'total_value': 0.0,
                'avg_value': 0.0,
                'hourly_averages': defaultdict(float),
                'chain_preferences': defaultdict(int)
            }
        
        profile = self.operator_profiles[operator]
        profile['total_operations'] += 1
        profile['total_value'] += features.value_eth
        profile['avg_value'] = profile['total_value'] / profile['total_operations']
        profile['chain_preferences'][f"{features.source_chain_id}->{features.target_chain_id}"] += 1
    
    def _score_to_threat_level(self, score: float) -> ThreatLevel:
        """Convert numerical score to threat level"""
        if score >= 0.8:
            return ThreatLevel.CRITICAL
        elif score >= 0.6:
            return ThreatLevel.HIGH
        elif score >= 0.4:
            return ThreatLevel.MEDIUM
        else:
            return ThreatLevel.LOW
    
    def _generate_alert_id(self) -> str:
        """Generate unique alert ID"""
        timestamp = str(datetime.now().timestamp())
        return hashlib.sha256(timestamp.encode()).hexdigest()[:16]
    
    def _identify_anomalous_features(self, feature_vector: List[float]) -> Dict[str, float]:
        """Identify which features contribute most to anomaly"""
        feature_names = [
            'value_eth', 'gas_price', 'payload_size', 'time_since_last_op',
            'operations_in_window', 'value_ratio_to_avg', 'cross_chain_frequency',
            'payload_entropy', 'gas_efficiency', 'source_chain_id', 'target_chain_id'
        ]
        
        deviations = {}
        for i, (name, value) in enumerate(zip(feature_names, feature_vector)):
            historical_values = [self._features_to_vector(op)[i] for op in self.operation_history]
            if historical_values:
                mean_val = np.mean(historical_values)
                std_val = np.std(historical_values)
                if std_val > 0:
                    z_score = abs((value - mean_val) / std_val)
                    if z_score > 2:  # More than 2 standard deviations
                        deviations[name] = z_score
                        
        return deviations
    
    def _get_historical_context(self, features: OperationFeatures) -> Dict[str, Any]:
        """Get historical context for the operation"""
        operator_ops = [op for op in self.operation_history 
                       if op.operator_address == features.operator_address]
        
        return {
            'operator_total_operations': len(operator_ops),
            'operator_avg_value': np.mean([op.value_eth for op in operator_ops]) if operator_ops else 0,
            'operator_total_volume': sum([op.value_eth for op in operator_ops]),
            'first_seen': min([op.timestamp for op in operator_ops]) if operator_ops else features.timestamp
        }
    
    def _get_anomaly_recommendations(self, threat_level: ThreatLevel) -> List[str]:
        """Get recommended actions based on threat level"""
        if threat_level == ThreatLevel.CRITICAL:
            return [
                "Immediately halt operation",
                "Alert security team",
                "Require manual review",
                "Investigate operator account"
            ]
        elif threat_level == ThreatLevel.HIGH:
            return [
                "Delay operation execution",
                "Require additional verification",
                "Monitor closely",
                "Alert operations team"
            ]
        elif threat_level == ThreatLevel.MEDIUM:
            return [
                "Flag for review",
                "Monitor subsequent operations",
                "Consider rate limiting"
            ]
        else:
            return [
                "Log for analysis",
                "Continue monitoring"
            ]
    
    def _get_operator_hourly_average(self, operator: str) -> float:
        """Get operator's historical hourly average volume"""
        if operator in self.operator_profiles:
            return self.operator_profiles[operator].get('hourly_averages', {}).get('default', 1.0)
        return 1.0
    
    async def _trigger_emergency_response(self, alert: ThreatAlert):
        """Trigger emergency response for high-severity alerts"""
        logger.warning(f"CRITICAL ALERT: {alert.description}")
        
        # In a real system, this would:
        # 1. Notify security team
        # 2. Potentially halt operations
        # 3. Trigger automated responses
        # 4. Update security configurations
        
        if alert.threat_level == ThreatLevel.CRITICAL:
            logger.critical(f"CRITICAL THREAT DETECTED - Operation {alert.operation_id}")
    
    def get_threat_summary(self) -> Dict[str, Any]:
        """Get summary of current threat landscape"""
        recent_alerts = [alert for alert in self.threat_alerts 
                        if alert.timestamp > datetime.now() - timedelta(hours=24)]
        
        threat_counts = defaultdict(int)
        for alert in recent_alerts:
            threat_counts[alert.threat_type.value] += 1
        
        return {
            'total_alerts_24h': len(recent_alerts),
            'threat_breakdown': dict(threat_counts),
            'critical_alerts': len([a for a in recent_alerts if a.threat_level == ThreatLevel.CRITICAL]),
            'high_alerts': len([a for a in recent_alerts if a.threat_level == ThreatLevel.HIGH]),
            'average_confidence': np.mean([a.confidence_score for a in recent_alerts]) if recent_alerts else 0,
            'most_affected_chains': self._get_most_affected_chains(recent_alerts)
        }
    
    def _get_most_affected_chains(self, alerts: List[ThreatAlert]) -> Dict[int, int]:
        """Get chains most affected by threats"""
        chain_counts = defaultdict(int)
        for alert in alerts:
            for chain_id in alert.affected_chains:
                chain_counts[chain_id] += 1
        return dict(sorted(chain_counts.items(), key=lambda x: x[1], reverse=True)[:5])

# Factory function
def create_threat_detection_engine(config_path: str) -> AdvancedThreatDetectionEngine:
    """Create and initialize threat detection engine"""
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    return AdvancedThreatDetectionEngine(config.get('threat_detection', {}))

if __name__ == "__main__":
    # Example usage
    config = {
        'threat_detection': {
            'anomaly_threshold': 0.1,
            'min_operations_for_training': 100,
            'alert_cooldown_seconds': 300
        }
    }
    
    engine = AdvancedThreatDetectionEngine(config['threat_detection'])
    
    # Example operation
    operation = {
        'operation_id': 'op_12345',
        'timestamp': datetime.now().timestamp(),
        'source_chain_id': 1,
        'target_chain_id': 137,
        'value': 10**18,  # 1 ETH in wei
        'gas_price': 20000000000,  # 20 gwei
        'payload': b'\x12\x34\x56\x78',
        'operator_address': '${CONTRACT_ADDRESS}'
    }
    
    async def test_analysis():
        alerts = await engine.analyze_operation(operation)
        print(f"Generated {len(alerts)} alerts")
        for alert in alerts:
            print(f"- {alert.threat_type.value}: {alert.description}")
    
    asyncio.run(test_analysis())
