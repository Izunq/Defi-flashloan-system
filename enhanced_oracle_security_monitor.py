#!/usr/bin/env python3
"""
Enhanced Oracle Security Monitor
Advanced monitoring and alerting system for oracle manipulation detection
"""

import json
import time
import logging
import asyncio
import statistics
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from web3 import Web3
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from collections import deque
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("enhanced_oracle_security.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("EnhancedOracleSecurityMonitor")

@dataclass
class PriceData:
    """Price data structure"""
    asset: str
    price: float
    timestamp: int
    source: str
    confidence: float
    volume: float = 0.0
    deviation: float = 0.0

@dataclass
class SecurityAlert:
    """Security alert structure"""
    alert_id: str
    alert_type: str
    severity: str
    asset: str
    price: float
    expected_price: float
    deviation: float
    timestamp: int
    description: str
    resolved: bool = False

@dataclass
class OracleMetrics:
    """Oracle performance metrics"""
    oracle_address: str
    total_updates: int
    successful_updates: int
    failed_updates: int
    average_deviation: float
    last_update: int
    reputation_score: float
    is_active: bool

class EnhancedOracleSecurityMonitor:
    """Enhanced oracle security monitoring system"""
    
    def __init__(self, config_path: str = "enhanced_oracle_config.yaml"):
        self.config = self._load_config(config_path)
        self.w3 = self._setup_web3()
        self.contracts = self._setup_contracts()
        
        # Security state
        self.price_history: Dict[str, deque] = {}
        self.oracle_metrics: Dict[str, OracleMetrics] = {}
        self.active_alerts: List[SecurityAlert] = []
        self.circuit_breakers: Dict[str, bool] = {}
        
        # Statistical models
        self.moving_averages: Dict[str, float] = {}
        self.volatility_models: Dict[str, float] = {}
        self.anomaly_thresholds: Dict[str, float] = {}
        
        # Security thresholds
        self.max_price_deviation = self.config.get('security', {}).get('max_price_deviation', 500)  # 5%
        self.circuit_breaker_threshold = self.config.get('security', {}).get('circuit_breaker_threshold', 1000)  # 10%
        self.min_oracle_consensus = self.config.get('security', {}).get('min_oracle_consensus', 3)
        self.staleness_threshold = self.config.get('security', {}).get('staleness_threshold', 3600)  # 1 hour
        
        logger.info("Enhanced Oracle Security Monitor initialized")
    
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
            'web3': {
                'provider_url': 'http://localhost:8545',
                'gas_limit': 3000000
            },
            'contracts': {
                'secure_multi_oracle': '',
                'oracle_security_wrapper': '',
                'oracle_manipulation_monitor': ''
            },
            'security': {
                'max_price_deviation': 500,  # 5%
                'circuit_breaker_threshold': 1000,  # 10%
                'min_oracle_consensus': 3,
                'staleness_threshold': 3600,  # 1 hour
                'monitoring_interval': 30,  # 30 seconds
                'anomaly_detection_window': 100  # 100 data points
            },
            'alerts': {
                'email_notifications': True,
                'webhook_url': '',
                'telegram_bot_token': '',
                'telegram_chat_id': ''
            }
        }
    
    def _setup_web3(self) -> Web3:
        """Setup Web3 connection"""
        provider_url = self.config.get('web3', {}).get('provider_url', 'http://localhost:8545')
        w3 = Web3(Web3.HTTPProvider(provider_url))
        
        if not w3.is_connected():
            raise ConnectionError(f"Failed to connect to {provider_url}")
        
        logger.info(f"Connected to Web3 at {provider_url}")
        return w3
    
    def _setup_contracts(self) -> Dict:
        """Setup contract instances"""
        contracts = {}
        
        try:
            # Load contract ABIs and addresses
            contract_configs = self.config.get('contracts', {})
            
            for contract_name, address in contract_configs.items():
                if address:
                    # Load ABI file
                    abi_path = f"abi/{contract_name}.json"
                    try:
                        with open(abi_path, 'r') as f:
                            abi = json.load(f)
                        
                        contracts[contract_name] = self.w3.eth.contract(
                            address=self.w3.to_checksum_address(address),
                            abi=abi
                        )
                        logger.info(f"Loaded contract {contract_name} at {address}")
                    except FileNotFoundError:
                        logger.warning(f"ABI file not found for {contract_name}")
                        
        except Exception as e:
            logger.error(f"Error setting up contracts: {e}")
        
        return contracts
    
    async def monitor_oracle_security(self) -> None:
        """Main monitoring loop"""
        logger.info("Starting enhanced oracle security monitoring")
        
        monitoring_interval = self.config.get('security', {}).get('monitoring_interval', 30)
        
        while True:
            try:
                start_time = time.time()
                
                # Collect price data from all oracles
                price_data = await self._collect_price_data()
                
                # Analyze for manipulation patterns
                alerts = await self._analyze_manipulation_patterns(price_data)
                
                # Update oracle performance metrics
                await self._update_oracle_metrics(price_data)
                
                # Check circuit breaker conditions
                await self._check_circuit_breakers(price_data)
                
                # Process and send alerts
                if alerts:
                    await self._process_alerts(alerts)
                
                # Log monitoring cycle
                elapsed = time.time() - start_time
                logger.info(f"Monitoring cycle completed in {elapsed:.2f}s, found {len(alerts)} alerts")
                
                # Sleep until next cycle
                sleep_time = max(0, monitoring_interval - elapsed)
                await asyncio.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(monitoring_interval)
    
    async def _collect_price_data(self) -> List[PriceData]:
        """Collect price data from all configured oracles"""
        price_data = []
        
        try:
            # Get data from SecureMultiOracle
            if 'secure_multi_oracle' in self.contracts:
                oracle_data = await self._get_multi_oracle_data()
                price_data.extend(oracle_data)
            
            # Get data from external sources (Chainlink, etc.)
            external_data = await self._get_external_oracle_data()
            price_data.extend(external_data)
            
        except Exception as e:
            logger.error(f"Error collecting price data: {e}")
        
        return price_data
    
    async def _get_multi_oracle_data(self) -> List[PriceData]:
        """Get price data from SecureMultiOracle contract"""
        price_data = []
        
        try:
            oracle_contract = self.contracts['secure_multi_oracle']
            
            # Get list of tracked assets (this would need to be configured)
            tracked_assets = self.config.get('tracked_assets', [])
            
            for asset in tracked_assets:
                try:
                    # Convert asset symbol to bytes32 price ID
                    price_id = self.w3.keccak(text=asset)
                    
                    # Get consensus price data
                    result = oracle_contract.functions.getPrice(price_id).call()
                    consensus_price, timestamp, deviation, is_valid = result
                    
                    if is_valid and consensus_price > 0:
                        price_data.append(PriceData(
                            asset=asset,
                            price=consensus_price / 1e18,  # Convert from wei
                            timestamp=timestamp,
                            source='SecureMultiOracle',
                            confidence=100 - (deviation / 100),  # Convert deviation to confidence
                            deviation=deviation / 100  # Convert to percentage
                        ))
                    
                except Exception as e:
                    logger.error(f"Error getting price for {asset}: {e}")
            
        except Exception as e:
            logger.error(f"Error accessing SecureMultiOracle: {e}")
        
        return price_data
    
    async def _get_external_oracle_data(self) -> List[PriceData]:
        """Get price data from external oracle sources"""
        price_data = []
        
        # This would integrate with external APIs (Chainlink, CoinGecko, etc.)
        # For now, return empty list
        
        return price_data
    
    async def _analyze_manipulation_patterns(self, price_data: List[PriceData]) -> List[SecurityAlert]:
        """Analyze price data for manipulation patterns"""
        alerts = []
        
        for data in price_data:
            try:
                # Update price history
                if data.asset not in self.price_history:
                    self.price_history[data.asset] = deque(maxlen=100)
                
                self.price_history[data.asset].append(data)
                
                # Perform anomaly detection
                anomalies = await self._detect_price_anomalies(data)
                alerts.extend(anomalies)
                
                # Check for manipulation patterns
                manipulation_alerts = await self._detect_manipulation_patterns(data)
                alerts.extend(manipulation_alerts)
                
            except Exception as e:
                logger.error(f"Error analyzing {data.asset}: {e}")
        
        return alerts
    
    async def _detect_price_anomalies(self, data: PriceData) -> List[SecurityAlert]:
        """Detect price anomalies using statistical analysis"""
        alerts = []
        
        try:
            history = self.price_history.get(data.asset, deque())
            
            if len(history) < 10:  # Need minimum data points
                return alerts
            
            # Calculate moving statistics
            prices = [p.price for p in history]
            mean_price = statistics.mean(prices)
            std_dev = statistics.stdev(prices) if len(prices) > 1 else 0
            
            # Calculate Z-score
            if std_dev > 0:
                z_score = abs(data.price - mean_price) / std_dev
                
                # Z-score > 3 indicates potential anomaly (99.7% confidence)
                if z_score > 3:
                    deviation = abs(data.price - mean_price) / mean_price * 10000  # in basis points
                    
                    severity = 'CRITICAL' if z_score > 5 else 'HIGH'
                    
                    alert = SecurityAlert(
                        alert_id=hashlib.md5(f"{data.asset}_{data.timestamp}_{z_score}".encode()).hexdigest(),
                        alert_type='PRICE_ANOMALY',
                        severity=severity,
                        asset=data.asset,
                        price=data.price,
                        expected_price=mean_price,
                        deviation=deviation,
                        timestamp=data.timestamp,
                        description=f"Price anomaly detected: Z-score {z_score:.2f}"
                    )
                    alerts.append(alert)
            
        except Exception as e:
            logger.error(f"Error in anomaly detection for {data.asset}: {e}")
        
        return alerts
    
    async def _detect_manipulation_patterns(self, data: PriceData) -> List[SecurityAlert]:
        """Detect potential manipulation patterns"""
        alerts = []
        
        try:
            history = self.price_history.get(data.asset, deque())
            
            if len(history) < 5:
                return alerts
            
            # Check for sudden price spikes
            recent_prices = [p.price for p in list(history)[-5:]]
            price_changes = [abs(recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1] 
                           for i in range(1, len(recent_prices))]
            
            # If multiple large price changes in sequence, potential manipulation
            large_changes = [change for change in price_changes if change > 0.05]  # 5%
            
            if len(large_changes) >= 3:
                deviation = max(price_changes) * 10000  # Convert to basis points
                
                alert = SecurityAlert(
                    alert_id=hashlib.md5(f"{data.asset}_manipulation_{data.timestamp}".encode()).hexdigest(),
                    alert_type='MANIPULATION_PATTERN',
                    severity='HIGH',
                    asset=data.asset,
                    price=data.price,
                    expected_price=recent_prices[0],
                    deviation=deviation,
                    timestamp=data.timestamp,
                    description=f"Potential manipulation: {len(large_changes)} large price changes detected"
                )
                alerts.append(alert)
            
        except Exception as e:
            logger.error(f"Error detecting manipulation patterns for {data.asset}: {e}")
        
        return alerts
    
    async def _update_oracle_metrics(self, price_data: List[PriceData]) -> None:
        """Update performance metrics for oracles"""
        try:
            for data in price_data:
                oracle_key = f"{data.source}_{data.asset}"
                
                if oracle_key not in self.oracle_metrics:
                    self.oracle_metrics[oracle_key] = OracleMetrics(
                        oracle_address=data.source,
                        total_updates=0,
                        successful_updates=0,
                        failed_updates=0,
                        average_deviation=0.0,
                        last_update=0,
                        reputation_score=100.0,
                        is_active=True
                    )
                
                metrics = self.oracle_metrics[oracle_key]
                metrics.total_updates += 1
                metrics.successful_updates += 1
                metrics.last_update = data.timestamp
                
                # Update average deviation
                if metrics.total_updates == 1:
                    metrics.average_deviation = data.deviation
                else:
                    metrics.average_deviation = (
                        (metrics.average_deviation * (metrics.total_updates - 1) + data.deviation) /
                        metrics.total_updates
                    )
                
                # Update reputation score based on performance
                if data.deviation > self.max_price_deviation / 100:  # Convert basis points to percentage
                    metrics.reputation_score = max(0, metrics.reputation_score - 1)
                else:
                    metrics.reputation_score = min(100, metrics.reputation_score + 0.1)
                
        except Exception as e:
            logger.error(f"Error updating oracle metrics: {e}")
    
    async def _check_circuit_breakers(self, price_data: List[PriceData]) -> None:
        """Check circuit breaker conditions"""
        try:
            for data in price_data:
                # Convert deviation to basis points for comparison
                deviation_bp = data.deviation * 100
                
                if deviation_bp > self.circuit_breaker_threshold:
                    if not self.circuit_breakers.get(data.asset, False):
                        logger.critical(f"CIRCUIT BREAKER TRIGGERED for {data.asset}: {deviation_bp}bp deviation")
                        self.circuit_breakers[data.asset] = True
                        
                        # Generate critical alert
                        alert = SecurityAlert(
                            alert_id=hashlib.md5(f"cb_{data.asset}_{data.timestamp}".encode()).hexdigest(),
                            alert_type='CIRCUIT_BREAKER',
                            severity='CRITICAL',
                            asset=data.asset,
                            price=data.price,
                            expected_price=data.price,  # Would need to calculate expected
                            deviation=deviation_bp,
                            timestamp=data.timestamp,
                            description=f"Circuit breaker activated: {deviation_bp}bp deviation exceeds threshold"
                        )
                        self.active_alerts.append(alert)
                        
                        # Trigger on-chain circuit breaker if contract available
                        if 'oracle_security_wrapper' in self.contracts:
                            await self._trigger_onchain_circuit_breaker(data.asset)
                
        except Exception as e:
            logger.error(f"Error checking circuit breakers: {e}")
    
    async def _trigger_onchain_circuit_breaker(self, asset: str) -> None:
        """Trigger on-chain circuit breaker"""
        try:
            # This would require proper transaction signing
            logger.info(f"Would trigger on-chain circuit breaker for {asset}")
            # Implementation would depend on available private key management
            
        except Exception as e:
            logger.error(f"Error triggering on-chain circuit breaker: {e}")
    
    async def _process_alerts(self, alerts: List[SecurityAlert]) -> None:
        """Process and send security alerts"""
        try:
            for alert in alerts:
                # Add to active alerts
                self.active_alerts.append(alert)
                
                # Log alert
                logger.warning(f"SECURITY ALERT [{alert.severity}] {alert.alert_type}: {alert.description}")
                
                # Send notifications
                await self._send_alert_notifications(alert)
                
                # Store alert for analysis
                await self._store_alert(alert)
                
        except Exception as e:
            logger.error(f"Error processing alerts: {e}")
    
    async def _send_alert_notifications(self, alert: SecurityAlert) -> None:
        """Send alert notifications via configured channels"""
        try:
            alert_config = self.config.get('alerts', {})
            
            # Email notifications
            if alert_config.get('email_notifications', False):
                await self._send_email_alert(alert)
            
            # Webhook notifications
            webhook_url = alert_config.get('webhook_url')
            if webhook_url:
                await self._send_webhook_alert(alert, webhook_url)
            
            # Telegram notifications
            telegram_config = alert_config.get('telegram_bot_token')
            if telegram_config:
                await self._send_telegram_alert(alert)
                
        except Exception as e:
            logger.error(f"Error sending alert notifications: {e}")
    
    async def _send_email_alert(self, alert: SecurityAlert) -> None:
        """Send email alert (placeholder)"""
        logger.info(f"Would send email alert: {alert.alert_type}")
    
    async def _send_webhook_alert(self, alert: SecurityAlert, webhook_url: str) -> None:
        """Send webhook alert (placeholder)"""
        logger.info(f"Would send webhook alert to {webhook_url}: {alert.alert_type}")
    
    async def _send_telegram_alert(self, alert: SecurityAlert) -> None:
        """Send Telegram alert (placeholder)"""
        logger.info(f"Would send Telegram alert: {alert.alert_type}")
    
    async def _store_alert(self, alert: SecurityAlert) -> None:
        """Store alert for historical analysis"""
        try:
            # Store in JSON format
            alert_data = asdict(alert)
            timestamp = datetime.now().isoformat()
            
            # Write to alerts log file
            with open(f"alerts_{datetime.now().strftime('%Y-%m-%d')}.json", "a") as f:
                f.write(json.dumps(alert_data) + "\n")
                
        except Exception as e:
            logger.error(f"Error storing alert: {e}")
    
    def get_system_status(self) -> Dict:
        """Get current system status"""
        return {
            'timestamp': int(time.time()),
            'active_alerts': len(self.active_alerts),
            'circuit_breakers': self.circuit_breakers,
            'oracle_metrics': {k: asdict(v) for k, v in self.oracle_metrics.items()},
            'monitored_assets': list(self.price_history.keys()),
            'monitoring_status': 'ACTIVE'
        }
    
    def reset_circuit_breaker(self, asset: str) -> bool:
        """Reset circuit breaker for an asset"""
        try:
            if asset in self.circuit_breakers:
                self.circuit_breakers[asset] = False
                logger.info(f"Circuit breaker reset for {asset}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error resetting circuit breaker: {e}")
            return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Oracle Security Monitor")
    parser.add_argument("--config", type=str, default="enhanced_oracle_config.yaml",
                       help="Configuration file path")
    
    args = parser.parse_args()
    
    # Create and start monitor
    monitor = EnhancedOracleSecurityMonitor(args.config)
    
    try:
        asyncio.run(monitor.monitor_oracle_security())
    except KeyboardInterrupt:
        logger.info("Oracle security monitor stopped by user")

if __name__ == "__main__":
    main()
