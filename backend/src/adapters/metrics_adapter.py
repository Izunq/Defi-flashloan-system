"""
Metrics adapter for monitoring.
"""
import logging
import threading
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class MetricsAdapter:
    """Metrics adapter for monitoring."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the metrics adapter."""
        self.config = config
        self.enabled = config.get("enabled", False)
        self.prometheus_port = config.get("prometheus_port", 9090)
        self.metrics = {}
        self.server = None
    
    def start(self) -> bool:
        """Start the metrics server."""
        if not self.enabled:
            logger.info("Metrics are disabled")
            return False
        
        try:
            # Import prometheus_client
            import prometheus_client as prom
            
            # Create metrics
            self.metrics = {
                "blocks_processed": prom.Counter(
                    "blocks_processed_total",
                    "Total number of blocks processed"
                ),
                "transactions_processed": prom.Counter(
                    "transactions_processed_total",
                    "Total number of transactions processed"
                ),
                "processing_time": prom.Histogram(
                    "block_processing_time_seconds",
                    "Time taken to process a block",
                    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
                ),
                "block_size": prom.Gauge(
                    "block_size_bytes",
                    "Size of the last processed block in bytes"
                ),
                "transactions_per_block": prom.Gauge(
                    "transactions_per_block",
                    "Number of transactions in the last processed block"
                ),
                "gas_used_per_block": prom.Gauge(
                    "gas_used_per_block",
                    "Gas used in the last processed block"
                ),
                "errors": prom.Counter(
                    "processing_errors_total",
                    "Total number of processing errors"
                ),
                "last_block_number": prom.Gauge(
                    "last_block_number",
                    "Number of the last processed block"
                ),
                "contract_interactions": prom.Counter(
                    "contract_interactions_total",
                    "Total number of contract interactions",
                    ["contract_address", "function_signature"]
                ),
                "token_transfers": prom.Counter(
                    "token_transfers_total",
                    "Total number of token transfers",
                    ["token_address"]
                )
            }
            
            # Start server
            self.server = prom.start_http_server(self.prometheus_port)
            
            logger.info(f"Started Prometheus metrics server on port {self.prometheus_port}")
            return True
        except ImportError:
            logger.warning("prometheus_client not installed, metrics not available")
            return False
        except Exception as e:
            logger.error(f"Failed to start metrics server: {str(e)}")
            return False
    
    def stop(self) -> bool:
        """Stop the metrics server."""
        if self.server:
            # There's no direct way to stop the server in prometheus_client
            # This is a workaround
            import prometheus_client as prom
            prom.REGISTRY.unregister(self.metrics["blocks_processed"])
            prom.REGISTRY.unregister(self.metrics["transactions_processed"])
            prom.REGISTRY.unregister(self.metrics["processing_time"])
            prom.REGISTRY.unregister(self.metrics["block_size"])
            prom.REGISTRY.unregister(self.metrics["transactions_per_block"])
            prom.REGISTRY.unregister(self.metrics["gas_used_per_block"])
            prom.REGISTRY.unregister(self.metrics["errors"])
            prom.REGISTRY.unregister(self.metrics["last_block_number"])
            
            logger.info("Stopped Prometheus metrics server")
            return True
        return False
    
    def increment_blocks_processed(self) -> None:
        """Increment the blocks processed counter."""
        if not self.enabled or "blocks_processed" not in self.metrics:
            return
        
        self.metrics["blocks_processed"].inc()
    
    def increment_transactions_processed(self, count: int = 1) -> None:
        """Increment the transactions processed counter."""
        if not self.enabled or "transactions_processed" not in self.metrics:
            return
        
        self.metrics["transactions_processed"].inc(count)
    
    def record_processing_time(self, seconds: float) -> None:
        """Record the time taken to process a block."""
        if not self.enabled or "processing_time" not in self.metrics:
            return
        
        self.metrics["processing_time"].observe(seconds)
    
    def set_block_size(self, size: int) -> None:
        """Set the size of the last processed block."""
        if not self.enabled or "block_size" not in self.metrics:
            return
        
        self.metrics["block_size"].set(size)
    
    def set_transactions_per_block(self, count: int) -> None:
        """Set the number of transactions in the last processed block."""
        if not self.enabled or "transactions_per_block" not in self.metrics:
            return
        
        self.metrics["transactions_per_block"].set(count)
    
    def set_gas_used_per_block(self, gas: int) -> None:
        """Set the gas used in the last processed block."""
        if not self.enabled or "gas_used_per_block" not in self.metrics:
            return
        
        self.metrics["gas_used_per_block"].set(gas)
    
    def increment_errors(self) -> None:
        """Increment the errors counter."""
        if not self.enabled or "errors" not in self.metrics:
            return
        
        self.metrics["errors"].inc()
    
    def set_last_block_number(self, block_number: int) -> None:
        """Set the last processed block number."""
        if not self.enabled or "last_block_number" not in self.metrics:
            return
        
        self.metrics["last_block_number"].set(block_number)
    
    def increment_contract_interaction(self, contract_address: str, function_signature: str) -> None:
        """Increment the contract interactions counter."""
        if not self.enabled or "contract_interactions" not in self.metrics:
            return
        
        self.metrics["contract_interactions"].labels(
            contract_address=contract_address,
            function_signature=function_signature
        ).inc()
    
    def increment_token_transfer(self, token_address: str) -> None:
        """Increment the token transfers counter."""
        if not self.enabled or "token_transfers" not in self.metrics:
            return
        
        self.metrics["token_transfers"].labels(
            token_address=token_address
        ).inc()