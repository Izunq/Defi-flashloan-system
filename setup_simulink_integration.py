#!/usr/bin/env python3
"""
🚀 Simulink Integration Setup for DeFi Arbitrage System
Automated setup and testing of Simulink model-based design integration
Author: DeFi Arbitrage System
Date: June 17, 2025
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimulinkSetup:
    """
    Automated Simulink integration setup for DeFi Arbitrage System
    """
    
    def __init__(self, project_root: str = None):
        """Initialize setup"""
        self.project_root = project_root or os.getcwd()
        self.simulink_dir = os.path.join(self.project_root, "simulink")
        self.models_dir = os.path.join(self.simulink_dir, "models")
        self.scripts_dir = os.path.join(self.simulink_dir, "scripts")
        
        logger.info(f"🎯 Simulink Setup initialized for project: {self.project_root}")
    
    def check_prerequisites(self) -> bool:
        """Check if prerequisites are installed"""
        logger.info("🔍 Checking prerequisites...")
        
        prerequisites_ok = True
        
        # Check Python packages
        required_packages = [
            "numpy", "pandas", "matplotlib", "scipy"
        ]
        
        for package in required_packages:
            try:
                __import__(package)
                logger.info(f"✅ {package} is installed")
            except ImportError:
                logger.warning(f"❌ {package} is not installed")
                prerequisites_ok = False
        
        # Check MATLAB availability
        try:
            import matlab.engine
            logger.info("✅ MATLAB Engine for Python is available")
        except ImportError:
            logger.warning("❌ MATLAB Engine for Python not found")
            logger.info("💡 Install with: pip install matlabengine")
            prerequisites_ok = False
        
        # Check if MATLAB is installed
        matlab_installed = self._check_matlab_installation()
        if matlab_installed:
            logger.info("✅ MATLAB installation found")
        else:
            logger.warning("❌ MATLAB installation not found")
            prerequisites_ok = False
        
        return prerequisites_ok
    
    def _check_matlab_installation(self) -> bool:
        """Check if MATLAB is installed"""
        matlab_paths = [
            r"C:\Program Files\MATLAB",
            r"C:\Program Files (x86)\MATLAB",
            "/usr/local/MATLAB",  # Linux
            "/Applications/MATLAB"  # macOS
        ]
        
        for path in matlab_paths:
            if os.path.exists(path):
                return True
        
        return False
    
    def create_directory_structure(self):
        """Create Simulink directory structure"""
        logger.info("📁 Creating directory structure...")
        
        directories = [
            self.simulink_dir,
            self.models_dir,
            self.scripts_dir,
            os.path.join(self.models_dir, "functions"),
            os.path.join(self.simulink_dir, "data"),
            os.path.join(self.simulink_dir, "tests"),
            os.path.join(self.simulink_dir, "docs")
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"📁 Created: {directory}")
    
    def install_python_packages(self):
        """Install required Python packages"""
        logger.info("📦 Installing Python packages...")
        
        packages = [
            "numpy>=1.21.0",
            "pandas>=1.3.0",
            "matplotlib>=3.4.0",
            "scipy>=1.7.0",
            "scikit-learn>=1.0.0",
            "plotly>=5.0.0"
        ]
        
        for package in packages:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", package], 
                             check=True, capture_output=True, text=True)
                logger.info(f"✅ Installed: {package}")
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Failed to install {package}: {e}")
    
    def create_matlab_startup_script(self):
        """Create MATLAB startup script for the project"""
        logger.info("🔧 Creating MATLAB startup script...")
        
        startup_script = f"""% MATLAB Startup Script for DeFi Arbitrage System
% Automatically configures paths and settings for Simulink integration
% Generated: {os.path.basename(__file__)}

fprintf('🚀 DeFi Arbitrage System - Simulink Integration\\n');

% Add project paths
project_root = '{self.project_root.replace(os.sep, '/')}';
simulink_dir = fullfile(project_root, 'simulink');
models_dir = fullfile(simulink_dir, 'models');
scripts_dir = fullfile(simulink_dir, 'scripts');
functions_dir = fullfile(models_dir, 'functions');

% Add paths to MATLAB search path
addpath(simulink_dir);
addpath(models_dir);
addpath(scripts_dir);
addpath(functions_dir);

fprintf('📁 Added Simulink directories to MATLAB path\\n');

% Configure Simulink preferences
set_param(0, 'SimulinkDefaultConfigSet', 'Configuration1');

% Set default solver for real-time applications
set_param(0, 'DefaultBlockDiagramSolver', 'ode45');

% Configure for code generation
set_param(0, 'DefaultParameterBehavior', 'Tunable');

% Display configuration
fprintf('⚙️  MATLAB configured for DeFi Arbitrage System\\n');
fprintf('   Models directory: %s\\n', models_dir);
fprintf('   Scripts directory: %s\\n', scripts_dir);
fprintf('   Functions directory: %s\\n', functions_dir);

