#!/usr/bin/env python3
"""
🧠 ARTEMIS AI CORE - SWARM INTEGRATION LAUNCHER
==============================================

This script launches the Artemis AI Core integration with the Swarm Agent Factory
and Parallel Opportunity Coordinator.

USAGE:
  python start_artemis_swarm_integration.py [--halal] [--debug]

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
import asyncio
import yaml
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/artemis_swarm_integration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ArtemisSwarmIntegrationLauncher")

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

async def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Start Artemis Swarm Integration")
    parser.add_argument("--halal", action="store_true", help="Enable Halal compliance mode")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("logs/artemis", exist_ok=True)
    
    # Set logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Update configurations if needed
    if args.halal:
        logger.info("Enabling Halal compliance mode")
        update_config("config/artemis_swarm_integration.yaml", {"halal_mode": True})
    
    # Import the integration module
    try:
        from artemis_core.swarm_integration_v2 import ArtemisSwarmIntegrationV2
    except ImportError as e:
        logger.error(f"Failed to import ArtemisSwarmIntegrationV2: {e}")
        return 1
    
    # Create and run the integration
    try:
        logger.info("Starting Artemis Swarm Integration")
        integration = ArtemisSwarmIntegrationV2()
        await integration.run()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down")
    except Exception as e:
        logger.error(f"Error running Artemis Swarm Integration: {e}")
        return 1
    
    logger.info("Artemis Swarm Integration stopped")
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))