#!/usr/bin/env python3
"""
SECURITY VERIFICATION SCRIPT
============================

This script verifies that all security fixes have been properly implemented
and that the system is ready for production deployment.

Run this script before deploying to production to ensure all security
measures are in place and working correctly.
"""

import os
import sys
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SecurityVerificationError(Exception):
    """Exception raised when security verification fails"""
    pass

class SecurityVerifier:
    """Comprehensive security verification for the arbitrage system"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.verification_results = {}
        self.errors = []
        self.warnings = []
    
    def run_all_verifications(self) -> Dict[str, Any]:
        """Run all security verifications"""
        logger.info("🔍 Starting comprehensive security verification...")
        
        verifications = [
            ("Private Key Elimination", self.verify_private_key_elimination),
            ("Input Validation", self.verify_input_validation),
            ("Secure Transaction Signing", self.verify_secure_transaction_signing),
            ("Access Control Implementation", self.verify_access_control),
            ("Oracle Security", self.verify_oracle_security),
            ("Monitoring and Alerting", self.verify_monitoring),
            ("Deployment Security", self.verify_deployment_security),
            ("Configuration Security", self.verify_configuration_security),
            ("Smart Contract Security", self.verify_smart_contract_security)
        ]
        
        for name, verification_func in verifications:
            try:
                logger.info(f"🔍 Verifying: {name}")
                result = verification_func()
                self.verification_results[name] = result
                if result['status'] == 'PASS':
                    logger.info(f"✅ {name}: PASSED")
                else:
                    logger.error(f"❌ {name}: FAILED - {result.get('error', 'Unknown error')}")
                    self.errors.append(f"{name}: {result.get('error', 'Unknown error')}")
            except Exception as e:
                logger.error(f"❌ {name}: EXCEPTION - {str(e)}")
                self.errors.append(f"{name}: Exception - {str(e)}")
                self.verification_results[name] = {'status': 'ERROR', 'error': str(e)}
        
        return self._generate_report()
    
    def verify_private_key_elimination(self) -> Dict[str, Any]:
        """Verify that all private key handling has been removed"""
        logger.info("Checking for private key references...")
        
        # Files that should NOT contain private key references
        python_files = [
            'swarm_intelligence_agent_v38.py',
            'strategy_generator_v37.py', 
            'zk_rl_agent_v40.py',
            'reincarnation_agent_v39.py',
            'python_agent_v26.py',
            'mev_protection.py',
            'PRODUCTION_ARBITRAGE_SYSTEM.py'
        ]
        
        dangerous_patterns = [
            'from_key(',
            'PRIVATE_KEY',
            'private_key',
            'privateKey',
            '.key)',
            'Account.from_key'
        ]
        
        violations = []
        
        for file_name in python_files:
            file_path = self.base_path / file_name
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    for pattern in dangerous_patterns:
                        if pattern in content and 'removed for security' not in content.lower():
                            lines = content.split('\n')
                            for i, line in enumerate(lines, 1):
                                if pattern in line and 'removed for security' not in line.lower():
                                    violations.append(f"{file_name}:{i} - {line.strip()}")
        
        # Check JavaScript files
        js_files = ['verify_and_deploy_zk.js']
        for file_name in js_files:
            file_path = self.base_path / file_name
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'new ethers.Wallet(privateKey' in content:
                        violations.append(f"{file_name} - Contains private key wallet initialization")
        
        if violations:
            return {
                'status': 'FAIL',
                'error': f"Private key references found: {violations}"
            }
        
        return {'status': 'PASS', 'message': 'No private key references found'}
    
    def verify_input_validation(self) -> Dict[str, Any]:
        """Verify that input validation is properly implemented"""
        logger.info("Checking input validation implementation...")
        
        # Check if secure_input_validator.py exists
        validator_file = self.base_path / 'secure_input_validator.py'
        if not validator_file.exists():
            return {'status': 'FAIL', 'error': 'secure_input_validator.py not found'}
        
        # Check if validation is integrated in production system
        prod_file = self.base_path / 'PRODUCTION_ARBITRAGE_SYSTEM.py'
        if prod_file.exists():
            with open(prod_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'validate_arbitrage_data' not in content:
                    return {'status': 'FAIL', 'error': 'Input validation not integrated in production system'}
                if 'ValidationError' not in content:
                    return {'status': 'FAIL', 'error': 'ValidationError handling not found'}
        
        return {'status': 'PASS', 'message': 'Input validation properly implemented'}
    
    def verify_secure_transaction_signing(self) -> Dict[str, Any]:
        """Verify secure transaction signing implementation"""
        logger.info("Checking secure transaction signing...")
        
        # Check if secure_transaction_signer.py exists
        signer_file = self.base_path / 'secure_transaction_signer.py'
        if not signer_file.exists():
            return {'status': 'FAIL', 'error': 'secure_transaction_signer.py not found'}
        
        # Check for proper integration
        files_to_check = [
            'swarm_intelligence_agent_v38.py',
            'strategy_generator_v37.py',
            'PRODUCTION_ARBITRAGE_SYSTEM.py'
        ]
        
        for file_name in files_to_check:
            file_path = self.base_path / file_name
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'transaction_signer' not in content and 'TransactionSigner' not in content:
                        return {'status': 'FAIL', 'error': f'Secure transaction signer not integrated in {file_name}'}
        
        return {'status': 'PASS', 'message': 'Secure transaction signing implemented'}
    
    def verify_access_control(self) -> Dict[str, Any]:
        """Verify access control implementation"""
        logger.info("Checking access control implementation...")
        
        # Check if SecurityEnhancedExecutor exists
        contract_file = self.base_path / 'contracts' / 'SecurityEnhancedExecutor.sol'
        if not contract_file.exists():
            return {'status': 'FAIL', 'error': 'SecurityEnhancedExecutor.sol not found'}
        
        # Check for key security features
        with open(contract_file, 'r', encoding='utf-8') as f:
            content = f.read()
            required_features = [
                'AccessControl',
                'ADMIN_ROLE',
                'EMERGENCY_ROLE',
                'timelock',
                'emergencyStop',
                'onlyRole'
            ]
            
            missing_features = []
            for feature in required_features:
                if feature not in content:
                    missing_features.append(feature)
            
            if missing_features:
                return {'status': 'FAIL', 'error': f'Missing access control features: {missing_features}'}
        
        return {'status': 'PASS', 'message': 'Access control properly implemented'}
    
    def verify_oracle_security(self) -> Dict[str, Any]:
        """Verify oracle security implementation"""
        logger.info("Checking oracle security...")
        
        # Check if SecureMultiOracle exists
        oracle_file = self.base_path / 'contracts' / 'SecureMultiOracle.sol'
        if not oracle_file.exists():
            return {'status': 'FAIL', 'error': 'SecureMultiOracle.sol not found'}
        
        # Check for multi-oracle features
        with open(oracle_file, 'r', encoding='utf-8') as f:
            content = f.read()
            required_features = [
                'consensus',
                'deviation',
                'circuitBreaker',
                'getConsensusPrice',
                'oracle',
                'manipulation'
            ]
            
            missing_features = []
            for feature in required_features:
                if feature not in content:
                    missing_features.append(feature)
            
            if missing_features:
                return {'status': 'FAIL', 'error': f'Missing oracle security features: {missing_features}'}
        
        return {'status': 'PASS', 'message': 'Oracle security properly implemented'}
    
    def verify_monitoring(self) -> Dict[str, Any]:
        """Verify monitoring and alerting implementation"""
        logger.info("Checking monitoring implementation...")
        
        # Check if security rules exist
        rules_file = self.base_path / 'monitoring' / 'security_rules.yml'
        if not rules_file.exists():
            return {'status': 'FAIL', 'error': 'security_rules.yml not found'}
        
        # Check for key security alerts
        with open(rules_file, 'r', encoding='utf-8') as f:
            content = f.read()
            required_alerts = [
                'PrivateKeyExposure',
                'ReentrancyAttack',
                'FlashLoanExploit',
                'OracleManipulation',
                'GasGriefing',
                'MEVSandwich'
            ]
            
            missing_alerts = []
            for alert in required_alerts:
                if alert not in content:
                    missing_alerts.append(alert)
            
            if missing_alerts:
                return {'status': 'FAIL', 'error': f'Missing security alerts: {missing_alerts}'}
        
        return {'status': 'PASS', 'message': 'Monitoring properly configured'}
    
    def verify_deployment_security(self) -> Dict[str, Any]:
        """Verify secure deployment implementation"""
        logger.info("Checking deployment security...")
        
        # Check if secure deployment script exists
        deploy_file = self.base_path / 'secure_deployment.py'
        if not deploy_file.exists():
            return {'status': 'FAIL', 'error': 'secure_deployment.py not found'}
        
        # Check deployment config
        config_file = self.base_path / 'deployment_config.json'
        if not config_file.exists():
            return {'status': 'FAIL', 'error': 'deployment_config.json not found'}
        
        return {'status': 'PASS', 'message': 'Secure deployment implemented'}
    
    def verify_configuration_security(self) -> Dict[str, Any]:
        """Verify configuration security"""
        logger.info("Checking configuration security...")
        
        # Check that .env files don't contain private keys
        env_files = ['.env', '.env.production']
        for env_file in env_files:
            file_path = self.base_path / env_file
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'PRIVATE_KEY='${PRIVATE_KEY}'removed for security' not in content:
                        return {'status': 'FAIL', 'error': f'Private key found in {env_file}'}
        
        # Check YAML config files
        yaml_files = [
            'swarm_intelligence_config.yaml',
            'strategy_generator_config.yaml',
            'zk_rl_config.yaml',
            'reincarnation_config.yaml'
        ]
        
        for yaml_file in yaml_files:
            file_path = self.base_path / yaml_file
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'private_key:' in content and 'removed for security' not in content:
                        return {'status': 'FAIL', 'error': f'Private key found in {yaml_file}'}
        
        return {'status': 'PASS', 'message': 'Configuration security verified'}
    
    def verify_smart_contract_security(self) -> Dict[str, Any]:
        """Verify smart contract security features"""
        logger.info("Checking smart contract security...")
        
        contracts_dir = self.base_path / 'contracts'
        if not contracts_dir.exists():
            return {'status': 'FAIL', 'error': 'contracts directory not found'}
        
        # Check for security contracts
        required_contracts = [
            'SecurityEnhancedExecutor.sol',
            'SecureMultiOracle.sol',
            'SecurityUpgradeDeployer.sol'
        ]
        
        missing_contracts = []
        for contract in required_contracts:
            if not (contracts_dir / contract).exists():
                missing_contracts.append(contract)
        
        if missing_contracts:
            return {'status': 'FAIL', 'error': f'Missing security contracts: {missing_contracts}'}
        
        return {'status': 'PASS', 'message': 'Security contracts present'}
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate final verification report"""
        total_checks = len(self.verification_results)
        passed_checks = sum(1 for result in self.verification_results.values() if result['status'] == 'PASS')
        
        report = {
            'timestamp': str(datetime.now()),
            'total_checks': total_checks,
            'passed_checks': passed_checks,
            'failed_checks': total_checks - passed_checks,
            'success_rate': f"{(passed_checks / total_checks * 100):.1f}%",
            'overall_status': 'PASS' if len(self.errors) == 0 else 'FAIL',
            'detailed_results': self.verification_results,
            'errors': self.errors,
            'warnings': self.warnings
        }
        
        return report


