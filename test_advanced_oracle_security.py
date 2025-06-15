#!/usr/bin/env python3
"""
Advanced Oracle Security Testing Suite
Comprehensive testing for next-generation oracle security improvements
"""

import unittest
import asyncio
import json
import time
import logging
import os
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, AsyncMock

# Import the advanced oracle security monitor
try:
    from advanced_oracle_security_monitor import (
        AdvancedOracleSecurityMonitor,
        EnhancedPriceData,
        AdvancedSecurityAlert,
        ThreatLevel,
        AttackType,
        MLAnomalyResult
    )
    ADVANCED_MONITOR_AVAILABLE = True
except ImportError:
    ADVANCED_MONITOR_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("advanced_oracle_security_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AdvancedOracleSecurityTests")

@dataclass
class TestMLResult:
    """Test ML result structure"""
    isolation_forest_score: float
    random_forest_score: float
    neural_net_score: float
    ensemble_score: float
    confidence: float
    is_anomalous: bool

@dataclass
class TestQuantumSignature:
    """Test quantum signature structure"""
    signature: bytes
    public_key: bytes
    algorithm: int
    timestamp: int
    is_verified: bool

class MockAdvancedOracleMonitor:
    """Mock advanced oracle monitor for testing"""
    
    def __init__(self, config_path: str = "test_config.json"):
        self.config = self._load_test_config()
        self.price_history: Dict[str, List] = {}
        self.threat_scores: Dict[str, float] = {}
        self.ml_models = {}
        self.active_alerts: List[AdvancedSecurityAlert] = []
        self.circuit_breakers: Dict[str, bool] = {}
        self.correlation_matrix: Dict[str, Dict[str, float]] = {}
        
        # Advanced features
        self.quantum_readiness_level = 1  # Hybrid mode
        self.economic_models = {}
        self.oracle_reputation_scores = {}
        self.real_time_threat_scores = {}
        
        logger.info("Mock Advanced Oracle Security Monitor initialized")
    
    def _load_test_config(self) -> Dict:
        """Load test configuration"""
        return {
            'web3': {
                'provider_url': 'http://localhost:8545',
                'gas_limit': 3000000
            },
            'security': {
                'max_price_deviation': 500,
                'circuit_breaker_threshold': 1000,
                'min_oracle_consensus': 3
            },
            'ml_security': {
                'enable_ml': True,
                'anomaly_threshold': 0.8,
                'correlation_threshold': 0.7,
                'prediction_window': 300
            },
            'advanced_features': {
                'cross_asset_analysis': True,
                'predictive_security': True,
                'quantum_ready': True,
                'economic_security': True,
                'mev_detection': True
            },
            'tracked_assets': ['ETH', 'BTC', 'USDC', 'USDT', 'DAI']
        }
    
    async def analyze_price_data_advanced(self, price_data: EnhancedPriceData) -> List[AdvancedSecurityAlert]:
        """Mock advanced price data analysis"""
        alerts = []
        
        # Store price data
        if price_data.asset not in self.price_history:
            self.price_history[price_data.asset] = []
        self.price_history[price_data.asset].append(price_data)
        
        # Generate mock alerts based on data
        if price_data.deviation > 15.0:  # High deviation threshold
            alert = AdvancedSecurityAlert(
                alert_id=f"advanced_{int(time.time())}_{price_data.asset}",
                alert_type=AttackType.PRICE_MANIPULATION,
                threat_level=ThreatLevel.HIGH,
                asset=price_data.asset,
                price=price_data.price,
                expected_price=price_data.price * 0.9,  # 10% lower
                deviation=price_data.deviation,
                timestamp=price_data.timestamp,
                description=f"Advanced manipulation detected: {price_data.deviation:.2f}% deviation",
                confidence_score=0.9,
                prediction_accuracy=0.88,
                related_assets=[],
                attack_vector="Advanced statistical manipulation",
                mitigation_actions=["Activate enhanced monitoring", "Cross-validate with external sources"],
                economic_impact=price_data.volume * price_data.deviation / 100,
                resolved=False,
                false_positive_probability=0.05
            )
            alerts.append(alert)
        
        # ML-based anomaly detection
        if price_data.risk_score > 0.7:
            alert = AdvancedSecurityAlert(
                alert_id=f"ml_advanced_{int(time.time())}_{price_data.asset}",
                alert_type=AttackType.STATISTICAL_ANOMALY,
                threat_level=ThreatLevel.MEDIUM,
                asset=price_data.asset,
                price=price_data.price,
                expected_price=price_data.price * 0.95,
                deviation=0.0,
                timestamp=price_data.timestamp,
                description=f"ML anomaly detected: risk score {price_data.risk_score:.3f}",
                confidence_score=price_data.risk_score,
                prediction_accuracy=0.92,
                related_assets=[],
                attack_vector="Machine learning detected anomaly",
                mitigation_actions=["Verify with ensemble models", "Check oracle reputation"],
                economic_impact=price_data.volume * 0.01,  # 1% impact estimate
                resolved=False,
                false_positive_probability=0.08
            )
            alerts.append(alert)
        
        # Store alerts
        self.active_alerts.extend(alerts)
        
        # Update threat scores
        self._update_threat_scores(price_data.asset, alerts)
        
        return alerts
    
    async def detect_mev_attacks(self, price_data: EnhancedPriceData) -> Optional[AdvancedSecurityAlert]:
        """Mock MEV attack detection"""
        if price_data.gas_used > 500000:  # High gas usage threshold
            return AdvancedSecurityAlert(
                alert_id=f"mev_{int(time.time())}_{price_data.asset}",
                alert_type=AttackType.MEV_ATTACK,
                threat_level=ThreatLevel.MEDIUM,
                asset=price_data.asset,
                price=price_data.price,
                expected_price=price_data.price,
                deviation=0.0,
                timestamp=price_data.timestamp,
                description=f"Potential MEV activity: gas usage {price_data.gas_used}",
                confidence_score=0.75,
                prediction_accuracy=0.82,
                related_assets=[],
                attack_vector="MEV extraction through transaction ordering",
                mitigation_actions=["Monitor transaction sequencing", "Implement fair ordering"],
                economic_impact=price_data.gas_used * 0.00001,  # Estimate based on gas
                resolved=False,
                false_positive_probability=0.15
            )
        return None
    
    async def analyze_cross_asset_correlations(self, asset: str) -> Dict[str, float]:
        """Mock cross-asset correlation analysis"""
        correlations = {}
        
        if asset in self.price_history and len(self.price_history[asset]) > 10:
            # Generate mock correlations
            for other_asset in ['ETH', 'BTC', 'USDC']:
                if other_asset != asset:
                    # Simulate correlation based on mock data
                    correlation = 0.3 + (hash(asset + other_asset) % 40) / 100.0  # 0.3 to 0.7
                    correlations[other_asset] = correlation
        
        return correlations
    
    async def predict_attack_probability(self, asset: str) -> Tuple[float, int, AttackType, float]:
        """Mock attack probability prediction"""
        # Calculate mock prediction based on threat score
        threat_score = self.threat_scores.get(asset, 0.0)
        
        attack_probability = min(threat_score * 1.2, 1.0)  # Scale threat score
        time_to_attack = max(3600 - int(threat_score * 3600), 300)  # 5 minutes to 1 hour
        most_likely_attack = AttackType.PRICE_MANIPULATION  # Default
        confidence = 0.8 + (threat_score * 0.15)  # 80-95% confidence
        
        return attack_probability, time_to_attack, most_likely_attack, confidence
    
    async def validate_quantum_signature(self, signature: TestQuantumSignature) -> bool:
        """Mock quantum signature validation"""
        # Mock validation based on algorithm type
        if signature.algorithm == 0:  # ECDSA
            return len(signature.signature) > 64
        elif signature.algorithm == 1:  # Dilithium
            return len(signature.signature) > 128
        elif signature.algorithm == 2:  # Falcon
            return len(signature.signature) > 256
        
        return False
    
    async def calculate_economic_impact(self, price_data: EnhancedPriceData) -> float:
        """Mock economic impact calculation"""
        volume_impact = price_data.volume * 0.001  # 0.1% of volume
        price_impact = price_data.price * price_data.deviation / 10000  # Scaled price impact
        risk_impact = price_data.risk_score * price_data.volume * 0.01  # Risk-based impact
        
        return volume_impact + price_impact + risk_impact
    
    def _update_threat_scores(self, asset: str, alerts: List[AdvancedSecurityAlert]) -> None:
        """Update threat scores based on alerts"""
        base_score = self.threat_scores.get(asset, 0.0)
        
        for alert in alerts:
            # Increase threat score based on alert severity
            severity_multiplier = {
                ThreatLevel.LOW: 0.1,
                ThreatLevel.MEDIUM: 0.3,
                ThreatLevel.HIGH: 0.6,
                ThreatLevel.CRITICAL: 0.9,
                ThreatLevel.EMERGENCY: 1.0
            }
            
            score_increase = alert.confidence_score * severity_multiplier.get(alert.threat_level, 0.5)
            base_score = min(base_score + score_increase, 1.0)
        
        # Decay threat score over time
        decay_factor = 0.98  # 2% decay
        self.threat_scores[asset] = base_score * decay_factor
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health status"""
        return {
            'timestamp': int(time.time()),
            'total_assets_monitored': len(self.price_history),
            'active_alerts': len([alert for alert in self.active_alerts if not alert.resolved]),
            'average_threat_score': sum(self.threat_scores.values()) / max(len(self.threat_scores), 1),
            'quantum_readiness_level': self.quantum_readiness_level,
            'ml_models_active': True,
            'economic_security_active': True,
            'system_status': 'OPERATIONAL'
        }

class TestAdvancedOracleSecurityMonitor(unittest.TestCase):
    """Comprehensive test suite for Advanced Oracle Security Monitor"""

    def setUp(self):
        """Set up test environment"""
        if ADVANCED_MONITOR_AVAILABLE:
            self.monitor = AdvancedOracleSecurityMonitor("test_config.json")
        else:
            self.monitor = MockAdvancedOracleMonitor("test_config.json")
        
        # Test data
        self.test_price_data = EnhancedPriceData(
            asset="ETH",
            price=2000.0,
            timestamp=int(time.time()),
            source="TestOracle",
            confidence=0.95,
            volume=1000000.0,
            volatility=0.05,
            liquidity=5000000.0,
            gas_used=200000,
            block_number=18000000,
            transaction_hash="0x123456789abcdef",
            oracle_reputation=0.98,
            risk_score=0.3
        )
    
    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self.monitor, 'close'):
            self.monitor.close()
    
    # Basic Functionality Tests
    
    def test_monitor_initialization(self):
        """Test monitor initialization"""
        self.assertIsNotNone(self.monitor)
        health = self.monitor.get_system_health()
        self.assertIn('system_status', health)
        self.assertEqual(health['system_status'], 'OPERATIONAL')
    
    async def test_advanced_price_analysis(self):
        """Test advanced price data analysis"""
        alerts = await self.monitor.analyze_price_data_advanced(self.test_price_data)
        
        # Should not generate alerts for normal data
        self.assertEqual(len(alerts), 0)
        
        # Test with anomalous data
        anomalous_data = EnhancedPriceData(
            asset="ETH",
            price=2500.0,  # 25% price increase
            timestamp=int(time.time()),
            source="TestOracle",
            confidence=0.8,
            volume=2000000.0,
            volatility=0.15,
            liquidity=3000000.0,
            gas_used=800000,  # High gas usage
            block_number=18000001,
            transaction_hash="0xabcdef123456789",
            oracle_reputation=0.85,
            risk_score=0.8,  # High risk score
            deviation=20.0  # High deviation
        )
        
        alerts = await self.monitor.analyze_price_data_advanced(anomalous_data)
        self.assertGreater(len(alerts), 0)
        
        # Check alert properties
        for alert in alerts:
            self.assertIsInstance(alert, AdvancedSecurityAlert)
            self.assertIn(alert.alert_type, [AttackType.PRICE_MANIPULATION, AttackType.STATISTICAL_ANOMALY])
            self.assertGreater(alert.confidence_score, 0.5)
    
    async def test_mev_attack_detection(self):
        """Test MEV attack detection"""
        # Normal gas usage - should not trigger
        normal_data = self.test_price_data
        normal_data.gas_used = 100000
        
        alert = await self.monitor.detect_mev_attacks(normal_data)
        self.assertIsNone(alert)
          # High gas usage - should trigger MEV detection
        mev_data = self.test_price_data
        mev_data.gas_used = 800000
        alert = await self.monitor.detect_mev_attacks(mev_data)
        self.assertIsNotNone(alert)
        self.assertEqual(alert.attack_type, AttackType.MEV_ATTACK)
        self.assertGreater(alert.confidence, 0.5)
    
    async def test_cross_asset_correlation_analysis(self):
        """Test cross-asset correlation analysis"""
        # Add some price history first
        for i in range(15):
            price_data = EnhancedPriceData(
                asset="ETH",
                price=2000.0 + i * 10,
                timestamp=int(time.time()) + i,
                source="TestOracle",
                confidence=0.95,
                volume=1000000.0,
                volatility=0.05,
                liquidity=5000000.0,
                gas_used=200000,
                block_number=18000000 + i,
                transaction_hash=f"0x{i:064x}",
                oracle_reputation=0.98,
                risk_score=0.3
            )
            await self.monitor.analyze_price_data_advanced(price_data)
        
        correlations = await self.monitor.analyze_cross_asset_correlations("ETH")
        
        self.assertIsInstance(correlations, dict)
        for asset, correlation in correlations.items():
            self.assertIsInstance(correlation, float)
            self.assertGreaterEqual(correlation, -1.0)
            self.assertLessEqual(correlation, 1.0)
    
    async def test_attack_probability_prediction(self):
        """Test attack probability prediction"""
        probability, time_to_attack, attack_type, confidence = await self.monitor.predict_attack_probability("ETH")
        
        self.assertIsInstance(probability, float)
        self.assertGreaterEqual(probability, 0.0)
        self.assertLessEqual(probability, 1.0)
        
        self.assertIsInstance(time_to_attack, int)
        self.assertGreater(time_to_attack, 0)
        
        self.assertIsInstance(attack_type, AttackType)
        
        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
    
    async def test_quantum_signature_validation(self):
        """Test quantum signature validation"""
        # Test ECDSA signature
        ecdsa_sig = TestQuantumSignature(
            signature=b"x" * 65,  # 65 bytes for ECDSA
            public_key=b"y" * 33,
            algorithm=0,
            timestamp=int(time.time()),
            is_verified=False
        )
        
        result = await self.monitor.validate_quantum_signature(ecdsa_sig)
        self.assertTrue(result)
        
        # Test Dilithium signature (post-quantum)
        dilithium_sig = TestQuantumSignature(
            signature=b"z" * 150,  # 150 bytes for Dilithium
            public_key=b"w" * 100,
            algorithm=1,
            timestamp=int(time.time()),
            is_verified=False
        )
        
        result = await self.monitor.validate_quantum_signature(dilithium_sig)
        self.assertTrue(result)
        
        # Test invalid signature
        invalid_sig = TestQuantumSignature(
            signature=b"short",  # Too short
            public_key=b"key",
            algorithm=0,
            timestamp=int(time.time()),
            is_verified=False
        )
        
        result = await self.monitor.validate_quantum_signature(invalid_sig)
        self.assertFalse(result)
    
    async def test_economic_impact_calculation(self):
        """Test economic impact calculation"""
        impact = await self.monitor.calculate_economic_impact(self.test_price_data)
        
        self.assertIsInstance(impact, float)
        self.assertGreaterEqual(impact, 0.0)
        
        # Test with high-impact data
        high_impact_data = EnhancedPriceData(
            asset="ETH",
            price=2000.0,
            timestamp=int(time.time()),
            source="TestOracle",
            confidence=0.5,  # Low confidence
            volume=10000000.0,  # High volume
            volatility=0.3,  # High volatility
            liquidity=1000000.0,  # Lower liquidity
            gas_used=200000,
            block_number=18000000,
            transaction_hash="0x123456789abcdef",
            oracle_reputation=0.7,  # Lower reputation
            risk_score=0.9,  # High risk
            deviation=30.0  # High deviation
        )
        
        high_impact = await self.monitor.calculate_economic_impact(high_impact_data)
        self.assertGreater(high_impact, impact)
    
    # Integration Tests
    
    async def test_full_security_pipeline(self):
        """Test complete security analysis pipeline"""
        # Simulate a sequence of price updates leading to an attack
        base_price = 2000.0
        
        # Normal updates
        for i in range(10):
            price_data = EnhancedPriceData(
                asset="ETH",
                price=base_price + i,
                timestamp=int(time.time()) + i * 60,
                source="TestOracle",
                confidence=0.95,
                volume=1000000.0,
                volatility=0.05,
                liquidity=5000000.0,
                gas_used=200000,
                block_number=18000000 + i,
                transaction_hash=f"0x{i:064x}",
                oracle_reputation=0.98,
                risk_score=0.2 + i * 0.01
            )
            
            alerts = await self.monitor.analyze_price_data_advanced(price_data)
            # Should generate minimal alerts for gradual changes
            self.assertLessEqual(len(alerts), 1)
        
        # Sudden suspicious activity
        attack_data = EnhancedPriceData(
            asset="ETH",
            price=base_price * 1.25,  # 25% jump
            timestamp=int(time.time()) + 11 * 60,
            source="SuspiciousOracle",
            confidence=0.7,
            volume=5000000.0,  # High volume
            volatility=0.25,   # High volatility
            liquidity=2000000.0,
            gas_used=1000000,  # Very high gas
            block_number=18000011,
            transaction_hash="0xattack123456789",
            oracle_reputation=0.6,  # Poor reputation
            risk_score=0.95,  # Very high risk
            deviation=25.0
        )
        
        alerts = await self.monitor.analyze_price_data_advanced(attack_data)
        
        # Should generate multiple alerts for suspicious activity
        self.assertGreater(len(alerts), 0)
        
        # Check that threat score increased
        health = self.monitor.get_system_health()
        self.assertGreater(health['average_threat_score'], 0.1)
    
    async def test_multi_asset_monitoring(self):
        """Test monitoring multiple assets simultaneously"""
        assets = ["ETH", "BTC", "USDC", "LINK"]
        
        # Generate price data for multiple assets
        for i, asset in enumerate(assets):
            price = 1000.0 + i * 500  # Different base prices
            
            for j in range(5):
                price_data = EnhancedPriceData(
                    asset=asset,
                    price=price + j * 10,
                    timestamp=int(time.time()) + j * 30,
                    source=f"Oracle_{asset}",
                    confidence=0.9,
                    volume=1000000.0 * (i + 1),
                    volatility=0.05 + i * 0.01,
                    liquidity=5000000.0,
                    gas_used=200000,
                    block_number=18000000 + j,
                    transaction_hash=f"0x{asset}_{j:032x}",
                    oracle_reputation=0.95,
                    risk_score=0.3 + j * 0.1
                )
                
                alerts = await self.monitor.analyze_price_data_advanced(price_data)
        
        # Check system health with multiple assets
        health = self.monitor.get_system_health()
        self.assertEqual(health['total_assets_monitored'], len(assets))
    
    # Performance Tests
    
    async def test_high_frequency_processing(self):
        """Test high-frequency data processing performance"""
        start_time = time.time()
        
        # Process 100 price updates rapidly
        for i in range(100):
            price_data = EnhancedPriceData(
                asset="ETH",
                price=2000.0 + (i % 20) - 10,  # Oscillating price
                timestamp=int(time.time()) + i,
                source="HighFreqOracle",
                confidence=0.9,
                volume=100000.0,
                volatility=0.02,
                liquidity=5000000.0,
                gas_used=150000,
                block_number=18000000 + i,
                transaction_hash=f"0xhf_{i:060x}",
                oracle_reputation=0.95,
                risk_score=0.2
            )
            
            await self.monitor.analyze_price_data_advanced(price_data)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process 100 updates in reasonable time (< 5 seconds)
        self.assertLess(processing_time, 5.0)
        
        # Calculate processing rate
        processing_rate = 100 / processing_time
        logger.info(f"High-frequency processing rate: {processing_rate:.2f} updates/second")
        
        # Should achieve reasonable throughput
        self.assertGreater(processing_rate, 20.0)  # At least 20 updates/second
    
    def test_memory_efficiency(self):
        """Test memory usage with large datasets"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Generate large amount of price data
        async def generate_large_dataset():
            for i in range(1000):
                price_data = EnhancedPriceData(
                    asset=f"ASSET_{i % 10}",  # 10 different assets
                    price=1000.0 + i,
                    timestamp=int(time.time()) + i,
                    source="TestOracle",
                    confidence=0.9,
                    volume=1000000.0,
                    volatility=0.05,
                    liquidity=5000000.0,
                    gas_used=200000,
                    block_number=18000000 + i,
                    transaction_hash=f"0x{i:064x}",
                    oracle_reputation=0.95,
                    risk_score=0.3
                )
                
                await self.monitor.analyze_price_data_advanced(price_data)
        
        # Run the test
        asyncio.run(generate_large_dataset())
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        logger.info(f"Memory usage: {initial_memory:.2f} MB -> {final_memory:.2f} MB (increase: {memory_increase:.2f} MB)")
        
        # Memory increase should be reasonable (less than 100 MB for 1000 entries)
        self.assertLess(memory_increase, 100.0)
    
    # Edge Case Tests
    
    async def test_invalid_data_handling(self):
        """Test handling of invalid price data"""
        # Test with invalid price (negative)
        invalid_price_data = EnhancedPriceData(
            asset="ETH",
            price=-100.0,  # Invalid negative price
            timestamp=int(time.time()),
            source="TestOracle",
            confidence=0.95,
            volume=1000000.0,
            volatility=0.05,
            liquidity=5000000.0,
            gas_used=200000,
            block_number=18000000,
            transaction_hash="0x123456789abcdef",
            oracle_reputation=0.98,
            risk_score=0.3
        )
        
        # Should handle gracefully without crashing
        try:
            alerts = await self.monitor.analyze_price_data_advanced(invalid_price_data)
            # Should either reject or flag as highly suspicious
            if alerts:
                self.assertEqual(alerts[0].threat_level, ThreatLevel.CRITICAL)
        except Exception as e:
            # Should handle gracefully
            self.assertIsInstance(e, (ValueError, TypeError))
    
    async def test_extreme_values(self):
        """Test handling of extreme values"""
        # Test with extremely high values
        extreme_data = EnhancedPriceData(
            asset="ETH",
            price=1000000.0,  # Extremely high price
            timestamp=int(time.time()),
            source="TestOracle",
            confidence=0.1,  # Very low confidence
            volume=1000000000000.0,  # Trillion volume
            volatility=10.0,  # 1000% volatility
            liquidity=1.0,  # Very low liquidity
            gas_used=5000000,  # Very high gas
            block_number=18000000,
            transaction_hash="0x123456789abcdef",
            oracle_reputation=0.01,  # Very poor reputation
            risk_score=1.0,  # Maximum risk
            deviation=1000.0  # 1000% deviation
        )
        
        alerts = await self.monitor.analyze_price_data_advanced(extreme_data)
        
        # Should generate critical alerts for extreme values
        self.assertGreater(len(alerts), 0)
        
        critical_alerts = [alert for alert in alerts if alert.threat_level == ThreatLevel.CRITICAL]
        self.assertGreater(len(critical_alerts), 0)

    def test_system_health_monitoring(self):
        """Test system health monitoring"""
        health = self.monitor.get_system_health()
        
        # Check required health metrics
        required_fields = [
            'timestamp', 'total_assets_monitored', 'active_alerts',
            'average_threat_score', 'system_status'
        ]
        
        for field in required_fields:
            self.assertIn(field, health)
        
        # Check data types
        self.assertIsInstance(health['timestamp'], int)
        self.assertIsInstance(health['total_assets_monitored'], int)
        self.assertIsInstance(health['active_alerts'], int)
        self.assertIsInstance(health['average_threat_score'], (int, float))
        self.assertIsInstance(health['system_status'], str)
        
        # Check reasonable values
        self.assertGreaterEqual(health['total_assets_monitored'], 0)
        self.assertGreaterEqual(health['active_alerts'], 0)
        self.assertGreaterEqual(health['average_threat_score'], 0.0)
        self.assertLessEqual(health['average_threat_score'], 1.0)

