#!/usr/bin/env python3
"""
Input Validation Integration Module
==================================

Integrates enhanced input validation across Python and Solidity components
with comprehensive monitoring, logging, and real-time security response.

Features:
- Python-Solidity validation bridge
- Real-time security monitoring
- Automated incident response
- Performance optimization
- Compliance reporting
"""

import json
import time
import asyncio
import logging
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import queue

# Enhanced validator import (with fallback)
try:
    from enhanced_input_validator import (
        EnhancedInputValidator, ValidationContext, ValidationResult,
        SecurityViolationError, RateLimitExceededError
    )
    ENHANCED_VALIDATOR_AVAILABLE = True
except ImportError:
    # Fallback to emergency validator
    try:
        from emergency_input_sanitizer import (
            emergency_sanitize, emergency_validate_eth_address,
            emergency_validate_number, SecurityError
        )
        ENHANCED_VALIDATOR_AVAILABLE = False
    except ImportError:
        ENHANCED_VALIDATOR_AVAILABLE = False

# Web3 integration (with graceful fallback)
try:
    from web3 import Web3
    from web3.types import ChecksumAddress
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
security_logger = logging.getLogger('security.integration')

@dataclass
class SecurityIncident:
    """Security incident data structure"""
    incident_id: str
    timestamp: datetime
    incident_type: str
    severity: str
    source: str
    details: Dict[str, Any]
    response_taken: str
    resolved: bool = False

@dataclass
class ValidationMetrics:
    """Validation performance metrics"""
    total_validations: int = 0
    successful_validations: int = 0
    failed_validations: int = 0
    security_violations: int = 0
    average_response_time: float = 0.0
    peak_response_time: float = 0.0
    rate_limit_hits: int = 0

class SecurityMonitor:
    """Real-time security monitoring and incident response"""
    
    def __init__(self):
        self.incidents: List[SecurityIncident] = []
        self.alert_callbacks: List[Callable] = []
        self.monitoring_active = True
        self.incident_queue = queue.Queue()
        self.monitor_thread = None
        
        # Threat detection thresholds
        self.thresholds = {
            'max_incidents_per_minute': 10,
            'max_incidents_per_hour': 100,
            'consecutive_failures_threshold': 5,
            'response_time_threshold': 1000.0  # ms
        }
        
        self.start_monitoring()
    
    def start_monitoring(self):
        """Start the security monitoring thread"""
        if self.monitor_thread is None or not self.monitor_thread.is_alive():
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            logger.info("Security monitoring started")
    
    def stop_monitoring(self):
        """Stop the security monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        logger.info("Security monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Process incidents from queue
                while not self.incident_queue.empty():
                    try:
                        incident = self.incident_queue.get_nowait()
                        self._process_incident(incident)
                    except queue.Empty:
                        break
                
                # Check for threat patterns
                self._analyze_threat_patterns()
                
                # Sleep briefly to prevent busy waiting
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in security monitor loop: {e}")
                time.sleep(1.0)
    
    def report_incident(self, incident: SecurityIncident):
        """Report a security incident"""
        self.incident_queue.put(incident)
    
    def _process_incident(self, incident: SecurityIncident):
        """Process a security incident"""
        self.incidents.append(incident)
        
        # Log the incident
        security_logger.warning(f"Security incident: {incident.incident_type} from {incident.source}")
        
        # Trigger alerts
        for callback in self.alert_callbacks:
            try:
                callback(incident)
            except Exception as e:
                logger.error(f"Error in security alert callback: {e}")
        
        # Auto-response based on severity
        if incident.severity == 'CRITICAL':
            self._trigger_emergency_response(incident)
        elif incident.severity == 'HIGH':
            self._trigger_high_priority_response(incident)
    
    def _trigger_emergency_response(self, incident: SecurityIncident):
        """Trigger emergency response for critical incidents"""
        logger.critical(f"EMERGENCY: Critical security incident - {incident.details}")
        # Could trigger circuit breakers, notifications, etc.
    
    def _trigger_high_priority_response(self, incident: SecurityIncident):
        """Trigger high priority response"""
        logger.error(f"HIGH PRIORITY: Security incident - {incident.details}")
    
    def _analyze_threat_patterns(self):
        """Analyze incident patterns for threats"""
        now = datetime.now()
        
        # Check incident rate in last minute
        recent_incidents = [
            i for i in self.incidents 
            if now - i.timestamp < timedelta(minutes=1)
        ]
        
        if len(recent_incidents) > self.thresholds['max_incidents_per_minute']:
            self._trigger_rate_limit_response(len(recent_incidents))
    
    def _trigger_rate_limit_response(self, incident_count: int):
        """Respond to high incident rate"""
        logger.warning(f"High incident rate detected: {incident_count} incidents in last minute")
    
    def add_alert_callback(self, callback: Callable):
        """Add an alert callback function"""
        self.alert_callbacks.append(callback)
    
    def get_recent_incidents(self, hours: int = 24) -> List[SecurityIncident]:
        """Get recent incidents"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [i for i in self.incidents if i.timestamp > cutoff]

