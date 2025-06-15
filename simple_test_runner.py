#!/usr/bin/env python3
"""
Simple Test Runner - Windows Compatible

A simple test runner that works reliably on Windows systems.
"""

import subprocess
import sys
import time
from pathlib import Path

def run_simple_tests():
    """Run a simple set of tests."""
    print("Flash Loan System - Test Runner")
    print("=" * 50)
    
    # Check if pytest is available
    try:
        result = subprocess.run([sys.executable, '-m', 'pytest', '--version'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("ERROR: pytest is not installed")
            print("Please run: pip install pytest pytest-asyncio")
            return False
    except Exception as e:
        print(f"ERROR: Failed to check pytest: {e}")
        return False
    
    print("Starting basic test validation...")
    
    # List of basic tests to run
    test_files = [
        'test_input_validation.py',
        'test_enhanced_oracle_security_fixed.py'
    ]
    
    passed_tests = 0
    failed_tests = 0
    
    for test_file in test_files:
        test_path = Path(test_file)
        if test_path.exists():
            print(f"\nRunning {test_file}...")
            try:
                result = subprocess.run([
                    sys.executable, '-m', 'pytest', 
                    str(test_path), 
                    '-v', '--tb=short', '--timeout=60', '-x'
                ], capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    print(f"PASS: {test_file}")
                    passed_tests += 1
                else:
                    print(f"FAIL: {test_file}")
                    failed_tests += 1
                    if result.stdout:
                        print("STDOUT:", result.stdout[-500:])  # Last 500 chars
                    if result.stderr:
                        print("STDERR:", result.stderr[-500:])  # Last 500 chars
                        
            except subprocess.TimeoutExpired:
                print(f"TIMEOUT: {test_file}")
                failed_tests += 1
            except Exception as e:
                print(f"ERROR: {test_file} - {e}")
                failed_tests += 1
        else:
            print(f"SKIP: {test_file} (not found)")
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    
    if failed_tests == 0 and passed_tests > 0:
        print("SUCCESS: All available tests passed!")
        return True
    else:
        print("FAILURE: Some tests failed or no tests found")
        return False

def check_environment():
    """Check the test environment."""
    print("Checking test environment...")
    
    # Check Python version
    print(f"Python version: {sys.version}")
    
    # Check if required files exist
    required_files = [
        'conftest.py',
        'pytest.ini',
        'requirements.txt'
    ]
    
    for file_name in required_files:
        if Path(file_name).exists():
            print(f"Found: {file_name}")
        else:
            print(f"Missing: {file_name}")
    
    # Check if test files exist
    test_files = list(Path('.').glob('test_*.py'))
    print(f"Found {len(test_files)} test files")
    
    # Try to import pytest
    try:
        import pytest
        print(f"pytest version: {pytest.__version__}")
    except ImportError:
        print("WARNING: pytest not installed")
        return False
    
    return True

def install_basic_dependencies():
    """Install basic test dependencies."""
    print("Installing basic test dependencies...")
    
    basic_packages = [
        'pytest>=7.4.0',
        'pytest-asyncio>=0.21.1',
        'pytest-timeout>=2.1.0'
    ]
    
    for package in basic_packages:
        try:
            print(f"Installing {package}...")
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', package
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"Installed: {package}")
            else:
                print(f"Failed to install: {package}")
                print(result.stderr)
        except Exception as e:
            print(f"Error installing {package}: {e}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'check':
            check_environment()
        elif command == 'install':
            install_basic_dependencies()
        elif command == 'test':
            success = run_simple_tests()
            sys.exit(0 if success else 1)
        else:
            print("Usage: python simple_test_runner.py [check|install|test]")
    else:
        print("Flash Loan System - Simple Test Runner")
        print("Usage:")
        print("  python simple_test_runner.py check   - Check environment")
        print("  python simple_test_runner.py install - Install dependencies")
        print("  python simple_test_runner.py test    - Run basic tests")
