#!/usr/bin/env python3
# =================================================================================================
# AST-BASED INPUT VALIDATION MODULE
# =================================================================================================

import ast
import json
import logging
import hashlib
import inspect
from typing import Dict, List, Any, Optional, Union, Callable, Set, Tuple
from dataclasses import dataclass
from web3 import Web3
from web3.types import ChecksumAddress

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ast_validation.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("ast_based_validator")

@dataclass
class ValidationContext:
    """Context for validation operations"""
    field_name: str
    source_ip: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    validation_type: Optional[str] = None
    max_depth: int = 5
    current_depth: int = 0
    parent_context: Optional['ValidationContext'] = None


@dataclass
class ValidationResult:
    """Result of a validation operation"""
    is_valid: bool
    value: Any
    error_message: Optional[str] = None
    context: Optional[ValidationContext] = None


class ASTValidator:
    """AST-based input validator for secure input validation"""
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize AST validator
        
        Args:
            strict_mode: Whether to use strict validation mode
        """
        self.strict_mode = strict_mode
        self.allowed_literals = {
            ast.Num, ast.Str, ast.Bytes, ast.List, ast.Tuple, ast.Set, ast.Dict,
            ast.NameConstant, ast.Name, ast.Constant
        }
        
        # Whitelist of allowed AST node types for expressions
        self.allowed_expressions = {
            # Basic literals
            ast.Num, ast.Str, ast.Bytes, ast.List, ast.Tuple, ast.Set, ast.Dict,
            ast.NameConstant, ast.Name, ast.Constant,
            
            # Basic operations
            ast.BinOp, ast.UnaryOp, ast.Compare,
            
            # Comprehensions (with restrictions)
            ast.ListComp, ast.DictComp, ast.SetComp,
            
            # Subscripting and attribute access
            ast.Subscript, ast.Attribute,
            
            # Function calls (with restrictions)
            ast.Call
        }
        
        # Whitelist of allowed binary operations
        self.allowed_bin_ops = {
            ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv,
            ast.Mod, ast.Pow, ast.LShift, ast.RShift, ast.BitOr,
            ast.BitXor, ast.BitAnd
        }
        
        # Whitelist of allowed unary operations
        self.allowed_unary_ops = {
            ast.UAdd, ast.USub, ast.Not, ast.Invert
        }
        
        # Whitelist of allowed comparison operations
        self.allowed_comparisons = {
            ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
            ast.Is, ast.IsNot, ast.In, ast.NotIn
        }
        
        # Whitelist of allowed function names
        self.allowed_functions = {
            # Built-in functions
            'len', 'int', 'float', 'str', 'bool', 'list', 'dict', 'set', 'tuple',
            'sum', 'min', 'max', 'abs', 'round', 'sorted', 'enumerate', 'zip',
            'any', 'all', 'filter', 'map',
            
            # String methods
            'lower', 'upper', 'strip', 'lstrip', 'rstrip', 'replace',
            'split', 'join', 'startswith', 'endswith', 'find', 'format',
            
            # List/dict methods
            'append', 'extend', 'insert', 'remove', 'pop', 'clear',
            'index', 'count', 'sort', 'reverse', 'keys', 'values', 'items',
            'get', 'update', 'copy'
        }
        
        # Initialize validation statistics
        self.validation_stats = {
            "total_validations": 0,
            "successful_validations": 0,
            "failed_validations": 0,
            "security_incidents": 0
        }
    
    def validate_with_ast(self, value: str, context: ValidationContext) -> ValidationResult:
        """
        Validate input using AST parsing
        
        Args:
            value: Input string to validate
            context: Validation context
            
        Returns:
            Validation result
        """
        self.validation_stats["total_validations"] += 1
        
        try:
            # Parse the input string into an AST
            tree = ast.parse(value, mode='eval')
            
            # Validate the AST
            is_valid = self._validate_ast_node(tree.body, context)
            
            if is_valid:
                self.validation_stats["successful_validations"] += 1
                return ValidationResult(
                    is_valid=True,
                    value=value,
                    context=context
                )
            else:
                self.validation_stats["failed_validations"] += 1
                return ValidationResult(
                    is_valid=False,
                    value=None,
                    error_message=f"Invalid AST structure in input: {value}",
                    context=context
                )
        except SyntaxError as e:
            self.validation_stats["failed_validations"] += 1
            return ValidationResult(
                is_valid=False,
                value=None,
                error_message=f"Syntax error in input: {e}",
                context=context
            )
        except Exception as e:
            self.validation_stats["failed_validations"] += 1
            return ValidationResult(
                is_valid=False,
                value=None,
                error_message=f"Error validating input: {e}",
                context=context
            )
    
    def _validate_ast_node(self, node: ast.AST, context: ValidationContext) -> bool:
        """
        Recursively validate an AST node
        
        Args:
            node: AST node to validate
            context: Validation context
            
        Returns:
            True if node is valid
        """
        # Check recursion depth
        if context.current_depth > context.max_depth:
            logger.warning(f"Maximum recursion depth exceeded for {context.field_name}")
            return False
        
        # Create new context with increased depth
        new_context = ValidationContext(
            field_name=context.field_name,
            source_ip=context.source_ip,
            user_id=context.user_id,
            request_id=context.request_id,
            validation_type=context.validation_type,
            max_depth=context.max_depth,
            current_depth=context.current_depth + 1,
            parent_context=context
        )
        
        # Check if node type is allowed
        if type(node) not in self.allowed_expressions:
            logger.warning(f"Disallowed AST node type: {type(node).__name__}")
            return False
        
        # Validate specific node types
        if isinstance(node, (ast.Num, ast.Str, ast.Bytes, ast.NameConstant, ast.Constant)):
            # Basic literals are always valid
            return True
        
        elif isinstance(node, ast.Name):
            # Only allow certain variable names
            allowed_names = {'True', 'False', 'None'}
            if node.id not in allowed_names:
                logger.warning(f"Disallowed variable name: {node.id}")
                return False
            return True
        
        elif isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            # Validate all elements
            for elt in node.elts:
                if not self._validate_ast_node(elt, new_context):
                    return False
            return True
        
        elif isinstance(node, ast.Dict):
            # Validate all keys and values
            for key, value in zip(node.keys, node.values):
                if not self._validate_ast_node(key, new_context) or not self._validate_ast_node(value, new_context):
                    return False
            return True
        
        elif isinstance(node, ast.BinOp):
            # Validate binary operation
            if type(node.op) not in self.allowed_bin_ops:
                logger.warning(f"Disallowed binary operation: {type(node.op).__name__}")
                return False
            
            return (self._validate_ast_node(node.left, new_context) and
                    self._validate_ast_node(node.right, new_context))
        
        elif isinstance(node, ast.UnaryOp):
            # Validate unary operation
            if type(node.op) not in self.allowed_unary_ops:
                logger.warning(f"Disallowed unary operation: {type(node.op).__name__}")
                return False
            
            return self._validate_ast_node(node.operand, new_context)
        
        elif isinstance(node, ast.Compare):
            # Validate comparison
            for op in node.ops:
                if type(op) not in self.allowed_comparisons:
                    logger.warning(f"Disallowed comparison operation: {type(op).__name__}")
                    return False
            
            # Validate left side and all comparators
            if not self._validate_ast_node(node.left, new_context):
                return False
            
            for comparator in node.comparators:
                if not self._validate_ast_node(comparator, new_context):
                    return False
            
            return True
        
        elif isinstance(node, (ast.ListComp, ast.DictComp, ast.SetComp)):
            # Validate comprehension
            
            # Validate generators
            for generator in node.generators:
                # Validate target
                if not isinstance(generator.target, ast.Name):
                    logger.warning(f"Disallowed comprehension target: {type(generator.target).__name__}")
                    return False
                
                # Validate iterator
                if not self._validate_ast_node(generator.iter, new_context):
                    return False
                
                # Validate ifs
                for if_clause in generator.ifs:
                    if not self._validate_ast_node(if_clause, new_context):
                        return False
            
            # Validate elt for ListComp and SetComp
            if isinstance(node, (ast.ListComp, ast.SetComp)):
                return self._validate_ast_node(node.elt, new_context)
            
            # Validate key and value for DictComp
            elif isinstance(node, ast.DictComp):
                return (self._validate_ast_node(node.key, new_context) and
                        self._validate_ast_node(node.value, new_context))
        
        elif isinstance(node, ast.Call):
            # Validate function call
            
            # Check if it's a direct function name
            if isinstance(node.func, ast.Name):
                if node.func.id not in self.allowed_functions:
                    logger.warning(f"Disallowed function call: {node.func.id}")
                    return False
            
            # Check if it's a method call
            elif isinstance(node.func, ast.Attribute):
                if not self._validate_ast_node(node.func.value, new_context):
                    return False
                
                if node.func.attr not in self.allowed_functions:
                    logger.warning(f"Disallowed method call: {node.func.attr}")
                    return False
            else:
                logger.warning(f"Disallowed function call type: {type(node.func).__name__}")
                return False
            
            # Validate all arguments
            for arg in node.args:
                if not self._validate_ast_node(arg, new_context):
                    return False
            
            # Validate all keyword arguments
            for keyword in node.keywords:
                if not self._validate_ast_node(keyword.value, new_context):
                    return False
            
            return True
        
        elif isinstance(node, ast.Subscript):
            # Validate subscripting
            return (self._validate_ast_node(node.value, new_context) and
                    self._validate_ast_node(node.slice, new_context))
        
        elif isinstance(node, ast.Index):
            # Validate index
            return self._validate_ast_node(node.value, new_context)
        
        elif isinstance(node, ast.Slice):
            # Validate slice
            if node.lower and not self._validate_ast_node(node.lower, new_context):
                return False
            if node.upper and not self._validate_ast_node(node.upper, new_context):
                return False
            if node.step and not self._validate_ast_node(node.step, new_context):
                return False
            return True
        
        elif isinstance(node, ast.Attribute):
            # Validate attribute access
            # Only allow certain attributes
            allowed_attributes = {
                'real', 'imag', 'numerator', 'denominator',
                'days', 'seconds', 'microseconds',
                'year', 'month', 'day', 'hour', 'minute', 'second',
                'items', 'keys', 'values'
            }
            
            if node.attr not in allowed_attributes and node.attr not in self.allowed_functions:
                logger.warning(f"Disallowed attribute access: {node.attr}")
                return False
            
            return self._validate_ast_node(node.value, new_context)
        
        # If we get here, the node type is not explicitly handled
        logger.warning(f"Unhandled AST node type: {type(node).__name__}")
        return False
    
    def validate_ethereum_address(self, value: Any) -> ValidationResult:
        """
        Validate an Ethereum address using AST-based validation
        
        Args:
            value: Address to validate
            
        Returns:
            Validation result
        """
        context = ValidationContext(field_name="ethereum_address")
        
        # First, validate as string
        if not isinstance(value, str):
            return ValidationResult(
                is_valid=False,
                value=None,
                error_message=f"Ethereum address must be a string, got {type(value).__name__}",
                context=context
            )
        
        # Check if it's a valid Ethereum address format using AST
        try:
            # Create a simple AST expression to check the address format
            expr = f"'{value}'.startswith('0x') and len('{value}') == 42 and all(c in '0123456789abcdefABCDEF' for c in '{value}'[2:])"
            tree = ast.parse(expr, mode='eval')
            
            # Validate the AST
            if not self._validate_ast_node(tree.body, context):
                return ValidationResult(
                    is_valid=False,
                    value=None,
                    error_message=f"Invalid Ethereum address format: {value}",
                    context=context
                )
            
            # Evaluate the expression
            result = eval(expr)
            
            if not result:
                return ValidationResult(
                    is_valid=False,
                    value=None,
                    error_message=f"Invalid Ethereum address format: {value}",
                    context=context
                )
            
            # Convert to checksum address
            try:
                checksum_address = Web3.to_checksum_address(value)
                return ValidationResult(
                    is_valid=True,
                    value=checksum_address,
                    context=context
                )
            except ValueError:
                return ValidationResult(
                    is_valid=False,
                    value=None,
                    error_message=f"Invalid Ethereum checksum address: {value}",
                    context=context
                )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                value=None,
                error_message=f"Error validating Ethereum address: {e}",
                context=context
            )
    
    def validate_transaction_data(self, tx_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate transaction data using AST-based validation
        
        Args:
            tx_data: Transaction data to validate
            
        Returns:
            Validation result
        """
        context = ValidationContext(field_name="transaction_data")
        
        # Check if tx_data is a dictionary
        if not isinstance(tx_data, dict):
            return ValidationResult(
                is_valid=False,
                value=None,
                error_message=f"Transaction data must be a dictionary, got {type(tx_data).__name__}",
                context=context
            )
        
        # Required fields
        required_fields = {'to', 'value'}
        
        # Check required fields
        for field in required_fields:
            if field not in tx_data:
                return ValidationResult(
                    is_valid=False,
                    value=None,
                    error_message=f"Missing required field: {field}",
                    context=context
                )
        
        # Validate 'to' address
        to_result = self.validate_ethereum_address(tx_data.get('to'))
        if not to_result.is_valid:
            return ValidationResult(
                is_valid=False,
                value=None,
                error_message=f"Invalid 'to' address: {to_result.error_message}",
                context=context
            )
        
        # Validate 'value'
        value = tx_data.get('value')
        if not isinstance(value, (int, float, str)):
            return ValidationResult(
                is_valid=False,
                value=None,
                error_message=f"Transaction value must be a number or string, got {type(value).__name__}",
                context=context
            )
        
        # If value is a string, validate it with AST
        if isinstance(value, str):
            value_context = ValidationContext(field_name="value")
            value_result = self.validate_with_ast(value, value_context)
            
            if not value_result.is_valid:
                return ValidationResult(
                    is_valid=False,
                    value=None,
                    error_message=f"Invalid transaction value: {value_result.error_message}",
                    context=context
                )
        
        # Validate optional fields
        optional_fields = {
            'gas': (int, str),
            'gasPrice': (int, str),
            'maxFeePerGas': (int, str),
            'maxPriorityFeePerGas': (int, str),
            'nonce': (int, str),
            'chainId': (int, str),
            'data': (str,),
        }
        
        for field, allowed_types in optional_fields.items():
            if field in tx_data:
                value = tx_data[field]
                
                # Check type
                if not isinstance(value, allowed_types):
                    return ValidationResult(
                        is_valid=False,
                        value=None,
                        error_message=f"Field '{field}' must be one of {allowed_types}, got {type(value).__name__}",
                        context=context
                    )
                
                # If string, validate with AST
                if isinstance(value, str) and field != 'data':
                    field_context = ValidationContext(field_name=field)
                    field_result = self.validate_with_ast(value, field_context)
                    
                    if not field_result.is_valid:
                        return ValidationResult(
                            is_valid=False,
                            value=None,
                            error_message=f"Invalid {field}: {field_result.error_message}",
                            context=context
                        )
        
        # Validate 'data' field if present
        if 'data' in tx_data:
            data = tx_data['data']
            
            # Check if it's a valid hex string
            if not isinstance(data, str) or not data.startswith('0x'):
                return ValidationResult(
                    is_valid=False,
                    value=None,
                    error_message=f"Transaction data must be a hex string starting with '0x'",
                    context=context
                )
            
            # Check if it contains only hex characters
            try:
                # Create a simple AST expression to check hex format
                expr = f"all(c in '0123456789abcdefABCDEF' for c in '{data[2:]}')"
                tree = ast.parse(expr, mode='eval')
                
                # Validate the AST
                if not self._validate_ast_node(tree.body, context):
                    return ValidationResult(
                        is_valid=False,
                        value=None,
                        error_message=f"Invalid transaction data format: {data}",
                        context=context
                    )
                
                # Evaluate the expression
                result = eval(expr)
                
                if not result:
                    return ValidationResult(
                        is_valid=False,
                        value=None,
                        error_message=f"Invalid transaction data format: {data}",
                        context=context
                    )
            except Exception as e:
                return ValidationResult(
                    is_valid=False,
                    value=None,
                    error_message=f"Error validating transaction data: {e}",
                    context=context
                )
        
        # All validations passed
        return ValidationResult(
            is_valid=True,
            value=tx_data,
            context=context
        )
    
    def validate_json_data(self, json_data: Any) -> ValidationResult:
        """
        Validate JSON data using AST-based validation
        
        Args:
            json_data: JSON data to validate
            
        Returns:
            Validation result
        """
        context = ValidationContext(field_name="json_data")
        
        # If json_data is a string, try to parse it
        if isinstance(json_data, str):
            try:
                json_data = json.loads(json_data)
            except json.JSONDecodeError as e:
                return ValidationResult(
                    is_valid=False,
                    value=None,
                    error_message=f"Invalid JSON: {e}",
                    context=context
                )
        
        # Validate JSON structure recursively
        return self._validate_json_recursive(json_data, context)
    
    def _validate_json_recursive(self, data: Any, context: ValidationContext) -> ValidationResult:
        """
        Recursively validate JSON data
        
        Args:
            data: JSON data to validate
            context: Validation context
            
        Returns:
            Validation result
        """
        # Check recursion depth
        if context.current_depth > context.max_depth:
            return ValidationResult(
                is_valid=False,
                value=None,
                error_message=f"Maximum recursion depth exceeded for {context.field_name}",
                context=context
            )
        
        # Create new context with increased depth
        new_context = ValidationContext(
            field_name=context.field_name,
            source_ip=context.source_ip,
            user_id=context.user_id,
            request_id=context.request_id,
            validation_type=context.validation_type,
            max_depth=context.max_depth,
            current_depth=context.current_depth + 1,
            parent_context=context
        )
        
        # Validate based on data type
        if isinstance(data, (int, float, bool, type(None))):
            # Basic types are always valid
            return ValidationResult(
                is_valid=True,
                value=data,
                context=context
            )
        
        elif isinstance(data, str):
            # Validate string with AST
            try:
                # Create a simple AST expression to check the string
                expr = f"len('{data}') <= 10000"  # Limit string length
                tree = ast.parse(expr, mode='eval')
                
                # Validate the AST
                if not self._validate_ast_node(tree.body, context):
                    return ValidationResult(
                        is_valid=False,
                        value=None,
                        error_message=f"Invalid string format",
                        context=context
                    )
                
                # Evaluate the expression
                result = eval(expr)
                
                if not result:
                    return ValidationResult(
                        is_valid=False,
                        value=None,
                        error_message=f"String too long (max 10000 characters)",
                        context=context
                    )
                
                return ValidationResult(
                    is_valid=True,
                    value=data,
                    context=context
                )
            except Exception as e:
                return ValidationResult(
                    is_valid=False,
                    value=None,
                    error_message=f"Error validating string: {e}",
                    context=context
                )
        
        elif isinstance(data, list):
            # Validate list elements
            valid_elements = []
            
            for i, element in enumerate(data):
                element_context = ValidationContext(
                    field_name=f"{context.field_name}[{i}]",
                    source_ip=context.source_ip,
                    user_id=context.user_id,
                    request_id=context.request_id,
                    validation_type=context.validation_type,
                    max_depth=context.max_depth,
                    current_depth=context.current_depth + 1,
                    parent_context=context
                )
                
                element_result = self._validate_json_recursive(element, element_context)
                
                if not element_result.is_valid:
                    return ValidationResult(
                        is_valid=False,
                        value=None,
                        error_message=f"Invalid element at index {i}: {element_result.error_message}",
                        context=context
                    )
                
                valid_elements.append(element_result.value)
            
            return ValidationResult(
                is_valid=True,
                value=valid_elements,
                context=context
            )
        
        elif isinstance(data, dict):
            # Validate dictionary keys and values
            valid_dict = {}
            
            for key, value in data.items():
                # Validate key
                if not isinstance(key, str):
                    return ValidationResult(
                        is_valid=False,
                        value=None,
                        error_message=f"Dictionary keys must be strings, got {type(key).__name__}",
                        context=context
                    )
                
                # Validate value
                value_context = ValidationContext(
                    field_name=f"{context.field_name}.{key}",
                    source_ip=context.source_ip,
                    user_id=context.user_id,
                    request_id=context.request_id,
                    validation_type=context.validation_type,
                    max_depth=context.max_depth,
                    current_depth=context.current_depth + 1,
                    parent_context=context
                )
                
                value_result = self._validate_json_recursive(value, value_context)
                
                if not value_result.is_valid:
                    return ValidationResult(
                        is_valid=False,
                        value=None,
                        error_message=f"Invalid value for key '{key}': {value_result.error_message}",
                        context=context
                    )
                
                valid_dict[key] = value_result.value
            
            return ValidationResult(
                is_valid=True,
                value=valid_dict,
                context=context
            )
        
        else:
            # Unsupported type
            return ValidationResult(
                is_valid=False,
                value=None,
                error_message=f"Unsupported data type: {type(data).__name__}",
                context=context
            )
    
    def validate_url(self, url: str) -> ValidationResult:
        """
        Validate a URL using AST-based validation
        
        Args:
            url: URL to validate
            
        Returns:
            Validation result
        """
        context = ValidationContext(field_name="url")
        
        # Check if url is a string
        if not isinstance(url, str):
            return ValidationResult(
                is_valid=False,
                value=None,
                error_message=f"URL must be a string, got {type(url).__name__}",
                context=context
            )
        
        # Validate URL format using AST
        try:
            # Create AST expressions to check URL format
            protocol_expr = f"'{url}'.startswith(('http://', 'https://'))"
            length_expr = f"len('{url}') <= 2083"  # Max URL length
            
            # Validate protocol
            protocol_tree = ast.parse(protocol_expr, mode='eval')
            if not self._validate_ast_node(protocol_tree.body, context):
                return ValidationResult(
                    is_valid=False,
                    value=None,
                    error_message=f"Invalid URL protocol: {url}",
                    context=context
                )
            
            protocol_valid = eval(protocol_expr)
            if not protocol_valid:
                return ValidationResult(
                    is_valid=False,
                    value=None,
                    error_message=f"URL must start with http:// or https://",
                    context=context
                )
            
            # Validate length
            length_tree = ast.parse(length_expr, mode='eval')
            if not self._validate_ast_node(length_tree.body, context):
                return ValidationResult(
                    is_valid=False,
                    value=None,
                    error_message=f"Invalid URL length expression",
                    context=context
                )
            
            length_valid = eval(length_expr)
            if not length_valid:
                return ValidationResult(
                    is_valid=False,
                    value=None,
                    error_message=f"URL too long (max 2083 characters)",
                    context=context
                )
            
            # Check for common URL components
            components_expr = f"'.' in '{url.split('//')[1]}'"
            components_tree = ast.parse(components_expr, mode='eval')
            if not self._validate_ast_node(components_tree.body, context):
                return ValidationResult(
                    is_valid=False,
                    value=None,
                    error_message=f"Invalid URL components expression",
                    context=context
                )
            
            components_valid = eval(components_expr)
            if not components_valid:
                return ValidationResult(
                    is_valid=False,
                    value=None,
                    error_message=f"URL must contain a domain with at least one dot",
                    context=context
                )
            
            # All validations passed
            return ValidationResult(
                is_valid=True,
                value=url,
                context=context
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                value=None,
                error_message=f"Error validating URL: {e}",
                context=context
            )
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        return self.validation_stats


