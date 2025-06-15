#!/usr/bin/env python3
"""Quick test script for input validation"""

try:
    from enhanced_input_validator import EnhancedInputValidator
    print("Enhanced validator imported successfully")
    
    validator = EnhancedInputValidator(strict_mode=True)
    print("Validator created")
    
    # Test SQL injection
    test_cases = [
        ("normal text", True, "Normal text"),
        ("'; DROP TABLE users; --", False, "SQL injection"),
        ("<script>alert('xss')</script>", False, "XSS attack"),
        ("0x742dA73Fe8e4B0b42d9D1B6C3F4d1F7b7b5c5c5c", True, "Valid address"),
        ("0x0000000000000000000000000000000000000000", False, "Zero address"),
    ]
    
    print("\nValidation Results:")
    print("=" * 50)
    
    for value, expected_valid, description in test_cases:
        try:
            if description.endswith("address"):
                result = validator.validate_with_context(value, "ethereum_address")
            else:
                result = validator.validate_with_context(value, "string")
            
            status = "PASS" if result.is_valid == expected_valid else "FAIL"
            print(f"{status}: {description}")
            print(f"  Input: {value}")
            print(f"  Expected: {'Valid' if expected_valid else 'Invalid'}")
            print(f"  Actual: {'Valid' if result.is_valid else 'Invalid'}")
            print(f"  Security flags: {result.security_flags}")
            print(f"  Warnings: {result.warnings}")
            print()
            
        except Exception as e:
            status = "PASS" if not expected_valid else "FAIL" 
            print(f"{status}: {description}")
            print(f"  Input: {value}")
            print(f"  Exception: {str(e)}")
            print()
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
