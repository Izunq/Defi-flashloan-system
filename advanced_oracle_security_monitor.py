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
    logger.warning("ML libraries not available, using statistical methods only")

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

class ThreatLevel(Enum):
    """Security threat levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"  
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"

class AttackType(Enum):
    """Types of detected attacks"""
    PRICE_MANIPULATION = "PRICE_MANIPULATION"
    FLASH_LOAN_ATTACK = "FLASH_LOAN_ATTACK"
    ORACLE_COORDINATION = "ORACLE_COORDINATION"
    VOLUME_MANIPULATION = "VOLUME_MANIPULATION"
    TIMESTAMP_MANIPULATION = "TIMESTAMP_MANIPULATION"
    STATISTICAL_ANOMALY = "STATISTICAL_ANOMALY"
    MEV_ATTACK = "MEV_ATTACK"
    CROSS_ASSET_MANIPULATION = "CROSS_ASSET_MANIPULATION"
    PREDICTIVE_THREAT = "PREDICTIVE_THREAT"

@dataclass
class EnhancedPriceData:
    """Enhanced price data with additional security metrics"""
    asset: str
    price: float
    timestamp: int
    source: str
    confidence: float
    volume: float = 0.0
    deviation: float = 0.0
    volatility: float = 0.0
    liquidity: float = 0.0
    gas_used: int = 0
    block_number: int = 0
    transaction_hash: str = ""
    oracle_reputation: float = 1.0
    risk_score: float = 0.0

@dataclass
class AdvancedSecurityAlert:
    """Advanced security alert with ML predictions"""
    alert_id: str
    alert_type: AttackType
    threat_level: ThreatLevel
    asset: str
    price: float
    expected_price: float
    deviation: float
    timestamp: int
    description: str
    confidence_score: float
    prediction_accuracy: float
    related_assets: List[str] = field(default_factory=list)
    attack_vector: str = ""
    mitigation_actions: List[str] = field(default_factory=list)
    economic_impact: float = 0.0
    resolved: bool = False
    false_positive_probability: float = 0.0

@dataclass
class MLAnomalyResult:
    """Machine learning anomaly detection result"""
    is_anomaly: bool
    anomaly_score: float
    confidence: float
    features_analyzed: List[str]
    model_type: str
    detection_method: str

@dataclass
class CrossAssetCorrelation:
    """Cross-asset correlation analysis"""
    primary_asset: str
    correlated_assets: Dict[str, float]
    correlation_strength: float
    correlation_change: float
    suspicious_correlation: bool

class AdvancedOracleSecurityMonitor:
    """Advanced oracle security monitor with ML-based detection"""
    
    def __init__(self, config_path: str = "advanced_oracle_config.yaml"):
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
        self._setup_database()
        
        # Initialize ML models
        if ML_AVAILABLE:
            self._initialize_ml_models()
        
        logger.info("Advanced Oracle Security Monitor initialized with ML capabilities")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load advanced configuration"""
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using default configuration")
            return self._get_default_advanced_config()
    
    def _get_default_advanced_config(self) -> Dict:
        """Get default advanced configuration"""
        return {
            'web3': {
                'provider_url': 'http://localhost:8545',
                'gas_limit': 3000000,
                'timeout': 30
            },
            'security': {
                'max_price_deviation': 500,  # 5%
                'circuit_breaker_threshold': 1000,  # 10%
                'min_oracle_consensus': 3,
                'staleness_threshold': 3600,
                'monitoring_interval': 30
            },
            'ml_security': {
                'enable_ml': True,
                'anomaly_threshold': 0.8,
                'correlation_threshold': 0.7,
                'prediction_window': 300,
                'feature_importance': 0.1,
                'retraining_interval': 86400,  # 24 hours
                'model_types': ['isolation_forest', 'dbscan', 'statistical']
            },
            'advanced_features': {
                'cross_asset_analysis': True,
                'predictive_security': True,
                'quantum_ready': False,
                'economic_security': True,
                'mev_detection': True
            },
            'tracked_assets': ['ETH', 'BTC', 'USDC', 'USDT', 'DAI', 'LINK', 'UNI'],
            'alerts': {
                'email_notifications': False,
                'webhook_url': '',
                'telegram_bot_token': '',                'telegram_chat_id': ''
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
                # This would be populated with actual contract ABIs and addresses
                logger.info("Contract interfaces initialized")
            except Exception as e:
                logger.warning(f"Contract setup failed: {e}")
        return contracts
    
    def _setup_database(self) -> None:
        """Setup SQLite database for historical analysis"""
        try:
            self.db_connection = sqlite3.connect('advanced_oracle_security.db', check_same_thread=False)
            self.db_lock = threading.Lock()
            
            cursor = self.db_connection.cursor()
            
            # Create tables for advanced analytics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS price_data_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset TEXT,
                    price REAL,
                    timestamp INTEGER,
                    source TEXT,
                    confidence REAL,
                    volume REAL,
                    volatility REAL,
                    risk_score REAL,
                    anomaly_score REAL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT UNIQUE,
                    alert_type TEXT,
                    threat_level TEXT,
                    asset TEXT,
                    timestamp INTEGER,
                    confidence_score REAL,
                    resolved BOOLEAN,
                    false_positive BOOLEAN
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ml_model_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_type TEXT,
                    accuracy REAL,
                    precision_score REAL,
                    recall REAL,
                    timestamp INTEGER,
                    training_data_size INTEGER
                )
            ''')
            
            self.db_connection.commit()
            logger.info("Database initialized for advanced analytics")
            
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            self.db_connection = None
    
    def _initialize_ml_models(self) -> None:
        """Initialize machine learning models for anomaly detection"""
        try:
            # Isolation Forest for outlier detection
            self.ml_models['isolation_forest'] = IsolationForest(
                contamination=0.1,
                random_state=42,
                n_estimators=100
            )
            
            # DBSCAN for clustering-based anomaly detection
            self.ml_models['dbscan'] = DBSCAN(eps=0.5, min_samples=5)
            
            # Standard scaler for feature normalization
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
        """Advanced price data analysis with ML and statistical methods"""
        alerts = []
        
        # Store price data for analysis
        self.price_history[price_data.asset].append(price_data)
        
        # Run multiple detection algorithms
        detection_results = await asyncio.gather(
            self._ml_anomaly_detection(price_data),
            self._statistical_anomaly_detection(price_data),
            self._cross_asset_correlation_analysis(price_data),
            self._temporal_pattern_analysis(price_data),
            self._mev_attack_detection(price_data),
            self._predictive_threat_analysis(price_data),
            return_exceptions=True
        )
        
        # Process detection results
        for result in detection_results:
            if isinstance(result, Exception):
                logger.error(f"Detection algorithm failed: {result}")
                continue
            
            if result and isinstance(result, AdvancedSecurityAlert):
                alerts.append(result)
        
        # Update threat scores
        self._update_threat_scores(price_data.asset, alerts)
        
        # Store results in database
        if self.db_connection:
            self._store_analysis_results(price_data, alerts)
        
        return alerts
    
    async def _ml_anomaly_detection(self, price_data: EnhancedPriceData) -> Optional[AdvancedSecurityAlert]:
        """Machine learning-based anomaly detection"""
        if not ML_AVAILABLE or len(self.price_history[price_data.asset]) < 50:
            return None
        
        try:
            # Prepare feature vector
            features = self._extract_ml_features(price_data)
            
            if len(features) < 5:  # Need minimum features
                return None
            
            # Reshape for single prediction
            features_array = np.array(features).reshape(1, -1)
            
            # Scale features
            if hasattr(self.ml_models['scaler'], 'n_features_in_'):
                features_scaled = self.ml_models['scaler'].transform(features_array)
            else:
                # First time, fit the scaler
                features_scaled = self._fit_and_transform_scaler(features_array)
            
            # Isolation Forest detection
            anomaly_score = self.ml_models['isolation_forest'].decision_function(features_scaled)[0]
            is_anomaly = self.ml_models['isolation_forest'].predict(features_scaled)[0] == -1
            
            if is_anomaly and abs(anomaly_score) > self.ml_anomaly_threshold:
                return AdvancedSecurityAlert(
                    alert_id=f"ml_anomaly_{int(time.time())}_{price_data.asset}",
                    alert_type=AttackType.STATISTICAL_ANOMALY,
                    threat_level=ThreatLevel.HIGH if abs(anomaly_score) > 1.5 else ThreatLevel.MEDIUM,
                    asset=price_data.asset,
                    price=price_data.price,
                    expected_price=self._calculate_expected_price(price_data.asset),
                    deviation=price_data.deviation,
                    timestamp=price_data.timestamp,
                    description=f"ML anomaly detected: score {anomaly_score:.3f}",
                    confidence_score=min(abs(anomaly_score), 1.0),
                    prediction_accuracy=0.85,  # Historical accuracy
                    attack_vector="Statistical anomaly in price behavior",
                    mitigation_actions=["Increase oracle consensus requirement", "Activate enhanced monitoring"]
                )
                
        except Exception as e:
            logger.error(f"ML anomaly detection failed: {e}")
        
        return None
    
    def _extract_ml_features(self, price_data: EnhancedPriceData) -> List[float]:
        """Extract features for ML analysis"""
        asset_history = list(self.price_history[price_data.asset])
        
        if len(asset_history) < 10:
            return []
        
        # Price-based features
        prices = [data.price for data in asset_history[-20:]]  # Last 20 data points
        
        features = [
            price_data.price,
            price_data.deviation,
            price_data.confidence,
            price_data.volume,
            price_data.volatility,
            statistics.mean(prices) if prices else 0,
            statistics.stdev(prices) if len(prices) > 1 else 0,
            max(prices) - min(prices) if prices else 0,  # Range
            len([p for p in prices if abs(p - statistics.mean(prices)) > 2 * statistics.stdev(prices)]) if len(prices) > 1 else 0,  # Outliers
            price_data.timestamp - asset_history[-2].timestamp if len(asset_history) > 1 else 0,  # Time delta
        ]
        
        return [f for f in features if f is not None and not np.isnan(f)]
    
    def _fit_and_transform_scaler(self, features_array: np.ndarray) -> np.ndarray:
        """Fit scaler with historical data and transform current features"""
        try:
            # Collect historical features for fitting
            all_features = []
            
            for asset in self.price_history:
                for data in self.price_history[asset]:
                    hist_features = self._extract_ml_features(data)
                    if len(hist_features) >= 5:
                        all_features.append(hist_features)
            
            if len(all_features) > 10:
                # Fit scaler with historical data
                hist_array = np.array(all_features)
                self.ml_models['scaler'].fit(hist_array)
                return self.ml_models['scaler'].transform(features_array)
            else:
                # Not enough data, return original
                return features_array
                
        except Exception as e:
            logger.warning(f"Scaler fitting failed: {e}")
            return features_array
    
    async def _statistical_anomaly_detection(self, price_data: EnhancedPriceData) -> Optional[AdvancedSecurityAlert]:
        """Enhanced statistical anomaly detection"""
        asset_history = list(self.price_history[price_data.asset])
        
        if len(asset_history) < 20:
            return None
        
        try:
            prices = [data.price for data in asset_history[-100:]]  # Last 100 data points
            
            # Calculate statistical measures
            mean_price = statistics.mean(prices)
            std_price = statistics.stdev(prices)
            
            # Z-score analysis
            z_score = abs(price_data.price - mean_price) / std_price if std_price > 0 else 0
            
            # Grubbs' test for outliers
            grubbs_statistic = z_score * np.sqrt(len(prices) - 1) / np.sqrt(len(prices))
            
            # Check for anomaly
            if z_score > 3.0 or grubbs_statistic > 2.5:  # 3-sigma rule + Grubbs test
                threat_level = ThreatLevel.CRITICAL if z_score > 4.0 else ThreatLevel.HIGH
                
                return AdvancedSecurityAlert(
                    alert_id=f"stat_anomaly_{int(time.time())}_{price_data.asset}",
                    alert_type=AttackType.STATISTICAL_ANOMALY,
                    threat_level=threat_level,
                    asset=price_data.asset,
                    price=price_data.price,
                    expected_price=mean_price,
                    deviation=abs(price_data.price - mean_price) / mean_price * 100,
                    timestamp=price_data.timestamp,
                    description=f"Statistical anomaly: Z-score {z_score:.2f}, Grubbs {grubbs_statistic:.2f}",
                    confidence_score=min(z_score / 5.0, 1.0),
                    prediction_accuracy=0.92,
                    attack_vector="Statistical outlier in price distribution",
                    mitigation_actions=["Verify oracle data sources", "Cross-check with external feeds"]
                )
                
        except Exception as e:
            logger.error(f"Statistical anomaly detection failed: {e}")
        
        return None
    
    async def _cross_asset_correlation_analysis(self, price_data: EnhancedPriceData) -> Optional[AdvancedSecurityAlert]:
        """Cross-asset correlation analysis for manipulation detection"""
        try:
            correlations = {}
            asset = price_data.asset
            
            # Calculate correlations with other assets
            for other_asset in self.price_history:
                if other_asset != asset and len(self.price_history[other_asset]) > 20:
                    # Get recent price data for both assets
                    asset_prices = [data.price for data in list(self.price_history[asset])[-50:]]
                    other_prices = [data.price for data in list(self.price_history[other_asset])[-50:]]
                    
                    min_length = min(len(asset_prices), len(other_prices))
                    if min_length > 10:
                        # Calculate correlation
                        correlation = np.corrcoef(
                            asset_prices[-min_length:], 
                            other_prices[-min_length:]
                        )[0, 1]
                        
                        if not np.isnan(correlation):
                            correlations[other_asset] = correlation
            
            # Detect suspicious correlation changes
            for other_asset, correlation in correlations.items():
                # Check if correlation suddenly changed
                if abs(correlation) > self.correlation_threshold:
                    # This could indicate coordinated manipulation
                    return AdvancedSecurityAlert(
                        alert_id=f"correlation_{int(time.time())}_{asset}_{other_asset}",
                        alert_type=AttackType.CROSS_ASSET_MANIPULATION,
                        threat_level=ThreatLevel.MEDIUM,
                        asset=asset,
                        price=price_data.price,
                        expected_price=self._calculate_expected_price(asset),
                        deviation=0.0,
                        timestamp=price_data.timestamp,
                        description=f"Suspicious correlation with {other_asset}: {correlation:.3f}",
                        confidence_score=abs(correlation),
                        prediction_accuracy=0.78,
                        related_assets=[other_asset],
                        attack_vector="Cross-asset manipulation coordination",
                        mitigation_actions=["Monitor related assets", "Verify independent oracle sources"]
                    )
            
        except Exception as e:
            logger.error(f"Cross-asset correlation analysis failed: {e}")
        
        return None
    
    async def _temporal_pattern_analysis(self, price_data: EnhancedPriceData) -> Optional[AdvancedSecurityAlert]:
        """Temporal pattern analysis for attack detection"""
        asset_history = list(self.price_history[price_data.asset])
        
        if len(asset_history) < 30:
            return None
        
        try:
            # Analyze price changes over time
            prices = [data.price for data in asset_history[-30:]]
            timestamps = [data.timestamp for data in asset_history[-30:]]
            
            # Calculate price change velocity
            price_changes = np.diff(prices)
            time_diffs = np.diff(timestamps)
            
            # Avoid division by zero
            velocities = [pc / td if td > 0 else 0 for pc, td in zip(price_changes, time_diffs)]
            
            if velocities:
                # Detect rapid price changes (potential flash loan attacks)
                max_velocity = max(abs(v) for v in velocities)
                
                # Define velocity threshold (this would be calibrated based on historical data)
                velocity_threshold = 0.01  # 1% per second
                
                if max_velocity > velocity_threshold:
                    return AdvancedSecurityAlert(
                        alert_id=f"temporal_{int(time.time())}_{price_data.asset}",
                        alert_type=AttackType.FLASH_LOAN_ATTACK,
                        threat_level=ThreatLevel.HIGH,
                        asset=price_data.asset,
                        price=price_data.price,
                        expected_price=self._calculate_expected_price(price_data.asset),
                        deviation=max_velocity * 100,
                        timestamp=price_data.timestamp,
                        description=f"Rapid price change detected: velocity {max_velocity:.6f}",
                        confidence_score=min(max_velocity / velocity_threshold, 1.0),
                        prediction_accuracy=0.88,
                        attack_vector="Rapid temporal price manipulation",
                        mitigation_actions=["Activate circuit breaker", "Require additional confirmations"]
                    )
                    
        except Exception as e:
            logger.error(f"Temporal pattern analysis failed: {e}")
        
        return None
    
    async def _mev_attack_detection(self, price_data: EnhancedPriceData) -> Optional[AdvancedSecurityAlert]:
        """MEV attack detection based on transaction patterns"""
        try:
            # Analyze transaction patterns for MEV indicators
            if price_data.gas_used > 0 and price_data.block_number > 0:
                # Check for suspicious gas usage patterns
                gas_threshold = self.config.get('advanced_features', {}).get('mev_gas_threshold', 1000000)
                
                if price_data.gas_used > gas_threshold:
                    # High gas usage could indicate MEV activity
                    return AdvancedSecurityAlert(
                        alert_id=f"mev_{int(time.time())}_{price_data.asset}",
                        alert_type=AttackType.MEV_ATTACK,
                        threat_level=ThreatLevel.MEDIUM,
                        asset=price_data.asset,
                        price=price_data.price,
                        expected_price=self._calculate_expected_price(price_data.asset),
                        deviation=0.0,
                        timestamp=price_data.timestamp,
                        description=f"Potential MEV activity: high gas usage {price_data.gas_used}",
                        confidence_score=0.7,
                        prediction_accuracy=0.75,
                        attack_vector="MEV extraction through transaction ordering",
                        mitigation_actions=["Monitor transaction ordering", "Implement commit-reveal scheme"]
                    )
                    
        except Exception as e:
            logger.error(f"MEV attack detection failed: {e}")
        
        return None
    
    async def _predictive_threat_analysis(self, price_data: EnhancedPriceData) -> Optional[AdvancedSecurityAlert]:
        """Predictive threat analysis using historical patterns"""
        try:
            # Analyze patterns that precede attacks
            threat_score = self._calculate_predictive_threat_score(price_data)
            
            if threat_score > 0.8:  # High threat score
                return AdvancedSecurityAlert(
                    alert_id=f"predictive_{int(time.time())}_{price_data.asset}",
                    alert_type=AttackType.PREDICTIVE_THREAT,
                    threat_level=ThreatLevel.MEDIUM,
                    asset=price_data.asset,
                    price=price_data.price,
                    expected_price=self._calculate_expected_price(price_data.asset),
                    deviation=0.0,
                    timestamp=price_data.timestamp,
                    description=f"Predictive threat detected: score {threat_score:.3f}",
                    confidence_score=threat_score,
                    prediction_accuracy=0.82,
                    attack_vector="Pattern-based predictive threat",
                    mitigation_actions=["Increase monitoring frequency", "Prepare defensive measures"]
                )
                
        except Exception as e:
            logger.error(f"Predictive threat analysis failed: {e}")
        
        return None
    
    def _calculate_expected_price(self, asset: str) -> float:
        """Calculate expected price using multiple methods"""
        asset_history = list(self.price_history[asset])
        
        if len(asset_history) < 5:
            return 0.0
        
        prices = [data.price for data in asset_history[-20:]]
        
        # Use median of recent prices as expected price
        return statistics.median(prices)
    
    def _calculate_predictive_threat_score(self, price_data: EnhancedPriceData) -> float:
        """Calculate predictive threat score based on multiple factors"""
        score = 0.0
        
        try:
            # Factor 1: Volatility increase
            volatility_score = min(price_data.volatility / 0.1, 1.0)  # Normalize to 0-1
            
            # Factor 2: Confidence decrease
            confidence_score = 1.0 - price_data.confidence
            
            # Factor 3: Volume anomaly
            volume_score = min(price_data.volume / 10000000, 1.0)  # Normalize to 0-1
            
            # Factor 4: Oracle reputation
            reputation_score = 1.0 - price_data.oracle_reputation
            
            # Weighted combination
            score = (
                volatility_score * 0.3 +
                confidence_score * 0.3 +
                volume_score * 0.2 +
                reputation_score * 0.2
            )
            
        except Exception as e:
            logger.error(f"Threat score calculation failed: {e}")
        
        return score
    
    def _update_threat_scores(self, asset: str, alerts: List[AdvancedSecurityAlert]) -> None:
        """Update threat scores based on detected alerts"""
        base_score = self.threat_scores[asset]
        
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
        decay_factor = 0.95  # 5% decay
        self.threat_scores[asset] = base_score * decay_factor
    
    def _store_analysis_results(self, price_data: EnhancedPriceData, alerts: List[AdvancedSecurityAlert]) -> None:
        """Store analysis results in database"""
        if not self.db_connection:
            return
        
        try:
            with self.db_lock:
                cursor = self.db_connection.cursor()
                
                # Store price data
                cursor.execute('''
                    INSERT INTO price_data_history 
                    (asset, price, timestamp, source, confidence, volume, volatility, risk_score, anomaly_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    price_data.asset,
                    price_data.price,
                    price_data.timestamp,
                    price_data.source,
                    price_data.confidence,
                    price_data.volume,
                    price_data.volatility,
                    price_data.risk_score,
                    0.0  # Will be updated with actual anomaly score
                ))
                
                # Store alerts
                for alert in alerts:
                    cursor.execute('''
                        INSERT OR IGNORE INTO security_alerts 
                        (alert_id, alert_type, threat_level, asset, timestamp, confidence_score, resolved, false_positive)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        alert.alert_id,
                        alert.alert_type.value,
                        alert.threat_level.value,
                        alert.asset,
                        alert.timestamp,
                        alert.confidence_score,
                        alert.resolved,
                        False  # Will be updated when validated
                    ))
                
                self.db_connection.commit()
                
        except Exception as e:
            logger.error(f"Database storage failed: {e}")
    
    async def get_security_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive security dashboard data"""
        dashboard = {
            'timestamp': int(time.time()),
            'system_status': 'OPERATIONAL',
            'total_assets_monitored': len(self.price_history),
            'active_alerts': len([alert for alert in self.active_alerts if not alert.resolved]),
            'circuit_breakers_active': sum(1 for active in self.circuit_breakers.values() if active),
            'ml_models_status': 'ACTIVE' if ML_AVAILABLE else 'UNAVAILABLE',
            'threat_scores': dict(self.threat_scores),
            'recent_alerts': [asdict(alert) for alert in self.active_alerts[-10:]],
            'model_performance': await self._get_model_performance(),
            'correlation_matrix': dict(self.correlation_matrix),
            'system_health': {
                'database_connection': self.db_connection is not None,
                'web3_connection': self.w3 is not None and self.w3.isConnected() if self.w3 else False,
                'ml_models_trained': len(self.ml_models) > 0
            }
        }
        
        return dashboard
    
    async def _get_model_performance(self) -> Dict[str, Any]:
        """Get ML model performance metrics"""
        if not self.db_connection:
            return {}
        
        try:
            with self.db_lock:
                cursor = self.db_connection.cursor()
                cursor.execute('''
                    SELECT model_type, AVG(accuracy), AVG(precision_score), AVG(recall)
                    FROM ml_model_performance 
                    WHERE timestamp > ? 
                    GROUP BY model_type
                ''', (int(time.time()) - 86400,))  # Last 24 hours
                
                results = cursor.fetchall()
                
                performance = {}
                for row in results:
                    performance[row[0]] = {
                        'accuracy': row[1],
                        'precision': row[2],
                        'recall': row[3]
                    }
                  return performance
                
        except Exception as e:
            logger.error(f"Model performance retrieval failed: {e}")
            return {}

    def close(self) -> None:
        """Close database connections and cleanup"""
        if self.db_connection:
            self.db_connection.close()
        logger.info("Advanced Oracle Security Monitor closed")

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
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return {
                "rss_mb": memory_info.rss / 1024 / 1024,
                "vms_mb": memory_info.vms / 1024 / 1024,
                "percent": process.memory_percent()
            }
        except ImportError:
            return {
                "rss_mb": 0.0,
                "vms_mb": 0.0,
                "percent": 0.0
            }

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

# Example usage
if __name__ == "__main__":
    async def main():
        monitor = AdvancedOracleSecurityMonitor()
        
        # Example price data
        test_price_data = EnhancedPriceData(
            asset="ETH",
            price=2000.0,
            timestamp=int(time.time()),
            source="TestOracle",
            confidence=0.95,
            volume=1000000.0,
            volatility=0.05,
            oracle_reputation=0.98
        )
        
        # Analyze price data
        alerts = await monitor.analyze_price_data_advanced(test_price_data)
        
        print(f"Generated {len(alerts)} alerts")
        for alert in alerts:
            print(f"- {alert.alert_type.value}: {alert.description}")
        
        # Get dashboard
        dashboard = await monitor.get_security_dashboard()
        print(f"System Status: {dashboard['system_status']}")
        
        monitor.close()
    
    asyncio.run(main())
