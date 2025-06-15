#!/usr/bin/env python3
# =================================================================================================
# LAUNCHER FOR ADVANCED FLASH LOAN ARBITRAGE SYSTEM - V34
# =================================================================================================

import os
import sys
import argparse
import subprocess
import logging
import time
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("launcher.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("V34Launcher")

def check_dependencies():
    """Check if all required dependencies are installed"""
    logger.info("Checking dependencies...")
    
    # Check Python dependencies
    try:
        import web3
        import yaml
        logger.info("Python dependencies OK")
    except ImportError as e:
        logger.error(f"Missing Python dependency: {e}")
        logger.info("Installing Python dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements_ultimate.txt"])
    
    # Check Node.js dependencies for ZK prover
    if os.path.exists("prover"):
        logger.info("Checking ZK prover dependencies...")
        try:
            # Check if snarkjs is installed
            result = subprocess.run(["snarkjs", "--version"], capture_output=True, text=True)
            logger.info(f"snarkjs version: {result.stdout.strip()}")
        except FileNotFoundError:
            logger.warning("snarkjs not found, installing...")
            subprocess.run(["npm", "install", "-g", "snarkjs"])
        
        # Check if prover has node modules installed
        if not os.path.exists(os.path.join("prover", "node_modules")):
            logger.info("Installing prover dependencies...")
            subprocess.run(["npm", "install"], cwd="prover")

def setup_environment(mode):
    """Setup environment for the specified mode"""
    logger.info(f"Setting up environment for mode: {mode}")
    
    # Load environment variables
    load_dotenv()
    
    # Set operating mode in config
    config_file = "config_ultimate.yaml"
    try:
        import yaml
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Update mode
        if 'system' not in config:
            config['system'] = {}
        config['system']['mode'] = mode
        
        # Write updated config
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        logger.info(f"Updated config with mode: {mode}")
    except Exception as e:
        logger.error(f"Failed to update config: {e}")

def setup_prover():
    """Setup the ZK prover"""
    logger.info("Setting up ZK prover...")
    
    # Create prover directory if it doesn't exist
    if not os.path.exists("prover"):
        logger.info("Creating prover directory...")
        os.makedirs("prover")
    
    # Check if circuit files exist
    circuit_files = ["circuit.circom", "circuit_final.zkey", "generate_witness.js"]
    missing_files = [f for f in circuit_files if not os.path.exists(os.path.join("prover", f))]
    
    if missing_files:
        logger.warning(f"Missing circuit files: {', '.join(missing_files)}")
        logger.info("Please ensure all required circuit files are in the prover directory")

def launch_agent(mode):
    """Launch the V34 agent"""
    logger.info(f"Launching V34 agent in {mode} mode...")
    
    try:
        # Run the agent
        subprocess.run([sys.executable, "python_agent_v34_ultimate.py"])
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
    except Exception as e:
        logger.error(f"Failed to launch agent: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Launch V34 Arbitrage Agent")
    parser.add_argument("--mode", choices=["micro", "max_profit", "institutional"], 
                        default="institutional", help="Operating mode")
    parser.add_argument("--setup-only", action="store_true", 
                        help="Only setup environment without launching agent")
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("ADVANCED FLASH LOAN ARBITRAGE SYSTEM - V34 (LIVE PROVING & HARDENED AGENT)")
    print("=" * 80)
    print(f"Mode: {args.mode}")
    print("=" * 80)
    
    # Check dependencies
    check_dependencies()
    
    # Setup environment
    setup_environment(args.mode)
    
    # Setup prover
    setup_prover()
    
    if not args.setup_only:
        # Launch agent
        launch_agent(args.mode)

if __name__ == "__main__":
    main()