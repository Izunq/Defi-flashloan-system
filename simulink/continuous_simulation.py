#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Continuous Simulation Environment for Simulink Models

This module provides a framework for continuous simulation of Simulink models
with real-time data feeds, event handling, and performance monitoring. It enables
long-running simulations for testing trading strategies under various market conditions.

Author: DeFi Arbitrage System
Date: June 17, 2025
"""

import os
import time
import json
import logging
import threading
import numpy as np
import pandas as pd
from queue import Queue
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

# Import the Simulink bridge and market data connector
from simulink_bridge import SimulinkBridge, MarketData, TradingSignals
from market_data_connector import MarketDataConnector, create_default_market_data_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('continuous_simulation')


@dataclass
class SimulationEvent:
    """Event that can occur during simulation."""
    event_type: str
    timestamp: float
    data: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass
class SimulationConfig:
    """Configuration for continuous simulation."""
    model_name: str
    duration: int = 0  # seconds (0 = run indefinitely)
    data_source: str = "live"  # "live", "historical", or "synthetic"
    historical_data_path: str = ""
    output_dir: str = "simulation_results"
    sample_rate: int = 1  # Hz
    save_interval: int = 60  # seconds
    event_handlers: Dict[str, List[Callable]] = field(default_factory=dict)
    market_conditions: Dict[str, Any] = field(default_factory=dict)
    random_seed: int = 42
    simulation_speed: float = 1.0  # 1.0 = real-time, 2.0 = 2x speed, etc.


@dataclass
class SimulationState:
    """Current state of the simulation."""
    running: bool = False
    paused: bool = False
    current_time: float = 0.0
    start_time: float = 0.0
    elapsed_time: float = 0.0
    processed_samples: int = 0
    events: List[SimulationEvent] = field(default_factory=list)
    portfolio_value: float = 1000.0
    positions: Dict[str, float] = field(default_factory=dict)
    trades: List[Dict[str, Any]] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


class ContinuousSimulation:
    """Framework for continuous simulation of Simulink models."""
    
    def __init__(
        self, 
        simulink_bridge: SimulinkBridge,
        market_data_connector: MarketDataConnector,
        config: SimulationConfig
    ):
        """Initialize the continuous simulation environment.
        
        Args:
            simulink_bridge: Instance of SimulinkBridge for model execution
            market_data_connector: Instance of MarketDataConnector for market data
            config: Simulation configuration
        """
        self.simulink_bridge = simulink_bridge
        self.market_data_connector = market_data_connector
        self.config = config
        self.state = SimulationState()
        self.simulation_thread = None
        self.event_queue = Queue()
        self.data_buffer = []
        self.results_buffer = []
        
        # Create output directory if it doesn't exist
        os.makedirs(config.output_dir, exist_ok=True)
        
        # Register default event handlers
        self._register_default_event_handlers()
        
        logger.info(f"Initialized continuous simulation for model {config.model_name}")
    
    def _register_default_event_handlers(self):
        """Register default event handlers."""
        # Register handlers for common events
        self.register_event_handler("trade_executed", self._handle_trade_executed)
        self.register_event_handler("stop_loss_triggered", self._handle_stop_loss_triggered)
        self.register_event_handler("take_profit_triggered", self._handle_take_profit_triggered)
        self.register_event_handler("market_anomaly_detected", self._handle_market_anomaly)
        self.register_event_handler("performance_threshold_breached", self._handle_performance_breach)
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """Register an event handler.
        
        Args:
            event_type: Type of event to handle
            handler: Function to call when event occurs
        """
        if event_type not in self.config.event_handlers:
            self.config.event_handlers[event_type] = []
        
        self.config.event_handlers[event_type].append(handler)
        logger.debug(f"Registered handler for event type: {event_type}")
    
    def _handle_trade_executed(self, event: SimulationEvent):
        """Handle trade executed event.
        
        Args:
            event: Trade executed event
        """
        # Update portfolio and positions
        trade_data = event.data
        symbol = trade_data.get("symbol", "unknown")
        position_size = trade_data.get("position_size", 0.0)
        price = trade_data.get("price", 0.0)
        side = trade_data.get("side", "buy")
        
        # Update positions
        if side == "buy":
            self.state.positions[symbol] = self.state.positions.get(symbol, 0.0) + position_size
        else:
            self.state.positions[symbol] = self.state.positions.get(symbol, 0.0) - position_size
        
        # Add to trades list
        self.state.trades.append({
            "timestamp": event.timestamp,
            "symbol": symbol,
            "side": side,
            "price": price,
            "position_size": position_size,
            "value": price * position_size,
            "portfolio_value": self.state.portfolio_value
        })
        
        logger.info(f"Trade executed: {side} {position_size} {symbol} @ {price}")
    
    def _handle_stop_loss_triggered(self, event: SimulationEvent):
        """Handle stop loss triggered event.
        
        Args:
            event: Stop loss triggered event
        """
        trade_data = event.data
        symbol = trade_data.get("symbol", "unknown")
        price = trade_data.get("price", 0.0)
        position_size = trade_data.get("position_size", 0.0)
        loss = trade_data.get("loss", 0.0)
        
        # Update portfolio value
        self.state.portfolio_value += loss  # loss is negative
        
        # Update positions
        self.state.positions[symbol] = self.state.positions.get(symbol, 0.0) - position_size
        
        logger.info(f"Stop loss triggered for {symbol}: {loss:.2f} loss")
    
    def _handle_take_profit_triggered(self, event: SimulationEvent):
        """Handle take profit triggered event.
        
        Args:
            event: Take profit triggered event
        """
        trade_data = event.data
        symbol = trade_data.get("symbol", "unknown")
        price = trade_data.get("price", 0.0)
        position_size = trade_data.get("position_size", 0.0)
        profit = trade_data.get("profit", 0.0)
        
        # Update portfolio value
        self.state.portfolio_value += profit
        
        # Update positions
        self.state.positions[symbol] = self.state.positions.get(symbol, 0.0) - position_size
        
        logger.info(f"Take profit triggered for {symbol}: {profit:.2f} profit")
    
    def _handle_market_anomaly(self, event: SimulationEvent):
        """Handle market anomaly event.
        
        Args:
            event: Market anomaly event
        """
        anomaly_data = event.data
        anomaly_type = anomaly_data.get("type", "unknown")
        severity = anomaly_data.get("severity", 0.0)
        
        logger.warning(f"Market anomaly detected: {anomaly_type} (severity: {severity:.2f})")
        
        # If severe anomaly, reduce position sizes
        if severity > 0.8:
            logger.warning("Severe market anomaly detected, reducing positions")
            for symbol, position in self.state.positions.items():
                if position > 0:
                    # Create a trade executed event to reduce position
                    self.add_event(SimulationEvent(
                        event_type="trade_executed",
                        timestamp=self.state.current_time,
                        data={
                            "symbol": symbol,
                            "side": "sell",
                            "price": anomaly_data.get(f"{symbol}_price", 0.0),
                            "position_size": position * 0.5,  # Reduce by 50%
                            "reason": "market_anomaly"
                        },
                        description=f"Reducing {symbol} position due to market anomaly"
                    ))
    
    def _handle_performance_breach(self, event: SimulationEvent):
        """Handle performance threshold breach event.
        
        Args:
            event: Performance threshold breach event
        """
        performance_data = event.data
        metric = performance_data.get("metric", "unknown")
        value = performance_data.get("value", 0.0)
        threshold = performance_data.get("threshold", 0.0)
        
        logger.warning(f"Performance threshold breached: {metric} = {value:.2f} (threshold: {threshold:.2f})")
    
    def add_event(self, event: SimulationEvent):
        """Add an event to the simulation.
        
        Args:
            event: Event to add
        """
        self.event_queue.put(event)
    
    def _process_events(self):
        """Process events in the event queue."""
        while not self.event_queue.empty():
            event = self.event_queue.get()
            
            # Add to events list
            self.state.events.append(event)
            
            # Call event handlers
            if event.event_type in self.config.event_handlers:
                for handler in self.config.event_handlers[event.event_type]:
                    try:
                        handler(event)
                    except Exception as e:
                        logger.error(f"Error in event handler for {event.event_type}: {str(e)}")
            
            self.event_queue.task_done()
    
    def _load_historical_data(self) -> pd.DataFrame:
        """Load historical data for simulation.
        
        Returns:
            pd.DataFrame: Historical market data
        """
        try:
            # Check if file exists
            if not os.path.exists(self.config.historical_data_path):
                logger.error(f"Historical data file not found: {self.config.historical_data_path}")
                return pd.DataFrame()
            
            # Load data based on file extension
            file_ext = os.path.splitext(self.config.historical_data_path)[1].lower()
            
            if file_ext == '.csv':
                data = pd.read_csv(self.config.historical_data_path)
            elif file_ext == '.json':
                data = pd.read_json(self.config.historical_data_path)
            elif file_ext in ['.xls', '.xlsx']:
                data = pd.read_excel(self.config.historical_data_path)
            elif file_ext == '.parquet':
                data = pd.read_parquet(self.config.historical_data_path)
            else:
                logger.error(f"Unsupported file format: {file_ext}")
                return pd.DataFrame()
            
            logger.info(f"Loaded historical data with {len(data)} samples")
            return data
            
        except Exception as e:
            logger.error(f"Error loading historical data: {str(e)}")
            return pd.DataFrame()
    
    def _generate_synthetic_data(self, samples: int = 1000) -> pd.DataFrame:
        """Generate synthetic market data for simulation.
        
        Args:
            samples: Number of samples to generate
            
        Returns:
            pd.DataFrame: Synthetic market data
        """
        logger.info(f"Generating {samples} synthetic data samples")
        
        # Set random seed for reproducibility
        np.random.seed(self.config.random_seed)
        
        # Generate timestamps
        start_time = time.time()
        timestamps = [start_time + i * (1.0 / self.config.sample_rate) for i in range(samples)]
        
        # Generate price data with realistic patterns
        # Start with random walk
        eth_price = 2000.0
        btc_price = 40000.0
        uni_price = 10.0
        aave_price = 100.0
        
        eth_prices = []
        btc_prices = []
        uni_prices = []
        aave_prices = []
        
        # Generate correlated price movements
        for i in range(samples):
            # Add random walk
            eth_change = np.random.normal(0, 1.0) * 0.001 * eth_price
            btc_change = np.random.normal(0, 1.0) * 0.001 * btc_price
            uni_change = np.random.normal(0, 1.0) * 0.001 * uni_price
            aave_change = np.random.normal(0, 1.0) * 0.001 * aave_price
            
            # Add correlation between assets
            eth_btc_corr = 0.7
            eth_uni_corr = 0.5
            eth_aave_corr = 0.6
            
            btc_change += eth_change * eth_btc_corr
            uni_change += eth_change * eth_uni_corr
            aave_change += eth_change * eth_aave_corr
            
            # Add some volatility clusters
            if i > 0 and i % 100 == 0:
                volatility_spike = np.random.choice([1.0, 3.0, 5.0])
                eth_change *= volatility_spike
                btc_change *= volatility_spike
                uni_change *= volatility_spike
                aave_change *= volatility_spike
            
            # Update prices
            eth_price += eth_change
            btc_price += btc_change
            uni_price += uni_change
            aave_price += aave_change
            
            # Ensure prices stay positive
            eth_price = max(1000.0, eth_price)
            btc_price = max(20000.0, btc_price)
            uni_price = max(5.0, uni_price)
            aave_price = max(50.0, aave_price)
            
            # Store prices
            eth_prices.append(eth_price)
            btc_prices.append(btc_price)
            uni_prices.append(uni_price)
            aave_prices.append(aave_price)
        
        # Generate volume data
        eth_volumes = np.random.lognormal(mean=np.log(1000000), sigma=0.5, size=samples)
        btc_volumes = np.random.lognormal(mean=np.log(2000000), sigma=0.5, size=samples)
        uni_volumes = np.random.lognormal(mean=np.log(500000), sigma=0.5, size=samples)
        aave_volumes = np.random.lognormal(mean=np.log(300000), sigma=0.5, size=samples)
        
        # Generate gas prices
        gas_fast = np.random.normal(50, 10, samples)
        gas_standard = np.random.normal(30, 5, samples)
        gas_slow = np.random.normal(20, 3, samples)
        
        # Ensure gas prices are positive and properly ordered
        for i in range(samples):
            gas_fast[i] = max(10.0, gas_fast[i])
            gas_standard[i] = max(5.0, min(gas_fast[i] - 5.0, gas_standard[i]))
            gas_slow[i] = max(1.0, min(gas_standard[i] - 2.0, gas_slow[i]))
        
        # Create DataFrame
        data = pd.DataFrame({
            'timestamp': timestamps,
            'eth_price': eth_prices,
            'btc_price': btc_prices,
            'uni_price': uni_prices,
            'aave_price': aave_prices,
            'eth_volume': eth_volumes,
            'btc_volume': btc_volumes,
            'uni_volume': uni_volumes,
            'aave_volume': aave_volumes,
            'gas_price_fast': gas_fast,
            'gas_price_standard': gas_standard,
            'gas_price_slow': gas_slow,
            'network_congestion': gas_fast / 100.0,  # Normalized 0-1
            'block_time': np.random.normal(12, 1, samples)  # Ethereum block time
        })
        
        # Add some arbitrage opportunities
        # Every 50 samples, create a price discrepancy between exchanges
        for i in range(0, samples, 50):
            if i + 10 < samples:
                # Create price discrepancy for ETH
                data.loc[i:i+10, 'eth_price_binance'] = data.loc[i:i+10, 'eth_price'] * (1 + 0.005)
                data.loc[i:i+10, 'eth_price_coinbase'] = data.loc[i:i+10, 'eth_price'] * (1 - 0.003)
                
                # Create price discrepancy for BTC
                data.loc[i+20:i+30, 'btc_price_binance'] = data.loc[i+20:i+30, 'btc_price'] * (1 + 0.004)
                data.loc[i+20:i+30, 'btc_price_coinbase'] = data.loc[i+20:i+30, 'btc_price'] * (1 - 0.002)
        
        logger.info(f"Generated synthetic data with {len(data)} samples")
        return data
    
    def _get_market_data(self) -> Optional[MarketData]:
        """Get market data for the current simulation step.
        
        Returns:
            Optional[MarketData]: Market data for the current step
        """
        if self.config.data_source == "live":
            # Get live market data
            return self.market_data_connector.get_latest_market_data()
        
        elif self.config.data_source == "historical":
            # Get historical data for the current time
            if not hasattr(self, '_historical_data'):
                self._historical_data = self._load_historical_data()
                if self._historical_data.empty:
                    logger.error("Failed to load historical data")
                    return None
            
            # Find the closest timestamp
            current_time = self.state.start_time + self.state.elapsed_time * self.config.simulation_speed
            idx = self._historical_data['timestamp'].searchsorted(current_time)
            if idx >= len(self._historical_data):
                logger.warning("Reached end of historical data")
                return None
            
            row = self._historical_data.iloc[idx]
            
            # Create MarketData object
            return MarketData(
                timestamp=row['timestamp'],
                prices={k: v for k, v in row.items() if 'price' in k},
                volumes={k: v for k, v in row.items() if 'volume' in k},
                gas_prices={
                    'fast': row['gas_price_fast'],
                    'standard': row['gas_price_standard'],
                    'slow': row['gas_price_slow']
                },
                additional_data={
                    'network_congestion': row['network_congestion'],
                    'block_time': row['block_time']
                }
            )
        
        elif self.config.data_source == "synthetic":
            # Generate synthetic data if not already generated
            if not hasattr(self, '_synthetic_data'):
                # Generate enough data for the simulation duration
                samples = self.config.duration * self.config.sample_rate
                if samples <= 0:
                    samples = 24 * 60 * 60 * self.config.sample_rate  # 24 hours
                
                self._synthetic_data = self._generate_synthetic_data(samples=samples)
                if self._synthetic_data.empty:
                    logger.error("Failed to generate synthetic data")
                    return None
            
            # Get data for the current time
            elapsed_seconds = int(self.state.elapsed_time * self.config.simulation_speed)
            idx = elapsed_seconds * self.config.sample_rate
            
            if idx >= len(self._synthetic_data):
                logger.warning("Reached end of synthetic data")
                return None
            
            row = self._synthetic_data.iloc[idx]
            
            # Create MarketData object
            return MarketData(
                timestamp=row['timestamp'],
                prices={k: v for k, v in row.items() if 'price' in k},
                volumes={k: v for k, v in row.items() if 'volume' in k},
                gas_prices={
                    'fast': row['gas_price_fast'],
                    'standard': row['gas_price_standard'],
                    'slow': row['gas_price_slow']
                },
                additional_data={
                    'network_congestion': row['network_congestion'],
                    'block_time': row['block_time']
                }
            )
        
        else:
            logger.error(f"Unknown data source: {self.config.data_source}")
            return None
    
    def _update_performance_metrics(self):
        """Update performance metrics for the simulation."""
        # Calculate performance metrics
        if not self.state.trades:
            return
        
        # Calculate returns
        returns = []
        for i in range(1, len(self.state.trades)):
            prev_value = self.state.trades[i-1]["portfolio_value"]
            curr_value = self.state.trades[i]["portfolio_value"]
            if prev_value > 0:
                returns.append((curr_value - prev_value) / prev_value)
        
        if not returns:
            return
        
        # Calculate metrics
        total_return = (self.state.portfolio_value / 1000.0) - 1.0
        win_count = sum(1 for r in returns if r > 0)
        loss_count = sum(1 for r in returns if r < 0)
        win_rate = win_count / len(returns) if returns else 0.0
        
        # Calculate drawdown
        peak = 1000.0
        drawdowns = []
        for trade in self.state.trades:
            value = trade["portfolio_value"]
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak if peak > 0 else 0.0
            drawdowns.append(drawdown)
        
        max_drawdown = max(drawdowns) if drawdowns else 0.0
        
        # Update metrics
        self.state.performance_metrics = {
            "total_return": total_return,
            "annualized_return": total_return * (365 * 24 * 60 * 60) / max(1, self.state.elapsed_time),
            "win_rate": win_rate,
            "trade_count": len(self.state.trades),
            "max_drawdown": max_drawdown,
            "sharpe_ratio": np.mean(returns) / np.std(returns) * np.sqrt(365) if np.std(returns) > 0 else 0.0,
            "volatility": np.std(returns) * np.sqrt(365) if returns else 0.0
        }
    
    def _save_simulation_state(self):
        """Save the current simulation state to file."""
        # Create output directory if it doesn't exist
        os.makedirs(self.config.output_dir, exist_ok=True)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.config.model_name}_simulation_{timestamp}.json"
        filepath = os.path.join(self.config.output_dir, filename)
        
        # Prepare data to save
        save_data = {
            "model_name": self.config.model_name,
            "timestamp": time.time(),
            "elapsed_time": self.state.elapsed_time,
            "processed_samples": self.state.processed_samples,
            "portfolio_value": self.state.portfolio_value,
            "positions": self.state.positions,
            "trades": self.state.trades[-100:],  # Save only the last 100 trades
            "performance_metrics": self.state.performance_metrics,
            "events": [
                {
                    "event_type": e.event_type,
                    "timestamp": e.timestamp,
                    "description": e.description
                }
                for e in self.state.events[-100:]  # Save only the last 100 events
            ]
        }
        
        # Save to file
        with open(filepath, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        logger.info(f"Saved simulation state to {filepath}")
    
    def _simulation_loop(self):
        """Main simulation loop."""
        logger.info(f"Starting simulation for model {self.config.model_name}")
        
        # Initialize simulation state
        self.state.running = True
        self.state.paused = False
        self.state.start_time = time.time()
        self.state.current_time = self.state.start_time
        self.state.elapsed_time = 0.0
        self.state.processed_samples = 0
        
        # Load the model
        if not self.simulink_bridge.load_model(self.config.model_name):
            logger.error(f"Failed to load model {self.config.model_name}")
            self.state.running = False
            return
        
        # Start real-time simulation
        if not self.simulink_bridge.start_real_time_simulation(self.config.model_name):
            logger.error(f"Failed to start real-time simulation for model {self.config.model_name}")
            self.state.running = False
            return
        
        # Start market data connector if using live data
        if self.config.data_source == "live":
            self.market_data_connector.start()
        
        # Calculate sleep time based on sample rate and simulation speed
        sleep_time = 1.0 / (self.config.sample_rate * self.config.simulation_speed)
        
        # Last save time
        last_save_time = time.time()
        
        try:
            # Main simulation loop
            while self.state.running:
                loop_start_time = time.time()
                
                # Skip if paused
                if self.state.paused:
                    time.sleep(0.1)
                    continue
                
                # Check if simulation duration has been reached
                if self.config.duration > 0 and self.state.elapsed_time >= self.config.duration:
                    logger.info(f"Simulation duration reached: {self.config.duration} seconds")
                    break
                
                # Process events
                self._process_events()
                
                # Get market data
                market_data = self._get_market_data()
                if market_data is None:
                    logger.warning("Failed to get market data")
                    time.sleep(sleep_time)
                    continue
                
                # Store data for analysis
                self.data_buffer.append(market_data)
                if len(self.data_buffer) > 1000:
                    self.data_buffer.pop(0)
                
                # Process through model
                trading_signals = self.simulink_bridge.process_market_data(market_data)
                
                if trading_signals:
                    # Store results for analysis
                    result = {
                        "timestamp": market_data.timestamp,
                        "eth_price": market_data.prices.get("eth_price", 0.0),
                        "btc_price": market_data.prices.get("btc_price", 0.0),
                        "gas_price_fast": market_data.gas_prices.get("fast", 0.0),
                        "execute_trade": trading_signals.execute_trade,
                        "position_size": trading_signals.position_size,
                        "target_price": trading_signals.target_price,
                        "stop_loss": trading_signals.stop_loss,
                        "confidence": trading_signals.confidence
                    }
                    
                    self.results_buffer.append(result)
                    if len(self.results_buffer) > 1000:
                        self.results_buffer.pop(0)
                    
                    # Check if trade should be executed
                    if trading_signals.execute_trade:
                        # Determine which asset to trade based on highest confidence
                        # For simplicity, we'll just use ETH
                        symbol = "eth"
                        price = market_data.prices.get("eth_price", 0.0)
                        
                        # Create trade executed event
                        self.add_event(SimulationEvent(
                            event_type="trade_executed",
                            timestamp=market_data.timestamp,
                            data={
                                "symbol": symbol,
                                "side": "buy",
                                "price": price,
                                "position_size": trading_signals.position_size,
                                "target_price": trading_signals.target_price,
                                "stop_loss": trading_signals.stop_loss,
                                "confidence": trading_signals.confidence
                            },
                            description=f"Executed trade: buy {trading_signals.position_size} {symbol} @ {price}"
                        ))
                
                # Update simulation state
                self.state.current_time = time.time()
                self.state.elapsed_time = self.state.current_time - self.state.start_time
                self.state.processed_samples += 1
                
                # Update performance metrics
                self._update_performance_metrics()
                
                # Save simulation state periodically
                if time.time() - last_save_time > self.config.save_interval:
                    self._save_simulation_state()
                    last_save_time = time.time()
                
                # Sleep to maintain sample rate
                execution_time = time.time() - loop_start_time
                sleep_duration = max(0, sleep_time - execution_time)
                if sleep_duration > 0:
                    time.sleep(sleep_duration)
                else:
                    logger.warning(f"Execution time ({execution_time:.4f} s) exceeds "
                                  f"sampling period ({sleep_time:.4f} s)")
        
        except Exception as e:
            logger.error(f"Error in simulation loop: {str(e)}")
        
        finally:
            # Stop real-time simulation
            self.simulink_bridge.stop_real_time_simulation(self.config.model_name)
            
            # Stop market data connector if using live data
            if self.config.data_source == "live":
                self.market_data_connector.stop()
            
            # Save final simulation state
            self._save_simulation_state()
            
            # Update simulation state
            self.state.running = False
            
            logger.info("Simulation completed")
    
    def start(self) -> bool:
        """Start the simulation.
        
        Returns:
            bool: True if simulation started successfully, False otherwise
        """
        if self.state.running:
            logger.warning("Simulation is already running")
            return False
        
        # Start simulation thread
        self.simulation_thread = threading.Thread(target=self._simulation_loop)
        self.simulation_thread.daemon = True
        self.simulation_thread.start()
        
        logger.info(f"Started simulation for model {self.config.model_name}")
        return True
    
    def stop(self) -> bool:
        """Stop the simulation.
        
        Returns:
            bool: True if simulation stopped successfully, False otherwise
        """
        if not self.state.running:
            logger.warning("Simulation is not running")
            return False
        
        # Stop the simulation
        self.state.running = False
        
        # Wait for simulation thread to terminate
        if self.simulation_thread and self.simulation_thread.is_alive():
            self.simulation_thread.join(timeout=10.0)
            if self.simulation_thread.is_alive():
                logger.warning("Simulation thread did not terminate gracefully")
        
        self.simulation_thread = None
        
        logger.info("Stopped simulation")
        return True
    
    def pause(self) -> bool:
        """Pause the simulation.
        
        Returns:
            bool: True if simulation paused successfully, False otherwise
        """
        if not self.state.running:
            logger.warning("Simulation is not running")
            return False
        
        if self.state.paused:
            logger.warning("Simulation is already paused")
            return False
        
        self.state.paused = True
        logger.info("Paused simulation")
        return True
    
    def resume(self) -> bool:
        """Resume the simulation.
        
        Returns:
            bool: True if simulation resumed successfully, False otherwise
        """
        if not self.state.running:
            logger.warning("Simulation is not running")
            return False
        
        if not self.state.paused:
            logger.warning("Simulation is not paused")
            return False
        
        self.state.paused = False
        logger.info("Resumed simulation")
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the simulation.
        
        Returns:
            Dict[str, Any]: Current simulation status
        """
        return {
            "running": self.state.running,
            "paused": self.state.paused,
            "elapsed_time": self.state.elapsed_time,
            "processed_samples": self.state.processed_samples,
            "portfolio_value": self.state.portfolio_value,
            "positions": self.state.positions,
            "trade_count": len(self.state.trades),
            "event_count": len(self.state.events),
            "performance_metrics": self.state.performance_metrics
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get a performance report for the simulation.
        
        Returns:
            Dict[str, Any]: Performance report
        """
        # Update performance metrics
        self._update_performance_metrics()
        
        # Create report
        report = {
            "model_name": self.config.model_name,
            "data_source": self.config.data_source,
            "elapsed_time": self.state.elapsed_time,
            "processed_samples": self.state.processed_samples,
            "portfolio_value": self.state.portfolio_value,
            "initial_value": 1000.0,
            "total_return": self.state.performance_metrics.get("total_return", 0.0),
            "annualized_return": self.state.performance_metrics.get("annualized_return", 0.0),
            "win_rate": self.state.performance_metrics.get("win_rate", 0.0),
            "trade_count": self.state.performance_metrics.get("trade_count", 0),
            "max_drawdown": self.state.performance_metrics.get("max_drawdown", 0.0),
            "sharpe_ratio": self.state.performance_metrics.get("sharpe_ratio", 0.0),
            "volatility": self.state.performance_metrics.get("volatility", 0.0),
            "positions": self.state.positions,
            "recent_trades": self.state.trades[-10:],  # Last 10 trades
            "recent_events": [
                {
                    "event_type": e.event_type,
                    "timestamp": e.timestamp,
                    "description": e.description
                }
                for e in self.state.events[-10:]  # Last 10 events
            ]
        }
        
        return report


def create_default_simulation_config(model_name: str) -> SimulationConfig:
    """Create a default simulation configuration.
    
    Args:
        model_name: Name of the model to simulate
        
    Returns:
        SimulationConfig: Default simulation configuration
    """
    # Create output directory
    output_dir = os.path.join("simulink", "simulation_results", model_name)
    os.makedirs(output_dir, exist_ok=True)
    
    return SimulationConfig(
        model_name=model_name,
        duration=3600,  # 1 hour
        data_source="synthetic",  # Use synthetic data by default
        historical_data_path="",
        output_dir=output_dir,
        sample_rate=1,  # 1 Hz
        save_interval=60,  # Save every 60 seconds
        event_handlers={},
        market_conditions={},
        random_seed=42,
        simulation_speed=1.0  # Real-time
    )


def main():
    """Run a demo of the continuous simulation environment."""
    from simulink_bridge import SimulinkBridge
    from market_data_connector import MarketDataConnector, create_default_market_data_config
    
    # Create Simulink bridge
    bridge = SimulinkBridge()
    
    # Create market data connector
    market_config = create_default_market_data_config()
    market_connector = MarketDataConnector(market_config)
    
    # Create simulation configuration
    config = create_default_simulation_config("Arbitrage_Strategy_Model")
    config.duration = 300  # 5 minutes
    config.data_source = "synthetic"
    config.simulation_speed = 10.0  # 10x speed
    
    # Create continuous simulation
    simulation = ContinuousSimulation(bridge, market_connector, config)
    
    try:
        # Start simulation
        print("Starting simulation...")
        simulation.start()
        
        # Wait for simulation to complete
        while simulation.state.running:
            status = simulation.get_status()
            print(f"\rElapsed: {status['elapsed_time']:.1f}s | "
                  f"Portfolio: ${status['portfolio_value']:.2f} | "
                  f"Trades: {status['trade_count']} | "
                  f"Events: {status['event_count']}", end="")
            time.sleep(1.0)
        
        # Print final report
        report = simulation.get_performance_report()
        
        print("\n\nSimulation Complete!")
        print(f"Model: {report['model_name']}")
        print(f"Duration: {report['elapsed_time']:.1f} seconds")
        print(f"Portfolio Value: ${report['portfolio_value']:.2f}")
        print(f"Total Return: {report['total_return']:.2%}")
        print(f"Win Rate: {report['win_rate']:.2%}")
        print(f"Trade Count: {report['trade_count']}")
        print(f"Max Drawdown: {report['max_drawdown']:.2%}")
        print(f"Sharpe Ratio: {report['sharpe_ratio']:.2f}")
        
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user")
        simulation.stop()
    except Exception as e:
        print(f"\nError during simulation: {str(e)}")
        simulation.stop()


if __name__ == "__main__":
    main()