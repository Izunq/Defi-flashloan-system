"""
Prime Brokerage Integration Module
Provides integration with prime brokerage services for institutional clients.
"""
import os
import logging
import json
import datetime
import uuid
from typing import Dict, List, Tuple, Any, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PrimeBrokerageClient:
    """
    Client for integrating with prime brokerage services.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize prime brokerage client.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config = self._load_config(config_path)
        self.api_key = self.config.get("api_key")
        self.api_secret = self.config.get("api_secret")
        self.base_url = self.config.get("base_url")
        
        # Connection state
        self.connected = False
        self.last_connection_time = None
        
        # Client information
        self.client_id = self.config.get("client_id")
        self.account_id = self.config.get("account_id")
        
        logger.info("Initialized Prime Brokerage Client")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """
        Load configuration from file or use defaults.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        default_config = {
            "api_key": "YOUR_API_KEY",
            "api_secret": "YOUR_API_SECRET",
            "base_url": "https://api.primebrokerage.example.com",
            "client_id": "CLIENT123",
            "account_id": "ACCOUNT456",
            "connection_timeout": 30,
            "retry_attempts": 3,
            "supported_brokers": ["Goldman Sachs", "Morgan Stanley", "JP Morgan", "UBS", "Credit Suisse"],
            "default_currency": "USD",
            "margin_requirements": {
                "initial": 0.5,
                "maintenance": 0.25
            }
        }
        
        if not config_path or not os.path.exists(config_path):
            logger.info("Using default prime brokerage configuration")
            return default_config
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Merge with defaults for any missing keys
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            
            logger.info(f"Loaded prime brokerage configuration from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}")
            return default_config
    
    def connect(self) -> bool:
        """
        Connect to the prime brokerage service.
        
        Returns:
            True if connected successfully, False otherwise
        """
        if self.connected:
            logger.info("Already connected to prime brokerage service")
            return True
        
        logger.info(f"Connecting to prime brokerage service at {self.base_url}")
        
        # In a real implementation, this would establish a connection to the prime brokerage API
        # This is a placeholder
        
        self.connected = True
        self.last_connection_time = datetime.datetime.now()
        
        logger.info("Connected to prime brokerage service")
        return True
    
    def disconnect(self) -> bool:
        """
        Disconnect from the prime brokerage service.
        
        Returns:
            True if disconnected successfully, False otherwise
        """
        if not self.connected:
            logger.info("Not connected to prime brokerage service")
            return True
        
        logger.info("Disconnecting from prime brokerage service")
        
        # In a real implementation, this would close the connection to the prime brokerage API
        # This is a placeholder
        
        self.connected = False
        
        logger.info("Disconnected from prime brokerage service")
        return True
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information from the prime brokerage.
        
        Returns:
            Account information
        """
        self._ensure_connected()
        
        logger.info(f"Getting account information for account {self.account_id}")
        
        # In a real implementation, this would fetch account information from the prime brokerage API
        # This is a placeholder
        
        account_info = {
            "account_id": self.account_id,
            "client_id": self.client_id,
            "account_type": "Institutional",
            "status": "Active",
            "currency": self.config.get("default_currency", "USD"),
            "balance": 10000000.00,
            "margin_available": 5000000.00,
            "margin_used": 2000000.00,
            "margin_ratio": 0.4,
            "margin_call_level": 0.75,
            "liquidation_level": 0.9,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": datetime.datetime.now().isoformat()
        }
        
        logger.info(f"Retrieved account information for account {self.account_id}")
        return account_info
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get current positions from the prime brokerage.
        
        Returns:
            List of positions
        """
        self._ensure_connected()
        
        logger.info(f"Getting positions for account {self.account_id}")
        
        # In a real implementation, this would fetch positions from the prime brokerage API
        # This is a placeholder
        
        positions = [
            {
                "asset": "BTC",
                "quantity": 100.0,
                "entry_price": 50000.0,
                "current_price": 55000.0,
                "value": 5500000.0,
                "pnl": 500000.0,
                "pnl_percentage": 10.0,
                "timestamp": datetime.datetime.now().isoformat()
            },
            {
                "asset": "ETH",
                "quantity": 1000.0,
                "entry_price": 3000.0,
                "current_price": 3500.0,
                "value": 3500000.0,
                "pnl": 500000.0,
                "pnl_percentage": 16.67,
                "timestamp": datetime.datetime.now().isoformat()
            }
        ]
        
        logger.info(f"Retrieved {len(positions)} positions for account {self.account_id}")
        return positions
    
    def execute_trade(self, asset: str, side: str, quantity: float, price: Optional[float] = None,
                     order_type: str = "MARKET") -> Dict[str, Any]:
        """
        Execute a trade through the prime brokerage.
        
        Args:
            asset: Asset to trade
            side: Trade side ("BUY" or "SELL")
            quantity: Quantity to trade
            price: Limit price (optional, required for LIMIT orders)
            order_type: Order type ("MARKET" or "LIMIT")
            
        Returns:
            Trade execution details
        """
        self._ensure_connected()
        
        if order_type == "LIMIT" and price is None:
            raise ValueError("Price is required for LIMIT orders")
        
        logger.info(f"Executing {order_type} {side} order for {quantity} {asset}")
        
        # In a real implementation, this would execute the trade through the prime brokerage API
        # This is a placeholder
        
        order_id = str(uuid.uuid4())
        execution_price = price if price else (55000.0 if asset == "BTC" else 3500.0)
        
        execution_details = {
            "order_id": order_id,
            "client_id": self.client_id,
            "account_id": self.account_id,
            "asset": asset,
            "side": side,
            "quantity": quantity,
            "order_type": order_type,
            "limit_price": price,
            "execution_price": execution_price,
            "status": "FILLED",
            "timestamp": datetime.datetime.now().isoformat(),
            "value": quantity * execution_price,
            "fee": quantity * execution_price * 0.001  # 0.1% fee
        }
        
        logger.info(f"Executed {order_type} {side} order for {quantity} {asset} at {execution_price}")
        return execution_details
    
    def get_trade_history(self, start_time: Optional[str] = None, end_time: Optional[str] = None,
                         limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get trade history from the prime brokerage.
        
        Args:
            start_time: Start time for history (ISO format)
            end_time: End time for history (ISO format)
            limit: Maximum number of trades to return
            
        Returns:
            List of trades
        """
        self._ensure_connected()
        
        logger.info(f"Getting trade history for account {self.account_id}")
        
        # In a real implementation, this would fetch trade history from the prime brokerage API
        # This is a placeholder
        
        # Generate some sample trades
        trades = []
        for i in range(limit):
            trade_time = datetime.datetime.now() - datetime.timedelta(hours=i)
            
            if start_time and trade_time.isoformat() < start_time:
                continue
                
            if end_time and trade_time.isoformat() > end_time:
                continue
            
            asset = "BTC" if i % 2 == 0 else "ETH"
            side = "BUY" if i % 3 == 0 else "SELL"
            price = 55000.0 if asset == "BTC" else 3500.0
            quantity = 1.0 if asset == "BTC" else 10.0
            
            trades.append({
                "trade_id": str(uuid.uuid4()),
                "order_id": str(uuid.uuid4()),
                "client_id": self.client_id,
                "account_id": self.account_id,
                "asset": asset,
                "side": side,
                "quantity": quantity,
                "price": price,
                "value": quantity * price,
                "fee": quantity * price * 0.001,  # 0.1% fee
                "timestamp": trade_time.isoformat()
            })
        
        logger.info(f"Retrieved {len(trades)} trades for account {self.account_id}")
        return trades
    
    def get_margin_requirements(self, asset: str) -> Dict[str, float]:
        """
        Get margin requirements for an asset.
        
        Args:
            asset: Asset to get margin requirements for
            
        Returns:
            Margin requirements
        """
        self._ensure_connected()
        
        logger.info(f"Getting margin requirements for {asset}")
        
        # In a real implementation, this would fetch margin requirements from the prime brokerage API
        # This is a placeholder
        
        # Default margin requirements
        default_requirements = self.config.get("margin_requirements", {
            "initial": 0.5,
            "maintenance": 0.25
        })
        
        # Asset-specific margin requirements
        asset_requirements = {
            "BTC": {"initial": 0.4, "maintenance": 0.2},
            "ETH": {"initial": 0.5, "maintenance": 0.25},
            "SOL": {"initial": 0.6, "maintenance": 0.3},
            "AVAX": {"initial": 0.6, "maintenance": 0.3},
            "DOT": {"initial": 0.7, "maintenance": 0.35}
        }
        
        requirements = asset_requirements.get(asset, default_requirements)
        
        logger.info(f"Retrieved margin requirements for {asset}: initial={requirements['initial']}, maintenance={requirements['maintenance']}")
        return requirements
    
    def get_available_brokers(self) -> List[Dict[str, Any]]:
        """
        Get available prime brokers.
        
        Returns:
            List of available brokers
        """
        self._ensure_connected()
        
        logger.info("Getting available prime brokers")
        
        # In a real implementation, this would fetch available brokers from the prime brokerage API
        # This is a placeholder
        
        brokers = []
        for broker_name in self.config.get("supported_brokers", []):
            brokers.append({
                "name": broker_name,
                "status": "Active",
                "supported_assets": ["BTC", "ETH", "SOL", "AVAX", "DOT"],
                "fee_schedule": {
                    "maker": 0.001,
                    "taker": 0.002
                },
                "minimum_deposit": 1000000.0
            })
        
        logger.info(f"Retrieved {len(brokers)} available prime brokers")
        return brokers
    
    def _ensure_connected(self) -> None:
        """Ensure that the client is connected to the prime brokerage service."""
        if not self.connected:
            self.connect()


class PrimeBrokerageManager:
    """
    Manager for prime brokerage integrations.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize prime brokerage manager.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config = self._load_config(config_path)
        self.clients = {}
        
        # Initialize clients for configured brokers
        for broker_config in self.config.get("brokers", []):
            broker_name = broker_config.get("name")
            if broker_name:
                self.clients[broker_name] = PrimeBrokerageClient(config_path=None)
                # Override client config with broker-specific config
                self.clients[broker_name].config.update(broker_config)
        
        logger.info(f"Initialized Prime Brokerage Manager with {len(self.clients)} brokers")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """
        Load configuration from file or use defaults.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        default_config = {
            "brokers": [
                {
                    "name": "Goldman Sachs",
                    "api_key": "GS_API_KEY",
                    "api_secret": "GS_API_SECRET",
                    "base_url": "https://api.gs.primebrokerage.example.com",
                    "client_id": "GS_CLIENT123",
                    "account_id": "GS_ACCOUNT456"
                },
                {
                    "name": "Morgan Stanley",
                    "api_key": "MS_API_KEY",
                    "api_secret": "MS_API_SECRET",
                    "base_url": "https://api.ms.primebrokerage.example.com",
                    "client_id": "MS_CLIENT123",
                    "account_id": "MS_ACCOUNT456"
                }
            ],
            "default_broker": "Goldman Sachs",
            "auto_connect": True,
            "connection_timeout": 30,
            "retry_attempts": 3
        }
        
        if not config_path or not os.path.exists(config_path):
            logger.info("Using default prime brokerage manager configuration")
            return default_config
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Merge with defaults for any missing keys
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            
            logger.info(f"Loaded prime brokerage manager configuration from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}")
            return default_config
    
    def get_client(self, broker_name: Optional[str] = None) -> PrimeBrokerageClient:
        """
        Get a prime brokerage client.
        
        Args:
            broker_name: Name of the broker (optional, uses default if not specified)
            
        Returns:
            Prime brokerage client
        """
        if not broker_name:
            broker_name = self.config.get("default_broker")
        
        if broker_name not in self.clients:
            raise ValueError(f"Prime broker not configured: {broker_name}")
        
        return self.clients[broker_name]
    
    def connect_all(self) -> Dict[str, bool]:
        """
        Connect to all configured prime brokers.
        
        Returns:
            Dictionary mapping broker names to connection status
        """
        results = {}
        
        for broker_name, client in self.clients.items():
            try:
                results[broker_name] = client.connect()
            except Exception as e:
                logger.error(f"Error connecting to {broker_name}: {e}")
                results[broker_name] = False
        
        logger.info(f"Connected to {sum(results.values())}/{len(results)} prime brokers")
        return results
    
    def disconnect_all(self) -> Dict[str, bool]:
        """
        Disconnect from all configured prime brokers.
        
        Returns:
            Dictionary mapping broker names to disconnection status
        """
        results = {}
        
        for broker_name, client in self.clients.items():
            try:
                results[broker_name] = client.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting from {broker_name}: {e}")
                results[broker_name] = False
        
        logger.info(f"Disconnected from {sum(results.values())}/{len(results)} prime brokers")
        return results
    
    def get_aggregated_positions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get aggregated positions across all prime brokers.
        
        Returns:
            Dictionary mapping assets to aggregated position information
        """
        aggregated = {}
        
        for broker_name, client in self.clients.items():
            try:
                positions = client.get_positions()
                
                for position in positions:
                    asset = position["asset"]
                    
                    if asset not in aggregated:
                        aggregated[asset] = {
                            "asset": asset,
                            "quantity": 0.0,
                            "value": 0.0,
                            "pnl": 0.0,
                            "brokers": {}
                        }
                    
                    aggregated[asset]["quantity"] += position["quantity"]
                    aggregated[asset]["value"] += position["value"]
                    aggregated[asset]["pnl"] += position["pnl"]
                    aggregated[asset]["brokers"][broker_name] = position
            except Exception as e:
                logger.error(f"Error getting positions from {broker_name}: {e}")
        
        # Calculate aggregated metrics
        for asset, position in aggregated.items():
            if position["quantity"] > 0:
                position["average_price"] = position["value"] / position["quantity"]
                position["pnl_percentage"] = position["pnl"] / (position["value"] - position["pnl"]) * 100
            else:
                position["average_price"] = 0.0
                position["pnl_percentage"] = 0.0
        
        logger.info(f"Retrieved aggregated positions for {len(aggregated)} assets across {len(self.clients)} brokers")
        return aggregated
    
    def execute_trade_with_best_broker(self, asset: str, side: str, quantity: float,
                                      price: Optional[float] = None, order_type: str = "MARKET") -> Dict[str, Any]:
        """
        Execute a trade with the best available broker.
        
        Args:
            asset: Asset to trade
            side: Trade side ("BUY" or "SELL")
            quantity: Quantity to trade
            price: Limit price (optional, required for LIMIT orders)
            order_type: Order type ("MARKET" or "LIMIT")
            
        Returns:
            Trade execution details
        """
        # In a real implementation, this would determine the best broker based on various factors
        # This is a placeholder
        
        # Use the default broker
        default_broker = self.config.get("default_broker")
        client = self.get_client(default_broker)
        
        logger.info(f"Executing trade for {quantity} {asset} with broker {default_broker}")
        
        execution_details = client.execute_trade(asset, side, quantity, price, order_type)
        execution_details["broker"] = default_broker
        
        return execution_details


if __name__ == "__main__":
    # Example usage
    manager = PrimeBrokerageManager()
    
    # Connect to all brokers
    connection_results = manager.connect_all()
    print("Connection results:", json.dumps(connection_results, indent=2))
    
    # Get aggregated positions
    positions = manager.get_aggregated_positions()
    print("Aggregated positions:", json.dumps(positions, indent=2))
    
    # Execute a trade
    trade = manager.execute_trade_with_best_broker("BTC", "BUY", 1.0)
    print("Trade execution:", json.dumps(trade, indent=2))
    
    # Disconnect from all brokers
    disconnection_results = manager.disconnect_all()
    print("Disconnection results:", json.dumps(disconnection_results, indent=2))