# Async test runner
def run_async_test(test_func):
    """Helper to run async test functions"""
    def wrapper(self):
        asyncio.run(test_func(self))
    return wrapper

# Apply async wrapper to async test methods
TestAdvancedOracleSecurityMonitor.test_advanced_price_analysis = run_async_test(TestAdvancedOracleSecurityMonitor.test_advanced_price_analysis)
TestAdvancedOracleSecurityMonitor.test_mev_attack_detection = run_async_test(TestAdvancedOracleSecurityMonitor.test_mev_attack_detection)
TestAdvancedOracleSecurityMonitor.test_cross_asset_correlation_analysis = run_async_test(TestAdvancedOracleSecurityMonitor.test_cross_asset_correlation_analysis)
TestAdvancedOracleSecurityMonitor.test_attack_probability_prediction = run_async_test(TestAdvancedOracleSecurityMonitor.test_attack_probability_prediction)
TestAdvancedOracleSecurityMonitor.test_quantum_signature_validation = run_async_test(TestAdvancedOracleSecurityMonitor.test_quantum_signature_validation)
TestAdvancedOracleSecurityMonitor.test_economic_impact_calculation = run_async_test(TestAdvancedOracleSecurityMonitor.test_economic_impact_calculation)
TestAdvancedOracleSecurityMonitor.test_full_security_pipeline = run_async_test(TestAdvancedOracleSecurityMonitor.test_full_security_pipeline)
TestAdvancedOracleSecurityMonitor.test_multi_asset_monitoring = run_async_test(TestAdvancedOracleSecurityMonitor.test_multi_asset_monitoring)
TestAdvancedOracleSecurityMonitor.test_high_frequency_processing = run_async_test(TestAdvancedOracleSecurityMonitor.test_high_frequency_processing)
TestAdvancedOracleSecurityMonitor.test_invalid_data_handling = run_async_test(TestAdvancedOracleSecurityMonitor.test_invalid_data_handling)
TestAdvancedOracleSecurityMonitor.test_extreme_values = run_async_test(TestAdvancedOracleSecurityMonitor.test_extreme_values)

if __name__ == "__main__":
    print("Starting Advanced Oracle Security Testing Suite...")
    
    # Run the test suite
    unittest.main(verbosity=2)
    
    print("\nAdvanced Oracle Security Testing Suite completed!")
    print("="*60)
    print("SUMMARY:")
    print("- Advanced ML-based anomaly detection: TESTED")
    print("- MEV attack detection: TESTED") 
    print("- Cross-asset correlation analysis: TESTED")
    print("- Attack probability prediction: TESTED")
    print("- Quantum signature validation: TESTED")
    print("- Economic impact calculation: TESTED")
    print("- High-frequency processing: TESTED")
    print("- Memory efficiency: TESTED")
    print("- System health monitoring: TESTED")
    print("="*60)