# Helper functions for common validations
def validate_string(value: Any, context: Optional[ValidationContext] = None) -> ValidationResult:
    """Validate a string using AST-based validation"""
    validator = ASTValidator()
    if context is None:
        context = ValidationContext(field_name="string")
    return validator.validate_with_ast(str(value), context)


def validate_ethereum_address(value: Any, context: Optional[ValidationContext] = None) -> ValidationResult:
    """Validate an Ethereum address using AST-based validation"""
    validator = ASTValidator()
    if context is None:
        context = ValidationContext(field_name="ethereum_address")
    return validator.validate_ethereum_address(value)


def validate_transaction_data(value: Any, context: Optional[ValidationContext] = None) -> ValidationResult:
    """Validate transaction data using AST-based validation"""
    validator = ASTValidator()
    if context is None:
        context = ValidationContext(field_name="transaction_data")
    return validator.validate_transaction_data(value)


def validate_json_data(value: Any, context: Optional[ValidationContext] = None) -> ValidationResult:
    """Validate JSON data using AST-based validation"""
    validator = ASTValidator()
    if context is None:
        context = ValidationContext(field_name="json_data")
    return validator.validate_json_data(value)


def validate_url(value: Any, context: Optional[ValidationContext] = None) -> ValidationResult:
    """Validate a URL using AST-based validation"""
    validator = ASTValidator()
    if context is None:
        context = ValidationContext(field_name="url")
    return validator.validate_url(value)


# Example usage
if __name__ == "__main__":
    # Initialize AST validator
    validator = ASTValidator()
    
    # Validate a simple expression
    result = validator.validate_with_ast("1 + 2 * 3", ValidationContext(field_name="expression"))
    print(f"Expression valid: {result.is_valid}")
    
    # Validate an Ethereum address
    address_result = validator.validate_ethereum_address("${CONTRACT_ADDRESS}")
    print(f"Address valid: {address_result.is_valid}")
    
    # Validate transaction data
    tx_data = {
        "to": "${CONTRACT_ADDRESS}",
        "value": "1000000000000000000",
        "gas": 21000,
        "gasPrice": "5000000000",
        "nonce": 0,
        "data": "0x"
    }
    tx_result = validator.validate_transaction_data(tx_data)
    print(f"Transaction data valid: {tx_result.is_valid}")
    
    # Validate a URL
    url_result = validator.validate_url("https://example.com/path?query=value")
    print(f"URL valid: {url_result.is_valid}")