class IntegratedInputValidator:
    """Integrated input validator with comprehensive security features"""
    
    def __init__(self, strict_mode: bool = True, enable_monitoring: bool = True):
        self.strict_mode = strict_mode
        self.enable_monitoring = enable_monitoring
        
        # Initialize components
        if ENHANCED_VALIDATOR_AVAILABLE:
            from enhanced_input_validator import EnhancedInputValidator
            self.validator = EnhancedInputValidator(strict_mode=strict_mode)
        else:
            self.validator = None
            logger.warning("Enhanced validator not available, using fallback methods")
        
        # Security monitoring
        if enable_monitoring:
            self.security_monitor = SecurityMonitor()
        else:
            self.security_monitor = None
        
        # Metrics tracking
        self.metrics = ValidationMetrics()
        self.response_times: List[float] = []
        
        # Performance optimization
        self.validation_cache = {}
        self.cache_max_size = 10000
        self.cache_ttl = 300  # 5 minutes
        
        # Contract integration
        self.web3_instance = None
        self.validation_contract = None
        
        logger.info(f"Integrated input validator initialized (strict_mode={strict_mode})")
    
    def set_web3_instance(self, web3_instance, contract_address: Optional[str] = None):
        """Set Web3 instance for Solidity integration"""
        if not WEB3_AVAILABLE:
            logger.warning("Web3 not available, Solidity integration disabled")
            return
        
        self.web3_instance = web3_instance
        
        if contract_address:
            # Would load the ComprehensiveInputValidator contract
            # self.validation_contract = web3_instance.eth.contract(...)
            pass
    
    def validate_input(self, value: Any, validation_type: str, 
                      context: Optional[Dict[str, Any]] = None,
                      use_cache: bool = True) -> Dict[str, Any]:
        """
        Main validation entry point with comprehensive features
        
        Returns:
            Dict with keys: 'valid', 'sanitized_value', 'warnings', 'errors', 'metrics'
        """
        start_time = time.time()
        
        # Create validation context
        if context is None:
            context = {}
        
        validation_context = ValidationContext(
            source_ip=context.get('source_ip'),
            user_agent=context.get('user_agent'),
            session_id=context.get('session_id'),
            operation_type=validation_type
        )
        
        # Check cache
        cache_key = None
        if use_cache:
            cache_key = self._generate_cache_key(value, validation_type, context)
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                return cached_result
        
        try:
            # Perform validation
            if self.validator:
                result = self.validator.validate_with_context(
                    value, validation_type, validation_context
                )
                
                response = {
                    'valid': result.is_valid,
                    'sanitized_value': result.sanitized_value,
                    'warnings': result.warnings,
                    'errors': [],
                    'security_flags': result.security_flags,
                    'execution_time_ms': result.execution_time_ms
                }
            else:
                # Fallback validation
                response = self._fallback_validation(value, validation_type, context)
            
            # Update metrics
            self.metrics.total_validations += 1
            if response['valid']:
                self.metrics.successful_validations += 1
            else:
                self.metrics.failed_validations += 1
            
            # Track response time
            execution_time = (time.time() - start_time) * 1000
            self.response_times.append(execution_time)
            if len(self.response_times) > 1000:  # Keep only last 1000
                self.response_times = self.response_times[-1000:]
            
            self.metrics.average_response_time = sum(self.response_times) / len(self.response_times)
            self.metrics.peak_response_time = max(self.response_times)
            
            # Cache result
            if use_cache and cache_key:
                self._cache_result(cache_key, response)
            
            # Security monitoring
            if not response['valid'] and self.security_monitor:
                self._report_validation_failure(validation_context, response, validation_type)
            
            return response
            
        except (SecurityViolationError, RateLimitExceededError) as e:
            # Security incident
            self.metrics.security_violations += 1
            
            if self.security_monitor:
                incident = SecurityIncident(
                    incident_id=f"sec_{int(time.time())}_{hash(str(e)) % 10000}",
                    timestamp=datetime.now(),
                    incident_type="security_violation",
                    severity="HIGH",
                    source=validation_context.source_ip or "unknown",
                    details={
                        'validation_type': validation_type,
                        'error': str(e),
                        'value_hash': hash(str(value)) % 10000
                    },
                    response_taken="validation_blocked"
                )
                self.security_monitor.report_incident(incident)
            
            return {
                'valid': False,
                'sanitized_value': None,
                'warnings': [],
                'errors': [str(e)],
                'security_flags': ['security_violation'],
                'execution_time_ms': (time.time() - start_time) * 1000
            }
        
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return {
                'valid': False,
                'sanitized_value': None,
                'warnings': [],
                'errors': [f"Validation failed: {e}"],
                'security_flags': ['validation_error'],
                'execution_time_ms': (time.time() - start_time) * 1000
            }
    
    def _fallback_validation(self, value: Any, validation_type: str, 
                           context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback validation when enhanced validator is not available"""
        try:
            if validation_type == "string":
                if ENHANCED_VALIDATOR_AVAILABLE:
                    sanitized = emergency_sanitize(value, "fallback")
                else:
                    sanitized = str(value)[:1000] if value else ""
                
                return {
                    'valid': True,
                    'sanitized_value': sanitized,
                    'warnings': ['Using fallback validation'],
                    'errors': [],
                    'security_flags': []
                }
            
            elif validation_type == "ethereum_address":
                if ENHANCED_VALIDATOR_AVAILABLE:
                    sanitized = emergency_validate_eth_address(value)
                elif WEB3_AVAILABLE:
                    if Web3.is_address(value):
                        sanitized = Web3.to_checksum_address(value)
                    else:
                        raise ValueError("Invalid address")
                else:
                    # Basic hex validation
                    if isinstance(value, str) and value.startswith('0x') and len(value) == 42:
                        sanitized = value
                    else:
                        raise ValueError("Invalid address format")
                
                return {
                    'valid': True,
                    'sanitized_value': sanitized,
                    'warnings': ['Using fallback validation'],
                    'errors': [],
                    'security_flags': []
                }
            
            elif validation_type == "number":
                if ENHANCED_VALIDATOR_AVAILABLE:
                    sanitized = emergency_validate_number(value)
                else:
                    sanitized = float(value)
                
                return {
                    'valid': True,
                    'sanitized_value': sanitized,
                    'warnings': ['Using fallback validation'],
                    'errors': [],
                    'security_flags': []
                }
            
            else:
                return {
                    'valid': False,
                    'sanitized_value': None,
                    'warnings': [],
                    'errors': [f"Unknown validation type: {validation_type}"],
                    'security_flags': ['unknown_validation_type']
                }
                
        except Exception as e:
            return {
                'valid': False,
                'sanitized_value': None,
                'warnings': [],
                'errors': [f"Fallback validation failed: {e}"],
                'security_flags': ['fallback_validation_failed']
            }
    
    def _generate_cache_key(self, value: Any, validation_type: str, context: Dict[str, Any]) -> str:
        """Generate cache key for validation result"""
        value_hash = hash(str(value)) % 100000
        context_hash = hash(str(sorted(context.items()))) % 100000
        return f"{validation_type}_{value_hash}_{context_hash}"
    
    def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached validation result"""
        if cache_key in self.validation_cache:
            cached_item = self.validation_cache[cache_key]
            if time.time() - cached_item['timestamp'] < self.cache_ttl:
                return cached_item['result']
            else:
                del self.validation_cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: Dict[str, Any]):
        """Cache validation result"""
        # Clean cache if too large
        if len(self.validation_cache) >= self.cache_max_size:
            # Remove oldest 20% of entries
            to_remove = len(self.validation_cache) // 5
            oldest_keys = sorted(
                self.validation_cache.keys(),
                key=lambda k: self.validation_cache[k]['timestamp']
            )[:to_remove]
            
            for key in oldest_keys:
                del self.validation_cache[key]
        
        self.validation_cache[cache_key] = {
            'result': result,
            'timestamp': time.time()
        }
    
    def _report_validation_failure(self, context: ValidationContext, 
                                 response: Dict[str, Any], validation_type: str):
        """Report validation failure to security monitor"""
        if not self.security_monitor:
            return
        
        incident = SecurityIncident(
            incident_id=f"val_{int(time.time())}_{hash(str(response)) % 10000}",
            timestamp=datetime.now(),
            incident_type="validation_failure",
            severity="MEDIUM",
            source=context.source_ip or "unknown",
            details={
                'validation_type': validation_type,
                'warnings': response.get('warnings', []),
                'errors': response.get('errors', []),
                'security_flags': response.get('security_flags', [])
            },
            response_taken="validation_rejected"
        )
        self.security_monitor.report_incident(incident)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get validation metrics"""
        return {
            'metrics': asdict(self.metrics),
            'cache_stats': {
                'cache_size': len(self.validation_cache),
                'cache_hit_rate': getattr(self, '_cache_hits', 0) / max(self.metrics.total_validations, 1)
            },
            'recent_incidents': len(self.security_monitor.get_recent_incidents()) if self.security_monitor else 0
        }
    
    def validate_batch(self, items: List[Dict[str, Any]], 
                      max_concurrency: int = 10) -> List[Dict[str, Any]]:
        """Validate multiple items in batch with concurrency control"""
        results = []
        
        # Process in chunks to control concurrency
        for i in range(0, len(items), max_concurrency):
            chunk = items[i:i + max_concurrency]
            chunk_results = []
            
            for item in chunk:
                result = self.validate_input(
                    value=item.get('value'),
                    validation_type=item.get('type', 'string'),
                    context=item.get('context', {}),
                    use_cache=item.get('use_cache', True)
                )
                chunk_results.append(result)
            
            results.extend(chunk_results)
        
        return results
    
    def cleanup(self):
        """Cleanup resources"""
        if self.security_monitor:
            self.security_monitor.stop_monitoring()
        
        # Clear cache
        self.validation_cache.clear()
        
        logger.info("Integrated input validator cleaned up")

# Global instance for easy access
integrated_validator = IntegratedInputValidator()

# Convenience functions
def validate_string(value: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Validate string input"""
    return integrated_validator.validate_input(value, "string", context)

