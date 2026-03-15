"""
Enhanced Parallel Opportunity Coordinator

This module implements an enhanced version of the Parallel Opportunity Coordinator
that serves as a dedicated service for assembling partial opportunities discovered
by the swarm into executable trades.

Key features:
- Listens to all "partial opportunity" messages from the swarm
- Uses graph theory and pattern matching to identify profitable multi-step paths
- Constructs final transaction payloads
- Requests final risk-approval and execution from the Artemis AI Core
- Provides a comprehensive API for monitoring and management
"""

import os
import sys
import json
import time
import uuid
import logging
import threading
import networkx as nx
from enum import Enum
from typing import Dict, List, Set, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
import redis
from web3 import Web3
import numpy as np
from datetime import datetime, timedelta
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ParallelOpportunityCoordinator")

# Add parent directory to path to import message_filter
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.message_filter import MessageBus, MessagePriority


def emergency_validate_input(value, field_name="input", validation_type="string"):
    """Emergency input validation function to prevent injection attacks"""
    if validation_type == "string":
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a string")
        if len(value) > 1000:  # Reasonable limit for strings
            raise ValueError(f"{field_name} exceeds maximum length")
        # Check for potential injection patterns
        dangerous_patterns = [';', '&&', '||', '`', '$(',
                             '${', 'eval(', 'exec(', 'system(', 'import']
        for pattern in dangerous_patterns:
            if pattern in value:
                raise ValueError(f"Potentially dangerous pattern in {field_name}")
    elif validation_type == "path":
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a string")
        if len(value) > 260:  # Max path length
            raise ValueError(f"{field_name} exceeds maximum path length")
        if '..' in value or '~' in value:
            raise ValueError(f"Potentially dangerous pattern in {field_name}")
    elif validation_type == "dict":
        if not isinstance(value, dict):
            raise ValueError(f"{field_name} must be a dictionary")
    elif validation_type == "list":
        if not isinstance(value, list):
            raise ValueError(f"{field_name} must be a list")
    return value


class OpportunityType(Enum):
    """Types of arbitrage opportunities"""
    SIMPLE_DEX = "simple_dex"
    TRIANGULAR = "triangular"
    FLASH_LOAN = "flash_loan"
    CROSS_CHAIN = "cross_chain"
    LIQUIDATION = "liquidation"
    MULTI_STEP = "multi_step"
    CUSTOM = "custom"


@dataclass
class OpportunityComponent:
    """Represents a component of an arbitrage opportunity"""
    id: str
    type: str
    source: str
    target: str
    chain_id: int
    token_in: str
    token_out: str
    amount_in: float
    amount_out: float
    dex: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CompositeOpportunity:
    """Represents a composite arbitrage opportunity made up of multiple components"""
    id: str
    components: List[OpportunityComponent]
    type: OpportunityType
    profit_usd: float
    gas_cost_usd: float
    risk_score: float
    execution_plan: List[Dict[str, Any]]
    timestamp: float = field(default_factory=time.time)
    status: str = "pending"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "components": [
                {
                    "id": c.id,
                    "type": c.type,
                    "source": c.source,
                    "target": c.target,
                    "chain_id": c.chain_id,
                    "token_in": c.token_in,
                    "token_out": c.token_out,
                    "amount_in": c.amount_in,
                    "amount_out": c.amount_out,
                    "dex": c.dex,
                    "timestamp": c.timestamp,
                    "metadata": c.metadata
                }
                for c in self.components
            ],
            "type": self.type.value,
            "profit_usd": self.profit_usd,
            "gas_cost_usd": self.gas_cost_usd,
            "risk_score": self.risk_score,
            "execution_plan": self.execution_plan,
            "timestamp": self.timestamp,
            "status": self.status,
            "metadata": self.metadata
        }


