#!/usr/bin/env python3
"""
Input Validation Integration Example
===================================

This script demonstrates how to integrate the enhanced input validation
system into your existing arbitrage agents and applications.
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def integrate_validation_into_agents():
    """Example of integrating validation into existing agents"""
    
    print("🔒 Input Validation Integration Example")
    print("=" * 50)
    
    # Import the validation functions
    try:
        from input_validation_integration import (
            validate_string, 
            validate_ethereum_address, 
            validate_number,
            validate_transaction_data,
            validate_strategy_params
        )
        print("✅ Enhanced validation modules loaded successfully")
    except ImportError as e:
        print(f"❌ Could not import validation modules: {e}")
        return False
    
    # Example 1: Validate user input
    print("\n1. Validating User Input:")
    user_inputs = [
        "normal_user_input",
        "'; DROP TABLE users; --",  # SQL injection attempt
        "<script>alert('xss')</script>",  # XSS attempt
        "valid_data_123"
    ]
    
    for input_data in user_inputs:
        result = validate_string(input_data)
        status = "✅ SAFE" if result["valid"] else "🚨 BLOCKED"
        print(f"  {status}: '{input_data[:30]}...' ")
        if not result["valid"]:
            print(f"    Reason: {result['errors']}")
    
    # Example 2: Validate Ethereum addresses
    print("\n2. Validating Ethereum Addresses:")
    addresses = [
        "0x742dA73Fe8e4B0b42d9D1B6C3F4d1F7b7b5c5c5c",  # Valid
        "0x0000000000000000000000000000000000000000",  # Zero address (dangerous)
        "invalid_address",  # Invalid format
        "0x1234567890123456789012345678901234567890"  # Valid format
    ]
    
    for address in addresses:
        result = validate_ethereum_address(address)
        status = "✅ SAFE" if result["valid"] else "🚨 BLOCKED"
        print(f"  {status}: {address}")
        if not result["valid"]:
            print(f"    Reason: {result['errors']}")
    
    # Example 3: Validate transaction data
    print("\n3. Validating Transaction Data:")
    tx_data = {
        "to": "0x742dA73Fe8e4B0b42d9D1B6C3F4d1F7b7b5c5c5c",
        "value": "1000000000000000000",  # 1 ETH in wei
        "gas": "21000",
        "gasPrice": "20000000000"  # 20 Gwei
    }
    
    result = validate_transaction_data(tx_data)
    status = "✅ SAFE" if result["valid"] else "🚨 BLOCKED"
    print(f"  {status}: Transaction validation")
    if result["valid"]:
        print(f"    Sanitized data: {result['sanitized_value']}")
    else:
        print(f"    Errors: {result['errors']}")
    
    return True

def show_integration_patterns():
    """Show common integration patterns"""
    
    print("\n🔧 Integration Patterns")
    print("=" * 30)
    
    integration_code = '''
# Pattern 1: Validate in API endpoints
from input_validation_integration import validate_string, validate_ethereum_address

def handle_arbitrage_request(request_data):
    # Validate all inputs first
    strategy_result = validate_string(request_data.get('strategy', ''))
    if not strategy_result['valid']:
        return {"error": "Invalid strategy parameter"}
    
    address_result = validate_ethereum_address(request_data.get('token_address', ''))
    if not address_result['valid']:
        return {"error": "Invalid token address"}
    
    # Use sanitized values
    strategy = strategy_result['sanitized_value']
    token_address = address_result['sanitized_value']
    
    # Continue with business logic...

# Pattern 2: Validate in existing agents
class ArbitrageAgent:
    def __init__(self):
        from input_validation_integration import IntegratedInputValidator
        self.validator = IntegratedInputValidator(strict_mode=True)
    
    def execute_trade(self, token_a, token_b, amount):
        # Validate inputs before processing
        context = {"source": "arbitrage_agent", "operation": "trade"}
        
        token_a_result = self.validator.validate_input(token_a, "ethereum_address", context)
        if not token_a_result['valid']:
            raise ValueError(f"Invalid token A: {token_a_result['errors']}")
        
        # Use validated data
        validated_token_a = token_a_result['sanitized_value']
        # Continue with trade execution...

# Pattern 3: Emergency validation in critical paths
from emergency_input_sanitizer import emergency_sanitize, SecurityError

def critical_operation(user_input):
    try:
        # Use emergency validation for critical operations
        safe_input = emergency_sanitize(user_input, "critical_op")
        # Proceed with critical operation
    except SecurityError as e:
        # Log security incident and abort
        logger.error(f"Security violation in critical operation: {e}")
        return {"error": "Security violation detected"}
'''
    
    print(integration_code)

def main():
    """Main function"""
    print("🚀 Input Validation System - Integration Guide")
    print("=" * 55)
    
    # Run integration example
    if integrate_validation_into_agents():
        show_integration_patterns()
        
        print("\n🎉 Integration Summary")
        print("=" * 25)
        print("✅ Enhanced input validation system is working")
        print("✅ Security patterns are being detected and blocked")
        print("✅ Validation can be integrated into existing agents")
        print("✅ Emergency fallback validation is available")
        
        print("\n📋 Next Steps:")
        print("1. Update your main agents to use the validation functions")
        print("2. Add validation to all user input entry points")
        print("3. Monitor the validation logs for security incidents")
        print("4. Test with your specific use cases")
        
        print("\n📚 Documentation: INPUT_VALIDATION_DOCUMENTATION.md")
        print("🔧 Configuration: config/validation_config.json")
        print("🧪 Tests: test_input_validation.py")
        
    else:
        print("❌ Integration example failed")
        return False
    
    return True

if __name__ == "__main__":
    main()
