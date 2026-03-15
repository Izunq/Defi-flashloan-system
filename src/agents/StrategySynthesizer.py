import os
import json
import time
import logging
import numpy as np
import pandas as pd
import tensorflow as tf
from typing import Dict, List, Tuple, Any, Optional, Union
from pathlib import Path
import yaml
import random
from datetime import datetime
import hashlib
import uuid
import copy
from tqdm import tqdm
import multiprocessing as mp
from WorldModelSimulator import WorldModelSimulator, DeFiEnvironment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("strategy_synthesizer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("StrategySynthesizer")

class StrategyPrimitive:
    """
    A basic building block for DeFi strategies.
    Each primitive represents a single action or condition that can be combined
    to create complex strategies.
    """
    
    def __init__(self, name: str, primitive_type: str, params: Dict = None):
        """
        Initialize a strategy primitive
        
        Args:
            name: Name of the primitive
            primitive_type: Type of primitive (action, condition, etc.)
            params: Parameters for the primitive
        """
        self.name = name
        self.primitive_type = primitive_type
        self.params = params or {}
        self.id = str(uuid.uuid4())[:8]  # Short unique ID
    
    def to_dict(self) -> Dict:
        """
        Convert primitive to dictionary
        
        Returns:
            Dict representation of the primitive
        """
        return {
            "id": self.id,
            "name": self.name,
            "type": self.primitive_type,
            "params": self.params
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StrategyPrimitive':
        """
        Create primitive from dictionary
        
        Args:
            data: Dict representation of the primitive
            
        Returns:
            StrategyPrimitive instance
        """
        primitive = cls(
            name=data.get("name", ""),
            primitive_type=data.get("type", ""),
            params=data.get("params", {})
        )
        primitive.id = data.get("id", primitive.id)
        return primitive
    
    def __str__(self) -> str:
        return f"{self.name} ({self.primitive_type})"

class StrategyNode:
    """
    A node in a strategy graph.
    Each node contains a primitive and connections to other nodes.
    """
    
    def __init__(self, primitive: StrategyPrimitive):
        """
        Initialize a strategy node
        
        Args:
            primitive: The primitive contained in this node
        """
        self.primitive = primitive
        self.next_nodes = []
        self.condition_nodes = []
        self.id = primitive.id
    
    def add_next_node(self, node: 'StrategyNode'):
        """
        Add a node to execute after this one
        
        Args:
            node: Node to add
        """
        if node not in self.next_nodes:
            self.next_nodes.append(node)
    
    def add_condition_node(self, node: 'StrategyNode'):
        """
        Add a condition node that determines whether this node executes
        
        Args:
            node: Condition node to add
        """
        if node not in self.condition_nodes:
            self.condition_nodes.append(node)
    
    def to_dict(self) -> Dict:
        """
        Convert node to dictionary
        
        Returns:
            Dict representation of the node
        """
        return {
            "id": self.id,
            "primitive": self.primitive.to_dict(),
            "next_nodes": [node.id for node in self.next_nodes],
            "condition_nodes": [node.id for node in self.condition_nodes]
        }
    
    @classmethod
    def from_dict(cls, data: Dict, node_map: Dict[str, 'StrategyNode'] = None) -> 'StrategyNode':
        """
        Create node from dictionary
        
        Args:
            data: Dict representation of the node
            node_map: Map of node IDs to nodes
            
        Returns:
            StrategyNode instance
        """
        primitive = StrategyPrimitive.from_dict(data.get("primitive", {}))
        node = cls(primitive)
        
        if node_map is not None:
            node_map[node.id] = node
        
        return node
    
    def __str__(self) -> str:
        return f"Node({self.primitive})"

class StrategyGraph:
    """
    A graph representation of a DeFi strategy.
    The graph consists of nodes connected by edges, where each node contains a primitive.
    """
    
    def __init__(self, name: str = None):
        """
        Initialize a strategy graph
        
        Args:
            name: Name of the strategy
        """
        self.name = name or f"Strategy-{int(time.time())}"
        self.nodes = {}  # Map of node IDs to nodes
        self.entry_nodes = []  # Nodes that start the strategy
        self.exit_nodes = []   # Nodes that end the strategy
    
    def add_node(self, node: StrategyNode) -> StrategyNode:
        """
        Add a node to the graph
        
        Args:
            node: Node to add
            
        Returns:
            The added node
        """
        self.nodes[node.id] = node
        return node
    
    def add_edge(self, from_node: StrategyNode, to_node: StrategyNode):
        """
        Add an edge between nodes
        
        Args:
            from_node: Source node
            to_node: Target node
        """
        from_node.add_next_node(to_node)
    
    def add_condition(self, condition_node: StrategyNode, target_node: StrategyNode):
        """
        Add a condition to a node
        
        Args:
            condition_node: Condition node
            target_node: Node that depends on the condition
        """
        target_node.add_condition_node(condition_node)
    
    def set_entry_node(self, node: StrategyNode):
        """
        Set a node as an entry point to the strategy
        
        Args:
            node: Entry node
        """
        if node not in self.entry_nodes:
            self.entry_nodes.append(node)
    
    def set_exit_node(self, node: StrategyNode):
        """
        Set a node as an exit point from the strategy
        
        Args:
            node: Exit node
        """
        if node not in self.exit_nodes:
            self.exit_nodes.append(node)
    
    def to_dict(self) -> Dict:
        """
        Convert graph to dictionary
        
        Returns:
            Dict representation of the graph
        """
        return {
            "name": self.name,
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "entry_nodes": [node.id for node in self.entry_nodes],
            "exit_nodes": [node.id for node in self.exit_nodes]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StrategyGraph':
        """
        Create graph from dictionary
        
        Args:
            data: Dict representation of the graph
            
        Returns:
            StrategyGraph instance
        """
        graph = cls(name=data.get("name", ""))
        
        # First pass: create all nodes
        node_data_map = {}
        for node_data in data.get("nodes", []):
            node_id = node_data.get("id", "")
            node_data_map[node_id] = node_data
            node = StrategyNode.from_dict(node_data, graph.nodes)
            graph.add_node(node)
        
        # Second pass: connect nodes
        for node_id, node_data in node_data_map.items():
            node = graph.nodes[node_id]
            
            # Connect next nodes
            for next_id in node_data.get("next_nodes", []):
                if next_id in graph.nodes:
                    node.add_next_node(graph.nodes[next_id])
            
            # Connect condition nodes
            for cond_id in node_data.get("condition_nodes", []):
                if cond_id in graph.nodes:
                    node.add_condition_node(graph.nodes[cond_id])
        
        # Set entry and exit nodes
        for entry_id in data.get("entry_nodes", []):
            if entry_id in graph.nodes:
                graph.set_entry_node(graph.nodes[entry_id])
        
        for exit_id in data.get("exit_nodes", []):
            if exit_id in graph.nodes:
                graph.set_exit_node(graph.nodes[exit_id])
        
        return graph
    
    def validate(self) -> bool:
        """
        Validate the graph structure
        
        Returns:
            Whether the graph is valid
        """
        # Check if there are entry nodes
        if not self.entry_nodes:
            logger.warning("No entry nodes in the graph")
            return False
        
        # Check if there are cycles
        visited = set()
        path = set()
        
        def has_cycle(node):
            if node.id in path:
                return True
            if node.id in visited:
                return False
            
            visited.add(node.id)
            path.add(node.id)
            
            for next_node in node.next_nodes:
                if has_cycle(next_node):
                    return True
            
            path.remove(node.id)
            return False
        
        for entry_node in self.entry_nodes:
            if has_cycle(entry_node):
                logger.warning("Cycle detected in the graph")
                return False
        
        return True
    
    def __str__(self) -> str:
        return f"StrategyGraph({self.name}, {len(self.nodes)} nodes)"

class StrategyExecutor:
    """
    Executes a strategy graph in a DeFi environment.
    """
    
    def __init__(self, strategy: StrategyGraph, env: DeFiEnvironment):
        """
        Initialize a strategy executor
        
        Args:
            strategy: Strategy graph to execute
            env: DeFi environment to execute in
        """
        self.strategy = strategy
        self.env = env
        self.current_nodes = []
        self.executed_nodes = set()
        self.node_results = {}
    
    def reset(self):
        """Reset the executor state"""
        self.current_nodes = list(self.strategy.entry_nodes)
        self.executed_nodes = set()
        self.node_results = {}
    
    def step(self, observation) -> Dict:
        """
        Execute one step of the strategy
        
        Args:
            observation: Current environment observation
            
        Returns:
            Action to take in the environment
        """
        # If no current nodes, start from entry nodes
        if not self.current_nodes:
            self.current_nodes = list(self.strategy.entry_nodes)
        
        # Find the next executable node
        next_node = self._find_next_executable_node(observation)
        
        if next_node:
            # Execute the node
            result = self._execute_node(next_node, observation)
            self.node_results[next_node.id] = result
            self.executed_nodes.add(next_node.id)
            
            # Add next nodes to current nodes
            for node in next_node.next_nodes:
                if node.id not in self.executed_nodes and node not in self.current_nodes:
                    self.current_nodes.append(node)
            
            # Remove executed node from current nodes
            if next_node in self.current_nodes:
                self.current_nodes.remove(next_node)
            
            # Return action if this was an action node
            if next_node.primitive.primitive_type == "action":
                return result.get("action", {})
        
        # Default action (do nothing)
        return {
            "protocol": 0,
            "action_type": 0,
            "asset1": 0,
            "asset2": 0,
            "amount_percentage": 0.0
        }
    
    def _find_next_executable_node(self, observation) -> Optional[StrategyNode]:
        """
        Find the next node that can be executed
        
        Args:
            observation: Current environment observation
            
        Returns:
            Next executable node, or None if none found
        """
        for node in self.current_nodes:
            # Skip already executed nodes
            if node.id in self.executed_nodes:
                continue
            
            # Check if all conditions are met
            conditions_met = True
            for condition_node in node.condition_nodes:
                # If condition node hasn't been executed yet, execute it
                if condition_node.id not in self.node_results:
                    condition_result = self._execute_node(condition_node, observation)
                    self.node_results[condition_node.id] = condition_result
                    self.executed_nodes.add(condition_node.id)
                
                # Check if condition is met
                condition_result = self.node_results[condition_node.id]
                if not condition_result.get("result", False):
                    conditions_met = False
                    break
            
            if conditions_met:
                return node
        
        return None
    
    def _execute_node(self, node: StrategyNode, observation) -> Dict:
        """
        Execute a node
        
        Args:
            node: Node to execute
            observation: Current environment observation
            
        Returns:
            Result of the execution
        """
        primitive = node.primitive
        
        if primitive.primitive_type == "condition":
            return self._execute_condition(primitive, observation)
        elif primitive.primitive_type == "action":
            return self._execute_action(primitive, observation)
        else:
            logger.warning(f"Unknown primitive type: {primitive.primitive_type}")
            return {"result": False}
    
    def _execute_condition(self, primitive: StrategyPrimitive, observation) -> Dict:
        """
        Execute a condition primitive
        
        Args:
            primitive: Condition primitive to execute
            observation: Current environment observation
            
        Returns:
            Result of the condition
        """
        condition_type = primitive.name
        params = primitive.params
        
        if condition_type == "price_above":
            asset = params.get("asset", "eth")
            threshold = params.get("threshold", 0)
            asset_idx = self.env.assets.index(asset) if asset in self.env.assets else 0
            price = observation["prices"][asset_idx]
            result = price > threshold
            return {"result": result, "price": price, "threshold": threshold}
        
        elif condition_type == "price_below":
            asset = params.get("asset", "eth")
            threshold = params.get("threshold", 0)
            asset_idx = self.env.assets.index(asset) if asset in self.env.assets else 0
            price = observation["prices"][asset_idx]
            result = price < threshold
            return {"result": result, "price": price, "threshold": threshold}
        
        elif condition_type == "price_change_above":
            asset = params.get("asset", "eth")
            threshold = params.get("threshold", 0)
            asset_idx = self.env.assets.index(asset) if asset in self.env.assets else 0
            price_change = observation["price_changes_24h"][asset_idx]
            result = price_change > threshold
            return {"result": result, "price_change": price_change, "threshold": threshold}
        
        elif condition_type == "price_change_below":
            asset = params.get("asset", "eth")
            threshold = params.get("threshold", 0)
            asset_idx = self.env.assets.index(asset) if asset in self.env.assets else 0
            price_change = observation["price_changes_24h"][asset_idx]
            result = price_change < threshold
            return {"result": result, "price_change": price_change, "threshold": threshold}
        
        elif condition_type == "gas_price_below":
            threshold = params.get("threshold", 100)
            gas_price = observation["gas_price"][0]
            result = gas_price < threshold
            return {"result": result, "gas_price": gas_price, "threshold": threshold}
        
        elif condition_type == "supply_apy_above":
            protocol = params.get("protocol", "aave_v3")
            asset = params.get("asset", "usdc")
            threshold = params.get("threshold", 0)
            protocol_idx = self.env.protocols.index(protocol) if protocol in self.env.protocols else 0
            asset_idx = self.env.assets.index(asset) if asset in self.env.assets else 0
            apy = observation["supply_apy"][protocol_idx, asset_idx]
            result = apy > threshold
            return {"result": result, "apy": apy, "threshold": threshold}
        
        elif condition_type == "has_balance":
            asset = params.get("asset", "eth")
            min_balance = params.get("min_balance", 0)
            asset_idx = self.env.assets.index(asset) if asset in self.env.assets else 0
            balance = observation["wallet_balances"][asset_idx]
            result = balance >= min_balance
            return {"result": result, "balance": balance, "min_balance": min_balance}
        
        elif condition_type == "portfolio_value_above":
            threshold = params.get("threshold", 0)
            portfolio_value = self.env.calculate_portfolio_value()
            result = portfolio_value > threshold
            return {"result": result, "portfolio_value": portfolio_value, "threshold": threshold}
        
        elif condition_type == "always":
            return {"result": True}
        
        else:
            logger.warning(f"Unknown condition type: {condition_type}")
            return {"result": False}
    
    def _execute_action(self, primitive: StrategyPrimitive, observation) -> Dict:
        """
        Execute an action primitive
        
        Args:
            primitive: Action primitive to execute
            observation: Current environment observation
            
        Returns:
            Action to take in the environment
        """
        action_type = primitive.name
        params = primitive.params
        
        if action_type == "swap":
            protocol = params.get("protocol", "uniswap_v3")
            asset_from = params.get("asset_from", "eth")
            asset_to = params.get("asset_to", "usdc")
            amount_percentage = params.get("amount_percentage", 0.5)
            
            protocol_idx = self.env.protocols.index(protocol) if protocol in self.env.protocols else 0
            asset_from_idx = self.env.assets.index(asset_from) if asset_from in self.env.assets else 0
            asset_to_idx = self.env.assets.index(asset_to) if asset_to in self.env.assets else 0
            
            return {
                "action": {
                    "protocol": protocol_idx,
                    "action_type": 0,  # swap
                    "asset1": asset_from_idx,
                    "asset2": asset_to_idx,
                    "amount_percentage": amount_percentage
                }
            }
        
        elif action_type == "deposit":
            protocol = params.get("protocol", "aave_v3")
            asset = params.get("asset", "eth")
            amount_percentage = params.get("amount_percentage", 0.5)
            
            protocol_idx = self.env.protocols.index(protocol) if protocol in self.env.protocols else 0
            asset_idx = self.env.assets.index(asset) if asset in self.env.assets else 0
            
            return {
                "action": {
                    "protocol": protocol_idx,
                    "action_type": 1,  # deposit
                    "asset1": asset_idx,
                    "asset2": 0,  # not used
                    "amount_percentage": amount_percentage
                }
            }
        
        elif action_type == "withdraw":
            protocol = params.get("protocol", "aave_v3")
            asset = params.get("asset", "eth")
            amount_percentage = params.get("amount_percentage", 0.5)
            
            protocol_idx = self.env.protocols.index(protocol) if protocol in self.env.protocols else 0
            asset_idx = self.env.assets.index(asset) if asset in self.env.assets else 0
            
            return {
                "action": {
                    "protocol": protocol_idx,
                    "action_type": 2,  # withdraw
                    "asset1": asset_idx,
                    "asset2": 0,  # not used
                    "amount_percentage": amount_percentage
                }
            }
        
        elif action_type == "borrow":
            protocol = params.get("protocol", "aave_v3")
            asset = params.get("asset", "usdc")
            amount_percentage = params.get("amount_percentage", 0.5)
            
            protocol_idx = self.env.protocols.index(protocol) if protocol in self.env.protocols else 0
            asset_idx = self.env.assets.index(asset) if asset in self.env.assets else 0
            
            return {
                "action": {
                    "protocol": protocol_idx,
                    "action_type": 3,  # borrow
                    "asset1": asset_idx,
                    "asset2": 0,  # not used
                    "amount_percentage": amount_percentage
                }
            }
        
        elif action_type == "repay":
            protocol = params.get("protocol", "aave_v3")
            asset = params.get("asset", "usdc")
            amount_percentage = params.get("amount_percentage", 0.5)
            
            protocol_idx = self.env.protocols.index(protocol) if protocol in self.env.protocols else 0
            asset_idx = self.env.assets.index(asset) if asset in self.env.assets else 0
            
            return {
                "action": {
                    "protocol": protocol_idx,
                    "action_type": 4,  # repay
                    "asset1": asset_idx,
                    "asset2": 0,  # not used
                    "amount_percentage": amount_percentage
                }
            }
        
        elif action_type == "do_nothing":
            return {
                "action": {
                    "protocol": 0,
                    "action_type": 0,
                    "asset1": 0,
                    "asset2": 0,
                    "amount_percentage": 0.0
                }
            }
        
        else:
            logger.warning(f"Unknown action type: {action_type}")
            return {
                "action": {
                    "protocol": 0,
                    "action_type": 0,
                    "asset1": 0,
                    "asset2": 0,
                    "amount_percentage": 0.0
                }
            }
    
    def get_action(self, observation):
        """
        Get the next action to take
        
        Args:
            observation: Current environment observation
            
        Returns:
            Action to take in the environment
        """
        return self.step(observation)

class StrategySynthesizer:
    """
    AI agent that synthesizes new DeFi strategies from primitives.
    Uses a combination of genetic algorithms and large language models.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the Strategy Synthesizer
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path or "strategy_synthesizer_config.yaml"
        self._load_config(self.config_path)
        self._setup_directories()
        self._init_primitives()
        self._init_simulator()
        
        logger.info(f"Strategy Synthesizer initialized")
    
    def _load_config(self, config_path: str) -> Dict:
        """
        Load configuration from YAML file
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Dict containing configuration
        """
        try:
            with open(config_path, 'r') as file:
                self.config = yaml.safe_load(file)
                logger.info(f"Configuration loaded from {config_path}")
                return self.config
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            # Default configuration
            self.config = {
                "primitives": {
                    "conditions": [
                        {"name": "price_above", "params": ["asset", "threshold"]},
                        {"name": "price_below", "params": ["asset", "threshold"]},
                        {"name": "price_change_above", "params": ["asset", "threshold"]},
                        {"name": "price_change_below", "params": ["asset", "threshold"]},
                        {"name": "gas_price_below", "params": ["threshold"]},
                        {"name": "supply_apy_above", "params": ["protocol", "asset", "threshold"]},
                        {"name": "has_balance", "params": ["asset", "min_balance"]},
                        {"name": "portfolio_value_above", "params": ["threshold"]},
                        {"name": "always", "params": []}
                    ],
                    "actions": [
                        {"name": "swap", "params": ["protocol", "asset_from", "asset_to", "amount_percentage"]},
                        {"name": "deposit", "params": ["protocol", "asset", "amount_percentage"]},
                        {"name": "withdraw", "params": ["protocol", "asset", "amount_percentage"]},
                        {"name": "borrow", "params": ["protocol", "asset", "amount_percentage"]},
                        {"name": "repay", "params": ["protocol", "asset", "amount_percentage"]},
                        {"name": "do_nothing", "params": []}
                    ]
                },
                "genetic_algorithm": {
                    "population_size": 50,
                    "generations": 20,
                    "mutation_rate": 0.2,
                    "crossover_rate": 0.7,
                    "elitism_count": 5
                },
                "simulation": {
                    "num_episodes": 10,
                    "max_steps": 1000
                },
                "strategy_constraints": {
                    "min_nodes": 3,
                    "max_nodes": 20,
                    "min_conditions": 1,
                    "max_conditions": 10,
                    "min_actions": 1,
                    "max_actions": 10
                },
                "data_dir": "data/strategy_synthesizer",
                "results_dir": "results/strategy_synthesizer"
            }
            return self.config
    
    def _setup_directories(self):
        """Create necessary directories for data storage"""
        os.makedirs(self.config.get("data_dir", "data/strategy_synthesizer"), exist_ok=True)
        os.makedirs(self.config.get("results_dir", "results/strategy_synthesizer"), exist_ok=True)
    
    def _init_primitives(self):
        """Initialize strategy primitives"""
        self.condition_primitives = []
        self.action_primitives = []
        
        # Load condition primitives
        for condition in self.config.get("primitives", {}).get("conditions", []):
            primitive = StrategyPrimitive(
                name=condition.get("name", ""),
                primitive_type="condition",
                params={}
            )
            self.condition_primitives.append(primitive)
        
        # Load action primitives
        for action in self.config.get("primitives", {}).get("actions", []):
            primitive = StrategyPrimitive(
                name=action.get("name", ""),
                primitive_type="action",
                params={}
            )
            self.action_primitives.append(primitive)
        
        logger.info(f"Initialized {len(self.condition_primitives)} condition primitives and {len(self.action_primitives)} action primitives")
    
    def _init_simulator(self):
        """Initialize the World Model Simulator"""
        self.simulator = WorldModelSimulator()
        logger.info("Initialized World Model Simulator")
    
    def generate_random_strategy(self, name: str = None) -> StrategyGraph:
        """
        Generate a random strategy
        
        Args:
            name: Name for the strategy
            
        Returns:
            Randomly generated strategy graph
        """
        if name is None:
            name = f"RandomStrategy-{int(time.time())}"
        
        graph = StrategyGraph(name=name)
        
        # Get constraints
        constraints = self.config.get("strategy_constraints", {})
        min_nodes = constraints.get("min_nodes", 3)
        max_nodes = constraints.get("max_nodes", 20)
        min_conditions = constraints.get("min_conditions", 1)
        max_conditions = constraints.get("max_conditions", 10)
        min_actions = constraints.get("min_actions", 1)
        max_actions = constraints.get("max_actions", 10)
        
        # Determine number of nodes
        num_nodes = random.randint(min_nodes, max_nodes)
        num_conditions = random.randint(min_conditions, min(max_conditions, num_nodes // 2))
        num_actions = num_nodes - num_conditions
        
        # Create condition nodes
        condition_nodes = []
        for _ in range(num_conditions):
            primitive = copy.deepcopy(random.choice(self.condition_primitives))
            self._randomize_primitive_params(primitive)
            node = StrategyNode(primitive)
            graph.add_node(node)
            condition_nodes.append(node)
        
        # Create action nodes
        action_nodes = []
        for _ in range(num_actions):
            primitive = copy.deepcopy(random.choice(self.action_primitives))
            self._randomize_primitive_params(primitive)
            node = StrategyNode(primitive)
            graph.add_node(node)
            action_nodes.append(node)
        
        # Connect nodes
        # First, create a linear chain of action nodes
        for i in range(len(action_nodes) - 1):
            graph.add_edge(action_nodes[i], action_nodes[i + 1])
        
        # Add entry node
        graph.set_entry_node(action_nodes[0])
        
        # Add exit node
        graph.set_exit_node(action_nodes[-1])
        
        # Add conditions to random action nodes
        for condition_node in condition_nodes:
            target_node = random.choice(action_nodes)
            graph.add_condition(condition_node, target_node)
        
        # Add some random edges (with low probability to avoid cycles)
        for _ in range(num_nodes // 3):
            if random.random() < 0.3:
                from_node = random.choice(action_nodes[:-1])  # Exclude last node to avoid cycles
                to_idx = action_nodes.index(from_node) + 1
                if to_idx < len(action_nodes):
                    to_node = random.choice(action_nodes[to_idx:])
                    graph.add_edge(from_node, to_node)
        
        return graph
    
    def _randomize_primitive_params(self, primitive: StrategyPrimitive):
        """
        Randomize the parameters of a primitive
        
        Args:
            primitive: Primitive to randomize
        """
        if primitive.primitive_type == "condition":
            if primitive.name == "price_above" or primitive.name == "price_below":
                primitive.params = {
                    "asset": random.choice(["eth", "wbtc", "usdc", "usdt", "dai"]),
                    "threshold": random.uniform(100, 5000)
                }
            elif primitive.name == "price_change_above" or primitive.name == "price_change_below":
                primitive.params = {
                    "asset": random.choice(["eth", "wbtc", "usdc", "usdt", "dai"]),
                    "threshold": random.uniform(-0.1, 0.1)
                }
            elif primitive.name == "gas_price_below":
                primitive.params = {
                    "threshold": random.uniform(20, 200)
                }
            elif primitive.name == "supply_apy_above":
                primitive.params = {
                    "protocol": random.choice(["aave_v3", "compound_v3"]),
                    "asset": random.choice(["eth", "wbtc", "usdc", "usdt", "dai"]),
                    "threshold": random.uniform(0.01, 0.1)
                }
            elif primitive.name == "has_balance":
                primitive.params = {
                    "asset": random.choice(["eth", "wbtc", "usdc", "usdt", "dai"]),
                    "min_balance": random.uniform(0.1, 10)
                }
            elif primitive.name == "portfolio_value_above":
                primitive.params = {
                    "threshold": random.uniform(10000, 200000)
                }
        
        elif primitive.primitive_type == "action":
            if primitive.name == "swap":
                asset_from = random.choice(["eth", "wbtc", "usdc", "usdt", "dai"])
                asset_to = random.choice(["eth", "wbtc", "usdc", "usdt", "dai"])
                while asset_from == asset_to:
                    asset_to = random.choice(["eth", "wbtc", "usdc", "usdt", "dai"])
                
                primitive.params = {
                    "protocol": random.choice(["uniswap_v3", "curve", "balancer"]),
                    "asset_from": asset_from,
                    "asset_to": asset_to,
                    "amount_percentage": random.uniform(0.1, 1.0)
                }
            elif primitive.name == "deposit" or primitive.name == "withdraw":
                primitive.params = {
                    "protocol": random.choice(["aave_v3", "compound_v3"]),
                    "asset": random.choice(["eth", "wbtc", "usdc", "usdt", "dai"]),
                    "amount_percentage": random.uniform(0.1, 1.0)
                }
            elif primitive.name == "borrow" or primitive.name == "repay":
                primitive.params = {
                    "protocol": random.choice(["aave_v3", "compound_v3"]),
                    "asset": random.choice(["usdc", "usdt", "dai"]),
                    "amount_percentage": random.uniform(0.1, 1.0)
                }
    
    def evaluate_strategy(self, strategy: StrategyGraph, num_simulations: int = None) -> Dict:
        """
        Evaluate a strategy using the World Model Simulator
        
        Args:
            strategy: Strategy to evaluate
            num_simulations: Number of simulations to run
            
        Returns:
            Evaluation results
        """
        if num_simulations is None:
            num_simulations = self.config.get("simulation", {}).get("num_episodes", 10)
        
        # Create a strategy executor
        env = self.simulator.create_environment()
        executor = StrategyExecutor(strategy, env)
        
        # Evaluate the strategy
        evaluation_results = self.simulator.evaluate_strategy(executor, num_simulations)
        
        return evaluation_results
    
    def mutate_strategy(self, strategy: StrategyGraph) -> StrategyGraph:
        """
        Mutate a strategy
        
        Args:
            strategy: Strategy to mutate
            
        Returns:
            Mutated strategy
        """
        # Create a deep copy of the strategy
        strategy_dict = strategy.to_dict()
        mutated_strategy = StrategyGraph.from_dict(strategy_dict)
        
        # Get mutation rate
        mutation_rate = self.config.get("genetic_algorithm", {}).get("mutation_rate", 0.2)
        
        # Randomly select mutation operations
        mutation_ops = [
            self._mutate_add_node,
            self._mutate_remove_node,
            self._mutate_change_params,
            self._mutate_add_edge,
            self._mutate_remove_edge,
            self._mutate_add_condition,
            self._mutate_remove_condition
        ]
        
        # Apply mutations
        num_mutations = max(1, int(len(mutated_strategy.nodes) * mutation_rate))
        for _ in range(num_mutations):
            mutation_op = random.choice(mutation_ops)
            mutation_op(mutated_strategy)
        
        return mutated_strategy
    
    def _mutate_add_node(self, strategy: StrategyGraph):
        """
        Mutation: Add a new node to the strategy
        
        Args:
            strategy: Strategy to mutate
        """
        # Determine if we add a condition or action
        if random.random() < 0.3:
            # Add condition
            primitive = copy.deepcopy(random.choice(self.condition_primitives))
            self._randomize_primitive_params(primitive)
            node = StrategyNode(primitive)
            strategy.add_node(node)
            
            # Connect to a random action node
            action_nodes = [n for n in strategy.nodes.values() if n.primitive.primitive_type == "action"]
            if action_nodes:
                target_node = random.choice(action_nodes)
                strategy.add_condition(node, target_node)
        else:
            # Add action
            primitive = copy.deepcopy(random.choice(self.action_primitives))
            self._randomize_primitive_params(primitive)
            node = StrategyNode(primitive)
            strategy.add_node(node)
            
            # Connect to a random action node
            action_nodes = [n for n in strategy.nodes.values() if n.primitive.primitive_type == "action"]
            if action_nodes:
                from_node = random.choice(action_nodes)
                strategy.add_edge(from_node, node)
    
    def _mutate_remove_node(self, strategy: StrategyGraph):
        """
        Mutation: Remove a node from the strategy
        
        Args:
            strategy: Strategy to mutate
        """
        # Don't remove if we have too few nodes
        if len(strategy.nodes) <= 3:
            return
        
        # Don't remove entry or exit nodes
        removable_nodes = [n for n in strategy.nodes.values() 
                          if n not in strategy.entry_nodes and n not in strategy.exit_nodes]
        
        if not removable_nodes:
            return
        
        # Select a node to remove
        node_to_remove = random.choice(removable_nodes)
        
        # Reconnect edges
        for node in strategy.nodes.values():
            if node_to_remove in node.next_nodes:
                node.next_nodes.remove(node_to_remove)
                # Connect to the removed node's next nodes
                for next_node in node_to_remove.next_nodes:
                    if next_node not in node.next_nodes:
                        node.next_nodes.append(next_node)
            
            if node_to_remove in node.condition_nodes:
                node.condition_nodes.remove(node_to_remove)
        
        # Remove the node
        if node_to_remove.id in strategy.nodes:
            del strategy.nodes[node_to_remove.id]
    
    def _mutate_change_params(self, strategy: StrategyGraph):
        """
        Mutation: Change parameters of a random node
        
        Args:
            strategy: Strategy to mutate
        """
        if not strategy.nodes:
            return
        
        # Select a random node
        node = random.choice(list(strategy.nodes.values()))
        
        # Randomize its parameters
        self._randomize_primitive_params(node.primitive)
    
    def _mutate_add_edge(self, strategy: StrategyGraph):
        """
        Mutation: Add an edge between two nodes
        
        Args:
            strategy: Strategy to mutate
        """
        # Get action nodes
        action_nodes = [n for n in strategy.nodes.values() if n.primitive.primitive_type == "action"]
        
        if len(action_nodes) < 2:
            return
        
        # Select two random action nodes
        from_node = random.choice(action_nodes)
        to_node = random.choice(action_nodes)
        
        # Avoid self-loops and existing edges
        if from_node != to_node and to_node not in from_node.next_nodes:
            # Check if this would create a cycle
            # For simplicity, we'll just avoid adding edges from later nodes to earlier ones
            if action_nodes.index(from_node) < action_nodes.index(to_node):
                strategy.add_edge(from_node, to_node)
    
    def _mutate_remove_edge(self, strategy: StrategyGraph):
        """
        Mutation: Remove an edge between two nodes
        
        Args:
            strategy: Strategy to mutate
        """
        # Find nodes with outgoing edges
        nodes_with_edges = [n for n in strategy.nodes.values() if n.next_nodes]
        
        if not nodes_with_edges:
            return
        
        # Select a random node
        node = random.choice(nodes_with_edges)
        
        if not node.next_nodes:
            return
        
        # Select a random edge to remove
        next_node = random.choice(node.next_nodes)
        node.next_nodes.remove(next_node)
    
    def _mutate_add_condition(self, strategy: StrategyGraph):
        """
        Mutation: Add a condition to a node
        
        Args:
            strategy: Strategy to mutate
        """
        # Get action nodes
        action_nodes = [n for n in strategy.nodes.values() if n.primitive.primitive_type == "action"]
        
        if not action_nodes:
            return
        
        # Select a random action node
        target_node = random.choice(action_nodes)
        
        # Create a new condition node
        primitive = copy.deepcopy(random.choice(self.condition_primitives))
        self._randomize_primitive_params(primitive)
        condition_node = StrategyNode(primitive)
        strategy.add_node(condition_node)
        
        # Add condition
        strategy.add_condition(condition_node, target_node)
    
    def _mutate_remove_condition(self, strategy: StrategyGraph):
        """
        Mutation: Remove a condition from a node
        
        Args:
            strategy: Strategy to mutate
        """
        # Find nodes with conditions
        nodes_with_conditions = [n for n in strategy.nodes.values() if n.condition_nodes]
        
        if not nodes_with_conditions:
            return
        
        # Select a random node
        node = random.choice(nodes_with_conditions)
        
        if not node.condition_nodes:
            return
        
        # Select a random condition to remove
        condition_node = random.choice(node.condition_nodes)
        node.condition_nodes.remove(condition_node)
    
    def crossover(self, parent1: StrategyGraph, parent2: StrategyGraph) -> StrategyGraph:
        """
        Perform crossover between two parent strategies
        
        Args:
            parent1: First parent strategy
            parent2: Second parent strategy
            
        Returns:
            Child strategy
        """
        # Create a new strategy
        child = StrategyGraph(name=f"Child-{int(time.time())}")
        
        # Get action nodes from both parents
        parent1_actions = [n for n in parent1.nodes.values() if n.primitive.primitive_type == "action"]
        parent2_actions = [n for n in parent2.nodes.values() if n.primitive.primitive_type == "action"]
        
        if not parent1_actions or not parent2_actions:
            return self.generate_random_strategy()
        
        # Select a random crossover point for each parent
        p1_point = random.randint(1, len(parent1_actions) - 1)
        p2_point = random.randint(1, len(parent2_actions) - 1)
        
        # Take first part from parent1 and second part from parent2
        p1_first = parent1_actions[:p1_point]
        p2_second = parent2_actions[p2_point:]
        
        # Create deep copies of the nodes
        p1_first_copies = []
        for node in p1_first:
            primitive = copy.deepcopy(node.primitive)
            new_node = StrategyNode(primitive)
            child.add_node(new_node)
            p1_first_copies.append(new_node)
        
        p2_second_copies = []
        for node in p2_second:
            primitive = copy.deepcopy(node.primitive)
            new_node = StrategyNode(primitive)
            child.add_node(new_node)
            p2_second_copies.append(new_node)
        
        # Connect nodes
        for i in range(len(p1_first_copies) - 1):
            child.add_edge(p1_first_copies[i], p1_first_copies[i + 1])
        
        # Connect the two parts
        if p1_first_copies and p2_second_copies:
            child.add_edge(p1_first_copies[-1], p2_second_copies[0])
        
        for i in range(len(p2_second_copies) - 1):
            child.add_edge(p2_second_copies[i], p2_second_copies[i + 1])
        
        # Set entry and exit nodes
        if p1_first_copies:
            child.set_entry_node(p1_first_copies[0])
        elif p2_second_copies:
            child.set_entry_node(p2_second_copies[0])
        
        if p2_second_copies:
            child.set_exit_node(p2_second_copies[-1])
        elif p1_first_copies:
            child.set_exit_node(p1_first_copies[-1])
        
        # Add some conditions from both parents
        parent1_conditions = [n for n in parent1.nodes.values() if n.primitive.primitive_type == "condition"]
        parent2_conditions = [n for n in parent2.nodes.values() if n.primitive.primitive_type == "condition"]
        
        # Take some conditions from parent1
        for _ in range(min(3, len(parent1_conditions))):
            if parent1_conditions:
                condition = random.choice(parent1_conditions)
                parent1_conditions.remove(condition)
                
                primitive = copy.deepcopy(condition.primitive)
                new_condition = StrategyNode(primitive)
                child.add_node(new_condition)
                
                # Connect to a random action node
                if p1_first_copies:
                    target_node = random.choice(p1_first_copies)
                    child.add_condition(new_condition, target_node)
        
        # Take some conditions from parent2
        for _ in range(min(3, len(parent2_conditions))):
            if parent2_conditions:
                condition = random.choice(parent2_conditions)
                parent2_conditions.remove(condition)
                
                primitive = copy.deepcopy(condition.primitive)
                new_condition = StrategyNode(primitive)
                child.add_node(new_condition)
                
                # Connect to a random action node
                if p2_second_copies:
                    target_node = random.choice(p2_second_copies)
                    child.add_condition(new_condition, target_node)
        
        return child
    
    def run_genetic_algorithm(self, goal: str = None) -> Dict:
        """
        Run the genetic algorithm to synthesize strategies
        
        Args:
            goal: Goal for the strategy (e.g., "maximize_profit", "minimize_risk")
            
        Returns:
            Dict containing the best strategy and results
        """
        # Get GA parameters
        ga_params = self.config.get("genetic_algorithm", {})
        population_size = ga_params.get("population_size", 50)
        generations = ga_params.get("generations", 20)
        mutation_rate = ga_params.get("mutation_rate", 0.2)
        crossover_rate = ga_params.get("crossover_rate", 0.7)
        elitism_count = ga_params.get("elitism_count", 5)
        
        logger.info(f"Running genetic algorithm with population={population_size}, generations={generations}")
        
        # Initialize population
        population = []
        for i in range(population_size):
            strategy = self.generate_random_strategy(name=f"Gen0-Ind{i}")
            population.append(strategy)
        
        # Evaluate initial population
        fitness_scores = []
        for strategy in tqdm(population, desc="Evaluating initial population"):
            results = self.evaluate_strategy(strategy)
            fitness = self._calculate_fitness(results, goal)
            fitness_scores.append(fitness)
        
        # Main GA loop
        best_strategy = None
        best_fitness = float("-inf")
        best_results = None
        
        for generation in range(generations):
            logger.info(f"Generation {generation+1}/{generations}")
            
            # Sort population by fitness
            sorted_indices = np.argsort(fitness_scores)[::-1]  # Descending order
            sorted_population = [population[i] for i in sorted_indices]
            sorted_fitness = [fitness_scores[i] for i in sorted_indices]
            
            # Update best strategy
            if sorted_fitness[0] > best_fitness:
                best_fitness = sorted_fitness[0]
                best_strategy = sorted_population[0]
                best_results = self.evaluate_strategy(best_strategy)
                
                logger.info(f"New best strategy: fitness={best_fitness:.4f}, return={best_results['mean_return']:.2%}")
            
            # Create new population
            new_population = []
            
            # Elitism: keep the best individuals
            for i in range(elitism_count):
                new_population.append(sorted_population[i])
            
            # Fill the rest of the population
            while len(new_population) < population_size:
                # Selection
                parent1 = self._tournament_selection(sorted_population, sorted_fitness)
                parent2 = self._tournament_selection(sorted_population, sorted_fitness)
                
                # Crossover
                if random.random() < crossover_rate:
                    child = self.crossover(parent1, parent2)
                else:
                    child = copy.deepcopy(parent1)
                
                # Mutation
                if random.random() < mutation_rate:
                    child = self.mutate_strategy(child)
                
                # Add to new population
                new_population.append(child)
            
            # Evaluate new population
            new_fitness_scores = []
            for strategy in tqdm(new_population, desc=f"Evaluating generation {generation+1}"):
                results = self.evaluate_strategy(strategy)
                fitness = self._calculate_fitness(results, goal)
                new_fitness_scores.append(fitness)
            
            # Update population and fitness scores
            population = new_population
            fitness_scores = new_fitness_scores
            
            # Log progress
            avg_fitness = sum(fitness_scores) / len(fitness_scores)
            logger.info(f"Generation {generation+1} complete: avg_fitness={avg_fitness:.4f}, best_fitness={best_fitness:.4f}")
        
        # Return best strategy and results
        return {
            "strategy": best_strategy,
            "fitness": best_fitness,
            "results": best_results
        }
    
    def _calculate_fitness(self, results: Dict, goal: str = None) -> float:
        """
        Calculate fitness score for a strategy
        
        Args:
            results: Evaluation results
            goal: Goal for the strategy
            
        Returns:
            Fitness score
        """
        if goal == "maximize_profit":
            # Prioritize return
            return results["mean_return"] * 0.7 + results["sharpe_ratio"] * 0.3
        elif goal == "minimize_risk":
            # Prioritize Sharpe ratio and minimize drawdown
            return results["sharpe_ratio"] * 0.7 - abs(results["max_drawdown"]) * 0.3
        elif goal == "balanced":
            # Balance return and risk
            return results["mean_return"] * 0.5 + results["sharpe_ratio"] * 0.5
        else:
            # Default: balance return, Sharpe ratio, and success rate
            return (
                results["mean_return"] * 0.4 +
                results["sharpe_ratio"] * 0.4 +
                results["success_rate"] * 0.2
            )
    
    def _tournament_selection(self, population: List[StrategyGraph], fitness_scores: List[float], tournament_size: int = 3) -> StrategyGraph:
        """
        Tournament selection for genetic algorithm
        
        Args:
            population: Population of strategies
            fitness_scores: Fitness scores for the population
            tournament_size: Number of individuals in each tournament
            
        Returns:
            Selected strategy
        """
        # Select random individuals for tournament
        indices = random.sample(range(len(population)), min(tournament_size, len(population)))
        
        # Find the best individual in the tournament
        best_idx = indices[0]
        best_fitness = fitness_scores[best_idx]
        
        for idx in indices[1:]:
            if fitness_scores[idx] > best_fitness:
                best_idx = idx
                best_fitness = fitness_scores[idx]
        
        return population[best_idx]
    
    def save_strategy(self, strategy: StrategyGraph, results: Dict = None) -> str:
        """
        Save a strategy to file
        
        Args:
            strategy: Strategy to save
            results: Evaluation results
            
        Returns:
            Path to the saved file
        """
        # Create a unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{strategy.name}_{timestamp}.json"
        
        # Save path
        save_path = os.path.join(self.config.get("results_dir", "results/strategy_synthesizer"), filename)
        
        # Prepare data to save
        save_data = {
            "strategy": strategy.to_dict(),
            "results": results
        }
        
        # Save to file
        with open(save_path, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        logger.info(f"Strategy saved to {save_path}")
        
        return save_path
    
    def load_strategy(self, path: str) -> Tuple[StrategyGraph, Dict]:
        """
        Load a strategy from file
        
        Args:
            path: Path to the strategy file
            
        Returns:
            Tuple of (strategy, results)
        """
        with open(path, 'r') as f:
            data = json.load(f)
        
        strategy = StrategyGraph.from_dict(data.get("strategy", {}))
        results = data.get("results", {})
        
        logger.info(f"Strategy loaded from {path}")
        
        return strategy, results
    
    def synthesize_strategy(self, goal: str = None) -> Dict:
        """
        Synthesize a new strategy
        
        Args:
            goal: Goal for the strategy
            
        Returns:
            Dict containing the synthesized strategy and results
        """
        # Run genetic algorithm
        ga_results = self.run_genetic_algorithm(goal)
        
        # Save the best strategy
        strategy = ga_results["strategy"]
        results = ga_results["results"]
        save_path = self.save_strategy(strategy, results)
        
        return {
            "strategy": strategy,
            "results": results,
            "save_path": save_path
        }

def main():
    """Main function"""
    # Initialize the Strategy Synthesizer
    synthesizer = StrategySynthesizer()
    
    # Synthesize a strategy
    result = synthesizer.synthesize_strategy(goal="balanced")
    
    # Print results
    strategy = result["strategy"]
    results = result["results"]
    
    print(f"Synthesized strategy: {strategy.name}")
    print(f"Number of nodes: {len(strategy.nodes)}")
    print(f"Performance:")
    print(f"  Mean Return: {results['mean_return']:.2%}")
    print(f"  Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"  Success Rate: {results['success_rate']:.2%}")
    print(f"  Max Drawdown: {results['max_drawdown']:.2%}")
    print(f"Strategy saved to: {result['save_path']}")

if __name__ == "__main__":
    main()