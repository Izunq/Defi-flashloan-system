#!/usr/bin/env python3
"""
Test Environment Setup Script

This script sets up the testing environment for the Flash Loan System,
including dependencies, test data, and mock services.
"""

import os
import sys
import json
import shutil
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('TestSetup')

class TestEnvironmentSetup:
    """Setup and manage test environment."""
    
    def __init__(self, project_root: Path):
        """Initialize the test environment setup."""
        self.project_root = project_root
        self.test_data_dir = project_root / 'test_data'
        self.temp_dir = None
        
    def setup_complete_environment(self) -> bool:
        """Setup complete test environment."""
        logger.info("🔧 Setting up complete test environment...")
        
        try:
            # Create necessary directories
            self._create_directories()
            
            # Install dependencies
            self._install_dependencies()
            
            # Setup test data
            self._setup_test_data()
            
            # Setup mock services
            self._setup_mock_services()
            
            # Verify environment
            self._verify_environment()
            
            logger.info("✅ Test environment setup complete!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup test environment: {e}")
            return False
    
    def _create_directories(self):
        """Create necessary test directories."""
        logger.info("📁 Creating test directories...")
        
        directories = [
            'test_data',
            'test_results',
            'test_logs',
            'mock_data',
            'coverage_reports',
            'performance_reports'
        ]
        
        for dir_name in directories:
            dir_path = self.project_root / dir_name
            dir_path.mkdir(exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
    
    def _install_dependencies(self):
        """Install test dependencies."""
        logger.info("📦 Installing test dependencies...")
        
        # Upgrade pip first
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'
        ], check=True)
        
        # Install requirements files in order
        requirements_files = [
            'requirements.txt',
            'requirements_test.txt',
            'requirements_fixed.txt'
        ]
        
        for req_file in requirements_files:
            req_path = self.project_root / req_file
            if req_path.exists():
                logger.info(f"Installing from {req_file}...")
                try:
                    subprocess.run([
                        sys.executable, '-m', 'pip', 'install', '-r', str(req_path)
                    ], check=True, capture_output=True)
                    logger.info(f"✅ Installed from {req_file}")
                except subprocess.CalledProcessError as e:
                    logger.warning(f"⚠️  Failed to install from {req_file}: {e}")
    
    def _setup_test_data(self):
        """Setup test data files."""
        logger.info("📊 Setting up test data...")
        
        # Create mock price data
        mock_price_data = {
            'ETH': {
                'current_price': 2000.0,
                'historical_prices': [
                    {'timestamp': 1640995200, 'price': 1900.0, 'volume': 1000000},
                    {'timestamp': 1641081600, 'price': 1950.0, 'volume': 1100000},
                    {'timestamp': 1641168000, 'price': 2000.0, 'volume': 1200000},
                    {'timestamp': 1641254400, 'price': 2050.0, 'volume': 1150000},
                    {'timestamp': 1641340800, 'price': 2000.0, 'volume': 1000000}
                ]
            },
            'BTC': {
                'current_price': 60000.0,
                'historical_prices': [
                    {'timestamp': 1640995200, 'price': 58000.0, 'volume': 500000},
                    {'timestamp': 1641081600, 'price': 59000.0, 'volume': 550000},
                    {'timestamp': 1641168000, 'price': 60000.0, 'volume': 600000},
                    {'timestamp': 1641254400, 'price': 61000.0, 'volume': 575000},
                    {'timestamp': 1641340800, 'price': 60000.0, 'volume': 500000}
                ]
            }
        }
        
        with open(self.test_data_dir / 'mock_price_data.json', 'w') as f:
            json.dump(mock_price_data, f, indent=2)
        
        # Create test configuration
        test_config = {
            'test_mode': True,
            'use_mock_data': True,
            'database_url': 'sqlite:///:memory:',
            'web3_provider': 'http://localhost:8545',
            'timeout_seconds': 30,
            'max_retries': 3,
            'log_level': 'INFO'
        }
        
        with open(self.test_data_dir / 'test_config.json', 'w') as f:
            json.dump(test_config, f, indent=2)
        
        # Create mock contract ABIs
        mock_abi = [
            {
                "inputs": [{"name": "asset", "type": "bytes32"}],
                "name": "getPrice",
                "outputs": [
                    {"name": "price", "type": "uint256"},
                    {"name": "timestamp", "type": "uint256"},
                    {"name": "isValid", "type": "bool"}
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        with open(self.test_data_dir / 'mock_contract_abi.json', 'w') as f:
            json.dump(mock_abi, f, indent=2)
        
        # Create security test payloads
        security_payloads = {
            'sql_injection': [
                "'; DROP TABLE users; --",
                "' OR '1'='1",
                "' UNION SELECT * FROM passwords --"
            ],
            'xss': [
                "<script>alert('xss')</script>",
                "<img src=x onerror=alert(1)>",
                "javascript:alert('xss')"
            ],
            'command_injection': [
                "; rm -rf /",
                "| cat /etc/passwd",
                "&& echo vulnerable"
            ]
        }
        
        with open(self.test_data_dir / 'security_payloads.json', 'w') as f:
            json.dump(security_payloads, f, indent=2)
        
        logger.info("✅ Test data setup complete")
    
    def _setup_mock_services(self):
        """Setup mock services for testing."""
        logger.info("🔧 Setting up mock services...")
        
        # Create mock oracle service configuration
        mock_oracle_config = {
            'oracles': {
                'chainlink': {
                    'url': 'http://localhost:8546/chainlink',
                    'timeout': 30,
                    'weight': 0.4
                },
                'uniswap': {
                    'url': 'http://localhost:8546/uniswap',
                    'timeout': 30,
                    'weight': 0.3
                },
                'binance': {
                    'url': 'http://localhost:8546/binance',
                    'timeout': 30,
                    'weight': 0.3
                }
            }
        }
        
        with open(self.test_data_dir / 'mock_oracle_config.json', 'w') as f:
            json.dump(mock_oracle_config, f, indent=2)
        
        # Create environment variables file for testing
        env_vars = {
            'TESTING': 'true',
            'TEST_MODE': 'true',
            'WEB3_PROVIDER_URL': 'http://localhost:8545',
            'DATABASE_URL': 'sqlite:///:memory:',
            'LOG_LEVEL': 'INFO',
            'REDIS_URL': 'redis://localhost:6379/0',
            'ETHEREUM_NETWORK': 'ganache',
            'PRIVATE_KEY': '0x' + '0' * 64  # Mock private key for testing
        }
        
        env_file_content = '\n'.join([f'{k}={v}' for k, v in env_vars.items()])
        
        with open(self.test_data_dir / '.env.test', 'w') as f:
            f.write(env_file_content)
        
        logger.info("✅ Mock services setup complete")
    
    def _verify_environment(self):
        """Verify the test environment is properly setup."""
        logger.info("🔍 Verifying test environment...")
        
        # Check Python version
        python_version = sys.version_info
        if python_version.major < 3 or python_version.minor < 8:
            raise RuntimeError(f"Python 3.8+ required, found {python_version.major}.{python_version.minor}")
        
        # Check required packages
        required_packages = [
            'pytest',
            'pytest-asyncio',
            'pytest-cov',
            'web3',
            'requests',
            'numpy',
            'pandas'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            logger.warning(f"Missing packages: {missing_packages}")
        
        # Check test data files
        required_files = [
            'mock_price_data.json',
            'test_config.json',
            'mock_contract_abi.json',
            'security_payloads.json'
        ]
        
        for file_name in required_files:
            file_path = self.test_data_dir / file_name
            if not file_path.exists():
                raise FileNotFoundError(f"Required test file not found: {file_path}")
        
        logger.info("✅ Environment verification complete")
    
    def cleanup_environment(self):
        """Cleanup test environment."""
        logger.info("🧹 Cleaning up test environment...")
        
        # Remove temporary files
        temp_patterns = [
            '*.tmp',
            '*.cache',
            '__pycache__',
            '.pytest_cache',
            '*.log',
            '.coverage'
        ]
        
        for pattern in temp_patterns:
            for file_path in self.project_root.glob(f"**/{pattern}"):
                try:
                    if file_path.is_file():
                        file_path.unlink()
                    elif file_path.is_dir():
                        shutil.rmtree(file_path)
                    logger.info(f"Removed: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to remove {file_path}: {e}")
        
        logger.info("✅ Cleanup complete")
    
    def run_environment_check(self) -> Dict[str, Any]:
        """Run comprehensive environment check."""
        logger.info("🔍 Running comprehensive environment check...")
        
        check_results = {
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'python_executable': sys.executable,
            'working_directory': str(Path.cwd()),
            'project_root': str(self.project_root),
            'environment_variables': {},
            'installed_packages': {},
            'test_data_files': {},
            'directories': {}
        }
        
        # Check environment variables
        test_env_vars = [
            'TESTING', 'TEST_MODE', 'WEB3_PROVIDER_URL', 'DATABASE_URL'
        ]
        
        for env_var in test_env_vars:
            check_results['environment_variables'][env_var] = os.environ.get(env_var, 'Not Set')
        
        # Check installed packages
        try:
            import pkg_resources
            installed_packages = {pkg.project_name: pkg.version 
                                for pkg in pkg_resources.working_set}
            check_results['installed_packages'] = installed_packages
        except Exception as e:
            check_results['installed_packages'] = {'error': str(e)}
        
        # Check test data files
        if self.test_data_dir.exists():
            for file_path in self.test_data_dir.iterdir():
                if file_path.is_file():
                    check_results['test_data_files'][file_path.name] = {
                        'exists': True,
                        'size': file_path.stat().st_size
                    }
        
        # Check directories
        test_dirs = ['test_data', 'test_results', 'test_logs']
        for dir_name in test_dirs:
            dir_path = self.project_root / dir_name
            check_results['directories'][dir_name] = {
                'exists': dir_path.exists(),
                'path': str(dir_path)
            }
        
        return check_results

def main():
    """Main function for test environment setup."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup test environment for Flash Loan System')
    parser.add_argument('--project-root', type=Path, default=Path.cwd(), 
                       help='Project root directory')
    parser.add_argument('--setup', action='store_true', 
                       help='Setup complete test environment')
    parser.add_argument('--check', action='store_true', 
                       help='Check environment status')
    parser.add_argument('--cleanup', action='store_true', 
                       help='Cleanup test environment')
    
    args = parser.parse_args()
    
    setup = TestEnvironmentSetup(args.project_root)
    
    if args.setup:
        success = setup.setup_complete_environment()
        sys.exit(0 if success else 1)
    
    elif args.check:
        results = setup.run_environment_check()
        print(json.dumps(results, indent=2))
    
    elif args.cleanup:
        setup.cleanup_environment()
    
    else:
        print("Please specify an action: --setup, --check, or --cleanup")
        sys.exit(1)

if __name__ == '__main__':
    main()
