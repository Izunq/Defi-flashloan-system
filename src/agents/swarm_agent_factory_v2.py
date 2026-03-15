#!/usr/bin/env python3
"""
🚀 SWARM AGENT FACTORY V2 - DYNAMIC MICRO-AGENT GENERATOR
=========================================================

This module implements a factory system that dynamically creates, manages,
and coordinates thousands of specialized micro-agents for maximum arbitrage
opportunity detection and exploitation.

KEY FEATURES:
🏭 Dynamic Agent Creation - Spawn thousands of specialized micro-bots
🔍 Hyper-Specialization - Each bot focuses on a single, specific task
📊 Performance Tracking - Automatically scale successful bot types
🧬 Evolutionary Selection - Retire underperforming bots, promote winners
🔄 Resource Optimization - Lightweight design for massive parallelism
🔗 Swarm Communication - Inter-bot messaging for complex opportunity detection

Author: AI Assistant
Version: 2.0
Date: June 2025
"""

import os
import json
import time
import uuid
import logging
import asyncio
import threading
import importlib
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
logger = logging.getLogger("SwarmAgentFactoryV2")

# Import security validation
try:
    from src.validation.emergency_input_sanitizer import (
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


class MicroAgentType(Enum):
    """Types of specialized micro-agents"""
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
class MicroAgentTemplate:
    """Template for creating micro-agents"""
    agent_type: MicroAgentType
    name: str
    description: str
    parameters: Dict[str, Any]
    module_path: str
    class_name: str
    resource_requirements: Dict[str, float]
    halal_compliant: bool = False
    version: str = "1.0"


@dataclass
class MicroAgentInstance:
    """Information about a running micro-agent instance"""
    agent_id: str
    template_id: str
    agent_type: MicroAgentType
    parameters: Dict[str, Any]
    status: str = "initializing"
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    discoveries: List[Dict[str, Any]] = field(default_factory=list)
    resource_usage: Dict[str, float] = field(default_factory=dict)
    process: Any = None  # Reference to the agent process or thread
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "agent_id": self.agent_id,
            "template_id": self.template_id,
            "agent_type": self.agent_type.value,
            "parameters": self.parameters,
            "status": self.status,
            "created_at": self.created_at,
            "last_active": self.last_active,
            "performance_metrics": self.performance_metrics,
            "discoveries_count": len(self.discoveries),
            "resource_usage": self.resource_usage
        }


