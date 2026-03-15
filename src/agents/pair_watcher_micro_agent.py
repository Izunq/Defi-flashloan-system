#!/usr/bin/env python3
"""
👁️ PAIR WATCHER MICRO-AGENT - SPECIALIZED DEX PAIR MONITOR
==========================================================

This module implements a specialized micro-agent that monitors a specific
token pair on specific DEXes for arbitrage opportunities.

KEY FEATURES:
- Hyper-specialized to watch a single token pair
- Monitors multiple DEXes for price differences
- Publishes discoveries to the swarm when opportunities are found
- Lightweight design for massive parallelism

Author: AI Assistant
Version: 1.0
Date: June 2025
"""

import time
import json
import logging
import random
from typing import Dict, List, Any, Optional, Tuple
from web3 import Web3

from src.agents.micro_agent_template import MicroAgent, MicroAgentStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger("PairWatcherMicroAgent")

class PairWatcherMicroAgent(MicroAgent):
    """
    A specialized micro-agent that monitors a specific token pair on specific DEXes
    
    This agent continuously checks the price of a token pair on multiple DEXes
    and publishes discoveries when it finds price differences that could be
    exploited for arbitrage.
    """
    
    def __init__(
        self,
        agent_id: str,
        parameters: Dict[str, Any],
        redis_url: str = "redis://localhost:6379/0",
        web3_provider: str = "http://localhost:8545"
    ):
        """
        Initialize a new pair watcher micro-agent
        
        Args:
            agent_id: Unique identifier for this agent
            parameters: Configuration parameters for this agent
            redis_url: URL for Redis connection
            web3_provider: URL for Web3 provider
        """
        super().__init__(agent_id, "pair_watcher", parameters, redis_url)
        
        # Validate required parameters
        required_params = ["token_pair", "exchanges", "min_price_difference_percent", "check_interval_seconds"]
        for param in required_params:
            if param not in parameters:
                raise ValueError(f"Missing required parameter: {param}")
        
        # Initialize Web3 connection
        self.web3_provider = web3_provider
        self._init_web3()
        
        # Initialize DEX connectors
        self._init_dex_connectors()
        
        # Last prices by exchange
        self.last_prices = {}
        
        self.logger.info(f"Initialized pair watcher for {parameters['token_pair'][0]}/{parameters['token_pair'][1]} on {parameters['exchanges']}")
    
    def _init_web3(self):
        """Initialize Web3 connection"""
        try:
            self.web3 = Web3(Web3.HTTPProvider(self.web3_provider))
            
            if not self.web3.is_connected():
                raise ConnectionError("Failed to connect to Web3 provider")
                
            self.logger.info(f"Connected to Web3 provider: {self.web3.client_version}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Web3: {e}")
            self.status = MicroAgentStatus.ERROR
            raise ConnectionError(f"Failed to initialize Web3: {e}")
    
    def _init_dex_connectors(self):
        """Initialize DEX connectors for each exchange"""
        self.dex_connectors = {}
        
        for exchange in self.parameters["exchanges"]:
            # In a real implementation, this would create actual connectors
            # to the specified DEXes. For this example, we'll use a mock.
            self.dex_connectors[exchange] = MockDEXConnector(
                exchange,
                self.parameters["token_pair"],
                self.web3
            )
            
            self.logger.info(f"Initialized connector for {exchange}")
    
    def execute_cycle(self):
        """Execute a single cycle of price checking"""
        token_pair = self.parameters["token_pair"]
        min_diff_percent = self.parameters["min_price_difference_percent"]
        
        # Get current prices from all exchanges
        current_prices = {}
        for exchange, connector in self.dex_connectors.items():
            try:
                price = connector.get_current_price()
                current_prices[exchange] = price
                self.logger.debug(f"Price on {exchange}: {price}")
            except Exception as e:
                self.logger.error(f"Error getting price from {exchange}: {e}")
                self.performance_metrics["errors"] += 1
        
        # Update last prices
        self.last_prices = current_prices
        
        # Check for arbitrage opportunities
        if len(current_prices) >= 2:
            opportunities = self._find_arbitrage_opportunities(current_prices, min_diff_percent)
            
            # Publish discoveries
            for opportunity in opportunities:
                self.publish_discovery(opportunity)
    
    def _find_arbitrage_opportunities(
        self,
        prices: Dict[str, float],
        min_diff_percent: float
    ) -> List[Dict[str, Any]]:
        """
        Find arbitrage opportunities between exchanges
        
        Args:
            prices: Dictionary of prices by exchange
            min_diff_percent: Minimum price difference percentage to consider
            
        Returns:
            List of arbitrage opportunities
        """
        opportunities = []
        
        # Compare each pair of exchanges
        exchanges = list(prices.keys())
        for i in range(len(exchanges)):
            for j in range(i + 1, len(exchanges)):
                exchange1 = exchanges[i]
                exchange2 = exchanges[j]
                
                price1 = prices[exchange1]
                price2 = prices[exchange2]
                
                # Calculate price difference percentage
                if price1 > 0 and price2 > 0:
                    diff_percent = abs(price1 - price2) / min(price1, price2) * 100
                    
                    if diff_percent >= min_diff_percent:
                        # Determine buy and sell exchanges
                        buy_exchange = exchange2 if price1 > price2 else exchange1
                        sell_exchange = exchange1 if price1 > price2 else exchange2
                        buy_price = min(price1, price2)
                        sell_price = max(price1, price2)
                        
                        # Calculate potential profit
                        token_pair = self.parameters["token_pair"]
                        base_token = token_pair[0]
                        quote_token = token_pair[1]
                        
                        # Create opportunity object
                        opportunity = {
                            "type": "price_difference",
                            "token_pair": token_pair,
                            "buy_exchange": buy_exchange,
                            "sell_exchange": sell_exchange,
                            "buy_price": buy_price,
                            "sell_price": sell_price,
                            "price_difference_percent": diff_percent,
                            "timestamp": time.time()
                        }
                        
                        opportunities.append(opportunity)
                        
                        self.logger.info(
                            f"Found arbitrage opportunity: "
                            f"Buy {base_token} on {buy_exchange} at {buy_price}, "
                            f"Sell on {sell_exchange} at {sell_price}, "
                            f"Difference: {diff_percent:.2f}%"
                        )
        
        return opportunities
    
    def get_cycle_interval(self) -> float:
        """Get the interval between price checks"""
        return self.parameters.get("check_interval_seconds", 5)
    
    def handle_command(self, action: str, command: Dict[str, Any]):
        """Handle pair watcher specific commands"""
        if action == "update_exchanges":
            if "exchanges" in command:
                self.parameters["exchanges"] = command["exchanges"]
                self._init_dex_connectors()
                self.logger.info(f"Updated exchanges: {command['exchanges']}")
        elif action == "update_min_difference":
            if "min_price_difference_percent" in command:
                self.parameters["min_price_difference_percent"] = command["min_price_difference_percent"]
                self.logger.info(f"Updated min difference: {command['min_price_difference_percent']}%")
        elif action == "get_last_prices":
            # Publish last prices to the response channel
            response_channel = command.get("response_channel")
            if response_channel:
                response = {
                    "agent_id": self.agent_id,
                    "last_prices": self.last_prices,
                    "timestamp": time.time()
                }
                self.redis_client.publish(response_channel, json.dumps(response))
                self.performance_metrics["messages_sent"] += 1


