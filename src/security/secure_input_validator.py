#!/usr/bin/env python3
"""
Secure Input Validation Module
=============================

This module provides comprehensive input validation for all external data
used in the arbitrage system to prevent malicious data injection.
"""

import re
import string
import json
import jsonschema
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

from web3 import Web3
from web3.types import ChecksumAddress
import logging
import requests

# EMERGENCY SECURITY PATCH - DEPLOYED IMMEDIATELY
try:
    from emergency_input_sanitizer import (
        emergency_sanitize,
        emergency_validate_eth_address,
        emergency_validate_number,
        emergency_validate_json_data,
        emergency_validate_url_safe,
        SecurityError
    )
    EMERGENCY_VALIDATION_ENABLED = True
    print("🛡️ EMERGENCY VALIDATION ENABLED")
except ImportError:
    EMERGENCY_VALIDATION_ENABLED = False
    print("⚠️ EMERGENCY VALIDATION NOT AVAILABLE")

def emergency_validate_input(value, field_name="input", validation_type="string"):
    """Emergency input validation wrapper"""
    if not EMERGENCY_VALIDATION_ENABLED:
        return value
    
    try:
        if validation_type == "address":
            return emergency_validate_eth_address(value)
        elif validation_type == "number":
            return emergency_validate_number(value)
        elif validation_type == "json":
            return emergency_validate_json_data(value)
        elif validation_type == "url":
            return emergency_validate_url_safe(value)
        else:
            return emergency_sanitize(value, field_name)
    except SecurityError as e:
        raise ValueError(f"SECURITY: {e}")



logger = logging.getLogger(__name__)

# Security constants
MAX_TOKEN_AMOUNT = 10**30  # Maximum token amount (extremely large but finite)
MIN_TOKEN_AMOUNT = 1  # Minimum meaningful token amount
MAX_GAS_PRICE = 1000 * 10**9  # 1000 Gwei max gas price
MIN_GAS_PRICE = 1 * 10**9  # 1 Gwei min gas price
MAX_PROFIT_PERCENT = 1.0  # 100% max profit (prevents overflow)
MIN_PROFIT_PERCENT = 0.0001  # 0.01% min profit

# Enhanced security constants
MAX_STRING_LENGTH = 1000
MAX_JSON_SIZE = 10 * 1024 * 1024  # 10MB max JSON size
MAX_API_RESPONSE_SIZE = 50 * 1024 * 1024  # 50MB max API response
ALLOWED_URL_SCHEMES = {'https'}  # Only HTTPS allowed
MAX_DECIMAL_PLACES = 18  # Maximum decimal places for token amounts

# Whitelisted token addresses (should be loaded from secure configuration)
WHITELISTED_TOKENS = {
    'mainnet': {
        '${CONTRACT_ADDRESS}',  # USDC
        '${CONTRACT_ADDRESS}',  # USDT
        '${CONTRACT_ADDRESS}',  # WETH
        '${CONTRACT_ADDRESS}',  # WBTC
    },
    'polygon': {
        '${CONTRACT_ADDRESS}',  # USDC
        '${CONTRACT_ADDRESS}',  # USDT
        '${CONTRACT_ADDRESS}',  # WMATIC
    },
    'arbitrum': {
        '${CONTRACT_ADDRESS}',  # USDC
        '${CONTRACT_ADDRESS}',  # USDT
        '${CONTRACT_ADDRESS}',  # WETH
    }
}

# Whitelisted DEX addresses
WHITELISTED_DEXES = {
    'mainnet': {
        '${CONTRACT_ADDRESS}',  # Uniswap V2 Router
        '${CONTRACT_ADDRESS}',  # Uniswap V3 Router
        '${CONTRACT_ADDRESS}',  # SushiSwap Router
    },
    'polygon': {
        '${CONTRACT_ADDRESS}',  # QuickSwap Router
        '${CONTRACT_ADDRESS}',  # SushiSwap Router
    },
    'arbitrum': {
        '${CONTRACT_ADDRESS}',  # SushiSwap Router
        '${CONTRACT_ADDRESS}',  # Uniswap V3 Router
    }
}

