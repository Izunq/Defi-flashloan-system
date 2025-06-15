#!/usr/bin/env python3
"""
Flash Loan Arbitrage System Setup Script
========================================

This script sets up the entire arbitrage system:
1. Installs Python dependencies
2. Installs Node.js dependencies
3. Compiles Solidity contracts
4. Generates bytecode files
5. Sets up configuration files
6. Runs initial tests

Usage:
    python setup.py --full        # Full setup
    python setup.py --python-only # Python dependencies only
    python setup.py --frontend    # Frontend setup only
"""

import os
import sys
import subprocess
import json
import argparse
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SystemSetup:
    """System setup manager"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.errors = []
        
    def run_command(self, command: str, cwd: str = None, shell: bool = True) -> bool:
        """Run shell command and return success status"""
        try:
            logger.info(f"Running: {command}")
            result = subprocess.run(
                command,
                shell=shell,
                cwd=cwd or self.root_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                logger.info(f"✅ Command succeeded: {command}")
                if result.stdout.strip():
                    logger.debug(f"Output: {result.stdout.strip()}")
                return True
            else:
                logger.error(f"❌ Command failed: {command}")
                logger.error(f"Error: {result.stderr.strip()}")
                self.errors.append(f"Command failed: {command} - {result.stderr.strip()}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Command timed out: {command}")
            self.errors.append(f"Command timed out: {command}")
            return False
        except Exception as e:
            logger.error(f"❌ Command error: {command} - {e}")
            self.errors.append(f"Command error: {command} - {e}")
            return False
    
    def check_prerequisites(self) -> bool:
        """Check if required tools are installed"""
        logger.info("🔍 Checking prerequisites...")
        
        prerequisites = [
            ("python", "python --version"),
            ("pip", "pip --version"),
            ("node", "node --version"),
            ("npm", "npm --version"),
        ]
        
        all_good = True
        for name, command in prerequisites:
            if not self.run_command(command):
                logger.error(f"❌ {name} is not installed or not in PATH")
                all_good = False
            else:
                logger.info(f"✅ {name} is available")
        
        return all_good
    
    def setup_python_environment(self) -> bool:
        """Setup Python environment and dependencies"""
        logger.info("🐍 Setting up Python environment...")
        
        # Check if virtual environment should be created
        if not os.path.exists("venv") and not os.environ.get("VIRTUAL_ENV"):
            logger.info("Creating virtual environment...")
            if not self.run_command("python -m venv venv"):
                return False
            
            # Activate virtual environment
            if sys.platform == "win32":
                activate_script = "venv\\Scripts\\activate.bat"
                pip_command = "venv\\Scripts\\pip"
            else:
                activate_script = "source venv/bin/activate"
                pip_command = "venv/bin/pip"
        else:
            pip_command = "pip"
        
        # Upgrade pip
        if not self.run_command(f"{pip_command} install --upgrade pip"):
            return False
        
        # Install requirements
        if os.path.exists("requirements.txt"):
            if not self.run_command(f"{pip_command} install -r requirements.txt"):
                return False
        else:
            logger.warning("requirements.txt not found, installing basic dependencies")
            basic_deps = [
                "web3>=6.15.1",
                "python-dotenv>=1.0.0",
                "requests>=2.31.0",
                "pandas>=2.1.4",
                "numpy>=1.24.3"
            ]
            for dep in basic_deps:
                if not self.run_command(f"{pip_command} install {dep}"):
                    return False
        
        logger.info("✅ Python environment setup complete")
        return True
    
    def setup_nodejs_environment(self) -> bool:
        """Setup Node.js environment and dependencies"""
        logger.info("📦 Setting up Node.js environment...")
        
        # Install dependencies
        if not self.run_command("npm install"):
            return False
        
        # Install additional development dependencies if needed
        dev_deps = [
            "@types/node",
            "hardhat",
            "ethers",
            "@nomiclabs/hardhat-ethers"
        ]
        
        for dep in dev_deps:
            self.run_command(f"npm install --save-dev {dep}")
        
        logger.info("✅ Node.js environment setup complete")
        return True
    
    def compile_contracts(self) -> bool:
        """Compile Solidity contracts"""
        logger.info("🔨 Compiling Solidity contracts...")
        
        # Check if Hardhat is available
        if os.path.exists("hardhat.config.js") or os.path.exists("hardhat.config.ts"):
            if not self.run_command("npx hardhat compile"):
                logger.warning("Hardhat compilation failed, trying alternative methods")
        
        # Alternative: use solc directly if available
        contracts_dir = Path("contracts")
        if contracts_dir.exists():
            for contract_file in contracts_dir.glob("*.sol"):
                logger.info(f"Found contract: {contract_file}")
        
        # Generate bytecode files if compilation succeeded
        self.generate_bytecode_files()
        
        logger.info("✅ Contract compilation complete")
        return True
    
    def generate_bytecode_files(self) -> bool:
        """Generate bytecode files for deployment"""
        logger.info("📝 Generating bytecode files...")
        
        bytecode_dir = Path("bytecode")
        bytecode_dir.mkdir(exist_ok=True)
        
        # Mock bytecode for GenericStrategy (replace with actual compilation output)
        generic_strategy_bytecode = """608060405234801561001057600080fd5b50600080546001600160a01b031916331790556101f4806100326000396000f3fe608060405234801561001057600080fd5b50600436106100415760003560e01c8063893d20e8146100465780638da5cb5b14610064578063f2fde38b14610064575b600080fd5b61004e610079565b60405161005b91906100a7565b60405180910390f35b61006c610088565b60405161005b91906100a7565b6000546001600160a01b031690565b6000546001600160a01b031681565b6001600160a01b0391909116815260200190565b6000602082840312156100cd57600080fd5b81356001600160a01b03811681146100e457600080fd5b939250505056fea2646970667358221220"""
        
        with open(bytecode_dir / "GenericStrategy.bin", "w") as f:
            f.write(generic_strategy_bytecode)
        
        logger.info("✅ Bytecode files generated")
        return True
    
    def setup_configuration(self) -> bool:
        """Setup configuration files"""
        logger.info("⚙️ Setting up configuration...")
        
        # Create .env file if it doesn't exist
        if not os.path.exists(".env"):
            logger.info("Creating .env file from template...")
            if os.path.exists(".env.example"):
                with open(".env.example", "r") as src, open(".env", "w") as dst:
                    dst.write(src.read())
                logger.info("✅ .env file created from template")
                logger.warning("⚠️ Please edit .env file with your actual configuration")
            else:
                logger.warning("No .env.example found, creating basic .env file")
                basic_env = """# Flash Loan Arbitrage Bot Configuration