% Load custom functions
if exist(functions_dir, 'dir')
    fprintf('🔧 Loading custom functions...\\n');
    addpath(functions_dir);
end

fprintf('✅ Simulink integration ready!\\n');
"""
        
        startup_path = os.path.join(self.simulink_dir, "startup.m")
        with open(startup_path, 'w') as f:
            f.write(startup_script)
        
        logger.info(f"✅ Created MATLAB startup script: {startup_path}")
    
    def create_test_script(self):
        """Create test script for Simulink integration"""
        logger.info("🧪 Creating test script...")
        
        test_script = """#!/usr/bin/env python3
\"\"\"
Test script for Simulink integration
\"\"\"

import sys
import os
import time
import numpy as np
from datetime import datetime

# Add simulink directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from simulink_bridge import SimulinkBridge, MarketData, create_sample_market_data
    
    def test_simulink_integration():
        print("🧪 Testing Simulink Integration...")
        
        # Test 1: Bridge initialization
        print("\\n1️⃣  Testing bridge initialization...")
        try:
            bridge = SimulinkBridge()
            print("✅ Bridge initialized successfully")
        except Exception as e:
            print(f"❌ Bridge initialization failed: {e}")
            return False
        
        # Test 2: Sample data creation
        print("\\n2️⃣  Testing sample data creation...")
        try:
            sample_data = create_sample_market_data()
            print(f"✅ Sample data created: ETH spread ${sample_data.price_feed_2 - sample_data.price_feed_1:.2f}")
        except Exception as e:
            print(f"❌ Sample data creation failed: {e}")
            return False
        
        # Test 3: Model configuration
        print("\\n3️⃣  Testing model configuration...")
        try:
            model_count = len(bridge.models)
            print(f"✅ {model_count} models configured")
            for model_name in bridge.models:
                print(f"   📊 {model_name}")
        except Exception as e:
            print(f"❌ Model configuration test failed: {e}")
            return False
        
        # Test 4: Cleanup
        print("\\n4️⃣  Testing cleanup...")
        try:
            bridge.cleanup()
            print("✅ Cleanup completed")
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
            return False
        
        print("\\n🎉 All tests passed!")
        return True
    
    if __name__ == "__main__":
        success = test_simulink_integration()
        sys.exit(0 if success else 1)

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure MATLAB Engine is installed: pip install matlabengine")
    sys.exit(1)
"""
        
        test_path = os.path.join(self.simulink_dir, "tests", "test_integration.py")
        with open(test_path, 'w') as f:
            f.write(test_script)
        
        logger.info(f"✅ Created test script: {test_path}")
    
    def create_documentation(self):
        """Create documentation for Simulink integration"""
        logger.info("📚 Creating documentation...")
        
        readme_content = f"""# Simulink Integration for DeFi Arbitrage System

## Overview

This directory contains the Simulink integration for model-based design of trading strategies, real-time market simulation, and advanced control systems.

## Directory Structure

```
simulink/
├── models/                 # Simulink models (.slx files)
│   ├── functions/         # Custom MATLAB functions
│   ├── Arbitrage_Strategy_Model.slx
│   ├── Market_Dynamics_Model.slx
│   ├── Risk_Controller_Model.slx
│   └── Signal_Processing_Model.slx
├── scripts/               # MATLAB scripts
│   └── create_simulink_models.m
├── data/                  # Data files for simulation
├── tests/                 # Test scripts
│   └── test_integration.py
├── docs/                  # Documentation
├── simulink_bridge.py     # Python-Simulink bridge
└── startup.m             # MATLAB startup script
```

## Quick Start

1. **Install Prerequisites**:
   ```bash
   pip install matlabengine numpy pandas matplotlib scipy
   ```

2. **Run Setup**:
   ```bash
   python setup_simulink_integration.py
   ```

3. **Start MATLAB and run**:
   ```matlab
   run('simulink/startup.m')
   create_simulink_models()
   ```

4. **Test Integration**:
   ```bash
   python simulink/tests/test_integration.py
   ```

## Model Descriptions

### Arbitrage Strategy Model
- **Purpose**: Detect arbitrage opportunities and calculate optimal trade parameters
- **Inputs**: Price feeds from multiple exchanges, liquidity data, gas prices
- **Outputs**: Trade signals, position sizes, expected profits

### Market Dynamics Model
- **Purpose**: Simulate realistic market behavior and price movements
- **Inputs**: Base prices, trading volumes, market impact factors
- **Outputs**: Simulated prices, liquidity depth, slippage estimates

### Risk Controller Model
- **Purpose**: Manage portfolio risk and position sizing
- **Inputs**: Portfolio value, position sizes, market volatility
- **Outputs**: Risk-adjusted positions, risk metrics, emergency stops

