#!/usr/bin/env python3
"""
DataIngestionService.py - Service for ingesting blockchain data from Arbitrum network.

This service connects to the Arbitrum network and listens for new blocks.
It serves as the first data pipeline for the system to interact with the blockchain.
"""

import os
import time
import signal
import logging
import threading
import yaml
import json
from datetime import datetime
from typing import Optional, Callable, Dict, Any, List
from dotenv import load_dotenv
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.types import BlockData

# Import adapters and models
from backend.src.adapters.database_adapter import get_database_adapter
from backend.src.adapters.message_queue_adapter import get_message_queue_adapter
from backend.src.adapters.metrics_adapter import MetricsAdapter
from backend.src.filters.contract_filter import ContractFilter
from backend.src.models.block_model import Block, Transaction

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataIngestionService:
    """Service for ingesting blockchain data from Arbitrum network."""
    
    def __init__(self, config_path: str = "backend/config/service_config.yaml"):
        """
        Initialize the DataIngestionService.
        
        Args:
            config_path: Path to the configuration file
        """
        # Load environment variables
        load_dotenv()
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Service state
        self.running = False
        self.health_status = {"status": "initializing", "last_check": datetime.now().isoformat()}
        self.polling_interval = self.config.get("service", {}).get("polling_interval", 5)
        self.stats = {
            "blocks_processed": 0,
            "transactions_processed": 0,
            "service_start_time": datetime.now().isoformat(),
            "last_block_time": None,
            "errors": 0
        }
        
        # Initialize adapters
        self._init_blockchain_connection()
        self._init_database_adapter()
        self._init_message_queue_adapter()
        self._init_metrics_adapter()
        self._init_contract_filter()
        
        # Track the last processed block
        self.last_block_number = self._get_last_processed_block()
        
        # Update health status
        self._update_health("healthy", "Service initialized successfully")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from a YAML file."""
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_path}: {str(e)}")
            logger.info("Using default configuration")
            return {
                "service": {
                    "name": "data_ingestion_service",
                    "polling_interval": 5,
                    "health_check_port": 8080
                },
                "database": {
                    "type": "json_files"
                },
                "message_queue": {
                    "enabled": False
                },
                "metrics": {
                    "enabled": False
                },
                "blockchain": {
                    "network": "arbitrum",
                    "rpc_url_env_var": "ARBITRUM_RPC_URL"
                },
                "filtering": {
                    "enabled": False
                }
            }
    
    def _init_blockchain_connection(self):
        """Initialize the blockchain connection."""
        # Get Arbitrum RPC URL from environment
        rpc_url_env_var = self.config.get("blockchain", {}).get("rpc_url_env_var", "ARBITRUM_RPC_URL")
        self.arbitrum_rpc_url = os.getenv(rpc_url_env_var)
        if not self.arbitrum_rpc_url:
            self._update_health("error", f"{rpc_url_env_var} not found in environment variables")
            raise ValueError(f"{rpc_url_env_var} not found in environment variables")
        
        try:
            # Initialize Web3 connection
            self.w3 = Web3(Web3.HTTPProvider(self.arbitrum_rpc_url))
            
            # Add middleware for POA chains (Arbitrum is a POA chain)
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            # Check connection
            if not self.w3.is_connected():
                self._update_health("error", f"Failed to connect to Arbitrum network")
                raise ConnectionError(f"Failed to connect to Arbitrum network at {self.arbitrum_rpc_url}")
            
            logger.info(f"Successfully connected to Arbitrum network")
            current_block = self.w3.eth.block_number
            logger.info(f"Current block number: {current_block}")
            
        except Exception as e:
            self._update_health("error", f"Blockchain connection error: {str(e)}")
            raise
    
    def _init_database_adapter(self):
        """Initialize the database adapter."""
        try:
            # Get database configuration
            db_config = self.config.get("database", {})
            
            # Create database adapter
            self.db = get_database_adapter(db_config)
            
            # Connect to database
            if not self.db.connect():
                self._update_health("error", "Failed to connect to database")
                raise ConnectionError("Failed to connect to database")
            
            logger.info(f"Successfully connected to database")
            
        except Exception as e:
            self._update_health("error", f"Database initialization error: {str(e)}")
            raise
    
    def _init_message_queue_adapter(self):
        """Initialize the message queue adapter."""
        try:
            # Get message queue configuration
            mq_config = self.config.get("message_queue", {})
            
            # Create message queue adapter
            self.mq = get_message_queue_adapter(mq_config)
            
            # Connect to message queue
            if mq_config.get("enabled", False) and not self.mq.connect():
                self._update_health("warning", "Failed to connect to message queue")
                logger.warning("Failed to connect to message queue, using dummy adapter")
            
            logger.info(f"Message queue adapter initialized")
            
        except Exception as e:
            self._update_health("warning", f"Message queue initialization error: {str(e)}")
            logger.warning(f"Failed to initialize message queue: {str(e)}")
    
    def _init_metrics_adapter(self):
        """Initialize the metrics adapter."""
        try:
            # Get metrics configuration
            metrics_config = self.config.get("metrics", {})
            
            # Create metrics adapter
            self.metrics = MetricsAdapter(metrics_config)
            
            # Start metrics server
            if metrics_config.get("enabled", False):
                self.metrics.start()
            
            logger.info(f"Metrics adapter initialized")
            
        except Exception as e:
            self._update_health("warning", f"Metrics initialization error: {str(e)}")
            logger.warning(f"Failed to initialize metrics: {str(e)}")
    
    def _init_contract_filter(self):
        """Initialize the contract filter."""
        try:
            # Get filtering configuration
            filter_config = self.config.get("filtering", {})
            
            # Create contract filter
            self.contract_filter = ContractFilter(filter_config)
            
            logger.info(f"Contract filter initialized")
            
        except Exception as e:
            self._update_health("warning", f"Contract filter initialization error: {str(e)}")
            logger.warning(f"Failed to initialize contract filter: {str(e)}")
    
    def _get_last_processed_block(self) -> int:
        """Get the last processed block number."""
        try:
            # Get latest block from database
            latest_block = self.db.get_latest_block_number()
            
            if latest_block is not None:
                logger.info(f"Last processed block from database: {latest_block}")
                return latest_block
            
            # If no blocks in database, use current block
            current_block = self.w3.eth.block_number
            logger.info(f"No blocks in database, using current block: {current_block}")
            return current_block
            
        except Exception as e:
            logger.error(f"Error getting last processed block: {str(e)}")
            
            # Use current block as fallback
            current_block = self.w3.eth.block_number
            logger.info(f"Using current block as fallback: {current_block}")
            return current_block
    
    def _update_health(self, status: str, message: str = ""):
        """Update the health status of the service."""
        self.health_status = {
            "status": status,
            "message": message,
            "last_check": datetime.now().isoformat(),
            "stats": self.stats
        }
    
    def get_health(self) -> Dict[str, Any]:
        """Get the current health status of the service."""
        return self.health_status
    
    def extract_block_data(self, block_number: int) -> Block:
        """
        Extract relevant data from a block.
        
        Args:
            block_number: The block number to extract data from
            
        Returns:
            Block object containing block data
        """
        try:
            start_time = time.time()
            
            # Get full block data with transaction details
            block_data = self.w3.eth.get_block(block_number, full_transactions=True)
            
            # Convert to Block model
            block = Block.from_web3_block(block_data)
            
            # Record metrics
            processing_time = time.time() - start_time
            self.metrics.record_processing_time(processing_time)
            self.metrics.set_block_size(block.size)
            self.metrics.set_transactions_per_block(block.transaction_count)
            self.metrics.set_gas_used_per_block(block.gas_used)
            self.metrics.set_last_block_number(block.number)
            
            return block
            
        except Exception as e:
            logger.error(f"Error extracting data from block {block_number}: {str(e)}")
            self.stats["errors"] += 1
            self.metrics.increment_errors()
            raise
    
    def process_block(self, block: Block) -> bool:
        """
        Process a block and its transactions.
        
        Args:
            block: Block object to process
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Save block to database
            if not self.db.save_block(block):
                logger.error(f"Failed to save block {block.number} to database")
                return False
            
            # Publish block to message queue
            self.mq.publish_block(block)
            
            # Process transactions
            if block.transactions:
                # Filter transactions if filtering is enabled
                filtered_transactions = []
                for tx in block.transactions:
                    tx_dict = tx.dict(by_alias=True)
                    if self.contract_filter.should_process_transaction(tx_dict):
                        filtered_transactions.append(tx)
                        
                        # Record contract interaction metrics
                        tx_type = self.contract_filter.get_transaction_type(tx_dict)
                        if tx_type == "contract_interaction":
                            function_sig = self.contract_filter.get_function_signature(tx_dict)
                            if function_sig and tx.to_address:
                                self.metrics.increment_contract_interaction(tx.to_address, function_sig)
                        elif tx_type == "token_transfer" and tx.to_address:
                            self.metrics.increment_token_transfer(tx.to_address)
                
                # Save filtered transactions to database
                if filtered_transactions:
                    if not self.db.save_transactions(filtered_transactions):
                        logger.error(f"Failed to save transactions for block {block.number} to database")
                    
                    # Publish transactions to message queue
                    for tx in filtered_transactions:
                        self.mq.publish_transaction(tx)
                    
                    # Update stats
                    self.stats["transactions_processed"] += len(filtered_transactions)
                    self.metrics.increment_transactions_processed(len(filtered_transactions))
            
            # Update stats
            self.stats["blocks_processed"] += 1
            self.stats["last_block_time"] = datetime.now().isoformat()
            self.metrics.increment_blocks_processed()
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing block {block.number}: {str(e)}")
            self.stats["errors"] += 1
            self.metrics.increment_errors()
            return False
    
    def subscribe_to_new_blocks(self, callback: Optional[Callable] = None):
        """
        Subscribe to new blocks on the Arbitrum network.
        
        Args:
            callback: Optional callback function to execute when a new block is found.
                     If None, the block number will be printed to the console.
        """
        self.running = True
        logger.info(f"Starting to listen for new blocks (polling every {self.polling_interval} seconds)...")
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        consecutive_errors = 0
        
        while self.running:
            try:
                # Get current block number
                current_block = self.w3.eth.block_number
                
                # Check if there's a new block
                if current_block > self.last_block_number:
                    logger.info(f"New block detected: {current_block}")
                    
                    # Extract block data
                    block = self.extract_block_data(current_block)
                    
                    # Process block
                    if self.process_block(block):
                        # Execute callback if provided, otherwise print block number
                        if callback:
                            callback(block)
                        else:
                            print(f"New block mined: {current_block}")
                            print(f"Transaction count: {block.transaction_count}")
                        
                        # Update last processed block
                        self.last_block_number = current_block
                    
                    # Reset consecutive errors counter on success
                    consecutive_errors = 0
                    self._update_health("healthy", "Processing blocks normally")
                
                # Adaptive polling: Increase interval if we've had consecutive errors
                sleep_time = self.polling_interval * (1 + min(consecutive_errors, 5))
                time.sleep(sleep_time)
                
            except Exception as e:
                consecutive_errors += 1
                self.stats["errors"] += 1
                self.metrics.increment_errors()
                
                logger.error(f"Error while listening for new blocks: {str(e)}")
                self._update_health("degraded", f"Error processing blocks: {str(e)}")
                
                # Exponential backoff for repeated errors (max 60 seconds)
                backoff_time = min(self.polling_interval * (2 ** consecutive_errors), 60)
                logger.info(f"Backing off for {backoff_time} seconds before retry")
                time.sleep(backoff_time)
        
        logger.info("Block subscription stopped")
    
    def _signal_handler(self, sig, frame):
        """Handle termination signals for graceful shutdown."""
        logger.info(f"Received signal {sig}, shutting down gracefully...")
        self.running = False
    
    def start_health_check_server(self):
        """Start a simple HTTP server for health checks."""
        try:
            from http.server import HTTPServer, BaseHTTPRequestHandler
            
            service = self  # Reference to the service for the handler
            port = self.config.get("service", {}).get("health_check_port", 8080)
            
            class HealthCheckHandler(BaseHTTPRequestHandler):
                def do_GET(self):
                    if self.path == '/health':
                        health_data = service.get_health()
                        self.send_response(200 if health_data["status"] in ["healthy", "initializing"] else 503)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(health_data).encode())
                    else:
                        self.send_response(404)
                        self.end_headers()
            
            server = HTTPServer(('', port), HealthCheckHandler)
            logger.info(f"Starting health check server on port {port}")
            
            # Run server in a separate thread
            thread = threading.Thread(target=server.serve_forever)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            logger.error(f"Failed to start health check server: {str(e)}")
    
    def shutdown(self):
        """Shutdown the service."""
        logger.info("Shutting down DataIngestionService...")
        
        # Stop running
        self.running = False
        
        # Disconnect from database
        try:
            self.db.disconnect()
            logger.info("Disconnected from database")
        except Exception as e:
            logger.error(f"Error disconnecting from database: {str(e)}")
        
        # Disconnect from message queue
        try:
            self.mq.disconnect()
            logger.info("Disconnected from message queue")
        except Exception as e:
            logger.error(f"Error disconnecting from message queue: {str(e)}")
        
        # Stop metrics server
        try:
            self.metrics.stop()
            logger.info("Stopped metrics server")
        except Exception as e:
            logger.error(f"Error stopping metrics server: {str(e)}")
        
        logger.info("DataIngestionService shutdown complete")

def main():
    """Main entry point for the DataIngestionService."""
    try:
        # Initialize the service
        service = DataIngestionService()
        
        # Start health check server
        service.start_health_check_server()
        
        # Subscribe to new blocks
        service.subscribe_to_new_blocks()
        
    except Exception as e:
        logger.error(f"Failed to start DataIngestionService: {str(e)}")
        return 1
    finally:
        # Ensure service is properly shutdown
        if 'service' in locals():
            service.shutdown()
    
    return 0

if __name__ == "__main__":
    exit(main())