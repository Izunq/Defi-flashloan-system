#!/usr/bin/env python3
"""
🚀 SWARM & PARALLEL AGENT SYSTEM LAUNCHER V2
===========================================

This script launches the Swarm Agent Factory V2 and Parallel Opportunity Coordinator
systems to enable massively parallel arbitrage opportunity detection and execution
using a true swarm intelligence model.

USAGE:
  python start_swarm_system_v2.py [--halal] [--debug] [--agents=500]

OPTIONS:
  --halal     Enable Halal compliance mode
  --debug     Enable debug logging
  --agents=N  Number of initial agents to create (default: 100)

Author: AI Assistant
Version: 2.0
Date: June 2025
"""

import os
import sys
import time
import logging
import argparse
import subprocess
import threading
import yaml
import json
import redis
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/swarm_system_v2.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SwarmSystemLauncherV2")

def update_config(config_path: str, updates: Dict[str, Any]) -> bool:
    """
    Update a YAML configuration file
    
    Args:
        config_path: Path to the configuration file
        updates: Dictionary of updates to apply
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Read existing config
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Apply updates (only top-level keys for simplicity)
        for key, value in updates.items():
            config[key] = value
        
        # Write updated config
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        
        logger.info(f"Updated configuration in {config_path}")
        return True
    except Exception as e:
        logger.error(f"Error updating configuration {config_path}: {e}")
        return False

def start_process(command: str, name: str) -> subprocess.Popen:
    """
    Start a subprocess
    
    Args:
        command: Command to run
        name: Name of the process
        
    Returns:
        Subprocess handle
    """
    logger.info(f"Starting {name}...")
    
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Start threads to monitor output
    def monitor_output(stream, prefix):
        for line in stream:
            logger.info(f"{prefix}: {line.strip()}")
    
    threading.Thread(
        target=monitor_output,
        args=(process.stdout, f"{name} [OUT]"),
        daemon=True
    ).start()
    
    threading.Thread(
        target=monitor_output,
        args=(process.stderr, f"{name} [ERR]"),
        daemon=True
    ).start()
    
    logger.info(f"{name} started with PID {process.pid}")
    return process

def create_initial_agents(redis_client: redis.Redis, num_agents: int, halal_mode: bool = False):
    """
    Create initial agents through the factory
    
    Args:
        redis_client: Redis client
        num_agents: Number of agents to create
        halal_mode: Whether to create only halal-compliant agents
    """
    logger.info(f"Creating {num_agents} initial agents (halal_mode={halal_mode})...")
    
    # Get available templates
    response_channel = "swarm:factory:response:" + str(time.time())
    
    # Request all agents (to get templates from the response)
    redis_client.publish(
        "swarm:factory:commands",
        json.dumps({
            "action": "get_all_agents",
            "response_channel": response_channel
        })
    )
    
    # Wait for response
    pubsub = redis_client.pubsub()
    pubsub.subscribe(response_channel)
    
    templates = []
    for message in pubsub.listen():
        if message["type"] == "message":
            try:
                data = json.loads(message["data"])
                if data.get("action") == "get_all_agents":
                    # Extract templates from agent data
                    agents = data.get("agents", [])
                    for agent in agents:
                        template_id = agent.get("template_id")
                        if template_id and template_id not in templates:
                            templates.append(template_id)
                    break
            except Exception as e:
                logger.error(f"Error processing response: {e}")
    
    pubsub.unsubscribe()
    
    # If no templates found, use default ones
    if not templates:
        if halal_mode:
            templates = ["halal_pair_watcher"]
        else:
            templates = ["eth_usdc_pair_watcher_v2", "whale_watcher_basic"]
    
    # Create agents
    agents_per_template = num_agents // len(templates)
    for template_id in templates:
        for i in range(agents_per_template):
            # Create agent with slightly different parameters
            parameters = {
                "check_interval_seconds": 5 + (i % 5)  # Stagger checks
            }
            
            # Add token pair variations
            if "pair_watcher" in template_id:
                # Create different token pair combinations
                token_pairs = [
                    ["ETH", "USDC"],
                    ["ETH", "DAI"],
                    ["WBTC", "USDC"],
                    ["ETH", "USDT"],
                    ["WBTC", "ETH"]
                ]
                
                parameters["token_pair"] = token_pairs[i % len(token_pairs)]
            
            redis_client.publish(
                "swarm:factory:commands",
                json.dumps({
                    "action": "create_agent",
                    "template_id": template_id,
                    "parameters": parameters
                })
            )
            
            # Small delay to avoid overwhelming the system
            time.sleep(0.01)
    
    logger.info(f"Requested creation of {num_agents} agents")

def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Start Swarm & Parallel Agent System V2")
    parser.add_argument("--halal", action="store_true", help="Enable Halal compliance mode")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--agents", type=int, default=100, help="Number of initial agents to create")
    args = parser.parse_args()
    
    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("logs/swarm", exist_ok=True)
    os.makedirs("logs/coordinator", exist_ok=True)
    os.makedirs("templates/micro_agents", exist_ok=True)
    os.makedirs("data/opportunities", exist_ok=True)
    
    # Set logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Update configurations if needed
    if args.halal:
        logger.info("Enabling Halal compliance mode")
        update_config("config/swarm_factory_config.yaml", {"halal_mode": True})
        update_config("config/parallel_coordinator_config.yaml", {"halal_mode": True})
    
    # Start Redis if not already running
    redis_process = None
    redis_client = None
    try:
        # Check if Redis is running
        redis_check = subprocess.run(
            "redis-cli ping",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if redis_check.returncode != 0 or redis_check.stdout.strip() != "PONG":
            logger.info("Redis not running, starting it...")
            redis_process = start_process("redis-server", "Redis")
            time.sleep(2)  # Give Redis time to start
        
        # Connect to Redis
        redis_client = redis.Redis()
        redis_client.ping()  # Test connection
        logger.info("Connected to Redis successfully")
    except Exception as e:
        logger.error(f"Error checking/starting Redis: {e}")
        return 1
    
    # Start the Swarm Agent Factory V2
    factory_process = start_process(
        "python src/agents/swarm_agent_factory_v2.py",
        "Swarm Agent Factory V2"
    )
    
    # Start the Parallel Opportunity Coordinator
    coordinator_process = start_process(
        "python src/agents/parallel_opportunity_coordinator.py",
        "Parallel Opportunity Coordinator"
    )
    
    # Give the processes time to initialize
    logger.info("Waiting for processes to initialize...")
    time.sleep(5)
    
    # Create initial agents
    if redis_client:
        create_initial_agents(redis_client, args.agents, args.halal)
    
    try:
        logger.info("Swarm & Parallel Agent System V2 started")
        logger.info("Press Ctrl+C to stop")
        
        # Wait for processes to complete (or Ctrl+C)
        factory_process.wait()
        coordinator_process.wait()
    except KeyboardInterrupt:
        logger.info("Stopping Swarm & Parallel Agent System V2...")
    finally:
        # Stop processes
        for process, name in [
            (coordinator_process, "Parallel Opportunity Coordinator"),
            (factory_process, "Swarm Agent Factory V2"),
            (redis_process, "Redis")
        ]:
            if process and process.poll() is None:
                logger.info(f"Stopping {name}...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning(f"{name} did not terminate gracefully, killing...")
                    process.kill()
        
        logger.info("Swarm & Parallel Agent System V2 stopped")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())