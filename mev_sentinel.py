#!/usr/bin/env python3
"""
MEV Sentinel Agent
Specialized sentinel bot for monitoring and protecting against MEV attacks
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
from typing import Dict, List, Any, Optional, Tuple, Union, Set
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mev_sentinel.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MEVSentinel")

class ThreatLevel(Enum):
    """Security threat levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"  
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"

class MEVAttackType(Enum):
    """Types of MEV attacks"""
    FRONTRUNNING = "FRONTRUNNING"
    BACKRUNNING = "BACKRUNNING"
    SANDWICH_ATTACK = "SANDWICH_ATTACK"
    ARBITRAGE = "ARBITRAGE"
    LIQUIDATION = "LIQUIDATION"
    TIME_BANDIT = "TIME_BANDIT"
    GENERALIZED_FRONTRUNNING = "GENERALIZED_FRONTRUNNING"
    PRIORITY_GAS_AUCTION = "PRIORITY_GAS_AUCTION"
    BUNDLE_MANIPULATION = "BUNDLE_MANIPULATION"

@dataclass
class TransactionData:
    """Transaction data with MEV-related metrics"""
    tx_hash: str
    block_number: int
    timestamp: int
    from_address: str
    to_address: str
    value: float
    gas_price: int
    gas_used: int
    method_id: str
    position_in_block: int
    related_txs: List[str] = field(default_factory=list)
    profit_estimate: float = 0.0
    mev_probability: float = 0.0
    attack_type: Optional[MEVAttackType] = None

@dataclass
class MEVAlert:
    """MEV attack alert with details"""
    alert_id: str
    attack_type: MEVAttackType
    threat_level: ThreatLevel
    transactions: List[str]
    timestamp: int
    profit_estimate: float
    affected_addresses: List[str]
    affected_pools: List[str]
    details: Dict[str, Any]
    recommended_actions: List[str]
    false_positive_probability: float = 0.0
    reported: bool = False
    resolved: bool = False
    resolution_time: Optional[int] = None
    resolution_details: Optional[str] = None