def validate_ethereum_address(value: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Validate Ethereum address"""
    return integrated_validator.validate_input(value, "ethereum_address", context)

def validate_number(value: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Validate number"""
    return integrated_validator.validate_input(value, "number", context)

def validate_transaction_data(value: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Validate transaction data"""
    return integrated_validator.validate_input(value, "transaction_data", context)

def validate_strategy_params(value: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Validate strategy parameters"""
    return integrated_validator.validate_input(value, "strategy_params", context)

def get_validation_metrics() -> Dict[str, Any]:
    """Get current validation metrics"""
    return integrated_validator.get_metrics()

if __name__ == "__main__":
    # Test the integrated validator
    print("🔒 Integrated Input Validator - Test Suite")
    
    test_cases = [
        {"value": "test_string", "type": "string"},
        {"value": "'; DROP TABLE users; --", "type": "string"},
        {"value": "0x742dA73Fe8e4B0b42d9D1B6C3F4d1F7b7b5c5c5c", "type": "ethereum_address"},
        {"value": "0x0000000000000000000000000000000000000000", "type": "ethereum_address"},
        {"value": "12345", "type": "number"},
        {"value": "invalid_number", "type": "number"},
    ]
    
    print(f"\nRunning {len(test_cases)} validation tests...")
    
    for i, test_case in enumerate(test_cases, 1):
        result = integrated_validator.validate_input(
            value=test_case["value"],
            validation_type=test_case["type"],
            context={"test_case": i}
        )
        
        status = "✅ PASS" if result["valid"] else "❌ FAIL"
        print(f"{status} Test {i}: {test_case['type']} validation")
        
        if result["warnings"]:
            print(f"  ⚠️ Warnings: {result['warnings']}")
        if result["errors"]:
            print(f"  🚫 Errors: {result['errors']}")
    
    # Display metrics
    metrics = integrated_validator.get_metrics()
    print(f"\n📊 Validation Metrics:")
    print(f"  Total validations: {metrics['metrics']['total_validations']}")
    print(f"  Successful: {metrics['metrics']['successful_validations']}")
    print(f"  Failed: {metrics['metrics']['failed_validations']}")
    print(f"  Security violations: {metrics['metrics']['security_violations']}")
    print(f"  Average response time: {metrics['metrics']['average_response_time']:.2f}ms")
    
    # Cleanup
    integrated_validator.cleanup()
    print("\n✅ Test suite completed")
