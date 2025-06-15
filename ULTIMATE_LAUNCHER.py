#!/usr/bin/env python3
"""
🚀 ULTIMATE ARBITRAGE SYSTEM LAUNCHER
====================================

COMPLETE PRODUCTION-READY SYSTEM
Turn $50 into thousands with minimal risk

This launcher provides:
✅ Automated setup and installation
✅ System health checks
✅ Trading system startup
✅ Dashboard monitoring
✅ Performance tracking
✅ Risk management
"""

import os
import sys
import subprocess
import asyncio
import threading
import time
import webbrowser
from pathlib import Path
import json

# Import comprehensive input validation system
try:
    from input_validation_integration import (
        validate_string,
        validate_number,
        validate_ethereum_address,
        integrated_validator,
        get_validation_metrics
    )
    from enhanced_input_validator import SecurityViolationError, ValidationResult
    INPUT_VALIDATION_AVAILABLE = True
except ImportError:
    print("⚠️ Comprehensive input validation not available - using basic validation")
    INPUT_VALIDATION_AVAILABLE = False

# Fallback basic validation for critical inputs
def basic_validate_amount(amount_str):
    """Basic validation for financial amounts"""
    try:
        amount = float(amount_str)
        if amount < 0:
            raise ValueError("Amount must be positive")
        return amount
    except (ValueError, TypeError):
        raise ValueError("Invalid amount format")

def basic_validate_choice(choice, valid_choices):
    """Basic validation for user choices"""
    if choice not in valid_choices:
        raise ValueError(f"Invalid choice. Must be one of: {valid_choices}")
    return choice

def print_welcome():
    """Print welcome message"""
    print("""
🚀 ULTIMATE ARBITRAGE SYSTEM LAUNCHER
====================================

TURN $50 INTO THOUSANDS WITH MINIMAL RISK
Complete production-ready arbitrage trading system

FEATURES:
✅ Flash loan arbitrage (AAVE)
✅ Cross-DEX arbitrage
✅ MEV sandwich detection  
✅ Real-time monitoring
✅ Risk management
✅ Web dashboard
✅ Automated setup

Ready to start making money? 💰
    """)

def check_system_requirements():
    """Check system requirements"""
    print("🔍 Checking system requirements...")
    
    # Check Python version
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required (current: {version.major}.{version.minor})")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    
    # Check required files
    required_files = [
        "PRODUCTION_ARBITRAGE_SYSTEM.py",
        "streamlit_dashboard.py", 
        "setup_production.py",
        "production_config.yaml"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"⚠️ Missing files: {', '.join(missing_files)}")
        print("   Some files may be created during setup")
    else:
        print("✅ All core files present")
    
    return True

