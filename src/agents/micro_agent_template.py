#!/usr/bin/env python3
"""
🤖 MICRO-AGENT TEMPLATE - BASE CLASS FOR SWARM INTELLIGENCE
==========================================================

This module defines the base class for hyper-specialized micro-agents that form
the foundation of the swarm intelligence system. Each micro-agent is designed to:

1. Focus on a single, specific task
2. Communicate findings to the swarm
3. Operate with minimal resource usage
4. Be dynamically created and destroyed

KEY FEATURES:
- Lightweight design for massive parallelism
- Built-in communication with the swarm
- Self-monitoring of performance
- Standardized lifecycle management

Author: AI Assistant
Version: 1.0
Date: June 2025
"""

import os
import time
import uuid
import json
import logging
import asyncio
import threading
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
import redis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
)

class MicroAgentStatus:
    """Status values for micro-agents"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"

class MicroAgent(ABC):
    """
    Base class for all micro-agents in the swarm
    
    This abstract class defines the interface and common functionality
    for all micro-agents. Specific agent types should inherit from this
    class and implement the abstract methods.
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        parameters: Dict[str, Any],
        redis_url: str = "redis://localhost:6379/0"
    ):
        """
        Initialize a new micro-agent
        
        Args:
            agent_id: Unique identifier for this agent
            agent_type: Type of agent (e.g., "pair_watcher", "whale_watcher")
            parameters: Configuration parameters for this agent
            redis_url: URL for Redis connection
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.parameters = parameters
        self.redis_url = redis_url
        
        # Agent state
        self.status = MicroAgentStatus.INITIALIZING
        self.created_at = time.time()
        self.last_active = time.time()
        self.performance_metrics = {
            "opportunities_found": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "errors": 0,
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
        }
        self.discoveries = []
        
        # Set up logging
        self.logger = logging.getLogger(f"MicroAgent.{agent_type}.{agent_id[:8]}")
        
        # Initialize Redis connection
        self._init_redis()
        
        # Initialize communication channels
        self.discovery_channel = "swarm:discoveries"
        self.status_channel = "swarm:agent_status"
        self.command_channel = f"swarm:agent:{agent_id}:commands"
        
        # Set up command listener
        self._command_listener_thread = None
        self._running = False
    
    def _init_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.Redis.from_url(self.redis_url)
            self.redis_client.ping()  # Test connection
            self.logger.info("Connected to Redis successfully")
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
            self.status = MicroAgentStatus.ERROR
            raise ConnectionError(f"Failed to connect to Redis: {e}")
    
    def start(self):
        """Start the agent's main loop"""
        if self.status in [MicroAgentStatus.RUNNING, MicroAgentStatus.INITIALIZING]:
            self.logger.warning(f"Agent already running or initializing")
            return
        
        self._running = True
        self.status = MicroAgentStatus.RUNNING
        
        # Start command listener thread
        self._command_listener_thread = threading.Thread(
            target=self._listen_for_commands,
            daemon=True
        )
        self._command_listener_thread.start()
        
        # Publish status update
        self._publish_status()
        
        # Start main loop in a separate thread
        self._main_thread = threading.Thread(
            target=self._main_loop,
            daemon=True
        )
        self._main_thread.start()
        
        self.logger.info(f"Agent started")
    
    def stop(self):
        """Stop the agent's main loop"""
        if self.status in [MicroAgentStatus.STOPPED, MicroAgentStatus.STOPPING]:
            self.logger.warning(f"Agent already stopped or stopping")
            return
        
        self.status = MicroAgentStatus.STOPPING
        self._running = False
        
        # Publish status update
        self._publish_status()
        
        # Wait for threads to complete
        if self._main_thread and self._main_thread.is_alive():
            self._main_thread.join(timeout=5)
        
        if self._command_listener_thread and self._command_listener_thread.is_alive():
            self._command_listener_thread.join(timeout=5)
        
        self.status = MicroAgentStatus.STOPPED
        self._publish_status()
        
        self.logger.info(f"Agent stopped")
    
    def pause(self):
        """Pause the agent's operations"""
        if self.status != MicroAgentStatus.RUNNING:
            self.logger.warning(f"Cannot pause agent in {self.status} state")
            return
        
        self.status = MicroAgentStatus.PAUSED
        self._publish_status()
        
        self.logger.info(f"Agent paused")
    
    def resume(self):
        """Resume the agent's operations"""
        if self.status != MicroAgentStatus.PAUSED:
            self.logger.warning(f"Cannot resume agent in {self.status} state")
            return
        
        self.status = MicroAgentStatus.RUNNING
        self._publish_status()
        
        self.logger.info(f"Agent resumed")
    
    def _main_loop(self):
        """Main execution loop for the agent"""
        try:
            while self._running:
                if self.status == MicroAgentStatus.RUNNING:
                    # Update last active timestamp
                    self.last_active = time.time()
                    
                    # Execute agent-specific logic
                    self.execute_cycle()
                    
                    # Update performance metrics
                    self._update_performance_metrics()
                    
                    # Publish status update periodically
                    if int(time.time()) % 60 == 0:  # Once per minute
                        self._publish_status()
                
                # Sleep for a bit to avoid consuming too many resources
                time.sleep(self.get_cycle_interval())
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}", exc_info=True)
            self.status = MicroAgentStatus.ERROR
            self.performance_metrics["errors"] += 1
            self._publish_status()
    
    def _listen_for_commands(self):
        """Listen for commands on the agent's command channel"""
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(self.command_channel)
        
        self.logger.info(f"Listening for commands on {self.command_channel}")
        
        try:
            for message in pubsub.listen():
                if not self._running:
                    break
                
                if message["type"] == "message":
                    try:
                        command = json.loads(message["data"])
                        self.logger.debug(f"Received command: {command}")
                        
                        self.performance_metrics["messages_received"] += 1
                        
                        # Process command
                        self._process_command(command)
                    except Exception as e:
                        self.logger.error(f"Error processing command: {e}", exc_info=True)
                        self.performance_metrics["errors"] += 1
        except Exception as e:
            self.logger.error(f"Error in command listener: {e}", exc_info=True)
            self.performance_metrics["errors"] += 1
        finally:
            pubsub.unsubscribe()
    
    def _process_command(self, command: Dict[str, Any]):
        """Process a command received from the command channel"""
        if "action" not in command:
            self.logger.warning(f"Received command without action: {command}")
            return
        
        action = command["action"]
        
        if action == "stop":
            self.stop()
        elif action == "pause":
            self.pause()
        elif action == "resume":
            self.resume()
        elif action == "update_parameters":
            if "parameters" in command:
                self._update_parameters(command["parameters"])
        elif action == "get_status":
            self._publish_status()
        else:
            # Pass to agent-specific command handler
            self.handle_command(action, command)
    
    def _update_parameters(self, new_parameters: Dict[str, Any]):
        """Update the agent's parameters"""
        self.parameters.update(new_parameters)
        self.logger.info(f"Updated parameters: {new_parameters}")
    
    def _publish_status(self):
        """Publish the agent's status to the status channel"""
        status_data = {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": self.status,
            "created_at": self.created_at,
            "last_active": self.last_active,
            "uptime": time.time() - self.created_at,
            "performance_metrics": self.performance_metrics,
            "discoveries_count": len(self.discoveries),
            "parameters": self.parameters
        }
        
        try:
            self.redis_client.publish(
                self.status_channel,
                json.dumps(status_data)
            )
            self.performance_metrics["messages_sent"] += 1
        except Exception as e:
            self.logger.error(f"Error publishing status: {e}")
            self.performance_metrics["errors"] += 1
    
    def publish_discovery(self, discovery: Dict[str, Any]):
        """
        Publish a discovery to the swarm
        
        Args:
            discovery: Dictionary containing discovery details
        """
        # Add agent information to the discovery
        discovery_data = {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "timestamp": time.time(),
            "discovery": discovery
        }
        
        # Add to local discoveries list
        self.discoveries.append(discovery_data)
        
        # Trim discoveries list if it gets too long
        if len(self.discoveries) > 100:
            self.discoveries = self.discoveries[-100:]
        
        # Publish to the discovery channel
        try:
            self.redis_client.publish(
                self.discovery_channel,
                json.dumps(discovery_data)
            )
            self.performance_metrics["messages_sent"] += 1
            self.performance_metrics["opportunities_found"] += 1
            self.logger.info(f"Published discovery: {discovery}")
        except Exception as e:
            self.logger.error(f"Error publishing discovery: {e}")
            self.performance_metrics["errors"] += 1
    
    def _update_performance_metrics(self):
        """Update performance metrics"""
        # This is a simple implementation that could be enhanced
        # with actual resource usage monitoring
        import psutil
        
        process = psutil.Process(os.getpid())
        self.performance_metrics["cpu_usage"] = process.cpu_percent(interval=0.1)
        self.performance_metrics["memory_usage"] = process.memory_info().rss / 1024 / 1024  # MB
    
    @abstractmethod
    def execute_cycle(self):
        """
        Execute a single cycle of the agent's logic
        
        This method should be implemented by each specific agent type.
        It should contain the core logic that the agent executes on each cycle.
        """
        pass
    
    @abstractmethod
    def get_cycle_interval(self) -> float:
        """
        Get the interval between execution cycles in seconds
        
        This method should be implemented by each specific agent type.
        It should return the time to wait between execution cycles.
        """
        pass
    
    @abstractmethod
    def handle_command(self, action: str, command: Dict[str, Any]):
        """
        Handle agent-specific commands
        
        This method should be implemented by each specific agent type.
        It should handle any commands that are specific to this agent type.
        
        Args:
            action: The action to perform
            command: The full command data
        """
        pass