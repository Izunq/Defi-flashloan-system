#!/usr/bin/env python3
"""
Cross-Chain Security Monitor
===========================

Enhanced monitoring and validation for cross-chain operations with comprehensive
security checks and automated threat detection.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import aiohttp
from web3 import Web3
from eth_account import Account
from secure_input_validator import SecureValidator, EnhancedValidationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OperationStatus(Enum):
    PENDING = "pending"
    VALIDATING = "validating"
    VALIDATED = "validated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class SecurityThreatLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ChainHealth:
    chain_id: int
    is_healthy: bool
    last_block: int
    avg_block_time: float
    last_update: datetime
    confirmation_depth: int

@dataclass
class CrossChainOperation:
    operation_id: str
    source_chain_id: int
    target_chain_id: int
    initiator: str
    payload: str
    value: int
    deadline: int
    status: OperationStatus
    security_score: int
    requires_multisig: bool
    created_at: datetime
    validated_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None

@dataclass
class SecurityAlert:
    alert_id: str
    threat_level: SecurityThreatLevel
    operation_id: Optional[str]
    chain_id: Optional[int]
    description: str
    timestamp: datetime
    details: Dict[str, Any]

class CrossChainSecurityMonitor:
    """
    Comprehensive cross-chain security monitoring system
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.validator = SecureValidator()
        self.web3_connections = {}
        self.chain_health = {}
        self.active_operations = {}
        self.security_alerts = []
        self.is_monitoring = False
        
        # Security thresholds
        self.max_operation_value = config.get('max_operation_value', 100 * 10**18)  # 100 ETH
        self.max_operations_per_hour = config.get('max_operations_per_hour', 100)
        self.max_failed_operations = config.get('max_failed_operations', 10)
        self.chain_health_timeout = config.get('chain_health_timeout', 600)  # 10 minutes
        
        # Initialize Web3 connections
        self._initialize_connections()
    
    def _initialize_connections(self):
        """Initialize Web3 connections for all supported chains"""
        for chain_config in self.config.get('chains', []):
            chain_id = chain_config['chain_id']
            rpc_url = chain_config['rpc_url']
            
            try:
                w3 = Web3(Web3.HTTPProvider(rpc_url))
                if w3.is_connected():
                    self.web3_connections[chain_id] = w3
                    logger.info(f"Connected to chain {chain_id}")
                else:
                    logger.error(f"Failed to connect to chain {chain_id}")
            except Exception as e:
                logger.error(f"Error connecting to chain {chain_id}: {e}")
    
    async def start_monitoring(self):
        """Start the security monitoring system"""
        self.is_monitoring = True
        logger.info("Starting cross-chain security monitoring...")
        
        # Start monitoring tasks
        tasks = [
            self._monitor_chain_health(),
            self._monitor_operations(),
            self._detect_suspicious_activity(),
            self._validate_cross_chain_messages(),
            self._monitor_bridge_health(),
            self._cleanup_expired_operations()
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def stop_monitoring(self):
        """Stop the monitoring system"""
        self.is_monitoring = False
        logger.info("Stopping cross-chain security monitoring...")
    
    async def _monitor_chain_health(self):
        """Monitor health of all connected chains"""
        while self.is_monitoring:
            try:
                for chain_id, w3 in self.web3_connections.items():
                    await self._check_chain_health(chain_id, w3)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in chain health monitoring: {e}")
                await asyncio.sleep(5)
    
    async def _check_chain_health(self, chain_id: int, w3: Web3):
        """Check health of a specific chain"""
        try:
            # Get latest block
            latest_block = w3.eth.get_block('latest')
            current_time = datetime.now()
            
            # Calculate block time
            if chain_id in self.chain_health:
                prev_health = self.chain_health[chain_id]
                block_diff = latest_block.number - prev_health.last_block
                time_diff = (current_time - prev_health.last_update).total_seconds()
                avg_block_time = time_diff / max(block_diff, 1)
            else:
                avg_block_time = 12.0  # Default for Ethereum
            
            # Determine health status
            block_age = current_time.timestamp() - latest_block.timestamp
            is_healthy = block_age < 300  # Block must be less than 5 minutes old
            
            # Update health status
            self.chain_health[chain_id] = ChainHealth(
                chain_id=chain_id,
                is_healthy=is_healthy,
                last_block=latest_block.number,
                avg_block_time=avg_block_time,
                last_update=current_time,
                confirmation_depth=12
            )
            
            # Alert if unhealthy
            if not is_healthy:
                await self._create_security_alert(
                    SecurityThreatLevel.HIGH,
                    f"Chain {chain_id} unhealthy - last block {block_age:.0f}s old",
                    chain_id=chain_id,
                    details={'block_age': block_age, 'latest_block': latest_block.number}
                )
            
        except Exception as e:
            logger.error(f"Error checking health for chain {chain_id}: {e}")
            
            # Mark chain as unhealthy
            self.chain_health[chain_id] = ChainHealth(
                chain_id=chain_id,
                is_healthy=False,
                last_block=0,
                avg_block_time=0,
                last_update=datetime.now(),
                confirmation_depth=12
            )
    
    async def _monitor_operations(self):
        """Monitor cross-chain operations for security issues"""
        while self.is_monitoring:
            try:
                # Get pending operations from contracts
                for chain_id in self.web3_connections:
                    await self._fetch_operations(chain_id)
                
                # Analyze operations for security risks
                await self._analyze_operation_patterns()
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in operation monitoring: {e}")
                await asyncio.sleep(5)
    
    async def _fetch_operations(self, chain_id: int):
        """Fetch operations from a specific chain"""
        try:
            w3 = self.web3_connections[chain_id]
            
            # Get contract instance (placeholder - would need actual ABI and address)
            contract_address = self.config.get('contracts', {}).get(chain_id, {}).get('mesh')
            if not contract_address:
                return
            
            # Fetch pending operations (placeholder implementation)
            # In real implementation, would call contract methods to get operations
            
        except Exception as e:
            logger.error(f"Error fetching operations from chain {chain_id}: {e}")
    
    async def _analyze_operation_patterns(self):
        """Analyze operation patterns for suspicious activity"""
        current_time = datetime.now()
        
        # Check for rapid succession of operations
        recent_operations = [
            op for op in self.active_operations.values()
            if (current_time - op.created_at).total_seconds() < 3600  # Last hour
        ]
        
        if len(recent_operations) > self.max_operations_per_hour:
            await self._create_security_alert(
                SecurityThreatLevel.HIGH,
                f"Excessive operations: {len(recent_operations)} in last hour",
                details={'operation_count': len(recent_operations)}
            )
        
        # Check for high-value operations
        high_value_operations = [
            op for op in recent_operations
            if op.value > self.max_operation_value
        ]
        
        if high_value_operations:
            await self._create_security_alert(
                SecurityThreatLevel.MEDIUM,
                f"High-value operations detected: {len(high_value_operations)}",
                details={'operations': [op.operation_id for op in high_value_operations]}
            )
        
        # Check for failed operations pattern
        failed_operations = [
            op for op in recent_operations
            if op.status == OperationStatus.FAILED
        ]
        
        if len(failed_operations) > self.max_failed_operations:
            await self._create_security_alert(
                SecurityThreatLevel.HIGH,
                f"Excessive failed operations: {len(failed_operations)}",
                details={'failed_operations': [op.operation_id for op in failed_operations]}
            )
    
    async def _detect_suspicious_activity(self):
        """Detect suspicious cross-chain activity patterns"""
        while self.is_monitoring:
            try:
                await self._detect_unusual_patterns()
                await self._detect_potential_attacks()
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in suspicious activity detection: {e}")
                await asyncio.sleep(10)
    
    async def _detect_unusual_patterns(self):
        """Detect unusual operation patterns"""
        # Check for same initiator creating many operations
        initiator_counts = {}
        current_time = datetime.now()
        
        for operation in self.active_operations.values():
            if (current_time - operation.created_at).total_seconds() < 3600:  # Last hour
                initiator_counts[operation.initiator] = initiator_counts.get(operation.initiator, 0) + 1
        
        for initiator, count in initiator_counts.items():
            if count > 20:  # More than 20 operations per hour
                await self._create_security_alert(
                    SecurityThreatLevel.MEDIUM,
                    f"Initiator {initiator} created {count} operations in last hour",
                    details={'initiator': initiator, 'operation_count': count}
                )
    
    async def _detect_potential_attacks(self):
        """Detect potential attack patterns"""
        # Check for payload manipulation attempts
        suspicious_payloads = []
        
        for operation in self.active_operations.values():
            if self._is_suspicious_payload(operation.payload):
                suspicious_payloads.append(operation.operation_id)
        
        if suspicious_payloads:
            await self._create_security_alert(
                SecurityThreatLevel.HIGH,
                f"Suspicious payloads detected in {len(suspicious_payloads)} operations",
                details={'suspicious_operations': suspicious_payloads}
            )
    
    def _is_suspicious_payload(self, payload: str) -> bool:
        """Check if payload contains suspicious patterns"""
        try:
            # Basic checks for suspicious patterns
            suspicious_patterns = [
                b'\x00' * 32,  # Null bytes
                b'\xff' * 32,  # All ones
                # Add more patterns as needed
            ]
            
            payload_bytes = bytes.fromhex(payload[2:] if payload.startswith('0x') else payload)
            
            for pattern in suspicious_patterns:
                if pattern in payload_bytes:
                    return True
            
            return False
            
        except Exception:
            return True  # Invalid payload is suspicious
    
    async def _validate_cross_chain_messages(self):
        """Validate cross-chain messages for security compliance"""
        while self.is_monitoring:
            try:
                for operation in self.active_operations.values():
                    if operation.status == OperationStatus.PENDING:
                        await self._validate_operation_security(operation)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in message validation: {e}")
                await asyncio.sleep(10)
    
    async def _validate_operation_security(self, operation: CrossChainOperation):
        """Validate security aspects of an operation"""
        try:
            # Validate chain health
            source_health = self.chain_health.get(operation.source_chain_id)
            target_health = self.chain_health.get(operation.target_chain_id)
            
            if not source_health or not source_health.is_healthy:
                await self._create_security_alert(
                    SecurityThreatLevel.HIGH,
                    f"Operation on unhealthy source chain {operation.source_chain_id}",
                    operation_id=operation.operation_id,
                    chain_id=operation.source_chain_id
                )
            
            if not target_health or not target_health.is_healthy:
                await self._create_security_alert(
                    SecurityThreatLevel.HIGH,
                    f"Operation targeting unhealthy chain {operation.target_chain_id}",
                    operation_id=operation.operation_id,
                    chain_id=operation.target_chain_id
                )
            
            # Validate payload
            try:
                self.validator.validate_transaction_data({
                    'data': operation.payload,
                    'value': operation.value,
                    'gas': 500000  # Placeholder
                })
            except EnhancedValidationError as e:
                await self._create_security_alert(
                    SecurityThreatLevel.HIGH,
                    f"Invalid operation payload: {e}",
                    operation_id=operation.operation_id
                )
            
            # Check operation deadline
            if operation.deadline < time.time() + 300:  # Less than 5 minutes
                await self._create_security_alert(
                    SecurityThreatLevel.MEDIUM,
                    f"Operation has short deadline: {operation.deadline}",
                    operation_id=operation.operation_id
                )
            
        except Exception as e:
            logger.error(f"Error validating operation {operation.operation_id}: {e}")
    
    async def _monitor_bridge_health(self):
        """Monitor health of bridge infrastructure"""
        while self.is_monitoring:
            try:
                await self._check_bridge_endpoints()
                await self._check_oracle_health()
                await asyncio.sleep(120)  # Check every 2 minutes
                
            except Exception as e:
                logger.error(f"Error in bridge health monitoring: {e}")
                await asyncio.sleep(10)
    
    async def _check_bridge_endpoints(self):
        """Check health of bridge endpoints"""
        for chain_config in self.config.get('chains', []):
            endpoint = chain_config.get('bridge_endpoint')
            if endpoint:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"{endpoint}/health", timeout=10) as response:
                            if response.status != 200:
                                await self._create_security_alert(
                                    SecurityThreatLevel.HIGH,
                                    f"Bridge endpoint unhealthy: {endpoint}",
                                    chain_id=chain_config['chain_id']
                                )
                except Exception as e:
                    await self._create_security_alert(
                        SecurityThreatLevel.HIGH,
                        f"Bridge endpoint unreachable: {endpoint} - {e}",
                        chain_id=chain_config['chain_id']
                    )
    
    async def _check_oracle_health(self):
        """Check health of oracle network"""
        oracle_endpoints = self.config.get('oracles', [])
        
        for oracle in oracle_endpoints:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{oracle}/status", timeout=5) as response:
                        if response.status != 200:
                            await self._create_security_alert(
                                SecurityThreatLevel.MEDIUM,
                                f"Oracle unhealthy: {oracle}"
                            )
            except Exception as e:
                await self._create_security_alert(
                    SecurityThreatLevel.MEDIUM,
                    f"Oracle unreachable: {oracle} - {e}"
                )
    
    async def _cleanup_expired_operations(self):
        """Clean up expired operations"""
        while self.is_monitoring:
            try:
                current_time = time.time()
                expired_operations = []
                
                for op_id, operation in self.active_operations.items():
                    if operation.deadline < current_time:
                        expired_operations.append(op_id)
                
                for op_id in expired_operations:
                    operation = self.active_operations.pop(op_id)
                    logger.info(f"Cleaned up expired operation: {op_id}")
                    
                    await self._create_security_alert(
                        SecurityThreatLevel.LOW,
                        f"Operation expired: {op_id}",
                        operation_id=op_id
                    )
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in operation cleanup: {e}")
                await asyncio.sleep(30)
    
    async def _create_security_alert(
        self,
        threat_level: SecurityThreatLevel,
        description: str,
        operation_id: Optional[str] = None,
        chain_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Create and log a security alert"""
        alert = SecurityAlert(
            alert_id=f"alert_{int(time.time() * 1000)}",
            threat_level=threat_level,
            operation_id=operation_id,
            chain_id=chain_id,
            description=description,
            timestamp=datetime.now(),
            details=details or {}
        )
        
        self.security_alerts.append(alert)
        
        # Log based on threat level
        log_level = {
            SecurityThreatLevel.LOW: logging.INFO,
            SecurityThreatLevel.MEDIUM: logging.WARNING,
            SecurityThreatLevel.HIGH: logging.ERROR,
            SecurityThreatLevel.CRITICAL: logging.CRITICAL
        }[threat_level]
        
        logger.log(log_level, f"SECURITY ALERT [{threat_level.value.upper()}]: {description}")
        
        # Send to external monitoring if critical
        if threat_level in [SecurityThreatLevel.HIGH, SecurityThreatLevel.CRITICAL]:
            await self._send_alert_to_external_monitoring(alert)
    
    async def _send_alert_to_external_monitoring(self, alert: SecurityAlert):
        """Send critical alerts to external monitoring systems"""
        try:
            webhook_url = self.config.get('monitoring', {}).get('webhook_url')
            if webhook_url:
                payload = {
                    'alert_id': alert.alert_id,
                    'threat_level': alert.threat_level.value,
                    'description': alert.description,
                    'timestamp': alert.timestamp.isoformat(),
                    'operation_id': alert.operation_id,
                    'chain_id': alert.chain_id,
                    'details': alert.details
                }
                
                async with aiohttp.ClientSession() as session:
                    await session.post(webhook_url, json=payload, timeout=10)
                    
        except Exception as e:
            logger.error(f"Failed to send alert to external monitoring: {e}")
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Get security monitoring summary"""
        current_time = datetime.now()
        
        # Recent alerts
        recent_alerts = [
            alert for alert in self.security_alerts
            if (current_time - alert.timestamp).total_seconds() < 3600
        ]
        
        alert_counts = {
            level.value: len([a for a in recent_alerts if a.threat_level == level])
            for level in SecurityThreatLevel
        }
        
        # Chain health summary
        healthy_chains = len([h for h in self.chain_health.values() if h.is_healthy])
        total_chains = len(self.chain_health)
        
        return {
            'timestamp': current_time.isoformat(),
            'chains': {
                'healthy': healthy_chains,
                'total': total_chains,
                'health_percentage': (healthy_chains / max(total_chains, 1)) * 100
            },
            'operations': {
                'active': len(self.active_operations),
                'pending': len([op for op in self.active_operations.values() 
                              if op.status == OperationStatus.PENDING])
            },
            'alerts': {
                'recent_count': len(recent_alerts),
                'by_level': alert_counts,
                'critical_active': alert_counts['critical'] > 0
            },
            'monitoring_status': 'active' if self.is_monitoring else 'stopped'
        }

# Example usage and configuration
if __name__ == "__main__":
    config = {
        'chains': [
            {
                'chain_id': 1,
                'name': 'Ethereum',
                'rpc_url': 'https://eth-mainnet.alchemyapi.io/v2/YOUR_API_KEY',
                'bridge_endpoint': 'https://bridge.example.com'
            },
            {
                'chain_id': 137,
                'name': 'Polygon',
                'rpc_url': 'https://polygon-mainnet.alchemyapi.io/v2/YOUR_API_KEY',
                'bridge_endpoint': 'https://polygon-bridge.example.com'
            }
        ],
        'contracts': {
            1: {'mesh': '0x1234567890123456789012345678901234567890'},
            137: {'mesh': '0x2345678901234567890123456789012345678901'}
        },
        'oracles': [
            'https://oracle1.example.com',
            'https://oracle2.example.com',
            'https://oracle3.example.com'
        ],
        'monitoring': {
            'webhook_url': 'https://monitoring.example.com/webhook'
        },
        'max_operation_value': 100 * 10**18,  # 100 ETH
        'max_operations_per_hour': 100,
        'max_failed_operations': 10
    }
    
    async def main():
        monitor = CrossChainSecurityMonitor(config)
        try:
            await monitor.start_monitoring()
        except KeyboardInterrupt:
            await monitor.stop_monitoring()
            logger.info("Security monitoring stopped")
    
    asyncio.run(main())
