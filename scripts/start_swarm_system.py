#!/usr/bin/env python3
"""
🚀 SWARM & PARALLEL AGENT SYSTEM LAUNCHER
=========================================

This script launches the Swarm Agent Factory and Parallel Opportunity Coordinator
systems to enable massively parallel arbitrage opportunity detection and execution.

USAGE:
  python start_swarm_system.py [--halal] [--debug]

OPTIONS:
  --halal    Enable Halal compliance mode
  --debug    Enable debug logging

Author: AI Assistant
Version: 1.0
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
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/swarm_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SwarmSystemLauncher")

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

def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Start Swarm & Parallel Agent System")
    parser.add_argument("--halal", action="store_true", help="Enable Halal compliance mode")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("logs/swarm", exist_ok=True)
    os.makedirs("logs/coordinator", exist_ok=True)
    os.makedirs("templates/micro_bots", exist_ok=True)
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
    except Exception as e:
        logger.error(f"Error checking/starting Redis: {e}")
        return 1
    
    # Start the Swarm Agent Factory
    factory_process = start_process(
        "python src/agents/swarm_agent_factory.py",
        "Swarm Agent Factory"
    )
    
    # Start the Parallel Opportunity Coordinator
    coordinator_process = start_process(
        "python src/agents/parallel_opportunity_coordinator.py",
        "Parallel Opportunity Coordinator"
    )
    
    try:
        logger.info("Swarm & Parallel Agent System started")
        logger.info("Press Ctrl+C to stop")
        
        # Wait for processes to complete (or Ctrl+C)
        factory_process.wait()
        coordinator_process.wait()
    except KeyboardInterrupt:
        logger.info("Stopping Swarm & Parallel Agent System...")
    finally:
        # Stop processes
        for process, name in [
            (coordinator_process, "Parallel Opportunity Coordinator"),
            (factory_process, "Swarm Agent Factory"),
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
        
        logger.info("Swarm & Parallel Agent System stopped")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())