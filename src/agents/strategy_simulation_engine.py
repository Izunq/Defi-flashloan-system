"""
Strategy Simulation Engine for Flashloan Arbitrage System
This module provides advanced simulation capabilities for testing and optimizing trading strategies.
"""

import os
import json
import time
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StrategySimulationEngine:
    """Advanced simulation engine for testing and optimizing trading strategies"""
    
    def __init__(self, config_path: str = None):
        """Initialize the Strategy Simulation Engine
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.market_data = {}
        self.simulation_results = {}
        self.optimization_results = {}
        
        # Load market data
        self._load_market_data()
        
        logger.info(f"Strategy Simulation Engine initialized")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from file
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        default_config = {
            "simulation": {
                "default_timeframe": "1h",
                "default_period": "30d",
                "default_capital": 100000,
                "default_fee": 0.003,
                "default_slippage": 0.001,
                "default_gas_price_gwei": 50,
                "max_concurrent_simulations": 8
            },
            "optimization": {
                "parameter_ranges": {
                    "slippage_tolerance": [0.0005, 0.005, 10],
                    "min_profit_threshold": [10, 100, 10],
                    "position_size_percent": [5, 50, 10],
                    "max_gas_price_gwei": [20, 200, 10]
                },
                "optimization_method": "grid_search",  # grid_search, random_search, bayesian
                "optimization_metric": "sharpe_ratio",  # total_profit, sharpe_ratio, sortino_ratio, profit_factor
                "num_iterations": 100
            },
            "market_data": {
                "sources": [
                    {
                        "name": "historical_data",
                        "type": "csv",
                        "path": "./data/historical_prices.csv"
                    },
                    {
                        "name": "dex_liquidity",
                        "type": "json",
                        "path": "./data/dex_liquidity.json"
                    }
                ],
                "default_source": "historical_data"
            },
            "strategies": {
                "default_strategy": "flash_arbitrage_v2",
                "available_strategies": [
                    "flash_arbitrage_v2",
                    "cross_chain_arbitrage",
                    "stable_swap_optimizer"
                ]
            },
            "reporting": {
                "output_dir": "./simulation_results",
                "generate_charts": True,
                "save_results": True
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    # Merge user config with default config
                    for key, value in user_config.items():
                        if key in default_config and isinstance(default_config[key], dict):
                            default_config[key].update(value)
                        else:
                            default_config[key] = value
                logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
        
        return default_config
    
    def _load_market_data(self):
        """Load market data from configured sources"""
        try:
            for source in self.config["market_data"]["sources"]:
                source_name = source["name"]
                source_type = source["type"]
                source_path = source["path"]
                
                if not os.path.exists(source_path):
                    logger.warning(f"Market data source {source_path} not found. Using synthetic data.")
                    self.market_data[source_name] = self._generate_synthetic_data(source_name)
                    continue
                
                logger.info(f"Loading market data from {source_path}")
                
                if source_type == "csv":
                    self.market_data[source_name] = pd.read_csv(source_path)
                elif source_type == "json":
                    with open(source_path, 'r') as f:
                        self.market_data[source_name] = json.load(f)
                else:
                    logger.warning(f"Unsupported market data source type: {source_type}")
            
            logger.info(f"Loaded {len(self.market_data)} market data sources")
        except Exception as e:
            logger.error(f"Error loading market data: {e}")
            logger.info("Generating synthetic market data")
            self._generate_all_synthetic_data()
    
    def _generate_all_synthetic_data(self):
        """Generate synthetic data for all required sources"""
        self.market_data["historical_data"] = self._generate_synthetic_price_data()
        self.market_data["dex_liquidity"] = self._generate_synthetic_liquidity_data()
        self.market_data["gas_prices"] = self._generate_synthetic_gas_data()
        self.market_data["exchange_volumes"] = self._generate_synthetic_volume_data()
    
    def _generate_synthetic_data(self, data_type: str) -> Union[pd.DataFrame, Dict]:
        """Generate synthetic data based on data type
        
        Args:
            data_type: Type of data to generate
            
        Returns:
            Synthetic data
        """
        if data_type == "historical_data":
            return self._generate_synthetic_price_data()
        elif data_type == "dex_liquidity":
            return self._generate_synthetic_liquidity_data()
        elif data_type == "gas_prices":
            return self._generate_synthetic_gas_data()
        elif data_type == "exchange_volumes":
            return self._generate_synthetic_volume_data()
        else:
            logger.warning(f"Unknown data type: {data_type}")
            return {}
    
    def _generate_synthetic_price_data(self) -> pd.DataFrame:
        """Generate synthetic price data
        
        Returns:
            DataFrame with synthetic price data
        """
        # Generate dates for the last 30 days with hourly data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        dates = pd.date_range(start=start_date, end=end_date, freq='1H')
        
        # Generate price data for multiple tokens
        tokens = ['ETH', 'BTC', 'USDC', 'DAI', 'USDT', 'WBTC', 'LINK', 'UNI', 'AAVE', 'COMP']
        
        # Base prices
        base_prices = {
            'ETH': 3000,
            'BTC': 50000,
            'USDC': 1,
            'DAI': 1,
            'USDT': 1,
            'WBTC': 50000,
            'LINK': 20,
            'UNI': 10,
            'AAVE': 200,
            'COMP': 150
        }
        
        # Volatility factors
        volatility = {
            'ETH': 0.03,
            'BTC': 0.025,
            'USDC': 0.0005,
            'DAI': 0.001,
            'USDT': 0.0005,
            'WBTC': 0.025,
            'LINK': 0.04,
            'UNI': 0.05,
            'AAVE': 0.045,
            'COMP': 0.05
        }
        
        # Create DataFrame
        df = pd.DataFrame(index=dates)
        df['timestamp'] = df.index
        
        # Generate price data for each token
        for token in tokens:
            # Generate random walk
            np.random.seed(hash(token) % 10000)  # Different seed for each token
            random_walk = np.random.normal(0, volatility[token], size=len(dates))
            random_walk = np.cumsum(random_walk)
            
            # Add trend
            trend = np.linspace(0, 0.2, len(dates))  # Slight upward trend
            
            # Calculate prices
            prices = base_prices[token] * np.exp(random_walk + trend)
            
            # Add to DataFrame
            df[f'{token}_price'] = prices
            
            # Add volume
            daily_volume_factor = np.random.uniform(0.5, 1.5, size=len(dates))
            intraday_pattern = 1 + 0.5 * np.sin(np.pi * df.index.hour / 12)  # Higher volume during day
            volume = base_prices[token] * 1000000 * daily_volume_factor * intraday_pattern
            df[f'{token}_volume'] = volume
        
        return df
    
    def _generate_synthetic_liquidity_data(self) -> Dict:
        """Generate synthetic liquidity data
        
        Returns:
            Dictionary with synthetic liquidity data
        """
        # Define exchanges
        exchanges = ['Uniswap', 'Sushiswap', 'Curve', 'Balancer', 'Quickswap']
        
        # Define token pairs
        token_pairs = [
            'ETH-USDC', 'ETH-DAI', 'ETH-USDT', 'BTC-USDC', 'BTC-ETH',
            'LINK-ETH', 'UNI-ETH', 'AAVE-ETH', 'COMP-ETH', 'DAI-USDC'
        ]
        
        # Generate liquidity data
        liquidity_data = {}
        
        for exchange in exchanges:
            liquidity_data[exchange] = {}
            
            for pair in token_pairs:
                # Base liquidity varies by exchange and pair
                base_liquidity = np.random.uniform(1000000, 50000000)
                
                # Adjust based on exchange
                if exchange == 'Uniswap':
                    base_liquidity *= 1.5  # Uniswap has more liquidity
                elif exchange == 'Curve' and ('DAI' in pair or 'USDC' in pair or 'USDT' in pair):
                    base_liquidity *= 2.0  # Curve has more stablecoin liquidity
                
                # Generate hourly liquidity for 30 days
                hours = 30 * 24
                hourly_liquidity = []
                
                for hour in range(hours):
                    # Add some randomness to liquidity
                    random_factor = np.random.uniform(0.95, 1.05)
                    # Add time-based pattern (liquidity grows over time)
                    time_factor = 1 + (hour / hours) * 0.1
                    
                    liquidity = base_liquidity * random_factor * time_factor
                    
                    hourly_liquidity.append({
                        'timestamp': (datetime.now() - timedelta(hours=hours-hour)).isoformat(),
                        'liquidity': liquidity,
                        'volume_24h': liquidity * np.random.uniform(0.05, 0.2)
                    })
                
                liquidity_data[exchange][pair] = hourly_liquidity
        
        return liquidity_data
    
    def _generate_synthetic_gas_data(self) -> pd.DataFrame:
        """Generate synthetic gas price data
        
        Returns:
            DataFrame with synthetic gas price data
        """
        # Generate dates for the last 30 days with hourly data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        dates = pd.date_range(start=start_date, end=end_date, freq='1H')
        
        # Create DataFrame
        df = pd.DataFrame(index=dates)
        df['timestamp'] = df.index
        
        # Base gas price
        base_gas_price = 50  # Gwei
        
        # Generate gas price with daily and weekly patterns
        hour_of_day = df.index.hour
        day_of_week = df.index.dayofweek
        
        # Hourly pattern: higher during business hours
        hourly_factor = 1 + 0.3 * np.sin(np.pi * (hour_of_day - 10) / 12)
        
        # Daily pattern: higher on weekdays
        daily_factor = 1 + 0.2 * (day_of_week < 5)
        
        # Random component
        np.random.seed(42)
        random_walk = np.random.normal(0, 0.1, size=len(dates))
        random_walk = np.cumsum(random_walk)
        random_factor = np.exp(random_walk)
        
        # Calculate gas prices
        gas_prices = base_gas_price * hourly_factor * daily_factor * random_factor
        
        # Add occasional gas price spikes
        spike_indices = np.random.choice(len(dates), size=10, replace=False)
        spike_multiplier = np.random.uniform(2, 5, size=10)
        
        for i, idx in enumerate(spike_indices):
            gas_prices[idx] *= spike_multiplier[i]
        
        # Smooth the spikes
        gas_prices = pd.Series(gas_prices).rolling(window=3, center=True).mean().fillna(method='bfill').fillna(method='ffill').values
        
        # Add to DataFrame
        df['gas_price_gwei'] = gas_prices
        df['gas_price_fast_gwei'] = gas_prices * 1.2
        df['gas_price_slow_gwei'] = gas_prices * 0.8
        
        return df
    
    def _generate_synthetic_volume_data(self) -> Dict:
        """Generate synthetic exchange volume data
        
        Returns:
            Dictionary with synthetic exchange volume data
        """
        # Define exchanges
        exchanges = ['Uniswap', 'Sushiswap', 'Curve', 'Balancer', 'Quickswap']
        
        # Generate volume data
        volume_data = {}
        
        for exchange in exchanges:
            # Base daily volume varies by exchange
            if exchange == 'Uniswap':
                base_volume = 500000000  # $500M
            elif exchange == 'Curve':
                base_volume = 300000000  # $300M
            elif exchange == 'Sushiswap':
                base_volume = 200000000  # $200M
            else:
                base_volume = 100000000  # $100M
            
            # Generate daily volumes for 30 days
            daily_volumes = []
            
            for day in range(30):
                # Add some randomness to volume
                random_factor = np.random.uniform(0.8, 1.2)
                # Add day-of-week pattern (higher on weekdays)
                day_of_week = (datetime.now() - timedelta(days=30-day)).weekday()
                weekday_factor = 1.1 if day_of_week < 5 else 0.9
                
                volume = base_volume * random_factor * weekday_factor
                
                daily_volumes.append({
                    'date': (datetime.now() - timedelta(days=30-day)).strftime('%Y-%m-%d'),
                    'volume_usd': volume,
                    'transactions': int(volume / 10000)  # Approximate number of transactions
                })
            
            volume_data[exchange] = daily_volumes
        
        return volume_data
    
    def simulate_strategy(self, strategy_config: Dict) -> Dict:
        """Simulate a trading strategy with the given configuration
        
        Args:
            strategy_config: Strategy configuration
            
        Returns:
            Simulation results
        """
        try:
            logger.info(f"Starting simulation for strategy: {strategy_config.get('name', 'unnamed')}")
            
            # Merge with default config
            config = self._merge_with_default_config(strategy_config)
            
            # Get strategy implementation
            strategy_type = config.get('type', self.config['strategies']['default_strategy'])
            strategy_func = self._get_strategy_function(strategy_type)
            
            # Get market data
            market_data_source = config.get('market_data_source', self.config['market_data']['default_source'])
            market_data = self.market_data.get(market_data_source)
            
            if market_data is None:
                logger.warning(f"Market data source {market_data_source} not found. Using synthetic data.")
                market_data = self._generate_synthetic_data(market_data_source)
            
            # Run simulation
            start_time = time.time()
            simulation_id = f"sim_{int(start_time)}_{strategy_type}"
            
            results = strategy_func(config, market_data)
            
            # Calculate performance metrics
            metrics = self._calculate_performance_metrics(results)
            
            # Combine results
            simulation_results = {
                'id': simulation_id,
                'strategy_type': strategy_type,
                'config': config,
                'results': results,
                'metrics': metrics,
                'execution_time': time.time() - start_time
            }
            
            # Store results
            self.simulation_results[simulation_id] = simulation_results
            
            # Generate report if configured
            if self.config['reporting']['generate_charts']:
                self._generate_simulation_charts(simulation_results)
            
            # Save results if configured
            if self.config['reporting']['save_results']:
                self._save_simulation_results(simulation_results)
            
            logger.info(f"Simulation completed: {simulation_id}")
            logger.info(f"Total profit: ${metrics['total_profit']:.2f}, Sharpe ratio: {metrics['sharpe_ratio']:.2f}")
            
            return simulation_results
        except Exception as e:
            logger.error(f"Error in simulation: {e}")
            return {
                'error': str(e),
                'status': 'failed'
            }
    
    def _merge_with_default_config(self, strategy_config: Dict) -> Dict:
        """Merge strategy config with default config
        
        Args:
            strategy_config: Strategy configuration
            
        Returns:
            Merged configuration
        """
        default_sim_config = {
            'timeframe': self.config['simulation']['default_timeframe'],
            'period': self.config['simulation']['default_period'],
            'capital': self.config['simulation']['default_capital'],
            'fee': self.config['simulation']['default_fee'],
            'slippage': self.config['simulation']['default_slippage'],
            'gas_price_gwei': self.config['simulation']['default_gas_price_gwei']
        }
        
        # Merge configs
        merged_config = {**default_sim_config, **strategy_config}
        
        return merged_config
    
    def _get_strategy_function(self, strategy_type: str):
        """Get the strategy implementation function
        
        Args:
            strategy_type: Type of strategy
            
        Returns:
            Strategy function
        """
        strategy_map = {
            'flash_arbitrage_v2': self._simulate_flash_arbitrage,
            'cross_chain_arbitrage': self._simulate_cross_chain_arbitrage,
            'stable_swap_optimizer': self._simulate_stable_swap_optimizer
        }
        
        if strategy_type not in strategy_map:
            logger.warning(f"Strategy type {strategy_type} not found. Using default strategy.")
            strategy_type = self.config['strategies']['default_strategy']
        
        return strategy_map[strategy_type]
    
    def _simulate_flash_arbitrage(self, config: Dict, market_data: pd.DataFrame) -> Dict:
        """Simulate flash arbitrage strategy
        
        Args:
            config: Strategy configuration
            market_data: Market data
            
        Returns:
            Simulation results
        """
        logger.info("Simulating Flash Arbitrage strategy")
        
        # Extract configuration
        capital = config['capital']
        fee = config['fee']
        slippage = config['slippage']
        gas_price_gwei = config['gas_price_gwei']
        
        # Initialize results
        trades = []
        capital_history = []
        current_capital = capital
        
        # Get token pairs to monitor
        token_pairs = [
            ('ETH', 'USDC'),
            ('ETH', 'DAI'),
            ('BTC', 'USDC'),
            ('ETH', 'BTC')
        ]
        
        # Simulate for each timestamp
        for idx, row in market_data.iterrows():
            timestamp = row['timestamp']
            
            # Check for arbitrage opportunities
            for base_token, quote_token in token_pairs:
                # Get prices from different exchanges (simulated as price +/- random factor)
                base_price = row[f'{base_token}_price']
                quote_price = row[f'{quote_token}_price']
                
                # Simulate price differences between exchanges
                uniswap_price = base_price / quote_price * (1 + np.random.uniform(-0.01, 0.01))
                sushiswap_price = base_price / quote_price * (1 + np.random.uniform(-0.01, 0.01))
                
                # Calculate price difference
                price_diff_pct = abs(uniswap_price - sushiswap_price) / min(uniswap_price, sushiswap_price)
                
                # Check if arbitrage is profitable
                gas_cost_usd = gas_price_gwei * 1e-9 * 21000 * base_price  # Approximate gas cost
                fee_cost = current_capital * fee * 2  # Fee for two trades
                slippage_cost = current_capital * slippage * 2  # Slippage for two trades
                total_cost = gas_cost_usd + fee_cost + slippage_cost
                
                potential_profit = current_capital * price_diff_pct - total_cost
                
                # Execute trade if profitable
                if potential_profit > 0:
                    # Determine direction
                    if uniswap_price < sushiswap_price:
                        buy_exchange = 'Uniswap'
                        sell_exchange = 'Sushiswap'
                        buy_price = uniswap_price
                        sell_price = sushiswap_price
                    else:
                        buy_exchange = 'Sushiswap'
                        sell_exchange = 'Uniswap'
                        buy_price = sushiswap_price
                        sell_price = uniswap_price
                    
                    # Execute trade
                    trade_amount = current_capital * 0.99  # Use 99% of capital
                    trade_profit = trade_amount * price_diff_pct - total_cost
                    
                    # Update capital
                    current_capital += trade_profit
                    
                    # Record trade
                    trades.append({
                        'timestamp': timestamp,
                        'base_token': base_token,
                        'quote_token': quote_token,
                        'buy_exchange': buy_exchange,
                        'sell_exchange': sell_exchange,
                        'buy_price': buy_price,
                        'sell_price': sell_price,
                        'amount': trade_amount,
                        'profit': trade_profit,
                        'gas_cost': gas_cost_usd,
                        'fee_cost': fee_cost,
                        'slippage_cost': slippage_cost
                    })
            
            # Record capital history
            capital_history.append({
                'timestamp': timestamp,
                'capital': current_capital
            })
        
        # Prepare results
        results = {
            'trades': trades,
            'capital_history': capital_history,
            'initial_capital': capital,
            'final_capital': current_capital,
            'total_profit': current_capital - capital,
            'total_trades': len(trades)
        }
        
        return results
    
    def _simulate_cross_chain_arbitrage(self, config: Dict, market_data: pd.DataFrame) -> Dict:
        """Simulate cross-chain arbitrage strategy
        
        Args:
            config: Strategy configuration
            market_data: Market data
            
        Returns:
            Simulation results
        """
        logger.info("Simulating Cross-Chain Arbitrage strategy")
        
        # Extract configuration
        capital = config['capital']
        fee = config['fee']
        slippage = config['slippage']
        gas_price_gwei = config['gas_price_gwei']
        bridge_fee = config.get('bridge_fee', 0.001)  # 0.1% bridge fee
        
        # Initialize results
        trades = []
        capital_history = []
        current_capital = capital
        
        # Get token pairs to monitor
        tokens = ['ETH', 'BTC', 'USDC', 'DAI']
        
        # Define chains
        chains = ['Ethereum', 'Polygon', 'Arbitrum', 'Optimism']
        
        # Simulate for each timestamp
        for idx, row in market_data.iterrows():
            timestamp = row['timestamp']
            
            # Check for arbitrage opportunities across chains
            for token in tokens:
                # Simulate prices on different chains
                token_price = row[f'{token}_price']
                chain_prices = {}
                
                for chain in chains:
                    # Add random price variation for each chain
                    chain_factor = 1 + np.random.uniform(-0.02, 0.02)
                    chain_prices[chain] = token_price * chain_factor
                
                # Find best buy and sell chains
                buy_chain = min(chain_prices.items(), key=lambda x: x[1])[0]
                sell_chain = max(chain_prices.items(), key=lambda x: x[1])[0]
                
                buy_price = chain_prices[buy_chain]
                sell_price = chain_prices[sell_chain]
                
                # Calculate price difference
                price_diff_pct = (sell_price - buy_price) / buy_price
                
                # Calculate costs
                gas_cost_eth = gas_price_gwei * 1e-9 * 100000  # Higher gas for cross-chain
                gas_cost_usd = gas_cost_eth * row['ETH_price']
                fee_cost = current_capital * fee * 2  # Fee for two trades
                slippage_cost = current_capital * slippage * 2  # Slippage for two trades
                bridge_cost = current_capital * bridge_fee  # Cost to bridge tokens
                
                total_cost = gas_cost_usd + fee_cost + slippage_cost + bridge_cost
                
                potential_profit = current_capital * price_diff_pct - total_cost
                
                # Execute trade if profitable
                if potential_profit > 0 and buy_chain != sell_chain:
                    # Execute trade
                    trade_amount = current_capital * 0.95  # Use 95% of capital (more conservative)
                    trade_profit = trade_amount * price_diff_pct - total_cost
                    
                    # Update capital
                    current_capital += trade_profit
                    
                    # Record trade
                    trades.append({
                        'timestamp': timestamp,
                        'token': token,
                        'buy_chain': buy_chain,
                        'sell_chain': sell_chain,
                        'buy_price': buy_price,
                        'sell_price': sell_price,
                        'amount': trade_amount,
                        'profit': trade_profit,
                        'gas_cost': gas_cost_usd,
                        'fee_cost': fee_cost,
                        'slippage_cost': slippage_cost,
                        'bridge_cost': bridge_cost
                    })
            
            # Record capital history
            capital_history.append({
                'timestamp': timestamp,
                'capital': current_capital
            })
        
        # Prepare results
        results = {
            'trades': trades,
            'capital_history': capital_history,
            'initial_capital': capital,
            'final_capital': current_capital,
            'total_profit': current_capital - capital,
            'total_trades': len(trades)
        }
        
        return results
    
    def _simulate_stable_swap_optimizer(self, config: Dict, market_data: pd.DataFrame) -> Dict:
        """Simulate stable swap optimizer strategy
        
        Args:
            config: Strategy configuration
            market_data: Market data
            
        Returns:
            Simulation results
        """
        logger.info("Simulating Stable Swap Optimizer strategy")
        
        # Extract configuration
        capital = config['capital']
        fee = config['fee']
        slippage = config['slippage']
        gas_price_gwei = config['gas_price_gwei']
        
        # Initialize results
        trades = []
        capital_history = []
        current_capital = capital
        
        # Get stablecoin pairs to monitor
        stablecoin_pairs = [
            ('USDC', 'DAI'),
            ('USDC', 'USDT'),
            ('DAI', 'USDT')
        ]
        
        # Define exchanges with stablecoin pools
        exchanges = ['Curve', 'Uniswap', 'Sushiswap']
        
        # Simulate for each timestamp
        for idx, row in market_data.iterrows():
            timestamp = row['timestamp']
            
            # Check for arbitrage opportunities
            for base_token, quote_token in stablecoin_pairs:
                # Get prices from different exchanges
                base_price = row[f'{base_token}_price']
                quote_price = row[f'{quote_token}_price']
                
                # Simulate exchange rates on different exchanges
                exchange_rates = {}
                
                for exchange in exchanges:
                    # Stablecoin prices are very close, so use smaller random factors
                    if exchange == 'Curve':
                        # Curve has tighter spreads for stablecoins
                        exchange_factor = 1 + np.random.uniform(-0.001, 0.001)
                    else:
                        exchange_factor = 1 + np.random.uniform(-0.003, 0.003)
                    
                    exchange_rates[exchange] = (base_price / quote_price) * exchange_factor
                
                # Find best buy and sell exchanges
                buy_exchange = min(exchange_rates.items(), key=lambda x: x[1])[0]
                sell_exchange = max(exchange_rates.items(), key=lambda x: x[1])[0]
                
                buy_rate = exchange_rates[buy_exchange]
                sell_rate = exchange_rates[sell_exchange]
                
                # Calculate rate difference
                rate_diff_pct = (sell_rate - buy_rate) / buy_rate
                
                # Calculate costs
                gas_cost_eth = gas_price_gwei * 1e-9 * 150000  # Gas for stablecoin swaps
                gas_cost_usd = gas_cost_eth * row['ETH_price']
                fee_cost = current_capital * fee * 2  # Fee for two trades
                slippage_cost = current_capital * slippage * 2  # Slippage for two trades
                
                total_cost = gas_cost_usd + fee_cost + slippage_cost
                
                potential_profit = current_capital * rate_diff_pct - total_cost
                
                # Execute trade if profitable
                if potential_profit > 0 and buy_exchange != sell_exchange:
                    # Execute trade
                    trade_amount = current_capital * 0.98  # Use 98% of capital
                    trade_profit = trade_amount * rate_diff_pct - total_cost
                    
                    # Update capital
                    current_capital += trade_profit
                    
                    # Record trade
                    trades.append({
                        'timestamp': timestamp,
                        'base_token': base_token,
                        'quote_token': quote_token,
                        'buy_exchange': buy_exchange,
                        'sell_exchange': sell_exchange,
                        'buy_rate': buy_rate,
                        'sell_rate': sell_rate,
                        'amount': trade_amount,
                        'profit': trade_profit,
                        'gas_cost': gas_cost_usd,
                        'fee_cost': fee_cost,
                        'slippage_cost': slippage_cost
                    })
            
            # Record capital history
            capital_history.append({
                'timestamp': timestamp,
                'capital': current_capital
            })
        
        # Prepare results
        results = {
            'trades': trades,
            'capital_history': capital_history,
            'initial_capital': capital,
            'final_capital': current_capital,
            'total_profit': current_capital - capital,
            'total_trades': len(trades)
        }
        
        return results
    
    def _calculate_performance_metrics(self, results: Dict) -> Dict:
        """Calculate performance metrics for simulation results
        
        Args:
            results: Simulation results
            
        Returns:
            Performance metrics
        """
        # Extract data
        trades = results['trades']
        capital_history = results['capital_history']
        initial_capital = results['initial_capital']
        final_capital = results['final_capital']
        
        # Convert to DataFrame for easier analysis
        if capital_history:
            capital_df = pd.DataFrame(capital_history)
            capital_df['timestamp'] = pd.to_datetime(capital_df['timestamp'])
            capital_df.set_index('timestamp', inplace=True)
            
            # Resample to daily for return calculation
            daily_capital = capital_df.resample('D').last().fillna(method='ffill')
            
            # Calculate daily returns
            daily_capital['daily_return'] = daily_capital['capital'].pct_change().fillna(0)
            
            # Calculate metrics
            total_days = len(daily_capital)
            profitable_days = len(daily_capital[daily_capital['daily_return'] > 0])
            
            # Annualized return
            total_return = (final_capital / initial_capital) - 1
            annualized_return = ((1 + total_return) ** (365 / total_days)) - 1 if total_days > 0 else 0
            
            # Volatility
            daily_volatility = daily_capital['daily_return'].std()
            annualized_volatility = daily_volatility * (365 ** 0.5) if not np.isnan(daily_volatility) else 0
            
            # Sharpe ratio (assuming risk-free rate of 0.02)
            risk_free_rate = 0.02
            sharpe_ratio = (annualized_return - risk_free_rate) / annualized_volatility if annualized_volatility > 0 else 0
            
            # Sortino ratio (downside deviation)
            downside_returns = daily_capital[daily_capital['daily_return'] < 0]['daily_return']
            downside_deviation = downside_returns.std() * (365 ** 0.5) if len(downside_returns) > 0 else 0
            sortino_ratio = (annualized_return - risk_free_rate) / downside_deviation if downside_deviation > 0 else 0
            
            # Maximum drawdown
            rolling_max = daily_capital['capital'].cummax()
            drawdown = (daily_capital['capital'] - rolling_max) / rolling_max
            max_drawdown = drawdown.min()
            
            # Profit factor
            gross_profit = sum([trade['profit'] for trade in trades if trade['profit'] > 0])
            gross_loss = abs(sum([trade['profit'] for trade in trades if trade['profit'] < 0]))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        else:
            # No capital history, set default values
            total_days = 0
            profitable_days = 0
            annualized_return = 0
            annualized_volatility = 0
            sharpe_ratio = 0
            sortino_ratio = 0
            max_drawdown = 0
            profit_factor = 0
        
        # Calculate trade metrics
        total_trades = len(trades)
        profitable_trades = len([t for t in trades if t['profit'] > 0])
        win_rate = profitable_trades / total_trades if total_trades > 0 else 0
        
        avg_profit_per_trade = sum([t['profit'] for t in trades]) / total_trades if total_trades > 0 else 0
        avg_profit_winning = sum([t['profit'] for t in trades if t['profit'] > 0]) / profitable_trades if profitable_trades > 0 else 0
        avg_loss_losing = sum([t['profit'] for t in trades if t['profit'] < 0]) / (total_trades - profitable_trades) if (total_trades - profitable_trades) > 0 else 0
        
        # Prepare metrics
        metrics = {
            'total_profit': final_capital - initial_capital,
            'total_return_pct': (final_capital / initial_capital - 1) * 100,
            'annualized_return_pct': annualized_return * 100,
            'annualized_volatility_pct': annualized_volatility * 100,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'max_drawdown_pct': abs(max_drawdown) * 100 if not np.isnan(max_drawdown) else 0,
            'profit_factor': profit_factor,
            'total_trades': total_trades,
            'profitable_trades': profitable_trades,
            'win_rate': win_rate,
            'total_days': total_days,
            'profitable_days': profitable_days,
            'avg_profit_per_trade': avg_profit_per_trade,
            'avg_profit_winning': avg_profit_winning,
            'avg_loss_losing': avg_loss_losing
        }
        
        return metrics
    
    def _generate_simulation_charts(self, simulation_results: Dict):
        """Generate charts for simulation results
        
        Args:
            simulation_results: Simulation results
        """
        try:
            # Create output directory if it doesn't exist
            output_dir = self.config['reporting']['output_dir']
            os.makedirs(output_dir, exist_ok=True)
            
            # Extract data
            results = simulation_results['results']
            metrics = simulation_results['metrics']
            simulation_id = simulation_results['id']
            
            # Convert to DataFrame
            capital_history = pd.DataFrame(results['capital_history'])
            capital_history['timestamp'] = pd.to_datetime(capital_history['timestamp'])
            capital_history.set_index('timestamp', inplace=True)
            
            # Create figure with subplots
            fig, axs = plt.subplots(2, 2, figsize=(16, 12))
            
            # Plot capital over time
            axs[0, 0].plot(capital_history.index, capital_history['capital'])
            axs[0, 0].set_title('Capital Over Time')
            axs[0, 0].set_xlabel('Date')
            axs[0, 0].set_ylabel('Capital ($)')
            axs[0, 0].grid(True)
            
            # Plot daily returns
            daily_capital = capital_history.resample('D').last().fillna(method='ffill')
            daily_capital['daily_return'] = daily_capital['capital'].pct_change().fillna(0)
            
            axs[0, 1].bar(daily_capital.index, daily_capital['daily_return'] * 100)
            axs[0, 1].set_title('Daily Returns (%)')
            axs[0, 1].set_xlabel('Date')
            axs[0, 1].set_ylabel('Return (%)')
            axs[0, 1].grid(True)
            
            # Plot drawdown
            rolling_max = daily_capital['capital'].cummax()
            drawdown = (daily_capital['capital'] - rolling_max) / rolling_max * 100
            
            axs[1, 0].fill_between(drawdown.index, drawdown, 0, color='red', alpha=0.3)
            axs[1, 0].set_title('Drawdown (%)')
            axs[1, 0].set_xlabel('Date')
            axs[1, 0].set_ylabel('Drawdown (%)')
            axs[1, 0].grid(True)
            
            # Plot trade profits
            if results['trades']:
                trades_df = pd.DataFrame(results['trades'])
                trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])
                trades_df.set_index('timestamp', inplace=True)
                
                axs[1, 1].bar(trades_df.index, trades_df['profit'])
                axs[1, 1].set_title('Trade Profits')
                axs[1, 1].set_xlabel('Date')
                axs[1, 1].set_ylabel('Profit ($)')
                axs[1, 1].grid(True)
            else:
                axs[1, 1].text(0.5, 0.5, 'No trades executed', horizontalalignment='center', verticalalignment='center', transform=axs[1, 1].transAxes)
                axs[1, 1].set_title('Trade Profits')
            
            # Add metrics as text
            plt.figtext(0.5, 0.01, f"Total Profit: ${metrics['total_profit']:.2f} | Return: {metrics['total_return_pct']:.2f}% | Sharpe: {metrics['sharpe_ratio']:.2f} | Win Rate: {metrics['win_rate']*100:.2f}% | Max Drawdown: {metrics['max_drawdown_pct']:.2f}%", 
                       ha='center', fontsize=12, bbox=dict(facecolor='lightgray', alpha=0.5))
            
            # Adjust layout and save
            plt.tight_layout(rect=[0, 0.03, 1, 0.95])
            plt.suptitle(f"Strategy Simulation Results - {simulation_results['strategy_type']}", fontsize=16)
            
            # Save figure
            output_path = os.path.join(output_dir, f"{simulation_id}_charts.png")
            plt.savefig(output_path)
            plt.close()
            
            logger.info(f"Saved simulation charts to {output_path}")
        except Exception as e:
            logger.error(f"Error generating simulation charts: {e}")
    
    def _save_simulation_results(self, simulation_results: Dict):
        """Save simulation results to file
        
        Args:
            simulation_results: Simulation results
        """
        try:
            # Create output directory if it doesn't exist
            output_dir = self.config['reporting']['output_dir']
            os.makedirs(output_dir, exist_ok=True)
            
            # Save results as JSON
            output_path = os.path.join(output_dir, f"{simulation_results['id']}_results.json")
            
            # Convert DataFrame-like structures to lists
            results_copy = {
                'id': simulation_results['id'],
                'strategy_type': simulation_results['strategy_type'],
                'config': simulation_results['config'],
                'results': {
                    'trades': simulation_results['results']['trades'],
                    'capital_history': simulation_results['results']['capital_history'],
                    'initial_capital': simulation_results['results']['initial_capital'],
                    'final_capital': simulation_results['results']['final_capital'],
                    'total_profit': simulation_results['results']['total_profit'],
                    'total_trades': simulation_results['results']['total_trades']
                },
                'metrics': simulation_results['metrics'],
                'execution_time': simulation_results['execution_time']
            }
            
            with open(output_path, 'w') as f:
                json.dump(results_copy, f, indent=2)
            
            logger.info(f"Saved simulation results to {output_path}")
        except Exception as e:
            logger.error(f"Error saving simulation results: {e}")
    
    def optimize_strategy(self, strategy_config: Dict) -> Dict:
        """Optimize strategy parameters
        
        Args:
            strategy_config: Base strategy configuration
            
        Returns:
            Optimization results
        """
        try:
            logger.info(f"Starting optimization for strategy: {strategy_config.get('name', 'unnamed')}")
            
            # Merge with default config
            base_config = self._merge_with_default_config(strategy_config)
            
            # Get optimization method
            optimization_method = self.config['optimization']['optimization_method']
            optimization_metric = self.config['optimization']['optimization_metric']
            
            # Get parameter ranges
            param_ranges = self.config['optimization']['parameter_ranges']
            
            # Run optimization
            start_time = time.time()
            optimization_id = f"opt_{int(start_time)}_{base_config.get('type', 'unknown')}"
            
            if optimization_method == 'grid_search':
                results = self._optimize_grid_search(base_config, param_ranges, optimization_metric)
            elif optimization_method == 'random_search':
                results = self._optimize_random_search(base_config, param_ranges, optimization_metric)
            else:
                logger.warning(f"Optimization method {optimization_method} not supported. Using grid search.")
                results = self._optimize_grid_search(base_config, param_ranges, optimization_metric)
            
            # Combine results
            optimization_results = {
                'id': optimization_id,
                'strategy_type': base_config.get('type', 'unknown'),
                'base_config': base_config,
                'param_ranges': param_ranges,
                'optimization_method': optimization_method,
                'optimization_metric': optimization_metric,
                'results': results,
                'execution_time': time.time() - start_time
            }
            
            # Store results
            self.optimization_results[optimization_id] = optimization_results
            
            # Generate report if configured
            if self.config['reporting']['generate_charts']:
                self._generate_optimization_charts(optimization_results)
            
            # Save results if configured
            if self.config['reporting']['save_results']:
                self._save_optimization_results(optimization_results)
            
            logger.info(f"Optimization completed: {optimization_id}")
            logger.info(f"Best parameters: {results['best_params']}")
            logger.info(f"Best {optimization_metric}: {results['best_metric']}")
            
            return optimization_results
        except Exception as e:
            logger.error(f"Error in optimization: {e}")
            return {
                'error': str(e),
                'status': 'failed'
            }
    
    def _optimize_grid_search(self, base_config: Dict, param_ranges: Dict, optimization_metric: str) -> Dict:
        """Optimize strategy using grid search
        
        Args:
            base_config: Base strategy configuration
            param_ranges: Parameter ranges for optimization
            optimization_metric: Metric to optimize
            
        Returns:
            Optimization results
        """
        logger.info("Running grid search optimization")
        
        # Generate parameter grid
        param_grid = self._generate_param_grid(param_ranges)
        
        # Track results
        all_results = []
        best_metric = float('-inf')
        best_params = None
        best_simulation = None
        
        # Number of simulations
        total_simulations = len(param_grid)
        logger.info(f"Running {total_simulations} simulations for grid search")
        
        # Run simulations with different parameters
        with ThreadPoolExecutor(max_workers=self.config['simulation']['max_concurrent_simulations']) as executor:
            # Submit all tasks
            future_to_params = {}
            for params in param_grid:
                # Create config for this simulation
                sim_config = base_config.copy()
                sim_config.update(params)
                
                # Submit task
                future = executor.submit(self.simulate_strategy, sim_config)
                future_to_params[future] = params
            
            # Process results as they complete
            for i, future in enumerate(as_completed(future_to_params)):
                params = future_to_params[future]
                
                try:
                    simulation_result = future.result()
                    
                    # Extract metric
                    if 'metrics' in simulation_result:
                        metric_value = simulation_result['metrics'].get(optimization_metric, 0)
                        
                        # Track result
                        result = {
                            'params': params,
                            'metric': metric_value,
                            'simulation_id': simulation_result['id']
                        }
                        all_results.append(result)
                        
                        # Update best if better
                        if metric_value > best_metric:
                            best_metric = metric_value
                            best_params = params
                            best_simulation = simulation_result
                    
                    logger.info(f"Completed simulation {i+1}/{total_simulations} - {optimization_metric}: {metric_value:.4f}")
                except Exception as e:
                    logger.error(f"Error in simulation with params {params}: {e}")
        
        # Sort results by metric
        all_results.sort(key=lambda x: x['metric'], reverse=True)
        
        # Prepare results
        results = {
            'all_results': all_results,
            'best_metric': best_metric,
            'best_params': best_params,
            'best_simulation_id': best_simulation['id'] if best_simulation else None
        }
        
        return results
    
    def _optimize_random_search(self, base_config: Dict, param_ranges: Dict, optimization_metric: str) -> Dict:
        """Optimize strategy using random search
        
        Args:
            base_config: Base strategy configuration
            param_ranges: Parameter ranges for optimization
            optimization_metric: Metric to optimize
            
        Returns:
            Optimization results
        """
        logger.info("Running random search optimization")
        
        # Number of iterations
        num_iterations = self.config['optimization']['num_iterations']
        
        # Track results
        all_results = []
        best_metric = float('-inf')
        best_params = None
        best_simulation = None
        
        logger.info(f"Running {num_iterations} simulations for random search")
        
        # Run simulations with different parameters
        with ThreadPoolExecutor(max_workers=self.config['simulation']['max_concurrent_simulations']) as executor:
            # Submit all tasks
            future_to_params = {}
            for _ in range(num_iterations):
                # Generate random parameters
                params = self._generate_random_params(param_ranges)
                
                # Create config for this simulation
                sim_config = base_config.copy()
                sim_config.update(params)
                
                # Submit task
                future = executor.submit(self.simulate_strategy, sim_config)
                future_to_params[future] = params
            
            # Process results as they complete
            for i, future in enumerate(as_completed(future_to_params)):
                params = future_to_params[future]
                
                try:
                    simulation_result = future.result()
                    
                    # Extract metric
                    if 'metrics' in simulation_result:
                        metric_value = simulation_result['metrics'].get(optimization_metric, 0)
                        
                        # Track result
                        result = {
                            'params': params,
                            'metric': metric_value,
                            'simulation_id': simulation_result['id']
                        }
                        all_results.append(result)
                        
                        # Update best if better
                        if metric_value > best_metric:
                            best_metric = metric_value
                            best_params = params
                            best_simulation = simulation_result
                    
                    logger.info(f"Completed simulation {i+1}/{num_iterations} - {optimization_metric}: {metric_value:.4f}")
                except Exception as e:
                    logger.error(f"Error in simulation with params {params}: {e}")
        
        # Sort results by metric
        all_results.sort(key=lambda x: x['metric'], reverse=True)
        
        # Prepare results
        results = {
            'all_results': all_results,
            'best_metric': best_metric,
            'best_params': best_params,
            'best_simulation_id': best_simulation['id'] if best_simulation else None
        }
        
        return results
    
    def _generate_param_grid(self, param_ranges: Dict) -> List[Dict]:
        """Generate parameter grid for grid search
        
        Args:
            param_ranges: Parameter ranges
            
        Returns:
            List of parameter combinations
        """
        # Extract parameter values
        param_values = {}
        for param, range_info in param_ranges.items():
            start, end, num = range_info
            values = np.linspace(start, end, num)
            param_values[param] = values
        
        # Generate all combinations
        param_names = list(param_values.keys())
        param_grid = []
        
        def generate_combinations(index, current_params):
            if index == len(param_names):
                param_grid.append(current_params.copy())
                return
            
            param = param_names[index]
            for value in param_values[param]:
                current_params[param] = value
                generate_combinations(index + 1, current_params)
        
        generate_combinations(0, {})
        
        return param_grid
    
    def _generate_random_params(self, param_ranges: Dict) -> Dict:
        """Generate random parameters within ranges
        
        Args:
            param_ranges: Parameter ranges
            
        Returns:
            Random parameter values
        """
        params = {}
        
        for param, range_info in param_ranges.items():
            start, end, _ = range_info
            value = np.random.uniform(start, end)
            params[param] = value
        
        return params
    
    def _generate_optimization_charts(self, optimization_results: Dict):
        """Generate charts for optimization results
        
        Args:
            optimization_results: Optimization results
        """
        try:
            # Create output directory if it doesn't exist
            output_dir = self.config['reporting']['output_dir']
            os.makedirs(output_dir, exist_ok=True)
            
            # Extract data
            results = optimization_results['results']
            all_results = results['all_results']
            optimization_id = optimization_results['id']
            optimization_metric = optimization_results['optimization_metric']
            
            # Convert to DataFrame
            results_df = pd.DataFrame(all_results)
            
            # Explode params column into separate columns
            param_df = pd.json_normalize(results_df['params'])
            results_df = pd.concat([results_df.drop('params', axis=1), param_df], axis=1)
            
            # Create figure with subplots
            num_params = len(param_df.columns)
            fig, axs = plt.subplots(1, num_params, figsize=(num_params * 5, 6))
            
            # Plot parameter vs metric for each parameter
            for i, param in enumerate(param_df.columns):
                ax = axs[i] if num_params > 1 else axs
                ax.scatter(results_df[param], results_df['metric'])
                ax.set_title(f'{param} vs {optimization_metric}')
                ax.set_xlabel(param)
                ax.set_ylabel(optimization_metric)
                ax.grid(True)
            
            # Adjust layout and save
            plt.tight_layout(rect=[0, 0.03, 1, 0.95])
            plt.suptitle(f"Strategy Optimization Results - {optimization_results['strategy_type']}", fontsize=16)
            
            # Save figure
            output_path = os.path.join(output_dir, f"{optimization_id}_charts.png")
            plt.savefig(output_path)
            plt.close()
            
            logger.info(f"Saved optimization charts to {output_path}")
        except Exception as e:
            logger.error(f"Error generating optimization charts: {e}")
    
    def _save_optimization_results(self, optimization_results: Dict):
        """Save optimization results to file
        
        Args:
            optimization_results: Optimization results
        """
        try:
            # Create output directory if it doesn't exist
            output_dir = self.config['reporting']['output_dir']
            os.makedirs(output_dir, exist_ok=True)
            
            # Save results as JSON
            output_path = os.path.join(output_dir, f"{optimization_results['id']}_results.json")
            
            with open(output_path, 'w') as f:
                json.dump(optimization_results, f, indent=2)
            
            logger.info(f"Saved optimization results to {output_path}")
        except Exception as e:
            logger.error(f"Error saving optimization results: {e}")

# Example usage
if __name__ == "__main__":
    # Initialize simulation engine
    engine = StrategySimulationEngine()
    
    # Example strategy configuration
    strategy_config = {
        'name': 'Flash Arbitrage Test',
        'type': 'flash_arbitrage_v2',
        'capital': 100000,
        'fee': 0.003,
        'slippage': 0.001,
        'gas_price_gwei': 50
    }
    
    # Run simulation
    simulation_results = engine.simulate_strategy(strategy_config)
    
    # Print results
    print(f"Simulation Results:")
    print(f"Total Profit: ${simulation_results['results']['total_profit']:.2f}")
    print(f"Total Trades: {simulation_results['results']['total_trades']}")
    print(f"Sharpe Ratio: {simulation_results['metrics']['sharpe_ratio']:.2f}")
    print(f"Win Rate: {simulation_results['metrics']['win_rate']*100:.2f}%")
    
    # Run optimization
    optimization_results = engine.optimize_strategy(strategy_config)
    
    # Print optimization results
    print(f"\nOptimization Results:")
    print(f"Best Parameters: {optimization_results['results']['best_params']}")
    print(f"Best Metric: {optimization_results['results']['best_metric']:.4f}")