#!/usr/bin/env python3
"""
🚨 EMERGENCY MONITORING QUICK START
===================================

Quick start script to deploy and run the emergency monitoring system.
This script will guide you through the setup process step by step.
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path

def print_banner():
    """Print startup banner"""
    print("=" * 60)
    print("🚨 EMERGENCY MONITORING SYSTEM - QUICK START")
    print("=" * 60)
    print()

def print_step(step_num, title, description):
    """Print setup step"""
    print(f"📌 Step {step_num}: {title}")
    print(f"   {description}")
    print()

def run_command(command, description):
    """Run a command and show results"""
    print(f"⏳ {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            return True
        else:
            print(f"❌ {description} - FAILED")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

async def quick_start():
    """Run quick start setup"""
    print_banner()
    
    print("🎯 This script will:")
    print("   • Test your system requirements")
    print("   • Install Python dependencies")
    print("   • Run system tests")
    print("   • Start the monitoring system")
    print("   • Open the dashboard")
    print()
    
    input("Press Enter to continue...")
    print()
    
    # Step 1: Test system requirements
    print_step(1, "System Requirements", "Checking Python and dependencies")
    
    # Check Python
    if not run_command("python --version", "Checking Python installation"):
        print("❌ Python is required. Please install Python 3.7+ and try again.")
        return False
    
    # Install dependencies
    print_step(2, "Dependencies", "Installing required Python packages")
    dependencies = [
        "psutil", "pyyaml", "aiohttp", "flask", "flask-socketio", "websockets"
    ]
    
    for dep in dependencies:
        if not run_command(f"pip install {dep} --quiet", f"Installing {dep}"):
            print(f"⚠️  Warning: Failed to install {dep}")
    
    # Step 3: Run tests
    print_step(3, "System Tests", "Running emergency monitoring tests")
    
    if not run_command("python test_emergency_monitoring.py --quick", "Quick system test"):
        print("❌ System tests failed. Please check the errors above.")
        return False
    
    # Step 4: Start monitoring
    print_step(4, "Start Monitoring", "Starting emergency monitoring system")
    
    print("🚀 Starting emergency monitoring system...")
    print("📊 Dashboard will be available at: http://localhost:8080")
    print()
    print("🔥 MONITORING SYSTEM STARTING...")
    print("   Press Ctrl+C to stop monitoring")
    print("=" * 50)
    
    try:
        # Import and start the monitoring system
        from emergency_monitoring_system import EmergencyMonitoringSystem
        from emergency_monitoring_dashboard import start_dashboard_thread
        
        # Create monitoring system
        monitor = EmergencyMonitoringSystem()
        
        # Start dashboard in background
        dashboard_thread = start_dashboard_thread(monitor)
        
        print("✅ Dashboard started on http://localhost:8080")
        print("🔍 Starting monitoring system...")
        
        # Start monitoring
        await monitor.start_monitoring()
        
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Some required modules are missing. Please install dependencies:")
        print("pip install flask flask-socketio psutil pyyaml aiohttp websockets")
        return False
    except Exception as e:
        print(f"❌ Error starting monitoring: {e}")
        return False

def main():
    """Main function"""
    try:
        asyncio.run(quick_start())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
