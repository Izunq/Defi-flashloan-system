#!/usr/bin/env python3
"""
Emergency Action Executor
Execute emergency actions based on sentinel alerts
"""

import os
import sys
import json
import time
import yaml
import logging
import asyncio
import sqlite3
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum

from sentinel_contract_manager import SentinelContractManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("emergency_action_executor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("EmergencyActionExecutor")

class ActionType(Enum):
    """Types of emergency actions"""
    CONTRACT_PAUSE = "contract_pause"
    CONTRACT_UNPAUSE = "contract_unpause"
    CAPITAL_REDUCTION = "capital_reduction"
    PARAMETER_ADJUSTMENT = "parameter_adjustment"
    STRATEGY_DISABLE = "strategy_disable"
    NOTIFICATION = "notification"
    CUSTOM_FUNCTION = "custom_function"

class ActionStatus(Enum):
    """Status of emergency actions"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    MANUAL_OVERRIDE = "manual_override"

@dataclass
class EmergencyAction:
    """Emergency action to be executed"""
    action_id: str
    action_type: ActionType
    alert_id: str
    alert_source: str
    alert_priority: str
    target: str  # Contract name or other target
    parameters: Dict[str, Any]
    status: ActionStatus = ActionStatus.PENDING
    created_at: int = 0
    updated_at: int = 0
    executed_at: Optional[int] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    manual_override: bool = False
    override_reason: Optional[str] = None
    override_by: Optional[str] = None

class EmergencyActionExecutor:
    """
    Execute emergency actions based on sentinel alerts
    """
    
    def __init__(self, config_path: str = "sentinel_config.yaml"):
        """Initialize the emergency action executor"""
        self.config = self._load_config(config_path)
        self.action_config = self.config.get("integration", {}).get("contract_interaction", {})
        
        # Check if contract interaction is enabled
        if not self.action_config.get("enabled", False):
            logger.warning("Contract interaction is disabled in config")
            return
        
        # Initialize contract manager
        self.contract_manager = SentinelContractManager(config_path)
        
        # Initialize database
        self.db_path = self.action_config.get("action_db_path", "emergency_actions.db")
        self.db = self._initialize_database()
        
        # Action queue
        self.action_queue = asyncio.Queue()
        self.processing_task = None
        
        # Auto-pause threshold
        self.auto_pause_threshold = self.action_config.get("auto_pause_threshold", "CRITICAL")
        
        # Progressive response config
        self.progressive_response = self.action_config.get("progressive_response", {})
        
        # Manual override settings
        self.manual_override_enabled = self.action_config.get("manual_override_enabled", True)
        self.override_approvers = self.action_config.get("override_approvers", [])
        
        # Rollback settings
        self.rollback_enabled = self.action_config.get("rollback_enabled", True)
        self.rollback_timeout = self.action_config.get("rollback_timeout", 3600)  # 1 hour default
        
        logger.info("Emergency Action Executor initialized")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Config file {config_path} not found")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            sys.exit(1)
    
    def _initialize_database(self) -> sqlite3.Connection:
        """Initialize SQLite database for action history"""
        try:
            db = sqlite3.connect(self.db_path)
            cursor = db.cursor()
            
            # Create actions table if it doesn't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS emergency_actions (
                action_id TEXT PRIMARY KEY,
                action_type TEXT NOT NULL,
                alert_id TEXT NOT NULL,
                alert_source TEXT NOT NULL,
                alert_priority TEXT NOT NULL,
                target TEXT NOT NULL,
                parameters TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL,
                executed_at INTEGER,
                result TEXT,
                error TEXT,
                manual_override INTEGER NOT NULL,
                override_reason TEXT,
                override_by TEXT
            )
            ''')
            
            # Create index on alert_id
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_alert_id ON emergency_actions(alert_id)
            ''')
            
            db.commit()
            logger.info(f"Initialized database at {self.db_path}")
            return db
        
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            sys.exit(1)
    
    async def start(self):
        """Start the emergency action executor"""
        if not self.action_config.get("enabled", False):
            logger.warning("Contract interaction is disabled in config")
            return
        
        logger.info("Starting Emergency Action Executor")
        self.processing_task = asyncio.create_task(self._process_action_queue())
    
    async def stop(self):
        """Stop the emergency action executor"""
        logger.info("Stopping Emergency Action Executor")
        
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
            self.processing_task = None
        
        # Close database connection
        if self.db:
            self.db.close()
    
    async def _process_action_queue(self):
        """Process actions from the queue"""
        while True:
            try:
                # Get action from queue
                action = await self.action_queue.get()
                
                # Update status to in progress
                action.status = ActionStatus.IN_PROGRESS
                action.updated_at = int(time.time())
                self._update_action_in_db(action)
                
                # Execute action
                result = await self._execute_action(action)
                
                # Update action with result
                action.result = result
                action.executed_at = int(time.time())
                action.updated_at = int(time.time())
                
                if result.get("success", False):
                    action.status = ActionStatus.COMPLETED
                else:
                    action.status = ActionStatus.FAILED
                    action.error = result.get("error", "Unknown error")
                
                # Update in database
                self._update_action_in_db(action)
                
                # Mark task as done
                self.action_queue.task_done()
                
            except asyncio.CancelledError:
                logger.info("Action processing task cancelled")
                break
            
            except Exception as e:
                logger.error(f"Error processing action: {e}")
                await asyncio.sleep(1)
    
    async def _execute_action(self, action: EmergencyAction) -> Dict[str, Any]:
        """
        Execute an emergency action
        
        Args:
            action: Emergency action to execute
            
        Returns:
            Dict with execution result
        """
        logger.info(f"Executing action {action.action_id} of type {action.action_type.value}")
        
        if action.action_type == ActionType.CONTRACT_PAUSE:
            return await self._execute_contract_pause(action)
        
        elif action.action_type == ActionType.CONTRACT_UNPAUSE:
            return await self._execute_contract_unpause(action)
        
        elif action.action_type == ActionType.CAPITAL_REDUCTION:
            return await self._execute_capital_reduction(action)
        
        elif action.action_type == ActionType.PARAMETER_ADJUSTMENT:
            return await self._execute_parameter_adjustment(action)
        
        elif action.action_type == ActionType.STRATEGY_DISABLE:
            return await self._execute_strategy_disable(action)
        
        elif action.action_type == ActionType.NOTIFICATION:
            return await self._execute_notification(action)
        
        elif action.action_type == ActionType.CUSTOM_FUNCTION:
            return await self._execute_custom_function(action)
        
        else:
            return {
                "success": False,
                "error": f"Unknown action type: {action.action_type.value}"
            }
    
    async def _execute_contract_pause(self, action: EmergencyAction) -> Dict[str, Any]:
        """Execute contract pause action"""
        contract_name = action.target
        reason = action.parameters.get("reason", f"Emergency pause triggered by {action.alert_source} alert")
        
        return await self.contract_manager.emergency_pause(contract_name, reason)
    
    async def _execute_contract_unpause(self, action: EmergencyAction) -> Dict[str, Any]:
        """Execute contract unpause action"""
        contract_name = action.target
        reason = action.parameters.get("reason", f"Emergency unpause triggered by manual override")
        
        return await self.contract_manager.emergency_unpause(contract_name, reason)
    
    async def _execute_capital_reduction(self, action: EmergencyAction) -> Dict[str, Any]:
        """Execute capital reduction action"""
        contract_name = action.target
        percentage = action.parameters.get("percentage", 50)  # Default to 50% reduction
        function_name = action.parameters.get("function_name", "reduceCapital")
        
        return await self.contract_manager.execute_contract_function(
            contract_name,
            function_name,
            [percentage]
        )
    
    async def _execute_parameter_adjustment(self, action: EmergencyAction) -> Dict[str, Any]:
        """Execute parameter adjustment action"""
        contract_name = action.target
        function_name = action.parameters.get("function_name")
        params = action.parameters.get("params", [])
        
        if not function_name:
            return {
                "success": False,
                "error": "No function name specified for parameter adjustment"
            }
        
        return await self.contract_manager.execute_contract_function(
            contract_name,
            function_name,
            params
        )
    
    async def _execute_strategy_disable(self, action: EmergencyAction) -> Dict[str, Any]:
        """Execute strategy disable action"""
        contract_name = action.target
        strategy_id = action.parameters.get("strategy_id")
        function_name = action.parameters.get("function_name", "disableStrategy")
        
        if not strategy_id:
            return {
                "success": False,
                "error": "No strategy ID specified for strategy disable"
            }
        
        return await self.contract_manager.execute_contract_function(
            contract_name,
            function_name,
            [strategy_id]
        )
    
    async def _execute_notification(self, action: EmergencyAction) -> Dict[str, Any]:
        """Execute notification action"""
        # This would typically integrate with notification systems
        # For now, just log the notification
        notification_type = action.parameters.get("type", "emergency")
        message = action.parameters.get("message", f"Emergency action triggered by {action.alert_source} alert")
        recipients = action.parameters.get("recipients", [])
        
        logger.warning(f"NOTIFICATION ({notification_type}): {message}")
        logger.warning(f"Recipients: {recipients}")
        
        return {
            "success": True,
            "message": "Notification logged",
            "notification_type": notification_type,
            "recipients": recipients
        }
    
    async def _execute_custom_function(self, action: EmergencyAction) -> Dict[str, Any]:
        """Execute custom function action"""
        contract_name = action.target
        function_name = action.parameters.get("function_name")
        args = action.parameters.get("args", [])
        value = action.parameters.get("value", 0)
        
        if not function_name:
            return {
                "success": False,
                "error": "No function name specified for custom function"
            }
        
        return await self.contract_manager.execute_contract_function(
            contract_name,
            function_name,
            args,
            value
        )
    
    def process_alert(self, alert: Dict[str, Any]) -> List[str]:
        """
        Process an alert and determine appropriate actions
        
        Args:
            alert: Alert data
            
        Returns:
            List of action IDs created
        """
        alert_id = alert.get("alert_id")
        alert_source = alert.get("source", "unknown")
        alert_priority = alert.get("priority", "low")
        
        if not alert_id:
            logger.error("Alert missing alert_id")
            return []
        
        logger.info(f"Processing alert {alert_id} from {alert_source} with priority {alert_priority}")
        
        # Determine actions based on alert
        actions = self._determine_actions(alert)
        
        # Create and queue actions
        action_ids = []
        for action in actions:
            # Create action in database
            self._create_action_in_db(action)
            
            # Add to queue for processing
            self.action_queue.put_nowait(action)
            
            action_ids.append(action.action_id)
            logger.info(f"Created action {action.action_id} of type {action.action_type.value} for alert {alert_id}")
        
        return action_ids
    
    def _determine_actions(self, alert: Dict[str, Any]) -> List[EmergencyAction]:
        """
        Determine appropriate actions for an alert
        
        Args:
            alert: Alert data
            
        Returns:
            List of actions to take
        """
        alert_id = alert.get("alert_id")
        alert_source = alert.get("source", "unknown")
        alert_priority = alert.get("priority", "low")
        alert_details = alert.get("details", {})
        
        actions = []
        timestamp = int(time.time())
        
        # Check for auto-pause threshold
        should_pause = self.contract_manager.should_auto_pause(alert_priority.upper())
        
        # Oracle alerts
        if alert_source == "oracle":
            if should_pause:
                # Pause all contracts that depend on this oracle
                asset = alert_details.get("asset")
                if asset:
                    for contract_name in self._get_contracts_using_asset(asset):
                        action_id = f"pause_{contract_name}_{alert_id}_{timestamp}"
                        actions.append(EmergencyAction(
                            action_id=action_id,
                            action_type=ActionType.CONTRACT_PAUSE,
                            alert_id=alert_id,
                            alert_source=alert_source,
                            alert_priority=alert_priority,
                            target=contract_name,
                            parameters={
                                "reason": f"Auto-pause due to oracle anomaly for {asset}"
                            },
                            created_at=timestamp,
                            updated_at=timestamp
                        ))
            
            # Always send notification for oracle alerts
            action_id = f"notify_{alert_id}_{timestamp}"
            actions.append(EmergencyAction(
                action_id=action_id,
                action_type=ActionType.NOTIFICATION,
                alert_id=alert_id,
                alert_source=alert_source,
                alert_priority=alert_priority,
                target="notification_system",
                parameters={
                    "type": "oracle_alert",
                    "message": f"Oracle alert: {alert.get('message', 'No message')}",
                    "recipients": self._get_recipients_for_priority(alert_priority)
                },
                created_at=timestamp,
                updated_at=timestamp
            ))
        
        # MEV alerts
        elif alert_source == "mev":
            if should_pause:
                # Pause arbitrage executor
                action_id = f"pause_arbitrage_{alert_id}_{timestamp}"
                actions.append(EmergencyAction(
                    action_id=action_id,
                    action_type=ActionType.CONTRACT_PAUSE,
                    alert_id=alert_id,
                    alert_source=alert_source,
                    alert_priority=alert_priority,
                    target="arbitrage_executor",
                    parameters={
                        "reason": f"Auto-pause due to MEV attack detection"
                    },
                    created_at=timestamp,
                    updated_at=timestamp
                ))
            
            # For high priority MEV alerts, adjust gas price parameters
            if alert_priority in ["high", "critical", "emergency"]:
                action_id = f"adjust_gas_{alert_id}_{timestamp}"
                actions.append(EmergencyAction(
                    action_id=action_id,
                    action_type=ActionType.PARAMETER_ADJUSTMENT,
                    alert_id=alert_id,
                    alert_source=alert_source,
                    alert_priority=alert_priority,
                    target="arbitrage_executor",
                    parameters={
                        "function_name": "setGasPriceMultiplier",
                        "params": [200]  # 2x gas price
                    },
                    created_at=timestamp,
                    updated_at=timestamp
                ))
        
        # Strategy alerts
        elif alert_source == "strategy":
            strategy_id = alert_details.get("strategy_id")
            
            if should_pause and strategy_id:
                # Disable specific strategy
                action_id = f"disable_strategy_{alert_id}_{timestamp}"
                actions.append(EmergencyAction(
                    action_id=action_id,
                    action_type=ActionType.STRATEGY_DISABLE,
                    alert_id=alert_id,
                    alert_source=alert_source,
                    alert_priority=alert_priority,
                    target="ai_strategy",
                    parameters={
                        "strategy_id": strategy_id,
                        "function_name": "disableStrategy"
                    },
                    created_at=timestamp,
                    updated_at=timestamp
                ))
            
            # For critical strategy alerts, reduce capital allocation
            if alert_priority in ["critical", "emergency"] and strategy_id:
                action_id = f"reduce_capital_{alert_id}_{timestamp}"
                actions.append(EmergencyAction(
                    action_id=action_id,
                    action_type=ActionType.CAPITAL_REDUCTION,
                    alert_id=alert_id,
                    alert_source=alert_source,
                    alert_priority=alert_priority,
                    target="ai_strategy",
                    parameters={
                        "function_name": "reduceStrategyAllocation",
                        "params": [strategy_id, 50]  # Reduce by 50%
                    },
                    created_at=timestamp,
                    updated_at=timestamp
                ))
        
        return actions
    
    def _get_contracts_using_asset(self, asset: str) -> List[str]:
        """Get contracts that use a specific asset"""
        # This would typically be configured or determined dynamically
        # For now, return a hardcoded list based on common assets
        if asset in ["ETH", "WETH"]:
            return ["arbitrage_executor", "ai_strategy", "vault"]
        elif asset in ["BTC", "WBTC"]:
            return ["arbitrage_executor", "ai_strategy"]
        elif asset in ["USDC", "USDT", "DAI"]:
            return ["arbitrage_executor", "ai_strategy", "vault"]
        else:
            return ["ai_strategy"]  # Default to just AI strategy for other assets
    
    def _get_recipients_for_priority(self, priority: str) -> List[str]:
        """Get notification recipients based on alert priority"""
        # This would typically be configured
        # For now, return hardcoded recipients
        if priority in ["critical", "emergency"]:
            return ["security_team", "dev_team", "management"]
        elif priority == "high":
            return ["security_team", "dev_team"]
        elif priority == "medium":
            return ["security_team"]
        else:
            return ["monitoring_system"]
    
    def _create_action_in_db(self, action: EmergencyAction):
        """Create action in database"""
        try:
            cursor = self.db.cursor()
            
            cursor.execute('''
            INSERT INTO emergency_actions (
                action_id, action_type, alert_id, alert_source, alert_priority,
                target, parameters, status, created_at, updated_at,
                executed_at, result, error, manual_override, override_reason, override_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                action.action_id,
                action.action_type.value,
                action.alert_id,
                action.alert_source,
                action.alert_priority,
                action.target,
                json.dumps(action.parameters),
                action.status.value,
                action.created_at,
                action.updated_at,
                action.executed_at,
                json.dumps(action.result) if action.result else None,
                action.error,
                1 if action.manual_override else 0,
                action.override_reason,
                action.override_by
            ))
            
            self.db.commit()
        
        except Exception as e:
            logger.error(f"Error creating action in database: {e}")
            self.db.rollback()
    
    def _update_action_in_db(self, action: EmergencyAction):
        """Update action in database"""
        try:
            cursor = self.db.cursor()
            
            cursor.execute('''
            UPDATE emergency_actions SET
                status = ?,
                updated_at = ?,
                executed_at = ?,
                result = ?,
                error = ?,
                manual_override = ?,
                override_reason = ?,
                override_by = ?
            WHERE action_id = ?
            ''', (
                action.status.value,
                action.updated_at,
                action.executed_at,
                json.dumps(action.result) if action.result else None,
                action.error,
                1 if action.manual_override else 0,
                action.override_reason,
                action.override_by,
                action.action_id
            ))
            
            self.db.commit()
        
        except Exception as e:
            logger.error(f"Error updating action in database: {e}")
            self.db.rollback()
    
    def get_action(self, action_id: str) -> Optional[EmergencyAction]:
        """Get action by ID"""
        try:
            cursor = self.db.cursor()
            
            cursor.execute('''
            SELECT * FROM emergency_actions WHERE action_id = ?
            ''', (action_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # Convert row to EmergencyAction
            return self._row_to_action(row)
        
        except Exception as e:
            logger.error(f"Error getting action from database: {e}")
            return None
    
    def get_actions_for_alert(self, alert_id: str) -> List[EmergencyAction]:
        """Get actions for an alert"""
        try:
            cursor = self.db.cursor()
            
            cursor.execute('''
            SELECT * FROM emergency_actions WHERE alert_id = ?
            ''', (alert_id,))
            
            rows = cursor.fetchall()
            
            # Convert rows to EmergencyActions
            return [self._row_to_action(row) for row in rows]
        
        except Exception as e:
            logger.error(f"Error getting actions for alert from database: {e}")
            return []
    
    def get_recent_actions(self, limit: int = 100) -> List[EmergencyAction]:
        """Get recent actions"""
        try:
            cursor = self.db.cursor()
            
            cursor.execute('''
            SELECT * FROM emergency_actions ORDER BY created_at DESC LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            
            # Convert rows to EmergencyActions
            return [self._row_to_action(row) for row in rows]
        
        except Exception as e:
            logger.error(f"Error getting recent actions from database: {e}")
            return []
    
    def _row_to_action(self, row) -> EmergencyAction:
        """Convert database row to EmergencyAction"""
        # Get column names
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM emergency_actions LIMIT 1")
        columns = [description[0] for description in cursor.description]
        
        # Create dict from row
        row_dict = {columns[i]: row[i] for i in range(len(columns))}
        
        # Convert to EmergencyAction
        return EmergencyAction(
            action_id=row_dict["action_id"],
            action_type=ActionType(row_dict["action_type"]),
            alert_id=row_dict["alert_id"],
            alert_source=row_dict["alert_source"],
            alert_priority=row_dict["alert_priority"],
            target=row_dict["target"],
            parameters=json.loads(row_dict["parameters"]),
            status=ActionStatus(row_dict["status"]),
            created_at=row_dict["created_at"],
            updated_at=row_dict["updated_at"],
            executed_at=row_dict["executed_at"],
            result=json.loads(row_dict["result"]) if row_dict["result"] else None,
            error=row_dict["error"],
            manual_override=bool(row_dict["manual_override"]),
            override_reason=row_dict["override_reason"],
            override_by=row_dict["override_by"]
        )
    
    def manual_override(
        self, 
        action_id: str, 
        override: bool, 
        reason: str, 
        override_by: str
    ) -> bool:
        """
        Apply manual override to an action
        
        Args:
            action_id: Action ID
            override: True to override (cancel), False to allow
            reason: Reason for override
            override_by: User who performed the override
            
        Returns:
            True if successful
        """
        if not self.manual_override_enabled:
            logger.warning("Manual override is disabled")
            return False
        
        # Check if override_by is authorized
        if self.override_approvers and override_by not in self.override_approvers:
            logger.warning(f"User {override_by} is not authorized for manual override")
            return False
        
        # Get action
        action = self.get_action(action_id)
        if not action:
            logger.error(f"Action {action_id} not found")
            return False
        
        # Check if action can be overridden
        if action.status not in [ActionStatus.PENDING, ActionStatus.IN_PROGRESS]:
            logger.warning(f"Cannot override action {action_id} with status {action.status.value}")
            return False
        
        # Apply override
        action.manual_override = True
        action.override_reason = reason
        action.override_by = override_by
        action.updated_at = int(time.time())
        
        if override:
            # Cancel the action
            action.status = ActionStatus.CANCELLED
            logger.info(f"Action {action_id} cancelled by {override_by}: {reason}")
        else:
            # Allow the action to proceed
            logger.info(f"Action {action_id} approved by {override_by}: {reason}")
        
        # Update in database
        self._update_action_in_db(action)
        
        return True
    
    async def rollback_action(self, action_id: str, reason: str) -> Dict[str, Any]:
        """
        Rollback an action
        
        Args:
            action_id: Action ID
            reason: Reason for rollback
            
        Returns:
            Dict with rollback result
        """
        if not self.rollback_enabled:
            return {
                "success": False,
                "error": "Rollback is disabled"
            }
        
        # Get action
        action = self.get_action(action_id)
        if not action:
            return {
                "success": False,
                "error": f"Action {action_id} not found"
            }
        
        # Check if action can be rolled back
        if action.status != ActionStatus.COMPLETED:
            return {
                "success": False,
                "error": f"Cannot rollback action with status {action.status.value}"
            }
        
        # Check if rollback is within timeout
        if action.executed_at and int(time.time()) - action.executed_at > self.rollback_timeout:
            return {
                "success": False,
                "error": f"Rollback timeout exceeded ({self.rollback_timeout} seconds)"
            }
        
        # Create rollback action
        timestamp = int(time.time())
        rollback_action = None
        
        if action.action_type == ActionType.CONTRACT_PAUSE:
            # Create unpause action
            rollback_id = f"rollback_{action_id}_{timestamp}"
            rollback_action = EmergencyAction(
                action_id=rollback_id,
                action_type=ActionType.CONTRACT_UNPAUSE,
                alert_id=action.alert_id,
                alert_source=action.alert_source,
                alert_priority=action.alert_priority,
                target=action.target,
                parameters={
                    "reason": f"Rollback of pause action: {reason}"
                },
                created_at=timestamp,
                updated_at=timestamp
            )
        
        elif action.action_type == ActionType.CONTRACT_UNPAUSE:
            # Create pause action
            rollback_id = f"rollback_{action_id}_{timestamp}"
            rollback_action = EmergencyAction(
                action_id=rollback_id,
                action_type=ActionType.CONTRACT_PAUSE,
                alert_id=action.alert_id,
                alert_source=action.alert_source,
                alert_priority=action.alert_priority,
                target=action.target,
                parameters={
                    "reason": f"Rollback of unpause action: {reason}"
                },
                created_at=timestamp,
                updated_at=timestamp
            )
        
        # Add other rollback types as needed
        
        if not rollback_action:
            return {
                "success": False,
                "error": f"No rollback defined for action type {action.action_type.value}"
            }
        
        # Create rollback action in database
        self._create_action_in_db(rollback_action)
        
        # Execute rollback action immediately
        result = await self._execute_action(rollback_action)
        
        # Update rollback action with result
        rollback_action.result = result
        rollback_action.executed_at = int(time.time())
        rollback_action.updated_at = int(time.time())
        
        if result.get("success", False):
            rollback_action.status = ActionStatus.COMPLETED
        else:
            rollback_action.status = ActionStatus.FAILED
            rollback_action.error = result.get("error", "Unknown error")
        
        # Update in database
        self._update_action_in_db(rollback_action)
        
        return {
            "success": result.get("success", False),
            "message": f"Rollback action {rollback_action.action_id} executed",
            "rollback_action_id": rollback_action.action_id,
            "original_action_id": action_id,
            "result": result
        }

async def main():
    """Main entry point for testing"""
    executor = EmergencyActionExecutor()
    
    # Example alert
    test_alert = {
        "alert_id": "test-alert-001",
        "source": "oracle",
        "priority": "critical",
        "message": "Test oracle alert",
        "details": {
            "asset": "ETH",
            "price": 2000,
            "expected_price": 2200,
            "deviation": 9.1
        }
    }
    
    # Process alert
    action_ids = executor.process_alert(test_alert)
    print(f"Created actions: {action_ids}")
    
    # Start executor
    await executor.start()
    
    # Wait for actions to complete
    await asyncio.sleep(5)
    
    # Get actions
    for action_id in action_ids:
        action = executor.get_action(action_id)
        print(f"Action {action_id} status: {action.status.value}")
        if action.result:
            print(f"Result: {action.result}")
    
    # Stop executor
    await executor.stop()

if __name__ == "__main__":
    asyncio.run(main())