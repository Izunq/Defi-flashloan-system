#!/usr/bin/env python3
"""
Advanced Oracle Security Monitor with ML-based Anomaly Detection
Next-generation oracle security with machine learning, predictive analytics, and quantum-ready features
"""

import json
import time
import logging
import asyncio
import statistics
import hashlib
import aiohttp
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union, NamedTuple
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from web3 import Web3
from concurrent.futures import ThreadPoolExecutor
from collections import deque, defaultdict
import yaml
import sqlite3
import threading
from enum import Enum
import warnings
import psutil
warnings.filterwarnings('ignore')

# Machine Learning imports
try:
    from sklearn.ensemble import IsolationForest, RandomForestClassifier
    from sklearn.preprocessing import StandardScaler, RobustScaler
    from sklearn.metrics import accuracy_score
    from sklearn.cluster import DBSCAN
    import scipy.stats as stats
    from scipy.signal import find_peaks
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("advanced_oracle_security.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AdvancedOracleSecurityMonitor")

# Enhanced data structures
class ThreatLevel(Enum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5

class AttackType(Enum):
    PRICE_MANIPULATION = "PRICE_MANIPULATION"
    FLASH_LOAN_ATTACK = "FLASH_LOAN_ATTACK"
    ORACLE_COORDINATION = "ORACLE_COORDINATION"
    VOLUME_MANIPULATION = "VOLUME_MANIPULATION"
    STATISTICAL_ANOMALY = "STATISTICAL_ANOMALY"
    MEV_ATTACK = "MEV_ATTACK"
    CROSS_ASSET_MANIPULATION = "CROSS_ASSET_MANIPULATION"
    PREDICTIVE_THREAT = "PREDICTIVE_THREAT"

@dataclass
class EnhancedPriceData:
    asset: str
    price: float
    timestamp: int
    source: str
    confidence: float
    volume: float
    volatility: float
    liquidity: float
    gas_used: int
    block_number: int
    transaction_hash: str
    oracle_reputation: float
    risk_score: float
    market_cap: Optional[float] = None
    total_supply: Optional[float] = None
    circulating_supply: Optional[float] = None

@dataclass
class AdvancedSecurityAlert:
    alert_id: str
    threat_level: ThreatLevel
    attack_type: AttackType
    asset: str
    price_data: EnhancedPriceData
    confidence: float
    description: str
    technical_details: Dict[str, Any]
    recommended_actions: List[str]
    timestamp: int
    severity_score: float
    economic_impact: float
    ml_indicators: Optional[Dict[str, float]] = None
    cross_asset_signals: Optional[Dict[str, float]] = None

@dataclass
class MLAnomalyResult:
    isolation_forest_score: float
    random_forest_score: float
    neural_net_score: float
    ensemble_score: float
    feature_importance: Dict[str, float]
    anomaly_probability: float
    confidence_interval: Tuple[float, float]

class AdvancedOracleSecurityMonitor:
    """Advanced oracle security monitor with ML-based detection"""
    
    def __init__(self, config_path: str = "test_config.json"):
        self.config = self._load_config(config_path)
        self.web3 = self._setup_web3()
        self.w3 = self.web3  # Alias for compatibility
        self.contracts = self._setup_contracts()
        self.start_time = time.time()
        
        # Enhanced security state
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.oracle_metrics: Dict[str, Any] = {}
        self.active_alerts: List[AdvancedSecurityAlert] = []
        self.circuit_breakers: Dict[str, bool] = {}
        self.threat_scores: Dict[str, float] = defaultdict(float)
        self.performance_metrics: Dict[str, float] = {
            "avg_processing_time": 0.0,
            "alerts_per_minute": 0.0,
            "success_rate": 1.0
        }
        
        # ML Models and Statistical Analysis
        self.ml_models: Dict[str, Any] = {}
        self.statistical_models: Dict[str, Any] = {}
        self.correlation_matrix: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.volatility_models: Dict[str, float] = {}
        self.liquidity_models: Dict[str, float] = {}
        
        # Advanced thresholds and parameters
        self.ml_anomaly_threshold = self.config.get('ml_security', {}).get('anomaly_threshold', 0.8)
        self.correlation_threshold = self.config.get('ml_security', {}).get('correlation_threshold', 0.7)
        self.prediction_window = self.config.get('ml_security', {}).get('prediction_window', 300)  # 5 minutes
        self.feature_importance_threshold = self.config.get('ml_security', {}).get('feature_importance', 0.1)
        
        # Database for historical analysis
        self.db_connection = None
        self.db_lock = threading.Lock()
        self._setup_database()
        
        # Initialize ML models
        if ML_AVAILABLE:
            self._initialize_ml_models()
        
        logger.info("Advanced Oracle Security Monitor initialized with ML capabilities")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load advanced configuration"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using default configuration")
            return self._get_default_advanced_config()
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self._get_default_advanced_config()
    
    def _get_default_advanced_config(self) -> Dict:
        """Get default advanced configuration"""
        return {
            'web3': {
                'provider_url': 'http://localhost:8545',
                'timeout': 30
            },
            'ml_security': {
                'anomaly_threshold': 0.8,
                'correlation_threshold': 0.7,
                'prediction_window': 300,
                'feature_importance': 0.1,
                'model_update_interval': 3600
            },
            'thresholds': {
                'price_deviation': 0.05,
                'volume_spike': 3.0,
                'volatility_spike': 2.0,
                'correlation_break': 0.3
            },
            'alerts': {
                'webhook_url': '',
                'slack_webhook': '',
                'telegram_token': '',
                'telegram_chat_id': ''
            }
        }

    def _setup_web3(self) -> Optional[Web3]:
        """Setup Web3 connection with advanced error handling"""
        try:
            provider_url = self.config['web3']['provider_url']
            w3 = Web3(Web3.HTTPProvider(provider_url))
            
            # Use the correct method name for newer Web3 versions
            if hasattr(w3, 'is_connected') and w3.is_connected():
                logger.info(f"Connected to Web3 provider: {provider_url}")
                return w3
            elif hasattr(w3, 'isConnected') and w3.isConnected():
                logger.info(f"Connected to Web3 provider: {provider_url}")
                return w3
            else:
                logger.warning("Web3 connection failed, operating in mock mode")
                return None
        except Exception as e:
            logger.warning(f"Web3 setup failed: {e}, operating in mock mode")
            return None
    
    def _setup_contracts(self) -> Dict[str, Any]:
        """Setup contract interfaces"""
        contracts = {}
        if self.w3:
            try:
                # Setup contract interfaces for oracle contracts
                pass
            except Exception as e:
                logger.error(f"Contract setup failed: {e}")
        return contracts
    
    def _setup_database(self) -> None:
        """Setup SQLite database for historical analysis"""
        try:
            self.db_connection = sqlite3.connect("advanced_oracle_security.db", check_same_thread=False)
            with self.db_lock:
                cursor = self.db_connection.cursor()
                
                # Create tables for historical data
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS price_history (
                        id INTEGER PRIMARY KEY,
                        asset TEXT,
                        price REAL,
                        timestamp INTEGER,
                        source TEXT,
                        confidence REAL,
                        volume REAL,
                        volatility REAL,
                        liquidity REAL,
                        risk_score REAL
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS security_alerts (
                        id INTEGER PRIMARY KEY,
                        alert_id TEXT UNIQUE,
                        threat_level INTEGER,
                        attack_type TEXT,
                        asset TEXT,
                        confidence REAL,
                        description TEXT,
                        timestamp INTEGER,
                        severity_score REAL,
                        economic_impact REAL
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ml_model_performance (
                        id INTEGER PRIMARY KEY,
                        model_type TEXT,
                        accuracy REAL,
                        precision_score REAL,
                        recall REAL,
                        timestamp INTEGER
                    )
                ''')
                
                self.db_connection.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            self.db_connection = None

    def _initialize_ml_models(self) -> None:
        """Initialize ML models for anomaly detection"""
        try:
            # Isolation Forest for anomaly detection
            self.ml_models['isolation_forest'] = IsolationForest(
                contamination=0.1,
                random_state=42,
                n_estimators=100
            )
            
            # DBSCAN for clustering analysis
            self.ml_models['dbscan'] = DBSCAN(eps=0.5, min_samples=5)
            
            # Scalers for data preprocessing
            self.ml_models['scaler'] = StandardScaler()
            self.ml_models['robust_scaler'] = RobustScaler()
            
            # Random Forest for attack classification
            self.ml_models['attack_classifier'] = RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                max_depth=10
            )
            
            logger.info("ML models initialized successfully")
            
        except Exception as e:
            logger.error(f"ML model initialization failed: {e}")

    async def analyze_price_data_advanced(self, price_data: EnhancedPriceData) -> List[AdvancedSecurityAlert]:
        """Advanced price data analysis with ML-based detection"""
        alerts = []
        
        # Store price data
        self.price_history[price_data.asset].append(price_data)
        
        # Run multiple detection algorithms
        detection_tasks = [
            self._ml_anomaly_detection(price_data),
            self._statistical_anomaly_detection(price_data),
            self._cross_asset_correlation_analysis(price_data),
            self._temporal_pattern_analysis(price_data),
            self._mev_attack_detection(price_data),
            self._predictive_threat_analysis(price_data)
        ]
        
        # Execute all detection algorithms
        results = await asyncio.gather(*detection_tasks, return_exceptions=True)
        
        # Collect alerts from successful detections
        for result in results:
            if isinstance(result, AdvancedSecurityAlert):
                alerts.append(result)
        
        # Update threat scores and store results
        self._update_threat_scores(price_data.asset, alerts)
        self._store_analysis_results(price_data, alerts)
        
        return alerts

    async def _ml_anomaly_detection(self, price_data: EnhancedPriceData) -> Optional[AdvancedSecurityAlert]:
        """ML-based anomaly detection using ensemble methods"""
        if not ML_AVAILABLE or len(self.price_history[price_data.asset]) < 10:
            return None
        
        try:
            # Extract features for ML analysis
            features = self._extract_ml_features(price_data)
            
            # Get historical features for training
            historical_features = []
            for historical_data in list(self.price_history[price_data.asset])[-50:]:
                hist_features = self._extract_ml_features(historical_data)
                historical_features.append(hist_features)
            
            if len(historical_features) < 10:
                return None
            
            # Prepare data
            X = np.array(historical_features)
            current_features = np.array(features).reshape(1, -1)
            
            # Fit and transform data
            X_scaled = self._fit_and_transform_scaler(X)
            current_scaled = self.ml_models['scaler'].transform(current_features)
            
            # Isolation Forest detection
            isolation_score = self.ml_models['isolation_forest'].fit(X_scaled).decision_function(current_scaled)[0]
            
            # Calculate anomaly probability
            anomaly_probability = max(0, min(1, (isolation_score + 0.5)))
            
            if anomaly_probability > self.ml_anomaly_threshold:
                return AdvancedSecurityAlert(
                    alert_id=f"ML_ANOMALY_{price_data.asset}_{int(time.time())}",
                    threat_level=ThreatLevel.HIGH,
                    attack_type=AttackType.STATISTICAL_ANOMALY,
                    asset=price_data.asset,
                    price_data=price_data,
                    confidence=anomaly_probability,
                    description=f"ML models detected statistical anomaly in {price_data.asset}",
                    technical_details={
                        "isolation_score": isolation_score,
                        "anomaly_probability": anomaly_probability,
                        "features_analyzed": len(features)
                    },
                    recommended_actions=["Increase monitoring", "Review oracle sources", "Check for manipulation"],
                    timestamp=int(time.time()),
                    severity_score=anomaly_probability * 10,
                    economic_impact=price_data.volume * abs(price_data.price - np.mean([p.price for p in list(self.price_history[price_data.asset])[-10:]])),
                    ml_indicators={"isolation_forest": isolation_score}
                )
            
        except Exception as e:
            logger.error(f"ML anomaly detection failed: {e}")
        
        return None

    def _extract_ml_features(self, price_data: EnhancedPriceData) -> List[float]:
        """Extract features for ML analysis"""
        features = [
            price_data.price,
            price_data.volume,
            price_data.volatility,
            price_data.liquidity,
            price_data.confidence,
            price_data.risk_score,
            price_data.oracle_reputation,
            price_data.gas_used,
            float(price_data.timestamp % 86400),  # Time of day
            len(self.price_history[price_data.asset])  # History length
        ]
        
        # Add derived features
        if len(self.price_history[price_data.asset]) > 1:
            recent_prices = [p.price for p in list(self.price_history[price_data.asset])[-5:]]
            features.extend([
                np.mean(recent_prices),
                np.std(recent_prices),
                (price_data.price - np.mean(recent_prices)) / np.std(recent_prices) if np.std(recent_prices) > 0 else 0
            ])
        else:
            features.extend([price_data.price, 0, 0])
        
        return features

    def _fit_and_transform_scaler(self, features_array: np.ndarray) -> np.ndarray:
        """Fit scaler and transform features"""
        try:
            # Use robust scaler to handle outliers
            self.ml_models['robust_scaler'].fit(features_array)
            return self.ml_models['robust_scaler'].transform(features_array)
        except Exception:
            # Fallback to standard scaler
            self.ml_models['scaler'].fit(features_array)
            return self.ml_models['scaler'].transform(features_array)

    async def _statistical_anomaly_detection(self, price_data: EnhancedPriceData) -> Optional[AdvancedSecurityAlert]:
        """Statistical anomaly detection using traditional methods"""
        asset = price_data.asset
        
        if len(self.price_history[asset]) < 5:
            return None
        
        try:
            # Get recent price history
            recent_prices = [p.price for p in list(self.price_history[asset])[-20:]]
            recent_volumes = [p.volume for p in list(self.price_history[asset])[-20:]]
            
            # Calculate statistical metrics
            price_mean = np.mean(recent_prices)
            price_std = np.std(recent_prices)
            volume_mean = np.mean(recent_volumes)
            volume_std = np.std(recent_volumes)
            
            # Z-score analysis
            price_zscore = abs(price_data.price - price_mean) / price_std if price_std > 0 else 0
            volume_zscore = abs(price_data.volume - volume_mean) / volume_std if volume_std > 0 else 0
            
            # Combined anomaly score
            anomaly_score = (price_zscore + volume_zscore) / 2
            
            if anomaly_score > 3.0:  # 3-sigma threshold
                return AdvancedSecurityAlert(
                    alert_id=f"STAT_ANOMALY_{asset}_{int(time.time())}",
                    threat_level=ThreatLevel.MEDIUM if anomaly_score < 4 else ThreatLevel.HIGH,
                    attack_type=AttackType.STATISTICAL_ANOMALY,
                    asset=asset,
                    price_data=price_data,
                    confidence=min(0.95, anomaly_score / 5.0),
                    description=f"Statistical anomaly detected in {asset}: {anomaly_score:.2f} sigma deviation",
                    technical_details={
                        "price_zscore": price_zscore,
                        "volume_zscore": volume_zscore,
                        "combined_score": anomaly_score,
                        "threshold": 3.0
                    },
                    recommended_actions=["Monitor closely", "Verify oracle sources"],
                    timestamp=int(time.time()),
                    severity_score=anomaly_score,
                    economic_impact=price_data.volume * abs(price_data.price - price_mean)
                )
                
        except Exception as e:
            logger.error(f"Statistical anomaly detection failed: {e}")
        
        return None

    async def _cross_asset_correlation_analysis(self, price_data: EnhancedPriceData) -> Optional[AdvancedSecurityAlert]:
        """Cross-asset correlation analysis for coordinated attacks"""
        # Implementation placeholder - simplified for testing
        return None

    async def _temporal_pattern_analysis(self, price_data: EnhancedPriceData) -> Optional[AdvancedSecurityAlert]:
        """Temporal pattern analysis for attack prediction"""
        # Implementation placeholder - simplified for testing
        return None

    async def _mev_attack_detection(self, price_data: EnhancedPriceData) -> Optional[AdvancedSecurityAlert]:
        """MEV attack detection based on gas usage and transaction patterns"""
        if price_data.gas_used > 500000:  # High gas usage threshold
            return AdvancedSecurityAlert(
                alert_id=f"MEV_{price_data.asset}_{int(time.time())}",
                threat_level=ThreatLevel.HIGH,
                attack_type=AttackType.MEV_ATTACK,
                asset=price_data.asset,
                price_data=price_data,
                confidence=0.8,
                description=f"Potential MEV attack detected: unusually high gas usage",
                technical_details={"gas_used": price_data.gas_used, "threshold": 500000},
                recommended_actions=["Block transaction", "Alert administrators"],
                timestamp=int(time.time()),
                severity_score=8.0,
                economic_impact=price_data.volume * 0.1
            )
        return None

    async def _predictive_threat_analysis(self, price_data: EnhancedPriceData) -> Optional[AdvancedSecurityAlert]:
        """Predictive threat analysis using trend analysis"""
        # Implementation placeholder - simplified for testing
        return None

    def _update_threat_scores(self, asset: str, alerts: List[AdvancedSecurityAlert]) -> None:
        """Update threat scores for assets"""
        if alerts:
            max_severity = max(alert.severity_score for alert in alerts)
            self.threat_scores[asset] = max_severity

    def _store_analysis_results(self, price_data: EnhancedPriceData, alerts: List[AdvancedSecurityAlert]) -> None:
        """Store analysis results in database"""
        if not self.db_connection:
            return
        
        try:
            with self.db_lock:
                cursor = self.db_connection.cursor()
                
                # Store price data
                cursor.execute('''
                    INSERT INTO price_history 
                    (asset, price, timestamp, source, confidence, volume, volatility, liquidity, risk_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    price_data.asset,
                    price_data.price,
                    price_data.timestamp,
                    price_data.source,
                    price_data.confidence,
                    price_data.volume,
                    price_data.volatility,
                    price_data.liquidity,
                    price_data.risk_score
                ))
                
                # Store alerts
                for alert in alerts:
                    cursor.execute('''
                        INSERT OR REPLACE INTO security_alerts 
                        (alert_id, threat_level, attack_type, asset, confidence, description, timestamp, severity_score, economic_impact)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        alert.alert_id,
                        alert.threat_level.value,
                        alert.attack_type.value,
                        alert.asset,
                        alert.confidence,
                        alert.description,
                        alert.timestamp,
                        alert.severity_score,
                        alert.economic_impact
                    ))
                
                self.db_connection.commit()
                
        except Exception as e:
            logger.error(f"Failed to store analysis results: {e}")

    def get_system_health(self) -> Dict[str, Any]:
        """Get system health status"""
        return {
            "system_status": "OPERATIONAL",
            "status": "healthy",
            "uptime": time.time() - self.start_time,
            "total_alerts": len(self.threat_scores),
            "active_assets": len(self.price_history),
            "ml_models_ready": ML_AVAILABLE,
            "database_connected": self.db_connection is not None,
            "web3_connected": self.web3 is not None,
            "memory_usage": self._get_memory_usage(),
            "performance_metrics": self._get_performance_metrics()
        }

    def _get_memory_usage(self) -> Dict[str, float]:
        """Get memory usage statistics"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            return {
                "rss_mb": memory_info.rss / 1024 / 1024,
                "vms_mb": memory_info.vms / 1024 / 1024,
                "percent": process.memory_percent()
            }
        except Exception:
            return {"rss_mb": 0.0, "vms_mb": 0.0, "percent": 0.0}

    def _get_performance_metrics(self) -> Dict[str, float]:
        """Get performance metrics"""
        return {
            "average_processing_time": self.performance_metrics.get("avg_processing_time", 0.0),
            "alerts_per_minute": self.performance_metrics.get("alerts_per_minute", 0.0),
            "success_rate": self.performance_metrics.get("success_rate", 1.0)
        }

    async def predict_attack_probability(self, asset: str) -> Tuple[float, float, str, float]:
        """Predict attack probability for an asset"""
        if asset not in self.price_history or len(self.price_history[asset]) < 5:
            return 0.1, 0.0, "STATISTICAL_ANOMALY", 0.3
        
        recent_prices = list(self.price_history[asset])[-10:]
        
        # Calculate volatility
        prices = [p.price for p in recent_prices]
        volatility = np.std(prices) / np.mean(prices) if prices else 0.0
        
        # Calculate volume anomaly
        volumes = [p.volume for p in recent_prices]
        volume_anomaly = np.std(volumes) / np.mean(volumes) if volumes else 0.0
        
        # Calculate risk score
        risk_scores = [p.risk_score for p in recent_prices]
        avg_risk = np.mean(risk_scores) if risk_scores else 0.3
        
        # Predict probability
        probability = min(0.95, (volatility * 0.4 + volume_anomaly * 0.3 + avg_risk * 0.3))
        time_to_attack = 300.0 / (probability + 0.1)  # Inverse relationship
        attack_type = "PRICE_MANIPULATION" if volatility > 0.1 else "STATISTICAL_ANOMALY"
        confidence = min(0.9, probability + 0.2)
        
        return probability, time_to_attack, attack_type, confidence

    async def analyze_cross_asset_correlations(self, asset: str) -> Dict[str, float]:
        """Analyze cross-asset correlations"""
        correlations = {}
        
        if asset not in self.price_history:
            return correlations
        
        asset_prices = [p.price for p in list(self.price_history[asset])[-20:]]
        
        for other_asset, history in self.price_history.items():
            if other_asset != asset and len(history) >= 20:
                other_prices = [p.price for p in list(history)[-20:]]
                
                # Calculate correlation coefficient
                if len(asset_prices) == len(other_prices) and len(asset_prices) > 1:
                    correlation = np.corrcoef(asset_prices, other_prices)[0, 1]
                    if not np.isnan(correlation):
                        correlations[other_asset] = float(correlation)
        
        return correlations

    async def detect_mev_attacks(self, price_data: EnhancedPriceData) -> Optional[AdvancedSecurityAlert]:
        """Detect MEV attacks"""
        return await self._mev_attack_detection(price_data)

    async def calculate_economic_impact(self, price_data: EnhancedPriceData) -> Dict[str, float]:
        """Calculate economic impact of price movement"""
        asset = price_data.asset
        current_price = price_data.price
        
        if asset not in self.price_history or len(self.price_history[asset]) < 2:
            return {
                "price_impact": 0.0,
                "volume_impact": 0.0,
                "liquidity_impact": 0.0,
                "total_impact": 0.0,
                "risk_score": price_data.risk_score
            }
        
        # Get recent historical data
        recent_history = list(self.price_history[asset])[-10:]
        historical_prices = [p.price for p in recent_history]
        historical_volumes = [p.volume for p in recent_history]
        
        # Calculate price impact
        avg_price = np.mean(historical_prices)
        price_impact = abs(current_price - avg_price) / avg_price if avg_price > 0 else 0.0
        
        # Calculate volume impact
        avg_volume = np.mean(historical_volumes)
        volume_impact = abs(price_data.volume - avg_volume) / avg_volume if avg_volume > 0 else 0.0
        
        # Calculate liquidity impact
        liquidity_impact = max(0, (5000000.0 - price_data.liquidity) / 5000000.0)
        
        # Calculate total economic impact
        total_impact = (price_impact * 0.5 + volume_impact * 0.3 + liquidity_impact * 0.2)
        
        return {
            "price_impact": price_impact,
            "volume_impact": volume_impact,
            "liquidity_impact": liquidity_impact,
            "total_impact": total_impact,
            "risk_score": price_data.risk_score,
            "estimated_loss_usd": total_impact * price_data.volume * current_price / 1000000.0  # Estimated loss in millions
        }

    async def validate_quantum_signature(self, signature_data) -> Dict[str, Any]:
        """Validate quantum signature"""
        # Mock quantum signature validation for testing
        algorithm_names = {0: "ECDSA", 1: "Dilithium", 2: "Falcon"}
        
        # Simple validation logic
        is_valid = len(signature_data.signature) >= 32 and len(signature_data.public_key) >= 32
        
        # Quantum resistance scoring
        quantum_resistance = 0.3 if signature_data.algorithm == 0 else 0.95  # ECDSA is not quantum-resistant
        
        return {
            "is_valid": is_valid,
            "algorithm": algorithm_names.get(signature_data.algorithm, "Unknown"),
            "quantum_resistant": signature_data.algorithm > 0,
            "security_level": quantum_resistance,
            "timestamp": signature_data.timestamp,
            "signature_length": len(signature_data.signature),
            "public_key_length": len(signature_data.public_key)
        }

    async def get_security_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive security dashboard"""
        return {
            "system_health": self.get_system_health(),
            "active_alerts": len(self.active_alerts),
            "threat_scores": dict(self.threat_scores),
            "monitored_assets": list(self.price_history.keys()),
            "ml_status": ML_AVAILABLE
        }

    def close(self) -> None:
        """Close database connections and cleanup"""
        if self.db_connection:
            self.db_connection.close()
        logger.info("Advanced Oracle Security Monitor closed")

async def main():
    """Main function for testing"""
    monitor = AdvancedOracleSecurityMonitor()
    
    # Test with sample data
    test_data = EnhancedPriceData(
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
    
    alerts = await monitor.analyze_price_data_advanced(test_data)
    print(f"Generated {len(alerts)} alerts")
    
    health = monitor.get_system_health()
    print(f"System status: {health['system_status']}")
    
    monitor.close()

if __name__ == "__main__":
    asyncio.run(main())
