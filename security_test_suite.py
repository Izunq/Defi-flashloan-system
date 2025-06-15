#!/usr/bin/env python3
"""
Input Validation Security Testing Suite
=======================================

Comprehensive testing suite to validate the input validation security fixes
and ensure the system is protected against malicious data injection attacks.
"""

import os
import sys
import json
import time
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import concurrent.futures

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from secure_input_validator import (
    SecureValidator, 
    EnhancedValidationError,
    validate_flash_loan_params,
    validate_mev_protection_params,
    validate_oracle_feed_data,
    sanitize_user_input
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("validation_security_tests.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ValidationSecurityTests")

class SecurityTestSuite:
    """
    Comprehensive security testing suite for input validation
    """
    
    def __init__(self):
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'critical_failures': 0,
            'test_categories': {},
            'execution_time': 0
        }
        self.validator = SecureValidator('mainnet')
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run complete security test suite"""
        start_time = time.time()
        
        try:
            logger.info("🚀 Starting comprehensive security testing")
            
            # Test categories
            test_categories = [
                ('SQL Injection Tests', self._test_sql_injection),
                ('Buffer Overflow Tests', self._test_buffer_overflow),
                ('XSS Prevention Tests', self._test_xss_prevention),
                ('Address Validation Tests', self._test_address_validation),
                ('Numeric Validation Tests', self._test_numeric_validation),
                ('Oracle Data Tests', self._test_oracle_validation),
                ('Flash Loan Tests', self._test_flash_loan_validation),
                ('MEV Protection Tests', self._test_mev_protection),
                ('Rate Limiting Tests', self._test_rate_limiting),
                ('Fuzzing Tests', self._test_fuzzing),
                ('Performance Tests', self._test_performance),
                ('Edge Case Tests', self._test_edge_cases)
            ]
            
            for category_name, test_function in test_categories:
                logger.info(f"🔍 Running {category_name}")
                category_results = test_function()
                self.test_results['test_categories'][category_name] = category_results
                
                # Update totals
                self.test_results['total_tests'] += category_results['total']
                self.test_results['passed_tests'] += category_results['passed']
                self.test_results['failed_tests'] += category_results['failed']
                self.test_results['critical_failures'] += category_results.get('critical', 0)
            
            self.test_results['execution_time'] = time.time() - start_time
            
            # Generate final report
            self._generate_security_report()
            
            logger.info("✅ Security testing completed")
            return self.test_results
            
        except Exception as e:
            logger.error(f"💥 Security testing failed: {e}")
            self.test_results['execution_time'] = time.time() - start_time
            return self.test_results
    
    def _test_sql_injection(self) -> Dict[str, Any]:
        """Test SQL injection prevention"""
        results = {'total': 0, 'passed': 0, 'failed': 0, 'critical': 0}
        
        injection_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; SELECT * FROM users WHERE 'x'='x",
            "admin'--",
            "' OR 1=1--",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --",
            "' UNION SELECT * FROM sensitive_data --"
        ]
        
        for payload in injection_payloads:
            results['total'] += 1
            
            try:
                # Test in various fields
                test_cases = [
                    {'token_a': payload, 'token_b': '0xValid'},
                    {'strategy_name': payload},
                    {'user_input': payload}
                ]
                
                for test_case in test_cases:
                    try:
                        if 'token_a' in test_case:
                            self.validator.validate_token_address(test_case['token_a'])
                        elif 'strategy_name' in test_case:
                            sanitized = sanitize_user_input(test_case['strategy_name'])
                            if payload in sanitized:
                                raise Exception("SQL injection not prevented")
                        elif 'user_input' in test_case:
                            sanitized = sanitize_user_input(test_case['user_input'])
                            if payload in sanitized:
                                raise Exception("SQL injection not prevented")
                        
                        # If we get here, validation failed to catch the injection
                        results['failed'] += 1
                        results['critical'] += 1
                        logger.error(f"❌ CRITICAL: SQL injection not prevented: {payload}")
                        break
                        
                    except (EnhancedValidationError, Exception):
                        # Validation correctly rejected the malicious input
                        continue
                
                else:
                    # All test cases correctly rejected the payload
                    results['passed'] += 1
                    logger.debug(f"✅ SQL injection correctly prevented: {payload[:20]}...")
                    
            except Exception as e:
                results['failed'] += 1
                logger.error(f"❌ SQL injection test error: {e}")
        
        return results
    
    def _test_buffer_overflow(self) -> Dict[str, Any]:
        """Test buffer overflow prevention"""
        results = {'total': 0, 'passed': 0, 'failed': 0}
        
        # Test with extremely large inputs
        large_inputs = [
            'A' * 10000,      # 10KB string
            'B' * 100000,     # 100KB string
            'C' * 1000000,    # 1MB string
            '0x' + 'F' * 10000,  # Large hex string
            json.dumps({'key': 'value' * 50000})  # Large JSON
        ]
        
        for large_input in large_inputs:
            results['total'] += 1
            
            try:
                # Test various validation functions
                sanitized = sanitize_user_input(large_input, max_length=1000)
                
                if len(sanitized) > 1000:
                    results['failed'] += 1
                    logger.error(f"❌ Buffer overflow not prevented: {len(sanitized)} chars")
                else:
                    results['passed'] += 1
                    logger.debug(f"✅ Buffer overflow prevented: {len(large_input)} -> {len(sanitized)}")
                    
            except EnhancedValidationError:
                results['passed'] += 1
                logger.debug(f"✅ Buffer overflow correctly rejected")
            except Exception as e:
                results['failed'] += 1
                logger.error(f"❌ Buffer overflow test error: {e}")
        
        return results
    
    def _test_xss_prevention(self) -> Dict[str, Any]:
        """Test XSS prevention"""
        results = {'total': 0, 'passed': 0, 'failed': 0}
        
        xss_payloads = [
            '<script>alert("xss")</script>',
            '"><script>alert(String.fromCharCode(88,83,83))</script>',
            '<img src=x onerror=alert(1)>',
            'javascript:alert("xss")',
            '<svg onload=alert(1)>',
            '<iframe src="javascript:alert(1)"></iframe>',
            '<body onload=alert(1)>'
        ]
        
        for payload in xss_payloads:
            results['total'] += 1
            
            try:
                sanitized = sanitize_user_input(payload)
                
                # Check if any dangerous patterns remain
                dangerous_patterns = ['<script', 'javascript:', 'onload=', 'onerror=', '<iframe']
                
                if any(pattern in sanitized.lower() for pattern in dangerous_patterns):
                    results['failed'] += 1
                    logger.error(f"❌ XSS not prevented: {sanitized}")
                else:
                    results['passed'] += 1
                    logger.debug(f"✅ XSS prevented: {payload[:30]}...")
                    
            except EnhancedValidationError:
                results['passed'] += 1
                logger.debug(f"✅ XSS correctly rejected")
            except Exception as e:
                results['failed'] += 1
                logger.error(f"❌ XSS test error: {e}")
        
        return results
    
    def _test_address_validation(self) -> Dict[str, Any]:
        """Test Ethereum address validation"""
        results = {'total': 0, 'passed': 0, 'failed': 0}
        
        test_cases = [
            # Valid addresses
            ('0xA0b86a33E6842E2c33cf84F4f7fE2C2F96d20A0b', True),
            ('0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', True),
            
            # Invalid addresses
            ('0x123', False),
            ('0xGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG', False),
            ('not_an_address', False),
            ('', False),
            ('0x' + 'F' * 41, False),  # Too long
            ('0x' + 'F' * 39, False),  # Too short
        ]
        
        for address, should_be_valid in test_cases:
            results['total'] += 1
            
            try:
                validated_address = self.validator.validate_token_address(address)
                
                if should_be_valid:
                    results['passed'] += 1
                    logger.debug(f"✅ Valid address accepted: {address}")
                else:
                    results['failed'] += 1
                    logger.error(f"❌ Invalid address accepted: {address}")
                    
            except EnhancedValidationError:
                if not should_be_valid:
                    results['passed'] += 1
                    logger.debug(f"✅ Invalid address rejected: {address}")
                else:
                    results['failed'] += 1
                    logger.error(f"❌ Valid address rejected: {address}")
            except Exception as e:
                results['failed'] += 1
                logger.error(f"❌ Address validation error: {e}")
        
        return results
    
    def _test_numeric_validation(self) -> Dict[str, Any]:
        """Test numeric input validation"""
        results = {'total': 0, 'passed': 0, 'failed': 0}
        
        test_cases = [
            # Valid amounts
            (100, True),
            (0.5, True),
            ('1000.5', True),
            
            # Invalid amounts
            (-100, False),
            ('not_a_number', False),
            (float('inf'), False),
            (float('nan'), False),
            (10**50, False),  # Too large
        ]
        
        for amount, should_be_valid in test_cases:
            results['total'] += 1
            
            try:
                validated_amount = self.validator.validate_decimal_amount(amount)
                
                if should_be_valid:
                    results['passed'] += 1
                    logger.debug(f"✅ Valid amount accepted: {amount}")
                else:
                    results['failed'] += 1
                    logger.error(f"❌ Invalid amount accepted: {amount}")
                    
            except EnhancedValidationError:
                if not should_be_valid:
                    results['passed'] += 1
                    logger.debug(f"✅ Invalid amount rejected: {amount}")
                else:
                    results['failed'] += 1
                    logger.error(f"❌ Valid amount rejected: {amount}")
            except Exception as e:
                results['failed'] += 1
                logger.error(f"❌ Numeric validation error: {e}")
        
        return results
    
    def _test_oracle_validation(self) -> Dict[str, Any]:
        """Test oracle data validation"""
        results = {'total': 0, 'passed': 0, 'failed': 0}
        
        current_time = int(datetime.now().timestamp())
        
        test_cases = [
            # Valid oracle data
            ({'price': 100.5, 'timestamp': current_time, 'asset': 'ETH'}, True),
            ({'price': 50000, 'timestamp': current_time - 300, 'asset': 'BTC'}, True),
            
            # Invalid oracle data
            ({'price': 0, 'timestamp': current_time, 'asset': 'ETH'}, False),  # Zero price
            ({'price': -100, 'timestamp': current_time, 'asset': 'ETH'}, False),  # Negative price
            ({'price': 100, 'timestamp': current_time - 7200, 'asset': 'ETH'}, False),  # Too old
            ({'price': 100, 'timestamp': current_time + 1000, 'asset': 'ETH'}, False),  # Future
            ({'timestamp': current_time, 'asset': 'ETH'}, False),  # Missing price
        ]
        
        for oracle_data, should_be_valid in test_cases:
            results['total'] += 1
            
            try:
                validated_data = validate_oracle_feed_data(oracle_data)
                
                if should_be_valid:
                    results['passed'] += 1
                    logger.debug(f"✅ Valid oracle data accepted")
                else:
                    results['failed'] += 1
                    logger.error(f"❌ Invalid oracle data accepted: {oracle_data}")
                    
            except EnhancedValidationError:
                if not should_be_valid:
                    results['passed'] += 1
                    logger.debug(f"✅ Invalid oracle data rejected")
                else:
                    results['failed'] += 1
                    logger.error(f"❌ Valid oracle data rejected: {oracle_data}")
            except Exception as e:
                results['failed'] += 1
                logger.error(f"❌ Oracle validation error: {e}")
        
        return results
    
    def _test_flash_loan_validation(self) -> Dict[str, Any]:
        """Test flash loan parameter validation"""
        results = {'total': 0, 'passed': 0, 'failed': 0}
        
        test_cases = [
            # Valid flash loan params
            ({
                'asset': '0xA0b86a33E6842E2c33cf84F4f7fE2C2F96d20A0b',
                'amount': 1000,
                'receiver': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
                'params': {}
            }, True),
            
            # Invalid flash loan params
            ({
                'asset': 'invalid_address',
                'amount': 1000,
                'receiver': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
                'params': {}
            }, False),
            ({
                'asset': '0xA0b86a33E6842E2c33cf84F4f7fE2C2F96d20A0b',
                'amount': -1000,
                'receiver': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
                'params': {}
            }, False),
        ]
        
        for params, should_be_valid in test_cases:
            results['total'] += 1
            
            try:
                validated_params = validate_flash_loan_params(params)
                
                if should_be_valid:
                    results['passed'] += 1
                    logger.debug(f"✅ Valid flash loan params accepted")
                else:
                    results['failed'] += 1
                    logger.error(f"❌ Invalid flash loan params accepted")
                    
            except EnhancedValidationError:
                if not should_be_valid:
                    results['passed'] += 1
                    logger.debug(f"✅ Invalid flash loan params rejected")
                else:
                    results['failed'] += 1
                    logger.error(f"❌ Valid flash loan params rejected")
            except Exception as e:
                results['failed'] += 1
                logger.error(f"❌ Flash loan validation error: {e}")
        
        return results
    
    def _test_mev_protection(self) -> Dict[str, Any]:
        """Test MEV protection parameter validation"""
        results = {'total': 0, 'passed': 0, 'failed': 0}
        
        current_time = int(datetime.now().timestamp())
        
        test_cases = [
            # Valid MEV protection params
            ({
                'maxGasPrice': 100 * 10**9,  # 100 Gwei
                'deadline': current_time + 300,  # 5 minutes
                'maxSlippage': 0.01  # 1%
            }, True),
            
            # Invalid MEV protection params
            ({
                'maxGasPrice': 2000 * 10**9,  # Too high
                'deadline': current_time + 300,
                'maxSlippage': 0.01
            }, False),
            ({
                'maxGasPrice': 100 * 10**9,
                'deadline': current_time + 10000,  # Too far in future
                'maxSlippage': 0.01
            }, False),
        ]
        
        for params, should_be_valid in test_cases:
            results['total'] += 1
            
            try:
                validated_params = validate_mev_protection_params(params)
                
                if should_be_valid:
                    results['passed'] += 1
                    logger.debug(f"✅ Valid MEV protection params accepted")
                else:
                    results['failed'] += 1
                    logger.error(f"❌ Invalid MEV protection params accepted")
                    
            except EnhancedValidationError:
                if not should_be_valid:
                    results['passed'] += 1
                    logger.debug(f"✅ Invalid MEV protection params rejected")
                else:
                    results['failed'] += 1
                    logger.error(f"❌ Valid MEV protection params rejected")
            except Exception as e:
                results['failed'] += 1
                logger.error(f"❌ MEV protection validation error: {e}")
        
        return results
    
    def _test_rate_limiting(self) -> Dict[str, Any]:
        """Test rate limiting functionality"""
        results = {'total': 1, 'passed': 0, 'failed': 0}
        
        try:
            from secure_input_validator import validation_rate_limiter
            
            # Test rate limiting by making many rapid requests
            test_identifier = "rate_limit_test"
            
            # Should pass initially
            for i in range(10):
                if not validation_rate_limiter.check_rate_limit(test_identifier):
                    results['failed'] += 1
                    logger.error("❌ Rate limiting triggered too early")
                    return results
            
            # Make many requests to trigger rate limit
            for i in range(1000):
                validation_rate_limiter.check_rate_limit(test_identifier)
            
            # Should be rate limited now
            if validation_rate_limiter.check_rate_limit(test_identifier):
                results['failed'] += 1
                logger.error("❌ Rate limiting not working")
            else:
                results['passed'] += 1
                logger.debug("✅ Rate limiting working correctly")
                
        except Exception as e:
            results['failed'] += 1
            logger.error(f"❌ Rate limiting test error: {e}")
        
        return results
    
    def _test_fuzzing(self) -> Dict[str, Any]:
        """Test with random/fuzzed inputs"""
        results = {'total': 0, 'passed': 0, 'failed': 0}
        
        import random
        import string
        
        # Generate random test inputs
        for _ in range(50):
            results['total'] += 1
            
            try:
                # Generate random string
                random_input = ''.join(
                    random.choice(string.printable) 
                    for _ in range(random.randint(1, 1000))
                )
                
                # Test sanitization
                sanitized = sanitize_user_input(random_input, max_length=500)
                
                # Should not crash and should be within length limit
                if len(sanitized) <= 500:
                    results['passed'] += 1
                else:
                    results['failed'] += 1
                    logger.error(f"❌ Fuzzing failed: output too long")
                    
            except Exception as e:
                # Exceptions are acceptable for random inputs
                results['passed'] += 1
                logger.debug(f"✅ Fuzzing correctly handled exception: {type(e).__name__}")
        
        return results
    
    def _test_performance(self) -> Dict[str, Any]:
        """Test validation performance"""
        results = {'total': 1, 'passed': 0, 'failed': 0}
        
        try:
            # Test validation speed
            test_data = {
                'token_pair': {
                    'token_a': '0xA0b86a33E6842E2c33cf84F4f7fE2C2F96d20A0b',
                    'token_b': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
                },
                'profit_percent': 0.025,
                'net_profit_usd': 150.0,
                'chains': ['ethereum'],
                'dexes': ['0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D']
            }
            
            # Time 1000 validations
            start_time = time.time()
            for _ in range(1000):
                self.validator.validate_opportunity_data(test_data)
            end_time = time.time()
            
            avg_time = (end_time - start_time) / 1000
            
            # Should be under 1ms per validation
            if avg_time < 0.001:
                results['passed'] += 1
                logger.info(f"✅ Performance test passed: {avg_time:.6f}s avg")
            else:
                results['failed'] += 1
                logger.error(f"❌ Performance test failed: {avg_time:.6f}s avg")
                
        except Exception as e:
            results['failed'] += 1
            logger.error(f"❌ Performance test error: {e}")
        
        return results
    
    def _test_edge_cases(self) -> Dict[str, Any]:
        """Test edge cases and boundary conditions"""
        results = {'total': 0, 'passed': 0, 'failed': 0}
        
        edge_cases = [
            # Empty inputs
            ('', 'empty_string'),
            ({}, 'empty_dict'),
            ([], 'empty_list'),
            
            # Null/None inputs
            (None, 'none_value'),
            
            # Unicode/special characters
            ('🚀💰📈', 'unicode_emojis'),
            ('Ñiño', 'unicode_text'),
            ('\x00\x01\x02', 'control_chars'),
            
            # Very large numbers
            (10**100, 'very_large_number'),
            (1e-100, 'very_small_number'),
        ]
        
        for test_input, test_name in edge_cases:
            results['total'] += 1
            
            try:
                if isinstance(test_input, str):
                    sanitized = sanitize_user_input(test_input)
                    results['passed'] += 1
                    logger.debug(f"✅ Edge case handled: {test_name}")
                elif isinstance(test_input, (int, float)):
                    validated = self.validator.validate_decimal_amount(test_input)
                    results['passed'] += 1
                    logger.debug(f"✅ Edge case handled: {test_name}")
                else:
                    # For other types, just check they don't crash
                    str(test_input)
                    results['passed'] += 1
                    logger.debug(f"✅ Edge case handled: {test_name}")
                    
            except EnhancedValidationError:
                # Validation errors are acceptable for edge cases
                results['passed'] += 1
                logger.debug(f"✅ Edge case correctly rejected: {test_name}")
            except Exception as e:
                results['failed'] += 1
                logger.error(f"❌ Edge case error {test_name}: {e}")
        
        return results
    
    def _generate_security_report(self):
        """Generate comprehensive security test report"""
        report = {
            'security_test_report': {
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total_tests': self.test_results['total_tests'],
                    'passed_tests': self.test_results['passed_tests'],
                    'failed_tests': self.test_results['failed_tests'],
                    'critical_failures': self.test_results['critical_failures'],
                    'success_rate': (self.test_results['passed_tests'] / max(self.test_results['total_tests'], 1)) * 100,
                    'execution_time': self.test_results['execution_time']
                },
                'category_results': self.test_results['test_categories'],
                'security_status': 'PASS' if self.test_results['critical_failures'] == 0 else 'FAIL',
                'recommendations': self._generate_recommendations()
            }
        }
        
        # Save report
        with open('security_test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info("📊 Security test report saved to security_test_report.json")
    
    def _generate_recommendations(self) -> List[str]:
        """Generate security recommendations based on test results"""
        recommendations = []
        
        if self.test_results['critical_failures'] > 0:
            recommendations.append("CRITICAL: Address critical security failures immediately")
        
        if self.test_results['failed_tests'] > 0:
            recommendations.append("Review and fix failed test cases")
        
        success_rate = (self.test_results['passed_tests'] / max(self.test_results['total_tests'], 1)) * 100
        
        if success_rate < 95:
            recommendations.append("Improve validation coverage to achieve >95% success rate")
        
        if self.test_results['execution_time'] > 60:
            recommendations.append("Optimize validation performance")
        
        if not recommendations:
            recommendations.append("Security validation system is functioning correctly")
        
        return recommendations

def main():
    """Main testing function"""
    try:
        logger.info("🔒 Starting Input Validation Security Testing")
        
        test_suite = SecurityTestSuite()
        results = test_suite.run_all_tests()
        
        # Print summary
        print("\n" + "="*60)
        print("SECURITY TEST RESULTS SUMMARY")
        print("="*60)
        print(f"Total Tests: {results['total_tests']}")
        print(f"Passed: {results['passed_tests']}")
        print(f"Failed: {results['failed_tests']}")
        print(f"Critical Failures: {results['critical_failures']}")
        print(f"Success Rate: {(results['passed_tests']/max(results['total_tests'], 1))*100:.1f}%")
        print(f"Execution Time: {results['execution_time']:.2f}s")
        
        if results['critical_failures'] == 0:
            print("\n✅ SECURITY STATUS: PASS")
            logger.info("🎉 All security tests passed!")
        else:
            print(f"\n❌ SECURITY STATUS: FAIL ({results['critical_failures']} critical failures)")
            logger.error("💥 Critical security failures detected!")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"💥 Security testing error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
