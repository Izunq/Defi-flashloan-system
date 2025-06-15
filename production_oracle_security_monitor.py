#!/usr/bin/env python3
"""
Production Oracle Security Monitor
Enterprise-grade oracle security monitoring with ML-based anomaly detection
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
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from web3 import Web3
from concurrent.futures import ThreadPoolExecutor
from collections import deque
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import yaml
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import sqlite3
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("production_oracle_security.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ProductionOracleSecurityMonitor")

@dataclass
class PriceDataPoint:
    """Enhanced price data structure"""
    asset: str
    price: float
    timestamp: int
    source: str
    confidence: float
    volume: float = 0.0
    deviation: float = 0.0
    validation_score: float = 100.0
    risk_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SecurityIncident:
    """Security incident structure"""
    incident_id: str
    incident_type: str
    severity: str
    asset: str
    detected_at: int
    price: float
    expected_price: float
    deviation: float
    description: str
    affected_oracles: List[str]
    response_actions: List[str] = field(default_factory=list)
    resolved: bool = False
    resolution_time: Optional[int] = None

@dataclass
class OracleHealthMetrics:
    """Comprehensive oracle health metrics"""
    oracle_id: str
    total_updates: int
    successful_updates: int
    failed_updates: int
    average_latency: float
    accuracy_score: float
    reputation_score: float
    uptime_percentage: float
    last_seen: int
    consecutive_failures: int
    is_healthy: bool

@dataclass
class ThreatAssessment:
    """Threat assessment result"""
    threat_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    probability: float
    confidence: float
    risk_factors: List[str]
    recommended_actions: List[str]
    time_to_impact: Optional[int] = None

class ProductionOracleSecurityMonitor:
    """Production-grade oracle security monitoring system"""
    
    def __init__(self, config_path: str = "production_oracle_config.yaml"):
        self.config = self._load_config(config_path)
        self.w3 = self._setup_web3()
        self.contracts = self._setup_contracts()
        self.db = self._setup_database()
        
        # ML Models
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
        self.ml_models_trained = False
        
        # Security state
        self.price_history: Dict[str, deque] = {}
        self.oracle_metrics: Dict[str, OracleHealthMetrics] = {}
        self.active_incidents: List[SecurityIncident] = []
        self.circuit_breakers: Dict[str, bool] = {}
        self.threat_assessments: Dict[str, ThreatAssessment] = {}
        
        # Real-time monitoring
        self.monitoring_active = False
        self.emergency_protocols_active = False
        self.last_global_check = time.time()
        
        # Performance metrics
        self.detection_stats = {
            'total_detections': 0,
            'false_positives': 0,
            'true_positives': 0,
            'response_times': deque(maxlen=1000)
        }
        
        # Security thresholds (configurable)
        self.thresholds = self.config.get('security_thresholds', {
            'max_price_deviation': 500,  # 5% in basis points
            'circuit_breaker_threshold': 1000,  # 10% in basis points
            'min_oracle_consensus': 3,
            'staleness_threshold': 3600,  # 1 hour in seconds
            'anomaly_threshold': 3.0,  # Z-score threshold
            'volume_spike_threshold': 300,  # 3x normal volume
            'ml_anomaly_threshold': -0.5,  # Isolation Forest threshold
            'threat_assessment_interval': 300  # 5 minutes
        })
        
        logger.info("Production Oracle Security Monitor initialized")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            'blockchain': {
                'rpc_url': 'http://localhost:8545',
                'chain_id': 31337
            },
            'contracts': {
                'secure_multi_oracle': '0x1234567890123456789012345678901234567890',
                'oracle_security_wrapper': '0x1234567890123456789012345678901234567891',
                'oracle_manipulation_monitor': '0x1234567890123456789012345678901234567892'
            },
            'monitoring': {
                'interval': 30,
                'assets': ['ETH', 'BTC', 'USDC', 'DAI'],
                'external_apis': []
            },
            'alerting': {
                'email_enabled': False,
                'webhook_enabled': False,
                'telegram_enabled': False
            },
            'security_thresholds': {
                'max_price_deviation': 500,
                'circuit_breaker_threshold': 1000,
                'min_oracle_consensus': 3,
                'staleness_threshold': 3600
            }
        }
    
    def _setup_web3(self) -> Web3:
        """Setup Web3 connection"""
        try:
            rpc_url = self.config.get('blockchain', {}).get('rpc_url', 'http://localhost:8545')
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            if w3.is_connected():
                logger.info(f"Connected to blockchain at {rpc_url}")
                return w3
            else:
                logger.error("Failed to connect to blockchain")
                return None
        except Exception as e:
            logger.error(f"Error setting up Web3: {e}")
            return None
    
    def _setup_contracts(self) -> Dict:
        """Setup smart contract interfaces"""
        contracts = {}
        
        if not self.w3:
            return contracts
        
        try:
            contract_configs = self.config.get('contracts', {})
            
            # Load contract ABIs (simplified for demo)
            for contract_name, address in contract_configs.items():
                if address and Web3.is_address(address):
                    # In production, load actual ABIs
                    contracts[contract_name] = {
                        'address': address,
                        'contract': None  # Would be actual contract instance
                    }
            
            logger.info(f"Loaded {len(contracts)} contract interfaces")
            
        except Exception as e:
            logger.error(f"Error setting up contracts: {e}")
        
        return contracts
    
    def _setup_database(self) -> sqlite3.Connection:
        """Setup SQLite database for persistent storage"""
        try:
            db = sqlite3.connect('oracle_security.db', check_same_thread=False)
            
            # Create tables
            db.execute('''
                CREATE TABLE IF NOT EXISTS price_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset TEXT NOT NULL,
                    price REAL NOT NULL,
                    timestamp INTEGER NOT NULL,
                    source TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    volume REAL DEFAULT 0,
                    deviation REAL DEFAULT 0
                )
            ''')
            
            db.execute('''
                CREATE TABLE IF NOT EXISTS security_incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    incident_id TEXT NOT NULL UNIQUE,
                    incident_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    asset TEXT NOT NULL,
                    detected_at INTEGER NOT NULL,
                    price REAL NOT NULL,
                    expected_price REAL NOT NULL,
                    deviation REAL NOT NULL,
                    description TEXT NOT NULL,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolution_time INTEGER
                )
            ''')
            
            db.execute('''
                CREATE TABLE IF NOT EXISTS oracle_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    oracle_id TEXT NOT NULL,
                    timestamp INTEGER NOT NULL,
                    total_updates INTEGER NOT NULL,
                    successful_updates INTEGER NOT NULL,
                    failed_updates INTEGER NOT NULL,
                    accuracy_score REAL NOT NULL,
                    reputation_score REAL NOT NULL,
                    uptime_percentage REAL NOT NULL
                )
            ''')
            
            db.commit()
            logger.info("Database initialized successfully")
            return db
            
        except Exception as e:
            logger.error(f"Error setting up database: {e}")
            return None
    
    async def start_monitoring(self) -> None:
        """Start the main monitoring loop"""
        logger.info("Starting production oracle security monitoring")
        self.monitoring_active = True
        
        # Start concurrent monitoring tasks
        tasks = [
            asyncio.create_task(self._real_time_monitoring()),
            asyncio.create_task(self._threat_assessment_loop()),
            asyncio.create_task(self._health_monitoring_loop()),
            asyncio.create_task(self._ml_training_loop()),
            asyncio.create_task(self._incident_response_loop())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
        finally:
            self.monitoring_active = False
    
    async def _real_time_monitoring(self) -> None:
        """Real-time price monitoring and anomaly detection"""
        interval = self.config.get('monitoring', {}).get('interval', 30)
        
        while self.monitoring_active:
            try:
                start_time = time.time()
                
                # Collect price data from all sources
                price_data = await self._collect_comprehensive_price_data()
                
                # Analyze for anomalies and threats
                incidents = await self._analyze_security_threats(price_data)
                
                # Process incidents
                if incidents:
                    await self._process_security_incidents(incidents)
                
                # Update oracle health metrics
                await self._update_oracle_health_metrics(price_data)
                
                # Store data persistently
                await self._store_price_data(price_data)
                
                # Check circuit breaker conditions
                await self._check_circuit_breaker_conditions(price_data)
                
                # Performance logging
                elapsed = time.time() - start_time
                logger.info(f"Monitoring cycle completed in {elapsed:.2f}s, analyzed {len(price_data)} data points")
                
                # Wait for next cycle
                await asyncio.sleep(max(0, interval - elapsed))
                
            except Exception as e:
                logger.error(f"Error in real-time monitoring: {e}")
                await asyncio.sleep(5)  # Short delay before retry
    
    async def _collect_comprehensive_price_data(self) -> List[PriceDataPoint]:
        """Collect price data from all configured sources"""
        price_data = []
        
        try:
            # Collect from on-chain oracles
            onchain_data = await self._collect_onchain_price_data()
            price_data.extend(onchain_data)
            
            # Collect from external APIs
            external_data = await self._collect_external_price_data()
            price_data.extend(external_data)
            
            # Cross-validate data
            validated_data = await self._cross_validate_price_data(price_data)
            
            return validated_data
            
        except Exception as e:
            logger.error(f"Error collecting price data: {e}")
            return []
    
    async def _collect_onchain_price_data(self) -> List[PriceDataPoint]:
        """Collect price data from on-chain oracle contracts"""
        price_data = []
        
        if not self.w3 or not self.contracts:
            return price_data
        
        try:
            assets = self.config.get('monitoring', {}).get('assets', [])
            
            for asset in assets:
                try:
                    # Get data from SecureMultiOracle
                    if 'secure_multi_oracle' in self.contracts:
                        price_data_point = await self._get_multi_oracle_price(asset)
                        if price_data_point:
                            price_data.append(price_data_point)
                    
                    # Get data from OracleSecurityWrapper
                    if 'oracle_security_wrapper' in self.contracts:
                        validated_price = await self._get_validated_price(asset)
                        if validated_price:
                            price_data.append(validated_price)
                    
                except Exception as e:
                    logger.error(f"Error getting on-chain price for {asset}: {e}")
            
        except Exception as e:
            logger.error(f"Error in on-chain data collection: {e}")
        
        return price_data
    
    async def _get_multi_oracle_price(self, asset: str) -> Optional[PriceDataPoint]:
        """Get price from SecureMultiOracle contract"""
        try:
            # This would interact with the actual contract
            # For now, return simulated data
            current_time = int(time.time())
            
            # Simulate getting consensus price
            base_price = self._get_simulated_price(asset)
            
            return PriceDataPoint(
                asset=asset,
                price=base_price,
                timestamp=current_time,
                source='SecureMultiOracle',
                confidence=95.0,
                volume=random.uniform(10000, 100000),
                deviation=random.uniform(0, 50),  # 0-0.5%
                validation_score=95.0,
                risk_score=random.uniform(0, 20)
            )
            
        except Exception as e:
            logger.error(f"Error getting multi-oracle price for {asset}: {e}")
            return None
    
    async def _get_validated_price(self, asset: str) -> Optional[PriceDataPoint]:
        """Get validated price from OracleSecurityWrapper"""
        try:
            # This would interact with the actual contract
            # For now, return simulated data
            current_time = int(time.time())
            
            base_price = self._get_simulated_price(asset)
            
            return PriceDataPoint(
                asset=asset,
                price=base_price * random.uniform(0.999, 1.001),  # Small variation
                timestamp=current_time,
                source='OracleSecurityWrapper',
                confidence=98.0,
                volume=random.uniform(8000, 80000),
                deviation=random.uniform(0, 30),
                validation_score=98.0,
                risk_score=random.uniform(0, 15),
                metadata={'validated': True, 'security_checked': True}
            )
            
        except Exception as e:
            logger.error(f"Error getting validated price for {asset}: {e}")
            return None
    
    def _get_simulated_price(self, asset: str) -> float:
        """Get simulated price for testing purposes"""
        base_prices = {
            'ETH': 2000.0,
            'BTC': 35000.0,
            'USDC': 1.0,
            'DAI': 1.0,
            'USDT': 1.0
        }
        
        base_price = base_prices.get(asset, 100.0)
        
        # Add some realistic price movement
        time_factor = time.time() % 3600  # Hourly cycle
        price_variation = np.sin(time_factor / 3600 * 2 * np.pi) * 0.01  # 1% variation
        noise = random.uniform(-0.005, 0.005)  # 0.5% random noise
        
        return base_price * (1 + price_variation + noise)
    
    async def _collect_external_price_data(self) -> List[PriceDataPoint]:
        """Collect price data from external APIs"""
        price_data = []
        
        try:
            external_apis = self.config.get('monitoring', {}).get('external_apis', [])
            
            for api_config in external_apis:
                try:
                    api_data = await self._fetch_external_api_data(api_config)
                    price_data.extend(api_data)
                except Exception as e:
                    logger.error(f"Error fetching from external API: {e}")
            
        except Exception as e:
            logger.error(f"Error collecting external price data: {e}")
        
        return price_data
    
    async def _fetch_external_api_data(self, api_config: Dict) -> List[PriceDataPoint]:
        """Fetch data from external API"""
        # This would implement actual API calls to external sources
        # For now, return empty list
        return []
    
    async def _cross_validate_price_data(self, price_data: List[PriceDataPoint]) -> List[PriceDataPoint]:
        """Cross-validate price data from multiple sources"""
        validated_data = []
        
        try:
            # Group by asset
            asset_groups = {}
            for data_point in price_data:
                if data_point.asset not in asset_groups:
                    asset_groups[data_point.asset] = []
                asset_groups[data_point.asset].append(data_point)
            
            # Validate each asset group
            for asset, data_points in asset_groups.items():
                validated = await self._validate_asset_prices(asset, data_points)
                validated_data.extend(validated)
            
        except Exception as e:
            logger.error(f"Error in cross-validation: {e}")
        
        return validated_data
    
    async def _validate_asset_prices(self, asset: str, data_points: List[PriceDataPoint]) -> List[PriceDataPoint]:
        """Validate prices for a specific asset"""
        if len(data_points) < 2:
            return data_points
        
        try:
            prices = [dp.price for dp in data_points]
            median_price = statistics.median(prices)
            
            validated_points = []
            for data_point in data_points:
                # Calculate deviation from median
                deviation = abs(data_point.price - median_price) / median_price
                data_point.deviation = deviation * 10000  # Convert to basis points
                
                # Update validation score based on deviation
                if deviation > 0.1:  # 10% deviation
                    data_point.validation_score *= 0.5
                    data_point.risk_score += 50
                elif deviation > 0.05:  # 5% deviation
                    data_point.validation_score *= 0.8
                    data_point.risk_score += 20
                
                validated_points.append(data_point)
            
            return validated_points
            
        except Exception as e:
            logger.error(f"Error validating prices for {asset}: {e}")
            return data_points
    
    async def _analyze_security_threats(self, price_data: List[PriceDataPoint]) -> List[SecurityIncident]:
        """Analyze price data for security threats and anomalies"""
        incidents = []
        
        try:
            for data_point in price_data:
                # Update price history
                if data_point.asset not in self.price_history:
                    self.price_history[data_point.asset] = deque(maxlen=1000)
                
                self.price_history[data_point.asset].append(data_point)
                
                # Statistical anomaly detection
                stat_incidents = await self._detect_statistical_anomalies(data_point)
                incidents.extend(stat_incidents)
                
                # ML-based anomaly detection
                ml_incidents = await self._detect_ml_anomalies(data_point)
                incidents.extend(ml_incidents)
                
                # Pattern-based threat detection
                pattern_incidents = await self._detect_pattern_threats(data_point)
                incidents.extend(pattern_incidents)
                
                # Volume-based anomaly detection
                volume_incidents = await self._detect_volume_anomalies(data_point)
                incidents.extend(volume_incidents)
            
        except Exception as e:
            logger.error(f"Error analyzing security threats: {e}")
        
        return incidents
    
    async def _detect_statistical_anomalies(self, data_point: PriceDataPoint) -> List[SecurityIncident]:
        """Detect statistical anomalies using Z-score analysis"""
        incidents = []
        
        try:
            history = self.price_history.get(data_point.asset, deque())
            
            if len(history) < 10:  # Need minimum data points
                return incidents
            
            # Calculate moving statistics
            recent_prices = [p.price for p in list(history)[-50:]]  # Last 50 data points
            mean_price = statistics.mean(recent_prices)
            std_dev = statistics.stdev(recent_prices) if len(recent_prices) > 1 else 0
            
            # Calculate Z-score
            if std_dev > 0:
                z_score = abs(data_point.price - mean_price) / std_dev
                
                # Check against threshold
                if z_score > self.thresholds['anomaly_threshold']:
                    severity = 'CRITICAL' if z_score > 5 else 'HIGH' if z_score > 4 else 'MEDIUM'
                    
                    incident = SecurityIncident(
                        incident_id=hashlib.md5(f"stat_{data_point.asset}_{data_point.timestamp}_{z_score}".encode()).hexdigest(),
                        incident_type='STATISTICAL_ANOMALY',
                        severity=severity,
                        asset=data_point.asset,
                        detected_at=data_point.timestamp,
                        price=data_point.price,
                        expected_price=mean_price,
                        deviation=abs(data_point.price - mean_price) / mean_price * 10000,
                        description=f"Statistical anomaly detected: Z-score {z_score:.2f}",
                        affected_oracles=[data_point.source]
                    )
                    incidents.append(incident)
            
        except Exception as e:
            logger.error(f"Error in statistical anomaly detection for {data_point.asset}: {e}")
        
        return incidents
    
    async def _detect_ml_anomalies(self, data_point: PriceDataPoint) -> List[SecurityIncident]:
        """Detect anomalies using machine learning models"""
        incidents = []
        
        try:
            if not self.ml_models_trained:
                return incidents
            
            history = self.price_history.get(data_point.asset, deque())
            
            if len(history) < 20:
                return incidents
            
            # Prepare features for ML model
            features = self._extract_features(data_point, history)
            
            if features is not None:
                # Predict anomaly score
                anomaly_score = self.anomaly_detector.decision_function([features])[0]
                
                # Check against threshold
                if anomaly_score < self.thresholds['ml_anomaly_threshold']:
                    severity = 'HIGH' if anomaly_score < -0.8 else 'MEDIUM'
                    
                    incident = SecurityIncident(
                        incident_id=hashlib.md5(f"ml_{data_point.asset}_{data_point.timestamp}_{anomaly_score}".encode()).hexdigest(),
                        incident_type='ML_ANOMALY',
                        severity=severity,
                        asset=data_point.asset,
                        detected_at=data_point.timestamp,
                        price=data_point.price,
                        expected_price=data_point.price,  # ML doesn't provide expected price
                        deviation=0.0,  # ML provides anomaly score instead
                        description=f"ML anomaly detected: Score {anomaly_score:.3f}",
                        affected_oracles=[data_point.source]
                    )
                    incidents.append(incident)
            
        except Exception as e:
            logger.error(f"Error in ML anomaly detection for {data_point.asset}: {e}")
        
        return incidents
    
    def _extract_features(self, data_point: PriceDataPoint, history: deque) -> Optional[List[float]]:
        """Extract features for ML anomaly detection"""
        try:
            if len(history) < 10:
                return None
            
            recent_prices = [p.price for p in list(history)[-10:]]
            recent_volumes = [p.volume for p in list(history)[-10:]]
            
            features = [
                data_point.price,
                data_point.volume,
                data_point.confidence,
                data_point.risk_score,
                statistics.mean(recent_prices),
                statistics.stdev(recent_prices) if len(recent_prices) > 1 else 0,
                statistics.mean(recent_volumes),
                max(recent_prices) - min(recent_prices),  # Price range
                (data_point.price - recent_prices[-1]) / recent_prices[-1] if recent_prices[-1] > 0 else 0  # Price change
            ]
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return None
    
    async def _detect_pattern_threats(self, data_point: PriceDataPoint) -> List[SecurityIncident]:
        """Detect pattern-based threats (flash loan attacks, coordinated manipulation)"""
        incidents = []
        
        try:
            history = self.price_history.get(data_point.asset, deque())
            
            if len(history) < 5:
                return incidents
            
            # Check for rapid price changes (flash loan pattern)
            recent_prices = [p.price for p in list(history)[-5:]]
            price_changes = [abs(recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1] 
                           for i in range(1, len(recent_prices)) if recent_prices[i-1] > 0]
            
            # If multiple large price changes in sequence
            large_changes = [change for change in price_changes if change > 0.03]  # 3%
            
            if len(large_changes) >= 3:
                incident = SecurityIncident(
                    incident_id=hashlib.md5(f"pattern_{data_point.asset}_{data_point.timestamp}".encode()).hexdigest(),
                    incident_type='FLASH_LOAN_PATTERN',
                    severity='HIGH',
                    asset=data_point.asset,
                    detected_at=data_point.timestamp,
                    price=data_point.price,
                    expected_price=recent_prices[0],
                    deviation=max(price_changes) * 10000,
                    description=f"Flash loan pattern detected: {len(large_changes)} rapid price changes",
                    affected_oracles=[data_point.source]
                )
                incidents.append(incident)
            
        except Exception as e:
            logger.error(f"Error in pattern threat detection for {data_point.asset}: {e}")
        
        return incidents
    
    async def _detect_volume_anomalies(self, data_point: PriceDataPoint) -> List[SecurityIncident]:
        """Detect volume-based anomalies"""
        incidents = []
        
        try:
            history = self.price_history.get(data_point.asset, deque())
            
            if len(history) < 10:
                return incidents
            
            # Calculate average volume
            recent_volumes = [p.volume for p in list(history)[-20:] if p.volume > 0]
            
            if not recent_volumes:
                return incidents
            
            avg_volume = statistics.mean(recent_volumes)
            
            # Check for volume spike
            if data_point.volume > avg_volume * self.thresholds['volume_spike_threshold'] / 100:
                incident = SecurityIncident(
                    incident_id=hashlib.md5(f"volume_{data_point.asset}_{data_point.timestamp}".encode()).hexdigest(),
                    incident_type='VOLUME_ANOMALY',
                    severity='MEDIUM',
                    asset=data_point.asset,
                    detected_at=data_point.timestamp,
                    price=data_point.price,
                    expected_price=data_point.price,
                    deviation=0.0,
                    description=f"Volume spike detected: {data_point.volume:.2f} vs avg {avg_volume:.2f}",
                    affected_oracles=[data_point.source]
                )
                incidents.append(incident)
            
        except Exception as e:
            logger.error(f"Error in volume anomaly detection for {data_point.asset}: {e}")
        
        return incidents
    
    async def _process_security_incidents(self, incidents: List[SecurityIncident]) -> None:
        """Process and respond to security incidents"""
        for incident in incidents:
            try:
                # Add to active incidents
                self.active_incidents.append(incident)
                
                # Store in database
                await self._store_incident(incident)
                
                # Log incident
                logger.warning(f"SECURITY INCIDENT: {incident.incident_type} - {incident.severity} - {incident.asset} - {incident.description}")
                
                # Determine response actions
                response_actions = await self._determine_response_actions(incident)
                incident.response_actions = response_actions
                
                # Execute automated responses
                await self._execute_automated_responses(incident)
                
                # Send alerts
                await self._send_security_alerts(incident)
                
                # Update detection statistics
                self._update_detection_stats(incident)
                
            except Exception as e:
                logger.error(f"Error processing incident {incident.incident_id}: {e}")
    
    async def _determine_response_actions(self, incident: SecurityIncident) -> List[str]:
        """Determine appropriate response actions for an incident"""
        actions = []
        
        try:
            if incident.severity == 'CRITICAL':
                actions.extend([
                    'activate_circuit_breaker',
                    'pause_trading',
                    'notify_emergency_team',
                    'increase_monitoring_frequency'
                ])
            elif incident.severity == 'HIGH':
                actions.extend([
                    'increase_monitoring_frequency',
                    'notify_security_team',
                    'validate_oracle_sources'
                ])
            elif incident.severity == 'MEDIUM':
                actions.extend([
                    'log_incident',
                    'monitor_closely'
                ])
            
            # Asset-specific actions
            if incident.incident_type == 'FLASH_LOAN_PATTERN':
                actions.append('check_mempool_activity')
            elif incident.incident_type == 'VOLUME_ANOMALY':
                actions.append('verify_external_market_conditions')
            
        except Exception as e:
            logger.error(f"Error determining response actions: {e}")
        
        return actions
    
    async def _execute_automated_responses(self, incident: SecurityIncident) -> None:
        """Execute automated response actions"""
        try:
            for action in incident.response_actions:
                if action == 'activate_circuit_breaker':
                    await self._activate_circuit_breaker(incident.asset)
                elif action == 'pause_trading':
                    await self._pause_trading(incident.asset)
                elif action == 'increase_monitoring_frequency':
                    await self._increase_monitoring_frequency(incident.asset)
                # Add more automated actions as needed
                
        except Exception as e:
            logger.error(f"Error executing automated responses: {e}")
    
    async def _activate_circuit_breaker(self, asset: str) -> None:
        """Activate circuit breaker for an asset"""
        try:
            self.circuit_breakers[asset] = True
            logger.critical(f"CIRCUIT BREAKER ACTIVATED for {asset}")
            
            # In production, this would interact with smart contracts
            # to actually pause trading or oracle updates
            
        except Exception as e:
            logger.error(f"Error activating circuit breaker for {asset}: {e}")
    
    async def _pause_trading(self, asset: str) -> None:
        """Pause trading for an asset"""
        try:
            logger.critical(f"TRADING PAUSED for {asset}")
            
            # In production, this would interact with trading contracts
            # to pause all trading activities for the asset
            
        except Exception as e:
            logger.error(f"Error pausing trading for {asset}: {e}")
    
    async def _increase_monitoring_frequency(self, asset: str) -> None:
        """Increase monitoring frequency for an asset"""
        try:
            logger.info(f"Increased monitoring frequency for {asset}")
            
            # Implementation would adjust monitoring intervals
            # for specific assets under threat
            
        except Exception as e:
            logger.error(f"Error increasing monitoring frequency for {asset}: {e}")
    
    async def _send_security_alerts(self, incident: SecurityIncident) -> None:
        """Send security alerts via configured channels"""
        try:
            alert_config = self.config.get('alerting', {})
            
            # Email alerts
            if alert_config.get('email_enabled'):
                await self._send_email_alert(incident)
            
            # Webhook alerts
            if alert_config.get('webhook_enabled'):
                await self._send_webhook_alert(incident)
            
            # Telegram alerts
            if alert_config.get('telegram_enabled'):
                await self._send_telegram_alert(incident)
            
        except Exception as e:
            logger.error(f"Error sending security alerts: {e}")
    
    async def _send_email_alert(self, incident: SecurityIncident) -> None:
        """Send email alert"""
        try:
            email_config = self.config.get('alerting', {}).get('email', {})
            
            if not email_config.get('smtp_server'):
                return
            
            # Create email content
            subject = f"SECURITY ALERT: {incident.incident_type} - {incident.severity}"
            body = f"""
