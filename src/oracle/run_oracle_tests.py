#!/usr/bin/env python3
"""
Oracle Security Testing Suite Runner

This script runs all oracle security tests in a coordinated manner and generates
a comprehensive report of the testing results.
"""

import os
import sys
import asyncio
import subprocess
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("oracle_testing_suite.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("OracleTestSuite")

class OracleTestingSuite:
    """Comprehensive oracle security testing suite"""
    
    def __init__(self):
        self.results = {}
        self.start_time = time.time()
        self.test_config_path = "test_oracle_config.yaml"
        
    def ensure_test_config(self):
        """Ensure test configuration file exists"""
        if not os.path.exists(self.test_config_path):
            logger.warning(f"Test config {self.test_config_path} not found, creating default")
            # The config file should already be created, but just in case
            return False
        return True
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all oracle security tests"""
        logger.info("Starting Oracle Security Testing Suite")
        
        # Ensure test configuration exists
        if not self.ensure_test_config():
            logger.error("Failed to create test configuration")
            return {"error": "Missing test configuration"}
        
        # Run each test suite
        await self._run_unit_tests()
        await self._run_integration_tests()
        await self._run_attack_simulation_tests()
        await self._run_performance_tests()
        
        # Generate comprehensive report
        self._generate_final_report()
        
        return self.results
    
    async def _run_unit_tests(self):
        """Run unit tests"""
        logger.info("Running unit tests...")
        
        try:
            # Run the enhanced oracle security tests
            if os.path.exists("test_enhanced_oracle_security_fixed.py"):
                result = await self._run_python_test("test_enhanced_oracle_security_fixed.py")
                self.results['unit_tests'] = result
            else:
                self.results['unit_tests'] = {"status": "SKIPPED", "reason": "Test file not found"}
                
        except Exception as e:
            logger.error(f"Unit tests failed: {e}")
            self.results['unit_tests'] = {"status": "ERROR", "error": str(e)}
    
    async def _run_integration_tests(self):
        """Run integration tests"""
        logger.info("Running integration tests...")
        
        try:
            # Run the integration tests
            if os.path.exists("test_oracle_security_integration_fixed.py"):
                result = await self._run_python_test("test_oracle_security_integration_fixed.py")
                self.results['integration_tests'] = result
            else:
                self.results['integration_tests'] = {"status": "SKIPPED", "reason": "Test file not found"}
                
        except Exception as e:
            logger.error(f"Integration tests failed: {e}")
            self.results['integration_tests'] = {"status": "ERROR", "error": str(e)}
    
    async def _run_attack_simulation_tests(self):
        """Run attack simulation tests"""
        logger.info("Running attack simulation tests...")
        
        try:
            # Run the attack simulation tests
            if os.path.exists("test_oracle_attack_scenarios_fixed.py"):
                result = await self._run_python_test("test_oracle_attack_scenarios_fixed.py")
                self.results['attack_simulation_tests'] = result
            else:
                self.results['attack_simulation_tests'] = {"status": "SKIPPED", "reason": "Test file not found"}
                
        except Exception as e:
            logger.error(f"Attack simulation tests failed: {e}")
            self.results['attack_simulation_tests'] = {"status": "ERROR", "error": str(e)}
    
    async def _run_performance_tests(self):
        """Run performance tests"""
        logger.info("Running performance tests...")
        
        try:
            # Performance tests are integrated into other test suites
            # Here we can run additional stress tests if needed
            
            # Run the oracle security testing suite if it exists
            if os.path.exists("oracle_security_testing_suite.py"):
                result = await self._run_python_test("oracle_security_testing_suite.py")
                self.results['performance_tests'] = result
            else:
                self.results['performance_tests'] = {"status": "SKIPPED", "reason": "Test file not found"}
                
        except Exception as e:
            logger.error(f"Performance tests failed: {e}")
            self.results['performance_tests'] = {"status": "ERROR", "error": str(e)}
    
    async def _run_python_test(self, test_file: str) -> Dict[str, Any]:
        """Run a Python test file and capture results"""
        logger.info(f"Running {test_file}...")
        
        start_time = time.time()
        
        try:
            # Run the test file as a subprocess
            process = await asyncio.create_subprocess_exec(
                sys.executable, test_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)  # 5 minutes timeout
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "status": "TIMEOUT",
                    "duration": time.time() - start_time,
                    "error": "Test execution timed out after 5 minutes"
                }
            
            duration = time.time() - start_time
            
            # Decode output
            stdout_text = stdout.decode('utf-8') if stdout else ""
            stderr_text = stderr.decode('utf-8') if stderr else ""
            
            # Determine test result
            if process.returncode == 0:
                status = "PASSED"
            else:
                status = "FAILED"
            
            # Try to parse any JSON reports generated by the test
            reports = self._find_test_reports(test_file)
            
            return {
                "status": status,
                "duration": duration,
                "return_code": process.returncode,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "reports": reports
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "duration": time.time() - start_time,
                "error": str(e)
            }
    
    def _find_test_reports(self, test_file: str) -> List[Dict]:
        """Find and load any JSON reports generated by the test"""
        reports = []
        
        # Common report file patterns
        report_patterns = [
            "oracle_security_integration_test_report.json",
            "oracle_attack_simulation_report.json",
            "oracle_security_test_report.json"
        ]
        
        for pattern in report_patterns:
            if os.path.exists(pattern):
                try:
                    with open(pattern, 'r') as f:
                        report_data = json.load(f)
                    reports.append({
                        "file": pattern,
                        "data": report_data
                    })
                except Exception as e:
                    logger.warning(f"Failed to load report {pattern}: {e}")
        
        return reports
    
    def _generate_final_report(self):
        """Generate a comprehensive final report"""
        total_duration = time.time() - self.start_time
        
        # Count test results
        test_counts = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "error": 0,
            "skipped": 0,
            "timeout": 0
        }
        
        for test_suite, result in self.results.items():
            if isinstance(result, dict) and 'status' in result:
                test_counts["total"] += 1
                status = result['status'].lower()
                if status in test_counts:
                    test_counts[status] += 1
        
        # Calculate success rate
        success_rate = 0
        if test_counts["total"] > 0:
            success_rate = (test_counts["passed"] / test_counts["total"]) * 100
        
        # Compile final report
        final_report = {
            "oracle_security_testing_suite": {
                "timestamp": datetime.now().isoformat(),
                "total_duration": total_duration,
                "test_summary": test_counts,
                "success_rate": success_rate,
                "test_results": self.results
            },
            "environment": {
                "python_version": sys.version,
                "working_directory": os.getcwd(),
                "test_config": self.test_config_path
            },
            "recommendations": self._generate_recommendations()
        }
        
        # Save final report
        report_filename = f"oracle_security_final_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(final_report, f, indent=2, default=str)
        
        # Print summary
        self._print_test_summary(final_report)
        
        logger.info(f"Final test report saved to {report_filename}")
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Check for failed tests
        failed_tests = [name for name, result in self.results.items() 
                       if isinstance(result, dict) and result.get('status') == 'FAILED']
        
        if failed_tests:
            recommendations.append(f"Investigate and fix failed tests: {', '.join(failed_tests)}")
        
        # Check for timeouts
        timeout_tests = [name for name, result in self.results.items() 
                        if isinstance(result, dict) and result.get('status') == 'TIMEOUT']
        
        if timeout_tests:
            recommendations.append(f"Optimize performance for timeout tests: {', '.join(timeout_tests)}")
        
        # Check for errors
        error_tests = [name for name, result in self.results.items() 
                      if isinstance(result, dict) and result.get('status') == 'ERROR']
        
        if error_tests:
            recommendations.append(f"Fix configuration or dependency issues for: {', '.join(error_tests)}")
        
        # General recommendations
        recommendations.extend([
            "Ensure all oracle security monitors are properly configured",
            "Verify smart contract deployments are successful",
            "Test with different network conditions",
            "Implement continuous monitoring in production"
        ])
        
        return recommendations
    
    def _print_test_summary(self, report: Dict):
        """Print a formatted test summary"""
        summary = report["oracle_security_testing_suite"]["test_summary"]
        success_rate = report["oracle_security_testing_suite"]["success_rate"]
        duration = report["oracle_security_testing_suite"]["total_duration"]
        
        print("\n" + "="*60)
        print("           ORACLE SECURITY TESTING SUITE SUMMARY")
        print("="*60)
        print(f"Total Duration: {duration:.2f} seconds")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        print("Test Results:")
        print(f"  Total Tests:  {summary['total']}")
        print(f"  Passed:       {summary['passed']}")
        print(f"  Failed:       {summary['failed']}")
        print(f"  Errors:       {summary['error']}")
        print(f"  Skipped:      {summary['skipped']}")
        print(f"  Timeouts:     {summary['timeout']}")
        print()
        
        # Print individual test results
        for test_name, result in self.results.items():
            if isinstance(result, dict) and 'status' in result:
                status = result['status']
                duration = result.get('duration', 0)
                print(f"  {test_name:30} {status:10} ({duration:.2f}s)")
        
        print()
        print("Recommendations:")
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"  {i}. {rec}")
        
        print("="*60)

async def main():
    """Run the oracle security testing suite"""
    suite = OracleTestingSuite()
    results = await suite.run_all_tests()
    
    # Return appropriate exit code
    if any(result.get('status') == 'FAILED' for result in results.values() if isinstance(result, dict)):
        sys.exit(1)
    elif any(result.get('status') == 'ERROR' for result in results.values() if isinstance(result, dict)):
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
