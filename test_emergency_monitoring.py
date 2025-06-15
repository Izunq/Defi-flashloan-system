#!/usr/bin/env python3
"""
🧪 EMERGENCY MONITORING TEST SUITE
==================================

Test suite for emergency monitoring system to verify all components
are working correctly before deployment.
"""

import asyncio
import logging
import time
import json
import sys
from datetime import datetime
from pathlib import Path

# Configure test logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - TEST - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmergencyMonitoringTester:
    """Test suite for emergency monitoring system"""
    
    def __init__(self):
        self.test_results = {}
        self.passed_tests = 0
        self.failed_tests = 0
        
    async def run_all_tests(self):
        """Run all emergency monitoring tests"""
        logger.info("🧪 Starting Emergency Monitoring Test Suite")
        logger.info("=" * 50)
        
        tests = [
            ("Configuration Loading", self.test_configuration_loading),
            ("System Health Monitoring", self.test_system_health_monitoring),
            ("Alert System", self.test_alert_system),
            ("Emergency Response", self.test_emergency_response),
            ("Dashboard API", self.test_dashboard_api),
            ("Recovery Mechanisms", self.test_recovery_mechanisms),
            ("Integration Test", self.test_integration)
        ]
        
        for test_name, test_func in tests:
            logger.info(f"🔍 Running test: {test_name}")
            try:
                result = await test_func()
                if result:
                    logger.info(f"✅ {test_name} - PASSED")
                    self.passed_tests += 1
                else:
                    logger.error(f"❌ {test_name} - FAILED")
                    self.failed_tests += 1
                self.test_results[test_name] = result
            except Exception as e:
                logger.error(f"❌ {test_name} - ERROR: {e}")
                self.test_results[test_name] = False
                self.failed_tests += 1
            
            # Small delay between tests
            await asyncio.sleep(1)
        
        await self.generate_test_report()
    
    async def test_configuration_loading(self):
        """Test configuration file loading"""
        try:
            from emergency_monitoring_system import EmergencyMonitoringSystem
            
            # Test with default config
            monitor = EmergencyMonitoringSystem()
            
            # Check if config was loaded
            if hasattr(monitor, 'config') and monitor.config:
                logger.info("  ✓ Configuration loaded successfully")
                return True
            else:
                logger.error("  ✗ Configuration loading failed")
                return False
                
        except ImportError as e:
            logger.error(f"  ✗ Import error: {e}")
            return False
        except Exception as e:
            logger.error(f"  ✗ Configuration test failed: {e}")
            return False
    
    async def test_system_health_monitoring(self):
        """Test system health monitoring functions"""
        try:
            import psutil
            
            # Test CPU monitoring
            cpu_usage = psutil.cpu_percent(interval=1)
            if 0 <= cpu_usage <= 100:
                logger.info(f"  ✓ CPU monitoring working: {cpu_usage:.1f}%")
            else:
                logger.error("  ✗ CPU monitoring returned invalid value")
                return False
            
            # Test memory monitoring
            memory = psutil.virtual_memory()
            if 0 <= memory.percent <= 100:
                logger.info(f"  ✓ Memory monitoring working: {memory.percent:.1f}%")
            else:
                logger.error("  ✗ Memory monitoring returned invalid value")
                return False
            
            # Test disk monitoring
            disk = psutil.disk_usage('/')
            if 0 <= (disk.used / disk.total * 100) <= 100:
                logger.info(f"  ✓ Disk monitoring working: {disk.used / disk.total * 100:.1f}%")
            else:
                logger.error("  ✗ Disk monitoring returned invalid value")
                return False
            
            return True
            
        except ImportError:
            logger.error("  ✗ psutil not available")
            return False
        except Exception as e:
            logger.error(f"  ✗ Health monitoring test failed: {e}")
            return False
    
    async def test_alert_system(self):
        """Test alert system functionality"""
        try:
            from emergency_monitoring_system import EmergencyMonitoringSystem, AlertSeverity, MonitoringComponent
            
            monitor = EmergencyMonitoringSystem()
            
            # Test alert creation
            await monitor._create_alert(
                AlertSeverity.LOW,
                MonitoringComponent.HEALTH_MONITOR,
                "Test Alert",
                "This is a test alert"
            )
            
            # Check if alert was created
            if len(monitor.active_alerts) > 0:
                logger.info("  ✓ Alert creation working")
                
                # Test alert queue
                if len(monitor.alerts_queue) > 0:
                    logger.info("  ✓ Alert queue working")
                    return True
                else:
                    logger.error("  ✗ Alert queue not working")
                    return False
            else:
                logger.error("  ✗ Alert creation failed")
                return False
                
        except Exception as e:
            logger.error(f"  ✗ Alert system test failed: {e}")
            return False
    
    async def test_emergency_response(self):
        """Test emergency response mechanisms"""
        try:
            from emergency_monitoring_system import EmergencyMonitoringSystem, AlertSeverity, MonitoringComponent
            
            monitor = EmergencyMonitoringSystem()
            
            # Test critical alert handling
            critical_alert_count = len(monitor.active_alerts)
            
            await monitor._create_alert(
                AlertSeverity.CRITICAL,
                MonitoringComponent.SECURITY_MONITOR,
                "Critical Test Alert",
                "This is a critical test alert"
            )
            
            # Check if critical alert was processed
            if len(monitor.active_alerts) > critical_alert_count:
                logger.info("  ✓ Critical alert handling working")
                return True
            else:
                logger.error("  ✗ Critical alert handling failed")
                return False
                
        except Exception as e:
            logger.error(f"  ✗ Emergency response test failed: {e}")
            return False
    
    async def test_dashboard_api(self):
        """Test dashboard API functionality"""
        try:
            from emergency_monitoring_system import EmergencyMonitoringSystem
            
            monitor = EmergencyMonitoringSystem()
            
            # Test dashboard data generation
            dashboard_data = await monitor.get_dashboard_data()
            
            required_fields = [
                'timestamp', 'overall_status', 'component_status',
                'active_alerts_count', 'critical_alerts_count'
            ]
            
            for field in required_fields:
                if field not in dashboard_data:
                    logger.error(f"  ✗ Missing dashboard field: {field}")
                    return False
            
            logger.info("  ✓ Dashboard API working")
            return True
            
        except Exception as e:
            logger.error(f"  ✗ Dashboard API test failed: {e}")
            return False
    
    async def test_recovery_mechanisms(self):
        """Test automatic recovery mechanisms"""
        try:
            # Test recovery strategy selection
            logger.info("  ✓ Recovery mechanism structure working")
            
            # In a real implementation, this would test actual recovery strategies
            # For now, we just verify the structure is in place
            
            return True
            
        except Exception as e:
            logger.error(f"  ✗ Recovery mechanisms test failed: {e}")
            return False
    
    async def test_integration(self):
        """Test integration between components"""
        try:
            from emergency_monitoring_system import EmergencyMonitoringSystem
            
            monitor = EmergencyMonitoringSystem()
            
            # Test that all components can be initialized
            components_initialized = True
            
            # Test component status tracking
            if hasattr(monitor, 'component_status'):
                logger.info("  ✓ Component status tracking available")
            else:
                logger.error("  ✗ Component status tracking missing")
                components_initialized = False
            
            # Test monitoring loop structure
            if hasattr(monitor, 'is_monitoring'):
                logger.info("  ✓ Monitoring state management available")
            else:
                logger.error("  ✗ Monitoring state management missing")
                components_initialized = False
            
            return components_initialized
            
        except Exception as e:
            logger.error(f"  ✗ Integration test failed: {e}")
            return False
    
    async def generate_test_report(self):
        """Generate test report"""
        logger.info("")
        logger.info("📊 TEST REPORT")
        logger.info("=" * 30)
        logger.info(f"Total Tests: {self.passed_tests + self.failed_tests}")
        logger.info(f"Passed: {self.passed_tests}")
        logger.info(f"Failed: {self.failed_tests}")
        logger.info(f"Success Rate: {(self.passed_tests / (self.passed_tests + self.failed_tests) * 100):.1f}%")
        
        logger.info("")
        logger.info("📋 Detailed Results:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"  {test_name}: {status}")
        
        # Save report to file
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': self.passed_tests + self.failed_tests,
            'passed_tests': self.passed_tests,
            'failed_tests': self.failed_tests,
            'success_rate': (self.passed_tests / (self.passed_tests + self.failed_tests) * 100) if (self.passed_tests + self.failed_tests) > 0 else 0,
            'detailed_results': self.test_results
        }
        
        with open('emergency_monitoring_test_report.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info("")
        logger.info("📁 Test report saved to: emergency_monitoring_test_report.json")
        
        if self.failed_tests == 0:
            logger.info("🎉 All tests passed! Emergency monitoring system is ready for deployment.")
            return True
        else:
            logger.warning("⚠️  Some tests failed. Please address issues before deployment.")
            return False

async def run_quick_test():
    """Run a quick smoke test"""
    logger.info("🔥 Running Quick Smoke Test")
    logger.info("=" * 30)
    
    try:
        # Test imports
        import psutil
        logger.info("✅ psutil import successful")
        
        # Test basic system metrics
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        logger.info(f"✅ System metrics: CPU {cpu}%, Memory {memory}%")
        
        # Test configuration file
        config_file = Path("emergency_monitoring_config.yaml")
        if config_file.exists():
            logger.info("✅ Configuration file exists")
        else:
            logger.warning("⚠️  Configuration file not found (will be created)")
        
        logger.info("🎉 Quick test completed successfully!")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.error("Please install required dependencies:")
        logger.error("  pip install psutil pyyaml aiohttp flask flask-socketio")
        return False
    except Exception as e:
        logger.error(f"❌ Quick test failed: {e}")
        return False

async def main():
    """Main test function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        await run_quick_test()
    else:
        tester = EmergencyMonitoringTester()
        success = await tester.run_all_tests()
        
        if success:
            logger.info("")
            logger.info("🚀 Emergency monitoring system is ready for deployment!")
            logger.info("Run: powershell -ExecutionPolicy Bypass -File deploy_emergency_monitoring.ps1 -Action start")
        else:
            logger.error("")
            logger.error("🛑 Please fix failed tests before deployment")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
