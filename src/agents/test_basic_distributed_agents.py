#!/usr/bin/env python3
"""
🧪 DISTRIBUTED AGENT ARCHITECTURE SIMPLE TEST
============================================

Basic validation test for the distributed agent architecture components.
This test validates that all components can be imported and initialized correctly.

Author: GitHub Copilot
Version: 1.0
Date: June 14, 2025
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_imports():
    """Test that all distributed agent modules can be imported"""
    logger.info("🔍 Testing module imports...")
      try:
        from distributed_agent_architecture import (
            AgentRole, AgentStatus, DistributedAgentCluster
        )
        logger.info("✅ Distributed agent architecture imported successfully")
        
        from agent_health_monitor import HealthMonitor, HealthStatus
        logger.info("✅ Health monitor imported successfully")
        
        from agent_failover_coordinator import FailoverCoordinator
        logger.info("✅ Failover coordinator imported successfully")
        
        from distributed_agent_integration import DistributedAgentIntegrator
        logger.info("✅ Agent integration imported successfully")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import failed: {e}")
        return False


def test_configuration():
    """Test configuration file loading"""
    logger.info("📄 Testing configuration loading...")
    
    try:
        config_path = "distributed_agent_config.yaml"
        if os.path.exists(config_path):
            logger.info(f"✅ Configuration file found: {config_path}")
            return True
        else:
            logger.warning(f"⚠️ Configuration file not found: {config_path}")
            return True  # Not critical for basic test
            
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {e}")
        return False


def test_health_monitor_initialization():
    """Test health monitor can be initialized"""
    logger.info("🔍 Testing health monitor initialization...")
    
    try:
        from agent_health_monitor import HealthMonitor
        
        # Create basic config
        config = {
            'monitoring_interval': 5,
            'trend_window_size': 10,
            'alert_cooldown': 60,
            'alert_thresholds': {
                'cpu_usage': {'warning': 70, 'critical': 90},
                'memory_usage': {'warning': 80, 'critical': 95}
            }
        }
        
        monitor = HealthMonitor(config)
        logger.info("✅ Health monitor initialized successfully")
        
        # Test agent registration
        monitor.register_agent('test_agent_1', {
            'cpu_usage': 30.0,
            'memory_usage': 40.0
        })
        logger.info("✅ Agent registration successful")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Health monitor test failed: {e}")
        return False


def test_failover_coordinator_initialization():
    """Test failover coordinator can be initialized"""
    logger.info("🔄 Testing failover coordinator initialization...")
    
    try:
        from agent_failover_coordinator import FailoverCoordinator
        
        # Create basic config
        config = {
            'failover_timeout': 30,
            'max_failover_attempts': 3,
            'load_balancing_strategy': 'round_robin'
        }
        
        coordinator = FailoverCoordinator(config)
        logger.info("✅ Failover coordinator initialized successfully")
        
        # Test agent capacity registration
        coordinator.register_agent_capacity(
            agent_id='test_agent_1',
            max_capacity=100.0,
            current_load=30.0,
            capabilities={'trading', 'monitoring'}
        )
        logger.info("✅ Agent capacity registration successful")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failover coordinator test failed: {e}")
        return False


def test_integration_layer():
    """Test the integration layer initialization"""
    logger.info("🔗 Testing integration layer...")
    
    try:
        from distributed_agent_integration import DistributedAgentIntegrator
        
        integrator = DistributedAgentIntegrator('distributed_agent_config.yaml')
        logger.info("✅ Integration layer initialized successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration layer test failed: {e}")
        return False


async def test_async_operations():
    """Test basic async operations"""
    logger.info("⚡ Testing async operations...")
    
    try:
        from agent_health_monitor import HealthMonitor
        
        config = {
            'monitoring_interval': 1,
            'alert_thresholds': {
                'cpu_usage': {'warning': 70, 'critical': 90}
            }
        }
        
        monitor = HealthMonitor(config)
        monitor.register_agent('async_test_agent', {'cpu_usage': 50.0})
        
        # Test async monitoring start/stop
        await monitor.start_monitoring()
        logger.info("✅ Async monitoring started")
        
        await asyncio.sleep(0.1)  # Brief monitoring
        
        await monitor.stop_monitoring()
        logger.info("✅ Async monitoring stopped")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Async operations test failed: {e}")
        return False


def test_dependencies():
    """Test that all required dependencies are available"""
    logger.info("📦 Testing dependencies...")
    
    dependencies = [
        'redis', 'consul', 'etcd3', 'psutil', 'aiohttp', 
        'yaml', 'web3', 'eth_account'
    ]
    
    missing_deps = []
    
    for dep in dependencies:
        try:
            __import__(dep)
            logger.info(f"✅ {dep} available")
        except ImportError:
            missing_deps.append(dep)
            logger.warning(f"⚠️ {dep} not available")
    
    if missing_deps:
        logger.info(f"Missing dependencies: {missing_deps}")
        logger.info("Run: pip install -r requirements_distributed_agents.txt")
    
    return len(missing_deps) == 0


async def main():
    """Run all basic tests"""
    logger.info("🚀 Starting distributed agent architecture validation...")
    
    tests = [
        ("Import Test", test_imports),
        ("Configuration Test", test_configuration),
        ("Health Monitor Test", test_health_monitor_initialization),
        ("Failover Coordinator Test", test_failover_coordinator_initialization),
        ("Integration Layer Test", test_integration_layer),
        ("Dependencies Test", test_dependencies),
    ]
    
    async_tests = [
        ("Async Operations Test", test_async_operations),
    ]
    
    results = {}
    
    # Run synchronous tests
    for test_name, test_func in tests:
        try:
            logger.info(f"\n--- {test_name} ---")
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"Test {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Run asynchronous tests
    for test_name, test_func in async_tests:
        try:
            logger.info(f"\n--- {test_name} ---")
            results[test_name] = await test_func()
        except Exception as e:
            logger.error(f"Test {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Print summary
    passed = sum(results.values())
    total = len(results)
    
    logger.info(f"\n📊 TEST SUMMARY:")
    logger.info(f"   Passed: {passed}/{total}")
    logger.info(f"   Success Rate: {(passed/total)*100:.1f}%")
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"   {test_name}: {status}")
    
    if passed == total:
        logger.info("\n🎉 All basic tests passed! The distributed agent architecture is ready for integration.")
        logger.info("\nNext steps:")
        logger.info("1. Start Redis/Consul services for full distributed functionality")
        logger.info("2. Update existing agent files to use the new distributed architecture")
        logger.info("3. Test with real trading operations")
        logger.info("4. Monitor failover behavior in production")
        return True
    else:
        logger.error(f"\n❌ {total - passed} tests failed. Please check the issues above.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
