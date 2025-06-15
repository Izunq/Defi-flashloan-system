#!/usr/bin/env python3
"""
Advanced Retry Mechanism System for Gas Optimization and DoS Protection
======================================================================

This module provides sophisticated retry mechanisms, gas optimization,
and DoS protection for the flashloan arbitrage system.

Features:
- Exponential backoff with jitter
- Circuit breaker patterns
- Adaptive gas estimation
- External call optimization
- Network congestion awareness
"""

import asyncio
import time
import random
import logging
import json
from typing import Dict, List, Optional, Callable, Any, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from contextlib import asynccontextmanager
try:
    import aiohttp
    from web3 import Web3
    from web3.exceptions import TimeExhausted, ContractLogicError
    import numpy as np
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    Web3 = None

logger = logging.getLogger(__name__)

class RetryErrorType(Enum):
    """Types of errors for retry logic"""
    TRANSIENT = "transient"           # Network issues, gas problems
    PERMANENT = "permanent"           # Logic errors, insufficient funds
    RATE_LIMITED = "rate_limited"     # Rate limiting errors
    GAS_RELATED = "gas_related"       # Gas estimation/limit errors
    NETWORK_CONGESTION = "congestion" # Network congestion

@dataclass
class RetryConfig:
    """Configuration for retry mechanisms"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter_range: float = 0.25  # ±25% jitter
    backoff_multiplier: float = 1.5
    timeout_seconds: float = 30.0
    
    # Circuit breaker settings
    failure_threshold: int = 5
    recovery_timeout: float = 300.0  # 5 minutes
    half_open_max_calls: int = 3
    
    # Gas optimization
    gas_estimation_buffer: float = 1.2  # 20% buffer
    gas_price_multiplier: float = 1.1   # 10% gas price increase on retry
    max_gas_price_multiplier: float = 2.0
    
    # Rate limiting
    rate_limit_window: float = 60.0
    max_calls_per_window: int = 100

@dataclass
class OperationMetrics:
    """Metrics for operation optimization"""
    total_attempts: int = 0
    successful_attempts: int = 0
    failed_attempts: int = 0
    total_gas_used: int = 0
    average_gas_used: float = 0.0
    last_execution_time: datetime = field(default_factory=datetime.now)
    optimal_gas_limit: int = 0
    success_rate: float = 0.0

class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, blocking calls
    HALF_OPEN = "half_open"  # Testing if circuit can close

class CircuitBreaker:
    """Enhanced circuit breaker implementation"""
    
    def __init__(self, config: RetryConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
        
    def can_execute(self) -> bool:
        """Check if operation can be executed"""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                self.half_open_calls = 0
                return True
            return False
        elif self.state == CircuitBreakerState.HALF_OPEN:
            return self.half_open_calls < self.config.half_open_max_calls
        
        return False
    
    def record_success(self):
        """Record successful operation"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.half_open_calls = 0
        
    def record_failure(self):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
        elif self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.half_open_calls += 1
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.config.recovery_timeout

