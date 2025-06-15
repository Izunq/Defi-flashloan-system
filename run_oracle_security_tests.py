#!/usr/bin/env python3
"""
Oracle Security Testing Suite Runner

This script orchestrates the execution of all oracle security tests,
including unit tests, attack simulations, contract tests, and integration tests.
"""

import os
import sys
import time
import argparse
import subprocess
import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("oracle_security_test_runner.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("OracleSecurityTestRunner")

class OracleSecurityTestRunner:
    """Orchestrates the execution of all oracle security tests"""
    
    def __init__(self):
        """Initialize the test runner"""
        self.start_time = time.time()
        self.results = {}
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        
    async def run_all_tests(self, args):
        """Run all test suites"""
        logger.info("Starting Oracle Security Testing Suite")
        
        # Create results directory
        results_dir = os.path.join(self.test_dir, "test_results")
        os.makedirs(results_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Run unit tests
        if args.unit or args.all:
            await self.run_unit_tests(results_dir, timestamp)
        
        # Run attack simulations
        if args.attack or args.all:
            await self.run_attack_simulations(results_dir, timestamp)
        
        # Run contract tests
        if args.contract or args.all:
            await self.run_contract_tests(results_dir, timestamp)
        
        # Run integration tests
        if args.integration or args.all:
            await self.run_integration_tests(results_dir, timestamp)
        
        # Generate summary report
        self.generate_summary_report(results_dir, timestamp)
        
        elapsed_time = time.time() - self.start_time
        logger.info(f"All tests completed in {elapsed_time:.2f} seconds")
    
    async def run_unit_tests(self, results_dir, timestamp):
        """Run unit tests"""
        logger.info("Running unit tests")
        
        try:
            # Run the unit tests using pytest
            result = subprocess.run(
                ["python", "-m", "pytest", "test_enhanced_oracle_security.py", "-v"],
                capture_output=True,
                text=True
            )
            
            # Save test output
            output_file = os.path.join(results_dir, f"unit_test_results_{timestamp}.txt")
            with open(output_file, 'w') as f:
                f.write(result.stdout)
                if result.stderr:
                    f.write("\n\nERRORS/WARNINGS:\n")
                    f.write(result.stderr)
            
            # Store result
            self.results['unit_tests'] = {
                'success': result.returncode == 0,
                'output_file': output_file,
                'return_code': result.returncode
            }
            
            logger.info(f"Unit tests {'passed' if result.returncode == 0 else 'failed'}")
            
        except Exception as e:
            logger.error(f"Error running unit tests: {e}")
            self.results['unit_tests'] = {
                'success': False,
                'error': str(e)
            }
    
    async def run_attack_simulations(self, results_dir, timestamp):
        """Run attack simulations"""
        logger.info("Running attack simulations")
        
        try:
            # Run the attack simulation script
            result = subprocess.run(
                ["python", "test_oracle_attack_scenarios.py"],
                capture_output=True,
                text=True
            )
            
            # Save test output
            output_file = os.path.join(results_dir, f"attack_simulation_results_{timestamp}.txt")
            with open(output_file, 'w') as f:
                f.write(result.stdout)
                if result.stderr:
                    f.write("\n\nERRORS/WARNINGS:\n")
                    f.write(result.stderr)
            
            # Store result
            self.results['attack_simulations'] = {
                'success': result.returncode == 0,
                'output_file': output_file,
                'return_code': result.returncode
            }
            
            # Copy the JSON report if it exists
            report_file = "oracle_attack_simulation_report.json"
            if os.path.exists(report_file):
                report_dest = os.path.join(results_dir, f"attack_simulation_report_{timestamp}.json")
                with open(report_file, 'r') as src, open(report_dest, 'w') as dest:
                    dest.write(src.read())
                self.results['attack_simulations']['report_file'] = report_dest
            
            # Copy visualization files if they exist
            viz_dir = "attack_visualizations"
            if os.path.exists(viz_dir):
                viz_dest = os.path.join(results_dir, f"attack_visualizations_{timestamp}")
                os.makedirs(viz_dest, exist_ok=True)
                for file in os.listdir(viz_dir):
                    if file.endswith(".png"):
                        src_file = os.path.join(viz_dir, file)
                        dest_file = os.path.join(viz_dest, file)
                        with open(src_file, 'rb') as src, open(dest_file, 'wb') as dest:
                            dest.write(src.read())
            
            logger.info(f"Attack simulations {'completed successfully' if result.returncode == 0 else 'failed'}")
            
        except Exception as e:
            logger.error(f"Error running attack simulations: {e}")
            self.results['attack_simulations'] = {
                'success': False,
                'error': str(e)
            }
    
    async def run_contract_tests(self, results_dir, timestamp):
        """Run contract tests"""
        logger.info("Running contract tests")
        
        try:
            # Run the contract tests using Hardhat
            result = subprocess.run(
                ["npx", "hardhat", "test", "test/oracle-security-contracts.js"],
                capture_output=True,
                text=True
            )
            
            # Save test output
            output_file = os.path.join(results_dir, f"contract_test_results_{timestamp}.txt")
            with open(output_file, 'w') as f:
                f.write(result.stdout)
                if result.stderr:
                    f.write("\n\nERRORS/WARNINGS:\n")
                    f.write(result.stderr)
            
            # Store result
            self.results['contract_tests'] = {
                'success': result.returncode == 0,
                'output_file': output_file,
                'return_code': result.returncode
            }
            
            logger.info(f"Contract tests {'passed' if result.returncode == 0 else 'failed'}")
            
        except Exception as e:
            logger.error(f"Error running contract tests: {e}")
            self.results['contract_tests'] = {
                'success': False,
                'error': str(e)
            }
    
    async def run_integration_tests(self, results_dir, timestamp):
        """Run integration tests"""
        logger.info("Running integration tests")
        
        try:
            # Run the integration tests
            result = subprocess.run(
                ["python", "test_oracle_security_integration.py"],
                capture_output=True,
                text=True
            )
            
            # Save test output
            output_file = os.path.join(results_dir, f"integration_test_results_{timestamp}.txt")
            with open(output_file, 'w') as f:
                f.write(result.stdout)
                if result.stderr:
                    f.write("\n\nERRORS/WARNINGS:\n")
                    f.write(result.stderr)
            
            # Store result
            self.results['integration_tests'] = {
                'success': result.returncode == 0,
                'output_file': output_file,
                'return_code': result.returncode
            }
            
            # Copy the JSON report if it exists
            report_file = "oracle_security_integration_test_report.json"
            if os.path.exists(report_file):
                report_dest = os.path.join(results_dir, f"integration_test_report_{timestamp}.json")
                with open(report_file, 'r') as src, open(report_dest, 'w') as dest:
                    dest.write(src.read())
                self.results['integration_tests']['report_file'] = report_dest
            
            logger.info(f"Integration tests {'completed successfully' if result.returncode == 0 else 'failed'}")
            
        except Exception as e:
            logger.error(f"Error running integration tests: {e}")
            self.results['integration_tests'] = {
                'success': False,
                'error': str(e)
            }
    
    def generate_summary_report(self, results_dir, timestamp):
        """Generate a summary report of all test results"""
        logger.info("Generating summary report")
        
        summary = {
            'timestamp': timestamp,
            'duration': time.time() - self.start_time,
            'results': self.results,
            'overall_success': all(result.get('success', False) for result in self.results.values())
        }
        
        # Save summary report
        summary_file = os.path.join(results_dir, f"test_summary_{timestamp}.txt")
        with open(summary_file, 'w') as f:
            f.write("ORACLE SECURITY TESTING SUITE SUMMARY\n")
            f.write("=====================================\n\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Duration: {summary['duration']:.2f} seconds\n\n")
            
            f.write("Test Results:\n")
            for test_type, result in self.results.items():
                status = "PASSED" if result.get('success', False) else "FAILED"
                f.write(f"  {test_type}: {status}\n")
            
            f.write(f"\nOverall Status: {'PASSED' if summary['overall_success'] else 'FAILED'}\n")
        
        logger.info(f"Summary report saved to {summary_file}")
        
        # Print summary to console
        print("\n===== ORACLE SECURITY TESTING SUMMARY =====")
        print(f"Timestamp: {timestamp}")
        print(f"Duration: {summary['duration']:.2f} seconds")
        print("\nTest Results:")
        for test_type, result in self.results.items():
            status = "PASSED" if result.get('success', False) else "FAILED"
            print(f"  {test_type}: {status}")
        print(f"\nOverall Status: {'PASSED' if summary['overall_success'] else 'FAILED'}")
        print("===========================================\n")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Oracle Security Testing Suite Runner")
    
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--attack", action="store_true", help="Run attack simulations")
    parser.add_argument("--contract", action="store_true", help="Run contract tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    
    args = parser.parse_args()
    
    # If no specific tests are selected, run all tests
    if not (args.all or args.unit or args.attack or args.contract or args.integration):
        args.all = True
    
    return args

async def main():
    """Main entry point"""
    args = parse_args()
    runner = OracleSecurityTestRunner()
    await runner.run_all_tests(args)

if __name__ == "__main__":
    asyncio.run(main())