class MockDEXConnector:
    """
    Mock DEX connector for demonstration purposes
    
    In a real implementation, this would be replaced with actual
    connectors to DEXes using their APIs or smart contracts.
    """
    
    def __init__(self, exchange_name: str, token_pair: List[str], web3: Web3):
        """
        Initialize a new mock DEX connector
        
        Args:
            exchange_name: Name of the exchange
            token_pair: Token pair to monitor
            web3: Web3 instance
        """
        self.exchange_name = exchange_name
        self.token_pair = token_pair
        self.web3 = web3
        
        # Base price for the token pair
        self.base_price = self._get_initial_price()
        
        # Last update time
        self.last_update = time.time()
    
    def _get_initial_price(self) -> float:
        """Get initial price for the token pair"""
        # In a real implementation, this would fetch the actual price
        # from the DEX. For this mock, we'll use different base prices
        # for different exchanges to simulate arbitrage opportunities.
        if self.token_pair[0] == "ETH" and self.token_pair[1] == "USDC":
            # ETH/USDC pair
            if self.exchange_name == "uniswap_v3":
                return 3500.0
            elif self.exchange_name == "sushiswap":
                return 3490.0
            else:
                return 3495.0
        else:
            # Other pairs
            return 100.0
    
    def get_current_price(self) -> float:
        """
        Get current price for the token pair
        
        Returns:
            Current price
        """
        # In a real implementation, this would fetch the actual price
        # from the DEX. For this mock, we'll simulate price movements.
        
        # Time since last update
        now = time.time()
        time_diff = now - self.last_update
        self.last_update = now
        
        # Simulate price movement
        # More volatile for demonstration purposes
        volatility = 0.002  # 0.2% per second
        price_change = self.base_price * volatility * time_diff
        
        # Random direction
        if random.random() > 0.5:
            price_change = -price_change
        
        # Update base price
        self.base_price += price_change
        
        # Add some noise specific to this exchange
        exchange_noise = random.uniform(-0.001, 0.001) * self.base_price
        
        return self.base_price + exchange_noise