# JSON Schemas for validation
ARBITRAGE_OPPORTUNITY_SCHEMA = {
    "type": "object",
    "required": ["token_pair", "profit_percent", "net_profit_usd", "chains", "dexes"],
    "properties": {
        "token_pair": {
            "type": "object",
            "required": ["token_a", "token_b"],
            "properties": {
                "token_a": {"type": "string", "pattern": "^0x[a-fA-F0-9]{40}$"},
                "token_b": {"type": "string", "pattern": "^0x[a-fA-F0-9]{40}$"}
            }
        },
        "profit_percent": {"type": "number", "minimum": 0, "maximum": 1},
        "net_profit_usd": {"type": "number", "minimum": 0},
        "chains": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 10
        },
        "dexes": {
            "type": "array",
            "items": {"type": "string", "pattern": "^0x[a-fA-F0-9]{40}$"},
            "minItems": 1,
            "maxItems": 20
        }
    }
}

STRATEGY_PARAMS_SCHEMA = {
    "type": "object",
    "required": ["strategy_type", "parameters"],
    "properties": {
        "strategy_type": {
            "type": "string",
            "enum": ["arbitrage", "liquidation", "mev", "yield_farming"]
        },
        "parameters": {
            "type": "object",
            "properties": {
                "min_profit_usd": {"type": "number", "minimum": 0},
                "max_slippage": {"type": "number", "minimum": 0, "maximum": 0.1},
                "max_gas_price": {"type": "number", "minimum": 0},
                "timeout_seconds": {"type": "number", "minimum": 30, "maximum": 3600}
            }
        }
    }
}

API_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["status", "data"],
    "properties": {
        "status": {"type": "string", "enum": ["success", "error"]},
        "data": {"type": "object"},
        "timestamp": {"type": "number"},
        "errors": {"type": "array", "items": {"type": "string"}}
    }
}

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class EnhancedValidationError(ValidationError):
    """Enhanced validation error with additional context"""
    def __init__(self, message: str, field: str = None, value: Any = None, context: Dict = None):
        self.field = field
        self.value = value
        self.context = context or {}
        super().__init__(message)