class EnhancedParallelOpportunityCoordinator:
    """
    Enhanced Parallel Opportunity Coordinator
    
    This class is responsible for:
    1. Listening to all "partial opportunity" messages from the swarm
    2. Using graph theory and pattern matching to identify profitable multi-step paths
    3. Constructing the final transaction payload
    4. Requesting final risk-approval and execution from the Artemis AI Core
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the coordinator.
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Set up directories
        self._setup_directories()
        
        # Initialize Redis connection
        self._init_redis()
        
        # Initialize Web3 connection
        self._init_web3()
        
        # Initialize message bus
        self._init_message_bus()
        
        # Opportunity graph
        self.opportunity_graph = nx.DiGraph()
        
        # Opportunity storage
        self.opportunities: Dict[str, CompositeOpportunity] = {}
        
        # Execution manager
        self.execution_manager = OpportunityExecutionManager(
            self.web3, self.config
        )
        
        # Statistics
        self.stats = {
            "components_received": 0,
            "opportunities_found": 0,
            "opportunities_executed": 0,
            "opportunities_failed": 0,
            "total_profit_usd": 0.0,
            "start_time": time.time()
        }
        
        # Lock for thread safety
        self.lock = threading.RLock()
        
        # Background threads
        self.cleanup_thread = None
        self.running = False
        
        logger.info("Enhanced Parallel Opportunity Coordinator initialized")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        # Default configuration
        config = {
            "redis": {
                "host": "localhost",
                "port": 6379,
                "db": 0
            },
            "web3": {
                "provider": "http://localhost:8545",
                "chain_id": 1
            },
            "opportunity": {
                "min_profit_usd": 1.0,
                "max_risk_score": 0.7,
                "max_gas_cost_percentage": 0.5,
                "min_components": 2,
                "max_components": 10,
                "max_path_search_depth": 5,
                "opportunity_ttl_seconds": 60,
                "component_ttl_seconds": 300
            },
            "execution": {
                "auto_execute": False,
                "max_concurrent_executions": 3,
                "retry_count": 3,
                "retry_delay_seconds": 2,
                "gas_price_multiplier": 1.1,
                "max_gas_price_gwei": 100
            },
            "channels": {
                "component": "swarm:discoveries",
                "opportunity": "swarm:composite_opportunities",
                "execution": "swarm:opportunity_executions",
                "validation": "artemis:opportunity_validations",
                "command": "coordinator:commands"
            },
            "logging": {
                "level": "INFO",
                "file": "logs/coordinator.log"
            }
        }
        
        # Load from file if provided
        if config_path:
            try:
                emergency_validate_input(config_path, "config_path", "path")
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
                    # Recursively update config
                    self._update_dict(config, file_config)
            except Exception as e:
                logger.error(f"Error loading config from {config_path}: {e}")
        
        return config
    
    def _update_dict(self, d: Dict, u: Dict) -> Dict:
        """Recursively update a dictionary"""
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._update_dict(d[k], v)
            else:
                d[k] = v
        return d
    
    def _setup_directories(self):
        """Set up necessary directories"""
        os.makedirs("logs", exist_ok=True)
        os.makedirs("data", exist_ok=True)
    
    def _init_redis(self):
        """Initialize Redis connection"""
        try:
            redis_config = self.config["redis"]
            self.redis = redis.Redis(
                host=redis_config["host"],
                port=redis_config["port"],
                db=redis_config["db"]
            )
            self.redis.ping()  # Test connection
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error(f"Error connecting to Redis: {e}")
            raise
    
    def _init_web3(self):
        """Initialize Web3 connection"""
        try:
            web3_config = self.config["web3"]
            provider_url = emergency_validate_input(
                web3_config["provider"], "web3_provider", "string"
            )
            self.web3 = Web3(Web3.HTTPProvider(provider_url))
            self.chain_id = web3_config["chain_id"]
            
            if not self.web3.is_connected():
                logger.warning("Web3 provider is not connected")
            else:
                logger.info(f"Connected to Web3 provider, chain ID: {self.chain_id}")
        except Exception as e:
            logger.error(f"Error connecting to Web3: {e}")
            self.web3 = None
    
    def _init_message_bus(self):
        """Initialize message bus for communication"""
        try:
            # Create message bus
            self.message_bus = MessageBus(
                self.redis, 
                config_path="config/message_filter_config.json"
            )
            
            # Subscribe to component channel
            self.component_subscriber = self.message_bus.subscribe(
                "opportunities:*:discovery",
                self._handle_opportunity_component
            )
            
            # Subscribe to agent status channel
            self.status_subscriber = self.message_bus.subscribe(
                "agent:status:*",
                self._handle_agent_status
            )
            
            # Subscribe to validation channel
            self.validation_subscriber = self.message_bus.subscribe(
                "artemis:validation:opportunity",
                self._handle_opportunity_validation
            )
            
            # Subscribe to command channel
            self.command_subscriber = self.message_bus.subscribe(
                "coordinator:commands",
                self._handle_command
            )
            
            logger.info("Message bus initialized")
        except Exception as e:
            logger.error(f"Error initializing message bus: {e}")
            raise
    
    def _handle_opportunity_component(self, message: Dict[str, Any]):
        """
        Handle an opportunity component message.
        
        Args:
            message: The message containing the opportunity component
        """
        try:
            # Validate message
            if not self._validate_component_message(message):
                logger.warning(f"Invalid component message: {message}")
                return
            
            # Extract component data
            component_data = message.get("data", {})
            component_id = component_data.get("id", str(uuid.uuid4()))
            
            # Create component object
            component = OpportunityComponent(
                id=component_id,
                type=component_data.get("type", "unknown"),
                source=component_data.get("source", "unknown"),
                target=component_data.get("target", "unknown"),
                chain_id=component_data.get("chain_id", self.chain_id),
                token_in=component_data.get("token_in", ""),
                token_out=component_data.get("token_out", ""),
                amount_in=float(component_data.get("amount_in", 0)),
                amount_out=float(component_data.get("amount_out", 0)),
                dex=component_data.get("dex", None),
                timestamp=component_data.get("timestamp", time.time()),
                metadata=component_data.get("metadata", {})
            )
            
            # Update opportunity graph
            with self.lock:
                self._update_opportunity_graph(component)
                self.stats["components_received"] += 1
            
            # Find composite opportunities
            self._find_composite_opportunities(component)
            
        except Exception as e:
            logger.error(f"Error handling component message: {e}")
    
    def _validate_component_message(self, message: Dict[str, Any]) -> bool:
        """
        Validate a component message.
        
        Args:
            message: The message to validate
            
        Returns:
            True if the message is valid, False otherwise
        """
        if not isinstance(message, dict):
            return False
        
        if "data" not in message or not isinstance(message["data"], dict):
            return False
        
        data = message["data"]
        required_fields = ["type", "token_in", "token_out", "amount_in", "amount_out"]
        
        for field in required_fields:
            if field not in data:
                return False
        
        # Validate numeric fields
        try:
            float(data["amount_in"])
            float(data["amount_out"])
        except (ValueError, TypeError):
            return False
        
        return True
    
    def _handle_agent_status(self, message: Dict[str, Any]):
        """
        Handle an agent status message.
        
        Args:
            message: The message containing the agent status
        """
        # This method can be expanded to track agent performance
        # and adjust opportunity finding strategies accordingly
        pass
    
    def _handle_opportunity_validation(self, message: Dict[str, Any]):
        """
        Handle an opportunity validation message from Artemis AI Core.
        
        Args:
            message: The validation message
        """
        try:
            data = message.get("data", {})
            opportunity_id = data.get("opportunity_id")
            is_valid = data.get("is_valid", False)
            risk_assessment = data.get("risk_assessment", {})
            
            if not opportunity_id or opportunity_id not in self.opportunities:
                logger.warning(f"Validation for unknown opportunity: {opportunity_id}")
                return
            
            with self.lock:
                opportunity = self.opportunities[opportunity_id]
                
                # Update opportunity with validation results
                opportunity.risk_score = risk_assessment.get("risk_score", opportunity.risk_score)
                opportunity.metadata["validation"] = data
                
                if is_valid:
                    opportunity.status = "validated"
                    logger.info(f"Opportunity {opportunity_id} validated")
                    
                    # Execute if auto-execute is enabled
                    if self.config["execution"]["auto_execute"]:
                        self._execute_opportunity(opportunity_id)
                else:
                    opportunity.status = "rejected"
                    logger.info(f"Opportunity {opportunity_id} rejected: {risk_assessment.get('reason', 'Unknown reason')}")
        
        except Exception as e:
            logger.error(f"Error handling validation message: {e}")
    
    def _handle_command(self, message: Dict[str, Any]):
        """
        Handle a command message.
        
        Args:
            message: The command message
        """
        try:
            command = message.get("command")
            params = message.get("params", {})
            
            if command == "execute_opportunity":
                opportunity_id = params.get("opportunity_id")
                if opportunity_id:
                    self._execute_opportunity(opportunity_id)
            
            elif command == "cancel_opportunity":
                opportunity_id = params.get("opportunity_id")
                if opportunity_id and opportunity_id in self.opportunities:
                    with self.lock:
                        self.opportunities[opportunity_id].status = "cancelled"
                    logger.info(f"Opportunity {opportunity_id} cancelled")
            
            elif command == "get_stats":
                # Publish stats to the response channel
                response_channel = params.get("response_channel")
                if response_channel:
                    stats = self.get_stats()
                    self.message_bus.publish(
                        response_channel,
                        {"stats": stats}
                    )
            
            elif command == "clear_graph":
                with self.lock:
                    self.opportunity_graph.clear()
                logger.info("Opportunity graph cleared")
            
            elif command == "set_config":
                config_updates = params.get("config", {})
                self._update_dict(self.config, config_updates)
                logger.info(f"Configuration updated: {config_updates}")
        
        except Exception as e:
            logger.error(f"Error handling command: {e}")
    
    def _update_opportunity_graph(self, component: OpportunityComponent):
        """
        Update the opportunity graph with a new component.
        
        Args:
            component: The opportunity component to add
        """
        # Create nodes for tokens if they don't exist
        token_in_key = f"{component.chain_id}:{component.token_in}"
        token_out_key = f"{component.chain_id}:{component.token_out}"
        
        if token_in_key not in self.opportunity_graph:
            self.opportunity_graph.add_node(
                token_in_key,
                type="token",
                chain_id=component.chain_id,
                token=component.token_in
            )
        
        if token_out_key not in self.opportunity_graph:
            self.opportunity_graph.add_node(
                token_out_key,
                type="token",
                chain_id=component.chain_id,
                token=component.token_out
            )
        
        # Add edge representing the component
        self.opportunity_graph.add_edge(
            token_in_key,
            token_out_key,
            id=component.id,
            type=component.type,
            source=component.source,
            target=component.target,
            chain_id=component.chain_id,
            amount_in=component.amount_in,
            amount_out=component.amount_out,
            dex=component.dex,
            timestamp=component.timestamp,
            component=component
        )
        
        # Clean up old components
        self._cleanup_old_components()
    
    def _cleanup_old_components(self):
        """Remove old components from the graph"""
        now = time.time()
        ttl = self.config["opportunity"]["component_ttl_seconds"]
        
        edges_to_remove = []
        for u, v, data in self.opportunity_graph.edges(data=True):
            if "timestamp" in data and now - data["timestamp"] > ttl:
                edges_to_remove.append((u, v))
        
        for u, v in edges_to_remove:
            self.opportunity_graph.remove_edge(u, v)
        
        # Remove isolated nodes
        isolated_nodes = list(nx.isolates(self.opportunity_graph))
        self.opportunity_graph.remove_nodes_from(isolated_nodes)
    
    def _can_connect(self, from_component: OpportunityComponent, to_component: OpportunityComponent) -> bool:
        """
        Check if two components can be connected.
        
        Args:
            from_component: The source component
            to_component: The target component
            
        Returns:
            True if the components can be connected, False otherwise
        """
        # Check if the output token of the first component matches the input token of the second
        if from_component.token_out != to_component.token_in:
            return False
        
        # Check if they're on the same chain
        if from_component.chain_id != to_component.chain_id:
            return False
        
        # Check if the output amount of the first is close to the input amount of the second
        # Allow for some slippage
        ratio = from_component.amount_out / to_component.amount_in if to_component.amount_in > 0 else 0
        if not (0.95 <= ratio <= 1.05):
            return False
        
        return True
    
    def _find_composite_opportunities(self, new_component: OpportunityComponent):
        """
        Find composite opportunities involving the new component.
        
        Args:
            new_component: The new component that was added
        """
        with self.lock:
            # Get the token keys
            token_in_key = f"{new_component.chain_id}:{new_component.token_in}"
            token_out_key = f"{new_component.chain_id}:{new_component.token_out}"
            
            # Find cycles that include the new component
            max_depth = self.config["opportunity"]["max_path_search_depth"]
            
            # Look for cycles starting from token_in
            for path in nx.all_simple_paths(
                self.opportunity_graph,
                source=token_in_key,
                target=token_in_key,
                cutoff=max_depth
            ):
                if len(path) >= 3:  # At least 2 edges (components)
                    self._evaluate_path_as_opportunity(path)
            
            # Look for cycles starting from token_out
            for path in nx.all_simple_paths(
                self.opportunity_graph,
                source=token_out_key,
                target=token_out_key,
                cutoff=max_depth
            ):
                if len(path) >= 3:  # At least 2 edges (components)
                    self._evaluate_path_as_opportunity(path)
    
    def _evaluate_path_as_opportunity(self, path: List[str]):
        """
        Evaluate a path as a potential opportunity.
        
        Args:
            path: List of node IDs forming a path
        """
        # Extract components from the path
        components = []
        for i in range(len(path) - 1):
            edge_data = self.opportunity_graph.get_edge_data(path[i], path[i+1])
            if edge_data and "component" in edge_data:
                components.append(edge_data["component"])
        
        # Check if we have enough components
        min_components = self.config["opportunity"]["min_components"]
        max_components = self.config["opportunity"]["max_components"]
        
        if len(components) < min_components or len(components) > max_components:
            return
        
        # Calculate profit
        initial_amount = components[0].amount_in
        final_amount = components[-1].amount_out
        profit_ratio = final_amount / initial_amount if initial_amount > 0 else 0
        
        # Only consider profitable opportunities
        if profit_ratio <= 1.0:
            return
        
        # Estimate profit in USD
        # In a real implementation, this would use price feeds
        profit_usd = (final_amount - initial_amount) * 1.0  # Placeholder
        
        # Check minimum profit threshold
        min_profit_usd = self.config["opportunity"]["min_profit_usd"]
        if profit_usd < min_profit_usd:
            return
        
        # Estimate gas cost
        gas_cost_usd = self._estimate_gas_cost(components)
        
        # Check if gas cost is too high relative to profit
        max_gas_percentage = self.config["opportunity"]["max_gas_cost_percentage"]
        if gas_cost_usd > 0 and gas_cost_usd / profit_usd > max_gas_percentage:
            return
        
        # Create execution plan
        execution_plan = self._create_execution_plan(components)
        
        # Determine opportunity type
        opportunity_type = self._determine_opportunity_type(components)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(components, profit_usd, gas_cost_usd)
        
        # Check risk threshold
        max_risk_score = self.config["opportunity"]["max_risk_score"]
        if risk_score > max_risk_score:
            return
        
        # Create opportunity ID
        opportunity_id = self._generate_opportunity_id(components)
        
        # Check if this opportunity already exists
        if opportunity_id in self.opportunities:
            # Update existing opportunity
            existing = self.opportunities[opportunity_id]
            if profit_usd > existing.profit_usd:
                existing.profit_usd = profit_usd
                existing.gas_cost_usd = gas_cost_usd
                existing.execution_plan = execution_plan
                existing.timestamp = time.time()
                logger.info(f"Updated opportunity {opportunity_id} with higher profit: ${profit_usd:.2f}")
            return
        
        # Create new opportunity
        opportunity = CompositeOpportunity(
            id=opportunity_id,
            components=components,
            type=opportunity_type,
            profit_usd=profit_usd,
            gas_cost_usd=gas_cost_usd,
            risk_score=risk_score,
            execution_plan=execution_plan,
            timestamp=time.time(),
            status="pending",
            metadata={
                "profit_ratio": profit_ratio,
                "initial_amount": initial_amount,
                "final_amount": final_amount,
                "path": path
            }
        )
        
        # Store the opportunity
        self.opportunities[opportunity_id] = opportunity
        
        # Update stats
        self.stats["opportunities_found"] += 1
        
        # Notify about the opportunity
        self._notify_opportunity(opportunity)
        
        logger.info(f"Found new opportunity {opportunity_id} with profit: ${profit_usd:.2f}")
    
    def _generate_opportunity_id(self, components: List[OpportunityComponent]) -> str:
        """
        Generate a unique ID for an opportunity based on its components.
        
        Args:
            components: List of opportunity components
            
        Returns:
            Unique opportunity ID
        """
        # Create a deterministic ID based on the components
        component_ids = [c.id for c in components]
        component_ids.sort()
        
        # Create a hash of the sorted component IDs
        hash_input = ":".join(component_ids)
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def _determine_opportunity_type(self, components: List[OpportunityComponent]) -> OpportunityType:
        """
        Determine the type of opportunity based on its components.
        
        Args:
            components: List of opportunity components
            
        Returns:
            Opportunity type
        """
        # Check for cross-chain components
        chain_ids = set(c.chain_id for c in components)
        if len(chain_ids) > 1:
            return OpportunityType.CROSS_CHAIN
        
        # Check for flash loan components
        if any(c.type == "flash_loan" for c in components):
            return OpportunityType.FLASH_LOAN
        
        # Check for liquidation components
        if any(c.type == "liquidation" for c in components):
            return OpportunityType.LIQUIDATION
        
        # Check for triangular arbitrage
        if len(components) == 3 and components[0].token_in == components[-1].token_out:
            return OpportunityType.TRIANGULAR
        
        # Check for simple DEX arbitrage
        if len(components) == 2 and components[0].token_in == components[-1].token_out:
            return OpportunityType.SIMPLE_DEX
        
        # Default to multi-step
        return OpportunityType.MULTI_STEP
    
    def _calculate_risk_score(self, components: List[OpportunityComponent], 
                             profit_usd: float, gas_cost_usd: float) -> float:
        """
        Calculate a risk score for an opportunity.
        
        Args:
            components: List of opportunity components
            profit_usd: Estimated profit in USD
            gas_cost_usd: Estimated gas cost in USD
            
        Returns:
            Risk score between 0 and 1 (higher is riskier)
        """
        # Base risk factors
        base_risk = 0.3
        
        # Complexity risk - more components = more risk
        complexity_risk = min(0.1 * len(components), 0.3)
        
        # Profit/gas ratio risk - lower ratio = higher risk
        ratio_risk = 0.0
        if profit_usd > 0:
            ratio = gas_cost_usd / profit_usd
            ratio_risk = min(ratio, 0.3)
        
        # Chain risk - some chains are riskier than others
        chain_risk = 0.0
        for component in components:
            # Example: Ethereum is less risky than newer chains
            if component.chain_id == 1:  # Ethereum
                chain_risk += 0.01
            else:
                chain_risk += 0.03
        chain_risk = min(chain_risk, 0.1)
        
        # Total risk score
        risk_score = base_risk + complexity_risk + ratio_risk + chain_risk
        
        # Cap at 1.0
        return min(risk_score, 1.0)
    
    def _estimate_gas_cost(self, components: List[OpportunityComponent]) -> float:
        """
        Estimate the gas cost for executing an opportunity.
        
        Args:
            components: List of opportunity components
            
        Returns:
            Estimated gas cost in USD
        """
        # In a real implementation, this would use gas price feeds and estimates
        # For now, use a simple heuristic
        base_gas = 100000  # Base gas units
        per_component_gas = 50000  # Additional gas per component
        
        total_gas = base_gas + per_component_gas * len(components)
        
        # Assume a gas price of 50 Gwei
        gas_price_gwei = 50
        
        # Assume ETH price of $2000
        eth_price_usd = 2000
        
        # Calculate cost in USD
        gas_cost_eth = total_gas * gas_price_gwei * 1e-9
        gas_cost_usd = gas_cost_eth * eth_price_usd
        
        return gas_cost_usd
    
    def _create_execution_plan(self, components: List[OpportunityComponent]) -> List[Dict[str, Any]]:
        """
        Create an execution plan for an opportunity.
        
        Args:
            components: List of opportunity components
            
        Returns:
            Execution plan as a list of steps
        """
        execution_plan = []
        
        for i, component in enumerate(components):
            step = {
                "step_id": i,
                "type": component.type,
                "chain_id": component.chain_id,
                "token_in": component.token_in,
                "token_out": component.token_out,
                "amount_in": component.amount_in,
                "expected_amount_out": component.amount_out,
                "dex": component.dex
            }
            
            # Add additional parameters based on component type
            if component.type == "flash_loan":
                step["loan_token"] = component.token_in
                step["loan_amount"] = component.amount_in
            
            elif component.type == "swap":
                step["swap_path"] = [component.token_in, component.token_out]
                step["slippage_tolerance"] = 0.005  # 0.5%
            
            # Add component-specific metadata
            if component.metadata:
                for key, value in component.metadata.items():
                    if key not in step and not key.startswith("_"):
                        step[key] = value
            
            execution_plan.append(step)
        
        return execution_plan
    
    def _notify_opportunity(self, opportunity: CompositeOpportunity):
        """
        Notify about a new opportunity.
        
        Args:
            opportunity: The opportunity to notify about
        """
        # Publish to the opportunity channel
        opportunity_channel = "opportunities:composite"
        
        # Add chain-specific subchannel
        chain_ids = set(c.chain_id for c in opportunity.components)
        if len(chain_ids) == 1:
            chain_id = next(iter(chain_ids))
            chain_name = self._get_chain_name(chain_id)
            opportunity_channel = f"opportunities:{chain_name}:composite"
        
        # Publish with high priority for profitable opportunities
        priority = MessagePriority.HIGH if opportunity.profit_usd > 10.0 else MessagePriority.NORMAL
        
        self.message_bus.publish(
            opportunity_channel,
            {
                "type": "composite_opportunity",
                "data": opportunity.to_dict()
            },
            priority=priority
        )
        
        # Also publish to Artemis for validation
        self.message_bus.publish(
            "artemis:validation:request",
            {
                "type": "opportunity_validation",
                "data": {
                    "opportunity_id": opportunity.id,
                    "opportunity": opportunity.to_dict()
                }
            },
            priority=priority
        )
    
    def _get_chain_name(self, chain_id: int) -> str:
        """
        Get the name of a chain from its ID.
        
        Args:
            chain_id: Chain ID
            
        Returns:
            Chain name
        """
        chain_names = {
            1: "ethereum",
            56: "bsc",
            137: "polygon",
            42161: "arbitrum",
            10: "optimism",
            43114: "avalanche"
        }
        return chain_names.get(chain_id, f"chain{chain_id}")
    
    def _should_execute(self, opportunity: CompositeOpportunity) -> bool:
        """
        Determine if an opportunity should be executed.
        
        Args:
            opportunity: The opportunity to check
            
        Returns:
            True if the opportunity should be executed, False otherwise
        """
        # Check if auto-execute is enabled
        if not self.config["execution"]["auto_execute"]:
            return False
        
        # Check opportunity status
        if opportunity.status != "validated":
            return False
        
        # Check risk score
        if opportunity.risk_score > self.config["opportunity"]["max_risk_score"]:
            return False
        
        # Check profit vs gas cost
        if opportunity.gas_cost_usd > 0:
            ratio = opportunity.gas_cost_usd / opportunity.profit_usd
            if ratio > self.config["opportunity"]["max_gas_cost_percentage"]:
                return False
        
        # Check if we're already executing too many opportunities
        executing_count = sum(1 for opp in self.opportunities.values() 
                             if opp.status == "executing")
        
        if executing_count >= self.config["execution"]["max_concurrent_executions"]:
            return False
        
        return True
    
    def _execute_opportunity(self, opportunity_id: str):
        """
        Execute an opportunity.
        
        Args:
            opportunity_id: ID of the opportunity to execute
        """
        with self.lock:
            if opportunity_id not in self.opportunities:
                logger.warning(f"Cannot execute unknown opportunity: {opportunity_id}")
                return
            
            opportunity = self.opportunities[opportunity_id]
            
            # Check if we should execute
            if not self._should_execute(opportunity):
                logger.info(f"Skipping execution of opportunity {opportunity_id}")
                return
            
            # Update status
            opportunity.status = "executing"
        
        # Execute in a separate thread
        threading.Thread(
            target=self._execute_opportunity_thread,
            args=(opportunity_id,),
            daemon=True
        ).start()
    
    def _execute_opportunity_thread(self, opportunity_id: str):
        """
        Thread function for executing an opportunity.
        
        Args:
            opportunity_id: ID of the opportunity to execute
        """
        try:
            with self.lock:
                if opportunity_id not in self.opportunities:
                    return
                
                opportunity = self.opportunities[opportunity_id]
            
            # Execute the opportunity
            result = self.execution_manager.execute_opportunity(opportunity)
            
            # Update opportunity with result
            with self.lock:
                if opportunity_id in self.opportunities:
                    opportunity = self.opportunities[opportunity_id]
                    opportunity.status = result["status"]
                    opportunity.metadata["execution_result"] = result
                    
                    # Update stats
                    if result["status"] == "executed":
                        self.stats["opportunities_executed"] += 1
                        self.stats["total_profit_usd"] += opportunity.profit_usd
                    elif result["status"] == "failed":
                        self.stats["opportunities_failed"] += 1
            
            # Publish execution result
            self.message_bus.publish(
                "swarm:opportunity_executions",
                {
                    "type": "opportunity_execution",
                    "data": {
                        "opportunity_id": opportunity_id,
                        "result": result
                    }
                }
            )
            
            logger.info(f"Executed opportunity {opportunity_id} with result: {result['status']}")
        
        except Exception as e:
            logger.error(f"Error executing opportunity {opportunity_id}: {e}")
            
            # Update opportunity status
            with self.lock:
                if opportunity_id in self.opportunities:
                    self.opportunities[opportunity_id].status = "failed"
                    self.opportunities[opportunity_id].metadata["execution_error"] = str(e)
                    self.stats["opportunities_failed"] += 1
    
    def get_opportunity(self, opportunity_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details of an opportunity.
        
        Args:
            opportunity_id: ID of the opportunity
            
        Returns:
            Opportunity details or None if not found
        """
        with self.lock:
            if opportunity_id in self.opportunities:
                return self.opportunities[opportunity_id].to_dict()
            return None
    
    def get_all_opportunities(self, 
                             status: Optional[str] = None,
                             chain_id: Optional[int] = None,
                             min_profit: Optional[float] = None,
                             max_risk: Optional[float] = None,
                             limit: int = 100,
                             offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get all opportunities matching the filters.
        
        Args:
            status: Filter by status
            chain_id: Filter by chain ID
            min_profit: Minimum profit in USD
            max_risk: Maximum risk score
            limit: Maximum number of opportunities to return
            offset: Offset for pagination
            
        Returns:
            List of opportunities
        """
        with self.lock:
            opportunities = list(self.opportunities.values())
            
            # Apply filters
            if status:
                opportunities = [o for o in opportunities if o.status == status]
            
            if chain_id:
                opportunities = [o for o in opportunities if any(c.chain_id == chain_id for c in o.components)]
            
            if min_profit is not None:
                opportunities = [o for o in opportunities if o.profit_usd >= min_profit]
            
            if max_risk is not None:
                opportunities = [o for o in opportunities if o.risk_score <= max_risk]
            
            # Sort by profit (descending)
            opportunities.sort(key=lambda o: o.profit_usd, reverse=True)
            
            # Apply pagination
            opportunities = opportunities[offset:offset+limit]
            
            # Convert to dictionaries
            return [o.to_dict() for o in opportunities]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the coordinator.
        
        Returns:
            Statistics dictionary
        """
        with self.lock:
            # Calculate additional stats
            uptime = time.time() - self.stats["start_time"]
            
            # Count opportunities by status
            status_counts = {}
            for opportunity in self.opportunities.values():
                status = opportunity.status
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Count opportunities by type
            type_counts = {}
            for opportunity in self.opportunities.values():
                type_name = opportunity.type.value
                type_counts[type_name] = type_counts.get(type_name, 0) + 1
            
            # Count opportunities by chain
            chain_counts = {}
            for opportunity in self.opportunities.values():
                chain_ids = set(c.chain_id for c in opportunity.components)
                for chain_id in chain_ids:
                    chain_name = self._get_chain_name(chain_id)
                    chain_counts[chain_name] = chain_counts.get(chain_name, 0) + 1
            
            # Calculate success rate
            total_executed = self.stats["opportunities_executed"] + self.stats["opportunities_failed"]
            success_rate = self.stats["opportunities_executed"] / total_executed if total_executed > 0 else 0
            
            return {
                **self.stats,
                "uptime_seconds": uptime,
                "opportunities_by_status": status_counts,
                "opportunities_by_type": type_counts,
                "opportunities_by_chain": chain_counts,
                "success_rate": success_rate,
                "active_opportunities": len(self.opportunities),
                "graph_nodes": self.opportunity_graph.number_of_nodes(),
                "graph_edges": self.opportunity_graph.number_of_edges()
            }
    
    def cleanup_expired(self):
        """Clean up expired opportunities"""
        with self.lock:
            now = time.time()
            ttl = self.config["opportunity"]["opportunity_ttl_seconds"]
            
            expired_ids = []
            for opportunity_id, opportunity in self.opportunities.items():
                if now - opportunity.timestamp > ttl and opportunity.status not in ["executing", "executed"]:
                    expired_ids.append(opportunity_id)
            
            for opportunity_id in expired_ids:
                del self.opportunities[opportunity_id]
            
            if expired_ids:
                logger.info(f"Cleaned up {len(expired_ids)} expired opportunities")
    
    def _cleanup_loop(self):
        """Background thread for cleanup tasks"""
        while self.running:
            try:
                self.cleanup_expired()
                self._cleanup_old_components()
                time.sleep(10)
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                time.sleep(1)
    
    def run(self):
        """Run the coordinator"""
        self.running = True
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True
        )
        self.cleanup_thread.start()
        
        logger.info("Enhanced Parallel Opportunity Coordinator is running")
        
        try:
            # Keep the main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            self.running = False
            
            # Shutdown message bus
            self.message_bus.shutdown()
    
    def shutdown(self):
        """Shutdown the coordinator"""
        self.running = False
        
        # Shutdown message bus
        self.message_bus.shutdown()
        
        logger.info("Enhanced Parallel Opportunity Coordinator shut down")