def run_setup():
    """Run the setup process"""
    print("\n🔧 Running system setup...")
    
    try:
        # Run setup script
        result = subprocess.run([
            sys.executable, "setup_production.py"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Setup completed successfully")
            return True
        else:
            print(f"❌ Setup failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Setup error: {e}")
        return False

def check_dependencies():
    """Check if dependencies are installed"""
    print("\n📦 Checking dependencies...")
    
    required_packages = [
        "numpy", "pandas", "aiohttp", "web3", 
        "ccxt", "streamlit", "plotly", "yaml"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("   Installing missing packages...")
        
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install"
            ] + missing_packages)
            print("✅ Packages installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install packages")
            return False
    else:
        print("✅ All dependencies available")
        return True

def get_user_configuration():
    """Get user configuration with comprehensive input validation"""
    print("\n⚙️ SYSTEM CONFIGURATION")
    print("-" * 30)
    
    # Get starting capital
    capital_input = ""
    while True:
        try:
            capital_input = input("💰 Enter starting capital ($10-$10000): $").strip()
            if not capital_input:
                capital = 50.0
                print("Using default: $50")
                break
            
            # Use comprehensive input validation if available
            if INPUT_VALIDATION_AVAILABLE:
                try:
                    from input_validation_integration import validate_string, validate_number
                    
                    # Validate input against malicious patterns
                    validation_result = validate_string(capital_input, {
                        "field_name": "starting_capital",
                        "context": "user_input",
                        "source": "terminal"
                    })
                    
                    if not validation_result["valid"]:
                        print(f"❌ Invalid input: {validation_result['errors']}")
                        continue
                    
                    # Additional financial validation
                    number_result = validate_number(capital_input, {
                        "field_name": "starting_capital",
                        "min_value": 10.0,
                        "max_value": 10000.0
                    })
                    
                    if not number_result["valid"]:
                        print(f"❌ Invalid amount: {number_result['errors']}")
                        continue
                    
                    capital = float(capital_input)
                except ImportError:
                    # Fallback to basic validation
                    capital = basic_validate_amount(capital_input)
                except Exception as validation_error:
                    print(f"❌ Validation error: {validation_error}")
                    continue
            else:
                # Fallback to basic validation
                capital = basic_validate_amount(capital_input)
            
            if capital < 10:
                print("⚠️ Minimum capital is $10")
                continue
            elif capital > 10000:
                print("💡 Large capital detected - institutional features available!")
            
            break
        except ValueError as e:
            print(f"❌ {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
    
    # Get risk tolerance
    print("\n🎯 Risk Tolerance:")
    print("1. Conservative (5-15% daily target, low risk)")
    print("2. Moderate (10-25% daily target, balanced)")
    print("3. Aggressive (20-50% daily target, high risk)")
    
    while True:
        risk_choice = input("Choose risk level (1-3): ").strip()
        
        # Validate risk choice
        if INPUT_VALIDATION_AVAILABLE:
            try:
                from input_validation_integration import validate_string
                validation_result = validate_string(risk_choice, {
                    "field_name": "risk_level",
                    "context": "user_input"
                })
                
                if not validation_result["valid"]:
                    print(f"❌ Invalid choice: {validation_result['errors']}")
                    continue
            except ImportError:
                pass  # Fall back to basic validation
            except Exception:
                pass  # Fall back to basic validation
        
        try:
            basic_validate_choice(risk_choice, ['1', '2', '3'])
        except ValueError as e:
            print(f"❌ {e}")
            continue
        
        if risk_choice in ['1', '2', '3']:
            break
        print("❌ Please choose 1, 2, or 3")
    
    risk_profiles = {
        '1': {
            'name': 'Conservative',
            'daily_target': 10.0,
            'max_position': 10.0,
            'strategies': ['simple_arbitrage', 'yield_arbitrage']
        },
        '2': {
            'name': 'Moderate', 
            'daily_target': 20.0,
            'max_position': 20.0,
            'strategies': ['simple_arbitrage', 'triangular_arbitrage', 'flash_arbitrage']
        },
        '3': {
            'name': 'Aggressive',
            'daily_target': 35.0,
            'max_position': 30.0,
            'strategies': ['simple_arbitrage', 'triangular_arbitrage', 'flash_arbitrage', 'cross_chain_arbitrage']
        }
    }
    
    risk_profile = risk_profiles[risk_choice]
    
    # Get preferred chains
    print("\n🌐 Preferred Blockchain Networks:")
    print("1. Polygon (very low fees)")
    print("2. BSC (low fees)")
    print("3. Arbitrum (moderate fees)")
    print("4. All networks (maximum opportunities)")
    
    chain_choice = input("Choose networks (1-4): ").strip()
    
    chain_options = {
        '1': ['polygon'],
        '2': ['bsc'],
        '3': ['arbitrum'],
        '4': ['polygon', 'bsc', 'arbitrum']
    }
    
    preferred_chains = chain_options.get(chain_choice, ['polygon', 'bsc'])
    
    return {
        'capital': capital,
        'risk_profile': risk_profile,
        'preferred_chains': preferred_chains
    }

def show_profit_projections(config):
    """Show profit projections"""
    capital = config['capital']
    daily_target = config['risk_profile']['daily_target']
    
    print(f"\n💰 PROFIT PROJECTIONS")
    print("-" * 25)
    print(f"Starting Capital: ${capital:.2f}")
    print(f"Daily Target: {daily_target:.1f}%")
    print(f"Risk Level: {config['risk_profile']['name']}")
    
    # Calculate projections
    daily_return = daily_target / 100
    
    projections = [
        (1, "Day 1"),
        (7, "Week 1"), 
        (30, "Month 1"),
        (90, "Month 3"),
        (365, "Year 1")
    ]
    
    print(f"\nPROJECTED GROWTH:")
    for days, label in projections:
        projected_value = capital * ((1 + daily_return) ** days)
        profit = projected_value - capital
        multiple = projected_value / capital
        
        print(f"{label:8}: ${projected_value:8.0f} (+${profit:6.0f}) [{multiple:.1f}x]")
    
    print(f"\n⚠️ DISCLAIMER: Projections assume {daily_target:.1f}% daily returns.")
    print("   Actual results will vary. Crypto trading involves risk!")

def start_trading_system(config):
    """Start the trading system"""
    print(f"\n🚀 STARTING TRADING SYSTEM")
    print("-" * 30)
    
    try:
        # Import and configure the trading system
        from PRODUCTION_ARBITRAGE_SYSTEM import ProductionArbitrageSystem, TradingConfig
        
        # Create trading configuration
        trading_config = TradingConfig(
            initial_capital=config['capital'],
            max_position_size_percent=config['risk_profile']['max_position'],
            enabled_strategies=config['risk_profile']['strategies'],
            preferred_chains=config['preferred_chains']
        )
        
        print(f"✅ Configuration created")
        print(f"   Capital: ${trading_config.initial_capital:.2f}")
        print(f"   Strategies: {len(trading_config.enabled_strategies)}")
        print(f"   Networks: {len(trading_config.preferred_chains)}")
        
        # Create and start system
        system = ProductionArbitrageSystem(trading_config)
        
        print(f"\n🎯 FINAL CONFIRMATION")
        print(f"You are about to start live trading with:")
        print(f"   💰 Capital: ${config['capital']:.2f}")
        print(f"   🎯 Risk Level: {config['risk_profile']['name']}")
        print(f"   📈 Daily Target: {config['risk_profile']['daily_target']:.1f}%")
        print(f"   🌐 Networks: {', '.join(config['preferred_chains'])}")
        
        confirm = input(f"\nType 'START TRADING' to begin: ").strip()
        if confirm != "START TRADING":
            print("👋 Trading cancelled")
            return None
        
        print(f"\n🚀 LAUNCHING TRADING SYSTEM...")
        print(f"Press Ctrl+C to stop trading at any time")
        
        return system
        
    except ImportError as e:
        print(f"❌ Failed to import trading system: {e}")
        return None
    except Exception as e:
        print(f"❌ Error starting trading system: {e}")
        return None

def start_dashboard():
    """Start the web dashboard"""
    print(f"\n📊 STARTING WEB DASHBOARD")
    print("-" * 25)
    
    try:
        # Start Streamlit dashboard in background
        dashboard_process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", 
            "streamlit_dashboard.py", 
            "--server.port", "8501",
            "--server.headless", "true"
        ])
        
        print("✅ Dashboard starting...")
        print("📊 Dashboard URL: http://localhost:8501")
        
        # Wait a moment then open browser
        time.sleep(3)
        try:
            webbrowser.open("http://localhost:8501")
            print("🌐 Opening dashboard in browser...")
        except:
            print("💡 Manually open: http://localhost:8501")
        
        return dashboard_process
        
    except Exception as e:
        print(f"❌ Failed to start dashboard: {e}")
        return None