class SwarmAgentFactoryV2:
    """
    Factory for creating and managing swarms of specialized micro-agents
    
    This factory dynamically creates, manages, and coordinates thousands of
    specialized micro-agents for maximum arbitrage opportunity detection
    and exploitation.
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
        
        # Templates for different types of micro-agents
        self.templates: Dict[str, MicroAgentTemplate] = {}
        self._load_templates()
        
        # Active agents managed by this factory
        self.active_agents: Dict[str, MicroAgentInstance] = {}
        
        # Performance tracking
        self.performance_history: Dict[str, List[Dict[str, Any]]] = {}
        
        # Resource management
        self.total_resources_available = self.config.get("resources", {})
        self.resources_used = {k: 0.0 for k in self.total_resources_available}
        
        # Thread pool for parallel agent execution
        self.executor = ThreadPoolExecutor(
            max_workers=self.config.get("max_worker_threads", 50)
        )
        
        # Communication channels
        self.message_bus = MessageBus(self.redis_client)
        self.message_bus.subscribe("swarm:agent_status", self._handle_agent_status)
        self.message_bus.subscribe("swarm:discoveries", self._handle_discovery)
        self.message_bus.subscribe("swarm:factory:commands", self._handle_factory_command)
        
        # Start message bus
        self.message_bus.start()
        
        logger.info(f"Swarm Agent Factory V2 initialized with {len(self.templates)} templates")
    
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
                'templates_dir': 'templates/micro_agents',
                'max_worker_threads': 50,
                'max_agents_per_type': 1000,
                'total_max_agents': 5000,
                'halal_mode': False
            }
    
    def _setup_directories(self):
        """Create necessary directories"""
        os.makedirs("templates/micro_agents", exist_ok=True)
        os.makedirs("data/swarm", exist_ok=True)
        os.makedirs("logs/swarm", exist_ok=True)
    
    def _init_redis(self):
        """Initialize Redis connection for agent communication"""
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
        """Load micro-agent templates from files"""
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
                required_fields = ['agent_type', 'name', 'description', 'parameters', 
                                  'module_path', 'class_name', 'resource_requirements']
                for field in required_fields:
                    if field not in template_data:
                        logger.warning(f"Template {template_id} missing required field: {field}")
                        continue
                
                # Create template object
                template = MicroAgentTemplate(
                    agent_type=MicroAgentType(template_data['agent_type']),
                    name=template_data['name'],
                    description=template_data['description'],
                    parameters=template_data['parameters'],
                    module_path=template_data['module_path'],
                    class_name=template_data['class_name'],
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
                "agent_type": "pair_watcher",
                "name": "ETH-USDC Pair Watcher",
                "description": "Monitors ETH/USDC pair on Uniswap and Sushiswap for arbitrage opportunities",
                "parameters": {
                    "token_pair": ["ETH", "USDC"],
                    "exchanges": ["uniswap_v3", "sushiswap"],
                    "min_price_difference_percent": 0.5,
                    "check_interval_seconds": 5,
                    "max_slippage_percent": 0.3,
                    "gas_price_limit_gwei": 50,
                    "min_profit_usd": 1.0
                },
                "module_path": "src.agents.pair_watcher_micro_agent",
                "class_name": "PairWatcherMicroAgent",
                "resource_requirements": {
                    "cpu_cores": 0.1,
                    "memory_mb": 50,
                    "network_bandwidth_mbps": 1
                },
                "halal_compliant": False,
                "version": "1.0"
            },
            "whale_watcher_basic": {
                "agent_type": "whale_watcher",
                "name": "Basic Whale Watcher",
                "description": "Monitors specific whale wallets for significant movements",
                "parameters": {
                    "min_transaction_value_usd": 100000,
                    "wallets_to_watch": [],
                    "check_interval_seconds": 10
                },
                "module_path": "src.agents.whale_watcher_micro_agent",
                "class_name": "WhaleWatcherMicroAgent",
                "resource_requirements": {
                    "cpu_cores": 0.1,
                    "memory_mb": 50,
                    "network_bandwidth_mbps": 1
                },
                "halal_compliant": False,
                "version": "1.0"
            },
            "halal_pair_watcher": {
                "agent_type": "pair_watcher",
                "name": "Halal Pair Watcher",
                "description": "Monitors Shariah-compliant token pairs for arbitrage opportunities",
                "parameters": {
                    "token_pair": ["WETH", "DAI"],
                    "exchanges": ["uniswap_v3", "sushiswap"],
                    "min_price_difference_percent": 0.5,
                    "check_interval_seconds": 5,
                    "max_slippage_percent": 0.3,
                    "gas_price_limit_gwei": 50,
                    "min_profit_usd": 1.0,
                    "halal_compliance_check": True
                },
                "module_path": "src.agents.pair_watcher_micro_agent",
                "class_name": "PairWatcherMicroAgent",
                "resource_requirements": {
                    "cpu_cores": 0.1,
                    "memory_mb": 50,
                    "network_bandwidth_mbps": 1
                },
                "halal_compliant": True,
                "version": "1.0"
            }
        }
        
        # Write default templates to files
        for template_id, template_data in default_templates.items():
            template_path = os.path.join(self.config['templates_dir'], f"{template_id}.yaml")
            try:
                with open(template_path, 'w') as f:
                    yaml.dump(template_data, f)
                logger.info(f"Created default template: {template_id}")
            except Exception as e:
                logger.error(f"Error creating default template {template_id}: {e}")
    
    def create_agent(self, template_id: str, parameters: Dict[str, Any] = None) -> Optional[str]:
        """
        Create a new micro-agent from a template
        
        Args:
            template_id: ID of the template to use
            parameters: Optional parameters to override template defaults
            
        Returns:
            ID of the created agent, or None if creation failed
        """
        if template_id not in self.templates:
            logger.error(f"Template {template_id} not found")
            return None
        
        template = self.templates[template_id]
        
        # Check if we're in halal mode and this template is not halal compliant
        if self.config.get("halal_mode", False) and not template.halal_compliant:
            logger.warning(f"Cannot create non-halal agent {template_id} in halal mode")
            return None
        
        # Check resource availability
        for resource, amount in template.resource_requirements.items():
            if resource in self.resources_used and resource in self.total_resources_available:
                if self.resources_used[resource] + amount > self.total_resources_available[resource]:
                    logger.warning(f"Insufficient {resource} to create agent from template {template_id}")
                    return None
        
        # Check agent count limits
        agent_type = template.agent_type
        type_count = sum(1 for a in self.active_agents.values() if a.agent_type == agent_type)
        if type_count >= self.config.get("max_agents_per_type", 1000):
            logger.warning(f"Maximum number of agents of type {agent_type.value} reached")
            return None
        
        if len(self.active_agents) >= self.config.get("total_max_agents", 5000):
            logger.warning("Maximum total number of agents reached")
            return None
        
        # Generate agent ID
        agent_id = str(uuid.uuid4())
        
        # Merge parameters
        merged_parameters = template.parameters.copy()
        if parameters:
            merged_parameters.update(parameters)
        
        # Create agent instance record
        agent_instance = MicroAgentInstance(
            agent_id=agent_id,
            template_id=template_id,
            agent_type=template.agent_type,
            parameters=merged_parameters,
            status="initializing",
            created_at=time.time(),
            last_active=time.time(),
            performance_metrics={},
            discoveries=[],
            resource_usage=template.resource_requirements.copy()
        )
        
        # Update resource usage
        for resource, amount in template.resource_requirements.items():
            if resource in self.resources_used:
                self.resources_used[resource] += amount
        
        # Add to active agents
        self.active_agents[agent_id] = agent_instance
        
        # Start the agent
        success = self._start_agent(agent_id)
        
        if not success:
            # Cleanup if start failed
            self._cleanup_agent(agent_id)
            return None
        
        logger.info(f"Created agent {agent_id} from template {template_id}")
        return agent_id
    
    def _start_agent(self, agent_id: str) -> bool:
        """
        Start a micro-agent
        
        Args:
            agent_id: ID of the agent to start
            
        Returns:
            True if successful, False otherwise
        """
        if agent_id not in self.active_agents:
            logger.error(f"Agent {agent_id} not found")
            return False
        
        agent_instance = self.active_agents[agent_id]
        template_id = agent_instance.template_id
        
        if template_id not in self.templates:
            logger.error(f"Template {template_id} not found")
            return False
        
        template = self.templates[template_id]
        
        try:
            # Import the agent class
            module = importlib.import_module(template.module_path)
            agent_class = getattr(module, template.class_name)
            
            # Create the agent instance
            agent = agent_class(
                agent_id=agent_id,
                parameters=agent_instance.parameters,
                redis_url=self.config['redis_url'],
                web3_provider=self.config['web3_provider']
            )
            
            # Start the agent in a separate thread
            def run_agent():
                try:
                    agent.start()
                    # Keep thread alive until agent is stopped
                    while agent.status != "stopped":
                        time.sleep(1)
                except Exception as e:
                    logger.error(f"Error running agent {agent_id}: {e}")
            
            # Start the agent thread
            agent_thread = threading.Thread(target=run_agent)
            agent_thread.daemon = True
            agent_thread.start()
            
            # Store the agent instance and thread
            agent_instance.process = agent
            agent_instance.status = "running"
            
            logger.info(f"Started agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting agent {agent_id}: {e}")
            return False
    
    def stop_agent(self, agent_id: str) -> bool:
        """
        Stop a micro-agent
        
        Args:
            agent_id: ID of the agent to stop
            
        Returns:
            True if successful, False otherwise
        """
        if agent_id not in self.active_agents:
            logger.error(f"Agent {agent_id} not found")
            return False
        
        agent_instance = self.active_agents[agent_id]
        
        try:
            # Stop the agent
            if agent_instance.process:
                agent_instance.process.stop()
            
            agent_instance.status = "stopped"
            logger.info(f"Stopped agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping agent {agent_id}: {e}")
            return False
    
    def delete_agent(self, agent_id: str) -> bool:
        """
        Delete a micro-agent
        
        Args:
            agent_id: ID of the agent to delete
            
        Returns:
            True if successful, False otherwise
        """
        if agent_id not in self.active_agents:
            logger.error(f"Agent {agent_id} not found")
            return False
        
        # Stop the agent if it's running
        if self.active_agents[agent_id].status not in ["stopped", "error"]:
            self.stop_agent(agent_id)
        
        # Clean up resources
        self._cleanup_agent(agent_id)
        
        logger.info(f"Deleted agent {agent_id}")
        return True
    
    def _cleanup_agent(self, agent_id: str):
        """
        Clean up resources used by an agent
        
        Args:
            agent_id: ID of the agent to clean up
        """
        if agent_id not in self.active_agents:
            return
        
        agent_instance = self.active_agents[agent_id]
        
        # Update resource usage
        for resource, amount in agent_instance.resource_usage.items():
            if resource in self.resources_used:
                self.resources_used[resource] -= amount
        
        # Remove from active agents
        del self.active_agents[agent_id]
    
    def _handle_agent_status(self, message: Dict[str, Any]):
        """
        Handle agent status updates
        
        Args:
            message: Status update message
        """
        if "agent_id" not in message:
            return
        
        agent_id = message["agent_id"]
        
        if agent_id in self.active_agents:
            agent_instance = self.active_agents[agent_id]
            
            # Update status
            if "status" in message:
                agent_instance.status = message["status"]
            
            # Update last active timestamp
            if "last_active" in message:
                agent_instance.last_active = message["last_active"]
            
            # Update performance metrics
            if "performance_metrics" in message:
                agent_instance.performance_metrics = message["performance_metrics"]
            
            # Update discoveries count
            if "discoveries_count" in message:
                # We don't store the actual discoveries in the factory
                # to avoid memory bloat
                pass
            
            # Add to performance history
            template_id = agent_instance.template_id
            if template_id not in self.performance_history:
                self.performance_history[template_id] = []
            
            self.performance_history[template_id].append({
                "agent_id": agent_id,
                "timestamp": time.time(),
                "metrics": agent_instance.performance_metrics.copy()
            })
            
            # Trim performance history if it gets too long
            if len(self.performance_history[template_id]) > 1000:
                self.performance_history[template_id] = self.performance_history[template_id][-1000:]
    
    def _handle_discovery(self, message: Dict[str, Any]):
        """
        Handle agent discoveries
        
        Args:
            message: Discovery message
        """
        # We don't need to do anything with discoveries in the factory
        # They are handled by the Parallel Opportunity Coordinator
        pass
    
    def _handle_factory_command(self, message: Dict[str, Any]):
        """
        Handle commands sent to the factory
        
        Args:
            message: Command message
        """
        if "action" not in message:
            logger.warning(f"Received command without action: {message}")
            return
        
        action = message["action"]
        
        if action == "create_agent":
            if "template_id" in message:
                template_id = message["template_id"]
                parameters = message.get("parameters", {})
                agent_id = self.create_agent(template_id, parameters)
                
                # Send response if requested
                if "response_channel" in message and agent_id:
                    response = {
                        "action": "create_agent",
                        "success": bool(agent_id),
                        "agent_id": agent_id,
                        "template_id": template_id
                    }
                    self.redis_client.publish(message["response_channel"], json.dumps(response))
        
        elif action == "stop_agent":
            if "agent_id" in message:
                agent_id = message["agent_id"]
                success = self.stop_agent(agent_id)
                
                # Send response if requested
                if "response_channel" in message:
                    response = {
                        "action": "stop_agent",
                        "success": success,
                        "agent_id": agent_id
                    }
                    self.redis_client.publish(message["response_channel"], json.dumps(response))
        
        elif action == "delete_agent":
            if "agent_id" in message:
                agent_id = message["agent_id"]
                success = self.delete_agent(agent_id)
                
                # Send response if requested
                if "response_channel" in message:
                    response = {
                        "action": "delete_agent",
                        "success": success,
                        "agent_id": agent_id
                    }
                    self.redis_client.publish(message["response_channel"], json.dumps(response))
        
        elif action == "get_agent_status":
            if "agent_id" in message:
                agent_id = message["agent_id"]
                status = self.get_agent_status(agent_id)
                
                # Send response if requested
                if "response_channel" in message:
                    response = {
                        "action": "get_agent_status",
                        "success": bool(status),
                        "agent_id": agent_id,
                        "status": status
                    }
                    self.redis_client.publish(message["response_channel"], json.dumps(response))
        
        elif action == "get_all_agents":
            agents = self.get_all_agents()
            
            # Send response if requested
            if "response_channel" in message:
                response = {
                    "action": "get_all_agents",
                    "success": True,
                    "agents": agents
                }
                self.redis_client.publish(message["response_channel"], json.dumps(response))
        
        elif action == "get_resource_usage":
            usage = self.get_resource_usage()
            
            # Send response if requested
            if "response_channel" in message:
                response = {
                    "action": "get_resource_usage",
                    "success": True,
                    "usage": usage
                }
                self.redis_client.publish(message["response_channel"], json.dumps(response))
        
        elif action == "evaluate_and_scale":
            self.evaluate_and_scale()
            
            # Send response if requested
            if "response_channel" in message:
                response = {
                    "action": "evaluate_and_scale",
                    "success": True
                }
                self.redis_client.publish(message["response_channel"], json.dumps(response))
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a micro-agent
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Agent status dictionary, or None if agent not found
        """
        if agent_id not in self.active_agents:
            return None
        
        return self.active_agents[agent_id].to_dict()
    
    def get_all_agents(self) -> List[Dict[str, Any]]:
        """
        Get information about all active agents
        
        Returns:
            List of agent status dictionaries
        """
        return [agent.to_dict() for agent in self.active_agents.values()]
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """
        Get resource usage information
        
        Returns:
            Dictionary with resource usage information
        """
        return {
            "resources_used": self.resources_used,
            "total_resources_available": self.total_resources_available,
            "agent_count": len(self.active_agents),
            "agent_count_by_type": {
                agent_type.value: sum(1 for a in self.active_agents.values() if a.agent_type == agent_type)
                for agent_type in MicroAgentType
            }
        }
    
    def evaluate_and_scale(self):
        """
        Evaluate agent performance and scale up/down as needed
        
        This method analyzes the performance of agents and:
        1. Scales up successful agent types by creating more instances
        2. Scales down underperforming agent types by removing instances
        """
        logger.info("Evaluating agent performance and scaling")
        
        # Group agents by template
        agents_by_template = {}
        for agent_id, agent in self.active_agents.items():
            template_id = agent.template_id
            if template_id not in agents_by_template:
                agents_by_template[template_id] = []
            agents_by_template[template_id].append(agent)
        
        # Evaluate each template
        for template_id, agents in agents_by_template.items():
            if template_id not in self.templates:
                continue
            
            template = self.templates[template_id]
            
            # Calculate average performance
            total_opportunities = sum(
                agent.performance_metrics.get("opportunities_found", 0)
                for agent in agents
            )
            
            avg_opportunities = total_opportunities / len(agents) if agents else 0
            
            # Get scaling parameters
            min_threshold = self.config["scaling_parameters"]["min_performance_threshold"]
            scale_up_factor = self.config["scaling_parameters"]["scale_up_factor"]
            scale_down_factor = self.config["scaling_parameters"]["scale_down_factor"]
            
            # Determine if we should scale up or down
            if avg_opportunities > 0:
                # Scale up - create more agents of this type
                current_count = len(agents)
                max_count = self.config.get("max_agents_per_type", 1000)
                
                # Calculate how many to add
                to_add = int(current_count * scale_up_factor) - current_count
                to_add = min(to_add, max_count - current_count)
                
                logger.info(f"Scaling up template {template_id}: adding {to_add} agents")
                
                # Create new agents
                for _ in range(to_add):
                    # Create with slight parameter variations for diversity
                    parameters = template.parameters.copy()
                    
                    # Add small random variations to numeric parameters
                    for key, value in parameters.items():
                        if isinstance(value, (int, float)) and key != "check_interval_seconds":
                            # Add +/- 10% variation
                            parameters[key] = value * (0.9 + 0.2 * random.random())
                    
                    self.create_agent(template_id, parameters)
            
            elif avg_opportunities < min_threshold:
                # Scale down - remove some agents of this type
                current_count = len(agents)
                
                # Calculate how many to remove
                to_remove = current_count - int(current_count * scale_down_factor)
                to_remove = min(to_remove, current_count - 1)  # Always keep at least one
                
                logger.info(f"Scaling down template {template_id}: removing {to_remove} agents")
                
                # Sort agents by performance (ascending)
                sorted_agents = sorted(
                    agents,
                    key=lambda a: a.performance_metrics.get("opportunities_found", 0)
                )
                
                # Remove the worst performing agents
                for agent in sorted_agents[:to_remove]:
                    self.delete_agent(agent.agent_id)
    
    def run(self):
        """Run the factory's main loop"""
        logger.info("Starting Swarm Agent Factory V2 main loop")
        
        try:
            # Create initial agents from templates
            for template_id, template in self.templates.items():
                # Skip non-halal templates if in halal mode
                if self.config.get("halal_mode", False) and not template.halal_compliant:
                    continue
                
                # Create a few instances of each template
                for _ in range(5):  # Start with 5 of each type
                    self.create_agent(template_id)
            
            # Main loop
            last_evaluation = time.time()
            
            while True:
                # Periodically evaluate and scale
                now = time.time()
                if now - last_evaluation > self.config["scaling_parameters"]["evaluation_interval_seconds"]:
                    self.evaluate_and_scale()
                    last_evaluation = now
                
                # Sleep for a bit
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, shutting down")
        finally:
            # Stop all agents
            for agent_id in list(self.active_agents.keys()):
                self.stop_agent(agent_id)
            
            # Stop message bus
            self.message_bus.stop()
            
            logger.info("Swarm Agent Factory V2 stopped")


