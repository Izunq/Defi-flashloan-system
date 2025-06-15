#!/usr/bin/env python3
# =================================================================================================
# SETUP SCRIPT FOR V34 ARBITRAGE SYSTEM
# =================================================================================================

import os
import sys
import subprocess
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("setup.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("V34Setup")

def install_python_dependencies():
    """Install Python dependencies"""
    logger.info("Installing Python dependencies...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements_ultimate.txt"], check=True)
        logger.info("Python dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install Python dependencies: {e}")
        return False

def install_node_dependencies():
    """Install Node.js dependencies"""
    logger.info("Installing Node.js dependencies...")
    
    # Check if Node.js is installed
    try:
        subprocess.run(["node", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("Node.js is not installed. Please install Node.js and npm first.")
        return False
    
    # Install global dependencies
    try:
        logger.info("Installing snarkjs globally...")
        subprocess.run(["npm", "install", "-g", "snarkjs"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install snarkjs: {e}")
        return False
    
    # Install prover dependencies
    prover_dir = Path("prover")
    if prover_dir.exists():
        try:
            logger.info("Installing prover dependencies...")
            subprocess.run(["npm", "install"], cwd=prover_dir, check=True)
            logger.info("Prover dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install prover dependencies: {e}")
            return False
    else:
        logger.warning(f"Prover directory does not exist: {prover_dir}")
    
    return True

def setup_environment():
    """Setup environment variables"""
    logger.info("Setting up environment...")
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        logger.info("Creating .env file from .env.example...")
        
        if os.path.exists(".env.example"):
            with open(".env.example", "r") as example_file:
                example_content = example_file.read()
            
            with open(".env", "w") as env_file:
                env_file.write(example_content)
            
            logger.info(".env file created. Please edit it with your actual values.")
        else:
            logger.warning(".env.example file not found. Please create .env file manually.")
    else:
        logger.info(".env file already exists")
    
    return True

def setup_prover():
    """Setup ZK prover"""
    logger.info("Setting up ZK prover...")
    
    prover_dir = Path("prover")
    
    # Create prover directory if it doesn't exist
    if not prover_dir.exists():
        logger.info(f"Creating prover directory: {prover_dir}")
        prover_dir.mkdir(exist_ok=True)
    
    # Check if circuit files exist
    circuit_files = ["circuit.circom", "circuit_final.zkey", "generate_witness.js"]
    missing_files = [f for f in circuit_files if not (prover_dir / f).exists()]
    
    if missing_files:
        logger.warning(f"Missing circuit files: {', '.join(missing_files)}")
        logger.info("These files should have been created during the installation process.")
    else:
        logger.info("All circuit files are present")
    
    return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Setup V34 Arbitrage System")
    parser.add_argument("--skip-python", action="store_true", help="Skip Python dependencies installation")
    parser.add_argument("--skip-node", action="store_true", help="Skip Node.js dependencies installation")
    parser.add_argument("--skip-env", action="store_true", help="Skip environment setup")
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("SETUP SCRIPT FOR V34 ARBITRAGE SYSTEM")
    print("=" * 80)
    
    success = True
    
    # Install Python dependencies
    if not args.skip_python:
        success = install_python_dependencies() and success
    
    # Install Node.js dependencies
    if not args.skip_node:
        success = install_node_dependencies() and success
    
    # Setup environment
    if not args.skip_env:
        success = setup_environment() and success
    
    # Setup prover
    success = setup_prover() and success
    
    if success:
        print("\n✅ Setup completed successfully")
        print("\nNext steps:")
        print("1. Edit the .env file with your actual values")
        print("2. Run the agent with: python launch_v34_agent.py")
    else:
        print("\n❌ Setup completed with errors. Please check the logs.")

if __name__ == "__main__":
    main()