#!/usr/bin/env python3
"""Debug the exact test scenario that's failing"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from emergency_input_sanitizer_fixed import emergency_sanitize_string

def test_like_framework(value, validation_type="string", description="test"):
    """Simulate how the test framework calls the emergency validator"""
    results = []
    
    # Test with emergency validator (mimic the test framework logic)
    try:
        if validation_type == "string" and emergency_sanitize_string:
            print(f"Testing {value} with emergency_sanitize_string...")
            emergency_sanitize_string(value)
            print("  -> emergency_sanitize_string completed without exception")
            results.append(("Emergency", True, [], []))
        else:
            print("  -> Validator not available or wrong type")
    except Exception as e:
        print(f"  -> emergency_sanitize_string raised exception: {type(e).__name__}: {e}")
        results.append(("Emergency", False, ["Security error"], ["security_violation"]))
    
    # Analyze results like the test framework
    for validator_name, actual_pass, warnings, security_flags in results:
        print(f"Result: {validator_name}, actual_pass={actual_pass}, security_flags={security_flags}")
        
        # Check the test assertion
        should_pass = False  # For security tests like path traversal
        if not should_pass:
            # Security tests should either fail validation OR have security flags
            condition = not actual_pass or len(security_flags) > 0
            print(f"Test condition: not actual_pass ({not actual_pass}) or len(security_flags) > 0 ({len(security_flags) > 0}) = {condition}")
            
    return results

# Test the failing case
print("Testing path traversal detection:")
print("=" * 50)
test_like_framework("../../../etc/passwd", "string", "Path traversal: ../../../etc/passwd")
