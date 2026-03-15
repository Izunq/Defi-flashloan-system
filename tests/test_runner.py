#!/usr/bin/env python3
"""
Comprehensive Test Runner for Flash Loan System

This script provides a unified interface to run all types of tests
including unit tests, integration tests, security tests, and performance tests.
"""

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_runner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('TestRunner')

@dataclass
class TestResult:
    """Test result data structure."""
    test_name: str
    status: str  # PASS, FAIL, SKIP, ERROR
    duration: float
    details: Dict[str, Any]
    error_message: Optional[str] = None

@dataclass
class TestSuite:
    """Test suite configuration."""
    name: str
    test_files: List[str]
    markers: List[str]
    timeout: int
    dependencies: List[str]
    setup_commands: List[str]
    cleanup_commands: List[str]

class ComprehensiveTestRunner:
    """Comprehensive test runner for the flash loan system."""
    
    def __init__(self, project_root: Path):
        """Initialize the test runner."""
        self.project_root = project_root
        self.test_results = []
        self.start_time = None
        self.total_duration = 0
        
        # Define test suites
        self.test_suites = {
            'unit': TestSuite(
                name='Unit Tests',
                test_files=[
                    'test_input_validation.py',
                    'test_enhanced_oracle_security.py',
                    'test_enhanced_oracle_security_fixed.py'
                ],
                markers=['unit'],
                timeout=300,
                dependencies=[],
                setup_commands=[],
                cleanup_commands=[]
            ),
            'integration': TestSuite(
                name='Integration Tests',
                test_files=[
                    'test_oracle_security_integration.py',
                    'test_oracle_security_integration_fixed.py',
                    'test_distributed_agents.py',
                    'test_cross_chain_security.py'
                ],
                markers=['integration'],
                timeout=600,
                dependencies=['unit'],
                setup_commands=[
                    'python deploy_contracts.py --test-mode',
                ],
                cleanup_commands=[
                    'python cleanup_test_environment.py'
                ]
            ),
            'security': TestSuite(
                name='Security Tests',
                test_files=[
                    'security_test_suite.py',
                    'test_gas_griefing_protection.py',
                    'test_oracle_attack_scenarios.py',
                    'test_oracle_attack_scenarios_fixed.py'
                ],
                markers=['security'],
                timeout=900,
                dependencies=[],
                setup_commands=[],
                cleanup_commands=[]
            ),
            'performance': TestSuite(
                name='Performance Tests',
                test_files=[
                    'oracle_security_testing_suite.py',
                    'test_advanced_oracle_security.py'
                ],
                markers=['performance', 'slow'],
                timeout=1200,
                dependencies=['unit'],
                setup_commands=[],
                cleanup_commands=[]
            ),
            'emergency': TestSuite(
                name='Emergency Monitoring Tests',
                test_files=[
                    'test_emergency_monitoring.py'
                ],
                markers=['emergency'],
                timeout=300,
                dependencies=[],
                setup_commands=[],
                cleanup_commands=[]
            ),
            'specialized': TestSuite(
                name='Specialized Tests',
                test_files=[
                    'test_zk_proof.py',
                    'test_basic_distributed_agents.py'
                ],
                markers=['specialized'],
                timeout=600,
                dependencies=[],
                setup_commands=[],
                cleanup_commands=[]
            )
        }
    
    def run_all_tests(self, 
                     suites: Optional[List[str]] = None,
                     parallel: bool = False,
                     coverage: bool = True,
                     generate_report: bool = True) -> Dict[str, Any]:
        """Run all test suites."""
        logger.info("🚀 Starting Comprehensive Test Suite")
        logger.info("=" * 60)
        
        self.start_time = time.time()
        
        if suites is None:
            suites = list(self.test_suites.keys())
        
        # Install dependencies first
        self._install_test_dependencies()
        
        # Run test suites
        for suite_name in suites:
            if suite_name not in self.test_suites:
                logger.error(f"Unknown test suite: {suite_name}")
                continue
            
            logger.info(f"🧪 Running {self.test_suites[suite_name].name}")
            result = self._run_test_suite(suite_name, coverage=coverage)
            self.test_results.append(result)
        
        self.total_duration = time.time() - self.start_time
        
        # Generate reports
        if generate_report:
            self._generate_comprehensive_report()
        
        return self._get_summary()
    
    def _install_test_dependencies(self):
        """Install test dependencies."""
        logger.info("📦 Installing test dependencies...")
        
        requirements_files = [
            'requirements.txt',
            'requirements_fixed.txt'
        ]
        
        for req_file in requirements_files:
            req_path = self.project_root / req_file
            if req_path.exists():
                try:
                    subprocess.run([
                        sys.executable, '-m', 'pip', 'install', '-r', str(req_path)
                    ], check=True, capture_output=True)
                    logger.info(f"✅ Installed dependencies from {req_file}")
                except subprocess.CalledProcessError as e:
                    logger.warning(f"⚠️  Failed to install from {req_file}: {e}")
    
    def _run_test_suite(self, suite_name: str, coverage: bool = True) -> TestResult:
        """Run a specific test suite."""
        suite = self.test_suites[suite_name]
        start_time = time.time()
        
        try:
            # Run setup commands
            for cmd in suite.setup_commands:
                self._run_command(cmd)
            
            # Build pytest command
            cmd_args = [sys.executable, '-m', 'pytest']
            
            # Add test files
            for test_file in suite.test_files:
                test_path = self.project_root / test_file
                if test_path.exists():
                    cmd_args.append(str(test_path))
            
            # Add markers
            if suite.markers:
                marker_expression = ' or '.join(suite.markers)
                cmd_args.extend(['-m', marker_expression])
            
            # Add coverage if requested
            if coverage:
                cmd_args.extend([
                    '--cov=.',
                    '--cov-report=term-missing',
                    f'--cov-report=html:htmlcov/{suite_name}',
                    f'--cov-report=xml:coverage_{suite_name}.xml'
                ])
            
            # Add other options
            cmd_args.extend([
                '--verbose',
                '--tb=short',
                f'--timeout={suite.timeout}',
                '--durations=10',
                '--strict-markers',
                f'--junitxml=test_results_{suite_name}.xml'
            ])
            
            # Run tests
            logger.info(f"Running: {' '.join(cmd_args)}")
            result = subprocess.run(
                cmd_args,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=suite.timeout
            )
            
            duration = time.time() - start_time
            
            # Determine status
            if result.returncode == 0:
                status = 'PASS'
                error_message = None
            elif result.returncode == 1:
                status = 'FAIL'
                error_message = result.stdout + result.stderr
            else:
                status = 'ERROR'
                error_message = result.stderr
            
            # Parse output for details
            details = self._parse_test_output(result.stdout, result.stderr)
            
            # Run cleanup commands
            for cmd in suite.cleanup_commands:
                self._run_command(cmd, ignore_errors=True)
            
            return TestResult(
                test_name=suite.name,
                status=status,
                duration=duration,
                details=details,
                error_message=error_message
            )
        
        except subprocess.TimeoutExpired:
            return TestResult(
                test_name=suite.name,
                status='TIMEOUT',
                duration=time.time() - start_time,
                details={},
                error_message=f'Test suite timed out after {suite.timeout} seconds'
            )
        except Exception as e:
            return TestResult(
                test_name=suite.name,
                status='ERROR',
                duration=time.time() - start_time,
                details={},
                error_message=str(e)
            )
    
    def _run_command(self, command: str, ignore_errors: bool = False):
        """Run a shell command."""
        try:
            logger.info(f"Running setup command: {command}")
            result = subprocess.run(
                command.split(),
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode != 0 and not ignore_errors:
                logger.warning(f"Command failed: {result.stderr}")
        except Exception as e:
            if not ignore_errors:
                logger.error(f"Failed to run command '{command}': {e}")
    
    def _parse_test_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Parse test output to extract details."""
        details = {
            'stdout': stdout,
            'stderr': stderr,
            'tests_collected': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'tests_skipped': 0,
            'tests_errors': 0,
            'coverage_percentage': 0
        }
        
        # Parse pytest output
        lines = stdout.split('\n')
        for line in lines:
            if 'collected' in line and 'items' in line:
                try:
                    details['tests_collected'] = int(line.split()[0])
                except (ValueError, IndexError):
                    pass
            
            if 'passed' in line and 'failed' in line:
                # Parse final results line
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == 'passed':
                        try:
                            details['tests_passed'] = int(parts[i-1])
                        except (ValueError, IndexError):
                            pass
                    elif part == 'failed':
                        try:
                            details['tests_failed'] = int(parts[i-1])
                        except (ValueError, IndexError):
                            pass
                    elif part == 'skipped':
                        try:
                            details['tests_skipped'] = int(parts[i-1])
                        except (ValueError, IndexError):
                            pass
            
            if 'Total coverage:' in line:
                try:
                    coverage_str = line.split(':')[1].strip().rstrip('%')
                    details['coverage_percentage'] = float(coverage_str)
                except (ValueError, IndexError):
                    pass
        
        return details
    
    def _generate_comprehensive_report(self):
        """Generate comprehensive test report."""
        logger.info("📊 Generating comprehensive test report...")
        
        report_data = {
            'test_run_info': {
                'timestamp': datetime.now().isoformat(),
                'total_duration': self.total_duration,
                'project_root': str(self.project_root),
                'python_version': sys.version,
                'test_suites_run': len(self.test_results)
            },
            'test_results': [asdict(result) for result in self.test_results],
            'summary': self._get_summary()
        }
        
        # Save JSON report
        report_path = self.project_root / 'test_report.json'
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Generate HTML report
        self._generate_html_report(report_data)
        
        logger.info(f"📄 Test report saved to: {report_path}")
    
    def _generate_html_report(self, report_data: Dict[str, Any]):
        """Generate HTML test report."""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Flash Loan System - Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ background: #e8f5e8; padding: 15px; margin: 20px 0; border-radius: 5px; }}
        .test-suite {{ background: #fff; border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
        .pass {{ color: #28a745; }}
        .fail {{ color: #dc3545; }}
        .error {{ color: #fd7e14; }}
        .timeout {{ color: #6f42c1; }}
        .skip {{ color: #6c757d; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 Flash Loan System - Comprehensive Test Report</h1>
        <p><strong>Generated:</strong> {report_data['test_run_info']['timestamp']}</p>
        <p><strong>Total Duration:</strong> {report_data['test_run_info']['total_duration']:.2f} seconds</p>
        <p><strong>Python Version:</strong> {report_data['test_run_info']['python_version']}</p>
    </div>
    
    <div class="summary">
        <h2>📊 Test Summary</h2>
        <p><strong>Total Test Suites:</strong> {report_data['summary']['total_suites']}</p>
        <p><strong>Passed:</strong> <span class="pass">{report_data['summary']['passed_suites']}</span></p>
        <p><strong>Failed:</strong> <span class="fail">{report_data['summary']['failed_suites']}</span></p>
        <p><strong>Errors:</strong> <span class="error">{report_data['summary']['error_suites']}</span></p>
        <p><strong>Success Rate:</strong> {report_data['summary']['success_rate']:.1f}%</p>
    </div>
    
    <h2>🔍 Test Suite Details</h2>
"""
        
        for result in self.test_results:
            status_class = result.status.lower()
            html_content += f"""
    <div class="test-suite">
        <h3>{result.test_name} - <span class="{status_class}">{result.status}</span></h3>
        <p><strong>Duration:</strong> {result.duration:.2f} seconds</p>
        
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Tests Collected</td><td>{result.details.get('tests_collected', 0)}</td></tr>
            <tr><td>Tests Passed</td><td class="pass">{result.details.get('tests_passed', 0)}</td></tr>
            <tr><td>Tests Failed</td><td class="fail">{result.details.get('tests_failed', 0)}</td></tr>
            <tr><td>Tests Skipped</td><td class="skip">{result.details.get('tests_skipped', 0)}</td></tr>
            <tr><td>Coverage</td><td>{result.details.get('coverage_percentage', 0):.1f}%</td></tr>
        </table>
        
        {f'<div style="background: #ffe6e6; padding: 10px; margin: 10px 0; border-radius: 3px;"><strong>Error:</strong> {result.error_message}</div>' if result.error_message else ''}
    </div>
"""
        
        html_content += """
</body>
</html>
"""
        
        html_path = self.project_root / 'test_report.html'
        with open(html_path, 'w') as f:
            f.write(html_content)
        
        logger.info(f"🌐 HTML report saved to: {html_path}")
    
    def _get_summary(self) -> Dict[str, Any]:
        """Get test summary statistics."""
        total_suites = len(self.test_results)
        passed_suites = sum(1 for r in self.test_results if r.status == 'PASS')
        failed_suites = sum(1 for r in self.test_results if r.status == 'FAIL')
        error_suites = sum(1 for r in self.test_results if r.status in ['ERROR', 'TIMEOUT'])
        
        success_rate = (passed_suites / max(total_suites, 1)) * 100
        
        return {
            'total_suites': total_suites,
            'passed_suites': passed_suites,
            'failed_suites': failed_suites,
            'error_suites': error_suites,
            'success_rate': success_rate,
            'total_duration': self.total_duration
        }
    
    def run_smoke_tests(self) -> Dict[str, Any]:
        """Run quick smoke tests."""
        logger.info("💨 Running smoke tests...")
        
        smoke_tests = [
            'test_input_validation.py::InputValidationTestSuite::test_string_validation_normal',
            'test_enhanced_oracle_security_fixed.py::TestEnhancedOracleSecurityMonitor::test_initialization',
            'security_test_suite.py::SecurityTestSuite::_test_address_validation'
        ]
        
        cmd_args = [sys.executable, '-m', 'pytest'] + smoke_tests + [
            '--verbose', '--tb=short', '--timeout=60'
        ]
        
        try:
            result = subprocess.run(
                cmd_args,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            return {
                'status': 'PASS' if result.returncode == 0 else 'FAIL',
                'output': result.stdout,
                'errors': result.stderr
            }
        except Exception as e:
            return {
                'status': 'ERROR',
                'output': '',
                'errors': str(e)
            }

def main():
    """Main function for the test runner."""
    parser = argparse.ArgumentParser(description='Comprehensive Test Runner for Flash Loan System')
    parser.add_argument('--suites', nargs='+', 
                       choices=['unit', 'integration', 'security', 'performance', 'emergency', 'specialized'],
                       help='Test suites to run')
    parser.add_argument('--smoke', action='store_true', help='Run smoke tests only')
    parser.add_argument('--no-coverage', action='store_true', help='Disable coverage reporting')
    parser.add_argument('--no-report', action='store_true', help='Disable report generation')
    parser.add_argument('--parallel', action='store_true', help='Run tests in parallel')
    parser.add_argument('--project-root', type=Path, default=Path.cwd(), 
                       help='Project root directory')
    
    args = parser.parse_args()
    
    runner = ComprehensiveTestRunner(args.project_root)
    
    try:
        if args.smoke:
            result = runner.run_smoke_tests()
            print(f"\n{'='*60}")
            print("SMOKE TEST RESULTS")
            print(f"{'='*60}")
            print(f"Status: {result['status']}")
            if result['status'] != 'PASS':
                print(f"Errors: {result['errors']}")
        else:
            result = runner.run_all_tests(
                suites=args.suites,
                parallel=args.parallel,
                coverage=not args.no_coverage,
                generate_report=not args.no_report
            )
            
            print(f"\n{'='*60}")
            print("COMPREHENSIVE TEST RESULTS")
            print(f"{'='*60}")
            print(f"Total Suites: {result['total_suites']}")
            print(f"Passed: {result['passed_suites']}")
            print(f"Failed: {result['failed_suites']}")
            print(f"Errors: {result['error_suites']}")
            print(f"Success Rate: {result['success_rate']:.1f}%")
            print(f"Total Duration: {result['total_duration']:.2f} seconds")
            
            if result['success_rate'] == 100:
                print("\n🎉 ALL TESTS PASSED!")
                sys.exit(0)
            else:
                print(f"\n❌ {result['failed_suites'] + result['error_suites']} test suite(s) failed")
                sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Test run interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Test run failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