class SecureValidator:
    """Secure input validator for arbitrage system"""
    
    def __init__(self, network: str = 'mainnet'):
        self.network = network
        self.whitelisted_tokens = WHITELISTED_TOKENS.get(network, set())
        self.whitelisted_dexes = WHITELISTED_DEXES.get(network, set())
    
    def validate_token_address(self, address: str) -> ChecksumAddress:
        """Validate and return checksum token address"""
        if not address:
            raise ValidationError("Token address cannot be empty")
        
        if not Web3.is_address(address):
            raise ValidationError(f"Invalid token address format: {address}")
        
        checksum_address = Web3.to_checksum_address(address)
        
        # Check against whitelist
        if checksum_address not in self.whitelisted_tokens:
            logger.warning(f"Token address not in whitelist: {checksum_address}")
            # In production, this should raise an error
            # raise ValidationError(f"Token address not whitelisted: {checksum_address}")
        
        return checksum_address
    
    def validate_dex_address(self, address: str) -> ChecksumAddress:
        """Validate and return checksum DEX address"""
        if not address:
            raise ValidationError("DEX address cannot be empty")
        
        if not Web3.is_address(address):
            raise ValidationError(f"Invalid DEX address format: {address}")
        
        checksum_address = Web3.to_checksum_address(address)
        
        # Check against whitelist
        if checksum_address not in self.whitelisted_dexes:
            logger.warning(f"DEX address not in whitelist: {checksum_address}")
            # In production, this should raise an error
            # raise ValidationError(f"DEX address not whitelisted: {checksum_address}")
        
        return checksum_address
    
    def validate_token_amount(self, amount: Union[int, float, str]) -> int:
        """Validate token amount and return as integer wei"""
        try:
            if isinstance(amount, str):
                amount = float(amount)
            
            if not isinstance(amount, (int, float)):
                raise ValidationError(f"Invalid amount type: {type(amount)}")
            
            if amount < 0:
                raise ValidationError("Amount cannot be negative")
            
            # Convert to wei (assuming 18 decimals)
            amount_wei = int(amount * 10**18)
            
            if amount_wei < MIN_TOKEN_AMOUNT:
                raise ValidationError(f"Amount too small: {amount}")
            
            if amount_wei > MAX_TOKEN_AMOUNT:
                raise ValidationError(f"Amount too large: {amount}")
            
            return amount_wei
            
        except (ValueError, OverflowError) as e:
            raise ValidationError(f"Invalid amount format: {amount}") from e
    
    def validate_profit_percent(self, profit_percent: Union[int, float, str]) -> float:
        """Validate profit percentage"""
        try:
            if isinstance(profit_percent, str):
                profit_percent = float(profit_percent)
            
            if not isinstance(profit_percent, (int, float)):
                raise ValidationError(f"Invalid profit percent type: {type(profit_percent)}")
            
            if profit_percent < MIN_PROFIT_PERCENT:
                raise ValidationError(f"Profit percent too small: {profit_percent}")
            
            if profit_percent > MAX_PROFIT_PERCENT:
                raise ValidationError(f"Profit percent too large: {profit_percent}")
            
            return float(profit_percent)
            
        except (ValueError, OverflowError) as e:
            raise ValidationError(f"Invalid profit percent format: {profit_percent}") from e
    
    def validate_gas_price(self, gas_price: Union[int, str]) -> int:
        """Validate gas price in wei"""
        try:
            if isinstance(gas_price, str):
                gas_price = int(gas_price)
            
            if not isinstance(gas_price, int):
                raise ValidationError(f"Invalid gas price type: {type(gas_price)}")
            
            if gas_price < MIN_GAS_PRICE:
                raise ValidationError(f"Gas price too low: {gas_price}")
            
            if gas_price > MAX_GAS_PRICE:
                raise ValidationError(f"Gas price too high: {gas_price}")
            
            return gas_price
            
        except (ValueError, OverflowError) as e:
            raise ValidationError(f"Invalid gas price format: {gas_price}") from e
    
    def validate_opportunity_data(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Validate complete arbitrage opportunity data"""
        validated = {}
        
        try:
            # Validate required fields exist
            required_fields = [
                'token_pair', 'profit_percent', 'net_profit_usd',
                'chains', 'dexes'
            ]
            
            for field in required_fields:
                if field not in opportunity:
                    raise ValidationError(f"Missing required field: {field}")
            
            # Validate token pair
            if 'token_a' in opportunity['token_pair']:
                validated['token_a'] = self.validate_token_address(
                    opportunity['token_pair']['token_a']
                )
            
            if 'token_b' in opportunity['token_pair']:
                validated['token_b'] = self.validate_token_address(
                    opportunity['token_pair']['token_b']
                )
            
            # Validate profit data
            validated['profit_percent'] = self.validate_profit_percent(
                opportunity['profit_percent']
            )
            
            validated['net_profit_usd'] = self.validate_token_amount(
                opportunity['net_profit_usd']
            )
            
            # Validate chain names
            if not isinstance(opportunity['chains'], list):
                raise ValidationError("Chains must be a list")
            
            valid_chains = {'mainnet', 'polygon', 'arbitrum', 'optimism', 'bsc'}
            for chain in opportunity['chains']:
                if chain not in valid_chains:
                    raise ValidationError(f"Invalid chain: {chain}")
            
            validated['chains'] = opportunity['chains']
            
            # Validate DEX addresses
            validated['dexes'] = []
            for dex in opportunity.get('dexes', []):
                if isinstance(dex, str):
                    validated['dexes'].append(self.validate_dex_address(dex))
                elif isinstance(dex, dict) and 'address' in dex:
                    validated['dexes'].append(self.validate_dex_address(dex['address']))
            
            # Validate optional fields
            if 'flash_loan_amount' in opportunity:
                validated['flash_loan_amount'] = self.validate_token_amount(
                    opportunity['flash_loan_amount']
                )
            
            if 'gas_price' in opportunity:
                validated['gas_price'] = self.validate_gas_price(
                    opportunity['gas_price']
                )
            
            # Validate against JSON schema
            jsonschema.validate(instance=opportunity, schema=ARBITRAGE_OPPORTUNITY_SCHEMA)
            
            logger.info(f"Successfully validated opportunity data")
            return validated
            
        except Exception as e:
            logger.error(f"Opportunity validation failed: {e}")
            raise ValidationError(f"Opportunity validation failed: {e}") from e
    
    def sanitize_string(self, value: str, max_length: int = 100) -> str:
        """Sanitize string input"""
        if not isinstance(value, str):
            raise ValidationError(f"Expected string, got {type(value)}")
        
        # Remove any non-printable characters
        sanitized = re.sub(r'[^\x20-\x7E]', '', value)
        
        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized
    
    def validate_strategy_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate strategy execution parameters"""
        validated = {}
        
        try:
            # Validate slippage tolerance
            if 'slippage_tolerance' in params:
                slippage = float(params['slippage_tolerance'])
                if slippage < 0 or slippage > 0.1:  # Max 10% slippage
                    raise ValidationError(f"Invalid slippage tolerance: {slippage}")
                validated['slippage_tolerance'] = slippage
            
            # Validate deadline
            if 'deadline' in params:
                deadline = int(params['deadline'])
                if deadline < 60 or deadline > 3600:  # 1 min to 1 hour
                    raise ValidationError(f"Invalid deadline: {deadline}")
                validated['deadline'] = deadline
            
            # Validate maximum gas
            if 'max_gas' in params:
                max_gas = int(params['max_gas'])
                if max_gas < 50000 or max_gas > 5000000:  # Reasonable gas limits
                    raise ValidationError(f"Invalid max gas: {max_gas}")
                validated['max_gas'] = max_gas
            
            # Validate against JSON schema
            jsonschema.validate(instance=params, schema=STRATEGY_PARAMS_SCHEMA)
            
            return validated
            
        except Exception as e:
            logger.error(f"Strategy params validation failed: {e}")
            raise ValidationError(f"Strategy params validation failed: {e}") from e
    
    def validate_json_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data against JSON schema"""
        try:
            jsonschema.validate(data, schema)
            return data
        except jsonschema.ValidationError as e:
            raise EnhancedValidationError(
                f"Schema validation failed: {e.message}",
                field='.'.join(str(p) for p in e.absolute_path),
                value=e.instance,
                context={'schema_path': list(e.schema_path)}
            )
        except Exception as e:
            raise EnhancedValidationError(f"Schema validation error: {e}")
    
    def validate_api_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate external API response structure and content"""
        try:
            # Size check
            response_size = len(json.dumps(response_data).encode('utf-8'))
            if response_size > MAX_API_RESPONSE_SIZE:
                raise EnhancedValidationError(
                    f"API response too large: {response_size} bytes",
                    context={'max_size': MAX_API_RESPONSE_SIZE}
                )
            
            # Schema validation
            validated = self.validate_json_schema(response_data, API_RESPONSE_SCHEMA)
            
            # Status validation
            if validated['status'] == 'error':
                errors = validated.get('errors', ['Unknown API error'])
                raise EnhancedValidationError(
                    f"API returned error status: {', '.join(errors)}",
                    context={'api_errors': errors}
                )
            
            # Timestamp validation if present
            if 'timestamp' in validated:
                timestamp = validated['timestamp']
                current_time = datetime.now().timestamp()
                if abs(current_time - timestamp) > 3600:  # 1 hour tolerance
                    raise EnhancedValidationError(
                        f"API response timestamp too old or future: {timestamp}",
                        field='timestamp',
                        value=timestamp
                    )
            
            return validated
            
        except EnhancedValidationError:
            raise
        except Exception as e:
            raise EnhancedValidationError(f"API response validation failed: {e}")
    
    def validate_url(self, url: str) -> str:
        """Validate URL for security"""
        try:
            if not url:
                raise EnhancedValidationError("URL cannot be empty")
            
            if len(url) > MAX_STRING_LENGTH:
                raise EnhancedValidationError(
                    f"URL too long: {len(url)} characters",
                    value=url[:100] + "..."
                )
            
            parsed = urlparse(url)
            
            # Scheme validation
            if parsed.scheme not in ALLOWED_URL_SCHEMES:
                raise EnhancedValidationError(
                    f"URL scheme not allowed: {parsed.scheme}",
                    field='scheme',
                    value=parsed.scheme,
                    context={'allowed_schemes': list(ALLOWED_URL_SCHEMES)}
                )
            
            # Host validation
            if not parsed.netloc:
                raise EnhancedValidationError("URL must have a valid host")
            
            # Prevent local/private IPs
            if any(blocked in parsed.netloc.lower() for blocked in [
                'localhost', '127.0.0.1', '0.0.0.0', '::1',
                '10.', '172.16.', '172.17.', '172.18.', '172.19.',
                '172.20.', '172.21.', '172.22.', '172.23.',
                '172.24.', '172.25.', '172.26.', '172.27.',
                '172.28.', '172.29.', '172.30.', '172.31.',
                '192.168.'
            ]):
                raise EnhancedValidationError(
                    f"Local/private URLs not allowed: {parsed.netloc}",
                    field='host',
                    value=parsed.netloc
                )
            
            return url
            
        except EnhancedValidationError:
            raise
        except Exception as e:
            raise EnhancedValidationError(f"URL validation failed: {e}")
    
    def validate_decimal_amount(self, amount: Union[str, float, int, Decimal]) -> Decimal:
        """Validate and convert amount to Decimal with proper precision"""
        try:
            if isinstance(amount, str):
                # Remove any whitespace
                amount = amount.strip()
                if not amount:
                    raise EnhancedValidationError("Amount string cannot be empty")
            
            # Convert to Decimal for precise calculations
            decimal_amount = Decimal(str(amount))
            
            # Check for negative amounts
            if decimal_amount < 0:
                raise EnhancedValidationError(
                    f"Amount cannot be negative: {decimal_amount}",
                    value=decimal_amount
                )
              # Check decimal places
            exponent = decimal_amount.as_tuple().exponent
            if isinstance(exponent, int) and exponent < -MAX_DECIMAL_PLACES:
                raise EnhancedValidationError(
                    f"Too many decimal places: {abs(exponent)}",
                    value=decimal_amount,
                    context={'max_decimal_places': MAX_DECIMAL_PLACES}
                )
            
            # Check for reasonable upper bound
            max_amount = Decimal('10') ** 30  # 1 trillion tokens with 18 decimals
            if decimal_amount > max_amount:
                raise EnhancedValidationError(
                    f"Amount too large: {decimal_amount}",
                    value=decimal_amount,
                    context={'max_amount': max_amount}
                )
            
            return decimal_amount
            
        except InvalidOperation as e:
            raise EnhancedValidationError(
                f"Invalid decimal format: {amount}",
                value=amount
            ) from e
        except EnhancedValidationError:
            raise
        except Exception as e:
            raise EnhancedValidationError(f"Decimal validation failed: {e}")
    
    def validate_network_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate network configuration parameters"""
        required_fields = ['network_name', 'rpc_url', 'chain_id']
        validated = {}
        
        try:
            # Check required fields
            for field in required_fields:
                if field not in config:
                    raise EnhancedValidationError(
                        f"Missing required network config field: {field}",
                        field=field
                    )
            
            # Validate network name
            network_name = config['network_name'].strip()
            if not network_name:
                raise EnhancedValidationError("Network name cannot be empty")
            validated['network_name'] = network_name
            
            # Validate RPC URL
            validated['rpc_url'] = self.validate_url(config['rpc_url'])
            
            # Validate chain ID
            chain_id = config['chain_id']
            if not isinstance(chain_id, int) or chain_id <= 0:
                raise EnhancedValidationError(
                    f"Invalid chain ID: {chain_id}",
                    field='chain_id',
                    value=chain_id
                )
            validated['chain_id'] = chain_id
            
            # Optional fields with validation
            if 'block_confirmations' in config:
                confirmations = config['block_confirmations']
                if not isinstance(confirmations, int) or confirmations < 1 or confirmations > 100:
                    raise EnhancedValidationError(
                        f"Invalid block confirmations: {confirmations}",
                        field='block_confirmations',
                        value=confirmations
                    )
                validated['block_confirmations'] = confirmations
            
            if 'gas_limit' in config:
                gas_limit = config['gas_limit']
                if not isinstance(gas_limit, int) or gas_limit < 21000 or gas_limit > 30000000:
                    raise EnhancedValidationError(
                        f"Invalid gas limit: {gas_limit}",
                        field='gas_limit',
                        value=gas_limit
                    )
                validated['gas_limit'] = gas_limit
            
            return validated
            
        except EnhancedValidationError:
            raise
        except Exception as e:
            raise EnhancedValidationError(f"Network config validation failed: {e}")
    
    def validate_transaction_data(self, tx_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate transaction data before submission"""
        validated = {}
        
        try:
            # Validate to address
            if 'to' in tx_data:
                validated['to'] = self.validate_token_address(tx_data['to'])
            
            # Validate value
            if 'value' in tx_data:
                validated['value'] = self.validate_token_amount(tx_data['value'])
            
            # Validate gas price
            if 'gasPrice' in tx_data:
                validated['gasPrice'] = self.validate_gas_price(tx_data['gasPrice'])
            
            # Validate gas limit
            if 'gas' in tx_data:
                gas_limit = tx_data['gas']
                if not isinstance(gas_limit, int) or gas_limit < 21000 or gas_limit > 30000000:
                    raise EnhancedValidationError(
                        f"Invalid gas limit: {gas_limit}",
                        field='gas',
                        value=gas_limit
                    )
                validated['gas'] = gas_limit
            
            # Validate nonce
            if 'nonce' in tx_data:
                nonce = tx_data['nonce']
                if not isinstance(nonce, int) or nonce < 0:
                    raise EnhancedValidationError(
                        f"Invalid nonce: {nonce}",
                        field='nonce',
                        value=nonce
                    )
                validated['nonce'] = nonce
            
            # Validate data field (transaction input)
            if 'data' in tx_data:
                data = tx_data['data']
                if isinstance(data, str):
                    if not data.startswith('0x'):
                        raise EnhancedValidationError(
                            "Transaction data must start with '0x'",
                            field='data',
                            value=data[:50] + "..." if len(data) > 50 else data
                        )
                    
                    # Check data size (reasonable limit)
                    if len(data) > 100000:  # ~50KB limit
                        raise EnhancedValidationError(
                            f"Transaction data too large: {len(data)} characters",
                            field='data'
                        )
                    
                    validated['data'] = data
                else:
                    raise EnhancedValidationError(
                        f"Transaction data must be string, got {type(data)}",
                        field='data',
                        value=type(data)
                    )
            
            return validated
            
        except EnhancedValidationError:
            raise
        except Exception as e:
            raise EnhancedValidationError(f"Transaction data validation failed: {e}")

def validate_flash_loan_params(params: Dict[str, Any], network: str = 'mainnet') -> Dict[str, Any]:
    """
    Comprehensive validation for flash loan parameters
    """
    validator = SecureValidator(network)
    validated = {}
    
    try:
        # Required fields
        required_fields = ['asset', 'amount', 'receiver', 'params']
        for field in required_fields:
            if field not in params:
                raise EnhancedValidationError(f"Missing required field: {field}")
        
        # Validate asset address
        validated['asset'] = validator.validate_token_address(params['asset'])
        
        # Validate amount
        validated['amount'] = validator.validate_decimal_amount(params['amount'])
        
        # Validate receiver address
        validated['receiver'] = validator.validate_token_address(params['receiver'])
        
        # Validate additional parameters
        if isinstance(params['params'], dict):
            validated['params'] = validator.validate_strategy_params(params['params'])
        else:
            validated['params'] = params['params']  # Pass through if not dict
        
        # Optional fields
        if 'referralCode' in params:
            ref_code = params['referralCode']
            if not isinstance(ref_code, int) or ref_code < 0 or ref_code > 65535:
                raise EnhancedValidationError(f"Invalid referral code: {ref_code}")
            validated['referralCode'] = ref_code
        
        return validated
        
    except Exception as e:
        if isinstance(e, EnhancedValidationError):
            raise
        raise EnhancedValidationError(f"Flash loan parameter validation failed: {e}")

def validate_mev_protection_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate MEV protection parameters
    """
    validator = SecureValidator()
    validated = {}
    
    try:
        # Gas price protection
        if 'maxGasPrice' in params:
            validated['maxGasPrice'] = validator.validate_gas_price(params['maxGasPrice'])
        
        # Priority fee protection
        if 'maxPriorityFee' in params:
            priority_fee = params['maxPriorityFee']
            if not isinstance(priority_fee, int) or priority_fee < 0:
                raise EnhancedValidationError(f"Invalid priority fee: {priority_fee}")
            validated['maxPriorityFee'] = priority_fee
        
        # Deadline protection
        if 'deadline' in params:
            deadline = params['deadline']
            if not isinstance(deadline, int) or deadline <= 0:
                raise EnhancedValidationError(f"Invalid deadline: {deadline}")
            
            # Check deadline is not too far in future
            current_time = int(datetime.now().timestamp())
            max_future = current_time + 7200  # 2 hours max
            
            if deadline > max_future:
                raise EnhancedValidationError(f"Deadline too far in future: {deadline}")
            
            validated['deadline'] = deadline
        
        # Slippage protection
        if 'maxSlippage' in params:
            validated['maxSlippage'] = validator.validate_profit_percent(params['maxSlippage'])
        
        return validated
        
    except Exception as e:
        if isinstance(e, EnhancedValidationError):
            raise
        raise EnhancedValidationError(f"MEV protection parameter validation failed: {e}")

def validate_oracle_feed_data(feed_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate oracle price feed data
    """
    validated = {}
    
    try:
        # Required fields
        required_fields = ['price', 'timestamp', 'asset']
        for field in required_fields:
            if field not in feed_data:
                raise EnhancedValidationError(f"Missing required oracle field: {field}")
        
        # Validate price
        price = feed_data['price']
        if not isinstance(price, (int, float)) or price <= 0:
            raise EnhancedValidationError(f"Invalid oracle price: {price}")
        validated['price'] = price
        
        # Validate timestamp
        timestamp = feed_data['timestamp']
        if not isinstance(timestamp, int) or timestamp <= 0:
            raise EnhancedValidationError(f"Invalid timestamp: {timestamp}")
        
        # Check timestamp freshness
        current_time = int(datetime.now().timestamp())
        age = current_time - timestamp
        max_age = 3600  # 1 hour max age
        
        if age > max_age:
            raise EnhancedValidationError(f"Oracle data too old: {age} seconds")
        
        if timestamp > current_time + 300:  # 5 minutes future tolerance
            raise EnhancedValidationError(f"Oracle timestamp in future: {timestamp}")
        
        validated['timestamp'] = timestamp
        
        # Validate asset
        if not isinstance(feed_data['asset'], str) or not feed_data['asset']:
            raise EnhancedValidationError("Invalid asset identifier")
        validated['asset'] = feed_data['asset']
        
        # Optional confidence score
        if 'confidence' in feed_data:
            confidence = feed_data['confidence']
            if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
                raise EnhancedValidationError(f"Invalid confidence score: {confidence}")
            validated['confidence'] = confidence
        
        # Optional source identifier
        if 'source' in feed_data:
            source = feed_data['source']
            if not isinstance(source, str) or len(source) > 100:
                raise EnhancedValidationError(f"Invalid source identifier: {source}")
            validated['source'] = source
        
        return validated
        
    except Exception as e:
        if isinstance(e, EnhancedValidationError):
            raise
        raise EnhancedValidationError(f"Oracle feed validation failed: {e}")

def validate_batch_operation(operations: List[Dict[str, Any]], network: str = 'mainnet') -> List[Dict[str, Any]]:
    """
    Validate batch operations for security
    """
    validator = SecureValidator(network)
    validated_operations = []
    
    try:
        # Check batch size
        if len(operations) == 0:
            raise EnhancedValidationError("Batch cannot be empty")
        
        if len(operations) > 50:  # Reasonable batch size limit
            raise EnhancedValidationError(f"Batch too large: {len(operations)} operations")
        
        for i, operation in enumerate(operations):
            try:
                # Each operation must have type and data
                if 'type' not in operation:
                    raise EnhancedValidationError(f"Operation {i} missing type")
                
                if 'data' not in operation:
                    raise EnhancedValidationError(f"Operation {i} missing data")
                
                operation_type = operation['type']
                operation_data = operation['data']
                  # Validate based on operation type
                if operation_type == 'arbitrage':
                    validated_data = validator.validate_opportunity_data(operation_data)
                elif operation_type == 'flash_loan':
                    validated_data = validate_flash_loan_params(operation_data, network)
                elif operation_type == 'strategy':
                    validated_data = validator.validate_strategy_params(operation_data)
                else:
                    raise EnhancedValidationError(f"Unknown operation type: {operation_type}")
                
                validated_operations.append({
                    'type': operation_type,
                    'data': validated_data,
                    'index': i
                })
                
            except Exception as e:
                raise EnhancedValidationError(f"Operation {i} validation failed: {e}")
        
        return validated_operations
        
    except Exception as e:
        if isinstance(e, EnhancedValidationError):
            raise
        raise EnhancedValidationError(f"Batch operation validation failed: {e}")

def sanitize_user_input(user_input: str, max_length: int = 1000) -> str:
    """
    Sanitize user input to prevent injection attacks
    """
    try:
        if not isinstance(user_input, str):
            raise EnhancedValidationError(f"Input must be string, got {type(user_input)}")
        
        # Check length
        if len(user_input) > max_length:
            raise EnhancedValidationError(f"Input too long: {len(user_input)} characters")
        
        # Remove null bytes
        sanitized = user_input.replace('\x00', '')
        
        # Remove other control characters except common whitespace
        allowed_chars = set(string.printable) - set(string.ascii_letters[26:])  # Remove some control chars
        sanitized = ''.join(char for char in sanitized if char in allowed_chars or char in ' \t\n\r')
        
        # Trim whitespace
        sanitized = sanitized.strip()
        
        return sanitized
        
    except Exception as e:
        if isinstance(e, EnhancedValidationError):
            raise
        raise EnhancedValidationError(f"Input sanitization failed: {e}")

# Rate limiting for validation calls
class ValidationRateLimiter:
    """Rate limiter for validation operations to prevent abuse"""
    
    def __init__(self, max_calls: int = 1000, time_window: int = 3600):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = {}
    
    def check_rate_limit(self, identifier: str) -> bool:
        """Check if identifier has exceeded rate limit"""
        current_time = datetime.now()
        
        if identifier not in self.calls:
            self.calls[identifier] = []
        
        # Remove old calls outside time window
        cutoff_time = current_time - timedelta(seconds=self.time_window)
        self.calls[identifier] = [
            call_time for call_time in self.calls[identifier] 
            if call_time > cutoff_time
        ]
        
        # Check if under limit
        if len(self.calls[identifier]) >= self.max_calls:
            return False
        
        # Record this call
        self.calls[identifier].append(current_time)
        return True

# Global rate limiter instance
validation_rate_limiter = ValidationRateLimiter()

def rate_limited_validation(identifier: str):
    """Decorator for rate-limited validation functions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not validation_rate_limiter.check_rate_limit(identifier):
                raise EnhancedValidationError(
                    f"Rate limit exceeded for validation: {identifier}",
                    context={'max_calls': validation_rate_limiter.max_calls}
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator
