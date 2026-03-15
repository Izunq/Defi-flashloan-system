#!/usr/bin/env python3
# =================================================================================================
# PYTHON-MATLAB BRIDGE MODULE
# =================================================================================================

import os
import json
import logging
import asyncio
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from datetime import datetime

# Import MATLAB Engine
try:
    import matlab.engine
    MATLAB_AVAILABLE = True
except ImportError:
    MATLAB_AVAILABLE = False
    logging.warning("MATLAB Engine for Python not available. Install with: pip install matlabengine")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("matlab_bridge.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("matlab_bridge")

@dataclass
class ArbitrageOpportunity:
    """Arbitrage opportunity data"""
    token_pair: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    price_difference: float
    price_difference_percent: float
    optimal_size: float
    expected_profit: float
    gas_cost: float
    execution_time: float
    slippage: float
    risk_metrics: Dict[str, float]


class MATLABArbitrageEngine:
    """
    Python-MATLAB bridge for arbitrage optimization
    """
    
    def __init__(self, models_path: str = None):
        """
        Initialize MATLAB Arbitrage Engine
        
        Args:
            models_path: Path to MATLAB models
        """
        if not MATLAB_AVAILABLE:
            raise ImportError("MATLAB Engine for Python is not available. Install with: pip install matlabengine")
        
        self.models_path = models_path or os.path.join(os.path.dirname(os.path.abspath(__file__)), "arbitrage_models")
        self.matlab_engine = None
        
        # Initialize MATLAB Engine
        self._init_matlab()
        
        logger.info("MATLAB Arbitrage Engine initialized")
    
    def _init_matlab(self):
        """Initialize MATLAB Engine"""
        try:
            # Start MATLAB Engine
            self.matlab_engine = matlab.engine.start_matlab()
            
            # Add models path to MATLAB path
            self.matlab_engine.addpath(self.models_path)
            
            # Initialize ArbitrageOptimizer
            self.matlab_engine.eval("optimizer = ArbitrageOptimizer();", nargout=0)
            
            logger.info("MATLAB Engine started and ArbitrageOptimizer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize MATLAB Engine: {e}")
            raise
    
    def _convert_to_matlab(self, market_data: List[Dict]) -> matlab.engine.MatlabEngine:
        """
        Convert Python market data to MATLAB format
        
        Args:
            market_data: Market data as list of dictionaries
            
        Returns:
            MATLAB struct array
        """
        # Create MATLAB struct array
        matlab_data = self.matlab_engine.eval("struct('exchange', {}, 'token_pair', {}, 'price', {}, 'volume_24h', {}, 'liquidity', {})")
        
        # Fill struct array
        for i, record in enumerate(market_data):
            # Add fields to struct
            self.matlab_engine.setfield(matlab_data, "exchange", record.get("exchange"), i+1)
            self.matlab_engine.setfield(matlab_data, "token_pair", record.get("token_pair"), i+1)
            self.matlab_engine.setfield(matlab_data, "price", float(record.get("price", 0)), i+1)
            self.matlab_engine.setfield(matlab_data, "volume_24h", float(record.get("volume_24h", 0)), i+1)
            self.matlab_engine.setfield(matlab_data, "liquidity", float(record.get("liquidity", 0)), i+1)
        
        return matlab_data
    
    def _convert_from_matlab(self, matlab_opportunities) -> List[ArbitrageOpportunity]:
        """
        Convert MATLAB opportunities to Python format
        
        Args:
            matlab_opportunities: MATLAB struct array of opportunities
            
        Returns:
            List of ArbitrageOpportunity objects
        """
        # Initialize results
        opportunities = []
        
        # Get number of opportunities
        num_opportunities = self.matlab_engine.eval("length(opportunities)")
        
        # Convert each opportunity
        for i in range(1, num_opportunities + 1):
            # Get fields from MATLAB struct
            token_pair = self.matlab_engine.getfield(matlab_opportunities, "tokenPair", i)
            buy_exchange = self.matlab_engine.getfield(matlab_opportunities, "buyExchange", i)
            sell_exchange = self.matlab_engine.getfield(matlab_opportunities, "sellExchange", i)
            buy_price = float(self.matlab_engine.getfield(matlab_opportunities, "buyPrice", i))
            sell_price = float(self.matlab_engine.getfield(matlab_opportunities, "sellPrice", i))
            price_difference = float(self.matlab_engine.getfield(matlab_opportunities, "priceDiff", i))
            price_difference_percent = float(self.matlab_engine.getfield(matlab_opportunities, "priceDiffPercent", i))
            optimal_size = float(self.matlab_engine.getfield(matlab_opportunities, "buyAmount", i))
            expected_profit = float(self.matlab_engine.getfield(matlab_opportunities, "expectedProfit", i))
            gas_cost = float(self.matlab_engine.getfield(matlab_opportunities, "gasCost", i))
            execution_time = float(self.matlab_engine.getfield(matlab_opportunities, "executionTime", i))
            slippage = float(self.matlab_engine.getfield(matlab_opportunities, "slippage", i))
            
            # Get risk metrics
            risk_metrics = {}
            
            # Create ArbitrageOpportunity object
            opportunity = ArbitrageOpportunity(
                token_pair=token_pair,
                buy_exchange=buy_exchange,
                sell_exchange=sell_exchange,
                buy_price=buy_price,
                sell_price=sell_price,
                price_difference=price_difference,
                price_difference_percent=price_difference_percent,
                optimal_size=optimal_size,
                expected_profit=expected_profit,
                gas_cost=gas_cost,
                execution_time=execution_time,
                slippage=slippage,
                risk_metrics=risk_metrics
            )
            
            opportunities.append(opportunity)
        
        return opportunities
    
    async def optimize_portfolio(self, market_data: List[Dict], constraints: Optional[Dict] = None) -> List[ArbitrageOpportunity]:
        """
        Optimize arbitrage portfolio
        
        Args:
            market_data: Market data as list of dictionaries
            constraints: Optimization constraints
            
        Returns:
            List of arbitrage opportunities
        """
        # Default constraints
        if constraints is None:
            constraints = {
                "maxCapital": 10000,  # Maximum capital to deploy
                "maxGas": 500,        # Maximum gas in USD
                "maxSlippage": 0.01,  # Maximum slippage (1%)
                "minProfit": 50,      # Minimum profit in USD
                "maxPositions": 3     # Maximum number of positions
            }
        
        # Convert market data to MATLAB format
        matlab_data = self._convert_to_matlab(market_data)
        
        # Load market data into optimizer
        self.matlab_engine.eval("optimizer.loadMarketData(matlab_data);", nargout=0)
        
        # Create constraints struct
        matlab_constraints = self.matlab_engine.eval("struct()")
        for key, value in constraints.items():
            self.matlab_engine.setfield(matlab_constraints, key, float(value))
        
        # Run optimization
        self.matlab_engine.eval("[optimalTrades, expectedProfit, riskMetrics] = optimizer.optimizeArbitrage(matlab_constraints);", nargout=0)
        
        # Get arbitrage opportunities
        self.matlab_engine.eval("opportunities = optimizer.findArbitrageOpportunities();", nargout=0)
        
        # Convert opportunities to Python format
        opportunities = self._convert_from_matlab(self.matlab_engine.eval("opportunities"))
        
        logger.info(f"Optimized portfolio with {len(opportunities)} arbitrage opportunities")
        
        return opportunities
    
    async def calculate_var(self, market_data: List[Dict], confidence_level: float = 0.95) -> Tuple[float, float]:
        """
        Calculate Value at Risk (VaR) for current market data
        
        Args:
            market_data: Market data as list of dictionaries
            confidence_level: Confidence level (e.g., 0.95 for 95%)
            
        Returns:
            Tuple of (VaR, CVaR)
        """
        # Convert market data to MATLAB format
        matlab_data = self._convert_to_matlab(market_data)
        
        # Load market data into optimizer
        self.matlab_engine.eval("optimizer.loadMarketData(matlab_data);", nargout=0)
        
        # Calculate VaR
        self.matlab_engine.eval(f"[var, cvar] = optimizer.calculateVaR({confidence_level});", nargout=0)
        
        # Get results
        var = float(self.matlab_engine.eval("var"))
        cvar = float(self.matlab_engine.eval("cvar"))
        
        logger.info(f"Calculated VaR ({confidence_level*100}%): ${var:.2f}, CVaR: ${cvar:.2f}")
        
        return var, cvar
    
    async def run_monte_carlo(self, market_data: List[Dict], num_simulations: int = 1000) -> Dict:
        """
        Run Monte Carlo simulation for arbitrage strategies
        
        Args:
            market_data: Market data as list of dictionaries
            num_simulations: Number of simulations to run
            
        Returns:
            Dictionary with simulation results
        """
        # Convert market data to MATLAB format
        matlab_data = self._convert_to_matlab(market_data)
        
        # Load market data into optimizer
        self.matlab_engine.eval("optimizer.loadMarketData(matlab_data);", nargout=0)
        
        # Run Monte Carlo simulation
        self.matlab_engine.eval(f"results = optimizer.runMonteCarloSimulation({num_simulations});", nargout=0)
        
        # Get results
        mean_profit = float(self.matlab_engine.eval("results.meanProfit"))
        median_profit = float(self.matlab_engine.eval("results.medianProfit"))
        std_profit = float(self.matlab_engine.eval("results.stdProfit"))
        min_profit = float(self.matlab_engine.eval("results.minProfit"))
        max_profit = float(self.matlab_engine.eval("results.maxProfit"))
        profit_probability = float(self.matlab_engine.eval("results.profitProbability"))
        var95 = float(self.matlab_engine.eval("results.var95"))
        cvar95 = float(self.matlab_engine.eval("results.cvar95"))
        
        # Create results dictionary
        results = {
            "mean_profit": mean_profit,
            "median_profit": median_profit,
            "std_profit": std_profit,
            "min_profit": min_profit,
            "max_profit": max_profit,
            "profit_probability": profit_probability,
            "var95": var95,
            "cvar95": cvar95,
            "num_simulations": num_simulations
        }
        
        logger.info(f"Completed Monte Carlo simulation with {num_simulations} iterations")
        
        return results
    
    def close(self):
        """Close MATLAB Engine"""
        if self.matlab_engine:
            self.matlab_engine.quit()
            logger.info("MATLAB Engine closed")


# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize MATLAB Arbitrage Engine
        engine = MATLABArbitrageEngine()
        
        # Sample market data
        market_data = [
            {
                "exchange": "binance",
                "token_pair": "BTC-USDT",
                "price": 50000,
                "volume_24h": 1000000000,
                "liquidity": 500000000
            },
            {
                "exchange": "coinbase",
                "token_pair": "BTC-USDT",
                "price": 50100,
                "volume_24h": 800000000,
                "liquidity": 400000000
            },
            {
                "exchange": "kraken",
                "token_pair": "BTC-USDT",
                "price": 49950,
                "volume_24h": 600000000,
                "liquidity": 300000000
            }
        ]
        
        # Optimize portfolio
        opportunities = await engine.optimize_portfolio(market_data)
        
        # Print opportunities
        for opp in opportunities:
            print(f"Opportunity: {opp.token_pair}")
            print(f"  Buy from {opp.buy_exchange} at ${opp.buy_price:.2f}")
            print(f"  Sell on {opp.sell_exchange} at ${opp.sell_price:.2f}")
            print(f"  Price difference: ${opp.price_difference:.2f} ({opp.price_difference_percent:.2f}%)")
            print(f"  Optimal size: {opp.optimal_size:.4f}")
            print(f"  Expected profit: ${opp.expected_profit:.2f}")
            print(f"  Gas cost: ${opp.gas_cost:.2f}")
            print(f"  Execution time: {opp.execution_time:.2f} seconds")
            print(f"  Slippage: {opp.slippage*100:.2f}%")
            print()
        
        # Calculate VaR
        var, cvar = await engine.calculate_var(market_data)
        print(f"VaR (95%): ${var:.2f}")
        print(f"CVaR (95%): ${cvar:.2f}")
        
        # Run Monte Carlo simulation
        results = await engine.run_monte_carlo(market_data, 100)
        print(f"Monte Carlo Results:")
        print(f"  Mean profit: ${results['mean_profit']:.2f}")
        print(f"  Median profit: ${results['median_profit']:.2f}")
        print(f"  Profit probability: {results['profit_probability']*100:.2f}%")
        
        # Close MATLAB Engine
        engine.close()
    
    # Run main function
    asyncio.run(main())