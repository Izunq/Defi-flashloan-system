#!/usr/bin/env python3
"""
Phase 4 Testing & Verification Execution Script
Executes the complete Phase 4 testing suite including:
1. Formal Verification
2. Comprehensive Test Suite
3. Penetration Testing
4. Load Testing & Optimization
"""

import os
import sys
import subprocess
import time
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Phase4TestRunner:
    """Main test runner for Phase 4"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.test_results = {}
        self.start_time = time.time()
        
    def install_dependencies(self) -> bool:
        """Install testing dependencies"""
        logger.info("[SETUP] Installing testing dependencies...")
        
        try:
            requirements_file = self.project_root / "requirements_testing.txt"
            
            if requirements_file.exists():
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info("[DONE] Dependencies installed successfully")
                    return True
                else:
                    logger.error(f"❌ Failed to install dependencies: {result.stderr}")
                    return False
            else:
                logger.warning("[WARN] requirements_testing.txt not found, skipping dependency installation")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error installing dependencies: {e}")
            return False
    
    def run_unit_tests(self) -> Dict[str, Any]:
        """Run unit tests including formal verification"""
        logger.info("🧪 Running unit tests and formal verification...")
        
        try:
            test_dir = self.project_root / "tests" / "unit"
            
            # Run pytest with coverage
            result = subprocess.run([
                sys.executable, "-m", "pytest",
                str(test_dir),
                "-v",
                "--cov=.",
                "--cov-report=html:reports/coverage",
                "--cov-report=term",
                "--html=reports/unit_tests.html",
                "--junitxml=reports/unit_tests.xml"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            return {
                "status": "passed" if result.returncode == 0 else "failed",
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration": time.time() - self.start_time
            }
            
        except Exception as e:
            logger.error(f"❌ Error running unit tests: {e}")
            return {"status": "error", "error": str(e)}
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests"""
        logger.info("🔗 Running integration tests...")
        
        try:
            test_dir = self.project_root / "tests" / "integration"
            
            result = subprocess.run([
                sys.executable, "-m", "pytest",
                str(test_dir),
                "-v",
                "-m", "integration",
                "--html=reports/integration_tests.html",
                "--junitxml=reports/integration_tests.xml"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            return {
                "status": "passed" if result.returncode == 0 else "failed",
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except Exception as e:
            logger.error(f"❌ Error running integration tests: {e}")
            return {"status": "error", "error": str(e)}
    
    def run_security_tests(self) -> Dict[str, Any]:
        """Run security and penetration tests"""
        logger.info("🔒 Running security tests...")
        
        try:
            test_dir = self.project_root / "tests" / "security"
            
            result = subprocess.run([
                sys.executable, "-m", "pytest",
                str(test_dir),
                "-v",
                "-m", "security",
                "--html=reports/security_tests.html",
                "--junitxml=reports/security_tests.xml"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            return {
                "status": "passed" if result.returncode == 0 else "failed",
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except Exception as e:
            logger.error(f"❌ Error running security tests: {e}")
            return {"status": "error", "error": str(e)}
    
    def run_load_tests(self, duration: int = 60, users: int = 10) -> Dict[str, Any]:
        """Run load tests using Locust"""
        logger.info(f"⚡ Running load tests (Duration: {duration}s, Users: {users})...")
        
        try:
            locust_file = self.project_root / "tests" / "load" / "locustfile.py"
            
            if not locust_file.exists():
                logger.warning("[WARN] Locust file not found, skipping load tests")
                return {"status": "skipped", "reason": "locustfile.py not found"}
            
            # Run Locust in headless mode
            result = subprocess.run([
                sys.executable, "-m", "locust",
                "-f", str(locust_file),
                "--headless",
                "--users", str(users),
                "--spawn-rate", "2",
                "--run-time", f"{duration}s",
                "--html", "reports/load_test_report.html",
                "--csv", "reports/load_test"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            return {
                "status": "passed" if result.returncode == 0 else "failed",
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except Exception as e:
            logger.error(f"❌ Error running load tests: {e}")
            return {"status": "error", "error": str(e)}
    
    def run_formal_verification(self) -> Dict[str, Any]:
        """Run formal verification tests"""
        logger.info("📐 Running formal verification...")
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest",
                "tests/unit/test_formal_verification.py",
                "-v",
                "-m", "formal_verification",
                "--html=reports/formal_verification.html",
                "--junitxml=reports/formal_verification.xml"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            return {
                "status": "passed" if result.returncode == 0 else "failed",
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except Exception as e:
            logger.error(f"❌ Error running formal verification: {e}")
            return {"status": "error", "error": str(e)}
    
    def generate_report(self) -> None:
        """Generate comprehensive test report"""
        logger.info("[INFO] Generating comprehensive test report...")
        
        try:
            # Create reports directory
            reports_dir = self.project_root / "reports"
            reports_dir.mkdir(exist_ok=True)
            
            # Calculate total duration
            total_duration = time.time() - self.start_time
            
            # Create summary report
            summary = {
                "phase": "Phase 4 - Testing & Verification",
                "execution_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_duration_seconds": total_duration,
                "test_results": self.test_results,
                "summary": {
                    "total_test_suites": len(self.test_results),
                    "passed_suites": sum(1 for r in self.test_results.values() if r.get("status") == "passed"),
                    "failed_suites": sum(1 for r in self.test_results.values() if r.get("status") == "failed"),
                    "error_suites": sum(1 for r in self.test_results.values() if r.get("status") == "error"),
                    "skipped_suites": sum(1 for r in self.test_results.values() if r.get("status") == "skipped")
                }
            }
              # Write JSON report
            with open(reports_dir / "phase4_test_summary.json", "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)
            
            # Write markdown report
            self._generate_markdown_report(summary, reports_dir / "phase4_test_report.md")
            
            logger.info(f"[DONE] Reports generated in {reports_dir}")
            
        except Exception as e:
            logger.error(f"[ERROR] Error generating report: {e}")
    
    def _generate_markdown_report(self, summary: Dict[str, Any], file_path: Path) -> None:
        """Generate markdown test report"""
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("# Phase 4 Testing & Verification Report\n\n")
            f.write(f"**Execution Time:** {summary['execution_time']}  \n")
            f.write(f"**Total Duration:** {summary['total_duration_seconds']:.2f} seconds  \n\n")
            
            f.write("## Summary\n\n")
            f.write(f"- **Total Test Suites:** {summary['summary']['total_test_suites']}\n")
            f.write(f"- **Passed:** {summary['summary']['passed_suites']}\n")
            f.write(f"- **Failed:** {summary['summary']['failed_suites']}\n")
            f.write(f"- **Errors:** {summary['summary']['error_suites']}\n")
            f.write(f"- **Skipped:** {summary['summary']['skipped_suites']}\n\n")
            
            f.write("## Test Suite Results\n\n")
            for suite_name, result in summary['test_results'].items():
                status_emoji = {
                    "passed": "[PASS]",
                    "failed": "[FAIL]",
                    "error": "[ERROR]",
                    "skipped": "[SKIP]"
                }.get(result.get("status"), "[UNKNOWN]")
                
                f.write(f"### {status_emoji} {suite_name.replace('_', ' ').title()}\n\n")
                f.write(f"**Status:** {result.get('status', 'unknown')}  \n")
                
                if result.get('duration'):
                    f.write(f"**Duration:** {result['duration']:.2f} seconds  \n")
                
                if result.get('returncode') is not None:
                    f.write(f"**Return Code:** {result['returncode']}  \n")
                
                if result.get('error'):
                    f.write(f"**Error:** {result['error']}  \n")
                
                f.write("\n")
            
            f.write("## Files Generated\n\n")
            f.write("- `phase4_test_summary.json` - JSON summary of all test results\n")
            f.write("- `unit_tests.html` - Unit test coverage report\n")
            f.write("- `integration_tests.html` - Integration test results\n")
            f.write("- `security_tests.html` - Security test results\n")
            f.write("- `formal_verification.html` - Formal verification results\n")
            f.write("- `load_test_report.html` - Load test performance report\n")
    
    def run_all_tests(self, load_test_duration: int = 60, load_test_users: int = 10) -> None:
        """Run complete Phase 4 test suite"""
        logger.info("[START] Starting Phase 4 Testing & Verification")
        logger.info("=" * 60)
        
        # Create reports directory
        reports_dir = self.project_root / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        # Install dependencies
        if not self.install_dependencies():
            logger.error("❌ Failed to install dependencies, aborting tests")
            return
        
        # Run test suites
        test_suites = [
            ("formal_verification", self.run_formal_verification),
            ("unit_tests", self.run_unit_tests),
            ("integration_tests", self.run_integration_tests),
            ("security_tests", self.run_security_tests),
            ("load_tests", lambda: self.run_load_tests(load_test_duration, load_test_users))
        ]
        
        for suite_name, test_function in test_suites:
            logger.info(f"\n{'='*20} {suite_name.replace('_', ' ').title()} {'='*20}")
            
            suite_start = time.time()
            result = test_function()
            suite_duration = time.time() - suite_start
            
            result['duration'] = suite_duration
            self.test_results[suite_name] = result
            
            if result['status'] == 'passed':
                logger.info(f"[PASS] {suite_name} completed successfully in {suite_duration:.2f}s")
            elif result['status'] == 'failed':
                logger.warning(f"[FAIL] {suite_name} completed with failures in {suite_duration:.2f}s")
            elif result['status'] == 'error':
                logger.error(f"❌ {suite_name} encountered errors in {suite_duration:.2f}s")
            elif result['status'] == 'skipped':
                logger.info(f"⏭️ {suite_name} was skipped")
        
        # Generate comprehensive report
        self.generate_report()
        
        # Print final summary
        total_duration = time.time() - self.start_time
        logger.info(f"\n{'='*60}")
        logger.info("[COMPLETE] Phase 4 Testing Complete")
        logger.info(f"Total Duration: {total_duration:.2f} seconds")
        
        passed = sum(1 for r in self.test_results.values() if r.get("status") == "passed")
        total = len(self.test_results)
        
        if passed == total:
            logger.info("🎉 All test suites passed successfully!")
        else:
            logger.warning(f"[SUMMARY] {passed}/{total} test suites passed")
        
        logger.info(f"[INFO] Detailed reports available in: {reports_dir}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Phase 4 Testing & Verification")
    parser.add_argument("--load-duration", type=int, default=60, 
                       help="Load test duration in seconds (default: 60)")
    parser.add_argument("--load-users", type=int, default=10,
                       help="Number of load test users (default: 10)")
    parser.add_argument("--suite", choices=[
        "all", "unit", "integration", "security", "load", "formal"
    ], default="all", help="Test suite to run (default: all)")
    
    args = parser.parse_args()
    
    # Determine project root
    script_dir = Path(__file__).parent.absolute()
    project_root = script_dir
    
    # Initialize test runner
    runner = Phase4TestRunner(project_root)
    
    if args.suite == "all":
        runner.run_all_tests(args.load_duration, args.load_users)
    elif args.suite == "unit":
        runner.install_dependencies()
        result = runner.run_unit_tests()
        logger.info(f"Unit tests: {result['status']}")
    elif args.suite == "integration":
        runner.install_dependencies()
        result = runner.run_integration_tests()
        logger.info(f"Integration tests: {result['status']}")
    elif args.suite == "security":
        runner.install_dependencies()
        result = runner.run_security_tests()
        logger.info(f"Security tests: {result['status']}")
    elif args.suite == "load":
        runner.install_dependencies()
        result = runner.run_load_tests(args.load_duration, args.load_users)
        logger.info(f"Load tests: {result['status']}")
    elif args.suite == "formal":
        runner.install_dependencies()
        result = runner.run_formal_verification()
        logger.info(f"Formal verification: {result['status']}")

if __name__ == "__main__":
    main()
