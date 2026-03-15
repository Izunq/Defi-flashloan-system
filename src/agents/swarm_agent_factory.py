#!/usr/bin/env python3
"""
🚀 SWARM AGENT FACTORY - HYPER-SPECIALIZED MICRO-BOT GENERATOR
==============================================================

This module implements a factory system that dynamically creates, manages,
and coordinates thousands of specialized micro-bots for maximum arbitrage
opportunity detection and exploitation.

KEY FEATURES:
🏭 Dynamic Agent Creation - Spawn thousands of specialized micro-bots
🔍 Hyper-Specialization - Each bot focuses on a single, specific task
📊 Performance Tracking - Automatically scale successful bot types
🧬 Evolutionary Selection - Retire underperforming bots, promote winners
🔄 Resource Optimization - Lightweight design for massive parallelism
🔗 Swarm Communication - Inter-bot messaging for complex opportunity detection

INTEGRATION POINTS:
- Artemis AI Core - Strategic oversight and resource allocation
- InterChainCognitiveMesh - Cross-chain coordination
- Distributed Agent Architecture - Infrastructure and failover support
- Halal Compliance - Optional Sharia-compliant bot templates

Author: AI Assistant
Version: 1.0
Date: June 2025
"""

import os
import json
import time
import uuid
import logging
import asyncio
import threading
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import redis
from web3 import Web3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger("SwarmAgentFactory")

# Import security validation
try:
    from emergency_input_sanitizer import (
        emergency_sanitize,
        emergency_validate_eth_address,
        emergency_validate_number,
        emergency_validate_json_data,
        emergency_validate_url_safe,
        SecurityError
    )
    EMERGENCY_VALIDATION_ENABLED = True
    logger.info("🛡️ EMERGENCY VALIDATION ENABLED")
except ImportError:
    EMERGENCY_VALIDATION_ENABLED = False
    logger.warning("⚠️ EMERGENCY VALIDATION NOT AVAILABLE")

def emergency_validate_input(value, field_name="input", validation_type="string"):
    """Emergency input validation wrapper"""
    if not EMERGENCY_VALIDATION_ENABLED:
        return value
    
    try:
        if validation_type == "address":
            return emergency_validate_eth_address(value)
        elif validation_type == "number":
            return emergency_validate_number(value)
        elif validation_type == "json":
            return emergency_validate_json_data(value)
        elif validation_type == "url":
            return emergency_validate_url_safe(value)
        else:
            return emergency_sanitize(value, field_name)
    except SecurityError as e:
        raise ValueError(f"SECURITY: {e}")


class MicroBotType(Enum):
    """Types of specialized micro-bots"""
    PAIR_WATCHER = "pair_watcher"  # Watches specific token pair on specific DEXes
    LIQUIDATION_HUNTER = "liquidation_hunter"  # Looks for liquidation opportunities
    WHALE_WATCHER = "whale_watcher"  # Monitors specific whale wallets
    FLASH_ARBITRAGE = "flash_arbitrage"  # Specialized in flash loan arbitrage
    MEV_SCANNER = "mev_scanner"  # Scans mempool for MEV opportunities
    CROSS_CHAIN_SCOUT = "cross_chain_scout"  # Looks for cross-chain opportunities
    GAS_OPTIMIZER = "gas_optimizer"  # Optimizes gas usage for transactions
    HALAL_COMPLIANT = "halal_compliant"  # Only operates on Sharia-compliant assets
    TRIANGULAR_ARBITRAGE = "triangular_arbitrage"  # Specialized in triangular arbitrage
    YIELD_OPTIMIZER = "yield_optimizer"  # Finds optimal yield farming strategies


@dataclass
class MicroBotTemplate:
    """Template for creating micro-bots"""
    bot_type: MicroBotType
    name: str
    description: str
    parameters: Dict[str, Any]
    code_template: str
    resource_requirements: Dict[str, float]
    halal_compliant: bool = False
    version: str = "1.0"