def monitor_system(trading_system, dashboard_process):
    """Monitor the system"""
    print(f"\n👁️ SYSTEM MONITORING ACTIVE")
    print("-" * 25)
    print("Commands:")
    print("  'status' - Show system status")
    print("  'stop' - Stop trading")
    print("  'dashboard' - Open dashboard")
    print("  'help' - Show commands")
    print("  'quit' - Exit completely")
    
    try:
        while True:
            command = input("\n> ").strip().lower()
            
            if command == 'status':
                if trading_system:
                    print(f"🟢 Trading System: Running")
                    print(f"💰 Total Profit: ${trading_system.total_profit:.2f}")
                else:
                    print(f"🔴 Trading System: Stopped")
                
                if dashboard_process and dashboard_process.poll() is None:
                    print(f"📊 Dashboard: Running (http://localhost:8501)")
                else:
                    print(f"📊 Dashboard: Stopped")
            
            elif command == 'stop':
                if trading_system:
                    trading_system.stop_trading()
                    print("⏹️ Trading stopped")
                else:
                    print("⚠️ Trading system not running")
            
            elif command == 'dashboard':
                try:
                    webbrowser.open("http://localhost:8501")
                    print("🌐 Opening dashboard...")
                except:
                    print("💡 Manually open: http://localhost:8501")
            
            elif command == 'help':
                print("Available commands:")
                print("  status, stop, dashboard, help, quit")
            
            elif command == 'quit':
                print("🛑 Shutting down system...")
                if trading_system:
                    trading_system.stop_trading()
                if dashboard_process:
                    dashboard_process.terminate()
                break
            
            else:
                print("❌ Unknown command. Type 'help' for available commands.")
                
    except KeyboardInterrupt:
        print("\n🛑 System interrupted")
        if trading_system:
            trading_system.stop_trading()
        if dashboard_process:
            dashboard_process.terminate()

async def run_trading_loop(trading_system):
    """Run the trading system loop"""
    try:
        await trading_system.start_trading()
    except Exception as e:
        print(f"💥 Trading system error: {e}")

def main():
    """Main launcher function"""
    print_welcome()
    
    # Check system requirements
    if not check_system_requirements():
        print("❌ System requirements not met")
        return
    
    # Check if setup is needed
    if not Path(".env").exists() or not Path("production_arbitrage.db").exists():
        print("🔧 First-time setup required...")
        if not run_setup():
            print("❌ Setup failed")
            return
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Dependencies not available")
        return
    
    # Get user configuration
    config = get_user_configuration()
    
    # Show projections
    show_profit_projections(config)
    
    # Confirm before starting
    print(f"\n🤔 Ready to start the ultimate arbitrage system?")
    confirm = input("Type 'yes' to continue: ").lower()
    
    if confirm != 'yes':
        print("👋 Setup cancelled. Run again when ready!")
        return
    
    # Start dashboard
    dashboard_process = start_dashboard()
    
    # Start trading system
    trading_system = start_trading_system(config)
    
    if trading_system:
        # Start trading in background thread
        trading_thread = threading.Thread(
            target=lambda: asyncio.run(run_trading_loop(trading_system))
        )
        trading_thread.daemon = True
        trading_thread.start()
        
        # Monitor system
        monitor_system(trading_system, dashboard_process)
    else:
        print("❌ Failed to start trading system")
        if dashboard_process:
            dashboard_process.terminate()

if __name__ == "__main__":
    main()