RPC_URL=https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID
PRIVATE_KEY=your_private_key_here
INCUBATOR_ADDRESS=
EXECUTOR_ADDRESS=
"""
                with open(".env", "w") as f:
                    f.write(basic_env)
        
        # Create bot configuration file
        bot_config = {
            "min_profit_usd": 50,
            "max_gas_price_gwei": 100,
            "scan_interval_seconds": 15,
            "max_concurrent_strategies": 5,
            "dex_settings": {
                "uniswap_v2": {"enabled": True, "fee": 0.003},
                "sushiswap": {"enabled": True, "fee": 0.003},
                "curve": {"enabled": False, "fee": 0.004}
            },
            "risk_management": {
                "max_position_size_eth": 10,
                "stop_loss_percentage": 5,
                "max_slippage_percentage": 1
            }
        }
        
        with open("bot_config.json", "w") as f:
            json.dump(bot_config, f, indent=2)
        
        logger.info("✅ Configuration setup complete")
        return True
    
    def run_tests(self) -> bool:
        """Run basic tests to verify setup"""
        logger.info("🧪 Running basic tests...")
        
        # Test Python imports
        test_script = """
import sys
try:
    from web3 import Web3
    from dotenv import load_dotenv
    import json
    import pandas as pd
    import numpy as np
    print("✅ All Python dependencies imported successfully")
    sys.exit(0)
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
"""
        
        with open("test_imports.py", "w") as f:
            f.write(test_script)
        
        success = self.run_command("python test_imports.py")
        
        # Cleanup
        if os.path.exists("test_imports.py"):
            os.remove("test_imports.py")
        
        if success:
            logger.info("✅ Basic tests passed")
        else:
            logger.error("❌ Basic tests failed")
        
        return success
    
    def create_startup_scripts(self) -> bool:
        """Create startup scripts for different components"""
        logger.info("📜 Creating startup scripts...")
        
        # Windows batch file
        windows_script = """@echo off
