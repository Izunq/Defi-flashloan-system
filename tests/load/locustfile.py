"""
Phase 4 Testing: Load Testing with Locust
Load testing for the Flash Loan Arbitrage System
Based on the guide provided in the Implementation Plan
"""

from locust import User, task, between, events
import redis
import json
import time
import random
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedisPublisher:
    """Redis client to publish events, simulating market data scanners."""
    
    def __init__(self, host="localhost", port=6379, db=0):
        try:
            self.r = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            # Test connection
            self.r.ping()
            logger.info(f"Connected to Redis at {host}:{port}")
        except redis.ConnectionError:
            logger.error(f"Failed to connect to Redis at {host}:{port}")
            self.r = None

    def publish(self, channel: str, data: Dict[str, Any]) -> bool:
        """Publish data to Redis channel"""
        try:
            if self.r:
                result = self.r.publish(channel, json.dumps(data))
                return result > 0
            return False
        except Exception as e:
            logger.error(f"Error publishing to channel {channel}: {e}")
            return False

class MarketScannerUser(User):
    """Locust user class simulating market scanner activity"""
    
    wait_time = between(0.1, 0.5)  # Simulate 2-10 events per second
    
    def on_start(self):
        """Called when a user starts"""
        self.publisher = RedisPublisher()
        self.user_id = random.randint(1000, 9999)
        self.opportunities_sent = 0
        self.errors = 0
        logger.info(f"Market scanner user {self.user_id} starting...")

    def on_stop(self):
        """Called when a user stops"""
        logger.info(f"User {self.user_id} stopping. Sent {self.opportunities_sent} opportunities, {self.errors} errors")

    @task(10)
    def publish_market_event(self):
        """Simulates finding a new market opportunity - highest frequency task"""
        
        start_time = time.time()
        
        try:
            # Generate realistic market opportunity
            base_prices = {
                "ETH/USDT": 3000,
                "BTC/USDT": 60000,
                "WBTC/ETH": 20,
                "USDC/USDT": 1.0001,
                "DAI/USDT": 0.9999
            }
            
            pair = random.choice(list(base_prices.keys()))
            base_price = base_prices[pair]
            
            # Add realistic price variation
            price_variation = random.uniform(-0.02, 0.02)  # ±2%
            dex_a_price = base_price * (1 + price_variation)
            
            # Create arbitrage opportunity with varying profit margins
            profit_margin = random.uniform(0.001, 0.05)  # 0.1% to 5%
            if random.random() < 0.3:  # 30% chance of profitable opportunity
                dex_b_price = dex_a_price * (1 + profit_margin)
            else:  # 70% chance of non-profitable
                dex_b_price = dex_a_price * (1 + random.uniform(-0.01, 0.015))
            
            opportunity = {
                "pair": pair,
                "dex_a": random.choice(["Uniswap", "SushiSwap", "Balancer"]),
                "dex_b": random.choice(["Uniswap", "SushiSwap", "Balancer", "Curve"]),
                "dex_a_price": round(dex_a_price, 6),
                "dex_b_price": round(dex_b_price, 6),
                "volume": random.uniform(1000, 100000),
                "timestamp": time.time(),
                "block_number": random.randint(18500000, 18600000),
                "gas_price": random.uniform(15, 50),  # Gwei
                "user_id": self.user_id,
                "sequence": self.opportunities_sent
            }
            
            success = self.publisher.publish("market-data-events", opportunity)
            
            if success:
                self.opportunities_sent += 1
                # Record successful event
                events.request.fire(
                    request_type="REDIS_PUBLISH",
                    name="market_opportunity",
                    response_time=(time.time() - start_time) * 1000,
                    response_length=len(json.dumps(opportunity)),
                    exception=None,
                    context=self.context()
                )
            else:
                self.errors += 1
                events.request.fire(
                    request_type="REDIS_PUBLISH",
                    name="market_opportunity",
                    response_time=(time.time() - start_time) * 1000,
                    response_length=0,
                    exception=Exception("Failed to publish to Redis"),
                    context=self.context()
                )
                
        except Exception as e:
            self.errors += 1
            events.request.fire(
                request_type="REDIS_PUBLISH",
                name="market_opportunity",
                response_time=(time.time() - start_time) * 1000,
                response_length=0,
                exception=e,
                context=self.context()
            )

    @task(3)
    def publish_high_value_opportunity(self):
        """Simulates finding a high-value arbitrage opportunity"""
        
        start_time = time.time()
        
        try:
            # Generate high-profit opportunity
            opportunity = {
                "pair": "ETH/USDT",
                "dex_a": "Uniswap",
                "dex_b": "SushiSwap",
                "dex_a_price": 3000.0,
                "dex_b_price": 3000.0 * (1 + random.uniform(0.02, 0.08)),  # 2-8% profit
                "volume": random.uniform(50000, 500000),  # High volume
                "timestamp": time.time(),
                "block_number": random.randint(18500000, 18600000),
                "gas_price": random.uniform(20, 80),
                "priority": "high",
                "confidence": random.uniform(0.8, 0.99),
                "user_id": self.user_id
            }
            
            success = self.publisher.publish("high-priority-opportunities", opportunity)
            
            events.request.fire(
                request_type="REDIS_PUBLISH",
                name="high_value_opportunity",
                response_time=(time.time() - start_time) * 1000,
                response_length=len(json.dumps(opportunity)),
                exception=None if success else Exception("Publish failed"),
                context=self.context()
            )
            
        except Exception as e:
            events.request.fire(
                request_type="REDIS_PUBLISH",
                name="high_value_opportunity",
                response_time=(time.time() - start_time) * 1000,
                response_length=0,
                exception=e,
                context=self.context()
            )

    @task(2)
    def publish_market_update(self):
        """Simulates general market data updates"""
        
        start_time = time.time()
        
        try:
            market_update = {
                "type": "market_update",
                "timestamp": time.time(),
                "gas_price": random.uniform(15, 100),
                "block_number": random.randint(18500000, 18600000),
                "network_congestion": random.choice(["low", "medium", "high"]),
                "total_volume_24h": random.uniform(1000000, 10000000),
                "active_pairs": random.randint(50, 200),
                "user_id": self.user_id
            }
            
            success = self.publisher.publish("market-updates", market_update)
            
            events.request.fire(
                request_type="REDIS_PUBLISH",
                name="market_update",
                response_time=(time.time() - start_time) * 1000,
                response_length=len(json.dumps(market_update)),
                exception=None if success else Exception("Publish failed"),
                context=self.context()
            )
            
        except Exception as e:
            events.request.fire(
                request_type="REDIS_PUBLISH",
                name="market_update",
                response_time=(time.time() - start_time) * 1000,
                response_length=0,
                exception=e,
                context=self.context()
            )

    @task(1)
    def publish_system_status(self):
        """Simulates system status updates"""
        
        start_time = time.time()
        
        try:
            status_update = {
                "type": "system_status",
                "timestamp": time.time(),
                "scanner_id": f"scanner_{self.user_id}",
                "status": "active",
                "opportunities_found": self.opportunities_sent,
                "errors": self.errors,
                "uptime": random.uniform(3600, 86400),  # 1 hour to 1 day
                "cpu_usage": random.uniform(0.1, 0.8),
                "memory_usage": random.uniform(0.2, 0.9)
            }
            
            success = self.publisher.publish("system-status", status_update)
            
            events.request.fire(
                request_type="REDIS_PUBLISH", 
                name="system_status",
                response_time=(time.time() - start_time) * 1000,
                response_length=len(json.dumps(status_update)),
                exception=None if success else Exception("Publish failed"),
                context=self.context()
            )
            
        except Exception as e:
            events.request.fire(
                request_type="REDIS_PUBLISH",
                name="system_status",
                response_time=(time.time() - start_time) * 1000,
                response_length=0,
                exception=e,
                context=self.context()
            )

