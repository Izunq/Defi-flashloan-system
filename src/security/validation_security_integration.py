#!/usr/bin/env python3
"""
Input Validation Security Integration Script
============================================

This script integrates enhanced input validation across all Python agents
and applies security hardening to prevent malicious data injection attacks.
"""

import os
import sys
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from secure_input_validator import (
    SecureValidator, 
    EnhancedValidationError,
    validate_flash_loan_params,
    validate_mev_protection_params,
    validate_oracle_feed_data,
    validate_batch_operation,
    sanitize_user_input,
    rate_limited_validation
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("validation_integration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ValidationIntegration")

class ValidationSecurityManager:
    """
    Manages security validation across all system components
    """
    
    def __init__(self, config_path: str = "config_ultimate.yaml"):
        self.config_path = config_path
        self.validators = {}
        self.validation_stats = {
            'total_validations': 0,
            'failed_validations': 0,
            'security_events': 0,
            'last_validation': None
        }
        self._initialize_validators()
    
    def _initialize_validators(self):
        """Initialize validators for different networks"""
        networks = ['mainnet', 'polygon', 'arbitrum', 'optimism']
        
        for network in networks:
            try:
                self.validators[network] = SecureValidator(network)
                logger.info(f"✅ Initialized validator for {network}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize validator for {network}: {e}")
    
    @rate_limited_validation("general")
    def validate_agent_input(self, agent_id: str, input_data: Dict[str, Any], 
                           network: str = 'mainnet') -> Dict[str, Any]:
        """
        Validate input data for any agent with comprehensive security checks
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"🔍 Validating input for agent {agent_id} on {network}")
            
            # Get appropriate validator
            if network not in self.validators:
                raise EnhancedValidationError(f"No validator available for network: {network}")
            
            validator = self.validators[network]
            validated_data = {}
            
            # Validate based on input type
            if 'type' in input_data:
                input_type = input_data['type']
                
                if input_type == 'arbitrage_opportunity':
                    validated_data = validator.validate_opportunity_data(input_data.get('data', {}))
                
                elif input_type == 'flash_loan_request':
                    validated_data = validate_flash_loan_params(input_data.get('data', {}), network)
                
                elif input_type == 'strategy_execution':
                    validated_data = validator.validate_strategy_params(input_data.get('data', {}))
                
                elif input_type == 'oracle_update':
                    validated_data = validate_oracle_feed_data(input_data.get('data', {}))
                
                elif input_type == 'mev_protection':
                    validated_data = validate_mev_protection_params(input_data.get('data', {}))
                
                elif input_type == 'batch_operation':
                    operations = input_data.get('operations', [])
                    validated_data = {'operations': validate_batch_operation(operations, network)}
                
                elif input_type == 'network_config':
                    validated_data = validator.validate_network_config(input_data.get('data', {}))
                
                elif input_type == 'transaction_data':
                    validated_data = validator.validate_transaction_data(input_data.get('data', {}))
                
                else:
                    # Generic validation for unknown types
                    validated_data = self._validate_generic_input(input_data, validator)
            
            else:
                # No type specified, apply generic validation
                validated_data = self._validate_generic_input(input_data, validator)
            
            # Record successful validation
            self.validation_stats['total_validations'] += 1
            self.validation_stats['last_validation'] = datetime.now()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Validation successful for agent {agent_id} (took {execution_time:.3f}s)")
            
            return {
                'status': 'valid',
                'data': validated_data,
                'agent_id': agent_id,
                'network': network,
                'validation_time': execution_time,
                'timestamp': datetime.now().isoformat()
            }
            
        except EnhancedValidationError as e:
            self.validation_stats['failed_validations'] += 1
            self.validation_stats['security_events'] += 1
            
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ Validation failed for agent {agent_id}: {e}")
            
            return {
                'status': 'invalid',
                'error': str(e),
                'field': getattr(e, 'field', None),
                'context': getattr(e, 'context', {}),
                'agent_id': agent_id,
                'network': network,
                'validation_time': execution_time,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            self.validation_stats['failed_validations'] += 1
            self.validation_stats['security_events'] += 1
            
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"💥 Unexpected validation error for agent {agent_id}: {e}")
            
            return {
                'status': 'error',
                'error': f"Unexpected validation error: {e}",
                'agent_id': agent_id,
                'network': network,
                'validation_time': execution_time,
                'timestamp': datetime.now().isoformat()
            }
    
    def _validate_generic_input(self, input_data: Dict[str, Any], 
                              validator: SecureValidator) -> Dict[str, Any]:
        """Apply generic validation to unknown input types"""
        validated = {}
        
        for key, value in input_data.items():
            try:
                # Apply appropriate validation based on key name and value type
                if 'address' in key.lower() and isinstance(value, str):
                    if len(value) == 42 and value.startswith('0x'):
                        validated[key] = validator.validate_token_address(value)
                    else:
                        validated[key] = sanitize_user_input(value)
                
                elif 'amount' in key.lower() and isinstance(value, (int, float, str)):
                    validated[key] = validator.validate_decimal_amount(value)
                
                elif 'percent' in key.lower() and isinstance(value, (int, float, str)):
                    validated[key] = validator.validate_profit_percent(value)
                
                elif 'gas' in key.lower() and isinstance(value, (int, str)):
                    validated[key] = validator.validate_gas_price(value)
                
                elif isinstance(value, str):
                    validated[key] = sanitize_user_input(value)
                
                elif isinstance(value, dict):
                    validated[key] = self._validate_generic_input(value, validator)
                
                elif isinstance(value, list):
                    validated[key] = [
                        self._validate_generic_input(item, validator) if isinstance(item, dict)
                        else sanitize_user_input(str(item)) if isinstance(item, str)
                        else item
                        for item in value
                    ]
                
                else:
                    validated[key] = value
                    
            except Exception as e:
                logger.warning(f"Failed to validate field {key}: {e}")
                # Skip invalid fields rather than failing entire validation
                continue
        
        return validated
    
    def validate_agent_config(self, agent_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate agent configuration parameters"""
        try:
            logger.info(f"🔧 Validating configuration for agent {agent_id}")
            
            validated_config = {}
            
            # Validate network configurations
            if 'networks' in config:
                validated_config['networks'] = {}
                for network_name, network_config in config['networks'].items():
                    validator = self.validators.get(network_name, self.validators['mainnet'])
                    validated_config['networks'][network_name] = validator.validate_network_config(network_config)
            
            # Validate trading parameters
            if 'trading' in config:
                validated_config['trading'] = self._validate_trading_config(config['trading'])
            
            # Validate security parameters
            if 'security' in config:
                validated_config['security'] = self._validate_security_config(config['security'])
            
            # Validate MEV protection
            if 'mev_protection' in config:
                validated_config['mev_protection'] = validate_mev_protection_params(config['mev_protection'])
            
            # Copy other configuration as-is after sanitization
            for key, value in config.items():
                if key not in validated_config:
                    if isinstance(value, str):
                        validated_config[key] = sanitize_user_input(value)
                    elif isinstance(value, dict):
                        validated_config[key] = self._sanitize_dict(value)
                    else:
                        validated_config[key] = value
            
            logger.info(f"✅ Configuration validation successful for agent {agent_id}")
            return validated_config
            
        except Exception as e:
            logger.error(f"❌ Configuration validation failed for agent {agent_id}: {e}")
            raise EnhancedValidationError(f"Agent configuration validation failed: {e}")
    
    def _validate_trading_config(self, trading_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate trading-specific configuration"""
        validated = {}
        validator = self.validators['mainnet']  # Use mainnet validator as default
        
        # Min profit validation
        if 'min_profit_usd' in trading_config:
            min_profit = trading_config['min_profit_usd']
            if isinstance(min_profit, (int, float)) and min_profit >= 0:
                validated['min_profit_usd'] = float(min_profit)
            else:
                raise EnhancedValidationError(f"Invalid min_profit_usd: {min_profit}")
        
        # Slippage validation
        if 'max_slippage' in trading_config:
            validated['max_slippage'] = validator.validate_profit_percent(trading_config['max_slippage'])
        
        # Gas price validation
        if 'max_gas_price' in trading_config:
            validated['max_gas_price'] = validator.validate_gas_price(trading_config['max_gas_price'])
        
        # Copy other parameters
        for key, value in trading_config.items():
            if key not in validated:
                validated[key] = value
        
        return validated
    
    def _validate_security_config(self, security_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate security-specific configuration"""
        validated = {}
        
        # Rate limiting configuration
        if 'rate_limit' in security_config:
            rate_config = security_config['rate_limit']
            if isinstance(rate_config, dict):
                if 'max_requests' in rate_config:
                    max_req = rate_config['max_requests']
                    if isinstance(max_req, int) and max_req > 0:
                        validated['rate_limit'] = {'max_requests': max_req}
                    else:
                        raise EnhancedValidationError(f"Invalid max_requests: {max_req}")
        
        # Whitelist validation
        if 'whitelisted_addresses' in security_config:
            whitelist = security_config['whitelisted_addresses']
            if isinstance(whitelist, list):
                validated_whitelist = []
                validator = self.validators['mainnet']
                for addr in whitelist:
                    try:
                        validated_whitelist.append(validator.validate_token_address(addr))
                    except Exception:
                        logger.warning(f"Invalid address in whitelist: {addr}")
                        continue
                validated['whitelisted_addresses'] = validated_whitelist
        
        # Copy other security parameters
        for key, value in security_config.items():
            if key not in validated:
                validated[key] = value
        
        return validated
    
    def _sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize dictionary values"""
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = sanitize_user_input(value)
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    sanitize_user_input(item) if isinstance(item, str)
                    else self._sanitize_dict(item) if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        return {
            **self.validation_stats,
            'active_validators': list(self.validators.keys()),
            'uptime': datetime.now().isoformat()
        }
    
    def reset_validation_stats(self):
        """Reset validation statistics"""
        self.validation_stats = {
            'total_validations': 0,
            'failed_validations': 0,
            'security_events': 0,
            'last_validation': None
        }
        logger.info("📊 Validation statistics reset")

def main():
    """Main integration function"""
    try:
        logger.info("🚀 Starting Input Validation Security Integration")
        
        # Initialize validation manager
        validation_manager = ValidationSecurityManager()
        
        # Test with sample data
        sample_arbitrage_data = {
            'type': 'arbitrage_opportunity',
            'data': {
                'token_pair': {
                    'token_a': '${CONTRACT_ADDRESS}',
                    'token_b': '${CONTRACT_ADDRESS}'
                },
                'profit_percent': 0.025,  # 2.5%
                'net_profit_usd': 150.0,
                'chains': ['ethereum'],
                'dexes': ['${CONTRACT_ADDRESS}']
            }
        }
        
        # Test validation
        result = validation_manager.validate_agent_input(
            'test_agent', 
            sample_arbitrage_data, 
            'mainnet'
        )
        
        if result['status'] == 'valid':
            logger.info("✅ Sample validation test passed")
        else:
            logger.error(f"❌ Sample validation test failed: {result.get('error')}")
        
        # Print statistics
        stats = validation_manager.get_validation_stats()
        logger.info(f"📊 Validation Statistics: {stats}")
        
        logger.info("🎉 Input Validation Security Integration completed successfully")
        
    except Exception as e:
        logger.error(f"💥 Integration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
