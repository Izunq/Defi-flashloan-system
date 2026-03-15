#!/usr/bin/env python3
"""
Simple Input Validation Test without Web3 dependencies
"""

import re
import html
import urllib.parse
from typing import Any, Dict, List, Optional, Union

class SimpleInputValidator:
    """Simple validator for testing without external dependencies"""
    
    # Refined SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"[\'\"];.*\b(union\s+select|drop\s+table|delete\s+from|insert\s+into)\b",
        r"\'\s*or\s*[\'\"]?\d+[\'\"]?\s*=\s*[\'\"]?\d+[\'\"]?",
        r"\'\s*union\s+select\b",
        r"\'\s*;.*\b(drop|delete|insert|update|exec)\b",
        r"\'\s*--",
        r";\s*(exec|execute)\s*\(",
        r";\s*waitfor\s+delay",
        r"\'\s*and\s+benchmark\s*\(",
    ]
    
    # Refined XSS patterns  
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"<iframe[^>]*src\s*=.*javascript:",
        r"<img[^>]*onerror\s*=",
        r"<[^>]*\s+on(click|load|error|focus|blur|change|submit)\s*=.*[\'\"][^\'\"]*[\'\"]",
        r"javascript:\s*[^;]+[;\(]",
        r"vbscript:\s*[^;]+[;\(]",
    ]
    
    def __init__(self):
        self.dangerous_addresses = {
            "${CONTRACT_ADDRESS}",
            "${CONTRACT_ADDRESS}", 
            "${CONTRACT_ADDRESS}",
        }
        
        # Add precompile addresses (0x01-0x09)
        for i in range(1, 10):
            self.dangerous_addresses.add(f"0x{i:040x}")
    
    def validate_string(self, value: str) -> Dict[str, Any]:
        """Validate string input"""
        if not isinstance(value, str):
            value = str(value)
        
        # Check SQL injection patterns
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE | re.DOTALL):
                return {"valid": False, "reason": "SQL injection pattern detected"}
        
        # Check XSS patterns
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE | re.DOTALL):
                return {"valid": False, "reason": "XSS pattern detected"}
        
        return {"valid": True, "sanitized": html.escape(value)}
    
    def validate_address(self, value: str) -> Dict[str, Any]:
        """Validate Ethereum address"""
        if not isinstance(value, str):
            value = str(value)
        
        # Basic format validation
        if not value.startswith('0x') or len(value) != 42:
            return {"valid": False, "reason": "Invalid address format"}
        
        # Hex validation
        try:
            hex_part = value[2:]
            int(hex_part, 16)
        except ValueError:
            return {"valid": False, "reason": "Invalid hex characters"}
        
        # Check dangerous addresses
        if value.lower() in [addr.lower() for addr in self.dangerous_addresses]:
            return {"valid": False, "reason": "Dangerous address"}
        
        return {"valid": True, "address": value}

def test_validation():
    """Test the validation fixes"""
    validator = SimpleInputValidator()
    
    print("Input Validation Fix Test")
    print("=" * 40)
    
    # SQL injection tests
    print("\n1. SQL Injection Tests:")
    sql_tests = [
        ("'; DROP TABLE users; --", False),
        ("' OR '1'='1", False), 
        ("' UNION SELECT * FROM passwords --", False),
        ("admin'--", False),
        ("normal text", True),
        ("user@example.com", True),
        ("It's a beautiful day", True),
    ]
    
    sql_correct = 0
    for text, should_pass in sql_tests:
        result = validator.validate_string(text)
        actual_pass = result["valid"]
        if actual_pass == should_pass:
            sql_correct += 1
            print(f"  ✓ {text[:25]:<25} {'PASS' if should_pass else 'BLOCK'}")
        else:
            print(f"  ✗ {text[:25]:<25} Expected {'PASS' if should_pass else 'BLOCK'}, got {'PASS' if actual_pass else 'BLOCK'}")
    
    sql_rate = (sql_correct / len(sql_tests)) * 100
    
    # XSS tests
    print("\n2. XSS Tests:")
    xss_tests = [
        ("<script>alert('xss')</script>", False),
        ("<img src=x onerror=alert(1)>", False),
        ("javascript:alert('xss')", False),
        ("<iframe src='javascript:alert(1)'></iframe>", False),
        ("Check out <example.com>", True),
        ("Price: $100 < $200", True),
        ("Email: user@domain.com", True),
    ]
    
    xss_correct = 0
    for text, should_pass in xss_tests:
        result = validator.validate_string(text)
        actual_pass = result["valid"]
        if actual_pass == should_pass:
            xss_correct += 1
            print(f"  ✓ {text[:25]:<25} {'PASS' if should_pass else 'BLOCK'}")
        else:
            print(f"  ✗ {text[:25]:<25} Expected {'PASS' if should_pass else 'BLOCK'}, got {'PASS' if actual_pass else 'BLOCK'}")
    
    xss_rate = (xss_correct / len(xss_tests)) * 100
    
    # Address tests
    print("\n3. Address Validation Tests:")
    addr_tests = [
        ("${CONTRACT_ADDRESS}", True),
        ("${CONTRACT_ADDRESS}", False),
        ("${CONTRACT_ADDRESS}", False),
        ("${CONTRACT_ADDRESS}", False),
        ("${CONTRACT_ADDRESS}", False),
        ("invalid_address", False),
        ("0x742dA73Fe8e4B0b42d9D1B6C3F4d1F7b7b5c5c", False),
        ("${CONTRACT_ADDRESS}5c", False),
    ]
    
    addr_correct = 0
    for addr, should_pass in addr_tests:
        result = validator.validate_address(addr)
        actual_pass = result["valid"]
        if actual_pass == should_pass:
            addr_correct += 1
            print(f"  ✓ {addr[:25]:<25} {'PASS' if should_pass else 'BLOCK'}")
        else:
            print(f"  ✗ {addr[:25]:<25} Expected {'PASS' if should_pass else 'BLOCK'}, got {'PASS' if actual_pass else 'BLOCK'}")
    
    addr_rate = (addr_correct / len(addr_tests)) * 100
    
    # Summary
    print("\n" + "=" * 40)
    print("RESULTS:")
    print(f"SQL Injection Tests: {sql_correct}/{len(sql_tests)} ({sql_rate:.1f}%)")
    print(f"XSS Tests: {xss_correct}/{len(xss_tests)} ({xss_rate:.1f}%)")
    print(f"Address Tests: {addr_correct}/{len(addr_tests)} ({addr_rate:.1f}%)")
    
    overall_rate = (sql_rate + xss_rate + addr_rate) / 3
    print(f"\nOverall Success Rate: {overall_rate:.1f}%")
    
    if overall_rate >= 95:
        print("🎉 TARGET ACHIEVED! 95%+ success rate")
    elif overall_rate >= 80:
        print("✅ Good progress! Above 80% success rate")
    else:
        print("⚠️  More improvements needed")
    
    return overall_rate

if __name__ == "__main__":
    test_validation()
