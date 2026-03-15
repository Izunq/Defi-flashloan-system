#!/usr/bin/env python3
"""
Simple Emergency Sanitizer Test
"""

from emergency_input_sanitizer import emergency_sanitize, emergency_validate_eth_address

def test_sanitizer():
    print("🔍 Testing Emergency Input Sanitizer Functions...")
    
    # Test SQL injection
    try:
        result = emergency_sanitize("'; DROP TABLE users; --", "sql_test")
        print(f"❌ SQL injection not blocked: {result}")
    except Exception as e:
        print(f"✅ SQL injection blocked: {str(e)[:50]}...")
    
    # Test XSS
    try:
        result = emergency_sanitize("<script>alert('xss')</script>", "xss_test")
        print(f"❌ XSS not blocked: {result}")
    except Exception as e:
        print(f"✅ XSS blocked: {str(e)[:50]}...")
    
    # Test valid input
    try:
        result = emergency_sanitize("normal_input_123", "test_field")
        print(f"✅ Valid input passed: {result}")
    except Exception as e:
        print(f"❌ Valid input blocked: {e}")
    
    # Test address validation
    try:
        result = emergency_validate_eth_address("${CONTRACT_ADDRESS}")
        print(f"✅ Valid address: {result}")
    except Exception as e:
        print(f"❌ Valid address rejected: {e}")
    
    try:
        result = emergency_validate_eth_address("${CONTRACT_ADDRESS}")
        print(f"❌ Zero address not blocked: {result}")
    except Exception as e:
        print(f"✅ Zero address blocked: {str(e)[:50]}...")

if __name__ == "__main__":
    test_sanitizer()
