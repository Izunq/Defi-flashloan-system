#!/usr/bin/env python3
"""
Oracle Sentinel Agent
Specialized sentinel bot for monitoring oracle data integrity and security
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
import sqlite3
import yaml
from typing import Dict, List, Any, Optional, Tuple, Union, Set, Callable
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
from web3 import Web3
from concurrent.futures import ThreadPoolExecutor

# Import emergency action executor
from emergency_action_executor import EmergencyActionExecutor
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
    print("ML libraries not available, using statistical methods only")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("oracle_sentinel.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("OracleSentinel")

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
    CROSS_ASSET_MANIPULATION = "CROSS_ASSET_MANIPULATION"
    PREDICTIVE_THREAT = "PREDICTIVE_THREAT"

@dataclass
class OracleData:
    """Oracle data with security metrics"""
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
class SecurityAlert:
    """Security alert with ML predictions"""
    alert_id: str
    alert_type: AttackType
    threat_level: ThreatLevel
    asset: str
    price: float
    expected_price: float
    deviation: float
    timestamp: int
    source: str
    confidence: float
    details: Dict[str, Any]
    recommended_actions: List[str]
    false_positive_probability: float = 0.0
    reported: bool = False
    resolved: bool = False
    resolution_time: Optional[int] = None
    resolution_details: Optional[str] = None

class OracleSentinel:
    """
    Specialized sentinel agent for monitoring oracle data integrity and security
    """
    
    def __init__(self, config_path: str = "oracle_sentinel_config.yaml"):
        """Initialize the Oracle Sentinel agent"""
        self.config = self._load_config(config_path)
        self.web3 = self._initialize_web3()
        self.db_conn = self._initialize_database()
        
        # Data structures for monitoring
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=self.config.get("history_size", 100)))
        self.alerts: List[SecurityAlert] = []
        self.active_alerts: Dict[str, SecurityAlert] = {}
        self.oracle_sources: Dict[str, Dict[str, Any]] = {}
        self.oracle_reputation: Dict[str, float] = defaultdict(lambda: 1.0)
        
        # ML models
        self.anomaly_detectors: Dict[str, Any] = {}
        self.price_predictors: Dict[str, Any] = {}
        
        # Initialize ML models if available
        if ML_AVAILABLE:
            self._initialize_ml_models()
        
        # Initialize emergency action executor
        self.emergency_executor = EmergencyActionExecutor()
        
        # Alert handlers
        self.alert_handlers = []
        self._register_default_alert_handlers()
        
        # Monitoring state
        self.is_monitoring = False
        self.monitoring_task = None
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=self.config.get("max_workers", 5))
        
        logger.info("Oracle Sentinel initialized")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using default configuration")
            return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "web3_provider": "http://localhost:8545",
            "history_size": 100,
            "alert_threshold": 0.8,
            "monitoring_interval": 10,
            "max_workers": 5,
            "db_path": "oracle_sentinel.db",
            "assets": ["ETH", "BTC", "USDT", "USDC"],
            "oracle_sources": ["chainlink", "uniswap", "compound"],
            "ml_enabled": True,
            "anomaly_detection": {
                "isolation_forest": {
                    "contamination": 0.05,
                    "n_estimators": 100
                }
            },
            "notification": {
                "email": False,
                "slack": False,
                "webhook": False
            }
        }
    
    def _initialize_web3(self) -> Web3:
        """Initialize Web3 connection"""
        provider_url = self.config.get("web3_provider", "http://localhost:8545")
        try:
            if provider_url.startswith("http"):
                web3 = Web3(Web3.HTTPProvider(provider_url))
            elif provider_url.startswith("ws"):
                web3 = Web3(Web3.WebsocketProvider(provider_url))
            else:
                web3 = Web3(Web3.IPCProvider(provider_url))
            
            if web3.is_connected():
                logger.info(f"Connected to Web3 provider at {provider_url}")
            else:
                logger.warning(f"Failed to connect to Web3 provider at {provider_url}")
            
            return web3
        except Exception as e:
            logger.error(f"Error initializing Web3: {e}")
            return Web3(Web3.HTTPProvider("http://localhost:8545"))
    
    def _initialize_database(self) -> sqlite3.Connection:
        """Initialize SQLite database for storing oracle data and alerts"""
        db_path = self.config.get("db_path", "oracle_sentinel.db")
        try:
            conn = sqlite3.connect(db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            # Create tables if they don't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS oracle_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset TEXT,
                price REAL,
                timestamp INTEGER,
                source TEXT,
                confidence REAL,
                volume REAL,
                deviation REAL,
                volatility REAL,
                liquidity REAL,
                gas_used INTEGER,
                block_number INTEGER,
                transaction_hash TEXT,
                oracle_reputation REAL,
                risk_score REAL
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT UNIQUE,
                alert_type TEXT,
                threat_level TEXT,
                asset TEXT,
                price REAL,
                expected_price REAL,
                deviation REAL,
                timestamp INTEGER,
                source TEXT,
                confidence REAL,
                details TEXT,
                recommended_actions TEXT,
                false_positive_probability REAL,
                reported INTEGER,
                resolved INTEGER,
                resolution_time INTEGER,
                resolution_details TEXT
            )
            ''')
            
            conn.commit()
            logger.info(f"Initialized database at {db_path}")
            return conn
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            return None
    
    def _initialize_ml_models(self):
        """Initialize machine learning models for anomaly detection and price prediction"""
        if not ML_AVAILABLE:
            logger.warning("ML libraries not available, skipping ML model initialization")
            return
        
        try:
            # Initialize anomaly detection models for each asset
            for asset in self.config.get("assets", []):
                # Isolation Forest for anomaly detection
                iso_forest_params = self.config.get("anomaly_detection", {}).get("isolation_forest", {})
                self.anomaly_detectors[asset] = IsolationForest(
                    n_estimators=iso_forest_params.get("n_estimators", 100),
                    contamination=iso_forest_params.get("contamination", 0.05),
                    random_state=42
                )
            
            logger.info("Initialized ML models for anomaly detection")
        except Exception as e:
            logger.error(f"Error initializing ML models: {e}")
    
    def _register_default_alert_handlers(self):
        """Register default alert handlers"""
        self.alert_handlers.append(self._log_alert)
        
        # Register additional handlers based on config
        notification_config = self.config.get("notification", {})
        if notification_config.get("email", False):
            self.alert_handlers.append(self._email_alert)
        if notification_config.get("slack", False):
            self.alert_handlers.append(self._slack_alert)
        if notification_config.get("webhook", False):
            self.alert_handlers.append(self._webhook_alert)
            
        # Register emergency action handler
        contract_config = self.config.get("integration", {}).get("contract_interaction", {})
        if contract_config.get("enabled", False):
            self.alert_handlers.append(self._process_emergency_actions)
            logger.info("Registered emergency action handler")
    
    async def start_monitoring(self):
        """Start the oracle sentinel monitoring process"""
        if self.is_monitoring:
            logger.warning("Oracle Sentinel is already monitoring")
            return
        
        self.is_monitoring = True
        logger.info("Starting Oracle Sentinel monitoring")
        
        # Start the emergency action executor
        contract_config = self.config.get("integration", {}).get("contract_interaction", {})
        if contract_config.get("enabled", False):
            await self.emergency_executor.start()
            logger.info("Started emergency action executor")
        
        # Start the monitoring task
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self):
        """Stop the oracle sentinel monitoring process"""
        if not self.is_monitoring:
            logger.warning("Oracle Sentinel is not monitoring")
            return
        
        self.is_monitoring = False
        logger.info("Stopping Oracle Sentinel monitoring")
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
            
        # Stop the emergency action executor
        contract_config = self.config.get("integration", {}).get("contract_interaction", {})
        if contract_config.get("enabled", False):
            await self.emergency_executor.stop()
            logger.info("Stopped emergency action executor")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        try:
            while self.is_monitoring:
                logger.debug("Running oracle monitoring cycle")
                
                # Fetch oracle data for all configured assets
                for asset in self.config.get("assets", []):
                    try:
                        await self._monitor_asset(asset)
                    except Exception as e:
                        logger.error(f"Error monitoring asset {asset}: {e}")
                
                # Process active alerts
                await self._process_active_alerts()
                
                # Wait for the next monitoring cycle
                await asyncio.sleep(self.config.get("monitoring_interval", 10))
        except asyncio.CancelledError:
            logger.info("Oracle monitoring loop cancelled")
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
            self.is_monitoring = False
    
    async def _monitor_asset(self, asset: str):
        """Monitor a specific asset for oracle anomalies"""
        # Fetch oracle data from multiple sources
        oracle_data_list = await self._fetch_oracle_data(asset)
        
        if not oracle_data_list:
            logger.warning(f"No oracle data available for {asset}")
            return
        
        # Process oracle data
        for oracle_data in oracle_data_list:
            # Store data in history
            self.price_history[asset].append(oracle_data)
            
            # Store in database
            self._store_oracle_data(oracle_data)
            
            # Detect anomalies
            await self._detect_anomalies(oracle_data)
    
    async def _fetch_oracle_data(self, asset: str) -> List[OracleData]:
        """Fetch oracle data from multiple sources"""
        oracle_data_list = []
        
        for source in self.config.get("oracle_sources", []):
            try:
                # In a real implementation, this would fetch data from actual oracles
                # For this example, we'll simulate oracle data
                price, confidence = self._simulate_oracle_data(asset, source)
                
                oracle_data = OracleData(
                    asset=asset,
                    price=price,
                    timestamp=int(time.time()),
                    source=source,
                    confidence=confidence,
                    volume=1000.0,  # Simulated volume
                    liquidity=10000.0,  # Simulated liquidity
                    gas_used=100000,  # Simulated gas used
                    block_number=self.web3.eth.block_number if self.web3.is_connected() else 0,
                    transaction_hash="0x" + hashlib.sha256(f"{asset}_{source}_{time.time()}".encode()).hexdigest(),
                    oracle_reputation=self.oracle_reputation.get(source, 1.0)
                )
                
                # Calculate additional metrics if we have history
                if len(self.price_history[asset]) > 0:
                    # Calculate deviation from average
                    avg_price = statistics.mean([data.price for data in self.price_history[asset]])
                    oracle_data.deviation = abs(oracle_data.price - avg_price) / avg_price if avg_price > 0 else 0
                    
                    # Calculate volatility (standard deviation of recent prices)
                    if len(self.price_history[asset]) >= 10:
                        recent_prices = [data.price for data in list(self.price_history[asset])[-10:]]
                        oracle_data.volatility = statistics.stdev(recent_prices) / avg_price if avg_price > 0 else 0
                
                oracle_data_list.append(oracle_data)
            except Exception as e:
                logger.error(f"Error fetching oracle data for {asset} from {source}: {e}")
        
        return oracle_data_list
    
    def _simulate_oracle_data(self, asset: str, source: str) -> Tuple[float, float]:
        """Simulate oracle data for testing purposes"""
        # Base prices for different assets
        base_prices = {
            "ETH": 3000.0,
            "BTC": 50000.0,
            "USDT": 1.0,
            "USDC": 1.0
        }
        
        # Add some random variation
        base_price = base_prices.get(asset, 100.0)
        variation = np.random.normal(0, 0.01)  # 1% standard deviation
        
        # Different sources might have slightly different prices
        source_bias = {
            "chainlink": 0.0,
            "uniswap": 0.002,
            "compound": -0.001
        }
        
        price = base_price * (1 + variation + source_bias.get(source, 0))
        confidence = 0.95 + np.random.uniform(0, 0.05)  # 95-100% confidence
        
        return price, confidence
    
    def _store_oracle_data(self, oracle_data: OracleData):
        """Store oracle data in the database"""
        if not self.db_conn:
            return
        
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
            INSERT INTO oracle_data (
                asset, price, timestamp, source, confidence, volume, deviation,
                volatility, liquidity, gas_used, block_number, transaction_hash,
                oracle_reputation, risk_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                oracle_data.asset, oracle_data.price, oracle_data.timestamp,
                oracle_data.source, oracle_data.confidence, oracle_data.volume,
                oracle_data.deviation, oracle_data.volatility, oracle_data.liquidity,
                oracle_data.gas_used, oracle_data.block_number, oracle_data.transaction_hash,
                oracle_data.oracle_reputation, oracle_data.risk_score
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"Error storing oracle data: {e}")
    
    async def _detect_anomalies(self, oracle_data: OracleData):
        """Detect anomalies in oracle data"""
        # Skip if we don't have enough history
        if len(self.price_history[oracle_data.asset]) < 10:
            return
        
        # Statistical anomaly detection
        await self._statistical_anomaly_detection(oracle_data)
        
        # ML-based anomaly detection
        if ML_AVAILABLE and self.config.get("ml_enabled", True):
            await self._ml_anomaly_detection(oracle_data)
    
    async def _statistical_anomaly_detection(self, oracle_data: OracleData):
        """Perform statistical anomaly detection"""
        # Get recent prices for this asset
        recent_data = list(self.price_history[oracle_data.asset])
        recent_prices = [data.price for data in recent_data]
        
        # Calculate z-score
        if len(recent_prices) >= 10:
            mean_price = statistics.mean(recent_prices[:-1])  # Exclude current price
            std_dev = statistics.stdev(recent_prices[:-1]) if len(recent_prices) > 1 else 0.01
            
            if std_dev > 0:
                z_score = abs(oracle_data.price - mean_price) / std_dev
                
                # Detect anomaly based on z-score threshold
                if z_score > 3.0:  # More than 3 standard deviations
                    await self._create_alert(
                        oracle_data=oracle_data,
                        alert_type=AttackType.STATISTICAL_ANOMALY,
                        threat_level=ThreatLevel.MEDIUM if z_score < 5.0 else ThreatLevel.HIGH,
                        expected_price=mean_price,
                        details={
                            "z_score": z_score,
                            "std_dev": std_dev,
                            "mean_price": mean_price,
                            "detection_method": "z_score"
                        }
                    )
        
        # Check for sudden price changes
        if len(recent_prices) >= 2:
            price_change = abs(oracle_data.price - recent_prices[-2]) / recent_prices[-2] if recent_prices[-2] > 0 else 0
            
            if price_change > 0.05:  # More than 5% change
                await self._create_alert(
                    oracle_data=oracle_data,
                    alert_type=AttackType.PRICE_MANIPULATION,
                    threat_level=ThreatLevel.MEDIUM if price_change < 0.1 else ThreatLevel.HIGH,
                    expected_price=recent_prices[-2],
                    details={
                        "price_change": price_change,
                        "previous_price": recent_prices[-2],
                        "detection_method": "price_change"
                    }
                )
    
    async def _ml_anomaly_detection(self, oracle_data: OracleData):
        """Perform ML-based anomaly detection"""
        if not ML_AVAILABLE:
            return
        
        asset = oracle_data.asset
        
        # Get recent data for this asset
        recent_data = list(self.price_history[asset])
        
        if len(recent_data) < 20:  # Need enough data to train
            return
        
        try:
            # Extract features for anomaly detection
            features = np.array([
                [
                    data.price,
                    data.deviation if data.deviation else 0,
                    data.volatility if data.volatility else 0,
                    data.confidence
                ] for data in recent_data
            ])
            
            # Normalize features
            scaler = StandardScaler()
            normalized_features = scaler.fit_transform(features)
            
            # Train isolation forest if not already trained
            if asset not in self.anomaly_detectors or len(recent_data) % 20 == 0:
                self.anomaly_detectors[asset].fit(normalized_features[:-1])  # Train on all but current data point
            
            # Predict anomaly for current data point
            current_features = normalized_features[-1].reshape(1, -1)
            prediction = self.anomaly_detectors[asset].predict(current_features)[0]
            
            # Isolation Forest returns -1 for anomalies and 1 for normal data
            if prediction == -1:
                # Calculate anomaly score (higher is more anomalous)
                anomaly_score = self.anomaly_detectors[asset].score_samples(current_features)[0]
                anomaly_score = 1.0 - np.exp(anomaly_score)  # Convert to 0-1 scale
                
                # Create alert for ML-detected anomaly
                await self._create_alert(
                    oracle_data=oracle_data,
                    alert_type=AttackType.STATISTICAL_ANOMALY,
                    threat_level=ThreatLevel.MEDIUM if anomaly_score < 0.8 else ThreatLevel.HIGH,
                    expected_price=statistics.mean([data.price for data in recent_data[:-1]]),
                    details={
                        "anomaly_score": anomaly_score,
                        "detection_method": "isolation_forest",
                        "features_used": ["price", "deviation", "volatility", "confidence"]
                    }
                )
        except Exception as e:
            logger.error(f"Error in ML anomaly detection: {e}")
    
    async def _create_alert(self, oracle_data: OracleData, alert_type: AttackType, 
                           threat_level: ThreatLevel, expected_price: float, details: Dict[str, Any]):
        """Create a security alert"""
        # Generate unique alert ID
        alert_id = f"{oracle_data.asset}_{alert_type.value}_{int(time.time())}"
        
        # Create recommended actions based on alert type and threat level
        recommended_actions = self._generate_recommended_actions(alert_type, threat_level)
        
        # Create alert object
        alert = SecurityAlert(
            alert_id=alert_id,
            alert_type=alert_type,
            threat_level=threat_level,
            asset=oracle_data.asset,
            price=oracle_data.price,
            expected_price=expected_price,
            deviation=abs(oracle_data.price - expected_price) / expected_price if expected_price > 0 else 0,
            timestamp=oracle_data.timestamp,
            source=oracle_data.source,
            confidence=oracle_data.confidence,
            details=details,
            recommended_actions=recommended_actions,
            false_positive_probability=0.1,  # Initial estimate
            reported=False,
            resolved=False
        )
        
        # Store alert in memory and database
        self.alerts.append(alert)
        self.active_alerts[alert_id] = alert
        self._store_alert(alert)
        
        # Trigger alert handlers
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")
    
    def _generate_recommended_actions(self, alert_type: AttackType, threat_level: ThreatLevel) -> List[str]:
        """Generate recommended actions based on alert type and threat level"""
        actions = []
        
        # Common actions for all alerts
        actions.append("Verify oracle data across multiple sources")
        
        # Type-specific actions
        if alert_type == AttackType.PRICE_MANIPULATION:
            actions.append("Check for unusual trading activity")
            actions.append("Verify liquidity levels across exchanges")
            
            if threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL, ThreatLevel.EMERGENCY]:
                actions.append("Temporarily pause trading for affected asset")
                actions.append("Notify exchange partners of potential manipulation")
        
        elif alert_type == AttackType.FLASH_LOAN_ATTACK:
            actions.append("Review recent large transactions")
            actions.append("Check for flash loan activity on lending platforms")
            
            if threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL, ThreatLevel.EMERGENCY]:
                actions.append("Temporarily increase collateral requirements")
                actions.append("Pause flash loan functionality")
        
        elif alert_type == AttackType.STATISTICAL_ANOMALY:
            actions.append("Review market conditions for external factors")
            actions.append("Check for news events affecting asset price")
            
            if threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL, ThreatLevel.EMERGENCY]:
                actions.append("Use fallback price oracle mechanisms")
        
        # Severity-specific actions
        if threat_level == ThreatLevel.EMERGENCY:
            actions.append("Activate emergency shutdown procedures")
            actions.append("Convene emergency response team immediately")
        elif threat_level == ThreatLevel.CRITICAL:
            actions.append("Notify security team immediately")
            actions.append("Prepare for possible emergency measures")
        
        return actions
    
    def _store_alert(self, alert: SecurityAlert):
        """Store alert in the database"""
        if not self.db_conn:
            return
        
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
            INSERT INTO alerts (
                alert_id, alert_type, threat_level, asset, price, expected_price,
                deviation, timestamp, source, confidence, details, recommended_actions,
                false_positive_probability, reported, resolved, resolution_time, resolution_details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert.alert_id, alert.alert_type.value, alert.threat_level.value,
                alert.asset, alert.price, alert.expected_price, alert.deviation,
                alert.timestamp, alert.source, alert.confidence,
                json.dumps(alert.details), json.dumps(alert.recommended_actions),
                alert.false_positive_probability, int(alert.reported), int(alert.resolved),
                alert.resolution_time, alert.resolution_details
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"Error storing alert: {e}")
    
    async def _process_active_alerts(self):
        """Process active alerts"""
        for alert_id, alert in list(self.active_alerts.items()):
            # Check if alert should be auto-resolved
            if not alert.resolved:
                await self._check_alert_resolution(alert)
            
            # Remove resolved alerts older than 1 hour
            if alert.resolved and alert.resolution_time and (int(time.time()) - alert.resolution_time) > 3600:
                self.active_alerts.pop(alert_id, None)
    
    async def _check_alert_resolution(self, alert: SecurityAlert):
        """Check if an alert should be automatically resolved"""
        # Get latest data for the asset
        if not self.price_history.get(alert.asset) or len(self.price_history[alert.asset]) < 5:
            return
        
        recent_data = list(self.price_history[alert.asset])[-5:]
        recent_prices = [data.price for data in recent_data]
        
        # Calculate current deviation from expected price
        avg_price = statistics.mean(recent_prices)
        current_deviation = abs(avg_price - alert.expected_price) / alert.expected_price if alert.expected_price > 0 else 0
        
        # If deviation has returned to normal, resolve the alert
        if current_deviation < 0.02:  # Less than 2% deviation
            alert.resolved = True
            alert.resolution_time = int(time.time())
            alert.resolution_details = "Auto-resolved: Price returned to normal range"
            
            # Update in database
            self._update_alert_resolution(alert)
            
            logger.info(f"Auto-resolved alert {alert.alert_id}: {alert.resolution_details}")
    
    def _update_alert_resolution(self, alert: SecurityAlert):
        """Update alert resolution status in database"""
        if not self.db_conn:
            return
        
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
            UPDATE alerts SET
                resolved = ?,
                resolution_time = ?,
                resolution_details = ?
            WHERE alert_id = ?
            ''', (
                int(alert.resolved),
                alert.resolution_time,
                alert.resolution_details,
                alert.alert_id
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"Error updating alert resolution: {e}")
    
    async def _log_alert(self, alert: SecurityAlert):
        """Log alert to file and console"""
        log_message = (
            f"ORACLE SECURITY ALERT: {alert.threat_level.value}\n"
            f"Type: {alert.alert_type.value}\n"
            f"Asset: {alert.asset}\n"
            f"Price: {alert.price} (Expected: {alert.expected_price}, Deviation: {alert.deviation:.2%})\n"
            f"Source: {alert.source}\n"
            f"Time: {datetime.fromtimestamp(alert.timestamp).strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Details: {json.dumps(alert.details, indent=2)}\n"
            f"Recommended Actions: {', '.join(alert.recommended_actions)}"
        )
        
        if alert.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL, ThreatLevel.EMERGENCY]:
            logger.critical(log_message)
        elif alert.threat_level == ThreatLevel.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    async def _email_alert(self, alert: SecurityAlert):
        """Send alert via email"""
        # This would be implemented with an email library in a real system
        logger.info(f"Would send email alert for {alert.alert_id}")
    
    async def _slack_alert(self, alert: SecurityAlert):
        """Send alert via Slack"""
        # This would be implemented with a Slack API client in a real system
        logger.info(f"Would send Slack alert for {alert.alert_id}")
    
    async def _webhook_alert(self, alert: SecurityAlert):
        """Send alert via webhook"""
        # This would be implemented with aiohttp in a real system
        logger.info(f"Would send webhook alert for {alert.alert_id}")
    
    async def _process_emergency_actions(self, alert: SecurityAlert):
        """Process emergency actions for an alert"""
        # Convert SecurityAlert to dict format expected by emergency executor
        alert_dict = {
            "alert_id": alert.alert_id,
            "source": "oracle",
            "priority": alert.threat_level.value,
            "message": f"Oracle anomaly detected for {alert.asset} with {alert.deviation:.2f}% deviation",
            "details": {
                "asset": alert.asset,
                "price": alert.price,
                "expected_price": alert.expected_price,
                "deviation": alert.deviation,
                "source": alert.source,
                "confidence": alert.confidence,
                "alert_type": alert.alert_type.value
            },
            "recommended_actions": alert.recommended_actions
        }
        
        # Process the alert through emergency executor
        action_ids = self.emergency_executor.process_alert(alert_dict)
        
        if action_ids:
            logger.info(f"Emergency actions triggered for alert {alert.alert_id}: {action_ids}")
            
            # Store action IDs in alert details
            if 'emergency_actions' not in alert.details:
                alert.details['emergency_actions'] = []
            alert.details['emergency_actions'].extend(action_ids)
            
            # Update alert in database
            self._store_alert(alert)
    
    def get_active_alerts(self) -> List[SecurityAlert]:
        """Get list of active alerts"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[SecurityAlert]:
        """Get historical alerts"""
        return self.alerts[-limit:]
    
    def get_asset_status(self, asset: str) -> Dict[str, Any]:
        """Get current status for a specific asset"""
        if not self.price_history.get(asset):
            return {"asset": asset, "status": "No data available"}
        
        recent_data = list(self.price_history[asset])
        if not recent_data:
            return {"asset": asset, "status": "No recent data"}
        
        latest_data = recent_data[-1]
        
        # Count active alerts for this asset
        asset_alerts = [a for a in self.active_alerts.values() if a.asset == asset and not a.resolved]
        
        return {
            "asset": asset,
            "latest_price": latest_data.price,
            "timestamp": latest_data.timestamp,
            "updated": datetime.fromtimestamp(latest_data.timestamp).strftime("%Y-%m-%d %H:%M:%S"),
            "sources": list(set(data.source for data in recent_data)),
            "deviation": latest_data.deviation,
            "volatility": latest_data.volatility,
            "active_alerts": len(asset_alerts),
            "alert_details": [{"id": a.alert_id, "type": a.alert_type.value, "level": a.threat_level.value} 
                             for a in asset_alerts]
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        assets_status = {}
        for asset in self.config.get("assets", []):
            assets_status[asset] = self.get_asset_status(asset)
        
        # Count alerts by severity
        alert_counts = {level.value: 0 for level in ThreatLevel}
        for alert in self.active_alerts.values():
            if not alert.resolved:
                alert_counts[alert.threat_level.value] += 1
        
        return {
            "timestamp": int(time.time()),
            "monitoring_active": self.is_monitoring,
            "assets_monitored": len(self.config.get("assets", [])),
            "oracle_sources": len(self.config.get("oracle_sources", [])),
            "active_alerts": sum(alert_counts.values()),
            "alerts_by_severity": alert_counts,
            "assets_status": assets_status,
            "ml_enabled": ML_AVAILABLE and self.config.get("ml_enabled", True)
        }

async def main():
    """Main function for running the Oracle Sentinel as a standalone process"""
    # Create and start the Oracle Sentinel
    sentinel = OracleSentinel()
    
    try:
        # Start monitoring
        await sentinel.start_monitoring()
        
        # Keep running until interrupted
        while True:
            await asyncio.sleep(60)
            
            # Print system status every minute
            status = sentinel.get_system_status()
            print(f"\nSystem Status at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:")
            print(f"Monitoring Active: {status['monitoring_active']}")
            print(f"Assets Monitored: {status['assets_monitored']}")
            print(f"Active Alerts: {status['active_alerts']}")
            print("Alerts by Severity:", end=" ")
            for level, count in status['alerts_by_severity'].items():
                if count > 0:
                    print(f"{level}: {count}", end=" ")
            print("\n")
    
    except KeyboardInterrupt:
        print("Shutting down Oracle Sentinel...")
        await sentinel.stop_monitoring()
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        await sentinel.stop_monitoring()

if __name__ == "__main__":
    asyncio.run(main())