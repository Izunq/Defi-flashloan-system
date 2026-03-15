# 📡 Live Data Connection Configuration
# Configure real-time data feeds for the arbitrage system

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
import aiohttp
import websockets
import json
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# Exchange API Configurations
EXCHANGE_CONFIGS = {
    'binance': {
        'rest_url': 'https://api.binance.com/api/v3',
        'ws_url': 'wss://stream.binance.com:9443/ws',
        'api_key': os.getenv('BINANCE_API_KEY'),
        'api_secret': os.getenv('BINANCE_API_SECRET')
    },
    'coinbase': {
        'rest_url': 'https://api.exchange.coinbase.com',
        'ws_url': 'wss://ws-feed.exchange.coinbase.com',
        'api_key': os.getenv('COINBASE_API_KEY'),
        'api_secret': os.getenv('COINBASE_API_SECRET')
    },
    'kraken': {
        'rest_url': 'https://api.kraken.com/0/public',
        'ws_url': 'wss://ws.kraken.com',
        'api_key': os.getenv('KRAKEN_API_KEY'),
        'api_secret': os.getenv('KRAKEN_API_SECRET')
    },
    'uniswap_v3': {
        'subgraph_url': 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3',
        'contract_address': '${CONTRACT_ADDRESS}'
    }
}

# Blockchain Node Configurations
BLOCKCHAIN_NODES = {
    'ethereum': {
        'mainnet': os.getenv('ETHEREUM_MAINNET_RPC', 'https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY'),
        'arbitrum': os.getenv('ARBITRUM_RPC', 'https://arb-mainnet.g.alchemy.com/v2/YOUR_KEY'),
        'polygon': os.getenv('POLYGON_RPC', 'https://polygon-mainnet.g.alchemy.com/v2/YOUR_KEY'),
        'bsc': os.getenv('BSC_RPC', 'https://bsc-dataseed.binance.org/')
    }
}

