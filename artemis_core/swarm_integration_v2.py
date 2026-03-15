#!/usr/bin/env python3
"""
🧠 ARTEMIS AI CORE - SWARM INTEGRATION V2
=========================================

This module integrates the Artemis AI Core with the Swarm Agent Factory V2
and Parallel Opportunity Coordinator to provide strategic oversight and
direction to the swarm.

KEY FEATURES:
- Strategic Oversight - Directs swarm resource allocation
- Performance Analysis - Evaluates swarm effectiveness and adapts strategies
- Dynamic Reconfiguration - Adjusts swarm composition based on market conditions
- Opportunity Validation - Validates complex opportunities before execution
- Risk Management - Applies risk controls to swarm activities

Author: AI Assistant
Version: 2.0
Date: June 2025
"""

import os
import json
import time
import logging
import asyncio
import threading
import yaml
import redis
from typing import Dict, List, Any, Optional, Callable, Tuple
import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger("ArtemisSwarmIntegrationV2")

class ArtemisSwarmIntegrationV2:
    """
    Integration between Artemis AI Core and the Swarm Agent Factory V2
    
    This class provides strategic oversight and direction to the swarm,
    analyzing performance and dynamically reconfiguring the swarm based
    on market conditions.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the Artemis Swarm Integration
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path or "config/artemis_swarm_integration.yaml")
        self._init_redis()
        self._init_message_bus()
        
        # Performance tracking
        self.agent_performance = {}
        self.opportunity_history = []
        self.execution_history = []
        
        # Strategy recommendations
        self.current_recommendations = []
        self.last_recommendation_update = 0
        
        # Swarm composition
        self.current_swarm_composition = {}
        
        logger.info("Artemis Swarm Integration V2 initialized")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file"""
        import yaml
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            # Validate required fields
            required_fields = [
                'redis_url', 'update_interval_seconds',
                'risk_parameters'
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
                'update_interval_seconds': 60,
                'risk_parameters': {
                    'max_opportunity_value_usd': 10000,
                    'max_daily_execution_count': 100,
                    'max_daily_value_usd': 50000,
                    'min_profit_threshold_usd': 1.0
                },
                'halal_mode': False
            }
    
    def _init_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.Redis.from_url(self.config['redis_url'])
            self.redis_client.ping()  # Test connection
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise ConnectionError(f"Failed to connect to Redis: {e}")
    
    def _init_message_bus(self):
        """Initialize message bus for communication"""
        self.message_bus = MessageBus(self.redis_client)
        
        # Subscribe to channels
        self.message_bus.subscribe("swarm:agent_status", self._handle_agent_status)
        self.message_bus.subscribe("swarm:discoveries", self._handle_discovery)
        self.message_bus.subscribe("swarm:composite_opportunities", self._handle_composite_opportunity)
        self.message_bus.subscribe("swarm:opportunity_executions", self._handle_opportunity_execution)
        self.message_bus.subscribe("artemis:commands", self._handle_artemis_command)
        
        # Start message bus
        self.message_bus.start()
        
        logger.info("Message bus initialized")
    
    def _handle_agent_status(self, message: Dict[str, Any]):
        """
        Handle agent status updates
        
        Args:
            message: Status update message
        """
        if "agent_id" not in message:
            return
        
        agent_id = message["agent_id"]
        
        # Update agent performance tracking
        self.agent_performance[agent_id] = {
            "agent_type": message.get("agent_type"),
            "status": message.get("status"),
            "last_active": message.get("last_active", time.time()),
            "performance_metrics": message.get("performance_metrics", {}),
            "parameters": message.get("parameters", {})
        }
        
        # Update swarm composition
        agent_type = message.get("agent_type")
        if agent_type:
            if agent_type not in self.current_swarm_composition:
                self.current_swarm_composition[agent_type] = 0
            
            # Only count active agents
            if message.get("status") in ["initializing", "running"]:
                self.current_swarm_composition[agent_type] += 1
    
    def _handle_discovery(self, message: Dict[str, Any]):
        """
        Handle agent discoveries
        
        Args:
            message: Discovery message
        """
        # We don't need to do much with individual discoveries
        # as they are processed by the Parallel Opportunity Coordinator
        # Just keep track of the most recent ones for analysis
        
        if len(self.opportunity_history) > 1000:
            self.opportunity_history = self.opportunity_history[-1000:]
        
        self.opportunity_history.append({
            "timestamp": time.time(),
            "agent_id": message.get("agent_id"),
            "agent_type": message.get("agent_type"),
            "discovery": message.get("discovery", {})
        })
    
    def _handle_composite_opportunity(self, message: Dict[str, Any]):
        """
        Handle composite opportunities from the coordinator
        
        Args:
            message: Composite opportunity message
        """
        # Validate the opportunity
        opportunity_id = message.get("opportunity_id")
        if not opportunity_id:
            return
        
        # Add to history
        self.opportunity_history.append({
            "timestamp": time.time(),
            "type": "composite",
            "opportunity_id": opportunity_id,
            "opportunity": message
        })
        
        # Trim history if it gets too long
        if len(self.opportunity_history) > 1000:
            self.opportunity_history = self.opportunity_history[-1000:]
        
        # Validate opportunity if it exceeds certain thresholds
        estimated_profit_usd = message.get("estimated_profit_usd", 0)
        risk_parameters = self.config["risk_parameters"]
        
        if estimated_profit_usd > risk_parameters.get("validation_threshold_usd", 100):
            # Schedule validation
            asyncio.create_task(self._validate_opportunity(message))
    
    def _handle_opportunity_execution(self, message: Dict[str, Any]):
        """
        Handle opportunity execution results
        
        Args:
            message: Execution result message
        """
        # Add to execution history
        self.execution_history.append({
            "timestamp": time.time(),
            "execution": message
        })
        
        # Trim history if it gets too long
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]
        
        # Update strategy based on execution results
        success = message.get("success", False)
        profit_usd = message.get("actual_profit_usd", 0)
        
        if success and profit_usd > 0:
            # Successful execution - consider scaling up this type of opportunity
            opportunity_type = message.get("opportunity_type")
            if opportunity_type:
                # Schedule strategy update
                if time.time() - self.last_recommendation_update > self.config["update_interval_seconds"]:
                    asyncio.create_task(self.update_strategy_recommendations())
    
    def _handle_artemis_command(self, message: Dict[str, Any]):
        """
        Handle commands sent to Artemis
        
        Args:
            message: Command message
        """
        if "action" not in message:
            logger.warning(f"Received command without action: {message}")
            return
        
        action = message["action"]
        
        if action == "update_strategy":
            # Force strategy update
            asyncio.create_task(self.update_strategy_recommendations())
            
            # Send response if requested
            if "response_channel" in message:
                response = {
                    "action": "update_strategy",
                    "success": True
                }
                self.redis_client.publish(message["response_channel"], json.dumps(response))
        
        elif action == "get_swarm_status":
            # Get current swarm status
            status = self.get_swarm_status()
            
            # Send response if requested
            if "response_channel" in message:
                response = {
                    "action": "get_swarm_status",
                    "success": True,
                    "status": status
                }
                self.redis_client.publish(message["response_channel"], json.dumps(response))
        
        elif action == "get_recommendations":
            # Get current recommendations
            
            # Send response if requested
            if "response_channel" in message:
                response = {
                    "action": "get_recommendations",
                    "success": True,
                    "recommendations": self.current_recommendations,
                    "last_update": self.last_recommendation_update
                }
                self.redis_client.publish(message["response_channel"], json.dumps(response))
    
    async def _validate_opportunity(self, opportunity: Dict[str, Any]) -> bool:
        """
        Validate a composite opportunity
        
        Args:
            opportunity: Opportunity to validate
            
        Returns:
            True if valid, False otherwise
        """
        opportunity_id = opportunity.get("opportunity_id")
        estimated_profit_usd = opportunity.get("estimated_profit_usd", 0)
        
        logger.info(f"Validating opportunity {opportunity_id} with estimated profit ${estimated_profit_usd}")
        
        # Check against risk parameters
        risk_parameters = self.config["risk_parameters"]
        
        if estimated_profit_usd > risk_parameters.get("max_opportunity_value_usd", 10000):
            logger.warning(f"Opportunity {opportunity_id} exceeds maximum value threshold")
            return False
        
        # Check daily execution count
        today_executions = [
            e for e in self.execution_history
            if time.time() - e.get("timestamp", 0) < 86400  # Last 24 hours
        ]
        
        if len(today_executions) >= risk_parameters.get("max_daily_execution_count", 100):
            logger.warning(f"Daily execution count limit reached")
            return False
        
        # Check daily value
        today_value = sum(
            e.get("execution", {}).get("actual_profit_usd", 0)
            for e in today_executions
        )
        
        if today_value + estimated_profit_usd > risk_parameters.get("max_daily_value_usd", 50000):
            logger.warning(f"Daily value limit would be exceeded")
            return False
        
        # If in halal mode, check compliance
        if self.config.get("halal_mode", False):
            # Check if all components are halal compliant
            components = opportunity.get("components", [])
            for component in components:
                if not component.get("halal_compliant", False):
                    logger.warning(f"Opportunity {opportunity_id} contains non-halal components")
                    return False
        
        # Opportunity is valid
        logger.info(f"Opportunity {opportunity_id} validated successfully")
        
        # Publish validation result
        validation_result = {
            "opportunity_id": opportunity_id,
            "validated": True,
            "validator": "artemis_ai_core",
            "timestamp": time.time()
        }
        
        self.redis_client.publish(
            "swarm:opportunity_validations",
            json.dumps(validation_result)
        )
        
        return True
    
    async def update_strategy_recommendations(self):
        """Update strategy recommendations based on performance data"""
        logger.info("Updating strategy recommendations")
        
        # Analyze recent performance
        recent_discoveries = [
            d for d in self.opportunity_history
            if time.time() - d.get("timestamp", 0) < 3600  # Last hour
        ]
        
        recent_executions = [
            e for e in self.execution_history
            if time.time() - e.get("timestamp", 0) < 3600  # Last hour
        ]
        
        # Count discoveries by agent type
        discoveries_by_type = {}
        for discovery in recent_discoveries:
            agent_type = discovery.get("agent_type")
            if agent_type:
                if agent_type not in discoveries_by_type:
                    discoveries_by_type[agent_type] = 0
                discoveries_by_type[agent_type] += 1
        
        # Calculate success rate by opportunity type
        executions_by_type = {}
        success_by_type = {}
        profit_by_type = {}
        
        for execution in recent_executions:
            execution_data = execution.get("execution", {})
            opportunity_type = execution_data.get("opportunity_type")
            
            if opportunity_type:
                if opportunity_type not in executions_by_type:
                    executions_by_type[opportunity_type] = 0
                    success_by_type[opportunity_type] = 0
                    profit_by_type[opportunity_type] = 0
                
                executions_by_type[opportunity_type] += 1
                
                if execution_data.get("success", False):
                    success_by_type[opportunity_type] += 1
                    profit_by_type[opportunity_type] += execution_data.get("actual_profit_usd", 0)
        
        # Generate recommendations
        recommendations = []
        
        # 1. Scale up agent types that are finding opportunities
        for agent_type, count in discoveries_by_type.items():
            if count > 0:
                # Calculate discoveries per agent
                agents_of_type = sum(
                    1 for a in self.agent_performance.values()
                    if a.get("agent_type") == agent_type and a.get("status") in ["initializing", "running"]
                )
                
                discoveries_per_agent = count / max(agents_of_type, 1)
                
                if discoveries_per_agent > 0.5:  # More than 0.5 discoveries per agent per hour
                    # Recommend scaling up
                    recommendations.append({
                        "action": "scale_up",
                        "agent_type": agent_type,
                        "reason": f"High discovery rate ({discoveries_per_agent:.2f} per agent per hour)",
                        "scale_factor": min(2.0, 1.0 + discoveries_per_agent / 2)
                    })
        
        # 2. Scale down agent types that aren't finding opportunities
        for agent_type, count in self.current_swarm_composition.items():
            if count > 10 and agent_type not in discoveries_by_type:
                # No discoveries from this agent type
                recommendations.append({
                    "action": "scale_down",
                    "agent_type": agent_type,
                    "reason": "No recent discoveries",
                    "scale_factor": 0.5
                })
        
        # 3. Recommend new agent types based on successful executions
        for opportunity_type, executions in executions_by_type.items():
            if executions > 0:
                success_rate = success_by_type[opportunity_type] / executions
                avg_profit = profit_by_type[opportunity_type] / max(success_by_type[opportunity_type], 1)
                
                if success_rate > 0.7 and avg_profit > 5.0:
                    # High success rate and good profit - recommend more agents
                    agent_type = self._map_opportunity_to_agent_type(opportunity_type)
                    if agent_type:
                        recommendations.append({
                            "action": "create_agents",
                            "agent_type": agent_type,
                            "reason": f"High success rate ({success_rate:.2f}) and profit (${avg_profit:.2f})",
                            "count": int(10 * success_rate * (avg_profit / 10))
                        })
        
        # Store recommendations
        self.current_recommendations = recommendations
        self.last_recommendation_update = time.time()
        
        # Publish recommendations
        self.redis_client.publish(
            "artemis:strategy_recommendations",
            json.dumps({
                "timestamp": time.time(),
                "recommendations": recommendations
            })
        )
        
        # Apply recommendations automatically
        await self._apply_recommendations(recommendations)
        
        logger.info(f"Updated strategy recommendations: {len(recommendations)} recommendations")
    
    def _map_opportunity_to_agent_type(self, opportunity_type: str) -> Optional[str]:
        """
        Map opportunity type to agent type
        
        Args:
            opportunity_type: Type of opportunity
            
        Returns:
            Corresponding agent type, or None if no mapping exists
        """
        # Simple mapping
        mapping = {
            "price_difference": "pair_watcher",
            "triangular_arbitrage": "triangular_arbitrage",
            "flash_loan": "flash_arbitrage",
            "liquidation": "liquidation_hunter",
            "whale_movement": "whale_watcher",
            "cross_chain": "cross_chain_scout",
            "mev": "mev_scanner"
        }
        
        return mapping.get(opportunity_type)
    
    async def _apply_recommendations(self, recommendations: List[Dict[str, Any]]):
        """
        Apply strategy recommendations
        
        Args:
            recommendations: List of recommendations to apply
        """
        for recommendation in recommendations:
            action = recommendation.get("action")
            
            if action == "scale_up":
                agent_type = recommendation.get("agent_type")
                scale_factor = recommendation.get("scale_factor", 1.5)
                
                # Find templates of this agent type
                templates = await self._get_templates_by_agent_type(agent_type)
                
                if templates:
                    # Calculate how many agents to create
                    current_count = self.current_swarm_composition.get(agent_type, 0)
                    target_count = int(current_count * scale_factor)
                    to_create = target_count - current_count
                    
                    if to_create > 0:
                        logger.info(f"Applying recommendation: Scale up {agent_type} by creating {to_create} agents")
                        
                        # Create agents
                        for _ in range(to_create):
                            template_id = templates[0]  # Use first template
                            
                            self.redis_client.publish(
                                "swarm:factory:commands",
                                json.dumps({
                                    "action": "create_agent",
                                    "template_id": template_id
                                })
                            )
                            
                            # Small delay to avoid overwhelming the system
                            await asyncio.sleep(0.01)
            
            elif action == "scale_down":
                agent_type = recommendation.get("agent_type")
                scale_factor = recommendation.get("scale_factor", 0.5)
                
                # Calculate how many agents to remove
                current_count = self.current_swarm_composition.get(agent_type, 0)
                target_count = max(1, int(current_count * scale_factor))
                to_remove = current_count - target_count
                
                if to_remove > 0:
                    logger.info(f"Applying recommendation: Scale down {agent_type} by removing {to_remove} agents")
                    
                    # Get agents of this type
                    agents_of_type = [
                        agent_id for agent_id, data in self.agent_performance.items()
                        if data.get("agent_type") == agent_type and data.get("status") in ["initializing", "running"]
                    ]
                    
                    # Sort by performance (ascending)
                    agents_of_type.sort(
                        key=lambda a: self.agent_performance[a].get("performance_metrics", {}).get("opportunities_found", 0)
                    )
                    
                    # Remove the worst performing agents
                    for agent_id in agents_of_type[:to_remove]:
                        self.redis_client.publish(
                            "swarm:factory:commands",
                            json.dumps({
                                "action": "delete_agent",
                                "agent_id": agent_id
                            })
                        )
                        
                        # Small delay to avoid overwhelming the system
                        await asyncio.sleep(0.01)
            
            elif action == "create_agents":
                agent_type = recommendation.get("agent_type")
                count = recommendation.get("count", 10)
                
                # Find templates of this agent type
                templates = await self._get_templates_by_agent_type(agent_type)
                
                if templates:
                    logger.info(f"Applying recommendation: Create {count} {agent_type} agents")
                    
                    # Create agents
                    for _ in range(count):
                        template_id = templates[0]  # Use first template
                        
                        self.redis_client.publish(
                            "swarm:factory:commands",
                            json.dumps({
                                "action": "create_agent",
                                "template_id": template_id
                            })
                        )
                        
                        # Small delay to avoid overwhelming the system
                        await asyncio.sleep(0.01)
    
    async def _get_templates_by_agent_type(self, agent_type: str) -> List[str]:
        """
        Get templates by agent type
        
        Args:
            agent_type: Type of agent
            
        Returns:
            List of template IDs
        """
        # Create a unique response channel
        response_channel = f"artemis:response:{time.time()}"
        
        # Request all agents to get templates
        self.redis_client.publish(
            "swarm:factory:commands",
            json.dumps({
                "action": "get_all_agents",
                "response_channel": response_channel
            })
        )
        
        # Wait for response
        templates = []
        
        # Create a future to wait for the response
        future = asyncio.Future()
        
        def message_handler(message):
            try:
                data = json.loads(message["data"])
                if data.get("action") == "get_all_agents":
                    # Extract templates from agent data
                    templates_by_type = {}
                    
                    for agent in data.get("agents", []):
                        template_id = agent.get("template_id")
                        agent_type_value = agent.get("agent_type")
                        
                        if template_id and agent_type_value:
                            if agent_type_value not in templates_by_type:
                                templates_by_type[agent_type_value] = []
                            
                            if template_id not in templates_by_type[agent_type_value]:
                                templates_by_type[agent_type_value].append(template_id)
                    
                    # Set the result
                    future.set_result(templates_by_type.get(agent_type, []))
            except Exception as e:
                logger.error(f"Error processing response: {e}")
                future.set_result([])
        
        # Subscribe to the response channel
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(**{response_channel: message_handler})
        pubsub_thread = pubsub.run_in_thread(sleep_time=0.001)
        
        try:
            # Wait for the response with a timeout
            templates = await asyncio.wait_for(future, timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for templates of type {agent_type}")
            templates = []
        finally:
            # Clean up
            pubsub_thread.stop()
            pubsub.unsubscribe(response_channel)
        
        return templates
    
    def get_swarm_status(self) -> Dict[str, Any]:
        """
        Get current swarm status
        
        Returns:
            Dictionary with swarm status information
        """
        # Count agents by status
        agents_by_status = {}
        for agent_data in self.agent_performance.values():
            status = agent_data.get("status", "unknown")
            if status not in agents_by_status:
                agents_by_status[status] = 0
            agents_by_status[status] += 1
        
        # Count agents by type
        agents_by_type = self.current_swarm_composition.copy()
        
        # Calculate discovery rate
        recent_discoveries = [
            d for d in self.opportunity_history
            if time.time() - d.get("timestamp", 0) < 3600  # Last hour
        ]
        
        # Calculate execution rate and success rate
        recent_executions = [
            e for e in self.execution_history
            if time.time() - e.get("timestamp", 0) < 3600  # Last hour
        ]
        
        successful_executions = [
            e for e in recent_executions
            if e.get("execution", {}).get("success", False)
        ]
        
        # Calculate total profit
        total_profit = sum(
            e.get("execution", {}).get("actual_profit_usd", 0)
            for e in successful_executions
        )
        
        return {
            "timestamp": time.time(),
            "total_agents": sum(agents_by_status.values()),
            "agents_by_status": agents_by_status,
            "agents_by_type": agents_by_type,
            "discovery_rate": {
                "hourly": len(recent_discoveries),
                "by_type": {
                    d.get("agent_type"): recent_discoveries.count(d.get("agent_type"))
                    for d in recent_discoveries if d.get("agent_type")
                }
            },
            "execution_rate": {
                "hourly": len(recent_executions),
                "success_rate": len(successful_executions) / max(len(recent_executions), 1),
                "total_profit_usd": total_profit
            },
            "recommendations": {
                "count": len(self.current_recommendations),
                "last_update": self.last_recommendation_update
            }
        }
    
    async def run(self):
        """Run the integration's main loop"""
        logger.info("Starting Artemis Swarm Integration V2 main loop")
        
        try:
            # Initial strategy update
            await self.update_strategy_recommendations()
            
            # Main loop
            while True:
                # Periodically update strategy recommendations
                if time.time() - self.last_recommendation_update > self.config["update_interval_seconds"]:
                    await self.update_strategy_recommendations()
                
                # Sleep for a bit
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, shutting down")
        finally:
            # Stop message bus
            self.message_bus.stop()
            
            logger.info("Artemis Swarm Integration V2 stopped")


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


async def main():
    """Main entry point"""
    integration = ArtemisSwarmIntegrationV2()
    await integration.run()


if __name__ == "__main__":
    asyncio.run(main())