class ArbitrageExecutorUser(User):
    """Simulates the arbitrage execution system under load"""
    
    wait_time = between(1, 5)  # Less frequent than market scanners
    
    def on_start(self):
        """Initialize executor user"""
        self.publisher = RedisPublisher()
        self.user_id = f"executor_{random.randint(1000, 9999)}"
        self.transactions_attempted = 0
        self.successful_transactions = 0

    @task(5)
    def execute_arbitrage_trade(self):
        """Simulates executing an arbitrage trade"""
        
        start_time = time.time()
        
        try:
            # Simulate trade execution
            trade_data = {
                "type": "trade_execution",
                "trade_id": f"trade_{int(time.time())}_{random.randint(1000, 9999)}",
                "pair": "ETH/USDT",
                "amount": random.uniform(1, 10),
                "profit_estimate": random.uniform(10, 500),
                "gas_limit": random.randint(250000, 500000),
                "timestamp": time.time(),
                "executor_id": self.user_id
            }
            
            self.transactions_attempted += 1
            
            # Simulate success/failure (85% success rate)
            if random.random() < 0.85:
                trade_data["status"] = "success"
                trade_data["actual_profit"] = trade_data["profit_estimate"] * random.uniform(0.8, 1.2)
                trade_data["tx_hash"] = f"0x{''.join([random.choice('0123456789abcdef') for _ in range(64)])}"
                self.successful_transactions += 1
                
                success = self.publisher.publish("trade-executions", trade_data)
                
                events.request.fire(
                    request_type="TRADE_EXECUTION",
                    name="arbitrage_trade",
                    response_time=(time.time() - start_time) * 1000,
                    response_length=len(json.dumps(trade_data)),
                    exception=None,
                    context=self.context()
                )
            else:
                trade_data["status"] = "failed"
                trade_data["error"] = random.choice([
                    "insufficient_liquidity",
                    "slippage_too_high", 
                    "gas_limit_exceeded",
                    "price_moved"
                ])
                
                events.request.fire(
                    request_type="TRADE_EXECUTION",
                    name="arbitrage_trade",
                    response_time=(time.time() - start_time) * 1000,
                    response_length=0,
                    exception=Exception(trade_data["error"]),
                    context=self.context()
                )
                
        except Exception as e:
            events.request.fire(
                request_type="TRADE_EXECUTION",
                name="arbitrage_trade",
                response_time=(time.time() - start_time) * 1000,
                response_length=0,
                exception=e,
                context=self.context()
            )

# Event handlers for test reporting
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when the test starts"""
    logger.info("🚀 Starting load test for Flash Loan Arbitrage System")
    logger.info("Test will simulate market scanners and arbitrage executors")

@events.test_stop.add_listener  
def on_test_stop(environment, **kwargs):
    """Called when the test stops"""
    logger.info("🏁 Load test completed")
    
    # Print summary statistics
    stats = environment.stats
    logger.info(f"Total requests: {stats.total.num_requests}")
    logger.info(f"Total failures: {stats.total.num_failures}")
    logger.info(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    logger.info(f"Max response time: {stats.total.max_response_time:.2f}ms")

if __name__ == "__main__":
    # Can be run standalone for debugging
    import subprocess
    import sys
    
    print("Starting Locust load test...")
    print("Open http://localhost:8089 in your browser to configure and start the test")
    
    # Run locust with this file
    subprocess.run([
        sys.executable, "-m", "locust",
        "-f", __file__,
        "--host", "redis://localhost:6379"
    ])
