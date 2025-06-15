#!/usr/bin/env python3
"""
Strategy Simulation Engine Launcher
This script launches the strategy simulation engine with the specified configuration.
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from strategy_simulation_engine import StrategySimulationEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Strategy Simulation Engine Launcher')
    
    parser.add_argument('--config', type=str, default='simulation_config.json',
                        help='Path to simulation configuration file')
    
    parser.add_argument('--mode', type=str, choices=['simulate', 'optimize', 'backtest'],
                        default='simulate', help='Simulation mode')
    
    parser.add_argument('--strategy', type=str,
                        choices=['flash_arbitrage_v2', 'cross_chain_arbitrage', 'stable_swap_optimizer'],
                        default='flash_arbitrage_v2', help='Strategy type')
    
    parser.add_argument('--capital', type=float, default=100000,
                        help='Initial capital for simulation')
    
    parser.add_argument('--output-dir', type=str, default='./simulation_results',
                        help='Directory for output files')
    
    parser.add_argument('--generate-charts', action='store_true',
                        help='Generate charts for simulation results')
    
    parser.add_argument('--save-results', action='store_true',
                        help='Save simulation results to file')
    
    return parser.parse_args()

def load_config(config_path):
    """Load configuration from file"""
    if not os.path.exists(config_path):
        logger.warning(f"Configuration file {config_path} not found. Using default configuration.")
        return {}
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        logger.info(f"Loaded configuration from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return {}

def create_strategy_config(args, config):
    """Create strategy configuration"""
    # Start with default strategy config
    strategy_config = {
        'name': f"{args.strategy}_simulation",
        'type': args.strategy,
        'capital': args.capital,
        'fee': 0.003,
        'slippage': 0.001,
        'gas_price_gwei': 50
    }
    
    # Override with config file values if present
    if 'strategy_config' in config:
        for key, value in config['strategy_config'].items():
            strategy_config[key] = value
    
    return strategy_config

def main():
    """Main function"""
    # Parse arguments
    args = parse_arguments()
    
    # Load configuration
    config = load_config(args.config)
    
    # Update configuration with command line arguments
    if 'reporting' not in config:
        config['reporting'] = {}
    
    config['reporting']['output_dir'] = args.output_dir
    config['reporting']['generate_charts'] = args.generate_charts
    config['reporting']['save_results'] = args.save_results
    
    # Create strategy configuration
    strategy_config = create_strategy_config(args, config)
    
    # Initialize simulation engine
    engine = StrategySimulationEngine(config_path=args.config)
    
    # Run simulation or optimization
    if args.mode == 'simulate':
        logger.info(f"Starting simulation for strategy: {strategy_config['name']}")
        results = engine.simulate_strategy(strategy_config)
        
        # Print results
        logger.info(f"Simulation Results:")
        logger.info(f"Total Profit: ${results['results']['total_profit']:.2f}")
        logger.info(f"Total Trades: {results['results']['total_trades']}")
        logger.info(f"Sharpe Ratio: {results['metrics']['sharpe_ratio']:.2f}")
        logger.info(f"Win Rate: {results['metrics']['win_rate']*100:.2f}%")
    
    elif args.mode == 'optimize':
        logger.info(f"Starting optimization for strategy: {strategy_config['name']}")
        results = engine.optimize_strategy(strategy_config)
        
        # Print results
        logger.info(f"Optimization Results:")
        logger.info(f"Best Parameters: {results['results']['best_params']}")
        logger.info(f"Best Metric: {results['results']['best_metric']:.4f}")
    
    elif args.mode == 'backtest':
        logger.info(f"Starting backtest for strategy: {strategy_config['name']}")
        # Backtest is just a simulation with historical data
        results = engine.simulate_strategy(strategy_config)
        
        # Print results
        logger.info(f"Backtest Results:")
        logger.info(f"Total Profit: ${results['results']['total_profit']:.2f}")
        logger.info(f"Total Trades: {results['results']['total_trades']}")
        logger.info(f"Sharpe Ratio: {results['metrics']['sharpe_ratio']:.2f}")
        logger.info(f"Win Rate: {results['metrics']['win_rate']*100:.2f}%")
    
    logger.info("Simulation completed successfully")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(f"Error in simulation: {e}")
        sys.exit(1)