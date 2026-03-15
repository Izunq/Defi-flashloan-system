#!/usr/bin/env python3
# =================================================================================================
# MAIN APPLICATION ENTRY POINT
# =================================================================================================

import os
import sys
import logging
import asyncio
import argparse
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("flashloan.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("flashloan")

# Import components
from database_manager import DatabaseManager, DBeaver
from matlab_bridge import MATLABArbitrageEngine
from monitoring_manager import MonitoringManager

class FlashloanApp:
    """
    Main application class
    """
    
    def __init__(self):
        """Initialize application"""
        # Load environment variables
        load_dotenv()
        
        # Initialize components
        self.db_manager = None
        self.matlab_engine = None
        self.monitoring_manager = None
        
        logger.info("Flashloan application initialized")
    
    async def initialize(self):
        """Initialize all components"""
        # Initialize database manager
        self.db_manager = DatabaseManager()
        logger.info("Database manager initialized")
        
        # Initialize MATLAB engine
        try:
            self.matlab_engine = MATLABArbitrageEngine()
            logger.info("MATLAB engine initialized")
        except ImportError:
            logger.warning("MATLAB engine not available, arbitrage optimization will be limited")
            self.matlab_engine = None
        
        # Initialize monitoring manager
        self.monitoring_manager = MonitoringManager()
        logger.info("Monitoring manager initialized")
    
    async def run(self):
        """Run the application"""
        # Initialize components
        await self.initialize()
        
        # Start monitoring
        monitoring_task = asyncio.create_task(
            self.monitoring_manager.run_monitoring_loop()
        )
        
        # Start arbitrage engine
        if self.matlab_engine:
            arbitrage_task = asyncio.create_task(
                self.run_arbitrage_engine()
            )
        
        # Wait for tasks to complete
        await asyncio.gather(
            monitoring_task,
            arbitrage_task if self.matlab_engine else asyncio.sleep(0)
        )
    
    async def run_arbitrage_engine(self):
        """Run the arbitrage engine"""
        logger.info("Starting arbitrage engine")
        
        while True:
            try:
                # Get market data
                market_data = await self.get_market_data()
                
                if not market_data:
                    logger.warning("No market data available")
                    await asyncio.sleep(10)
                    continue
                
                # Optimize arbitrage portfolio
                opportunities = await self.matlab_engine.optimize_portfolio(market_data)
                
                if opportunities:
                    logger.info(f"Found {len(opportunities)} arbitrage opportunities")
                    
                    # Store opportunities in database
                    await self.store_arbitrage_opportunities(opportunities)
                    
                    # Execute profitable opportunities
                    await self.execute_arbitrage_opportunities(opportunities)
                else:
                    logger.info("No arbitrage opportunities found")
                
                # Wait before next iteration
                await asyncio.sleep(30)
            except Exception as e:
                logger.error(f"Error in arbitrage engine: {e}")
                await asyncio.sleep(10)
    
    async def get_market_data(self) -> List[Dict]:
        """
        Get market data from various exchanges
        
        Returns:
            List of market data records
        """
        try:
            # Query market data from Redis cache
            token_pairs = ["BTC-USDT", "ETH-USDT", "BNB-USDT", "SOL-USDT", "AVAX-USDT"]
            exchanges = ["binance", "coinbase", "kraken", "kucoin"]
            
            market_data = []
            
            for token_pair in token_pairs:
                for exchange in exchanges:
                    # Get market data from Redis
                    key = f"market:prices:{token_pair}:{exchange}"
                    data = self.db_manager.cache_hash_get_all(key)
                    
                    if data:
                        # Create market data record
                        record = {
                            "token_pair": token_pair,
                            "exchange": exchange,
                            "price": float(data.get("price", 0)),
                            "volume_24h": float(data.get("volume_24h", 0)),
                            "liquidity": float(data.get("liquidity", 0)),
                            "timestamp": data.get("timestamp")
                        }
                        
                        market_data.append(record)
            
            return market_data
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return []
    
    async def store_arbitrage_opportunities(self, opportunities: List[Any]):
        """
        Store arbitrage opportunities in database
        
        Args:
            opportunities: List of arbitrage opportunities
        """
        try:
            # Prepare data for database
            records = []
            
            for opp in opportunities:
                # Create record
                record = {
                    "token_pair": opp.token_pair,
                    "exchange_a": opp.buy_exchange,
                    "exchange_b": opp.sell_exchange,
                    "price_difference": opp.price_difference,
                    "price_difference_percent": opp.price_difference_percent,
                    "potential_profit": opp.expected_profit,
                    "gas_cost": opp.gas_cost,
                    "execution_time": opp.execution_time,
                    "slippage": opp.slippage,
                    "executed": False
                }
                
                records.append(record)
            
            # Insert into database
            if records:
                query = """
                INSERT INTO arbitrage_opportunities
                (id, token_pair, exchange_a, exchange_b, price_difference, price_difference_percent, 
                 potential_profit, gas_cost, execution_time, slippage, executed, timestamp)
                VALUES
                (gen_random_uuid(), %(token_pair)s, %(exchange_a)s, %(exchange_b)s, %(price_difference)s, 
                 %(price_difference_percent)s, %(potential_profit)s, %(gas_cost)s, %(execution_time)s, 
                 %(slippage)s, %(executed)s, NOW())
                """
                
                await self.db_manager.execute_batch(query, records)
                
                logger.info(f"Stored {len(records)} arbitrage opportunities in database")
        except Exception as e:
            logger.error(f"Error storing arbitrage opportunities: {e}")
    
    async def execute_arbitrage_opportunities(self, opportunities: List[Any]):
        """
        Execute profitable arbitrage opportunities
        
        Args:
            opportunities: List of arbitrage opportunities
        """
        # Filter profitable opportunities
        profitable_opportunities = [
            opp for opp in opportunities 
            if opp.expected_profit > opp.gas_cost * 1.5  # Ensure profit is at least 50% more than gas cost
        ]
        
        if not profitable_opportunities:
            logger.info("No profitable arbitrage opportunities to execute")
            return
        
        # Sort by expected profit
        profitable_opportunities.sort(key=lambda x: x.expected_profit, reverse=True)
        
        # Execute top opportunities
        max_executions = 3  # Maximum number of opportunities to execute at once
        
        for i, opp in enumerate(profitable_opportunities[:max_executions]):
            try:
                logger.info(f"Executing arbitrage opportunity: {opp.token_pair} ({opp.buy_exchange} -> {opp.sell_exchange})")
                logger.info(f"Expected profit: ${opp.expected_profit:.2f}, Gas cost: ${opp.gas_cost:.2f}")
                
                # In a real implementation, this would execute the trade
                # For now, we'll just simulate execution
                
                # Update opportunity in database
                query = """
                UPDATE arbitrage_opportunities
                SET executed = true, execution_timestamp = NOW()
                WHERE token_pair = %(token_pair)s AND exchange_a = %(exchange_a)s AND exchange_b = %(exchange_b)s
                AND timestamp > NOW() - INTERVAL '5 minutes'
                AND executed = false
                LIMIT 1
                """
                
                params = {
                    "token_pair": opp.token_pair,
                    "exchange_a": opp.buy_exchange,
                    "exchange_b": opp.sell_exchange
                }
                
                await self.db_manager.execute_query(query, params)
                
                logger.info(f"Arbitrage opportunity executed successfully")
            except Exception as e:
                logger.error(f"Error executing arbitrage opportunity: {e}")
    
    async def close(self):
        """Close all components"""
        # Close database manager
        if self.db_manager:
            await self.db_manager.close()
        
        # Close MATLAB engine
        if self.matlab_engine:
            self.matlab_engine.close()
        
        logger.info("Application closed")


async def main():
    """Main function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Flashloan Arbitrage Application")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    # Set logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize application
    app = FlashloanApp()
    
    try:
        # Run application
        await app.run()
    except KeyboardInterrupt:
        logger.info("Application interrupted")
    finally:
        # Close application
        await app.close()


if __name__ == "__main__":
    asyncio.run(main())