class LiveDataConnector:
    """Manages live connections to exchanges and blockchain networks"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.connections = {}
        self.price_feeds = {}
        self.blockchain_connections = {}
        
    async def initialize_connections(self):
        """Initialize all live data connections"""
        self.logger.info("🔌 Initializing live data connections...")
        
        # Initialize blockchain connections
        await self._connect_to_blockchains()
        
        # Initialize exchange connections
        await self._connect_to_exchanges()
        
        # Start price monitoring
        await self._start_price_monitoring()
        
        self.logger.info("✅ All live data connections established")
    
    async def _connect_to_blockchains(self):
        """Connect to blockchain networks"""
        for network, rpc_url in BLOCKCHAIN_NODES['ethereum'].items():
            try:
                w3 = Web3(Web3.HTTPProvider(rpc_url))
                if w3.is_connected():
                    self.blockchain_connections[network] = w3
                    latest_block = w3.eth.block_number
                    self.logger.info(f"✅ Connected to {network} (Block: {latest_block})")
                else:
                    self.logger.error(f"❌ Failed to connect to {network}")
            except Exception as e:
                self.logger.error(f"❌ Error connecting to {network}: {e}")
    
    async def _connect_to_exchanges(self):
        """Connect to exchange WebSocket feeds"""
        for exchange, config in EXCHANGE_CONFIGS.items():
            if 'ws_url' in config:
                try:
                    # Start WebSocket connection for each exchange
                    asyncio.create_task(self._maintain_ws_connection(exchange, config))
                    self.logger.info(f"✅ WebSocket connection initiated for {exchange}")
                except Exception as e:
                    self.logger.error(f"❌ Failed to connect to {exchange}: {e}")
    
    async def _maintain_ws_connection(self, exchange: str, config: Dict):
        """Maintain WebSocket connection for an exchange"""
        while True:
            try:
                async with websockets.connect(config['ws_url']) as websocket:
                    self.connections[exchange] = websocket
                    
                    # Subscribe to relevant streams based on exchange
                    if exchange == 'binance':
                        subscribe_msg = {
                            "method": "SUBSCRIBE",
                            "params": [
                                "btcusdt@ticker",
                                "ethusdt@ticker",
                                "adausdt@ticker"
                            ],
                            "id": 1
                        }
                    elif exchange == 'coinbase':
                        subscribe_msg = {
                            "type": "subscribe",
                            "channels": [
                                {
                                    "name": "ticker",
                                    "product_ids": ["BTC-USD", "ETH-USD", "ADA-USD"]
                                }
                            ]
                        }
                    
                    await websocket.send(json.dumps(subscribe_msg))
                    
                    # Listen for messages
                    async for message in websocket:
                        data = json.loads(message)
                        await self._process_market_data(exchange, data)
                        
            except websockets.exceptions.ConnectionClosed:
                self.logger.warning(f"🔄 WebSocket connection to {exchange} closed, reconnecting...")
                await asyncio.sleep(5)
            except Exception as e:
                self.logger.error(f"❌ Error in {exchange} WebSocket: {e}")
                await asyncio.sleep(10)
    
    async def _process_market_data(self, exchange: str, data: Dict):
        """Process incoming market data"""
        try:
            # Store latest prices
            if exchange == 'binance' and 's' in data:
                symbol = data['s']
                price = float(data['c'])
                self.price_feeds[f"{exchange}_{symbol}"] = {
                    'price': price,
                    'timestamp': datetime.now(),
                    'volume': float(data['v']) if 'v' in data else 0
                }
            
            # Trigger arbitrage detection
            await self._check_arbitrage_opportunities()
            
        except Exception as e:
            self.logger.error(f"Error processing market data from {exchange}: {e}")
    
    async def _start_price_monitoring(self):
        """Start continuous price monitoring"""
        asyncio.create_task(self._monitor_prices())
    
    async def _monitor_prices(self):
        """Monitor price feeds for arbitrage opportunities"""
        while True:
            try:
                # Check for arbitrage opportunities every second
                await self._check_arbitrage_opportunities()
                await asyncio.sleep(1)
            except Exception as e:
                self.logger.error(f"Error in price monitoring: {e}")
                await asyncio.sleep(5)
    
    async def _check_arbitrage_opportunities(self):
        """Check for arbitrage opportunities across exchanges"""
        if len(self.price_feeds) < 2:
            return
        
        # Simple arbitrage detection (can be enhanced)
        btc_prices = {k: v['price'] for k, v in self.price_feeds.items() if 'BTC' in k}
        
        if len(btc_prices) >= 2:
            prices = list(btc_prices.values())
            min_price = min(prices)
            max_price = max(prices)
            
            if max_price > 0:
                profit_percentage = ((max_price - min_price) / min_price) * 100
                
                if profit_percentage > 0.1:  # 0.1% threshold
                    self.logger.info(f"🚨 Arbitrage opportunity detected: {profit_percentage:.2f}% profit potential")
                    # Here you would trigger the actual arbitrage execution

# Configuration template for environment variables
def create_env_template():
    """Create environment template for live data connections"""
    env_template = """
# 📡 LIVE DATA CONNECTION CONFIGURATION

# Blockchain RPC Endpoints
ETHEREUM_MAINNET_RPC=https://eth-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
ARBITRUM_RPC=https://arb-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
POLYGON_RPC=https://polygon-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
BSC_RPC=https://bsc-dataseed.binance.org/

# Exchange API Keys (for live trading - use testnet first!)
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_secret
COINBASE_API_KEY=your_coinbase_key
COINBASE_API_SECRET=your_coinbase_secret
KRAKEN_API_KEY=your_kraken_key
KRAKEN_API_SECRET=your_kraken_secret

# WebSocket Configuration
WS_RECONNECT_INTERVAL=5
MAX_RECONNECT_ATTEMPTS=10

# Arbitrage Thresholds
MIN_PROFIT_THRESHOLD=0.1
MAX_TRADE_SIZE_USD=1000
GAS_PRICE_LIMIT_GWEI=50

# Database for storing live data
LIVE_DATA_DATABASE_URL=postgresql://user:password@localhost:5432/live_data

# Redis for caching real-time data
REDIS_URL=redis://localhost:6379

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=8090
"""
    
    with open('.env.live-data', 'w') as f:
        f.write(env_template)
    
    print("📝 Created .env.live-data template")
    print("Please configure with your actual API keys and endpoints")

if __name__ == "__main__":
    # Create environment template
    create_env_template()
    
    # Start live data connector
    connector = LiveDataConnector()
    asyncio.run(connector.initialize_connections())
