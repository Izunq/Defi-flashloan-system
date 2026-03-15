#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Market Data Connector for Simulink Models

This module provides real-time market data to Simulink models by connecting
to various cryptocurrency exchange APIs and other data sources. It handles
data normalization, synchronization, and buffering for reliable model inputs.

Author: DeFi Arbitrage System
Date: June 17, 2025
"""

import os
import time
import json
import logging
import requests
import websocket
import threading
import numpy as np
from queue import Queue
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone

# Import the Simulink bridge
from simulink_bridge import SimulinkBridge, MarketData

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('market_data_connector')


@dataclass
class ExchangeConfig:
    """Configuration for a cryptocurrency exchange."""
    name: str
    api_key: str = ""
    api_secret: str = ""
    base_url: str = ""
    websocket_url: str = ""
    rate_limit: int = 10  # requests per second
    timeout: float = 5.0  # seconds
    symbols: List[str] = field(default_factory=list)
    use_websocket: bool = True


@dataclass
class MarketDataConfig:
    """Configuration for market data collection."""
    exchanges: List[ExchangeConfig]
    update_interval: float = 1.0  # seconds
    buffer_size: int = 1000
    max_age: float = 60.0  # seconds
    retry_attempts: int = 3
    retry_delay: float = 1.0  # seconds
    use_fallback: bool = True
    fallback_timeout: float = 2.0  # seconds


class ExchangeConnector:
    """Base class for exchange API connectors."""
    
    def __init__(self, config: ExchangeConfig):
        """Initialize the exchange connector.
        
        Args:
            config: Exchange configuration
        """
        self.config = config
        self.name = config.name
        self.session = requests.Session()
        self.ws = None
        self.ws_thread = None
        self.running = False
        self.last_request_time = 0
        self.data_queue = Queue()
        self.last_data = {}
        
        # Add API key to headers if provided
        if config.api_key:
            self.session.headers.update({
                'X-API-Key': config.api_key
            })
        
        logger.info(f"Initialized connector for exchange: {self.name}")
    
    def _respect_rate_limit(self):
        """Ensure we don't exceed the exchange's rate limit."""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        min_interval = 1.0 / self.config.rate_limit
        
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        
        self.last_request_time = time.time()
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get current ticker data for a symbol.
        
        Args:
            symbol: Trading pair symbol (e.g., 'ETH-USDT')
            
        Returns:
            Dict[str, Any]: Ticker data
        """
        self._respect_rate_limit()
        
        try:
            response = self.session.get(
                f"{self.config.base_url}/ticker/{symbol}",
                timeout=self.config.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            # Normalize the data format
            normalized = {
                'exchange': self.name,
                'symbol': symbol,
                'price': float(data.get('last', 0)),
                'bid': float(data.get('bid', 0)),
                'ask': float(data.get('ask', 0)),
                'volume': float(data.get('volume', 0)),
                'timestamp': data.get('timestamp', time.time())
            }
            
            return normalized
        
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol} from {self.name}: {str(e)}")
            return {
                'exchange': self.name,
                'symbol': symbol,
                'price': 0.0,
                'bid': 0.0,
                'ask': 0.0,
                'volume': 0.0,
                'timestamp': time.time(),
                'error': str(e)
            }
    
    def get_order_book(self, symbol: str, depth: int = 20) -> Dict[str, Any]:
        """Get order book data for a symbol.
        
        Args:
            symbol: Trading pair symbol (e.g., 'ETH-USDT')
            depth: Depth of the order book to retrieve
            
        Returns:
            Dict[str, Any]: Order book data
        """
        self._respect_rate_limit()
        
        try:
            response = self.session.get(
                f"{self.config.base_url}/orderbook/{symbol}?depth={depth}",
                timeout=self.config.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            # Normalize the data format
            normalized = {
                'exchange': self.name,
                'symbol': symbol,
                'bids': data.get('bids', []),
                'asks': data.get('asks', []),
                'timestamp': data.get('timestamp', time.time())
            }
            
            return normalized
        
        except Exception as e:
            logger.error(f"Error fetching order book for {symbol} from {self.name}: {str(e)}")
            return {
                'exchange': self.name,
                'symbol': symbol,
                'bids': [],
                'asks': [],
                'timestamp': time.time(),
                'error': str(e)
            }
    
    def get_recent_trades(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """Get recent trades for a symbol.
        
        Args:
            symbol: Trading pair symbol (e.g., 'ETH-USDT')
            limit: Maximum number of trades to retrieve
            
        Returns:
            Dict[str, Any]: Recent trades data
        """
        self._respect_rate_limit()
        
        try:
            response = self.session.get(
                f"{self.config.base_url}/trades/{symbol}?limit={limit}",
                timeout=self.config.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            # Normalize the data format
            normalized = {
                'exchange': self.name,
                'symbol': symbol,
                'trades': data.get('trades', []),
                'timestamp': time.time()
            }
            
            return normalized
        
        except Exception as e:
            logger.error(f"Error fetching recent trades for {symbol} from {self.name}: {str(e)}")
            return {
                'exchange': self.name,
                'symbol': symbol,
                'trades': [],
                'timestamp': time.time(),
                'error': str(e)
            }
    
    def start_websocket(self, on_message: Callable[[Dict[str, Any]], None]):
        """Start a websocket connection to the exchange.
        
        Args:
            on_message: Callback function for handling websocket messages
        """
        if not self.config.use_websocket or not self.config.websocket_url:
            logger.warning(f"Websocket not configured for {self.name}")
            return False
        
        if self.ws:
            logger.warning(f"Websocket already running for {self.name}")
            return True
        
        def on_ws_message(ws, message):
            try:
                data = json.loads(message)
                on_message(data)
            except Exception as e:
                logger.error(f"Error processing websocket message from {self.name}: {str(e)}")
        
        def on_ws_error(ws, error):
            logger.error(f"Websocket error for {self.name}: {str(error)}")
        
        def on_ws_close(ws, close_status_code, close_msg):
            logger.info(f"Websocket closed for {self.name}: {close_msg} (code: {close_status_code})")
            if self.running:
                logger.info(f"Attempting to reconnect websocket for {self.name}")
                time.sleep(5)  # Wait before reconnecting
                self._start_ws_thread()
        
        def on_ws_open(ws):
            logger.info(f"Websocket opened for {self.name}")
            # Subscribe to symbols
            subscribe_msg = json.dumps({
                "method": "SUBSCRIBE",
                "params": [f"{s.lower()}@ticker" for s in self.config.symbols],
                "id": int(time.time())
            })
            ws.send(subscribe_msg)
        
        def ws_thread():
            self.ws = websocket.WebSocketApp(
                self.config.websocket_url,
                on_message=on_ws_message,
                on_error=on_ws_error,
                on_close=on_ws_close,
                on_open=on_ws_open
            )
            self.ws.run_forever()
        
        def _start_ws_thread():
            self.ws_thread = threading.Thread(target=ws_thread)
            self.ws_thread.daemon = True
            self.ws_thread.start()
        
        self.running = True
        _start_ws_thread()
        return True
    
    def stop_websocket(self):
        """Stop the websocket connection."""
        self.running = False
        if self.ws:
            self.ws.close()
            self.ws = None
        
        if self.ws_thread and self.ws_thread.is_alive():
            self.ws_thread.join(timeout=5.0)
            if self.ws_thread.is_alive():
                logger.warning(f"Websocket thread for {self.name} did not terminate gracefully")
        
        self.ws_thread = None
        logger.info(f"Stopped websocket for {self.name}")
        return True
    
    def process_websocket_message(self, message: Dict[str, Any]):
        """Process a websocket message and put it in the data queue.
        
        Args:
            message: Websocket message data
        """
        try:
            # Extract symbol and data from the message
            # This will vary by exchange, so we use a generic approach
            symbol = message.get('s', message.get('symbol', 'unknown'))
            
            # Normalize the data format
            normalized = {
                'exchange': self.name,
                'symbol': symbol,
                'price': float(message.get('c', message.get('price', 0))),
                'bid': float(message.get('b', message.get('bid', 0))),
                'ask': float(message.get('a', message.get('ask', 0))),
                'volume': float(message.get('v', message.get('volume', 0))),
                'timestamp': message.get('E', message.get('timestamp', time.time())) / 1000
                if message.get('E', 0) > 1e10 else message.get('E', time.time())
            }
            
            # Update last data
            self.last_data[symbol] = normalized
            
            # Put in queue
            self.data_queue.put(normalized)
            
        except Exception as e:
            logger.error(f"Error processing websocket message from {self.name}: {str(e)}")
    
    def get_latest_data(self, symbol: str) -> Dict[str, Any]:
        """Get the latest data for a symbol.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Dict[str, Any]: Latest market data
        """
        # If we have recent websocket data, use it
        if symbol in self.last_data:
            data_age = time.time() - self.last_data[symbol].get('timestamp', 0)
            if data_age < 5.0:  # Data less than 5 seconds old
                return self.last_data[symbol]
        
        # Otherwise, fetch via REST API
        return self.get_ticker(symbol)


class MarketDataConnector:
    """Connector for real-time market data from multiple exchanges."""
    
    def __init__(self, config: MarketDataConfig):
        """Initialize the market data connector.
        
        Args:
            config: Market data configuration
        """
        self.config = config
        self.exchanges = {}
        self.data_buffer = {}
        self.running = False
        self.update_thread = None
        self.gas_price_data = {
            'fast': 50.0,
            'standard': 30.0,
            'slow': 20.0,
            'timestamp': time.time()
        }
        
        # Initialize exchange connectors
        for exchange_config in config.exchanges:
            self.exchanges[exchange_config.name] = ExchangeConnector(exchange_config)
        
        logger.info(f"Initialized market data connector with {len(self.exchanges)} exchanges")
    
    def start(self):
        """Start collecting market data."""
        if self.running:
            logger.warning("Market data connector is already running")
            return
        
        self.running = True
        
        # Start websockets for all exchanges
        for name, exchange in self.exchanges.items():
            if exchange.config.use_websocket:
                exchange.start_websocket(exchange.process_websocket_message)
        
        # Start update thread for REST API fallback
        self.update_thread = threading.Thread(target=self._update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
        
        logger.info("Started market data collection")
    
    def stop(self):
        """Stop collecting market data."""
        if not self.running:
            logger.warning("Market data connector is not running")
            return
        
        self.running = False
        
        # Stop websockets for all exchanges
        for name, exchange in self.exchanges.items():
            if exchange.config.use_websocket:
                exchange.stop_websocket()
        
        # Stop update thread
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=5.0)
            if self.update_thread.is_alive():
                logger.warning("Update thread did not terminate gracefully")
        
        self.update_thread = None
        logger.info("Stopped market data collection")
    
    def _update_loop(self):
        """Background thread for updating market data via REST API."""
        logger.info("Starting market data update loop")
        
        while self.running:
            try:
                # Update gas prices periodically
                self._update_gas_prices()
                
                # Update market data for exchanges without websockets
                for name, exchange in self.exchanges.items():
                    if not exchange.config.use_websocket:
                        for symbol in exchange.config.symbols:
                            data = exchange.get_ticker(symbol)
                            self._process_market_data(data)
                
                # Sleep until next update
                time.sleep(self.config.update_interval)
                
            except Exception as e:
                logger.error(f"Error in market data update loop: {str(e)}")
                time.sleep(1.0)  # Sleep on error
    
    def _update_gas_prices(self):
        """Update Ethereum gas prices."""
        try:
            # Update gas prices every 30 seconds
            if time.time() - self.gas_price_data['timestamp'] > 30.0:
                response = requests.get(
                    "https://api.etherscan.io/api?module=gastracker&action=gasoracle",
                    timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == '1':
                        result = data.get('result', {})
                        self.gas_price_data = {
                            'fast': float(result.get('FastGasPrice', 50.0)),
                            'standard': float(result.get('ProposeGasPrice', 30.0)),
                            'slow': float(result.get('SafeGasPrice', 20.0)),
                            'timestamp': time.time()
                        }
                        logger.debug(f"Updated gas prices: {self.gas_price_data}")
        except Exception as e:
            logger.error(f"Error updating gas prices: {str(e)}")
    
    def _process_market_data(self, data: Dict[str, Any]):
        """Process market data and add it to the buffer.
        
        Args:
            data: Market data from an exchange
        """
        exchange = data.get('exchange')
        symbol = data.get('symbol')
        key = f"{exchange}:{symbol}"
        
        # Add to buffer
        if key not in self.data_buffer:
            self.data_buffer[key] = []
        
        self.data_buffer[key].append(data)
        
        # Trim buffer if it exceeds max size
        if len(self.data_buffer[key]) > self.config.buffer_size:
            self.data_buffer[key].pop(0)
    
    def get_latest_price(self, symbol: str, exchange: str = None) -> float:
        """Get the latest price for a symbol.
        
        Args:
            symbol: Trading pair symbol
            exchange: Exchange name (optional)
            
        Returns:
            float: Latest price
        """
        if exchange:
            # Get from specific exchange
            if exchange in self.exchanges:
                data = self.exchanges[exchange].get_latest_data(symbol)
                return data.get('price', 0.0)
            else:
                logger.warning(f"Exchange {exchange} not found")
                return 0.0
        else:
            # Get median price across all exchanges
            prices = []
            for name, exchange_connector in self.exchanges.items():
                data = exchange_connector.get_latest_data(symbol)
                price = data.get('price', 0.0)
                if price > 0:
                    prices.append(price)
            
            if prices:
                return np.median(prices)
            else:
                return 0.0
    
    def get_latest_market_data(self) -> MarketData:
        """Get the latest market data for all symbols.
        
        Returns:
            MarketData: Latest market data
        """
        # Collect prices and volumes
        prices = {}
        volumes = {}
        
        # Get data from all exchanges
        for name, exchange in self.exchanges.items():
            for symbol in exchange.config.symbols:
                data = exchange.get_latest_data(symbol)
                
                # Add to prices and volumes
                if data.get('price', 0) > 0:
                    key = f"{symbol.lower().replace('-', '_')}"
                    
                    # Store price by exchange
                    prices[f"{key}_{name.lower()}"] = data.get('price', 0.0)
                    
                    # Store volume by exchange
                    volumes[f"{key}_{name.lower()}"] = data.get('volume', 0.0)
                    
                    # Also store median price across exchanges
                    if key not in prices:
                        prices[key] = self.get_latest_price(symbol)
        
        # Create MarketData object
        market_data = MarketData(
            timestamp=time.time(),
            prices=prices,
            volumes=volumes,
            gas_prices={
                'fast': self.gas_price_data['fast'],
                'standard': self.gas_price_data['standard'],
                'slow': self.gas_price_data['slow']
            },
            additional_data={
                'block_time': 12.0,  # Ethereum average block time
                'network_congestion': min(1.0, self.gas_price_data['fast'] / 100.0)  # Normalized 0-1
            }
        )
        
        return market_data


def create_default_market_data_config() -> MarketDataConfig:
    """Create a default market data configuration.
    
    Returns:
        MarketDataConfig: Default configuration
    """
    # Define exchange configurations
    binance = ExchangeConfig(
        name="Binance",
        base_url="https://api.binance.com/api/v3",
        websocket_url="wss://stream.binance.com:9443/ws",
        symbols=["ETHUSDT", "BTCUSDT", "UNIUSDT", "AAVEUSDT"],
        use_websocket=True
    )
    
    coinbase = ExchangeConfig(
        name="Coinbase",
        base_url="https://api.pro.coinbase.com",
        websocket_url="wss://ws-feed.pro.coinbase.com",
        symbols=["ETH-USD", "BTC-USD", "UNI-USD", "AAVE-USD"],
        use_websocket=True
    )
    
    kraken = ExchangeConfig(
        name="Kraken",
        base_url="https://api.kraken.com/0/public",
        websocket_url="wss://ws.kraken.com",
        symbols=["ETHUSD", "XBTUSD", "UNIUSD", "AAVEUSD"],
        use_websocket=True
    )
    
    # Create market data configuration
    return MarketDataConfig(
        exchanges=[binance, coinbase, kraken],
        update_interval=1.0,
        buffer_size=1000,
        max_age=60.0,
        retry_attempts=3,
        retry_delay=1.0,
        use_fallback=True,
        fallback_timeout=2.0
    )


def main():
    """Run a demo of the market data connector."""
    # Create market data connector
    config = create_default_market_data_config()
    connector = MarketDataConnector(config)
    
    try:
        # Start collecting data
        connector.start()
        
        # Print market data every second
        for _ in range(10):  # Run for 10 seconds
            market_data = connector.get_latest_market_data()
            
            print("\nLatest Market Data:")
            print(f"Timestamp: {datetime.fromtimestamp(market_data.timestamp)}")
            
            print("\nPrices:")
            for symbol, price in market_data.prices.items():
                print(f"  {symbol}: ${price:.2f}")
            
            print("\nGas Prices (Gwei):")
            for speed, price in market_data.gas_prices.items():
                print(f"  {speed}: {price:.1f}")
            
            print("\nAdditional Data:")
            for key, value in market_data.additional_data.items():
                print(f"  {key}: {value}")
            
            time.sleep(1.0)
        
    except KeyboardInterrupt:
        print("Demo interrupted by user")
    finally:
        # Stop collecting data
        connector.stop()


if __name__ == "__main__":
    main()