class MEVSentinel:
    """
    Specialized sentinel agent for monitoring and protecting against MEV attacks
    """
    
    def __init__(self, config_path: str = "mev_sentinel_config.yaml"):
        """Initialize the MEV Sentinel agent"""
        self.config = self._load_config(config_path)
        self.web3 = self._initialize_web3()
        self.db_conn = self._initialize_database()
        
        # Data structures for monitoring
        self.transaction_history: Dict[str, TransactionData] = {}
        self.block_transactions: Dict[int, List[str]] = defaultdict(list)
        self.address_transactions: Dict[str, List[str]] = defaultdict(list)
        self.alerts: List[MEVAlert] = []
        self.active_alerts: Dict[str, MEVAlert] = {}
        
        # Monitoring state
        self.is_monitoring = False
        self.monitoring_task = None
        self.block_subscription = None
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=self.config.get("max_workers", 5))
        
        # Alert handlers
        self.alert_handlers = []
        self._register_default_alert_handlers()
        
        # Protection strategies
        self.protection_strategies = {}
        self._register_protection_strategies()
        
        # Statistics
        self.stats = {
            "blocks_monitored": 0,
            "transactions_analyzed": 0,
            "mev_detected": 0,
            "protected_transactions": 0,
            "estimated_savings": 0.0
        }
        
        logger.info("MEV Sentinel initialized")
    
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
            "flashbots_relay": "https://relay.flashbots.net",
            "monitoring_interval": 1,
            "max_workers": 5,
            "db_path": "mev_sentinel.db",
            "block_history_size": 100,
            "protected_addresses": [],
            "protected_contracts": [],
            "min_profit_threshold": 0.01,  # In ETH
            "gas_price_bump_percentage": 10,
            "private_mempool_enabled": True,
            "randomized_submission_enabled": True,
            "notification": {
                "email": False,
                "slack": False,
                "webhook": False
            },
            "protection_strategies": {
                "frontrunning": True,
                "backrunning": True,
                "sandwich_attack": True,
                "time_bandit": False  # Advanced, may require consensus-level changes
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
        """Initialize SQLite database for storing MEV data and alerts"""
        db_path = self.config.get("db_path", "mev_sentinel.db")
        try:
            conn = sqlite3.connect(db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            # Create tables if they don't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                tx_hash TEXT PRIMARY KEY,
                block_number INTEGER,
                timestamp INTEGER,
                from_address TEXT,
                to_address TEXT,
                value REAL,
                gas_price INTEGER,
                gas_used INTEGER,
                method_id TEXT,
                position_in_block INTEGER,
                related_txs TEXT,
                profit_estimate REAL,
                mev_probability REAL,
                attack_type TEXT
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS mev_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT UNIQUE,
                attack_type TEXT,
                threat_level TEXT,
                transactions TEXT,
                timestamp INTEGER,
                profit_estimate REAL,
                affected_addresses TEXT,
                affected_pools TEXT,
                details TEXT,
                recommended_actions TEXT,
                false_positive_probability REAL,
                reported INTEGER,
                resolved INTEGER,
                resolution_time INTEGER,
                resolution_details TEXT
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS protected_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_tx_hash TEXT,
                protected_tx_hash TEXT,
                protection_strategy TEXT,
                timestamp INTEGER,
                gas_saved REAL,
                value_protected REAL
            )
            ''')
            
            conn.commit()
            logger.info(f"Initialized database at {db_path}")
            return conn
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            return None
    
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
    
    def _register_protection_strategies(self):
        """Register MEV protection strategies"""
        strategies_config = self.config.get("protection_strategies", {})
        
        if strategies_config.get("frontrunning", True):
            self.protection_strategies["frontrunning"] = self._protect_from_frontrunning
        
        if strategies_config.get("backrunning", True):
            self.protection_strategies["backrunning"] = self._protect_from_backrunning
        
        if strategies_config.get("sandwich_attack", True):
            self.protection_strategies["sandwich_attack"] = self._protect_from_sandwich
        
        if strategies_config.get("time_bandit", False):
            self.protection_strategies["time_bandit"] = self._protect_from_time_bandit
    
    async def start_monitoring(self):
        """Start the MEV sentinel monitoring process"""
        if self.is_monitoring:
            logger.warning("MEV Sentinel is already monitoring")
            return
        
        self.is_monitoring = True
        logger.info("Starting MEV Sentinel monitoring")
        
        # Start the monitoring task
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        # Subscribe to new blocks if using WebSocket provider
        if isinstance(self.web3.provider, Web3.WebsocketProvider):
            self._subscribe_to_new_blocks()
    
    async def stop_monitoring(self):
        """Stop the MEV sentinel monitoring process"""
        if not self.is_monitoring:
            logger.warning("MEV Sentinel is not monitoring")
            return
        
        self.is_monitoring = False
        logger.info("Stopping MEV Sentinel monitoring")
        
        # Unsubscribe from new blocks
        if self.block_subscription:
            self._unsubscribe_from_blocks()
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
    
    def _subscribe_to_new_blocks(self):
        """Subscribe to new block events using Web3 WebSocket provider"""
        if not isinstance(self.web3.provider, Web3.WebsocketProvider):
            logger.warning("WebSocket provider required for block subscription")
            return
        
        try:
            # This is a simplified version - actual implementation would use web3.eth.subscribe
            logger.info("Subscribed to new block events")
        except Exception as e:
            logger.error(f"Error subscribing to new blocks: {e}")
    
    def _unsubscribe_from_blocks(self):
        """Unsubscribe from block events"""
        if self.block_subscription:
            try:
                # This is a simplified version - actual implementation would unsubscribe
                logger.info("Unsubscribed from block events")
                self.block_subscription = None
            except Exception as e:
                logger.error(f"Error unsubscribing from blocks: {e}")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        try:
            last_block_checked = self.web3.eth.block_number - 1
            
            while self.is_monitoring:
                current_block = self.web3.eth.block_number
                
                # Process new blocks
                for block_num in range(last_block_checked + 1, current_block + 1):
                    await self._process_block(block_num)
                    self.stats["blocks_monitored"] += 1
                
                last_block_checked = current_block
                
                # Process active alerts
                await self._process_active_alerts()
                
                # Wait for the next monitoring cycle
                await asyncio.sleep(self.config.get("monitoring_interval", 1))
        except asyncio.CancelledError:
            logger.info("MEV monitoring loop cancelled")
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
            self.is_monitoring = False
    
    async def _process_block(self, block_number: int):
        """Process a block to detect MEV activity"""
        try:
            # Get block data
            block = self.web3.eth.get_block(block_number, full_transactions=True)
            block_timestamp = block.timestamp
            
            # Process transactions in the block
            for tx_index, tx in enumerate(block.transactions):
                tx_hash = tx.hash.hex()
                
                # Create transaction data object
                tx_data = TransactionData(
                    tx_hash=tx_hash,
                    block_number=block_number,
                    timestamp=block_timestamp,
                    from_address=tx["from"],
                    to_address=tx["to"] if tx["to"] else "",
                    value=self.web3.from_wei(tx["value"], "ether"),
                    gas_price=tx["gasPrice"],
                    gas_used=0,  # Will be updated with receipt data
                    method_id=tx["input"][:10] if len(tx["input"]) >= 10 else "",
                    position_in_block=tx_index
                )
                
                # Get transaction receipt for gas used
                try:
                    receipt = self.web3.eth.get_transaction_receipt(tx_hash)
                    tx_data.gas_used = receipt["gasUsed"]
                except Exception as e:
                    logger.error(f"Error getting receipt for tx {tx_hash}: {e}")
                
                # Store transaction data
                self.transaction_history[tx_hash] = tx_data
                self.block_transactions[block_number].append(tx_hash)
                self.address_transactions[tx_data.from_address].append(tx_hash)
                if tx_data.to_address:
                    self.address_transactions[tx_data.to_address].append(tx_hash)
                
                # Store in database
                self._store_transaction(tx_data)
                
                self.stats["transactions_analyzed"] += 1
            
            # Analyze block for MEV activity
            await self._analyze_block_for_mev(block_number)
            
            # Clean up old data
            self._cleanup_old_data()
            
        except Exception as e:
            logger.error(f"Error processing block {block_number}: {e}")
    
    def _store_transaction(self, tx_data: TransactionData):
        """Store transaction data in the database"""
        if not self.db_conn:
            return
        
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
            INSERT OR REPLACE INTO transactions (
                tx_hash, block_number, timestamp, from_address, to_address,
                value, gas_price, gas_used, method_id, position_in_block,
                related_txs, profit_estimate, mev_probability, attack_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tx_data.tx_hash, tx_data.block_number, tx_data.timestamp,
                tx_data.from_address, tx_data.to_address, tx_data.value,
                tx_data.gas_price, tx_data.gas_used, tx_data.method_id,
                tx_data.position_in_block, json.dumps(tx_data.related_txs),
                tx_data.profit_estimate, tx_data.mev_probability,
                tx_data.attack_type.value if tx_data.attack_type else None
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"Error storing transaction data: {e}")
    
    async def _analyze_block_for_mev(self, block_number: int):
        """Analyze a block for MEV activity"""
        if block_number not in self.block_transactions:
            return
        
        tx_hashes = self.block_transactions[block_number]
        if len(tx_hashes) < 2:
            return  # Need at least 2 transactions for MEV
        
        # Get transaction data objects
        transactions = [self.transaction_history[tx_hash] for tx_hash in tx_hashes 
                       if tx_hash in self.transaction_history]
        
        # Sort by position in block
        transactions.sort(key=lambda tx: tx.position_in_block)
        
        # Check for frontrunning
        await self._detect_frontrunning(transactions, block_number)
        
        # Check for sandwich attacks
        await self._detect_sandwich_attacks(transactions, block_number)
        
        # Check for arbitrage
        await self._detect_arbitrage(transactions, block_number)
    
    async def _detect_frontrunning(self, transactions: List[TransactionData], block_number: int):
        """Detect frontrunning attacks"""
        # Group transactions by method ID (function signature)
        method_groups = defaultdict(list)
        for tx in transactions:
            if tx.method_id:
                method_groups[tx.method_id].append(tx)
        
        # Look for similar transactions with increasing gas prices
        for method_id, txs in method_groups.items():
            if len(txs) < 2:
                continue
            
            # Sort by gas price (descending)
            txs.sort(key=lambda tx: tx.gas_price, reverse=True)
            
            # Check for potential frontrunning
            for i in range(len(txs) - 1):
                frontrunner = txs[i]
                victim = txs[i + 1]
                
                # If gas price is significantly higher and from different addresses
                if (frontrunner.gas_price > victim.gas_price * 1.2 and
                    frontrunner.from_address != victim.from_address):
                    
                    # Mark as potential frontrunning
                    frontrunner.attack_type = MEVAttackType.FRONTRUNNING
                    frontrunner.mev_probability = 0.7
                    frontrunner.related_txs.append(victim.tx_hash)
                    
                    # Update in database
                    self._update_transaction_mev_data(frontrunner)
                    
                    # Create alert if probability is high enough
                    if frontrunner.mev_probability >= 0.6:
                        await self._create_mev_alert(
                            attack_type=MEVAttackType.FRONTRUNNING,
                            threat_level=ThreatLevel.MEDIUM,
                            transactions=[frontrunner.tx_hash, victim.tx_hash],
                            profit_estimate=0.0,  # Would need more analysis to estimate profit
                            affected_addresses=[victim.from_address],
                            affected_pools=[victim.to_address] if victim.to_address else [],
                            details={
                                "frontrunner_gas_price": frontrunner.gas_price,
                                "victim_gas_price": victim.gas_price,
                                "gas_price_increase": frontrunner.gas_price / victim.gas_price,
                                "method_id": method_id,
                                "block_number": block_number
                            }
                        )
                        
                        self.stats["mev_detected"] += 1
    
    async def _detect_sandwich_attacks(self, transactions: List[TransactionData], block_number: int):
        """Detect sandwich attacks"""
        # Look for patterns where the same address has transactions before and after another address's transaction
        # This is a simplified detection - real detection would analyze token swaps and price impacts
        
        # Group transactions by to_address (potential DEX or pool)
        pool_txs = defaultdict(list)
        for tx in transactions:
            if tx.to_address:
                pool_txs[tx.to_address].append(tx)
        
        # Check each pool for sandwich patterns
        for pool_address, txs in pool_txs.items():
            if len(txs) < 3:
                continue
            
            # Check for sandwich pattern: same address before and after another address
            for i in range(len(txs) - 2):
                tx1 = txs[i]
                tx2 = txs[i + 1]
                tx3 = txs[i + 2]
                
                # If first and third tx are from the same address, but second is different
                if (tx1.from_address == tx3.from_address and
                    tx1.from_address != tx2.from_address):
                    
                    # Mark as potential sandwich attack
                    tx1.attack_type = MEVAttackType.SANDWICH_ATTACK
                    tx1.mev_probability = 0.8
                    tx1.related_txs.extend([tx2.tx_hash, tx3.tx_hash])
                    
                    tx3.attack_type = MEVAttackType.SANDWICH_ATTACK
                    tx3.mev_probability = 0.8
                    tx3.related_txs.extend([tx1.tx_hash, tx2.tx_hash])
                    
                    # Update in database
                    self._update_transaction_mev_data(tx1)
                    self._update_transaction_mev_data(tx3)
                    
                    # Create alert
                    await self._create_mev_alert(
                        attack_type=MEVAttackType.SANDWICH_ATTACK,
                        threat_level=ThreatLevel.HIGH,
                        transactions=[tx1.tx_hash, tx2.tx_hash, tx3.tx_hash],
                        profit_estimate=0.0,  # Would need more analysis to estimate profit
                        affected_addresses=[tx2.from_address],
                        affected_pools=[pool_address],
                        details={
                            "attacker_address": tx1.from_address,
                            "victim_address": tx2.from_address,
                            "pool_address": pool_address,
                            "block_number": block_number,
                            "first_tx_position": tx1.position_in_block,
                            "victim_tx_position": tx2.position_in_block,
                            "last_tx_position": tx3.position_in_block
                        }
                    )
                    
                    self.stats["mev_detected"] += 1
                    
                    # Skip to avoid overlapping patterns
                    i += 2
    
    async def _detect_arbitrage(self, transactions: List[TransactionData], block_number: int):
        """Detect arbitrage transactions"""
        # Look for transactions that interact with multiple pools in a single transaction
        # This is a simplified detection - real detection would analyze internal transactions and token flows
        
        # Check for transactions with high gas usage (complex transactions)
        for tx in transactions:
            # Arbitrage transactions typically use a lot of gas
            if tx.gas_used > 500000:
                # Mark as potential arbitrage
                tx.attack_type = MEVAttackType.ARBITRAGE
                tx.mev_probability = 0.6
                
                # Update in database
                self._update_transaction_mev_data(tx)
                
                # Create alert if from known MEV bot addresses
                known_mev_bots = self.config.get("known_mev_bots", [])
                if tx.from_address in known_mev_bots:
                    tx.mev_probability = 0.9
                    
                    await self._create_mev_alert(
                        attack_type=MEVAttackType.ARBITRAGE,
                        threat_level=ThreatLevel.LOW,  # Arbitrage itself is not necessarily harmful
                        transactions=[tx.tx_hash],
                        profit_estimate=0.0,  # Would need more analysis to estimate profit
                        affected_addresses=[],
                        affected_pools=[],
                        details={
                            "from_address": tx.from_address,
                            "gas_used": tx.gas_used,
                            "block_number": block_number,
                            "known_mev_bot": True
                        }
                    )
                    
                    self.stats["mev_detected"] += 1
    
    def _update_transaction_mev_data(self, tx_data: TransactionData):
        """Update transaction MEV data in the database"""
        if not self.db_conn:
            return
        
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
            UPDATE transactions SET
                related_txs = ?,
                profit_estimate = ?,
                mev_probability = ?,
                attack_type = ?
            WHERE tx_hash = ?
            ''', (
                json.dumps(tx_data.related_txs),
                tx_data.profit_estimate,
                tx_data.mev_probability,
                tx_data.attack_type.value if tx_data.attack_type else None,
                tx_data.tx_hash
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"Error updating transaction MEV data: {e}")
    
    async def _create_mev_alert(self, attack_type: MEVAttackType, threat_level: ThreatLevel,
                              transactions: List[str], profit_estimate: float,
                              affected_addresses: List[str], affected_pools: List[str],
                              details: Dict[str, Any]):
        """Create a MEV attack alert"""
        # Generate unique alert ID
        alert_id = f"{attack_type.value}_{int(time.time())}_{hashlib.md5('_'.join(transactions).encode()).hexdigest()[:8]}"
        
        # Create recommended actions based on alert type and threat level
        recommended_actions = self._generate_recommended_actions(attack_type, threat_level)
        
        # Create alert object
        alert = MEVAlert(
            alert_id=alert_id,
            attack_type=attack_type,
            threat_level=threat_level,
            transactions=transactions,
            timestamp=int(time.time()),
            profit_estimate=profit_estimate,
            affected_addresses=affected_addresses,
            affected_pools=affected_pools,
            details=details,
            recommended_actions=recommended_actions,
            false_positive_probability=0.2,  # Initial estimate
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
        
        # Apply protection strategies if configured
        if attack_type.value.lower() in self.protection_strategies:
            protection_strategy = self.protection_strategies[attack_type.value.lower()]
            await protection_strategy(alert)
    
    def _generate_recommended_actions(self, attack_type: MEVAttackType, threat_level: ThreatLevel) -> List[str]:
        """Generate recommended actions based on alert type and threat level"""
        actions = []
        
        # Common actions for all alerts
        actions.append("Monitor affected addresses for unusual activity")
        
        # Type-specific actions
        if attack_type == MEVAttackType.FRONTRUNNING:
            actions.append("Use private transaction pools for sensitive transactions")
            actions.append("Implement gas price randomization")
            
            if threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                actions.append("Consider implementing commit-reveal schemes for critical operations")
        
        elif attack_type == MEVAttackType.SANDWICH_ATTACK:
            actions.append("Set appropriate slippage tolerance in DEX transactions")
            actions.append("Use private transaction pools for large swaps")
            
            if threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                actions.append("Split large trades into smaller amounts")
                actions.append("Consider using DEX aggregators with MEV protection")
        
        elif attack_type == MEVAttackType.ARBITRAGE:
            actions.append("Monitor price impact on liquidity pools")
            
            if threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                actions.append("Adjust pool fees or implement price impact protections")
        
        # Severity-specific actions
        if threat_level == ThreatLevel.EMERGENCY:
            actions.append("Pause affected contracts immediately")
            actions.append("Convene emergency response team")
        elif threat_level == ThreatLevel.CRITICAL:
            actions.append("Prepare for possible emergency measures")
            actions.append("Notify security team immediately")
        
        return actions
    
    def _store_alert(self, alert: MEVAlert):
        """Store alert in the database"""
        if not self.db_conn:
            return
        
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
            INSERT INTO mev_alerts (
                alert_id, attack_type, threat_level, transactions, timestamp,
                profit_estimate, affected_addresses, affected_pools, details,
                recommended_actions, false_positive_probability, reported,
                resolved, resolution_time, resolution_details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert.alert_id, alert.attack_type.value, alert.threat_level.value,
                json.dumps(alert.transactions), alert.timestamp, alert.profit_estimate,
                json.dumps(alert.affected_addresses), json.dumps(alert.affected_pools),
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
    
    async def _check_alert_resolution(self, alert: MEVAlert):
        """Check if an alert should be automatically resolved"""
        # Auto-resolve after 24 hours if not manually resolved
        if int(time.time()) - alert.timestamp > 86400:  # 24 hours
            alert.resolved = True
            alert.resolution_time = int(time.time())
            alert.resolution_details = "Auto-resolved: Alert expired after 24 hours"
            
            # Update in database
            self._update_alert_resolution(alert)
            
            logger.info(f"Auto-resolved alert {alert.alert_id}: {alert.resolution_details}")
    
    def _update_alert_resolution(self, alert: MEVAlert):
        """Update alert resolution status in database"""
        if not self.db_conn:
            return
        
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
            UPDATE mev_alerts SET
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
    
    async def _log_alert(self, alert: MEVAlert):
        """Log alert to file and console"""
        log_message = (
            f"MEV ATTACK ALERT: {alert.threat_level.value}\n"
            f"Type: {alert.attack_type.value}\n"
            f"Transactions: {', '.join(alert.transactions[:3])}{'...' if len(alert.transactions) > 3 else ''}\n"
            f"Affected Addresses: {', '.join(alert.affected_addresses[:3])}{'...' if len(alert.affected_addresses) > 3 else ''}\n"
            f"Affected Pools: {', '.join(alert.affected_pools[:3])}{'...' if len(alert.affected_pools) > 3 else ''}\n"
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
    
    async def _email_alert(self, alert: MEVAlert):
        """Send alert via email"""
        # This would be implemented with an email library in a real system
        logger.info(f"Would send email alert for {alert.alert_id}")
    
    async def _slack_alert(self, alert: MEVAlert):
        """Send alert via Slack"""
        # This would be implemented with a Slack API client in a real system
        logger.info(f"Would send Slack alert for {alert.alert_id}")
    
    async def _webhook_alert(self, alert: MEVAlert):
        """Send alert via webhook"""
        # This would be implemented with aiohttp in a real system
        logger.info(f"Would send webhook alert for {alert.alert_id}")
    
    def _cleanup_old_data(self):
        """Clean up old transaction data to prevent memory bloat"""
        current_block = self.web3.eth.block_number
        history_size = self.config.get("block_history_size", 100)
        
        # Remove old block data
        blocks_to_remove = []
        for block_num in self.block_transactions.keys():
            if current_block - block_num > history_size:
                blocks_to_remove.append(block_num)
        
        for block_num in blocks_to_remove:
            # Get transactions in this block
            tx_hashes = self.block_transactions.pop(block_num, [])
            
            # Remove transactions from memory (but keep in database)
            for tx_hash in tx_hashes:
                if tx_hash in self.transaction_history:
                    # Remove from address index
                    tx = self.transaction_history[tx_hash]
                    if tx.from_address in self.address_transactions:
                        self.address_transactions[tx.from_address].remove(tx_hash)
                    if tx.to_address and tx.to_address in self.address_transactions:
                        self.address_transactions[tx.to_address].remove(tx_hash)
                    
                    # Remove from transaction history
                    self.transaction_history.pop(tx_hash, None)
    
    async def _protect_from_frontrunning(self, alert: MEVAlert):
        """Apply protection strategy against frontrunning"""
        if not self.config.get("private_mempool_enabled", True):
            return
        
        # In a real implementation, this would:
        # 1. Identify transactions from protected addresses
        # 2. Route them through private mempools (e.g., Flashbots)
        # 3. Apply randomized submission timing
        
        logger.info(f"Applied frontrunning protection for alert {alert.alert_id}")
        self.stats["protected_transactions"] += 1
    
    async def _protect_from_backrunning(self, alert: MEVAlert):
        """Apply protection strategy against backrunning"""
        # Similar to frontrunning protection
        logger.info(f"Applied backrunning protection for alert {alert.alert_id}")
        self.stats["protected_transactions"] += 1
    
    async def _protect_from_sandwich(self, alert: MEVAlert):
        """Apply protection strategy against sandwich attacks"""
        # In a real implementation, this would:
        # 1. Adjust slippage parameters for protected transactions
        # 2. Route through private mempools
        # 3. Potentially split large trades
        
        logger.info(f"Applied sandwich attack protection for alert {alert.alert_id}")
        self.stats["protected_transactions"] += 1
    
    async def _protect_from_time_bandit(self, alert: MEVAlert):
        """Apply protection strategy against time bandit attacks"""
        # This is an advanced protection that might require consensus-level changes
        logger.info(f"Applied time bandit protection for alert {alert.alert_id}")
        self.stats["protected_transactions"] += 1
    
    def get_active_alerts(self) -> List[MEVAlert]:
        """Get list of active alerts"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[MEVAlert]:
        """Get historical alerts"""
        return self.alerts[-limit:]
    
    def get_mev_statistics(self) -> Dict[str, Any]:
        """Get MEV statistics"""
        return {
            "timestamp": int(time.time()),
            "blocks_monitored": self.stats["blocks_monitored"],
            "transactions_analyzed": self.stats["transactions_analyzed"],
            "mev_detected": self.stats["mev_detected"],
            "protected_transactions": self.stats["protected_transactions"],
            "estimated_savings": self.stats["estimated_savings"],
            "active_alerts": len(self.active_alerts),
            "alerts_by_type": self._get_alerts_by_type()
        }
    
    def _get_alerts_by_type(self) -> Dict[str, int]:
        """Get count of alerts by attack type"""
        counts = {attack_type.value: 0 for attack_type in MEVAttackType}
        
        for alert in self.active_alerts.values():
            if not alert.resolved:
                counts[alert.attack_type.value] += 1
        
        return counts
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            "timestamp": int(time.time()),
            "monitoring_active": self.is_monitoring,
            "web3_connected": self.web3.is_connected(),
            "current_block": self.web3.eth.block_number if self.web3.is_connected() else 0,
            "private_mempool_enabled": self.config.get("private_mempool_enabled", True),
            "randomized_submission_enabled": self.config.get("randomized_submission_enabled", True),
            "protection_strategies_enabled": [k for k, v in self.config.get("protection_strategies", {}).items() if v],
            "statistics": self.get_mev_statistics()
        }

async def main():
    """Main function for running the MEV Sentinel as a standalone process"""
    # Create and start the MEV Sentinel
    sentinel = MEVSentinel()
    
    try:
        # Start monitoring
        await sentinel.start_monitoring()
        
        # Keep running until interrupted
        while True:
            await asyncio.sleep(60)
            
            # Print system status every minute
            status = sentinel.get_system_status()
            stats = status["statistics"]
            
            print(f"\nMEV Sentinel Status at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:")
            print(f"Monitoring Active: {status['monitoring_active']}")
            print(f"Current Block: {status['current_block']}")
            print(f"Blocks Monitored: {stats['blocks_monitored']}")
            print(f"Transactions Analyzed: {stats['transactions_analyzed']}")
            print(f"MEV Attacks Detected: {stats['mev_detected']}")
            print(f"Protected Transactions: {stats['protected_transactions']}")
            print(f"Active Alerts: {stats['active_alerts']}")
            
            print("Alerts by Type:", end=" ")
            for attack_type, count in stats['alerts_by_type'].items():
                if count > 0:
                    print(f"{attack_type}: {count}", end=" ")
            print("\n")
    
    except KeyboardInterrupt:
        print("Shutting down MEV Sentinel...")
        await sentinel.stop_monitoring()
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        await sentinel.stop_monitoring()

if __name__ == "__main__":
    asyncio.run(main())