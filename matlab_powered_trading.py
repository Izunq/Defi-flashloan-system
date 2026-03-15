#!/usr/bin/env python3
"""
MATLAB-Powered Arbitrage Trading System
Integrates MATLAB-style analytics with real-time trading capabilities
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import time
from pathlib import Path
import asyncio
import aiohttp
import subprocess

class MATLABPoweredArbitrageSystem:
    def __init__(self):
        self.results_dir = Path("matlab_trading_system")
        self.results_dir.mkdir(exist_ok=True)
        
        # Strategy parameters (MATLAB-optimized)
        self.strategy_params = {
            'statistical': {
                'lookback_window': 30,
                'entry_threshold': 2.0,
                'exit_threshold': 0.5,
                'position_size': 1000  # USD
            },
            'momentum': {
                'short_window': 5,
                'long_window': 20,
                'momentum_threshold': 1.5,
                'position_size': 800
            },
            'volatility': {
                'vol_window': 20,
                'position_multiplier': 0.5,
                'min_liquidity': 0.6,
                'base_position': 1200
            }
        }
        
        # Trading state
        self.active_positions = {}
        self.signal_history = []
        self.performance_metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0,
            'current_drawdown': 0.0
        }
        
        print("MATLAB-Powered Arbitrage Trading System Initialized")
        print(f"Strategy Parameters Loaded: {len(self.strategy_params)} strategies")

    def generate_market_simulation_data(self):
        """Generate realistic real-time market simulation"""
        np.random.seed(int(time.time()) % 1000)  # Dynamic seed
        
        # Current market conditions
        current_time = datetime.now()
        
        # Simulate different market regimes based on time
        hour = current_time.hour
        if 6 <= hour <= 10:  # Morning volatility
            volatility_multiplier = 1.5
            spread_multiplier = 1.3
        elif 14 <= hour <= 16:  # Afternoon trading
            volatility_multiplier = 1.2
            spread_multiplier = 1.1
        elif 20 <= hour <= 22:  # Evening activity
            volatility_multiplier = 1.4
            spread_multiplier = 1.2
        else:  # Quiet periods
            volatility_multiplier = 0.8
            spread_multiplier = 0.9
        
        # Generate opportunity
        base_spread = 0.003 * spread_multiplier
        price_spread = max(0.0001, base_spread + np.random.normal(0, base_spread * 0.3))
        
        volatility = max(0.005, 0.015 * volatility_multiplier + np.random.exponential(0.01))
        
        # Gas costs vary with network congestion
        base_gas = 0.01
        gas_multiplier = 1 + np.random.exponential(0.5)  # Occasional spikes
        gas_cost = base_gas * gas_multiplier
        
        # Liquidity varies
        liquidity_score = min(1.0, max(0.2, np.random.beta(2.5, 2) + np.random.normal(0, 0.1)))
        
        # Calculate profit potential
        gross_profit = price_spread * 10000
        net_profit = gross_profit - gas_cost * 1000
        final_profit = net_profit * liquidity_score + np.random.normal(0, 1.0)
        
        opportunity = {
            'timestamp': current_time,
            'price_spread': price_spread,
            'volatility': volatility,
            'gas_cost': gas_cost,
            'liquidity_score': liquidity_score,
            'profit_potential': final_profit,
            'market_regime': hour,
            'network_congestion': gas_multiplier
        }
        
        return opportunity

    def matlab_statistical_signal(self, market_history):
        """MATLAB-style statistical arbitrage signal"""
        if len(market_history) < self.strategy_params['statistical']['lookback_window']:
            return {'signal': 0, 'confidence': 0, 'reason': 'Insufficient data'}
        
        # Extract price spreads
        spreads = [m['price_spread'] for m in market_history]
        window = self.strategy_params['statistical']['lookback_window']
        
        # Rolling statistics
        recent_spreads = spreads[-window:]
        spread_mean = np.mean(recent_spreads)
        spread_std = np.std(recent_spreads)
        
        if spread_std == 0:
            return {'signal': 0, 'confidence': 0, 'reason': 'No volatility'}
        
        # Z-score of current spread
        current_spread = spreads[-1]
        z_score = (current_spread - spread_mean) / spread_std
        
        # Generate signal
        entry_threshold = self.strategy_params['statistical']['entry_threshold']
        
        if z_score > entry_threshold:
            signal = -1  # Short - expect mean reversion
            confidence = min(1.0, abs(z_score) / 3.0)
            reason = f"Overpriced (Z={z_score:.2f})"
        elif z_score < -entry_threshold:
            signal = 1   # Long - expect mean reversion
            confidence = min(1.0, abs(z_score) / 3.0)
            reason = f"Underpriced (Z={z_score:.2f})"
        else:
            signal = 0
            confidence = 0
            reason = f"Within range (Z={z_score:.2f})"
        
        return {
            'signal': signal,
            'confidence': confidence,
            'reason': reason,
            'z_score': z_score,
            'spread_mean': spread_mean,
            'spread_std': spread_std
        }

    def matlab_momentum_signal(self, market_history):
        """MATLAB-style momentum arbitrage signal"""
        if len(market_history) < self.strategy_params['momentum']['long_window']:
            return {'signal': 0, 'confidence': 0, 'reason': 'Insufficient data'}
        
        # Extract spreads and volatility
        spreads = [m['price_spread'] for m in market_history]
        volatilities = [m['volatility'] for m in market_history]
        
        short_window = self.strategy_params['momentum']['short_window']
        long_window = self.strategy_params['momentum']['long_window']
        
        # Moving averages
        short_ma = np.mean(spreads[-short_window:])
        long_ma = np.mean(spreads[-long_window:])
        
        # Momentum
        momentum = short_ma - long_ma
        momentum_std = np.std([spreads[i] - spreads[i-1] for i in range(1, len(spreads))])
        
        if momentum_std == 0:
            return {'signal': 0, 'confidence': 0, 'reason': 'No momentum'}
        
        momentum_z = momentum / (momentum_std + 1e-8)
        
        # Volatility filter - only trade in high volatility
        vol_threshold = np.percentile(volatilities[-long_window:], 70)
        current_vol = volatilities[-1]
        
        threshold = self.strategy_params['momentum']['momentum_threshold']
        
        if current_vol > vol_threshold:
            if momentum_z > threshold:
                signal = 1
                confidence = min(1.0, float(abs(momentum_z)) / 3.0)
                reason = f"Momentum Up (Z={momentum_z:.2f})"
            elif momentum_z < -threshold:
                signal = -1
                confidence = min(1.0, float(abs(momentum_z)) / 3.0)
                reason = f"Momentum Down (Z={momentum_z:.2f})"
            else:
                signal = 0
                confidence = 0
                reason = f"Weak momentum (Z={momentum_z:.2f})"
        else:
            signal = 0
            confidence = 0
            reason = "Low volatility regime"
        
        return {
            'signal': signal,
            'confidence': confidence,
            'reason': reason,
            'momentum': momentum,
            'momentum_z': momentum_z,
            'volatility_filter': current_vol > vol_threshold
        }

    def matlab_volatility_signal(self, market_history):
        """MATLAB-style volatility-adjusted signal"""
        if len(market_history) < self.strategy_params['volatility']['vol_window']:
            return {'signal': 0, 'confidence': 0, 'reason': 'Insufficient data'}
        
        # Extract data
        profits = [m['profit_potential'] for m in market_history]
        volatilities = [m['volatility'] for m in market_history]
        liquidities = [m['liquidity_score'] for m in market_history]
        
        current_profit = profits[-1]
        current_liquidity = liquidities[-1]
        
        # Volatility adjustment
        vol_window = self.strategy_params['volatility']['vol_window']
        vol_mean = np.mean(volatilities[-vol_window:])
        vol_std = np.std(volatilities[-vol_window:])
        
        current_vol = volatilities[-1]
        vol_z = (current_vol - vol_mean) / (vol_std + 1e-8)
        
        # Position size adjustment
        vol_adjustment = 1.0 / (1 + abs(vol_z) * 0.3)  # Reduce size in high vol
        
        # Opportunity filter
        min_liquidity = self.strategy_params['volatility']['min_liquidity']
        
        if current_profit > 0 and current_liquidity > min_liquidity:
            signal = vol_adjustment  # Proportional signal
            confidence = min(1.0, current_liquidity)
            reason = f"Profitable opportunity (Adj={vol_adjustment:.2f})"
        else:
            signal = 0
            confidence = 0
            reason = "Poor opportunity"
        
        return {
            'signal': signal,
            'confidence': confidence,
            'reason': reason,
            'vol_adjustment': vol_adjustment,
            'vol_z': vol_z,
            'liquidity_ok': current_liquidity > min_liquidity
        }

    def generate_combined_trading_signal(self, market_history):
        """Combine all MATLAB-style signals"""
        # Get individual signals
        stat_signal = self.matlab_statistical_signal(market_history)
        momentum_signal = self.matlab_momentum_signal(market_history)
        vol_signal = self.matlab_volatility_signal(market_history)
        
        # Weighted combination
        stat_weight = 0.4
        momentum_weight = 0.3
        vol_weight = 0.3
        
        combined_signal = (
            stat_signal['signal'] * stat_signal['confidence'] * stat_weight +
            momentum_signal['signal'] * momentum_signal['confidence'] * momentum_weight +
            vol_signal['signal'] * vol_signal['confidence'] * vol_weight
        )
        
        combined_confidence = (
            stat_signal['confidence'] * stat_weight +
            momentum_signal['confidence'] * momentum_weight +
            vol_signal['confidence'] * vol_weight
        )
        
        # Trading decision
        signal_threshold = 0.3
        confidence_threshold = 0.4
        
        if abs(combined_signal) > signal_threshold and combined_confidence > confidence_threshold:
            if combined_signal > 0:
                action = "BUY"
                strength = "STRONG" if combined_confidence > 0.7 else "MODERATE"
            else:
                action = "SELL"
                strength = "STRONG" if combined_confidence > 0.7 else "MODERATE"
        else:
            action = "HOLD"
            strength = "WEAK"
        
        return {
            'timestamp': datetime.now(),
            'action': action,
            'strength': strength,
            'signal_value': combined_signal,
            'confidence': combined_confidence,
            'components': {
                'statistical': stat_signal,
                'momentum': momentum_signal,
                'volatility': vol_signal
            },
            'market_data': market_history[-1] if market_history else None
        }

    def execute_trading_simulation(self, trading_signal):
        """Simulate trade execution"""
        if trading_signal['action'] == 'HOLD':
            return None
        
        market_data = trading_signal['market_data']
        signal_strength = trading_signal['confidence']
        
        # Position sizing based on signal strength
        base_size = 1000  # USD
        position_size = base_size * signal_strength
        
        # Estimate execution
        expected_profit = market_data['profit_potential'] * (position_size / 1000)
        gas_cost = market_data['gas_cost'] * (position_size / 1000)
        
        # Slippage and execution costs
        slippage = np.random.normal(0, 0.02) * expected_profit
        net_pnl = expected_profit - gas_cost + slippage
        
        trade = {
            'timestamp': trading_signal['timestamp'],
            'action': trading_signal['action'],
            'position_size': position_size,
            'expected_profit': expected_profit,
            'gas_cost': gas_cost,
            'slippage': slippage,
            'net_pnl': net_pnl,
            'signal_confidence': signal_strength
        }
        
        # Update performance metrics
        self.performance_metrics['total_trades'] += 1
        if net_pnl > 0:
            self.performance_metrics['winning_trades'] += 1
        
        self.performance_metrics['total_pnl'] += net_pnl
        
        # Update drawdown
        if net_pnl < 0:
            self.performance_metrics['current_drawdown'] += abs(net_pnl)
        else:
            self.performance_metrics['current_drawdown'] = max(0, 
                self.performance_metrics['current_drawdown'] - net_pnl)
        
        self.performance_metrics['max_drawdown'] = max(
            self.performance_metrics['max_drawdown'],
            self.performance_metrics['current_drawdown']
        )
        
        return trade

    def run_live_trading_simulation(self, duration_minutes=10):
        """Run live trading simulation with MATLAB-powered strategies"""
        print(f"\n{'='*60}")
        print("MATLAB-POWERED LIVE ARBITRAGE TRADING SIMULATION")
        print("="*60)
        
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        market_history = []
        trades_executed = []
        
        print(f"Simulation Period: {duration_minutes} minutes")
        print(f"Start Time: {start_time.strftime('%H:%M:%S')}")
        print(f"Strategy Components: Statistical, Momentum, Volatility")
        
        iteration = 0
        
        while datetime.now() < end_time:
            iteration += 1
            
            # Generate market opportunity
            market_data = self.generate_market_simulation_data()
            market_history.append(market_data)
            
            # Keep history manageable
            if len(market_history) > 100:
                market_history = market_history[-50:]
            
            # Generate trading signal
            if len(market_history) >= 20:  # Minimum data for signals
                trading_signal = self.generate_combined_trading_signal(market_history)
                self.signal_history.append(trading_signal)
                
                # Execute trade if signal is strong enough
                trade = self.execute_trading_simulation(trading_signal)
                if trade:
                    trades_executed.append(trade)
                    
                    print(f"\\n[{datetime.now().strftime('%H:%M:%S')}] TRADE #{len(trades_executed)}:")
                    print(f"  Action: {trade['action']} | Size: ${trade['position_size']:.0f}")
                    print(f"  Expected: ${trade['expected_profit']:.2f} | Gas: ${trade['gas_cost']:.2f}")
                    print(f"  Net P&L: ${trade['net_pnl']:.2f} | Confidence: {trade['signal_confidence']:.1%}")
                
                # Periodic status update
                if iteration % 20 == 0:
                    win_rate = (self.performance_metrics['winning_trades'] / 
                              max(1, self.performance_metrics['total_trades']))
                    
                    print(f"\\n[STATUS] Iteration {iteration}")
                    print(f"  Signal: {trading_signal['action']} ({trading_signal['strength']})")
                    print(f"  Confidence: {trading_signal['confidence']:.1%}")
                    print(f"  Total P&L: ${self.performance_metrics['total_pnl']:.2f}")
                    print(f"  Win Rate: {win_rate:.1%} ({self.performance_metrics['winning_trades']}/{self.performance_metrics['total_trades']})")
            
            # Simulate real-time delay
            time.sleep(0.5)  # 500ms between opportunities
        
        # Final results
        self.generate_simulation_report(trades_executed, market_history)
        
        return {
            'trades': trades_executed,
            'signals': self.signal_history,
            'performance': self.performance_metrics,
            'market_data': market_history
        }

    def generate_simulation_report(self, trades, market_history):
        """Generate comprehensive simulation report"""
        print(f"\n{'='*60}")
        print("MATLAB-POWERED TRADING SIMULATION RESULTS")
        print("="*60)
        
        # Trading performance
        total_trades = len(trades)
        winning_trades = 0
        total_pnl = 0.0
        avg_trade = 0.0
        win_rate = 0.0
        
        if total_trades > 0:
            winning_trades = sum(1 for t in trades if t['net_pnl'] > 0)
            total_pnl = sum(t['net_pnl'] for t in trades)
            avg_trade = total_pnl / total_trades
            win_rate = winning_trades / total_trades
            
            print(f"\\nTRADING PERFORMANCE:")
            print(f"  Total Trades: {total_trades}")
            print(f"  Winning Trades: {winning_trades}")
            print(f"  Win Rate: {win_rate:.1%}")
            print(f"  Total P&L: ${total_pnl:.2f}")
            print(f"  Average Trade: ${avg_trade:.2f}")
            print(f"  Max Drawdown: ${self.performance_metrics['max_drawdown']:.2f}")
        else:
            print("\\nNo trades executed during simulation period")
        
        # Signal analysis
        if self.signal_history:
            signals = [s['action'] for s in self.signal_history]
            buy_signals = signals.count('BUY')
            sell_signals = signals.count('SELL')
            hold_signals = signals.count('HOLD')
            
            print(f"\\nSIGNAL ANALYSIS:")
            print(f"  Total Signals: {len(signals)}")
            print(f"  BUY Signals: {buy_signals} ({buy_signals/len(signals):.1%})")
            print(f"  SELL Signals: {sell_signals} ({sell_signals/len(signals):.1%})")
            print(f"  HOLD Signals: {hold_signals} ({hold_signals/len(signals):.1%})")
        
        # Market conditions
        if market_history:
            avg_spread = np.mean([m['price_spread'] for m in market_history])
            avg_vol = np.mean([m['volatility'] for m in market_history])
            avg_liquidity = np.mean([m['liquidity_score'] for m in market_history])
            
            print(f"\\nMARKET CONDITIONS:")
            print(f"  Average Spread: {avg_spread:.6f}")
            print(f"  Average Volatility: {avg_vol:.4f}")
            print(f"  Average Liquidity: {avg_liquidity:.3f}")
            print(f"  Opportunities Analyzed: {len(market_history)}")
        
        # Save detailed results
        results = {
            'timestamp': datetime.now().isoformat(),
            'simulation_summary': {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'max_drawdown': self.performance_metrics['max_drawdown']
            },
            'trades': trades,
            'performance_metrics': self.performance_metrics
        }
        
        results_file = self.results_dir / f"matlab_trading_simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\\nDetailed results saved: {results_file}")
        print("="*60)


def main():
    """Main execution"""
    system = MATLABPoweredArbitrageSystem()
    
    print("Starting MATLAB-powered arbitrage trading simulation...")
    print("This demonstrates how MATLAB-style analytics can power real-time trading")
    
    # Run simulation
    results = system.run_live_trading_simulation(duration_minutes=5)
    
    print("\\n✓ MATLAB-powered trading simulation completed!")
    print("✓ Advanced statistical, momentum, and volatility strategies demonstrated")
    print("✓ Real-time signal generation and trade execution simulated")
    print("✓ Professional analytics and performance tracking implemented")

if __name__ == "__main__":
    main()