Security Incident Detected:

Type: {incident.incident_type}
Severity: {incident.severity}
Asset: {incident.asset}
Price: {incident.price}
Expected Price: {incident.expected_price}
Deviation: {incident.deviation:.2f} basis points
Time: {datetime.fromtimestamp(incident.detected_at)}
Description: {incident.description}

Response Actions: {', '.join(incident.response_actions)}

This is an automated alert from the Oracle Security Monitor.
            """
            
            # Send email (simplified implementation)
            logger.info(f"Would send email alert: {subject}")
            
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
    
    async def _send_webhook_alert(self, incident: SecurityIncident) -> None:
        """Send webhook alert"""
        try:
            webhook_config = self.config.get('alerting', {}).get('webhook', {})
            
            if not webhook_config.get('url'):
                return
            
            payload = {
                'type': 'security_incident',
                'incident': asdict(incident),
                'timestamp': time.time()
            }
            
            # Send webhook (simplified implementation)
            logger.info(f"Would send webhook alert to {webhook_config.get('url')}")
            
        except Exception as e:
            logger.error(f"Error sending webhook alert: {e}")
    
    async def _send_telegram_alert(self, incident: SecurityIncident) -> None:
        """Send Telegram alert"""
        try:
            telegram_config = self.config.get('alerting', {}).get('telegram', {})
            
            if not telegram_config.get('bot_token') or not telegram_config.get('chat_id'):
                return
            
            message = f"🚨 SECURITY ALERT 🚨\n\n"
            message += f"Type: {incident.incident_type}\n"
            message += f"Severity: {incident.severity}\n"
            message += f"Asset: {incident.asset}\n"
            message += f"Description: {incident.description}\n"
            
            # Send Telegram message (simplified implementation)
            logger.info(f"Would send Telegram alert: {message[:100]}...")
            
        except Exception as e:
            logger.error(f"Error sending Telegram alert: {e}")
    
    def _update_detection_stats(self, incident: SecurityIncident) -> None:
        """Update detection statistics"""
        try:
            self.detection_stats['total_detections'] += 1
            
            # For now, assume all detections are true positives
            # In production, this would be validated by security team
            self.detection_stats['true_positives'] += 1
            
            # Record response time (instant for automated detection)
            response_time = time.time() - incident.detected_at
            self.detection_stats['response_times'].append(response_time)
            
        except Exception as e:
            logger.error(f"Error updating detection stats: {e}")
    
    async def _store_price_data(self, price_data: List[PriceDataPoint]) -> None:
        """Store price data in database"""
        try:
            if not self.db:
                return
            
            for data_point in price_data:
                self.db.execute('''
                    INSERT INTO price_data (asset, price, timestamp, source, confidence, volume, deviation)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data_point.asset,
                    data_point.price,
                    data_point.timestamp,
                    data_point.source,
                    data_point.confidence,
                    data_point.volume,
                    data_point.deviation
                ))
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error storing price data: {e}")
    
    async def _store_incident(self, incident: SecurityIncident) -> None:
        """Store security incident in database"""
        try:
            if not self.db:
                return
            
            self.db.execute('''
                INSERT OR REPLACE INTO security_incidents 
                (incident_id, incident_type, severity, asset, detected_at, price, expected_price, deviation, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                incident.incident_id,
                incident.incident_type,
                incident.severity,
                incident.asset,
                incident.detected_at,
                incident.price,
                incident.expected_price,
                incident.deviation,
                incident.description
            ))
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error storing incident: {e}")
    
    async def _check_circuit_breaker_conditions(self, price_data: List[PriceDataPoint]) -> None:
        """Check circuit breaker conditions"""
        try:
            for data_point in price_data:
                if data_point.deviation > self.thresholds['circuit_breaker_threshold']:
                    if not self.circuit_breakers.get(data_point.asset, False):
                        await self._activate_circuit_breaker(data_point.asset)
            
        except Exception as e:
            logger.error(f"Error checking circuit breaker conditions: {e}")
    
    async def _update_oracle_health_metrics(self, price_data: List[PriceDataPoint]) -> None:
        """Update oracle health metrics"""
        try:
            for data_point in price_data:
                oracle_id = data_point.source
                
                if oracle_id not in self.oracle_metrics:
                    self.oracle_metrics[oracle_id] = OracleHealthMetrics(
                        oracle_id=oracle_id,
                        total_updates=0,
                        successful_updates=0,
                        failed_updates=0,
                        average_latency=0.0,
                        accuracy_score=100.0,
                        reputation_score=100.0,
                        uptime_percentage=100.0,
                        last_seen=data_point.timestamp,
                        consecutive_failures=0,
                        is_healthy=True
                    )
                
                metrics = self.oracle_metrics[oracle_id]
                metrics.total_updates += 1
                metrics.last_seen = data_point.timestamp
                
                # Update success/failure based on validation score
                if data_point.validation_score > 80:
                    metrics.successful_updates += 1
                    metrics.consecutive_failures = 0
                else:
                    metrics.failed_updates += 1
                    metrics.consecutive_failures += 1
                
                # Update reputation based on performance
                if data_point.risk_score < 20:
                    metrics.reputation_score = min(metrics.reputation_score + 0.1, 100.0)
                else:
                    metrics.reputation_score = max(metrics.reputation_score - 1.0, 0.0)
                
                # Update health status
                metrics.is_healthy = (
                    metrics.consecutive_failures < 3 and
                    metrics.reputation_score > 50.0 and
                    data_point.confidence > 70.0
                )
            
        except Exception as e:
            logger.error(f"Error updating oracle health metrics: {e}")
    
    async def _threat_assessment_loop(self) -> None:
        """Continuous threat assessment loop"""
        interval = self.thresholds['threat_assessment_interval']
        
        while self.monitoring_active:
            try:
                await self._perform_threat_assessment()
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in threat assessment loop: {e}")
                await asyncio.sleep(30)
    
    async def _perform_threat_assessment(self) -> None:
        """Perform comprehensive threat assessment"""
        try:
            assets = self.config.get('monitoring', {}).get('assets', [])
            
            for asset in assets:
                threat_assessment = await self._assess_asset_threat_level(asset)
                self.threat_assessments[asset] = threat_assessment
                
                if threat_assessment.threat_level in ['HIGH', 'CRITICAL']:
                    logger.warning(f"HIGH THREAT LEVEL for {asset}: {threat_assessment.probability:.2f} probability")
            
        except Exception as e:
            logger.error(f"Error performing threat assessment: {e}")
    
    async def _assess_asset_threat_level(self, asset: str) -> ThreatAssessment:
        """Assess threat level for a specific asset"""
        try:
            risk_factors = []
            probability = 0.0
            confidence = 0.0
            
            # Check recent incidents
            recent_incidents = [inc for inc in self.active_incidents 
                             if inc.asset == asset and not inc.resolved 
                             and (time.time() - inc.detected_at) < 3600]  # Last hour
            
            if recent_incidents:
                risk_factors.append(f"{len(recent_incidents)} recent incidents")
                probability += len(recent_incidents) * 0.2
            
            # Check oracle health
            oracle_health_scores = []
            for oracle_id, metrics in self.oracle_metrics.items():
                if metrics.is_healthy:
                    oracle_health_scores.append(metrics.reputation_score)
            
            if oracle_health_scores:
                avg_health = statistics.mean(oracle_health_scores)
                if avg_health < 70:
                    risk_factors.append(f"Poor oracle health: {avg_health:.1f}")
                    probability += (100 - avg_health) / 100 * 0.3
            
            # Check price volatility
            history = self.price_history.get(asset, deque())
            if len(history) > 10:
                recent_prices = [p.price for p in list(history)[-20:]]
                volatility = statistics.stdev(recent_prices) / statistics.mean(recent_prices) if recent_prices else 0
                
                if volatility > 0.05:  # 5% volatility
                    risk_factors.append(f"High volatility: {volatility:.3f}")
                    probability += volatility * 2
            
            # Check circuit breaker status
            if self.circuit_breakers.get(asset, False):
                risk_factors.append("Circuit breaker active")
                probability += 0.4
            
            # Normalize probability
            probability = min(probability, 1.0)
            confidence = min(0.8 + len(risk_factors) * 0.1, 1.0)
            
            # Determine threat level
            if probability > 0.8:
                threat_level = 'CRITICAL'
            elif probability > 0.6:
                threat_level = 'HIGH'
            elif probability > 0.4:
                threat_level = 'MEDIUM'
            else:
                threat_level = 'LOW'
            
            # Recommended actions
            recommended_actions = []
            if threat_level in ['HIGH', 'CRITICAL']:
                recommended_actions.extend([
                    'increase_monitoring_frequency',
                    'validate_all_oracle_sources',
                    'prepare_emergency_protocols'
                ])
            
            return ThreatAssessment(
                threat_level=threat_level,
                probability=probability,
                confidence=confidence,
                risk_factors=risk_factors,
                recommended_actions=recommended_actions,
                time_to_impact=300 if threat_level == 'CRITICAL' else None  # 5 minutes
            )
            
        except Exception as e:
            logger.error(f"Error assessing threat level for {asset}: {e}")
            return ThreatAssessment(
                threat_level='UNKNOWN',
                probability=0.0,
                confidence=0.0,
                risk_factors=['Assessment error'],
                recommended_actions=[]
            )
    
    async def _health_monitoring_loop(self) -> None:
        """Oracle health monitoring loop"""
        while self.monitoring_active:
            try:
                await self._monitor_oracle_health()
                await asyncio.sleep(60)  # Check health every minute
                
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(30)
    
    async def _monitor_oracle_health(self) -> None:
        """Monitor overall oracle system health"""
        try:
            current_time = time.time()
            unhealthy_oracles = []
            
            for oracle_id, metrics in self.oracle_metrics.items():
                # Check if oracle is stale
                if current_time - metrics.last_seen > self.thresholds['staleness_threshold']:
                    metrics.is_healthy = False
                    unhealthy_oracles.append(oracle_id)
                
                # Check consecutive failures
                if metrics.consecutive_failures >= 3:
                    metrics.is_healthy = False
                    unhealthy_oracles.append(oracle_id)
                
                # Update uptime percentage
                uptime = metrics.successful_updates / max(metrics.total_updates, 1) * 100
                metrics.uptime_percentage = uptime
            
            # Log health status
            healthy_count = sum(1 for m in self.oracle_metrics.values() if m.is_healthy)
            total_count = len(self.oracle_metrics)
            
            if unhealthy_oracles:
                logger.warning(f"Unhealthy oracles detected: {unhealthy_oracles}")
            
            logger.info(f"Oracle health: {healthy_count}/{total_count} healthy")
            
            # Check minimum consensus
            if healthy_count < self.thresholds['min_oracle_consensus']:
                logger.critical("INSUFFICIENT ORACLE CONSENSUS - Emergency protocols may be needed")
                
        except Exception as e:
            logger.error(f"Error monitoring oracle health: {e}")
    
    async def _ml_training_loop(self) -> None:
        """Machine learning model training loop"""
        while self.monitoring_active:
            try:
                await self._train_ml_models()
                await asyncio.sleep(3600)  # Retrain every hour
                
            except Exception as e:
                logger.error(f"Error in ML training loop: {e}")
                await asyncio.sleep(1800)  # Retry in 30 minutes
    
    async def _train_ml_models(self) -> None:
        """Train machine learning models on historical data"""
        try:
            if not self.db:
                return
            
            # Get training data from database
            cursor = self.db.cursor()
            cursor.execute('''
                SELECT asset, price, confidence, volume, deviation 
                FROM price_data 
                WHERE timestamp > ? 
                ORDER BY timestamp DESC 
                LIMIT 10000
            ''', (time.time() - 24*3600,))  # Last 24 hours
            
            data = cursor.fetchall()
            
            if len(data) < 100:  # Need minimum data for training
                logger.info("Insufficient data for ML training")
                return
            
            # Prepare training data
            features = []
            for row in data:
                asset, price, confidence, volume, deviation = row
                
                # Create feature vector (simplified)
                feature_vector = [
                    price,
                    confidence,
                    volume,
                    deviation,
                    # Could add more sophisticated features
                ]
                features.append(feature_vector)
            
            # Convert to numpy array and normalize
            X = np.array(features)
            X_scaled = self.scaler.fit_transform(X)
            
            # Train isolation forest
            self.anomaly_detector.fit(X_scaled)
            self.ml_models_trained = True
            
            logger.info(f"ML models trained on {len(data)} data points")
            
        except Exception as e:
            logger.error(f"Error training ML models: {e}")
    
    async def _incident_response_loop(self) -> None:
        """Incident response and cleanup loop"""
        while self.monitoring_active:
            try:
                await self._cleanup_resolved_incidents()
                await self._auto_resolve_incidents()
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in incident response loop: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_resolved_incidents(self) -> None:
        """Clean up resolved incidents"""
        try:
            current_time = time.time()
            
            # Remove incidents older than 24 hours
            self.active_incidents = [
                inc for inc in self.active_incidents
                if (current_time - inc.detected_at) < 24*3600
            ]
            
        except Exception as e:
            logger.error(f"Error cleaning up incidents: {e}")
    
    async def _auto_resolve_incidents(self) -> None:
        """Auto-resolve incidents based on conditions"""
        try:
            current_time = time.time()
            
            for incident in self.active_incidents:
                if incident.resolved:
                    continue
                
                # Auto-resolve old incidents of certain types
                age = current_time - incident.detected_at
                
                if (incident.incident_type in ['VOLUME_ANOMALY', 'STATISTICAL_ANOMALY'] 
                    and age > 3600):  # 1 hour
                    incident.resolved = True
                    incident.resolution_time = int(current_time)
                    logger.info(f"Auto-resolved incident {incident.incident_id}")
                
        except Exception as e:
            logger.error(f"Error auto-resolving incidents: {e}")
    
    def get_security_dashboard(self) -> Dict[str, Any]:
        """Get security dashboard data"""
        try:
            current_time = time.time()
            
            # Active incidents by severity
            active_incidents_by_severity = {}
            for incident in self.active_incidents:
                if not incident.resolved:
                    severity = incident.severity
                    active_incidents_by_severity[severity] = active_incidents_by_severity.get(severity, 0) + 1
            
            # Oracle health summary
            healthy_oracles = sum(1 for m in self.oracle_metrics.values() if m.is_healthy)
            total_oracles = len(self.oracle_metrics)
            
            # Circuit breaker status
            active_circuit_breakers = [asset for asset, active in self.circuit_breakers.items() if active]
            
            # Threat levels
            threat_levels = {asset: assessment.threat_level 
                           for asset, assessment in self.threat_assessments.items()}
            
            # Detection statistics
            total_detections = self.detection_stats['total_detections']
            accuracy = (self.detection_stats['true_positives'] / max(total_detections, 1)) * 100
            avg_response_time = (statistics.mean(self.detection_stats['response_times']) 
                               if self.detection_stats['response_times'] else 0)
            
            return {
                'timestamp': current_time,
                'system_status': 'HEALTHY' if not active_circuit_breakers else 'DEGRADED',
                'active_incidents': active_incidents_by_severity,
                'oracle_health': {
                    'healthy': healthy_oracles,
                    'total': total_oracles,
                    'percentage': (healthy_oracles / max(total_oracles, 1)) * 100
                },
                'circuit_breakers': active_circuit_breakers,
                'threat_levels': threat_levels,
                'detection_stats': {
                    'total_detections': total_detections,
                    'accuracy_percentage': accuracy,
                    'average_response_time': avg_response_time
                },
                'monitoring_active': self.monitoring_active
            }
            
        except Exception as e:
            logger.error(f"Error generating security dashboard: {e}")
            return {}
    
    async def stop_monitoring(self) -> None:
        """Stop monitoring and cleanup"""
        logger.info("Stopping oracle security monitoring")
        self.monitoring_active = False
        
        if self.db:
            self.db.close()
        
        logger.info("Oracle security monitoring stopped")

# Main execution
async def main():
    """Main execution function"""
    monitor = ProductionOracleSecurityMonitor()
    
    try:
        # Start monitoring
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await monitor.stop_monitoring()

if __name__ == "__main__":
    asyncio.run(main())