class MessageBus:
    """
    Message bus for communication between components
    
    This class provides a simple publish-subscribe mechanism using Redis.
    """
    
    def __init__(self, redis_client: redis.Redis):
        """
        Initialize the message bus
        
        Args:
            redis_client: Redis client instance
        """
        self.redis_client = redis_client
        self.pubsub = redis_client.pubsub()
        self.callbacks = {}
        self.running = False
        self.thread = None
    
    def subscribe(self, channel: str, callback: Callable):
        """
        Subscribe to a channel
        
        Args:
            channel: Channel to subscribe to
            callback: Function to call when a message is received
        """
        self.callbacks[channel] = callback
        self.pubsub.subscribe(channel)
        logger.debug(f"Subscribed to channel: {channel}")
    
    def publish(self, channel: str, message: Dict[str, Any]):
        """
        Publish a message to a channel
        
        Args:
            channel: Channel to publish to
            message: Message to publish
        """
        self.redis_client.publish(channel, json.dumps(message))
        logger.debug(f"Published message to channel: {channel}")
    
    def start(self):
        """Start the message bus"""
        self.running = True
        self.thread = threading.Thread(target=self._message_loop)
        self.thread.daemon = True
        self.thread.start()
        logger.debug("Message bus started")
    
    def stop(self):
        """Stop the message bus"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        logger.debug("Message bus stopped")
    
    def _message_loop(self):
        """Message processing loop"""
        for message in self.pubsub.listen():
            if not self.running:
                break
            
            if message["type"] == "message":
                channel = message["channel"].decode("utf-8")
                if channel in self.callbacks:
                    try:
                        data = json.loads(message["data"])
                        self.callbacks[channel](data)
                    except Exception as e:
                        logger.error(f"Error processing message on channel {channel}: {e}")


def main():
    """Main entry point"""
    factory = SwarmAgentFactoryV2()
    factory.run()


if __name__ == "__main__":
    main()