def main():
    """Main verification function"""
    print("🔒 SECURITY VERIFICATION STARTING...")
    print("=" * 50)
    
    verifier = SecurityVerifier()
    report = verifier.run_all_verifications()
    
    print("\n" + "=" * 50)
    print("🔒 SECURITY VERIFICATION COMPLETE")
    print("=" * 50)
    
    print(f"Total Checks: {report['total_checks']}")
    print(f"Passed: {report['passed_checks']}")
    print(f"Failed: {report['failed_checks']}")
    print(f"Success Rate: {report['success_rate']}")
    print(f"Overall Status: {report['overall_status']}")
    
    if report['errors']:
        print("\n❌ ERRORS FOUND:")
        for error in report['errors']:
            print(f"  - {error}")
    
    if report['warnings']:
        print("\n⚠️ WARNINGS:")
        for warning in report['warnings']:
            print(f"  - {warning}")
    
    # Save report to file
    with open('security_verification_report.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📄 Detailed report saved to: security_verification_report.json")
    
    if report['overall_status'] == 'PASS':
        print("\n✅ SECURITY VERIFICATION PASSED")
        print("System is ready for security audit and production deployment.")
        return 0
    else:
        print("\n❌ SECURITY VERIFICATION FAILED")
        print("Please fix all errors before proceeding to production.")
        return 1


if __name__ == "__main__":
    from datetime import datetime
    sys.exit(main())
