#!/usr/bin/env python3
"""Debug emergency validator behavior"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from emergency_input_sanitizer_fixed import emergency_sanitize_string

# Test payloads that are failing
test_payloads = [
    "../../../etc/passwd",
    "/etc/passwd",
    "C:\\windows\\system32\\config\\sam",
]

print("Testing emergency validator directly:")
print("=" * 50)

for payload in test_payloads:
    print(f"\nTesting payload: {payload}")
    try:
        result = emergency_sanitize_string(payload)
        print(f"  PASSED - result: {result}")
    except Exception as e:
        print(f"  BLOCKED - exception: {type(e).__name__}: {e}")