### Signal Processing Model
- **Purpose**: Filter and analyze market data for patterns
- **Inputs**: Raw price data, volume data
- **Outputs**: Filtered signals, technical indicators, anomaly alerts

## Usage Examples

### Basic Integration

```python
from simulink_bridge import SimulinkBridge, MarketData

# Initialize bridge
bridge = SimulinkBridge()

# Create market data
market_data = MarketData(
    timestamp=datetime.now(),
    price_feed_1=3000.0,
    price_feed_2=3001.0,
    liquidity_data={{"eth_usdc": 1000000.0}},
    gas_price=50.0,
    volume=1000000.0,
    volatility=0.02
)

# Process through Simulink models
signals = bridge.process_market_data(market_data)

if signals:
    print(f"Trade Signal: {{signals.trade_signal}}")
    print(f"Position Size: ${{signals.position_size:.2f}}")
    print(f"Expected Profit: ${{signals.expected_profit:.2f}}")
```

### Real-Time Processing

```python
# Start continuous processing
bridge.start_continuous_processing()

# Add market data to queue
bridge.add_market_data(market_data)

# Get trading signals
signals = bridge.get_trading_signals()

# Stop processing
bridge.stop_continuous_processing()
```

## Configuration

Model parameters can be configured in the bridge initialization or through MATLAB workspace variables.

## Troubleshooting

1. **MATLAB Engine Issues**:
   - Ensure MATLAB is installed and licensed
   - Install MATLAB Engine: `pip install matlabengine`
   - Check MATLAB version compatibility

2. **Model Loading Issues**:
   - Verify .slx files exist in models directory
   - Check MATLAB path configuration
   - Ensure required toolboxes are installed

3. **Performance Issues**:
   - Adjust sample times in model configurations
   - Consider using Simulink Real-Time for hardware deployment
   - Optimize model complexity for real-time requirements

## Advanced Features

- **Hardware-in-the-Loop**: Deploy models to real-time targets
- **Code Generation**: Generate C/C++ code for embedded deployment
- **Model Verification**: Use Simulink Design Verifier for formal verification
- **Parallel Computing**: Utilize MATLAB Parallel Computing Toolbox

## Support

For support and questions:
- Check documentation in `docs/SIMULINK_INTEGRATION_ARCHITECTURE.md`
- Review test scripts in `tests/` directory
- Consult MATLAB/Simulink documentation

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        readme_path = os.path.join(self.simulink_dir, "README.md")
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        
        logger.info(f"✅ Created documentation: {readme_path}")
    
    def run_setup(self):
        """Run complete setup process"""
        logger.info("🚀 Starting Simulink Integration Setup...")
        
        try:
            # Step 1: Check prerequisites
            logger.info("\\n" + "="*50)
            logger.info("STEP 1: Checking Prerequisites")
            logger.info("="*50)
            
            if not self.check_prerequisites():
                logger.warning("⚠️  Some prerequisites are missing. Installation will continue but may not work properly.")
            
            # Step 2: Create directory structure
            logger.info("\\n" + "="*50)
            logger.info("STEP 2: Creating Directory Structure")
            logger.info("="*50)
            
            self.create_directory_structure()
            
            # Step 3: Install Python packages
            logger.info("\\n" + "="*50)
            logger.info("STEP 3: Installing Python Packages")
            logger.info("="*50)
            
            self.install_python_packages()
            
            # Step 4: Create MATLAB startup script
            logger.info("\\n" + "="*50)
            logger.info("STEP 4: Creating MATLAB Configuration")
            logger.info("="*50)
            
            self.create_matlab_startup_script()
            
            # Step 5: Create test script
            logger.info("\\n" + "="*50)
            logger.info("STEP 5: Creating Test Scripts")
            logger.info("="*50)
            
            self.create_test_script()
            
            # Step 6: Create documentation
            logger.info("\\n" + "="*50)
            logger.info("STEP 6: Creating Documentation")
            logger.info("="*50)
            
            self.create_documentation()
            
            # Summary
            logger.info("\\n" + "="*50)
            logger.info("🎉 SETUP COMPLETED SUCCESSFULLY!")
            logger.info("="*50)
            
            logger.info("\\n📋 Next Steps:")
            logger.info("1. Start MATLAB and run: run('simulink/startup.m')")
            logger.info("2. Create Simulink models: run('simulink/scripts/create_simulink_models.m')")
            logger.info("3. Test integration: python simulink/tests/test_integration.py")
            logger.info("4. Review documentation in simulink/README.md")
            
            logger.info(f"\\n📁 Simulink integration installed in: {self.simulink_dir}")
            
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            raise

def main():
    """Main function"""
    print("🚀 Simulink Integration Setup for DeFi Arbitrage System")
    print("=" * 60)
    
    # Initialize setup
    setup = SimulinkSetup()
    
    try:
        # Run setup process
        setup.run_setup()
        
    except KeyboardInterrupt:
        logger.info("\\n⏹️  Setup interrupted by user")
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
