#!/usr/bin/env python3
# =================================================================================================
# ARBITRAGE EXPORTER FOR PROMETHEUS
# =================================================================================================

import os
import time
import logging
import asyncio
from typing import Dict, List, Any, Optional
from prometheus_client import start_http_server, Gauge, Counter, Summary
from database_manager import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("arbitrage_exporter.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("arbitrage_exporter")

# Define Prometheus metrics
OPPORTUNITIES_DETECTED = Counter('arbitrage_opportunities_detected_total', 'Total number of arbitrage opportunities detected')
TRADES_EXECUTED = Counter('arbitrage_trades_executed_total', 'Total number of arbitrage trades executed')
PROFIT_TOTAL = Counter('arbitrage_profit_total', 'Total profit from arbitrage trades in USD')
GAS_COST_TOTAL = Counter('arbitrage_gas_cost_total', 'Total gas cost for arbitrage trades in USD')
EXECUTION_FAILURES = Counter('arbitrage_execution_failures_total', 'Total number of arbitrage execution failures')

OPPORTUNITY_PROFIT = Gauge('arbitrage_opportunity_profit', 'Profit of current arbitrage opportunity in USD', ['token_pair', 'buy_exchange', 'sell_exchange'])
OPPORTUNITY_PRICE_DIFF = Gauge('arbitrage_opportunity_price_diff_percent', 'Price difference percentage of current arbitrage opportunity', ['token_pair', 'buy_exchange', 'sell_exchange'])
OPPORTUNITY_SLIPPAGE = Gauge('arbitrage_opportunity_slippage', 'Expected slippage of current arbitrage opportunity', ['token_pair', 'buy_exchange', 'sell_exchange'])

EXECUTION_TIME = Summary('arbitrage_execution_time_seconds', 'Time taken to execute arbitrage trade')
TRADE_SIZE = Gauge('arbitrage_trade_size', 'Size of arbitrage trade in base units', ['token_pair'])

GAS_PRICE = Gauge('ethereum_gas_price', 'Current Ethereum gas price in Gwei')
TOKEN_PRICE = Gauge('token_price', 'Current token price in USD', ['token_pair', 'exchange'])
TOKEN_LIQUIDITY = Gauge('token_liquidity', 'Current token liquidity in USD', ['token_pair', 'exchange'])

class ArbitrageExporter:
    """
    Prometheus exporter for arbitrage metrics
    """
    
    def __init__(self, port: int = 9090, poll_interval: int = 15):
        """
        Initialize arbitrage exporter
        
        Args:
            port: Port to expose metrics on
            poll_interval: Interval in seconds to poll for metrics
        """
        self.port = port
        self.poll_interval = poll_interval
        self.db_manager = None
        
        logger.info(f"Arbitrage Exporter initialized on port {port}")
    
    async def start(self):
        """Start the exporter"""
        # Start Prometheus HTTP server
        start_http_server(self.port)
        logger.info(f"Prometheus metrics server started on port {self.port}")
        
        # Initialize database manager
        self.db_manager = DatabaseManager()
        logger.info("Database manager initialized")
        
        # Start metrics collection loop
        await self.collect_metrics_loop()
    
    async def collect_metrics_loop(self):
        """Collect metrics in a loop"""
        logger.info(f"Starting metrics collection loop with interval {self.poll_interval} seconds")
        
        while True:
            try:
                # Collect arbitrage metrics
                await self.collect_arbitrage_metrics()
                
                # Collect market metrics
                await self.collect_market_metrics()
                
                # Collect gas metrics
                await self.collect_gas_metrics()
                
                # Wait for next interval
                await asyncio.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
                await asyncio.sleep(5)  # Wait a bit before retrying
    
    async def collect_arbitrage_metrics(self):
        """Collect arbitrage metrics"""
        try:
            # Get arbitrage opportunities
            opportunities = await self.db_manager.execute_query("""
                SELECT id, token_pair, exchange_a, exchange_b, price_difference, price_difference_percent, 
                       potential_profit, executed, execution_tx_id, timestamp
                FROM arbitrage_opportunities
                WHERE timestamp > NOW() - INTERVAL '1 day'
                ORDER BY timestamp DESC
                LIMIT 100
            """)
            
            # Update opportunity metrics
            for opp in opportunities:
                token_pair = opp.get("token_pair")
                buy_exchange = opp.get("exchange_a")
                sell_exchange = opp.get("exchange_b")
                profit = opp.get("potential_profit", 0)
                price_diff = opp.get("price_difference_percent", 0)
                
                # Update gauges
                OPPORTUNITY_PROFIT.labels(token_pair=token_pair, buy_exchange=buy_exchange, sell_exchange=sell_exchange).set(profit)
                OPPORTUNITY_PRICE_DIFF.labels(token_pair=token_pair, buy_exchange=buy_exchange, sell_exchange=sell_exchange).set(price_diff)
            
            # Get executed trades
            executed_trades = await self.db_manager.execute_query("""
                SELECT COUNT(*) as count, SUM(potential_profit) as total_profit
                FROM arbitrage_opportunities
                WHERE executed = true AND timestamp > NOW() - INTERVAL '1 day'
            """)
            
            # Update counters
            if executed_trades and len(executed_trades) > 0:
                trade_count = executed_trades[0].get("count", 0)
                total_profit = executed_trades[0].get("total_profit", 0)
                
                # Set counters to current values
                TRADES_EXECUTED._value.set(trade_count)
                PROFIT_TOTAL._value.set(total_profit)
            
            # Get execution failures
            execution_failures = await self.db_manager.execute_query("""
                SELECT COUNT(*) as count
                FROM arbitrage_execution_logs
                WHERE status = 'failed' AND timestamp > NOW() - INTERVAL '1 day'
            """)
            
            # Update failure counter
            if execution_failures and len(execution_failures) > 0:
                failure_count = execution_failures[0].get("count", 0)
                EXECUTION_FAILURES._value.set(failure_count)
            
            # Get opportunity count
            opportunity_count = await self.db_manager.execute_query("""
                SELECT COUNT(*) as count
                FROM arbitrage_opportunities
                WHERE timestamp > NOW() - INTERVAL '1 day'
            """)
            
            # Update opportunity counter
            if opportunity_count and len(opportunity_count) > 0:
                count = opportunity_count[0].get("count", 0)
                OPPORTUNITIES_DETECTED._value.set(count)
            
            logger.debug("Arbitrage metrics collected")
        except Exception as e:
            logger.error(f"Error collecting arbitrage metrics: {e}")
    
    async def collect_market_metrics(self):
        """Collect market metrics"""
        try:
            # Get market data from Redis
            # This is faster than querying the database
            token_pairs = ["BTC-USDT", "ETH-USDT", "BNB-USDT", "SOL-USDT", "AVAX-USDT"]
            exchanges = ["binance", "coinbase", "kraken", "kucoin"]
            
            for token_pair in token_pairs:
                for exchange in exchanges:
                    # Get market data from Redis
                    key = f"market:prices:{token_pair}:{exchange}"
                    data = self.db_manager.cache_hash_get_all(key)
                    
                    if data:
                        # Update token price
                        if "price" in data:
                            price = float(data["price"])
                            TOKEN_PRICE.labels(token_pair=token_pair, exchange=exchange).set(price)
                        
                        # Update token liquidity
                        if "liquidity" in data:
                            liquidity = float(data["liquidity"])
                            TOKEN_LIQUIDITY.labels(token_pair=token_pair, exchange=exchange).set(liquidity)
            
            logger.debug("Market metrics collected")
        except Exception as e:
            logger.error(f"Error collecting market metrics: {e}")
    
    async def collect_gas_metrics(self):
        """Collect gas metrics"""
        try:
            # Get gas price from Redis
            gas_price = self.db_manager.cache_get("gas:price")
            
            if gas_price:
                # Update gas price
                GAS_PRICE.set(float(gas_price))
            
            logger.debug("Gas metrics collected")
        except Exception as e:
            logger.error(f"Error collecting gas metrics: {e}")


# Main function
async def main():
    # Initialize exporter
    exporter = ArbitrageExporter()
    
    # Start exporter
    await exporter.start()

# Run main function
if __name__ == "__main__":
    asyncio.run(main())