@dataclass
class MicroBot:
    """A lightweight, specialized agent focused on a single task"""
    bot_id: str
    template_id: str
    bot_type: MicroBotType
    parameters: Dict[str, Any]
    status: str = "initializing"
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    discoveries: List[Dict[str, Any]] = field(default_factory=list)
    resource_usage: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "bot_id": self.bot_id,
            "template_id": self.template_id,
            "bot_type": self.bot_type.value,
            "parameters": self.parameters,
            "status": self.status,
            "created_at": self.created_at,
            "last_active": self.last_active,
            "performance_metrics": self.performance_metrics,
            "discoveries_count": len(self.discoveries),
            "resource_usage": self.resource_usage
        }


class SwarmAgentFactory:
    """
    Factory for creating and managing swarms of specialized micro-bots
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the Swarm Agent Factory
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path or "config/swarm_factory_config.yaml")
        self._setup_directories()
        self._init_redis()
        self._init_web3()
        
        # Templates for different types of micro-bots
        self.templates: Dict[str, MicroBotTemplate] = {}
        self._load_templates()
        
        # Active bots managed by this factory
        self.active_bots: Dict[str, MicroBot] = {}
        
        # Performance tracking
        self.performance_history: Dict[str, List[Dict[str, Any]]] = {}
        
        # Resource management
        self.total_resources_available = self.config.get("resources", {})
        self.resources_used = {k: 0.0 for k in self.total_resources_available}
        
        # Thread pool for parallel bot execution
        self.executor = ThreadPoolExecutor(
            max_workers=self.config.get("max_worker_threads", 50)
        )
        
        # Communication channels
        self.message_bus = MessageBus(self.redis_client)
        
        logger.info(f"Swarm Agent Factory initialized with {len(self.templates)} templates")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file"""
        import yaml
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            # Validate required fields
            required_fields = [
                'redis_url', 'web3_provider', 'resources',
                'scaling_parameters', 'templates_dir'
            ]
            
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing required config field: {field}")
                    
            return config
            
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            # Use default config
            return {
                'redis_url': 'redis://localhost:6379/0',
                'web3_provider': 'http://localhost:8545',
                'resources': {
                    'cpu_cores': 4,
                    'memory_mb': 8192,
                    'network_bandwidth_mbps': 100
                },
                'scaling_parameters': {
                    'min_performance_threshold': 0.2,
                    'scale_up_factor': 2.0,
                    'scale_down_factor': 0.5,
                    'evaluation_interval_seconds': 300
                },
                'templates_dir': 'templates/micro_bots',
                'max_worker_threads': 50,
                'max_bots_per_type': 1000,
                'total_max_bots': 5000
            }
    
    def _setup_directories(self):
        """Create necessary directories"""
        os.makedirs("templates/micro_bots", exist_ok=True)
        os.makedirs("data/swarm", exist_ok=True)
        os.makedirs("logs/swarm", exist_ok=True)
    
    def _init_redis(self):
        """Initialize Redis connection for bot communication"""
        try:
            self.redis_client = redis.Redis.from_url(
                emergency_validate_input(self.config['redis_url'], validation_type="url")
            )
            self.redis_client.ping()  # Test connection
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise ConnectionError(f"Failed to connect to Redis: {e}")
    
    def _init_web3(self):
        """Initialize Web3 connection"""
        try:
            self.web3 = Web3(Web3.HTTPProvider(
                emergency_validate_input(self.config['web3_provider'], validation_type="url")
            ))
            
            if not self.web3.is_connected():
                raise ConnectionError("Failed to connect to Web3 provider")
                
            logger.info(f"Connected to Web3 provider: {self.web3.client_version}")
        except Exception as e:
            logger.error(f"Failed to initialize Web3: {e}")
            raise ConnectionError(f"Failed to initialize Web3: {e}")
    
    def _load_templates(self):
        """Load micro-bot templates from files"""
        import yaml
        
        templates_dir = self.config['templates_dir']
        if not os.path.exists(templates_dir):
            logger.warning(f"Templates directory {templates_dir} does not exist. Creating it.")
            os.makedirs(templates_dir, exist_ok=True)
            self._create_default_templates()
            
        template_files = [f for f in os.listdir(templates_dir) if f.endswith('.yaml')]
        
        for template_file in template_files:
            try:
                with open(os.path.join(templates_dir, template_file), 'r') as f:
                    template_data = yaml.safe_load(f)
                
                template_id = template_file.replace('.yaml', '')
                
                # Validate template data
                required_fields = ['bot_type', 'name', 'description', 'parameters', 
                                  'code_template', 'resource_requirements']
                for field in required_fields:
                    if field not in template_data:
                        logger.warning(f"Template {template_id} missing required field: {field}")
                        continue
                
                # Create template object
                template = MicroBotTemplate(
                    bot_type=MicroBotType(template_data['bot_type']),
                    name=template_data['name'],
                    description=template_data['description'],
                    parameters=template_data['parameters'],
                    code_template=template_data['code_template'],
                    resource_requirements=template_data['resource_requirements'],
                    halal_compliant=template_data.get('halal_compliant', False),
                    version=template_data.get('version', '1.0')
                )
                
                self.templates[template_id] = template
                logger.info(f"Loaded template: {template_id} ({template.name})")
                
            except Exception as e:
                logger.error(f"Error loading template {template_file}: {e}")
    
    def _create_default_templates(self):
        """Create default templates if none exist"""
        import yaml
        
        default_templates = {
            "eth_usdc_pair_watcher": {
                "bot_type": "pair_watcher",
                "name": "ETH-USDC Pair Watcher",
                "description": "Monitors ETH/USDC pair on Uniswap and Sushiswap for arbitrage opportunities",
                "parameters": {
                    "token_pair": ["ETH", "USDC"],
                    "exchanges": ["uniswap_v3", "sushiswap"],
                    "min_price_difference_percent": 0.5,
                    "check_interval_seconds": 5
                },
                "code_template": "pair_watcher_template.py",
                "resource_requirements": {
                    "cpu_cores": 0.1,
                    "memory_mb": 50,
                    "network_bandwidth_mbps": 1
                }
            },
            "whale_watcher_basic": {
                "bot_type": "whale_watcher",
                "name": "Basic Whale Watcher",
                "description": "Monitors specific whale wallets for significant movements",
                "parameters": {
                    "min_transaction_value_usd": 100000,
                    "wallets_to_watch": [],
                    "check_interval_seconds": 10
                },
                "code_template": "whale_watcher_template.py",
                "resource_requirements": {
                    "cpu_cores": 0.1,
                    "memory_mb": 50,
                    "network_bandwidth_mbps": 1
                }
            },
            "halal_flash_arbitrage": {
                "bot_type": "flash_arbitrage",
                "name": "Halal Flash Arbitrage",
                "description": "Executes Shariah-compliant flash arbitrage using MudarabahFlashSwap",
                "parameters": {
                    "min_profit_usd": 5,
                    "max_gas_cost_usd": 2,
                    "halal_assets_only": True
                },
                "code_template": "halal_flash_arbitrage_template.py",
                "resource_requirements": {
                    "cpu_cores": 0.2,
                    "memory_mb": 100,
                    "network_bandwidth_mbps": 2
                },
                "halal_compliant": True
            }
        }
        
        templates_dir = self.config['templates_dir']
        for template_id, template_data in default_templates.items():
            try:
                file_path = os.path.join(templates_dir, f"{template_id}.yaml")
                with open(file_path, 'w') as f:
                    yaml.dump(template_data, f)
                logger.info(f"Created default template: {template_id}")
            except Exception as e:
                logger.error(f"Error creating default template {template_id}: {e}")
    
    def create_micro_bot(self, template_id: str, parameters: Dict[str, Any] = None) -> Optional[str]:
        """
        Create a new micro-bot from a template
        
        Args:
            template_id: ID of the template to use
            parameters: Optional parameters to override template defaults
            
        Returns:
            Bot ID if successful, None otherwise
        """
        if template_id not in self.templates:
            logger.error(f"Template {template_id} not found")
            return None
        
        template = self.templates[template_id]
        
        # Check resource availability
        for resource, amount in template.resource_requirements.items():
            if resource in self.resources_used:
                if self.resources_used[resource] + amount > self.total_resources_available.get(resource, 0):
                    logger.warning(f"Insufficient {resource} to create bot from template {template_id}")
                    return None
        
        # Generate bot ID
        bot_id = f"{template.bot_type.value}_{uuid.uuid4().hex[:8]}"
        
        # Merge parameters (template defaults + overrides)
        merged_parameters = template.parameters.copy()
        if parameters:
            merged_parameters.update(parameters)
        
        # Create bot instance
        bot = MicroBot(
            bot_id=bot_id,
            template_id=template_id,
            bot_type=template.bot_type,
            parameters=merged_parameters,
            status="created",
            performance_metrics={
                "opportunities_found": 0,
                "opportunities_executed": 0,
                "total_profit_usd": 0.0,
                "success_rate": 0.0,
                "avg_response_time_ms": 0.0
            }
        )
        
        # Update resource usage
        for resource, amount in template.resource_requirements.items():
            if resource in self.resources_used:
                self.resources_used[resource] += amount
                bot.resource_usage[resource] = amount
        
        # Store bot
        self.active_bots[bot_id] = bot
        
        # Initialize performance history
        self.performance_history[bot_id] = []
        
        logger.info(f"Created micro-bot {bot_id} from template {template_id}")
        return bot_id
    
    def start_micro_bot(self, bot_id: str) -> bool:
        """
        Start a micro-bot
        
        Args:
            bot_id: ID of the bot to start
            
        Returns:
            True if successful, False otherwise
        """
        if bot_id not in self.active_bots:
            logger.error(f"Bot {bot_id} not found")
            return False
        
        bot = self.active_bots[bot_id]
        if bot.status in ["running", "starting"]:
            logger.warning(f"Bot {bot_id} is already running or starting")
            return False
        
        # Update status
        bot.status = "starting"
        
        # Submit bot execution to thread pool
        try:
            self.executor.submit(self._run_micro_bot, bot_id)
            logger.info(f"Started micro-bot {bot_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to start micro-bot {bot_id}: {e}")
            bot.status = "error"
            return False
    
    def _run_micro_bot(self, bot_id: str):
        """
        Run a micro-bot in a separate thread
        
        Args:
            bot_id: ID of the bot to run
        """
        if bot_id not in self.active_bots:
            logger.error(f"Bot {bot_id} not found")
            return
        
        bot = self.active_bots[bot_id]
        template = self.templates.get(bot.template_id)
        if not template:
            logger.error(f"Template {bot.template_id} not found for bot {bot_id}")
            bot.status = "error"
            return
        
        # Update status
        bot.status = "running"
        
        # Execute bot logic based on type
        try:
            if bot.bot_type == MicroBotType.PAIR_WATCHER:
                self._run_pair_watcher_bot(bot)
            elif bot.bot_type == MicroBotType.WHALE_WATCHER:
                self._run_whale_watcher_bot(bot)
            elif bot.bot_type == MicroBotType.FLASH_ARBITRAGE:
                self._run_flash_arbitrage_bot(bot)
            elif bot.bot_type == MicroBotType.MEV_SCANNER:
                self._run_mev_scanner_bot(bot)
            elif bot.bot_type == MicroBotType.CROSS_CHAIN_SCOUT:
                self._run_cross_chain_scout_bot(bot)
            else:
                logger.warning(f"No implementation for bot type {bot.bot_type}")
                bot.status = "error"
        except Exception as e:
            logger.error(f"Error running micro-bot {bot_id}: {e}")
            bot.status = "error"
    
    def _run_pair_watcher_bot(self, bot: MicroBot):
        """Run a pair watcher bot"""
        # Implementation would go here
        # This is a placeholder for the actual implementation
        pass
    
    def _run_whale_watcher_bot(self, bot: MicroBot):
        """Run a whale watcher bot"""
        # Implementation would go here
        # This is a placeholder for the actual implementation
        pass
    
    def _run_flash_arbitrage_bot(self, bot: MicroBot):
        """Run a flash arbitrage bot"""
        # Implementation would go here
        # This is a placeholder for the actual implementation
        pass
    
    def _run_mev_scanner_bot(self, bot: MicroBot):
        """Run a MEV scanner bot"""
        # Implementation would go here
        # This is a placeholder for the actual implementation
        pass
    
    def _run_cross_chain_scout_bot(self, bot: MicroBot):
        """Run a cross-chain scout bot"""
        # Implementation would go here
        # This is a placeholder for the actual implementation
        pass
    
    def stop_micro_bot(self, bot_id: str) -> bool:
        """
        Stop a micro-bot
        
        Args:
            bot_id: ID of the bot to stop
            
        Returns:
            True if successful, False otherwise
        """
        if bot_id not in self.active_bots:
            logger.error(f"Bot {bot_id} not found")
            return False
        
        bot = self.active_bots[bot_id]
        if bot.status not in ["running", "starting"]:
            logger.warning(f"Bot {bot_id} is not running")
            return False
        
        # Update status
        bot.status = "stopping"
        
        # Actual stopping logic would depend on implementation
        # For now, we just update the status
        bot.status = "stopped"
        
        logger.info(f"Stopped micro-bot {bot_id}")
        return True
    
    def delete_micro_bot(self, bot_id: str) -> bool:
        """
        Delete a micro-bot and free its resources
        
        Args:
            bot_id: ID of the bot to delete
            
        Returns:
            True if successful, False otherwise
        """
        if bot_id not in self.active_bots:
            logger.error(f"Bot {bot_id} not found")
            return False
        
        bot = self.active_bots[bot_id]
        
        # Stop the bot if it's running
        if bot.status in ["running", "starting"]:
            self.stop_micro_bot(bot_id)
        
        # Free resources
        for resource, amount in bot.resource_usage.items():
            if resource in self.resources_used:
                self.resources_used[resource] -= amount
        
        # Remove bot
        del self.active_bots[bot_id]
        
        # Remove performance history
        if bot_id in self.performance_history:
            del self.performance_history[bot_id]
        
        logger.info(f"Deleted micro-bot {bot_id}")
        return True
    
    def update_bot_performance(self, bot_id: str, metrics: Dict[str, Any]) -> bool:
        """
        Update performance metrics for a bot
        
        Args:
            bot_id: ID of the bot
            metrics: Performance metrics to update
            
        Returns:
            True if successful, False otherwise
        """
        if bot_id not in self.active_bots:
            logger.error(f"Bot {bot_id} not found")
            return False
        
        bot = self.active_bots[bot_id]
        
        # Update metrics
        for key, value in metrics.items():
            if key in bot.performance_metrics:
                bot.performance_metrics[key] = value
        
        # Update last active timestamp
        bot.last_active = time.time()
        
        # Add to performance history
        self.performance_history[bot_id].append({
            "timestamp": time.time(),
            "metrics": bot.performance_metrics.copy()
        })
        
        logger.debug(f"Updated performance metrics for bot {bot_id}")
        return True
    
    def evaluate_and_scale(self):
        """
        Evaluate bot performance and scale up/down as needed
        """
        logger.info("Evaluating bot performance for scaling decisions")
        
        # Group bots by template
        bots_by_template: Dict[str, List[MicroBot]] = {}
        for bot_id, bot in self.active_bots.items():
            if bot.template_id not in bots_by_template:
                bots_by_template[bot.template_id] = []
            bots_by_template[bot.template_id].append(bot)
        
        # Evaluate each template group
        for template_id, bots in bots_by_template.items():
            # Skip if no bots
            if not bots:
                continue
            
            # Calculate average performance
            total_opportunities = sum(bot.performance_metrics.get("opportunities_found", 0) for bot in bots)
            total_profit = sum(bot.performance_metrics.get("total_profit_usd", 0) for bot in bots)
            avg_profit_per_bot = total_profit / len(bots) if bots else 0
            
            # Get scaling parameters
            min_threshold = self.config["scaling_parameters"]["min_performance_threshold"]
            scale_up = self.config["scaling_parameters"]["scale_up_factor"]
            scale_down = self.config["scaling_parameters"]["scale_down_factor"]
            max_bots_per_type = self.config["max_bots_per_type"]
            
            # Make scaling decision
            if avg_profit_per_bot > 0 and total_opportunities > 0:
                # Performing well, consider scaling up
                current_count = len(bots)
                target_count = min(int(current_count * scale_up), max_bots_per_type)
                
                if target_count > current_count:
                    # Scale up
                    logger.info(f"Scaling up template {template_id} from {current_count} to {target_count} bots")
                    for _ in range(target_count - current_count):
                        self.create_micro_bot(template_id)
            elif avg_profit_per_bot < min_threshold:
                # Performing poorly, consider scaling down
                current_count = len(bots)
                target_count = max(1, int(current_count * scale_down))
                
                if target_count < current_count:
                    # Scale down
                    logger.info(f"Scaling down template {template_id} from {current_count} to {target_count} bots")
                    # Sort by performance (worst first)
                    bots_sorted = sorted(bots, 
                                        key=lambda b: b.performance_metrics.get("total_profit_usd", 0))
                    # Delete worst performers
                    for bot in bots_sorted[:current_count - target_count]:
                        self.delete_micro_bot(bot.bot_id)
    
    def get_bot_status(self, bot_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a micro-bot
        
        Args:
            bot_id: ID of the bot
            
        Returns:
            Bot status dictionary if found, None otherwise
        """
        if bot_id not in self.active_bots:
            logger.error(f"Bot {bot_id} not found")
            return None
        
        bot = self.active_bots[bot_id]
        return bot.to_dict()
    
    def get_all_bots(self) -> List[Dict[str, Any]]:
        """
        Get status of all micro-bots
        
        Returns:
            List of bot status dictionaries
        """
        return [bot.to_dict() for bot in self.active_bots.values()]
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """
        Get current resource usage
        
        Returns:
            Dictionary of resource usage
        """
        return {
            "used": self.resources_used,
            "total": self.total_resources_available,
            "percent_used": {
                k: (self.resources_used.get(k, 0) / v) * 100 
                for k, v in self.total_resources_available.items() 
                if v > 0
            }
        }
    
    def run(self):
        """
        Run the Swarm Agent Factory
        """
        logger.info("Starting Swarm Agent Factory")
        
        # Start evaluation loop
        evaluation_interval = self.config["scaling_parameters"]["evaluation_interval_seconds"]
        
        try:
            while True:
                # Evaluate and scale
                self.evaluate_and_scale()
                
                # Sleep
                time.sleep(evaluation_interval)
        except KeyboardInterrupt:
            logger.info("Stopping Swarm Agent Factory")
        finally:
            # Clean up
            self.executor.shutdown(wait=False)
            logger.info("Swarm Agent Factory stopped")


class MessageBus:
    """
    Message bus for inter-bot communication
    """
    
    def __init__(self, redis_client: redis.Redis):
        """
        Initialize the message bus
        
        Args:
            redis_client: Redis client for pub/sub
        """
        self.redis = redis_client
        self.pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
        self.channels: Dict[str, List[Callable]] = {}
        self.running = False
        self.thread = None
    
    def subscribe(self, channel: str, callback: Callable):
        """
        Subscribe to a channel
        
        Args:
            channel: Channel name
            callback: Callback function to call when a message is received
        """
        if channel not in self.channels:
            self.channels[channel] = []
            self.pubsub.subscribe(channel)
        
        self.channels[channel].append(callback)
    
    def publish(self, channel: str, message: Dict[str, Any]):
        """
        Publish a message to a channel
        
        Args:
            channel: Channel name
            message: Message to publish
        """
        self.redis.publish(channel, json.dumps(message))
    
    def start(self):
        """Start the message bus"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._message_loop)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """Stop the message bus"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None
    
    def _message_loop(self):
        """Message processing loop"""
        while self.running:
            message = self.pubsub.get_message()
            if message:
                try:
                    channel = message['channel'].decode('utf-8')
                    data = json.loads(message['data'].decode('utf-8'))
                    
                    # Call callbacks
                    if channel in self.channels:
                        for callback in self.channels[channel]:
                            try:
                                callback(data)
                            except Exception as e:
                                logger.error(f"Error in message callback: {e}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
            
            time.sleep(0.01)


def main():
    """Main entry point"""
    try:
        factory = SwarmAgentFactory()
        factory.run()
    except Exception as e:
        logger.error(f"Error in Swarm Agent Factory: {e}")
        return 1
    return 0


if __name__ == "__main__":
    main()