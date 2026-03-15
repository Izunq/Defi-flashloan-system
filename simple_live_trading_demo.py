#!/usr/bin/env python3
"""
Simple Live Trading Demo
Core demonstration of live market data and trading without external dependencies
"""

import asyncio
import json
import random
import time
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging
import threading
from queue import Queue
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleMarketData:
    """Simple market data structure"""
    def __init__(self, symbol: str, price: float, volume: float, bid: float, ask: float):
        self.symbol = symbol
        self.price = price
        self.volume = volume
        self.bid = bid
        self.ask = ask
        self.timestamp = datetime.now()

class SimpleTradingSignal:
    """Simple trading signal"""
    def __init__(self, symbol: str, action: str, quantity: float, price: float, confidence: float, strategy: str):
        self.symbol = symbol
        self.action = action
        self.quantity = quantity
        self.price = price
        self.confidence = confidence
        self.strategy = strategy
        self.timestamp = datetime.now()

class SimpleOrderResult:
    """Simple order result"""
    def __init__(self, order_id: str, symbol: str, side: str, quantity: float, price: float, status: str):
        self.order_id = order_id
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.price = price
        self.status = status
        self.timestamp = datetime.now()

class SimpleLiveTradingDemo:
    """Simplified live trading demonstration"""
    
    def __init__(self):
        # Trading symbols and their base prices
        self.symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT']
        self.base_prices = {
            'BTC/USDT': 45000,
            'ETH/USDT': 3200,
            'BNB/USDT': 320,
            'ADA/USDT': 0.55,
            'SOL/USDT': 110
        }
        self.current_prices = self.base_prices.copy()
        
        # Trading components
        self.initial_balance = 10000
        self.balance = self.initial_balance
        self.positions = {}
        self.orders = []
        self.order_counter = 0
        
        # Price history for technical analysis
        self.price_history = {}
        self.signals_history = []
        self.performance_history = []
        
        # Control flags
        self.running = False
        self.start_time = None
        
    def generate_market_data(self, symbol: str) -> SimpleMarketData:
        """Generate realistic market data"""
        current_price = self.current_prices[symbol]
        
        # Random walk with slight upward bias
        change_percent = random.normalvariate(0.0002, 0.003)  # 0.02% mean, 0.3% std
        new_price = current_price * (1 + change_percent)
        new_price = max(new_price, current_price * 0.95)  # Prevent extreme drops
        
        self.current_prices[symbol] = new_price
        
        # Generate bid/ask spread (0.1-0.3%)
        spread = new_price * random.uniform(0.001, 0.003)
        bid = new_price - spread/2
        ask = new_price + spread/2
        
        # Generate volume
        volume = random.uniform(100, 10000)
        
        return SimpleMarketData(symbol, new_price, volume, bid, ask)
    
    def add_price_data(self, data: SimpleMarketData):
        """Add price data for analysis"""
        symbol = data.symbol
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        
        self.price_history[symbol].append({
            'price': data.price,
            'volume': data.volume,
            'timestamp': data.timestamp
        })
        
        # Keep only last 50 data points for analysis
        if len(self.price_history[symbol]) > 50:
            self.price_history[symbol] = self.price_history[symbol][-50:]
    
    def calculate_indicators(self, symbol: str) -> Dict:
        """Calculate simple technical indicators"""
        if symbol not in self.price_history or len(self.price_history[symbol]) < 10:
            return {}
        
        prices = [d['price'] for d in self.price_history[symbol]]
        
        # Simple moving averages
        ma_5 = np.mean(prices[-5:]) if len(prices) >= 5 else prices[-1]
        ma_20 = np.mean(prices[-20:]) if len(prices) >= 20 else np.mean(prices)
        
        # Simple RSI calculation
        if len(prices) >= 14:
            deltas = np.diff(prices)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            avg_gain = np.mean(gains[-14:])
            avg_loss = np.mean(losses[-14:])
            
            if avg_loss != 0:
                rsi = 100 - (100 / (1 + avg_gain / avg_loss))
            else:
                rsi = 100
        else:
            rsi = 50
        
        # Price momentum
        momentum = (prices[-1] / prices[-5] - 1) * 100 if len(prices) >= 5 else 0
        
        return {
            'ma_5': ma_5,
            'ma_20': ma_20,
            'rsi': rsi,
            'momentum': momentum,
            'current_price': prices[-1]
        }
    
    def generate_signal(self, data: SimpleMarketData) -> Optional[SimpleTradingSignal]:
        """Generate trading signals"""
        self.add_price_data(data)
        indicators = self.calculate_indicators(data.symbol)
        
        if not indicators:
            return None
        
        signal_strength = 0
        strategy_reasons = []
        
        # Moving Average Strategy
        if indicators['ma_5'] > indicators['ma_20']:
            signal_strength += 0.3
            strategy_reasons.append("MA_BULLISH")
        else:
            signal_strength -= 0.3
            strategy_reasons.append("MA_BEARISH")
        
        # RSI Strategy
        if indicators['rsi'] < 30:  # Oversold
            signal_strength += 0.4
            strategy_reasons.append("RSI_OVERSOLD")
        elif indicators['rsi'] > 70:  # Overbought
            signal_strength -= 0.4
            strategy_reasons.append("RSI_OVERBOUGHT")
        
        # Momentum Strategy
        if indicators['momentum'] > 2:  # Strong upward momentum
            signal_strength += 0.2
            strategy_reasons.append("MOMENTUM_UP")
        elif indicators['momentum'] < -2:  # Strong downward momentum
            signal_strength -= 0.2
            strategy_reasons.append("MOMENTUM_DOWN")
        
        # Determine action
        action = "HOLD"
        if signal_strength >= 0.5:
            action = "BUY"
        elif signal_strength <= -0.5:
            action = "SELL"
        
        if action != "HOLD":
            # Calculate position size with risk management
            position_size = min(abs(signal_strength) * 800, 400)  # Max 400 units
            
            signal = SimpleTradingSignal(
                symbol=data.symbol,
                action=action,
                quantity=position_size,
                price=data.ask if action == "BUY" else data.bid,
                confidence=abs(signal_strength),
                strategy=" + ".join(strategy_reasons)
            )
            
            self.signals_history.append(signal)
            return signal
        
        return None
    
    def execute_order(self, signal: SimpleTradingSignal) -> SimpleOrderResult:
        """Execute trading order"""
        self.order_counter += 1
        order_id = f"ORDER_{self.order_counter:06d}"
        
        status = "REJECTED"
        
        if signal.action == "BUY":
            cost = signal.quantity * signal.price
            if cost <= self.balance:
                self.balance -= cost
                if signal.symbol not in self.positions:
                    self.positions[signal.symbol] = 0
                self.positions[signal.symbol] += signal.quantity
                status = "FILLED"
            else:
                status = "REJECTED_INSUFFICIENT_BALANCE"
        
        elif signal.action == "SELL":
            if signal.symbol in self.positions and self.positions[signal.symbol] >= signal.quantity:
                self.positions[signal.symbol] -= signal.quantity
                self.balance += signal.quantity * signal.price
                status = "FILLED"
            else:
                status = "REJECTED_INSUFFICIENT_POSITION"
        
        result = SimpleOrderResult(order_id, signal.symbol, signal.action, signal.quantity, signal.price, status)
        self.orders.append(result)
        return result
    
    def get_portfolio_value(self) -> float:
        """Calculate current portfolio value"""
        total_value = self.balance
        
        for symbol, quantity in self.positions.items():
            if quantity > 0:
                price = self.current_prices.get(symbol, 0)
                total_value += quantity * price
        
        return total_value
    
    def get_pnl(self) -> float:
        """Calculate profit/loss"""
        return self.get_portfolio_value() - self.initial_balance
    
    async def run_live_demo(self, duration_seconds: int = 60):
        """Run the complete live trading demo"""
        print("="*100)
        print("🚀 LIVE MARKET DATA & TRADING DEMO")
        print("="*100)
        print(f"⏱️ Duration: {duration_seconds} seconds")
        print(f"💰 Initial Balance: ${self.initial_balance:.2f}")
        print(f"📈 Symbols: {', '.join(self.symbols)}")
        print(f"🎯 Trading Strategy: MA + RSI + Momentum")
        print("-" * 100)
        
        self.running = True
        self.start_time = datetime.now()
        
        # Main trading loop
        iteration = 0
        while self.running and iteration < duration_seconds * 2:  # 2 iterations per second
            iteration += 1
            
            # Generate market data for all symbols
            for symbol in self.symbols:
                data = self.generate_market_data(symbol)
                
                # Print market data every 5th iteration (every 2.5 seconds)
                if iteration % 5 == 0:
                    print(f"📈 {data.symbol}: ${data.price:.4f} | "
                          f"Bid: ${data.bid:.4f} | Ask: ${data.ask:.4f} | "
                          f"Vol: {data.volume:.0f}")
                
                # Generate and process trading signals
                signal = self.generate_signal(data)
                
                if signal and signal.confidence >= 0.6:  # Only execute high-confidence signals
                    result = self.execute_order(signal)
                    
                    print(f"⚡ SIGNAL: {signal.action} {signal.quantity:.2f} {signal.symbol} "
                          f"at ${signal.price:.4f} | Confidence: {signal.confidence:.2f}")
                    
                    if result.status == "FILLED":
                        print(f"✅ ORDER FILLED: {result.side} {result.quantity:.2f} "
                              f"{result.symbol} | Balance: ${self.balance:.2f}")
                    else:
                        print(f"❌ ORDER REJECTED: {result.status}")
            
            # Calculate and store performance
            portfolio_value = self.get_portfolio_value()
            pnl = self.get_pnl()
            pnl_percent = (pnl / self.initial_balance) * 100
            
            self.performance_history.append({
                'timestamp': datetime.now(),
                'portfolio_value': portfolio_value,
                'pnl': pnl,
                'pnl_percent': pnl_percent
            })
            
            # Print performance update every 20 iterations (every 10 seconds)
            if iteration % 20 == 0:
                print(f"\n📊 PERFORMANCE UPDATE (Iteration {iteration}):")
                print(f"   Portfolio Value: ${portfolio_value:.2f}")
                print(f"   P&L: ${pnl:.2f} ({pnl_percent:.2f}%)")
                print(f"   Active Positions: {sum(1 for q in self.positions.values() if q > 0)}")
                print(f"   Total Orders: {len(self.orders)}")
                print("-" * 80)
            
            await asyncio.sleep(0.5)  # 2 updates per second
        
        self.running = False
        self.generate_final_report()
    
    def generate_final_report(self):
        """Generate comprehensive final report"""
        print(f"\n" + "="*100)
        print("📊 LIVE TRADING DEMO - FINAL REPORT")
        print("="*100)
        
        runtime = datetime.now() - self.start_time
        final_portfolio_value = self.get_portfolio_value()
        final_pnl = self.get_pnl()
        final_pnl_percent = (final_pnl / self.initial_balance) * 100
        
        print(f"⏱️ Runtime: {runtime}")
        print(f"💰 Initial Balance: ${self.initial_balance:.2f}")
        print(f"📈 Final Portfolio Value: ${final_portfolio_value:.2f}")
        print(f"💵 Total P&L: ${final_pnl:.2f} ({final_pnl_percent:.2f}%)")
        
        # Order statistics
        filled_orders = [o for o in self.orders if o.status == "FILLED"]
        buy_orders = [o for o in filled_orders if o.side == "BUY"]
        sell_orders = [o for o in filled_orders if o.side == "SELL"]
        
        print(f"\n📋 ORDER STATISTICS:")
        print(f"   Total Orders: {len(self.orders)}")
        print(f"   Filled Orders: {len(filled_orders)}")
        print(f"   Buy Orders: {len(buy_orders)}")
        print(f"   Sell Orders: {len(sell_orders)}")
        
        if filled_orders:
            total_volume = sum(o.quantity * o.price for o in filled_orders)
            print(f"   Total Volume Traded: ${total_volume:.2f}")
        
        # Current positions
        print(f"\n💼 FINAL POSITIONS:")
        print(f"   Cash Balance: ${self.balance:.2f}")
        
        for symbol, quantity in self.positions.items():
            if quantity > 0:
                current_price = self.current_prices[symbol]
                position_value = quantity * current_price
                print(f"   {symbol}: {quantity:.4f} units (${position_value:.2f})")
        
        # Signal statistics
        print(f"\n⚡ SIGNAL STATISTICS:")
        print(f"   Total Signals Generated: {len(self.signals_history)}")
        
        if self.signals_history:
            buy_signals = [s for s in self.signals_history if s.action == "BUY"]
            sell_signals = [s for s in self.signals_history if s.action == "SELL"]
            avg_confidence = np.mean([s.confidence for s in self.signals_history])
            
            print(f"   Buy Signals: {len(buy_signals)}")
            print(f"   Sell Signals: {len(sell_signals)}")
            print(f"   Average Confidence: {avg_confidence:.2f}")
        
        # Performance metrics
        if len(self.performance_history) > 1:
            pnl_values = [p['pnl_percent'] for p in self.performance_history]
            max_gain = max(pnl_values)
            max_drawdown = min(pnl_values)
            volatility = np.std(pnl_values)
            
            print(f"\n📈 PERFORMANCE METRICS:")
            print(f"   Max Gain: {max_gain:.2f}%")
            print(f"   Max Drawdown: {max_drawdown:.2f}%")
            print(f"   Volatility: {volatility:.2f}%")
            
            if volatility > 0:
                sharpe_ratio = final_pnl_percent / volatility
                print(f"   Sharpe Ratio: {sharpe_ratio:.2f}")
        
        # Price movements summary
        print(f"\n📈 PRICE MOVEMENTS:")
        for symbol in self.symbols:
            start_price = self.base_prices[symbol]
            end_price = self.current_prices[symbol]
            price_change = ((end_price / start_price) - 1) * 100
            print(f"   {symbol}: ${start_price:.2f} → ${end_price:.2f} ({price_change:+.2f}%)")
        
        print(f"\n✅ Live trading demo completed successfully!")

async def main():
    """Main demonstration function"""
    print("🎯 Simple Live Trading Demo")
    print("\n📱 Demo Features:")
    print("   • Live market data simulation (5 crypto pairs)")
    print("   • Technical analysis (MA, RSI, Momentum)")
    print("   • Automated signal generation")
    print("   • Order execution with risk management")
    print("   • Real-time performance tracking")
    print("   • Comprehensive reporting")
    
    demo = SimpleLiveTradingDemo()
    await demo.run_live_demo(duration_seconds=60)
    
    return demo

if __name__ == "__main__":
    asyncio.run(main())