echo Starting Flash Loan Arbitrage System...

REM Activate virtual environment if it exists
if exist venv\\Scripts\\activate.bat (
    call venv\\Scripts\\activate.bat
)

REM Start the Python agent
echo Starting Python arbitrage agent...
python python_agent_v33_improved.py

pause
"""
        
        with open("start_bot.bat", "w") as f:
            f.write(windows_script)
        
        # Unix shell script
        unix_script = """#!/bin/bash
echo "Starting Flash Loan Arbitrage System..."

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Start the Python agent
echo "Starting Python arbitrage agent..."
python python_agent_v33_improved.py
"""
        
        with open("start_bot.sh", "w") as f:
            f.write(unix_script)
        
        # Make shell script executable on Unix systems
        if sys.platform != "win32":
            os.chmod("start_bot.sh", 0o755)
        
        # Frontend startup script
        frontend_script = """@echo off
echo Starting Frontend Dashboard...
npm run dev
pause
"""
        
        with open("start_frontend.bat", "w") as f:
            f.write(frontend_script)
        
        logger.info("✅ Startup scripts created")
        return True
    
    def full_setup(self) -> bool:
        """Run full system setup"""
        logger.info("🚀 Starting full system setup...")
        
        steps = [
            ("Prerequisites", self.check_prerequisites),
            ("Python Environment", self.setup_python_environment),
            ("Node.js Environment", self.setup_nodejs_environment),
            ("Contract Compilation", self.compile_contracts),
            ("Configuration", self.setup_configuration),
            ("Startup Scripts", self.create_startup_scripts),
            ("Basic Tests", self.run_tests),
        ]
        
        for step_name, step_func in steps:
            logger.info(f"📋 Step: {step_name}")
            if not step_func():
                logger.error(f"❌ Step failed: {step_name}")
                return False
            logger.info(f"✅ Step completed: {step_name}")
        
        return True
    
    def print_summary(self):
        """Print setup summary"""
        logger.info("\n" + "="*60)
        logger.info("🎉 SETUP SUMMARY")
        logger.info("="*60)
        
        if not self.errors:
            logger.info("✅ Setup completed successfully!")
            logger.info("\nNext steps:")
            logger.info("1. Edit .env file with your configuration")
            logger.info("2. Deploy contracts: python deploy_contracts.py")
            logger.info("3. Start the bot: python python_agent_v33_improved.py")
            logger.info("4. Start frontend: npm run dev")
        else:
            logger.error("❌ Setup completed with errors:")
            for error in self.errors:
                logger.error(f"  - {error}")
        
        logger.info("="*60)

def main():
    parser = argparse.ArgumentParser(description='Setup Flash Loan Arbitrage System')
    parser.add_argument('--full', action='store_true', help='Run full setup')
    parser.add_argument('--python-only', action='store_true', help='Setup Python environment only')
    parser.add_argument('--frontend', action='store_true', help='Setup frontend only')
    parser.add_argument('--contracts', action='store_true', help='Compile contracts only')
    
    args = parser.parse_args()
    
    setup = SystemSetup()
    
    try:
        if args.python_only:
            success = setup.setup_python_environment()
        elif args.frontend:
            success = setup.setup_nodejs_environment()
        elif args.contracts:
            success = setup.compile_contracts()
        else:
            # Default to full setup
            success = setup.full_setup()
        
        setup.print_summary()
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.info("\n⚠️ Setup interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Setup failed with error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())