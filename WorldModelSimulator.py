import os
import json
import time
import logging
import numpy as np
import pandas as pd
import tensorflow as tf
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
import yaml
import gym
from gym import spaces
import random
from datetime import datetime, timedelta
import hashlib
import multiprocessing as mp
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("world_model_simulator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("WorldModelSimulator")

class DeFiEnvironment(gym.Env):
    """
    A simulated DeFi environment that models various protocols, assets, and market conditions.
    This environment can be used to test strategies in a realistic but controlled setting.
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize the DeFi environment
        
        Args:
            config: Configuration dictionary
        """
        super(DeFiEnvironment, self).__init__()
        
        self.config = config or {}
        
        # Set up the action and observation spaces
        self.setup_spaces()
        
        # Initialize market state
        self.reset()
        
        logger.info("DeFi environment initialized")
    
    def setup_spaces(self):
        """Set up the action and observation spaces"""
        # Define the protocols available in the environment
        self.protocols = self.config.get("protocols", [
            "uniswap_v3", "aave_v3", "compound_v3", "curve", "balancer"
        ])
        
        # Define the assets available in the environment
        self.assets = self.config.get("assets", [
            "eth", "wbtc", "usdc", "usdt", "dai", "aave", "comp", "uni", "link"
        ])
        
        # Define the action space
        # Each action is a tuple of (protocol, action_type, asset1, asset2, amount)
        self.action_space = spaces.Dict({
            "protocol": spaces.Discrete(len(self.protocols)),
            "action_type": spaces.Discrete(5),  # 0: swap, 1: deposit, 2: withdraw, 3: borrow, 4: repay
            "asset1": spaces.Discrete(len(self.assets)),
            "asset2": spaces.Discrete(len(self.assets)),
            "amount_percentage": spaces.Box(low=0, high=1, shape=(1,), dtype=np.float32)
        })
        
        # Define the observation space
        # This includes market prices, liquidity, interest rates, and portfolio state
        num_assets = len(self.assets)
        num_protocols = len(self.protocols)
        
        self.observation_space = spaces.Dict({
            # Market data
            "prices": spaces.Box(low=0, high=np.inf, shape=(num_assets,), dtype=np.float32),
            "price_changes_24h": spaces.Box(low=-1, high=1, shape=(num_assets,), dtype=np.float32),
            "volumes_24h": spaces.Box(low=0, high=np.inf, shape=(num_assets,), dtype=np.float32),
            
            # Protocol-specific data
            "liquidity": spaces.Box(low=0, high=np.inf, shape=(num_protocols, num_assets), dtype=np.float32),
            "supply_apy": spaces.Box(low=0, high=1, shape=(num_protocols, num_assets), dtype=np.float32),
            "borrow_apy": spaces.Box(low=0, high=1, shape=(num_protocols, num_assets), dtype=np.float32),
            
            # Portfolio state
            "wallet_balances": spaces.Box(low=0, high=np.inf, shape=(num_assets,), dtype=np.float32),
            "supplied_balances": spaces.Box(low=0, high=np.inf, shape=(num_protocols, num_assets), dtype=np.float32),
            "borrowed_balances": spaces.Box(low=0, high=np.inf, shape=(num_protocols, num_assets), dtype=np.float32),
            "collateral_factors": spaces.Box(low=0, high=1, shape=(num_protocols, num_assets), dtype=np.float32),
            
            # Gas and network state
            "gas_price": spaces.Box(low=0, high=np.inf, shape=(1,), dtype=np.float32),
            "network_congestion": spaces.Box(low=0, high=1, shape=(1,), dtype=np.float32),
            
            # Time features
            "hour_of_day": spaces.Box(low=0, high=23, shape=(1,), dtype=np.int32),
            "day_of_week": spaces.Box(low=0, high=6, shape=(1,), dtype=np.int32)
        })
    
    def reset(self):
        """
        Reset the environment to an initial state
        
        Returns:
            Initial observation
        """
        # Initialize market state
        self.current_step = 0
        self.max_steps = self.config.get("max_steps", 1000)
        self.current_timestamp = datetime.now()
        
        # Initialize prices with realistic values
        self.prices = {
            "eth": 2000.0 + random.uniform(-100, 100),
            "wbtc": 30000.0 + random.uniform(-1000, 1000),
            "usdc": 1.0 + random.uniform(-0.01, 0.01),
            "usdt": 1.0 + random.uniform(-0.01, 0.01),
            "dai": 1.0 + random.uniform(-0.01, 0.01),
            "aave": 80.0 + random.uniform(-5, 5),
            "comp": 60.0 + random.uniform(-3, 3),
            "uni": 5.0 + random.uniform(-0.5, 0.5),
            "link": 15.0 + random.uniform(-1, 1)
        }
        
        # Initialize price history for calculating 24h changes
        self.price_history = {asset: [price] for asset, price in self.prices.items()}
        
        # Initialize volumes
        self.volumes_24h = {asset: random.uniform(1e6, 1e9) for asset in self.assets}
        
        # Initialize protocol-specific data
        self.liquidity = {
            protocol: {asset: random.uniform(1e6, 1e9) for asset in self.assets}
            for protocol in self.protocols
        }
        
        self.supply_apy = {
            protocol: {asset: random.uniform(0.01, 0.2) for asset in self.assets}
            for protocol in self.protocols
        }
        
        self.borrow_apy = {
            protocol: {asset: random.uniform(0.02, 0.3) for asset in self.assets}
            for protocol in self.protocols
        }
        
        # Initialize portfolio state
        initial_balance = self.config.get("initial_balance", 100000)  # $100k in USD
        
        self.wallet_balances = {
            "eth": initial_balance * 0.3 / self.prices["eth"],  # 30% in ETH
            "wbtc": initial_balance * 0.2 / self.prices["wbtc"],  # 20% in WBTC
            "usdc": initial_balance * 0.5,  # 50% in USDC
            "usdt": 0.0,
            "dai": 0.0,
            "aave": 0.0,
            "comp": 0.0,
            "uni": 0.0,
            "link": 0.0
        }
        
        self.supplied_balances = {
            protocol: {asset: 0.0 for asset in self.assets}
            for protocol in self.protocols
        }
        
        self.borrowed_balances = {
            protocol: {asset: 0.0 for asset in self.assets}
            for protocol in self.protocols
        }
        
        self.collateral_factors = {
            protocol: {asset: random.uniform(0.5, 0.9) for asset in self.assets}
            for protocol in self.protocols
        }
        
        # Initialize gas and network state
        self.gas_price = random.uniform(20, 100)  # in gwei
        self.network_congestion = random.uniform(0.1, 0.8)
        
        # Calculate portfolio value
        self.portfolio_value = self.calculate_portfolio_value()
        self.initial_portfolio_value = self.portfolio_value
        
        # Return initial observation
        return self._get_observation()
    
    def step(self, action):
        """
        Take a step in the environment
        
        Args:
            action: Action to take
            
        Returns:
            observation: New observation
            reward: Reward from the action
            done: Whether the episode is done
            info: Additional information
        """
        # Unpack action
        protocol_idx = action["protocol"]
        action_type = action["action_type"]
        asset1_idx = action["asset1"]
        asset2_idx = action["asset2"]
        amount_percentage = float(action["amount_percentage"])
        
        protocol = self.protocols[protocol_idx]
        asset1 = self.assets[asset1_idx]
        asset2 = self.assets[asset2_idx]
        
        # Execute action
        success, action_result = self._execute_action(protocol, action_type, asset1, asset2, amount_percentage)
        
        # Update environment state
        self._update_state()
        
        # Calculate reward
        new_portfolio_value = self.calculate_portfolio_value()
        reward = (new_portfolio_value - self.portfolio_value) / self.portfolio_value
        self.portfolio_value = new_portfolio_value
        
        # Check if episode is done
        self.current_step += 1
        done = self.current_step >= self.max_steps
        
        # Get observation
        observation = self._get_observation()
        
        # Additional info
        info = {
            "portfolio_value": self.portfolio_value,
            "portfolio_change": (self.portfolio_value - self.initial_portfolio_value) / self.initial_portfolio_value,
            "action_success": success,
            "action_result": action_result
        }
        
        return observation, reward, done, info
    
    def _execute_action(self, protocol, action_type, asset1, asset2, amount_percentage):
        """
        Execute an action in the environment
        
        Args:
            protocol: Protocol to interact with
            action_type: Type of action (0: swap, 1: deposit, 2: withdraw, 3: borrow, 4: repay)
            asset1: First asset
            asset2: Second asset
            amount_percentage: Percentage of available balance to use
            
        Returns:
            success: Whether the action was successful
            result: Result of the action
        """
        # Ensure amount_percentage is between 0 and 1
        amount_percentage = max(0.0, min(1.0, amount_percentage))
        
        # Execute action based on type
        if action_type == 0:  # swap
            return self._execute_swap(protocol, asset1, asset2, amount_percentage)
        elif action_type == 1:  # deposit
            return self._execute_deposit(protocol, asset1, amount_percentage)
        elif action_type == 2:  # withdraw
            return self._execute_withdraw(protocol, asset1, amount_percentage)
        elif action_type == 3:  # borrow
            return self._execute_borrow(protocol, asset1, amount_percentage)
        elif action_type == 4:  # repay
            return self._execute_repay(protocol, asset1, amount_percentage)
        else:
            return False, {"error": "Invalid action type"}
    
    def _execute_swap(self, protocol, asset_from, asset_to, amount_percentage):
        """Execute a swap action"""
        if asset_from == asset_to:
            return False, {"error": "Cannot swap an asset for itself"}
        
        # Calculate amount to swap
        available_amount = self.wallet_balances[asset_from]
        amount = available_amount * amount_percentage
        
        if amount <= 0:
            return False, {"error": f"Insufficient {asset_from} balance for swap"}
        
        # Calculate output amount with slippage
        price_from = self.prices[asset_from]
        price_to = self.prices[asset_to]
        
        # Base conversion
        output_amount_base = amount * price_from / price_to
        
        # Apply slippage based on amount relative to liquidity
        liquidity = self.liquidity[protocol][asset_to]
        slippage_factor = 1.0 - min(0.1, (amount * price_from) / liquidity)
        
        output_amount = output_amount_base * slippage_factor
        
        # Update balances
        self.wallet_balances[asset_from] -= amount
        self.wallet_balances[asset_to] += output_amount
        
        # Update volumes
        self.volumes_24h[asset_from] += amount * price_from
        self.volumes_24h[asset_to] += output_amount * price_to
        
        return True, {
            "action": "swap",
            "protocol": protocol,
            "asset_from": asset_from,
            "asset_to": asset_to,
            "amount_in": amount,
            "amount_out": output_amount,
            "slippage": 1.0 - slippage_factor
        }
    
    def _execute_deposit(self, protocol, asset, amount_percentage):
        """Execute a deposit action"""
        # Calculate amount to deposit
        available_amount = self.wallet_balances[asset]
        amount = available_amount * amount_percentage
        
        if amount <= 0:
            return False, {"error": f"Insufficient {asset} balance for deposit"}
        
        # Update balances
        self.wallet_balances[asset] -= amount
        self.supplied_balances[protocol][asset] += amount
        
        return True, {
            "action": "deposit",
            "protocol": protocol,
            "asset": asset,
            "amount": amount
        }
    
    def _execute_withdraw(self, protocol, asset, amount_percentage):
        """Execute a withdraw action"""
        # Calculate amount to withdraw
        available_amount = self.supplied_balances[protocol][asset]
        amount = available_amount * amount_percentage
        
        if amount <= 0:
            return False, {"error": f"Insufficient {asset} supplied balance for withdrawal"}
        
        # Check if withdrawal would cause liquidation
        if not self._check_health_factor(protocol, asset, -amount, 0):
            return False, {"error": "Withdrawal would cause liquidation"}
        
        # Update balances
        self.supplied_balances[protocol][asset] -= amount
        self.wallet_balances[asset] += amount
        
        return True, {
            "action": "withdraw",
            "protocol": protocol,
            "asset": asset,
            "amount": amount
        }
    
    def _execute_borrow(self, protocol, asset, amount_percentage):
        """Execute a borrow action"""
        # Calculate maximum borrowable amount
        max_borrow = self._calculate_max_borrow(protocol, asset)
        amount = max_borrow * amount_percentage
        
        if amount <= 0:
            return False, {"error": f"Cannot borrow {asset} due to insufficient collateral"}
        
        # Update balances
        self.borrowed_balances[protocol][asset] += amount
        self.wallet_balances[asset] += amount
        
        return True, {
            "action": "borrow",
            "protocol": protocol,
            "asset": asset,
            "amount": amount
        }
    
    def _execute_repay(self, protocol, asset, amount_percentage):
        """Execute a repay action"""
        # Calculate amount to repay
        borrowed_amount = self.borrowed_balances[protocol][asset]
        wallet_amount = self.wallet_balances[asset]
        
        amount = min(borrowed_amount, wallet_amount * amount_percentage)
        
        if amount <= 0:
            return False, {"error": f"No {asset} to repay or insufficient wallet balance"}
        
        # Update balances
        self.borrowed_balances[protocol][asset] -= amount
        self.wallet_balances[asset] -= amount
        
        return True, {
            "action": "repay",
            "protocol": protocol,
            "asset": asset,
            "amount": amount
        }
    
    def _check_health_factor(self, protocol, asset, supply_change, borrow_change):
        """
        Check if a change in supply or borrow would maintain a healthy position
        
        Args:
            protocol: Protocol to check
            asset: Asset being changed
            supply_change: Change in supplied amount (negative for withdrawals)
            borrow_change: Change in borrowed amount (positive for new borrows)
            
        Returns:
            bool: Whether the health factor would remain above 1.0
        """
        # Calculate current collateral value
        collateral_value = 0
        for a in self.assets:
            supplied = self.supplied_balances[protocol][a]
            if supplied > 0:
                if a == asset:
                    supplied += supply_change
                collateral_value += supplied * self.prices[a] * self.collateral_factors[protocol][a]
        
        # Calculate current borrow value
        borrow_value = 0
        for a in self.assets:
            borrowed = self.borrowed_balances[protocol][a]
            if borrowed > 0:
                if a == asset:
                    borrowed += borrow_change
                borrow_value += borrowed * self.prices[a]
        
        # Calculate health factor
        if borrow_value == 0:
            return True  # No borrows, always healthy
        
        health_factor = collateral_value / borrow_value
        return health_factor >= 1.0
    
    def _calculate_max_borrow(self, protocol, asset):
        """
        Calculate maximum borrowable amount for an asset
        
        Args:
            protocol: Protocol to check
            asset: Asset to borrow
            
        Returns:
            float: Maximum borrowable amount
        """
        # Calculate current collateral value
        collateral_value = 0
        for a in self.assets:
            supplied = self.supplied_balances[protocol][a]
            if supplied > 0:
                collateral_value += supplied * self.prices[a] * self.collateral_factors[protocol][a]
        
        # Calculate current borrow value
        borrow_value = 0
        for a in self.assets:
            borrowed = self.borrowed_balances[protocol][a]
            if borrowed > 0:
                borrow_value += borrowed * self.prices[a]
        
        # Calculate maximum additional borrow value
        # Using a safety factor of 0.8 to avoid getting too close to liquidation
        max_additional_borrow_value = (collateral_value - borrow_value) * 0.8
        
        # Convert to asset amount
        max_borrow_amount = max_additional_borrow_value / self.prices[asset]
        
        # Ensure it doesn't exceed protocol liquidity
        max_borrow_amount = min(max_borrow_amount, self.liquidity[protocol][asset] * 0.1)
        
        return max(0, max_borrow_amount)
    
    def _update_state(self):
        """Update the environment state for the next step"""
        # Update timestamp
        self.current_timestamp += timedelta(minutes=15)  # 15-minute intervals
        
        # Update prices with random walk
        for asset in self.assets:
            # Volatility varies by asset
            if asset in ["usdc", "usdt", "dai"]:
                volatility = 0.001  # Stablecoins have low volatility
            elif asset in ["eth", "wbtc"]:
                volatility = 0.02   # Major cryptos have medium volatility
            else:
                volatility = 0.03   # Altcoins have higher volatility
            
            # Random price change with mean reversion for stablecoins
            if asset in ["usdc", "usdt", "dai"]:
                # Mean reversion to $1
                current_price = self.prices[asset]
                mean_reversion = 0.1 * (1.0 - current_price)
                price_change = mean_reversion + random.normalvariate(0, volatility)
            else:
                price_change = random.normalvariate(0, volatility)
            
            # Update price
            self.prices[asset] *= (1 + price_change)
            
            # Ensure stablecoins don't deviate too far from $1
            if asset in ["usdc", "usdt", "dai"]:
                self.prices[asset] = max(0.95, min(1.05, self.prices[asset]))
            
            # Update price history
            self.price_history[asset].append(self.prices[asset])
            if len(self.price_history[asset]) > 96:  # Keep 24 hours of 15-min data
                self.price_history[asset].pop(0)
        
        # Update APYs based on utilization
        for protocol in self.protocols:
            for asset in self.assets:
                # Calculate utilization rate
                total_supplied = sum(self.supplied_balances[p][asset] for p in self.protocols)
                total_borrowed = sum(self.borrowed_balances[p][asset] for p in self.protocols)
                
                if total_supplied > 0:
                    utilization = total_borrowed / total_supplied
                else:
                    utilization = 0
                
                # Update supply APY
                base_supply_apy = 0.01  # 1% base APY
                utilization_bonus = 0.1 * utilization  # Up to 10% additional APY at 100% utilization
                self.supply_apy[protocol][asset] = base_supply_apy + utilization_bonus
                
                # Update borrow APY
                base_borrow_apy = 0.02  # 2% base APY
                utilization_premium = 0.2 * utilization  # Up to 20% additional APY at 100% utilization
                self.borrow_apy[protocol][asset] = base_borrow_apy + utilization_premium
        
        # Update gas price with random walk
        gas_change = random.normalvariate(0, 0.1)
        self.gas_price *= (1 + gas_change)
        self.gas_price = max(10, min(500, self.gas_price))  # Keep between 10-500 gwei
        
        # Update network congestion
        self.network_congestion = max(0.1, min(0.9, self.network_congestion + random.normalvariate(0, 0.05)))
        
        # Apply interest to supplied and borrowed balances
        time_factor = 15 / (24 * 60)  # 15 minutes as fraction of a day
        for protocol in self.protocols:
            for asset in self.assets:
                # Apply supply interest
                supply_interest = self.supplied_balances[protocol][asset] * self.supply_apy[protocol][asset] * time_factor
                self.supplied_balances[protocol][asset] += supply_interest
                
                # Apply borrow interest
                borrow_interest = self.borrowed_balances[protocol][asset] * self.borrow_apy[protocol][asset] * time_factor
                self.borrowed_balances[protocol][asset] += borrow_interest
    
    def _get_observation(self):
        """
        Get the current observation
        
        Returns:
            Dict containing the current observation
        """
        # Convert dictionaries to arrays for gym spaces
        prices_array = np.array([self.prices[asset] for asset in self.assets], dtype=np.float32)
        
        # Calculate 24h price changes
        price_changes_24h = np.zeros(len(self.assets), dtype=np.float32)
        for i, asset in enumerate(self.assets):
            if len(self.price_history[asset]) > 1:
                old_price = self.price_history[asset][0]
                current_price = self.price_history[asset][-1]
                price_changes_24h[i] = (current_price - old_price) / old_price
        
        volumes_24h_array = np.array([self.volumes_24h[asset] for asset in self.assets], dtype=np.float32)
        
        # Protocol-specific data
        liquidity_array = np.zeros((len(self.protocols), len(self.assets)), dtype=np.float32)
        supply_apy_array = np.zeros((len(self.protocols), len(self.assets)), dtype=np.float32)
        borrow_apy_array = np.zeros((len(self.protocols), len(self.assets)), dtype=np.float32)
        
        for i, protocol in enumerate(self.protocols):
            for j, asset in enumerate(self.assets):
                liquidity_array[i, j] = self.liquidity[protocol][asset]
                supply_apy_array[i, j] = self.supply_apy[protocol][asset]
                borrow_apy_array[i, j] = self.borrow_apy[protocol][asset]
        
        # Portfolio state
        wallet_balances_array = np.array([self.wallet_balances[asset] for asset in self.assets], dtype=np.float32)
        
        supplied_balances_array = np.zeros((len(self.protocols), len(self.assets)), dtype=np.float32)
        borrowed_balances_array = np.zeros((len(self.protocols), len(self.assets)), dtype=np.float32)
        collateral_factors_array = np.zeros((len(self.protocols), len(self.assets)), dtype=np.float32)
        
        for i, protocol in enumerate(self.protocols):
            for j, asset in enumerate(self.assets):
                supplied_balances_array[i, j] = self.supplied_balances[protocol][asset]
                borrowed_balances_array[i, j] = self.borrowed_balances[protocol][asset]
                collateral_factors_array[i, j] = self.collateral_factors[protocol][asset]
        
        # Time features
        hour_of_day = np.array([self.current_timestamp.hour], dtype=np.int32)
        day_of_week = np.array([self.current_timestamp.weekday()], dtype=np.int32)
        
        return {
            # Market data
            "prices": prices_array,
            "price_changes_24h": price_changes_24h,
            "volumes_24h": volumes_24h_array,
            
            # Protocol-specific data
            "liquidity": liquidity_array,
            "supply_apy": supply_apy_array,
            "borrow_apy": borrow_apy_array,
            
            # Portfolio state
            "wallet_balances": wallet_balances_array,
            "supplied_balances": supplied_balances_array,
            "borrowed_balances": borrowed_balances_array,
            "collateral_factors": collateral_factors_array,
            
            # Gas and network state
            "gas_price": np.array([self.gas_price], dtype=np.float32),
            "network_congestion": np.array([self.network_congestion], dtype=np.float32),
            
            # Time features
            "hour_of_day": hour_of_day,
            "day_of_week": day_of_week
        }
    
    def calculate_portfolio_value(self):
        """
        Calculate the total portfolio value in USD
        
        Returns:
            float: Total portfolio value
        """
        total_value = 0
        
        # Add wallet balances
        for asset, balance in self.wallet_balances.items():
            total_value += balance * self.prices[asset]
        
        # Add supplied balances
        for protocol in self.protocols:
            for asset, balance in self.supplied_balances[protocol].items():
                total_value += balance * self.prices[asset]
        
        # Subtract borrowed balances
        for protocol in self.protocols:
            for asset, balance in self.borrowed_balances[protocol].items():
                total_value -= balance * self.prices[asset]
        
        return total_value
    
    def render(self, mode='human'):
        """Render the environment"""
        if mode == 'human':
            portfolio_value = self.calculate_portfolio_value()
            portfolio_change = (portfolio_value - self.initial_portfolio_value) / self.initial_portfolio_value * 100
            
            print(f"\n=== DeFi Environment State (Step {self.current_step}) ===")
            print(f"Timestamp: {self.current_timestamp}")
            print(f"Portfolio Value: ${portfolio_value:.2f} ({portfolio_change:+.2f}%)")
            
            print("\nAsset Prices:")
            for asset in self.assets:
                price = self.prices[asset]
                if len(self.price_history[asset]) > 1:
                    old_price = self.price_history[asset][0]
                    price_change = (price - old_price) / old_price * 100
                    print(f"  {asset.upper()}: ${price:.2f} ({price_change:+.2f}%)")
                else:
                    print(f"  {asset.upper()}: ${price:.2f}")
            
            print("\nWallet Balances:")
            for asset, balance in self.wallet_balances.items():
                if balance > 0:
                    value = balance * self.prices[asset]
                    print(f"  {asset.upper()}: {balance:.6f} (${value:.2f})")
            
            print("\nSupplied Balances:")
            for protocol in self.protocols:
                for asset, balance in self.supplied_balances[protocol].items():
                    if balance > 0:
                        value = balance * self.prices[asset]
                        apy = self.supply_apy[protocol][asset] * 100
                        print(f"  {protocol} - {asset.upper()}: {balance:.6f} (${value:.2f}, APY: {apy:.2f}%)")
            
            print("\nBorrowed Balances:")
            for protocol in self.protocols:
                for asset, balance in self.borrowed_balances[protocol].items():
                    if balance > 0:
                        value = balance * self.prices[asset]
                        apy = self.borrow_apy[protocol][asset] * 100
                        print(f"  {protocol} - {asset.upper()}: {balance:.6f} (${value:.2f}, APY: {apy:.2f}%)")
            
            print(f"\nGas Price: {self.gas_price:.2f} gwei")
            print(f"Network Congestion: {self.network_congestion:.2f}")
            
            print("=" * 50)

class WorldModelSimulator:
    """
    A massively parallel simulation environment for testing DeFi strategies.
    This simulator can run multiple scenarios simultaneously to evaluate strategy performance.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the World Model Simulator
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path or "world_model_simulator_config.yaml"
        self._load_config(self.config_path)
        self._setup_directories()
        
        logger.info(f"World Model Simulator initialized")
    
    def _load_config(self, config_path: str) -> Dict:
        """
        Load configuration from YAML file
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Dict containing configuration
        """
        try:
            with open(config_path, 'r') as file:
                self.config = yaml.safe_load(file)
                logger.info(f"Configuration loaded from {config_path}")
                return self.config
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            # Default configuration
            self.config = {
                "simulation": {
                    "num_parallel_envs": mp.cpu_count(),
                    "num_episodes": 100,
                    "max_steps_per_episode": 1000,
                    "random_seed": 42
                },
                "environment": {
                    "protocols": ["uniswap_v3", "aave_v3", "compound_v3", "curve", "balancer"],
                    "assets": ["eth", "wbtc", "usdc", "usdt", "dai", "aave", "comp", "uni", "link"],
                    "initial_balance": 100000  # $100k in USD
                },
                "scenarios": [
                    {
                        "name": "bull_market",
                        "description": "Simulates a bull market with rising prices",
                        "price_trend_factor": 0.001,  # 0.1% upward trend per step
                        "volatility_factor": 1.0,
                        "liquidity_factor": 1.2,
                        "probability": 0.3  # 30% chance of this scenario
                    },
                    {
                        "name": "bear_market",
                        "description": "Simulates a bear market with falling prices",
                        "price_trend_factor": -0.001,  # 0.1% downward trend per step
                        "volatility_factor": 1.5,
                        "liquidity_factor": 0.8,
                        "probability": 0.3  # 30% chance of this scenario
                    },
                    {
                        "name": "sideways_market",
                        "description": "Simulates a sideways market with no clear trend",
                        "price_trend_factor": 0.0,
                        "volatility_factor": 0.7,
                        "liquidity_factor": 1.0,
                        "probability": 0.4  # 40% chance of this scenario
                    }
                ],
                "black_swan_events": [
                    {
                        "name": "flash_crash",
                        "description": "Sudden market crash with quick recovery",
                        "price_impact": -0.3,  # 30% drop
                        "duration_steps": 10,
                        "recovery_factor": 0.8,  # 80% recovery
                        "probability": 0.05  # 5% chance per episode
                    },
                    {
                        "name": "liquidity_crisis",
                        "description": "Severe reduction in market liquidity",
                        "liquidity_impact": -0.7,  # 70% reduction
                        "duration_steps": 50,
                        "recovery_factor": 0.9,  # 90% recovery
                        "probability": 0.03  # 3% chance per episode
                    },
                    {
                        "name": "protocol_hack",
                        "description": "Security breach in a protocol",
                        "affected_protocols": ["aave_v3", "compound_v3"],  # Randomly select one
                        "tvl_impact": -0.5,  # 50% TVL reduction
                        "duration_steps": 100,
                        "recovery_factor": 0.7,  # 70% recovery
                        "probability": 0.02  # 2% chance per episode
                    }
                ],
                "data_dir": "data/world_model_simulator",
                "results_dir": "results/world_model_simulator"
            }
            return self.config
    
    def _setup_directories(self):
        """Create necessary directories for data storage"""
        os.makedirs(self.config.get("data_dir", "data/world_model_simulator"), exist_ok=True)
        os.makedirs(self.config.get("results_dir", "results/world_model_simulator"), exist_ok=True)
    
    def create_environment(self, scenario: Dict = None) -> DeFiEnvironment:
        """
        Create a DeFi environment with the specified scenario
        
        Args:
            scenario: Scenario configuration
            
        Returns:
            DeFiEnvironment instance
        """
        # Create environment config
        env_config = self.config.get("environment", {}).copy()
        
        # Apply scenario modifications if provided
        if scenario:
            # Add scenario parameters to config
            env_config["scenario"] = scenario
            
            # Modify environment based on scenario
            if "price_trend_factor" in scenario:
                env_config["price_trend_factor"] = scenario["price_trend_factor"]
            
            if "volatility_factor" in scenario:
                env_config["volatility_factor"] = scenario["volatility_factor"]
            
            if "liquidity_factor" in scenario:
                env_config["liquidity_factor"] = scenario["liquidity_factor"]
        
        # Create environment
        env = DeFiEnvironment(config=env_config)
        
        return env
    
    def run_simulation(self, strategy, scenario_name: str = None) -> Dict:
        """
        Run a simulation with the specified strategy and scenario
        
        Args:
            strategy: Strategy to evaluate
            scenario_name: Name of the scenario to use (or None for random selection)
            
        Returns:
            Dict containing simulation results
        """
        # Select scenario
        if scenario_name:
            scenario = next((s for s in self.config.get("scenarios", []) if s["name"] == scenario_name), None)
            if not scenario:
                logger.warning(f"Scenario '{scenario_name}' not found, using random scenario")
                scenario = self._select_random_scenario()
        else:
            scenario = self._select_random_scenario()
        
        logger.info(f"Running simulation with scenario: {scenario['name']}")
        
        # Create environment
        env = self.create_environment(scenario)
        
        # Run episode
        observation = env.reset()
        done = False
        total_reward = 0
        step_results = []
        
        # Check if black swan event should occur
        black_swan_event = self._select_random_black_swan_event()
        black_swan_step = None
        
        if black_swan_event:
            # Randomly select when the event will occur
            black_swan_step = random.randint(
                int(env.max_steps * 0.2),  # Not too early
                int(env.max_steps * 0.8)   # Not too late
            )
            logger.info(f"Black swan event '{black_swan_event['name']}' will occur at step {black_swan_step}")
        
        # Run episode
        for step in range(env.max_steps):
            # Apply black swan event if it's time
            if black_swan_event and step == black_swan_step:
                self._apply_black_swan_event(env, black_swan_event)
                logger.info(f"Applied black swan event: {black_swan_event['name']}")
            
            # Get action from strategy
            action = strategy.get_action(observation)
            
            # Take step in environment
            next_observation, reward, done, info = env.step(action)
            
            # Record step results
            step_results.append({
                "step": step,
                "action": action,
                "reward": reward,
                "portfolio_value": info["portfolio_value"],
                "portfolio_change": info["portfolio_change"]
            })
            
            # Update total reward
            total_reward += reward
            
            # Update observation
            observation = next_observation
            
            if done:
                break
        
        # Calculate final portfolio value and return
        final_portfolio_value = env.calculate_portfolio_value()
        portfolio_return = (final_portfolio_value - env.initial_portfolio_value) / env.initial_portfolio_value
        
        # Compile results
        results = {
            "scenario": scenario["name"],
            "black_swan_event": black_swan_event["name"] if black_swan_event else None,
            "initial_portfolio_value": env.initial_portfolio_value,
            "final_portfolio_value": final_portfolio_value,
            "portfolio_return": portfolio_return,
            "total_reward": total_reward,
            "num_steps": len(step_results),
            "step_results": step_results
        }
        
        logger.info(f"Simulation completed: Return: {portfolio_return:.2%}, Reward: {total_reward:.4f}")
        
        return results
    
    def run_parallel_simulations(self, strategy, num_simulations: int = None) -> List[Dict]:
        """
        Run multiple simulations in parallel
        
        Args:
            strategy: Strategy to evaluate
            num_simulations: Number of simulations to run (default: from config)
            
        Returns:
            List of simulation results
        """
        if num_simulations is None:
            num_simulations = self.config.get("simulation", {}).get("num_episodes", 100)
        
        logger.info(f"Running {num_simulations} parallel simulations")
        
        # Create a pool of workers
        num_workers = min(
            self.config.get("simulation", {}).get("num_parallel_envs", mp.cpu_count()),
            mp.cpu_count()
        )
        
        # Prepare arguments for each simulation
        args = [(strategy, None) for _ in range(num_simulations)]
        
        # Run simulations in parallel
        with mp.Pool(num_workers) as pool:
            results = list(tqdm(pool.starmap(self.run_simulation, args), total=num_simulations))
        
        logger.info(f"Completed {num_simulations} simulations")
        
        return results
    
    def evaluate_strategy(self, strategy, num_simulations: int = None) -> Dict:
        """
        Evaluate a strategy across multiple simulations
        
        Args:
            strategy: Strategy to evaluate
            num_simulations: Number of simulations to run
            
        Returns:
            Dict containing evaluation results
        """
        # Run simulations
        simulation_results = self.run_parallel_simulations(strategy, num_simulations)
        
        # Calculate aggregate statistics
        returns = [result["portfolio_return"] for result in simulation_results]
        rewards = [result["total_reward"] for result in simulation_results]
        
        mean_return = np.mean(returns)
        median_return = np.median(returns)
        std_return = np.std(returns)
        min_return = np.min(returns)
        max_return = np.max(returns)
        
        # Calculate risk metrics
        negative_returns = [r for r in returns if r < 0]
        max_drawdown = min(returns) if returns else 0
        
        # Calculate Sharpe ratio (assuming risk-free rate of 0)
        sharpe_ratio = mean_return / std_return if std_return > 0 else 0
        
        # Calculate success rate
        success_rate = len([r for r in returns if r > 0]) / len(returns) if returns else 0
        
        # Compile evaluation results
        evaluation_results = {
            "num_simulations": len(simulation_results),
            "mean_return": mean_return,
            "median_return": median_return,
            "std_return": std_return,
            "min_return": min_return,
            "max_return": max_return,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "success_rate": success_rate,
            "mean_reward": np.mean(rewards),
            "scenario_performance": self._calculate_scenario_performance(simulation_results),
            "black_swan_performance": self._calculate_black_swan_performance(simulation_results),
            "simulation_results": simulation_results
        }
        
        # Save results
        self._save_evaluation_results(strategy, evaluation_results)
        
        logger.info(f"Strategy evaluation completed:")
        logger.info(f"  Mean Return: {mean_return:.2%}")
        logger.info(f"  Sharpe Ratio: {sharpe_ratio:.2f}")
        logger.info(f"  Success Rate: {success_rate:.2%}")
        
        return evaluation_results
    
    def _select_random_scenario(self) -> Dict:
        """
        Select a random scenario based on probabilities
        
        Returns:
            Dict containing scenario configuration
        """
        scenarios = self.config.get("scenarios", [])
        
        if not scenarios:
            # Return default scenario
            return {
                "name": "default",
                "description": "Default scenario",
                "price_trend_factor": 0.0,
                "volatility_factor": 1.0,
                "liquidity_factor": 1.0
            }
        
        # Get probabilities
        probabilities = [scenario.get("probability", 1.0 / len(scenarios)) for scenario in scenarios]
        
        # Normalize probabilities
        total_prob = sum(probabilities)
        if total_prob > 0:
            probabilities = [p / total_prob for p in probabilities]
        else:
            probabilities = [1.0 / len(scenarios) for _ in scenarios]
        
        # Select scenario
        return random.choices(scenarios, weights=probabilities, k=1)[0]
    
    def _select_random_black_swan_event(self) -> Optional[Dict]:
        """
        Select a random black swan event based on probabilities
        
        Returns:
            Dict containing black swan event configuration, or None if no event occurs
        """
        events = self.config.get("black_swan_events", [])
        
        if not events:
            return None
        
        # Check if any event should occur
        for event in events:
            probability = event.get("probability", 0.0)
            if random.random() < probability:
                return event
        
        return None
    
    def _apply_black_swan_event(self, env: DeFiEnvironment, event: Dict):
        """
        Apply a black swan event to the environment
        
        Args:
            env: DeFi environment
            event: Black swan event configuration
        """
        event_name = event.get("name", "unknown")
        
        if event_name == "flash_crash":
            # Apply price impact to all assets except stablecoins
            price_impact = event.get("price_impact", -0.3)
            for asset in env.assets:
                if asset not in ["usdc", "usdt", "dai"]:
                    env.prices[asset] *= (1 + price_impact)
            
            # Schedule recovery
            # In a real implementation, this would modify the price trend
            # For this example, we'll just log it
            logger.info(f"Flash crash applied: {price_impact:.1%} price impact")
            
        elif event_name == "liquidity_crisis":
            # Reduce liquidity across all protocols and assets
            liquidity_impact = event.get("liquidity_impact", -0.7)
            for protocol in env.protocols:
                for asset in env.assets:
                    env.liquidity[protocol][asset] *= (1 + liquidity_impact)
            
            # Increase volatility
            # In a real implementation, this would modify the volatility factor
            logger.info(f"Liquidity crisis applied: {liquidity_impact:.1%} liquidity impact")
            
        elif event_name == "protocol_hack":
            # Select a random affected protocol
            affected_protocols = event.get("affected_protocols", [])
            if not affected_protocols:
                affected_protocols = env.protocols
            
            affected_protocol = random.choice(affected_protocols)
            tvl_impact = event.get("tvl_impact", -0.5)
            
            # Reduce TVL in the affected protocol
            for asset in env.assets:
                env.liquidity[affected_protocol][asset] *= (1 + tvl_impact)
            
            logger.info(f"Protocol hack applied to {affected_protocol}: {tvl_impact:.1%} TVL impact")
    
    def _calculate_scenario_performance(self, simulation_results: List[Dict]) -> Dict:
        """
        Calculate performance metrics by scenario
        
        Args:
            simulation_results: List of simulation results
            
        Returns:
            Dict containing performance metrics by scenario
        """
        scenario_performance = {}
        
        # Group results by scenario
        for scenario in self.config.get("scenarios", []):
            scenario_name = scenario["name"]
            scenario_results = [r for r in simulation_results if r["scenario"] == scenario_name]
            
            if scenario_results:
                returns = [r["portfolio_return"] for r in scenario_results]
                
                scenario_performance[scenario_name] = {
                    "count": len(scenario_results),
                    "mean_return": np.mean(returns),
                    "std_return": np.std(returns),
                    "min_return": np.min(returns),
                    "max_return": np.max(returns),
                    "success_rate": len([r for r in returns if r > 0]) / len(returns)
                }
        
        return scenario_performance
    
    def _calculate_black_swan_performance(self, simulation_results: List[Dict]) -> Dict:
        """
        Calculate performance metrics by black swan event
        
        Args:
            simulation_results: List of simulation results
            
        Returns:
            Dict containing performance metrics by black swan event
        """
        black_swan_performance = {}
        
        # Add "none" category for simulations without black swan events
        black_swan_events = [event["name"] for event in self.config.get("black_swan_events", [])] + ["none"]
        
        # Group results by black swan event
        for event_name in black_swan_events:
            if event_name == "none":
                event_results = [r for r in simulation_results if r["black_swan_event"] is None]
            else:
                event_results = [r for r in simulation_results if r["black_swan_event"] == event_name]
            
            if event_results:
                returns = [r["portfolio_return"] for r in event_results]
                
                black_swan_performance[event_name] = {
                    "count": len(event_results),
                    "mean_return": np.mean(returns),
                    "std_return": np.std(returns),
                    "min_return": np.min(returns),
                    "max_return": np.max(returns),
                    "success_rate": len([r for r in returns if r > 0]) / len(returns)
                }
        
        return black_swan_performance
    
    def _save_evaluation_results(self, strategy, evaluation_results: Dict):
        """
        Save evaluation results to file
        
        Args:
            strategy: Strategy that was evaluated
            evaluation_results: Evaluation results
        """
        # Create a unique identifier for the strategy
        strategy_name = getattr(strategy, "name", "unknown_strategy")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{strategy_name}_{timestamp}.json"
        
        # Save path
        save_path = os.path.join(self.config.get("results_dir", "results/world_model_simulator"), filename)
        
        # Save results
        with open(save_path, 'w') as f:
            # Create a copy without the full simulation results to save space
            save_results = evaluation_results.copy()
            save_results.pop("simulation_results", None)
            
            json.dump(save_results, f, indent=2)
        
        logger.info(f"Evaluation results saved to {save_path}")

class RandomStrategy:
    """A simple random strategy for testing the simulator"""
    
    def __init__(self, name: str = "RandomStrategy"):
        """
        Initialize the random strategy
        
        Args:
            name: Name of the strategy
        """
        self.name = name
    
    def get_action(self, observation):
        """
        Generate a random action
        
        Args:
            observation: Current observation from the environment
            
        Returns:
            Dict containing the action
        """
        return {
            "protocol": random.randint(0, 4),  # 5 protocols
            "action_type": random.randint(0, 4),  # 5 action types
            "asset1": random.randint(0, 8),  # 9 assets
            "asset2": random.randint(0, 8),  # 9 assets
            "amount_percentage": random.random()  # 0-1
        }

def main():
    """Main function"""
    # Initialize the World Model Simulator
    simulator = WorldModelSimulator()
    
    # Create a random strategy for testing
    strategy = RandomStrategy()
    
    # Evaluate the strategy
    evaluation_results = simulator.evaluate_strategy(strategy, num_simulations=10)
    
    print(json.dumps(evaluation_results, indent=2))

if __name__ == "__main__":
    main()