class GasOptimizer:
    """Advanced gas optimization system"""
      def __init__(self, web3, config: RetryConfig):
        if not WEB3_AVAILABLE:
            raise ImportError("Web3 and related packages not available")
        self.web3 = web3
        self.config = config
        self.gas_price_history = []
        self.network_congestion_level = 0.0
        self.last_gas_update = 0
        
    async def estimate_optimal_gas(
        self,
        transaction: Dict[str, Any],
        operation_metrics: OperationMetrics
    ) -> Tuple[int, int]:
        """Estimate optimal gas limit and gas price"""
        
        # Base gas estimation
        try:
            estimated_gas = await self._estimate_gas_async(transaction)
        except Exception as e:
            logger.warning(f"Gas estimation failed: {e}")
            estimated_gas = 500000  # Fallback
        
        # Apply buffer
        gas_limit = int(estimated_gas * self.config.gas_estimation_buffer)
        
        # Use historical data if available
        if operation_metrics.optimal_gas_limit > 0:
            historical_gas = operation_metrics.optimal_gas_limit
            gas_limit = max(gas_limit, historical_gas)
        
        # Adjust for network congestion
        gas_limit = self._adjust_gas_for_congestion(gas_limit)
        
        # Estimate gas price
        gas_price = await self._estimate_optimal_gas_price()
        
        return gas_limit, gas_price
    
    async def _estimate_gas_async(self, transaction: Dict[str, Any]) -> int:
        """Async gas estimation with timeout"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.web3.eth.estimate_gas(transaction)
        )
    
    async def _estimate_optimal_gas_price(self) -> int:
        """Estimate optimal gas price based on network conditions"""
        try:
            # Get current gas price
            current_gas_price = await self._get_current_gas_price()
            
            # Adjust based on congestion
            if self.network_congestion_level > 0.8:
                multiplier = 1.5
            elif self.network_congestion_level > 0.6:
                multiplier = 1.2
            else:
                multiplier = 1.0
            
            return int(current_gas_price * multiplier)
            
        except Exception as e:
            logger.warning(f"Gas price estimation failed: {e}")
            return 20 * 10**9  # 20 gwei fallback
    
    async def _get_current_gas_price(self) -> int:
        """Get current gas price"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.web3.eth.gas_price
        )
    
    def _adjust_gas_for_congestion(self, base_gas: int) -> int:
        """Adjust gas limit based on network congestion"""
        if self.network_congestion_level > 0.8:
            return int(base_gas * 1.3)  # 30% increase
        elif self.network_congestion_level > 0.6:
            return int(base_gas * 1.15)  # 15% increase
        return base_gas
    
    async def update_network_congestion(self):
        """Update network congestion level"""
        try:
            latest_block = await self._get_latest_block_async()
            if latest_block and 'gasUsed' in latest_block and 'gasLimit' in latest_block:
                self.network_congestion_level = latest_block['gasUsed'] / latest_block['gasLimit']
            
        except Exception as e:
            logger.warning(f"Failed to update network congestion: {e}")
    
    async def _get_latest_block_async(self) -> Optional[Dict]:
        """Get latest block asynchronously"""
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(
                None,
                lambda: dict(self.web3.eth.get_block('latest'))
            )
        except Exception:
            return None