class OpportunityExecutionManager:
    """
    Manages the execution of arbitrage opportunities.
    """
    
    def __init__(self, web3: Web3, config: Dict[str, Any]):
        """
        Initialize the execution manager.
        
        Args:
            web3: Web3 instance
            config: Configuration dictionary
        """
        self.web3 = web3
        self.config = config
        
        # In a real implementation, this would load contract ABIs, etc.
        logger.info("Opportunity Execution Manager initialized")
    
    def execute_opportunity(self, opportunity: CompositeOpportunity) -> Dict[str, Any]:
        """
        Execute an arbitrage opportunity.
        
        Args:
            opportunity: The opportunity to execute
            
        Returns:
            Execution result
        """
        logger.info(f"Executing opportunity {opportunity.id}")
        
        # In a real implementation, this would:
        # 1. Prepare the transaction(s)
        # 2. Sign and send the transaction(s)
        # 3. Monitor for confirmation
        # 4. Handle any errors
        
        # For this example, we'll simulate execution
        execution_result = {
            "opportunity_id": opportunity.id,
            "status": "executed",
            "timestamp": time.time(),
            "transactions": [],
            "actual_profit_usd": opportunity.profit_usd * 0.95,  # Slightly less than expected
            "gas_used": 0,
            "gas_cost_usd": opportunity.gas_cost_usd
        }
        
        # Simulate execution of each step
        for i, step in enumerate(opportunity.execution_plan):
            try:
                step_result = self._execute_step(step, opportunity)
                execution_result["transactions"].append(step_result)
                
                # If any step fails, the whole execution fails
                if step_result["status"] != "success":
                    execution_result["status"] = "failed"
                    execution_result["error"] = step_result["error"]
                    break
                
                # Add gas used
                execution_result["gas_used"] += step_result.get("gas_used", 0)
            
            except Exception as e:
                logger.error(f"Error executing step {i}: {e}")
                execution_result["status"] = "failed"
                execution_result["error"] = str(e)
                break
        
        # In a real implementation, we would calculate the actual profit here
        
        logger.info(f"Opportunity {opportunity.id} execution result: {execution_result['status']}")
        return execution_result
    
    def _execute_step(self, step: Dict[str, Any], opportunity: CompositeOpportunity) -> Dict[str, Any]:
        """
        Execute a single step of an opportunity.
        
        Args:
            step: The step to execute
            opportunity: The parent opportunity
            
        Returns:
            Step execution result
        """
        # In a real implementation, this would execute the actual transaction
        # For this example, we'll simulate execution with a 95% success rate
        
        # Simulate random success/failure
        if np.random.random() < 0.95:
            # Success
            return {
                "step_id": step["step_id"],
                "status": "success",
                "tx_hash": f"0x{uuid.uuid4().hex}",
                "gas_used": 150000 + np.random.randint(0, 100000),
                "block_number": 12345678,
                "timestamp": time.time(),
                "amount_in": step["amount_in"],
                "amount_out": step["expected_amount_out"] * (0.98 + 0.04 * np.random.random())  # Slight variation
            }
        else:
            # Failure
            return {
                "step_id": step["step_id"],
                "status": "failed",
                "error": "Transaction reverted",
                "timestamp": time.time()
            }


def main():
    """Main entry point"""
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Enhanced Parallel Opportunity Coordinator")
    parser.add_argument("--config", help="Path to configuration file")
    args = parser.parse_args()
    
    # Create and run coordinator
    coordinator = EnhancedParallelOpportunityCoordinator(args.config)
    coordinator.run()


if __name__ == "__main__":
    main()