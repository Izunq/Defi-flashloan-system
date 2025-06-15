#!/usr/bin/env python3
"""
Strategy Sentinel Agent
Specialized sentinel bot for monitoring trading strategy execution and performance
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
        logging.FileHandler("strategy_sentinel.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("StrategySentinel")

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"

class StrategyStatus(Enum):
    """Strategy execution status"""
    PENDING = "PENDING"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"

class PerformanceMetric(Enum):
    """Strategy performance metrics"""
    PROFIT_LOSS = "PROFIT_LOSS"
    ROI = "ROI"
    EXECUTION_TIME = "EXECUTION_TIME"
    GAS_EFFICIENCY = "GAS_EFFICIENCY"
    SUCCESS_RATE = "SUCCESS_RATE"
    SLIPPAGE = "SLIPPAGE"
    PRICE_IMPACT = "PRICE_IMPACT"
    OPPORTUNITY_CAPTURE = "OPPORTUNITY_CAPTURE"

@dataclass
class StrategyExecution:
    """Strategy execution data"""
    execution_id: str
    strategy_name: str
    start_time: int
    end_time: Optional[int] = None
    status: StrategyStatus = StrategyStatus.PENDING
    parameters: Dict[str, Any] = field(default_factory=dict)
    transactions: List[str] = field(default_factory=list)
    assets_involved: List[str] = field(default_factory=list)
    initial_capital: float = 0.0
    final_capital: Optional[float] = None
    profit_loss: Optional[float] = None
    gas_used: int = 0
    gas_cost: float = 0.0
    error_message: Optional[str] = None
    performance_metrics: Dict[str, float] = field(default_factory=dict)

@dataclass
class StrategyAlert:
    """Strategy monitoring alert"""
    alert_id: str
    alert_level: AlertLevel
    strategy_name: str
    execution_id: Optional[str]
    timestamp: int
    message: str
    details: Dict[str, Any]
    recommended_actions: List[str]
    resolved: bool = False
    resolution_time: Optional[int] = None
    resolution_details: Optional[str] = None

class StrategySentinel:
    """
    Specialized sentinel agent for monitoring trading strategy execution and performance
    """
    
    def __init__(self, config_path: str = "strategy_sentinel_config.yaml"):
        """Initialize the Strategy Sentinel agent"""
        self.config = self._load_config(config_path)
        self.web3 = self._initialize_web3()
        self.db_conn = self._initialize_database()
        
        # Data structures for monitoring
        self.strategy_executions: Dict[str, StrategyExecution] = {}
        self.active_executions: Dict[str, StrategyExecution] = {}
        self.strategy_history: Dict[str, List[StrategyExecution]] = defaultdict(list)
        self.alerts: List[StrategyAlert] = []
        self.active_alerts: Dict[str, StrategyAlert] = {}
        
        # Performance baselines for strategies
        self.performance_baselines: Dict[str, Dict[str, float]] = {}
        self._load_performance_baselines()
        
        # Monitoring state
        self.is_monitoring = False
        self.monitoring_task = None
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=self.config.get("max_workers", 5))
        
        # Alert handlers
        self.alert_handlers = []
        self._register_default_alert_handlers()
        
        # Strategy abort handlers
        self.abort_handlers = {}
        self._register_abort_handlers()
        
        # Statistics
        self.stats = {
            "strategies_monitored": 0,
            "executions_tracked": 0,
            "alerts_generated": 0,
            "aborted_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_profit": 0.0,
            "total_gas_cost": 0.0
        }
        
        logger.info("Strategy Sentinel initialized")
    
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
            "monitoring_interval": 5,
            "max_workers": 5,
            "db_path": "strategy_sentinel.db",
            "performance_baselines_path": "strategy_performance_baselines.json",
            "alert_thresholds": {
                "profit_loss_deviation": 0.2,  # 20% deviation from baseline
                "execution_time_max_deviation": 0.5,  # 50% longer than baseline
                "gas_cost_max_deviation": 0.3,  # 30% higher than baseline
                "slippage_max": 0.02,  # 2% max slippage
                "price_impact_max": 0.03  # 3% max price impact
            },
            "strategies": {
                "arbitrage_v1": {
                    "max_execution_time": 60,  # seconds
                    "min_profit_threshold": 0.001,  # ETH
                    "max_gas_cost": 0.01,  # ETH
                    "abort_on_slippage_above": 0.03  # 3%
                },
                "flashloan_arbitrage": {
                    "max_execution_time": 30,
                    "min_profit_threshold": 0.005,
                    "max_gas_cost": 0.02,
                    "abort_on_slippage_above": 0.02
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
        """Initialize SQLite database for storing strategy execution data and alerts"""
        db_path = self.config.get("db_path", "strategy_sentinel.db")
        try:
            conn = sqlite3.connect(db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            # Create tables if they don't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategy_executions (
                execution_id TEXT PRIMARY KEY,
                strategy_name TEXT,
                start_time INTEGER,
                end_time INTEGER,
                status TEXT,
                parameters TEXT,
                transactions TEXT,
                assets_involved TEXT,
                initial_capital REAL,
                final_capital REAL,
                profit_loss REAL,
                gas_used INTEGER,
                gas_cost REAL,
                error_message TEXT,
                performance_metrics TEXT
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategy_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT UNIQUE,
                alert_level TEXT,
                strategy_name TEXT,
                execution_id TEXT,
                timestamp INTEGER,
                message TEXT,
                details TEXT,
                recommended_actions TEXT,
                resolved INTEGER,
                resolution_time INTEGER,
                resolution_details TEXT
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_baselines (
                strategy_name TEXT PRIMARY KEY,
                profit_loss REAL,
                roi REAL,
                execution_time REAL,
                gas_efficiency REAL,
                success_rate REAL,
                slippage REAL,
                price_impact REAL,
                opportunity_capture REAL,
                last_updated INTEGER
            )
            ''')
            
            conn.commit()
            logger.info(f"Initialized database at {db_path}")
            return conn
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            return None
    
    def _load_performance_baselines(self):
        """Load performance baselines from file or database"""
        # Try to load from file first
        baselines_path = self.config.get("performance_baselines_path", "strategy_performance_baselines.json")
        try:
            with open(baselines_path, 'r') as f:
                self.performance_baselines = json.load(f)
            logger.info(f"Loaded performance baselines from {baselines_path}")
            return
        except FileNotFoundError:
            logger.info(f"Performance baselines file {baselines_path} not found, checking database")
        except Exception as e:
            logger.error(f"Error loading performance baselines from file: {e}")
        
        # If file not found or error, try to load from database
        if self.db_conn:
            try:
                cursor = self.db_conn.cursor()
                cursor.execute("SELECT * FROM performance_baselines")
                rows = cursor.fetchall()
                
                for row in rows:
                    strategy_name = row[0]
                    self.performance_baselines[strategy_name] = {
                        PerformanceMetric.PROFIT_LOSS.value: row[1],
                        PerformanceMetric.ROI.value: row[2],
                        PerformanceMetric.EXECUTION_TIME.value: row[3],
                        PerformanceMetric.GAS_EFFICIENCY.value: row[4],
                        PerformanceMetric.SUCCESS_RATE.value: row[5],
                        PerformanceMetric.SLIPPAGE.value: row[6],
                        PerformanceMetric.PRICE_IMPACT.value: row[7],
                        PerformanceMetric.OPPORTUNITY_CAPTURE.value: row[8]
                    }
                
                logger.info(f"Loaded performance baselines for {len(rows)} strategies from database")
            except Exception as e:
                logger.error(f"Error loading performance baselines from database: {e}")
                # Initialize with empty baselines
                self.performance_baselines = {}
    
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
    
    def _register_abort_handlers(self):
        """Register strategy abort handlers"""
        # Register default abort handlers for each strategy type
        for strategy_name in self.config.get("strategies", {}).keys():
            self.abort_handlers[strategy_name] = self._default_abort_handler
    
    async def start_monitoring(self):
        """Start the strategy sentinel monitoring process"""
        if self.is_monitoring:
            logger.warning("Strategy Sentinel is already monitoring")
            return
        
        self.is_monitoring = True
        logger.info("Starting Strategy Sentinel monitoring")
        
        # Start the monitoring task
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self):
        """Stop the strategy sentinel monitoring process"""
        if not self.is_monitoring:
            logger.warning("Strategy Sentinel is not monitoring")
            return
        
        self.is_monitoring = False
        logger.info("Stopping Strategy Sentinel monitoring")
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        try:
            while self.is_monitoring:
                logger.debug("Running strategy monitoring cycle")
                
                # Monitor active strategy executions
                await self._monitor_active_executions()
                
                # Process active alerts
                await self._process_active_alerts()
                
                # Update performance baselines periodically
                if int(time.time()) % 3600 < self.config.get("monitoring_interval", 5):  # Once per hour
                    self._update_performance_baselines()
                
                # Wait for the next monitoring cycle
                await asyncio.sleep(self.config.get("monitoring_interval", 5))
        except asyncio.CancelledError:
            logger.info("Strategy monitoring loop cancelled")
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
            self.is_monitoring = False
    
    async def register_strategy_execution(self, strategy_name: str, parameters: Dict[str, Any],
                                        initial_capital: float, assets_involved: List[str]) -> str:
        """Register a new strategy execution for monitoring"""
        # Generate unique execution ID
        execution_id = f"{strategy_name}_{int(time.time())}_{hashlib.md5(json.dumps(parameters).encode()).hexdigest()[:8]}"
        
        # Create execution object
        execution = StrategyExecution(
            execution_id=execution_id,
            strategy_name=strategy_name,
            start_time=int(time.time()),
            status=StrategyStatus.PENDING,
            parameters=parameters,
            assets_involved=assets_involved,
            initial_capital=initial_capital
        )
        
        # Store execution
        self.strategy_executions[execution_id] = execution
        self.active_executions[execution_id] = execution
        self.strategy_history[strategy_name].append(execution)
        
        # Store in database
        self._store_execution(execution)
        
        self.stats["executions_tracked"] += 1
        if strategy_name not in [s["strategy_name"] for s in self.stats.get("strategies", [])]:
            self.stats["strategies_monitored"] += 1
        
        logger.info(f"Registered new strategy execution: {execution_id} ({strategy_name})")
        
        return execution_id
    
    async def update_execution_status(self, execution_id: str, status: StrategyStatus,
                                    transactions: Optional[List[str]] = None,
                                    final_capital: Optional[float] = None,
                                    gas_used: Optional[int] = None,
                                    gas_cost: Optional[float] = None,
                                    error_message: Optional[str] = None) -> bool:
        """Update the status of a strategy execution"""
        if execution_id not in self.strategy_executions:
            logger.warning(f"Execution ID {execution_id} not found")
            return False
        
        execution = self.strategy_executions[execution_id]
        
        # Update status
        execution.status = status
        
        # Update other fields if provided
        if transactions is not None:
            execution.transactions = transactions
        
        if final_capital is not None:
            execution.final_capital = final_capital
            # Calculate profit/loss
            execution.profit_loss = final_capital - execution.initial_capital
        
        if gas_used is not None:
            execution.gas_used = gas_used
        
        if gas_cost is not None:
            execution.gas_cost = gas_cost
        
        if error_message is not None:
            execution.error_message = error_message
        
        # If status is terminal, set end time and update stats
        if status in [StrategyStatus.COMPLETED, StrategyStatus.FAILED, StrategyStatus.ABORTED]:
            execution.end_time = int(time.time())
            
            # Calculate performance metrics
            await self._calculate_performance_metrics(execution)
            
            # Remove from active executions
            self.active_executions.pop(execution_id, None)
            
            # Update statistics
            if status == StrategyStatus.COMPLETED:
                self.stats["successful_executions"] += 1
                if execution.profit_loss is not None:
                    self.stats["total_profit"] += execution.profit_loss
            elif status == StrategyStatus.FAILED:
                self.stats["failed_executions"] += 1
            elif status == StrategyStatus.ABORTED:
                self.stats["aborted_executions"] += 1
            
            if execution.gas_cost:
                self.stats["total_gas_cost"] += execution.gas_cost
        
        # Store updated execution in database
        self._store_execution(execution)
        
        logger.info(f"Updated execution {execution_id} status to {status.value}")
        
        # Check for alerts based on new status
        await self._check_execution_alerts(execution)
        
        return True
    
    async def _calculate_performance_metrics(self, execution: StrategyExecution):
        """Calculate performance metrics for a completed strategy execution"""
        metrics = {}
        
        # Calculate execution time
        if execution.start_time and execution.end_time:
            metrics[PerformanceMetric.EXECUTION_TIME.value] = execution.end_time - execution.start_time
        
        # Calculate ROI
        if execution.initial_capital > 0 and execution.final_capital is not None:
            metrics[PerformanceMetric.ROI.value] = (execution.final_capital - execution.initial_capital) / execution.initial_capital
        
        # Calculate gas efficiency (profit per gas used)
        if execution.gas_used > 0 and execution.profit_loss is not None and execution.profit_loss > 0:
            metrics[PerformanceMetric.GAS_EFFICIENCY.value] = execution.profit_loss / execution.gas_used
        
        # Other metrics would be calculated based on transaction data
        # For this example, we'll use placeholder values
        metrics[PerformanceMetric.SLIPPAGE.value] = 0.01  # 1% slippage
        metrics[PerformanceMetric.PRICE_IMPACT.value] = 0.005  # 0.5% price impact
        metrics[PerformanceMetric.OPPORTUNITY_CAPTURE.value] = 0.8  # 80% of theoretical opportunity captured
        
        # Store metrics
        execution.performance_metrics = metrics
    
    async def _check_execution_alerts(self, execution: StrategyExecution):
        """Check for alerts based on execution status and performance"""
        strategy_name = execution.strategy_name
        strategy_config = self.config.get("strategies", {}).get(strategy_name, {})
        
        # Check for failure alerts
        if execution.status == StrategyStatus.FAILED:
            await self._create_alert(
                alert_level=AlertLevel.CRITICAL,
                strategy_name=strategy_name,
                execution_id=execution.execution_id,
                message=f"Strategy execution failed: {execution.error_message}",
                details={
                    "error": execution.error_message,
                    "parameters": execution.parameters,
                    "assets": execution.assets_involved,
                    "transactions": execution.transactions
                }
            )
            return
        
        # Check for completed execution alerts
        if execution.status == StrategyStatus.COMPLETED:
            # Check profit threshold
            min_profit = strategy_config.get("min_profit_threshold", 0.001)
            if execution.profit_loss is not None and execution.profit_loss < min_profit:
                await self._create_alert(
                    alert_level=AlertLevel.WARNING,
                    strategy_name=strategy_name,
                    execution_id=execution.execution_id,
                    message=f"Strategy execution profit below threshold: {execution.profit_loss} ETH < {min_profit} ETH",
                    details={
                        "profit": execution.profit_loss,
                        "threshold": min_profit,
                        "parameters": execution.parameters,
                        "assets": execution.assets_involved
                    }
                )
            
            # Check execution time
            max_time = strategy_config.get("max_execution_time", 60)
            execution_time = execution.end_time - execution.start_time if execution.end_time and execution.start_time else 0
            if execution_time > max_time:
                await self._create_alert(
                    alert_level=AlertLevel.WARNING,
                    strategy_name=strategy_name,
                    execution_id=execution.execution_id,
                    message=f"Strategy execution time above threshold: {execution_time}s > {max_time}s",
                    details={
                        "execution_time": execution_time,
                        "threshold": max_time,
                        "parameters": execution.parameters
                    }
                )
            
            # Check gas cost
            max_gas_cost = strategy_config.get("max_gas_cost", 0.01)
            if execution.gas_cost > max_gas_cost:
                await self._create_alert(
                    alert_level=AlertLevel.WARNING,
                    strategy_name=strategy_name,
                    execution_id=execution.execution_id,
                    message=f"Strategy gas cost above threshold: {execution.gas_cost} ETH > {max_gas_cost} ETH",
                    details={
                        "gas_cost": execution.gas_cost,
                        "threshold": max_gas_cost,
                        "gas_used": execution.gas_used,
                        "parameters": execution.parameters
                    }
                )
            
            # Check performance against baselines
            if strategy_name in self.performance_baselines:
                await self._check_performance_against_baseline(execution)
    
    async def _check_performance_against_baseline(self, execution: StrategyExecution):
        """Check execution performance against established baselines"""
        strategy_name = execution.strategy_name
        baseline = self.performance_baselines.get(strategy_name, {})
        thresholds = self.config.get("alert_thresholds", {})
        
        if not baseline:
            return
        
        # Check profit/loss deviation
        if (PerformanceMetric.PROFIT_LOSS.value in baseline and 
            execution.profit_loss is not None):
            baseline_profit = baseline[PerformanceMetric.PROFIT_LOSS.value]
            if baseline_profit > 0:
                deviation = abs(execution.profit_loss - baseline_profit) / baseline_profit
                max_deviation = thresholds.get("profit_loss_deviation", 0.2)
                
                if deviation > max_deviation:
                    await self._create_alert(
                        alert_level=AlertLevel.WARNING,
                        strategy_name=strategy_name,
                        execution_id=execution.execution_id,
                        message=f"Profit deviation from baseline: {deviation:.2%} > {max_deviation:.2%}",
                        details={
                            "actual_profit": execution.profit_loss,
                            "baseline_profit": baseline_profit,
                            "deviation": deviation,
                            "threshold": max_deviation
                        }
                    )
        
        # Check execution time deviation
        if (PerformanceMetric.EXECUTION_TIME.value in baseline and 
            PerformanceMetric.EXECUTION_TIME.value in execution.performance_metrics):
            baseline_time = baseline[PerformanceMetric.EXECUTION_TIME.value]
            actual_time = execution.performance_metrics[PerformanceMetric.EXECUTION_TIME.value]
            
            if baseline_time > 0:
                deviation = (actual_time - baseline_time) / baseline_time
                max_deviation = thresholds.get("execution_time_max_deviation", 0.5)
                
                if deviation > max_deviation:
                    await self._create_alert(
                        alert_level=AlertLevel.INFO,
                        strategy_name=strategy_name,
                        execution_id=execution.execution_id,
                        message=f"Execution time deviation from baseline: {deviation:.2%} > {max_deviation:.2%}",
                        details={
                            "actual_time": actual_time,
                            "baseline_time": baseline_time,
                            "deviation": deviation,
                            "threshold": max_deviation
                        }
                    )
    
    async def _monitor_active_executions(self):
        """Monitor active strategy executions"""
        for execution_id, execution in list(self.active_executions.items()):
            # Check for stuck executions
            if execution.status in [StrategyStatus.PENDING, StrategyStatus.EXECUTING]:
                current_time = int(time.time())
                execution_time = current_time - execution.start_time
                
                # Get max execution time from strategy config
                strategy_config = self.config.get("strategies", {}).get(execution.strategy_name, {})
                max_time = strategy_config.get("max_execution_time", 60)
                
                # If execution is taking too long, create alert
                if execution_time > max_time * 2:  # Double the max time as a hard limit
                    await self._create_alert(
                        alert_level=AlertLevel.CRITICAL,
                        strategy_name=execution.strategy_name,
                        execution_id=execution_id,
                        message=f"Strategy execution stuck or hanging: {execution_time}s > {max_time*2}s",
                        details={
                            "execution_time": execution_time,
                            "max_time": max_time,
                            "status": execution.status.value,
                            "parameters": execution.parameters
                        }
                    )
                    
                    # Consider aborting the execution
                    await self._consider_aborting_execution(execution)
    
    async def _consider_aborting_execution(self, execution: StrategyExecution):
        """Consider aborting a stuck or problematic execution"""
        # Check if we have an abort handler for this strategy
        if execution.strategy_name in self.abort_handlers:
            abort_handler = self.abort_handlers[execution.strategy_name]
            
            # Call the abort handler
            should_abort = await abort_handler(execution)
            
            if should_abort:
                # Update execution status to aborted
                await self.update_execution_status(
                    execution_id=execution.execution_id,
                    status=StrategyStatus.ABORTED,
                    error_message="Execution aborted due to timeout or performance issues"
                )
                
                logger.warning(f"Aborted execution {execution.execution_id} due to timeout or performance issues")
    
    async def _default_abort_handler(self, execution: StrategyExecution) -> bool:
        """Default handler for deciding whether to abort an execution"""
        # By default, abort if execution is taking more than 3x the max time
        strategy_config = self.config.get("strategies", {}).get(execution.strategy_name, {})
        max_time = strategy_config.get("max_execution_time", 60)
        
        current_time = int(time.time())
        execution_time = current_time - execution.start_time
        
        return execution_time > max_time * 3
    
    async def _create_alert(self, alert_level: AlertLevel, strategy_name: str,
                          message: str, details: Dict[str, Any],
                          execution_id: Optional[str] = None):
        """Create a strategy alert"""
        # Generate unique alert ID
        alert_id = f"{strategy_name}_{alert_level.value}_{int(time.time())}_{hashlib.md5(message.encode()).hexdigest()[:8]}"
        
        # Create recommended actions based on alert level and type
        recommended_actions = self._generate_recommended_actions(alert_level, strategy_name, message)
        
        # Create alert object
        alert = StrategyAlert(
            alert_id=alert_id,
            alert_level=alert_level,
            strategy_name=strategy_name,
            execution_id=execution_id,
            timestamp=int(time.time()),
            message=message,
            details=details,
            recommended_actions=recommended_actions,
            resolved=False
        )
        
        # Store alert in memory and database
        self.alerts.append(alert)
        self.active_alerts[alert_id] = alert
        self._store_alert(alert)
        
        self.stats["alerts_generated"] += 1
        
        # Trigger alert handlers
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")
    
    def _generate_recommended_actions(self, alert_level: AlertLevel, strategy_name: str, message: str) -> List[str]:
        """Generate recommended actions based on alert level and message"""
        actions = []
        
        # Common actions for all alerts
        actions.append("Review strategy execution details and parameters")
        
        # Level-specific actions
        if alert_level == AlertLevel.EMERGENCY:
            actions.append("Pause all strategy executions immediately")
            actions.append("Notify emergency response team")
            actions.append("Prepare for potential financial loss mitigation")
        
        elif alert_level == AlertLevel.CRITICAL:
            actions.append("Pause affected strategy executions")
            actions.append("Investigate root cause immediately")
            actions.append("Prepare incident report")
        
        elif alert_level == AlertLevel.WARNING:
            actions.append("Monitor subsequent executions closely")
            actions.append("Review strategy parameters for optimization")
        
        # Message-specific actions
        if "profit below threshold" in message:
            actions.append("Review market conditions for strategy viability")
            actions.append("Consider adjusting profit thresholds or strategy parameters")
        
        elif "execution time above threshold" in message:
            actions.append("Check for network congestion or high gas prices")
            actions.append("Optimize transaction batching or execution flow")
        
        elif "gas cost above threshold" in message:
            actions.append("Review gas optimization opportunities")
            actions.append("Consider adjusting gas price strategies")
        
        elif "stuck or hanging" in message:
            actions.append("Check for pending transactions in mempool")
            actions.append("Consider manual intervention to unstick transactions")
        
        return actions
    
    def _store_execution(self, execution: StrategyExecution):
        """Store strategy execution in the database"""
        if not self.db_conn:
            return
        
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
            INSERT OR REPLACE INTO strategy_executions (
                execution_id, strategy_name, start_time, end_time, status,
                parameters, transactions, assets_involved, initial_capital,
                final_capital, profit_loss, gas_used, gas_cost, error_message,
                performance_metrics
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                execution.execution_id, execution.strategy_name, execution.start_time,
                execution.end_time, execution.status.value, json.dumps(execution.parameters),
                json.dumps(execution.transactions), json.dumps(execution.assets_involved),
                execution.initial_capital, execution.final_capital, execution.profit_loss,
                execution.gas_used, execution.gas_cost, execution.error_message,
                json.dumps(execution.performance_metrics)
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"Error storing execution data: {e}")
    
    def _store_alert(self, alert: StrategyAlert):
        """Store alert in the database"""
        if not self.db_conn:
            return
        
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
            INSERT INTO strategy_alerts (
                alert_id, alert_level, strategy_name, execution_id, timestamp,
                message, details, recommended_actions, resolved,
                resolution_time, resolution_details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert.alert_id, alert.alert_level.value, alert.strategy_name,
                alert.execution_id, alert.timestamp, alert.message,
                json.dumps(alert.details), json.dumps(alert.recommended_actions),
                int(alert.resolved), alert.resolution_time, alert.resolution_details
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
    
    async def _check_alert_resolution(self, alert: StrategyAlert):
        """Check if an alert should be automatically resolved"""
        # Auto-resolve INFO alerts after 1 hour
        if alert.alert_level == AlertLevel.INFO and (int(time.time()) - alert.timestamp) > 3600:
            alert.resolved = True
            alert.resolution_time = int(time.time())
            alert.resolution_details = "Auto-resolved: INFO alert expired after 1 hour"
            
            # Update in database
            self._update_alert_resolution(alert)
            
            logger.info(f"Auto-resolved alert {alert.alert_id}: {alert.resolution_details}")
        
        # Auto-resolve WARNING alerts after 4 hours
        elif alert.alert_level == AlertLevel.WARNING and (int(time.time()) - alert.timestamp) > 14400:
            alert.resolved = True
            alert.resolution_time = int(time.time())
            alert.resolution_details = "Auto-resolved: WARNING alert expired after 4 hours"
            
            # Update in database
            self._update_alert_resolution(alert)
            
            logger.info(f"Auto-resolved alert {alert.alert_id}: {alert.resolution_details}")
        
        # Don't auto-resolve CRITICAL or EMERGENCY alerts
    
    def _update_alert_resolution(self, alert: StrategyAlert):
        """Update alert resolution status in database"""
        if not self.db_conn:
            return
        
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
            UPDATE strategy_alerts SET
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
    
    def _update_performance_baselines(self):
        """Update performance baselines based on historical executions"""
        # For each strategy, calculate new baselines from successful executions
        for strategy_name, executions in self.strategy_history.items():
            # Filter for completed executions
            completed_executions = [e for e in executions if e.status == StrategyStatus.COMPLETED]
            
            if len(completed_executions) < 5:
                logger.debug(f"Not enough completed executions for {strategy_name} to update baselines")
                continue
            
            # Calculate new baselines
            new_baseline = {}
            
            # Profit/Loss
            if all(e.profit_loss is not None for e in completed_executions):
                new_baseline[PerformanceMetric.PROFIT_LOSS.value] = statistics.mean(
                    [e.profit_loss for e in completed_executions]
                )
            
            # ROI
            roi_values = []
            for e in completed_executions:
                if e.initial_capital > 0 and e.final_capital is not None:
                    roi = (e.final_capital - e.initial_capital) / e.initial_capital
                    roi_values.append(roi)
            
            if roi_values:
                new_baseline[PerformanceMetric.ROI.value] = statistics.mean(roi_values)
            
            # Execution Time
            execution_times = []
            for e in completed_executions:
                if e.start_time and e.end_time:
                    execution_times.append(e.end_time - e.start_time)
            
            if execution_times:
                new_baseline[PerformanceMetric.EXECUTION_TIME.value] = statistics.mean(execution_times)
            
            # Gas Efficiency
            gas_efficiencies = []
            for e in completed_executions:
                if e.gas_used > 0 and e.profit_loss is not None and e.profit_loss > 0:
                    gas_efficiencies.append(e.profit_loss / e.gas_used)
            
            if gas_efficiencies:
                new_baseline[PerformanceMetric.GAS_EFFICIENCY.value] = statistics.mean(gas_efficiencies)
            
            # Success Rate
            all_executions = len(self.strategy_history[strategy_name])
            success_rate = len(completed_executions) / all_executions if all_executions > 0 else 0
            new_baseline[PerformanceMetric.SUCCESS_RATE.value] = success_rate
            
            # Other metrics from performance_metrics field
            for metric in [PerformanceMetric.SLIPPAGE.value, PerformanceMetric.PRICE_IMPACT.value, 
                          PerformanceMetric.OPPORTUNITY_CAPTURE.value]:
                values = []
                for e in completed_executions:
                    if metric in e.performance_metrics:
                        values.append(e.performance_metrics[metric])
                
                if values:
                    new_baseline[metric] = statistics.mean(values)
            
            # Update baselines
            self.performance_baselines[strategy_name] = new_baseline
            
            # Store in database
            self._store_performance_baseline(strategy_name, new_baseline)
            
            logger.info(f"Updated performance baselines for {strategy_name}")
    
    def _store_performance_baseline(self, strategy_name: str, baseline: Dict[str, float]):
        """Store performance baseline in the database"""
        if not self.db_conn:
            return
        
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
            INSERT OR REPLACE INTO performance_baselines (
                strategy_name, profit_loss, roi, execution_time, gas_efficiency,
                success_rate, slippage, price_impact, opportunity_capture, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                strategy_name,
                baseline.get(PerformanceMetric.PROFIT_LOSS.value, 0),
                baseline.get(PerformanceMetric.ROI.value, 0),
                baseline.get(PerformanceMetric.EXECUTION_TIME.value, 0),
                baseline.get(PerformanceMetric.GAS_EFFICIENCY.value, 0),
                baseline.get(PerformanceMetric.SUCCESS_RATE.value, 0),
                baseline.get(PerformanceMetric.SLIPPAGE.value, 0),
                baseline.get(PerformanceMetric.PRICE_IMPACT.value, 0),
                baseline.get(PerformanceMetric.OPPORTUNITY_CAPTURE.value, 0),
                int(time.time())
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"Error storing performance baseline: {e}")
    
    async def _log_alert(self, alert: StrategyAlert):
        """Log alert to file and console"""
        log_message = (
            f"STRATEGY ALERT: {alert.alert_level.value}\n"
            f"Strategy: {alert.strategy_name}\n"
            f"Execution: {alert.execution_id if alert.execution_id else 'N/A'}\n"
            f"Message: {alert.message}\n"
            f"Time: {datetime.fromtimestamp(alert.timestamp).strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Details: {json.dumps(alert.details, indent=2)}\n"
            f"Recommended Actions: {', '.join(alert.recommended_actions)}"
        )
        
        if alert.alert_level in [AlertLevel.CRITICAL, AlertLevel.EMERGENCY]:
            logger.critical(log_message)
        elif alert.alert_level == AlertLevel.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    async def _email_alert(self, alert: StrategyAlert):
        """Send alert via email"""
        # This would be implemented with an email library in a real system
        logger.info(f"Would send email alert for {alert.alert_id}")
    
    async def _slack_alert(self, alert: StrategyAlert):
        """Send alert via Slack"""
        # This would be implemented with a Slack API client in a real system
        logger.info(f"Would send Slack alert for {alert.alert_id}")
    
    async def _webhook_alert(self, alert: StrategyAlert):
        """Send alert via webhook"""
        # This would be implemented with aiohttp in a real system
        logger.info(f"Would send webhook alert for {alert.alert_id}")
    
    def get_active_alerts(self) -> List[StrategyAlert]:
        """Get list of active alerts"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[StrategyAlert]:
        """Get historical alerts"""
        return self.alerts[-limit:]
    
    def get_strategy_performance(self, strategy_name: str) -> Dict[str, Any]:
        """Get performance metrics for a specific strategy"""
        if strategy_name not in self.strategy_history:
            return {"strategy_name": strategy_name, "status": "No data available"}
        
        executions = self.strategy_history[strategy_name]
        completed_executions = [e for e in executions if e.status == StrategyStatus.COMPLETED]
        failed_executions = [e for e in executions if e.status == StrategyStatus.FAILED]
        aborted_executions = [e for e in executions if e.status == StrategyStatus.ABORTED]
        
        # Calculate performance metrics
        total_executions = len(executions)
        success_rate = len(completed_executions) / total_executions if total_executions > 0 else 0
        
        # Calculate profit metrics
        total_profit = sum(e.profit_loss for e in completed_executions if e.profit_loss is not None)
        avg_profit = total_profit / len(completed_executions) if completed_executions else 0
        
        # Calculate time metrics
        execution_times = [e.end_time - e.start_time for e in completed_executions 
                          if e.end_time and e.start_time]
        avg_execution_time = statistics.mean(execution_times) if execution_times else 0
        
        # Calculate gas metrics
        total_gas_used = sum(e.gas_used for e in completed_executions)
        total_gas_cost = sum(e.gas_cost for e in completed_executions if e.gas_cost is not None)
        avg_gas_cost = total_gas_cost / len(completed_executions) if completed_executions else 0
        
        # Get baseline for comparison
        baseline = self.performance_baselines.get(strategy_name, {})
        
        return {
            "strategy_name": strategy_name,
            "total_executions": total_executions,
            "completed_executions": len(completed_executions),
            "failed_executions": len(failed_executions),
            "aborted_executions": len(aborted_executions),
            "success_rate": success_rate,
            "total_profit": total_profit,
            "average_profit": avg_profit,
            "average_execution_time": avg_execution_time,
            "total_gas_used": total_gas_used,
            "total_gas_cost": total_gas_cost,
            "average_gas_cost": avg_gas_cost,
            "baseline": baseline,
            "recent_executions": [
                {
                    "execution_id": e.execution_id,
                    "status": e.status.value,
                    "start_time": datetime.fromtimestamp(e.start_time).strftime("%Y-%m-%d %H:%M:%S"),
                    "profit_loss": e.profit_loss,
                    "gas_cost": e.gas_cost
                } for e in executions[-5:]  # Last 5 executions
            ]
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        strategies_status = {}
        for strategy_name in set(e.strategy_name for e in self.strategy_executions.values()):
            strategies_status[strategy_name] = self.get_strategy_performance(strategy_name)
        
        # Count alerts by level
        alert_counts = {level.value: 0 for level in AlertLevel}
        for alert in self.active_alerts.values():
            if not alert.resolved:
                alert_counts[alert.alert_level.value] += 1
        
        return {
            "timestamp": int(time.time()),
            "monitoring_active": self.is_monitoring,
            "strategies_monitored": self.stats["strategies_monitored"],
            "executions_tracked": self.stats["executions_tracked"],
            "successful_executions": self.stats["successful_executions"],
            "failed_executions": self.stats["failed_executions"],
            "aborted_executions": self.stats["aborted_executions"],
            "total_profit": self.stats["total_profit"],
            "total_gas_cost": self.stats["total_gas_cost"],
            "active_executions": len(self.active_executions),
            "active_alerts": sum(alert_counts.values()),
            "alerts_by_level": alert_counts,
            "strategies_status": strategies_status
        }

async def main():
    """Main function for running the Strategy Sentinel as a standalone process"""
    # Create and start the Strategy Sentinel
    sentinel = StrategySentinel()
    
    try:
        # Start monitoring
        await sentinel.start_monitoring()
        
        # Simulate a strategy execution for testing
        execution_id = await sentinel.register_strategy_execution(
            strategy_name="arbitrage_v1",
            parameters={"token_pair": "ETH/USDC", "min_profit": 0.01},
            initial_capital=1.0,
            assets_involved=["ETH", "USDC"]
        )
        
        # Update to executing
        await sentinel.update_execution_status(
            execution_id=execution_id,
            status=StrategyStatus.EXECUTING
        )
        
        # Wait a bit
        await asyncio.sleep(2)
        
        # Complete the execution
        await sentinel.update_execution_status(
            execution_id=execution_id,
            status=StrategyStatus.COMPLETED,
            transactions=["0x" + hashlib.sha256(f"tx_{time.time()}".encode()).hexdigest()],
            final_capital=1.05,
            gas_used=150000,
            gas_cost=0.005
        )
        
        # Keep running until interrupted
        while True:
            await asyncio.sleep(60)
            
            # Print system status every minute
            status = sentinel.get_system_status()
            
            print(f"\nStrategy Sentinel Status at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:")
            print(f"Monitoring Active: {status['monitoring_active']}")
            print(f"Strategies Monitored: {status['strategies_monitored']}")
            print(f"Executions Tracked: {status['executions_tracked']}")
            print(f"Active Executions: {status['active_executions']}")
            print(f"Successful/Failed/Aborted: {status['successful_executions']}/{status['failed_executions']}/{status['aborted_executions']}")
            print(f"Total Profit: {status['total_profit']} ETH")
            print(f"Active Alerts: {status['active_alerts']}")
            
            print("Alerts by Level:", end=" ")
            for level, count in status['alerts_by_level'].items():
                if count > 0:
                    print(f"{level}: {count}", end=" ")
            print("\n")
    
    except KeyboardInterrupt:
        print("Shutting down Strategy Sentinel...")
        await sentinel.stop_monitoring()
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        await sentinel.stop_monitoring()

if __name__ == "__main__":
    asyncio.run(main())