class RetryManager:
    """Enhanced retry manager with circuit breakers and optimization"""
    
    def __init__(self, web3: Web3, config: RetryConfig = None):
        self.web3 = web3
        self.config = config or RetryConfig()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.operation_metrics: Dict[str, OperationMetrics] = {}
        self.gas_optimizer = GasOptimizer(web3, self.config)
        self.rate_limiters: Dict[str, List[float]] = {}
        
    @asynccontextmanager
    async def retry_context(self, operation_id: str):
        """Context manager for retry operations"""
        circuit_breaker = self._get_circuit_breaker(operation_id)
        
        if not circuit_breaker.can_execute():
            raise Exception(f"Circuit breaker open for operation: {operation_id}")
        
        start_time = time.time()
        try:
            yield self
            # Record success
            circuit_breaker.record_success()
            self._update_metrics(operation_id, success=True, execution_time=time.time() - start_time)
            
        except Exception as e:
            # Record failure
            circuit_breaker.record_failure()
            self._update_metrics(operation_id, success=False, execution_time=time.time() - start_time)
            raise
    
    async def execute_with_retry(
        self,
        operation_id: str,
        operation_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute operation with advanced retry logic"""
        
        if not self._check_rate_limit(operation_id):
            raise Exception(f"Rate limit exceeded for operation: {operation_id}")
        
        last_exception = None
        metrics = self._get_operation_metrics(operation_id)
        
        for attempt in range(self.config.max_retries + 1):
            try:
                async with self.retry_context(operation_id):
                    # Update network conditions
                    await self.gas_optimizer.update_network_congestion()
                    
                    # Execute operation
                    start_gas = self.web3.eth.get_block('latest')['gasUsed'] if hasattr(self.web3.eth, 'get_block') else 0
                    
                    result = await self._execute_operation(operation_func, *args, **kwargs)
                    
                    # Record gas usage if this was a transaction
                    if isinstance(result, dict) and 'gasUsed' in result:
                        metrics.total_gas_used += result['gasUsed']
                        self._update_optimal_gas_limit(operation_id, result['gasUsed'])
                    
                    return result
                    
            except Exception as e:
                last_exception = e
                error_type = self._classify_error(e)
                
                logger.warning(f"Attempt {attempt + 1} failed for {operation_id}: {e}")
                
                # Don't retry permanent errors
                if error_type == RetryErrorType.PERMANENT:
                    break
                
                # Don't retry if we've reached max attempts
                if attempt >= self.config.max_retries:
                    break
                
                # Calculate delay based on error type and attempt
                delay = self._calculate_retry_delay(attempt, error_type)
                
                # Adjust gas parameters for next attempt if gas-related error
                if error_type == RetryErrorType.GAS_RELATED:
                    kwargs = self._adjust_gas_parameters(kwargs, attempt)
                
                logger.info(f"Retrying {operation_id} in {delay:.2f} seconds (attempt {attempt + 2})")
                await asyncio.sleep(delay)
        
        # All retries exhausted
        metrics.failed_attempts += 1
        raise Exception(f"Operation {operation_id} failed after {self.config.max_retries + 1} attempts. Last error: {last_exception}")
    
    async def _execute_operation(self, operation_func: Callable, *args, **kwargs) -> Any:
        """Execute the operation with timeout"""
        try:
            return await asyncio.wait_for(
                operation_func(*args, **kwargs),
                timeout=self.config.timeout_seconds
            )
        except asyncio.TimeoutError:
            raise Exception(f"Operation timed out after {self.config.timeout_seconds} seconds")
    
    def _classify_error(self, error: Exception) -> RetryErrorType:
        """Classify error type for retry logic"""
        error_str = str(error).lower()
        
        # Permanent errors - don't retry
        permanent_indicators = [
            'insufficient funds',
            'invalid signature',
            'unauthorized',
            'invalid parameter',
            'execution reverted',
            'invalid address'
        ]
        
        if any(indicator in error_str for indicator in permanent_indicators):
            return RetryErrorType.PERMANENT
        
        # Gas-related errors
        gas_indicators = [
            'gas',
            'out of gas',
            'gas limit',
            'gas price',
            'underpriced'
        ]
        
        if any(indicator in error_str for indicator in gas_indicators):
            return RetryErrorType.GAS_RELATED
        
        # Rate limiting
        rate_limit_indicators = [
            'rate limit',
            'too many requests',
            'throttled'
        ]
        
        if any(indicator in error_str for indicator in rate_limit_indicators):
            return RetryErrorType.RATE_LIMITED
        
        # Network congestion
        congestion_indicators = [
            'network congestion',
            'mempool full',
            'too busy'
        ]
        
        if any(indicator in error_str for indicator in congestion_indicators):
            return RetryErrorType.NETWORK_CONGESTION
        
        # Default to transient
        return RetryErrorType.TRANSIENT
    
    def _calculate_retry_delay(self, attempt: int, error_type: RetryErrorType) -> float:
        """Calculate retry delay with exponential backoff and jitter"""
        
        # Base delay calculation
        if error_type == RetryErrorType.RATE_LIMITED:
            base_delay = self.config.base_delay * 2  # Longer delay for rate limits
        elif error_type == RetryErrorType.NETWORK_CONGESTION:
            base_delay = self.config.base_delay * 1.5  # Moderate delay for congestion
        else:
            base_delay = self.config.base_delay
        
        # Exponential backoff
        delay = base_delay * (self.config.exponential_base ** attempt)
        
        # Apply backoff multiplier
        delay *= self.config.backoff_multiplier ** attempt
        
        # Cap at max delay
        delay = min(delay, self.config.max_delay)
        
        # Add jitter (±jitter_range%)
        jitter = delay * self.config.jitter_range * (random.random() * 2 - 1)
        delay += jitter
        
        return max(0.1, delay)  # Minimum 0.1 second delay
    
    def _adjust_gas_parameters(self, kwargs: Dict[str, Any], attempt: int) -> Dict[str, Any]:
        """Adjust gas parameters for retry attempt"""
        if 'gas' in kwargs:
            # Increase gas limit
            current_gas = kwargs['gas']
            new_gas = int(current_gas * (1 + 0.1 * attempt))  # 10% increase per attempt
            kwargs['gas'] = new_gas
        
        if 'gasPrice' in kwargs:
            # Increase gas price
            current_price = kwargs['gasPrice']
            multiplier = min(
                self.config.gas_price_multiplier ** attempt,
                self.config.max_gas_price_multiplier
            )
            kwargs['gasPrice'] = int(current_price * multiplier)
        
        return kwargs
    
    def _get_circuit_breaker(self, operation_id: str) -> CircuitBreaker:
        """Get or create circuit breaker for operation"""
        if operation_id not in self.circuit_breakers:
            self.circuit_breakers[operation_id] = CircuitBreaker(self.config)
        return self.circuit_breakers[operation_id]
    
    def _get_operation_metrics(self, operation_id: str) -> OperationMetrics:
        """Get or create operation metrics"""
        if operation_id not in self.operation_metrics:
            self.operation_metrics[operation_id] = OperationMetrics()
        return self.operation_metrics[operation_id]
    
    def _update_metrics(self, operation_id: str, success: bool, execution_time: float):
        """Update operation metrics"""
        metrics = self._get_operation_metrics(operation_id)
        metrics.total_attempts += 1
        
        if success:
            metrics.successful_attempts += 1
        else:
            metrics.failed_attempts += 1
        
        metrics.success_rate = metrics.successful_attempts / metrics.total_attempts
        metrics.last_execution_time = datetime.now()
    
    def _update_optimal_gas_limit(self, operation_id: str, gas_used: int):
        """Update optimal gas limit based on actual usage"""
        metrics = self._get_operation_metrics(operation_id)
        
        # Update average gas used
        if metrics.successful_attempts > 0:
            total_gas = metrics.average_gas_used * (metrics.successful_attempts - 1) + gas_used
            metrics.average_gas_used = total_gas / metrics.successful_attempts
        else:
            metrics.average_gas_used = gas_used
        
        # Calculate optimal gas limit with buffer
        metrics.optimal_gas_limit = int(metrics.average_gas_used * self.config.gas_estimation_buffer)
    
    def _check_rate_limit(self, operation_id: str) -> bool:
        """Check if operation is within rate limits"""
        current_time = time.time()
        
        if operation_id not in self.rate_limiters:
            self.rate_limiters[operation_id] = []
        
        # Clean old entries
        window_start = current_time - self.config.rate_limit_window
        self.rate_limiters[operation_id] = [
            t for t in self.rate_limiters[operation_id] if t > window_start
        ]
        
        # Check if under limit
        if len(self.rate_limiters[operation_id]) >= self.config.max_calls_per_window:
            return False
        
        # Add current request
        self.rate_limiters[operation_id].append(current_time)
        return True
    
    def get_operation_stats(self, operation_id: str) -> Dict[str, Any]:
        """Get comprehensive operation statistics"""
        metrics = self._get_operation_metrics(operation_id)
        circuit_breaker = self._get_circuit_breaker(operation_id)
        
        return {
            'operation_id': operation_id,
            'total_attempts': metrics.total_attempts,
            'successful_attempts': metrics.successful_attempts,
            'failed_attempts': metrics.failed_attempts,
            'success_rate': metrics.success_rate,
            'average_gas_used': metrics.average_gas_used,
            'optimal_gas_limit': metrics.optimal_gas_limit,
            'last_execution': metrics.last_execution_time.isoformat(),
            'circuit_breaker_state': circuit_breaker.state.value,
            'circuit_breaker_failures': circuit_breaker.failure_count,
            'network_congestion': self.gas_optimizer.network_congestion_level
        }
    
    def reset_circuit_breaker(self, operation_id: str):
        """Manually reset circuit breaker"""
        if operation_id in self.circuit_breakers:
            cb = self.circuit_breakers[operation_id]
            cb.state = CircuitBreakerState.CLOSED
            cb.failure_count = 0
            cb.half_open_calls = 0
            logger.info(f"Reset circuit breaker for operation: {operation_id}")

class ExternalCallOptimizer:
    """Optimizer for external contract calls"""
    
    def __init__(self, retry_manager: RetryManager):
        self.retry_manager = retry_manager
        self.call_cache: Dict[str, Any] = {}
        self.cache_ttl = 60  # 1 minute cache TTL
        
    async def optimized_call(
        self,
        contract_method: Callable,
        operation_id: str,
        cache_key: Optional[str] = None,
        *args,
        **kwargs
    ) -> Any:
        """Execute optimized external call with caching and retry"""
        
        # Check cache first
        if cache_key and cache_key in self.call_cache:
            cached_result, timestamp = self.call_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
        
        # Execute with retry logic
        result = await self.retry_manager.execute_with_retry(
            operation_id,
            contract_method,
            *args,
            **kwargs
        )
        
        # Cache result if cache key provided
        if cache_key:
            self.call_cache[cache_key] = (result, time.time())
        
        return result
    
    def clear_cache(self, cache_key: Optional[str] = None):
        """Clear cache entries"""
        if cache_key:
            self.call_cache.pop(cache_key, None)
        else:
            self.call_cache.clear()

# Example usage and integration
class GasOptimizedArbitrageExecutor:
    """Example integration of gas optimization with arbitrage execution"""
    
    def __init__(self, web3: Web3, contract_address: str):
        self.web3 = web3
        self.contract_address = contract_address
        self.retry_manager = RetryManager(web3)
        self.external_call_optimizer = ExternalCallOptimizer(self.retry_manager)
        
    async def execute_arbitrage_with_optimization(
        self,
        strategy_address: str,
        asset: str,
        amount: int,
        params: bytes
    ) -> Dict[str, Any]:
        """Execute arbitrage with gas optimization and retry logic"""
        
        operation_id = f"arbitrage_{strategy_address}_{asset}_{amount}"
        
        # Prepare transaction
        transaction = {
            'to': self.contract_address,
            'data': self._encode_arbitrage_call(strategy_address, asset, amount, params),
            'value': 0
        }
        
        # Optimize gas parameters
        metrics = self.retry_manager._get_operation_metrics(operation_id)
        gas_limit, gas_price = await self.retry_manager.gas_optimizer.estimate_optimal_gas(
            transaction, metrics
        )
        
        transaction.update({
            'gas': gas_limit,
            'gasPrice': gas_price
        })
        
        # Execute with retry logic
        result = await self.retry_manager.execute_with_retry(
            operation_id,
            self._send_transaction_async,
            transaction
        )
        
        return result
    
    async def _send_transaction_async(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Send transaction asynchronously"""
        loop = asyncio.get_event_loop()
        
        # Send transaction
        tx_hash = await loop.run_in_executor(
            None,
            lambda: self.web3.eth.send_transaction(transaction)
        )
        
        # Wait for receipt
        receipt = await loop.run_in_executor(
            None,
            lambda: self.web3.eth.wait_for_transaction_receipt(tx_hash)
        )
        
        return {
            'transactionHash': receipt.transactionHash.hex(),
            'gasUsed': receipt.gasUsed,
            'status': receipt.status,
            'blockNumber': receipt.blockNumber
        }
    
    def _encode_arbitrage_call(self, strategy: str, asset: str, amount: int, params: bytes) -> str:
        """Encode arbitrage function call"""
        # This would encode the actual contract call
        # Implementation depends on your contract ABI
        pass

# Factory function for easy integration
def create_gas_optimized_retry_manager(
    web3: Web3,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    gas_buffer: float = 1.2
) -> RetryManager:
    """Create a pre-configured retry manager with gas optimization"""
    
    config = RetryConfig(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
        gas_estimation_buffer=gas_buffer,
        exponential_base=2.0,
        jitter_range=0.25,
        failure_threshold=5,
        recovery_timeout=300.0
    )
    
    return RetryManager(web3, config)
