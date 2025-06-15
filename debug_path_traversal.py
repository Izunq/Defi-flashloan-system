#!/usr/bin/env python3
"""Debug path traversal pattern matching"""

import re

# Test patterns from emergency validator
dangerous_path_patterns = [
    r"\.\./",                           # Directory traversal ../
    r"\.\.\\",                          # Windows traversal ..\
    r"\.\.\.",                          # Multiple dots (any format)
    r"[/\\]etc[/\\]",                   # Unix system directories
    r"etc/passwd",                      # Direct passwd access
    r"/etc/passwd",                     # Absolute passwd path
    r"\\etc\\passwd",                   # Windows-style passwd
    r"%2e%2e%2f",                       # URL encoded ../
    r"%2e%2e%5c",                       # URL encoded ..\
    r"[cC]:[/\\]",                      # Windows drive roots C:/
    r"[cC]:\\\\",                       # Windows drive C:\\
    r"\.\.[\\/]\.\.[\\/]\.\.[\\/]",     # ../../../
    r"\.\.\\\.\.\\\.\.\\",              # ..\..\..\
    r"windows\\system32",               # Windows system32
    r"\\windows\\system32\\",           # Full Windows system32 path
    r"C:\\windows",                     # Windows paths
    r"%2e%2e%2f%2e%2e%2f%2e%2e%2f",     # URL encoded ../../../
    r"\.\.%252f\.\.%252f",              # Double URL encoded
    r"file:///",                        # File protocol
    r"~/\.\./",                         # Home directory traversal
    r"~[\\/]\.\.[\\/]",                 # Home with traversal
    r"~[\\/]\.\.",                      # Simplified home traversal
]

# Test payloads that are failing
test_payloads = [
    "../../../etc/passwd",
    "..\\..\\..\\windows\\system32\\config\\sam",
    "/etc/passwd",
    "C:\\windows\\system32\\config\\sam",
    "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
    "..%252f..%252f..%252fetc%252fpasswd",
    "file:///etc/passwd",
    "~/../../etc/passwd"
]

print("Testing path traversal patterns:")
print("=" * 50)

for payload in test_payloads:
    print(f"\nTesting payload: {payload}")
    matches = []
    
    for pattern in dangerous_path_patterns:
        try:
            if re.search(pattern, payload, re.IGNORECASE):
                matches.append(pattern)
        except Exception as e:
            print(f"  ERROR with pattern {pattern}: {e}")
    
    if matches:
        print(f"  MATCHED patterns: {matches}")
    else:
        print(f"  NO MATCHES - payload would pass validation")

print("\n" + "=" * 50)
print("Testing individual patterns that should match:")

# Test specific patterns that should match
test_cases = [
    ("../../../etc/passwd", r"\.\./"),
    ("../../../etc/passwd", r"etc/passwd"),
    ("/etc/passwd", r"/etc/passwd"),
    ("C:\\windows\\system32\\config\\sam", r"[cC]:[/\\]"),
    ("C:\\windows\\system32\\config\\sam", r"windows\\system32"),
    ("..\\..\\..\\windows\\system32\\config\\sam", r"\.\.\\"),
    ("..\\..\\..\\windows\\system32\\config\\sam", r"windows\\system32"),
]

for payload, pattern in test_cases:
    try:
        match = re.search(pattern, payload, re.IGNORECASE)
        if match:
            print(f"✓ MATCH: '{payload}' matched pattern '{pattern}'")
        else:
            print(f"✗ NO MATCH: '{payload}' did not match pattern '{pattern}'")
    except Exception as e:
        print(f"✗ ERROR: '{payload}' with pattern '{pattern}': {e}")
