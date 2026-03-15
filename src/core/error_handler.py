"""
Error Handler Module

This module provides centralized error handling functionality with sanitized error messages
to prevent information disclosure in production environments.
"""

import logging
import traceback
import sys
import os
import re
import json
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Error severity levels
class ErrorSeverity(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

# Error categories
class ErrorCategory(Enum):
    VALIDATION = "VALIDATION"
    AUTHENTICATION = "AUTHENTICATION"
    AUTHORIZATION = "AUTHORIZATION"
    DATABASE = "DATABASE"
    NETWORK = "NETWORK"
    BLOCKCHAIN = "BLOCKCHAIN"
    SMART_CONTRACT = "SMART_CONTRACT"
    CONFIGURATION = "CONFIGURATION"
    EXTERNAL_SERVICE = "EXTERNAL_SERVICE"
    INTERNAL = "INTERNAL"
    UNKNOWN = "UNKNOWN"

class ErrorHandler:
    """
    Centralized error handler for the application.
    Provides sanitized error messages for production environments.
    """
    
    # Patterns to identify sensitive information
    SENSITIVE_PATTERNS = [
        (r'password\s*[=:]\s*[\'"][^\'"]*[\'"]', 'password=*****'),
        (r'secret\s*[=:]\s*[\'"][^\'"]*[\'"]', 'secret=*****'),
        (r'key\s*[=:]\s*[\'"][^\'"]*[\'"]', 'key=*****'),
        (r'token\s*[=:]\s*[\'"][^\'"]*[\'"]', 'token=*****'),
        (r'auth\s*[=:]\s*[\'"][^\'"]*[\'"]', 'auth=*****'),
        (r'0x[a-fA-F0-9]{40}', '0x****'),  # Ethereum addresses
        (r'0x[a-fA-F0-9]{64}', '0x****'),  # Transaction hashes
        (r'(\d{1,3}\.){3}\d{1,3}', 'IP_REDACTED'),  # IP addresses
        (r'mongodb:\/\/[^\s]*', 'mongodb://****'),  # MongoDB connection strings
        (r'https?:\/\/[^\/\s]+\/api\/[^\s]*', 'https://api-endpoint/****'),  # API URLs
    ]
    
    # Error code prefixes by category
    ERROR_CODE_PREFIXES = {
        ErrorCategory.VALIDATION: "VAL",
        ErrorCategory.AUTHENTICATION: "AUTH",
        ErrorCategory.AUTHORIZATION: "PERM",
        ErrorCategory.DATABASE: "DB",
        ErrorCategory.NETWORK: "NET",
        ErrorCategory.BLOCKCHAIN: "BC",
        ErrorCategory.SMART_CONTRACT: "SC",
        ErrorCategory.CONFIGURATION: "CFG",
        ErrorCategory.EXTERNAL_SERVICE: "EXT",
        ErrorCategory.INTERNAL: "INT",
        ErrorCategory.UNKNOWN: "UNK"
    }
    
    @staticmethod
    def is_production() -> bool:
        """Check if the application is running in production mode"""
        return os.environ.get('ENVIRONMENT', '').lower() == 'production'
    
    @staticmethod
    def sanitize_error_message(message: str) -> str:
        """
        Remove sensitive information from error messages
        """
        sanitized = message
        for pattern, replacement in ErrorHandler.SENSITIVE_PATTERNS:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        return sanitized
    
    @staticmethod
    def sanitize_traceback(tb: str) -> str:
        """
        Sanitize a traceback string to remove sensitive information
        """
        sanitized = tb
        for pattern, replacement in ErrorHandler.SENSITIVE_PATTERNS:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        return sanitized
    
    @staticmethod
    def get_error_code(category: ErrorCategory, error_id: int) -> str:
        """
        Generate a unique error code based on category and ID
        """
        prefix = ErrorHandler.ERROR_CODE_PREFIXES.get(category, "UNK")
        return f"{prefix}-{error_id:04d}"
    
    @staticmethod
    def handle_exception(
        exception: Exception,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        error_id: int = 1000,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Handle an exception and return a sanitized error response
        """
        # Get exception details
        exc_type, exc_value, exc_traceback = sys.exc_info()
        stack_trace = traceback.format_exception(exc_type, exc_value, exc_traceback)
        
        # Generate error code
        error_code = ErrorHandler.get_error_code(category, error_id)
        
        # Create full error details for logging
        error_details = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_code": error_code,
            "error_type": exc_type.__name__ if exc_type else "Unknown",
            "error_message": str(exception),
            "category": category.value,
            "severity": severity.value,
            "stack_trace": stack_trace,
            "context": context or {}
        }
        
        # Log the full error details
        log_message = f"Error {error_code}: {error_details['error_type']} - {error_details['error_message']}"
        
        if severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message, exc_info=True, extra={"error_details": error_details})
        elif severity == ErrorSeverity.ERROR:
            logger.error(log_message, exc_info=True, extra={"error_details": error_details})
        elif severity == ErrorSeverity.WARNING:
            logger.warning(log_message, exc_info=True, extra={"error_details": error_details})
        elif severity == ErrorSeverity.INFO:
            logger.info(log_message, extra={"error_details": error_details})
        else:
            logger.debug(log_message, exc_info=True, extra={"error_details": error_details})
        
        # Create sanitized response for the client
        if ErrorHandler.is_production():
            # In production, return minimal information
            client_response = {
                "error": True,
                "error_code": error_code,
                "message": ErrorHandler.get_public_message(category),
                "category": category.value,
                "timestamp": error_details["timestamp"]
            }
        else:
            # In development, return more details but still sanitize sensitive info
            sanitized_message = ErrorHandler.sanitize_error_message(str(exception))
            sanitized_traceback = [ErrorHandler.sanitize_traceback(frame) for frame in stack_trace]
            
            client_response = {
                "error": True,
                "error_code": error_code,
                "message": sanitized_message,
                "category": category.value,
                "timestamp": error_details["timestamp"],
                "error_type": error_details["error_type"],
                "stack_trace": sanitized_traceback
            }
        
        return client_response
    
    @staticmethod
    def get_public_message(category: ErrorCategory) -> str:
        """
        Get a generic public-facing error message based on the error category
        """
        messages = {
            ErrorCategory.VALIDATION: "The provided data failed validation. Please check your input and try again.",
            ErrorCategory.AUTHENTICATION: "Authentication failed. Please check your credentials and try again.",
            ErrorCategory.AUTHORIZATION: "You do not have permission to perform this action.",
            ErrorCategory.DATABASE: "A database error occurred. Please try again later.",
            ErrorCategory.NETWORK: "A network error occurred. Please check your connection and try again.",
            ErrorCategory.BLOCKCHAIN: "A blockchain interaction error occurred. Please try again later.",
            ErrorCategory.SMART_CONTRACT: "A smart contract error occurred. Please try again later.",
            ErrorCategory.CONFIGURATION: "A system configuration error occurred. Please contact support.",
            ErrorCategory.EXTERNAL_SERVICE: "An error occurred with an external service. Please try again later.",
            ErrorCategory.INTERNAL: "An internal server error occurred. Please try again later.",
            ErrorCategory.UNKNOWN: "An unexpected error occurred. Please try again later."
        }
        
        return messages.get(category, "An error occurred. Please try again later.")
    
    @staticmethod
    def log_error(
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        error_id: int = 1000,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Log an error without an exception
        """
        # Generate error code
        error_code = ErrorHandler.get_error_code(category, error_id)
        
        # Create error details
        error_details = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_code": error_code,
            "error_message": message,
            "category": category.value,
            "severity": severity.value,
            "context": context or {}
        }
        
        # Log the error
        log_message = f"Error {error_code}: {message}"
        
        if severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message, extra={"error_details": error_details})
        elif severity == ErrorSeverity.ERROR:
            logger.error(log_message, extra={"error_details": error_details})
        elif severity == ErrorSeverity.WARNING:
            logger.warning(log_message, extra={"error_details": error_details})
        elif severity == ErrorSeverity.INFO:
            logger.info(log_message, extra={"error_details": error_details})
        else:
            logger.debug(log_message, extra={"error_details": error_details})
        
        # Create sanitized response
        if ErrorHandler.is_production():
            client_response = {
                "error": True,
                "error_code": error_code,
                "message": ErrorHandler.get_public_message(category),
                "category": category.value,
                "timestamp": error_details["timestamp"]
            }
        else:
            sanitized_message = ErrorHandler.sanitize_error_message(message)
            
            client_response = {
                "error": True,
                "error_code": error_code,
                "message": sanitized_message,
                "category": category.value,
                "timestamp": error_details["timestamp"]
            }
        
        return client_response

# Example usage:
# try:
#     # Some code that might raise an exception
#     result = 1 / 0
# except Exception as e:
#     error_response = ErrorHandler.handle_exception(
#         e,
#         category=ErrorCategory.INTERNAL,
#         severity=ErrorSeverity.ERROR,
#         error_id=1001,
#         context={"operation": "division"}
#     )
#     # Return error_response to the client