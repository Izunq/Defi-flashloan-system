#!/usr/bin/env python3
"""
Pure Python Live Trading Demo
Live market data and trading demonstration using only built-in Python modules
"""

import asyncio
import json
import random
import time
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MarketTick:
    """Market data tick"""
    def __init__(self, symbol: str, price: float, volume: float, bid: float, ask: float):
        self.symbol = symbol
        self.price = price
        self.volume = volume
        self.bid = bid
        self.ask = ask
        self.timestamp = datetime.now()

class TradingSignal:
    """Trading signal"""
    def __init__(self, symbol: str, action: str, quantity: float, price: float, confidence: float, strategy: str):
        self.symbol = symbol
        self.action = action
        self.quantity = quantity
        self.price = price
        self.confidence = confidence
        self.strategy = strategy
        self.timestamp = datetime.now()

class Order:
    """Order execution result"""
    def __init__(self, order_id: str, symbol: str, side: str, quantity: float, price: float, status: str):
        self.order_id = order_id
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.price = price
        self.status = status
        self.timestamp = datetime.now()

class PurePythonTradingDemo:
    """Complete trading demo using only built-in Python modules"""
    
    def __init__(self):
        # Market configuration
        self.symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT']
        self.base_prices = {
            'BTC/USDT': 45000.0,
            'ETH/USDT': 3200.0,
            'BNB/USDT': 320.0,
            'ADA/USDT': 0.55,
            'SOL/USDT': 110.0
        }
        self.current_prices = self.base_prices.copy()
        
        # Trading account
        self.initial_balance = 10000.0
        self.balance = self.initial_balance
        self.positions = {}  # symbol -> quantity
        self.orders = []
        self.order_counter = 0
        
        # Data storage
        self.price_history = {}  # symbol -> list of prices
        self.volume_history = {}  # symbol -> list of volumes
        self.signals = []
        self.performance = []
        
        # Control
        self.running = False
        self.start_time = None
        
        # Initialize price history
        for symbol in self.symbols:
            self.price_history[symbol] = []
            self.volume_history[symbol] = []
    
    def generate_realistic_price_movement(self, current_price: float, volatility: float = 0.003) -> float:
        """Generate realistic price movement using geometric Brownian motion approximation"""
        # Random walk with slight upward drift
        dt = 0.5  # 0.5 second intervals
        drift = 0.0001  # Small positive drift (annual ~3%)
        
        # Generate random shock
        shock = random.gauss(0, 1)
        
        # Calculate price change
        price_change = current_price * (drift * dt + volatility * math.sqrt(dt) * shock)
        new_price = current_price + price_change
        
        # Prevent negative prices and extreme movements
        new_price = max(new_price, current_price * 0.95)
        new_price = min(new_price, current_price * 1.05)
        
        return new_price
    
    def generate_market_tick(self, symbol: str) -> MarketTick:
        """Generate realistic market data tick"""
        current_price = self.current_prices[symbol]
        
        # Different volatilities for different assets
        volatilities = {
            'BTC/USDT': 0.004,
            'ETH/USDT': 0.005,
            'BNB/USDT': 0.006,
            'ADA/USDT': 0.008,
            'SOL/USDT': 0.007
        }
        
        volatility = volatilities.get(symbol, 0.005)
        new_price = self.generate_realistic_price_movement(current_price, volatility)
        self.current_prices[symbol] = new_price
        
        # Generate bid/ask spread (0.05% to 0.2%)
        spread_percent = random.uniform(0.0005, 0.002)
        spread = new_price * spread_percent
        bid = new_price - spread / 2
        ask = new_price + spread / 2
        
        # Generate volume (correlated with volatility)
        base_volume = 1000
        volume_multiplier = 1 + abs(new_price / current_price - 1) * 50  # Higher volume on big moves
        volume = base_volume * volume_multiplier * random.uniform(0.5, 2.0)
        
        return MarketTick(symbol, new_price, volume, bid, ask)
    
    def simple_moving_average(self, prices: List[float], period: int) -> float:
        """Calculate simple moving average"""
        if len(prices) < period:
            return sum(prices) / len(prices) if prices else 0
        return sum(prices[-period:]) / period
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return 50.0  # Neutral RSI
        
        # Calculate price changes
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        # Separate gains and losses
        gains = [delta if delta > 0 else 0 for delta in deltas]
        losses = [-delta if delta < 0 else 0 for delta in deltas]
        
        # Calculate average gains and losses
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_momentum(self, prices: List[float], period: int = 5) -> float:
        """Calculate price momentum"""
        if len(prices) < period + 1:
            return 0.0
        
        return ((prices[-1] / prices[-period]) - 1) * 100
    
    def add_market_data(self, tick: MarketTick):
        """Add market data for analysis"""
        symbol = tick.symbol
        
        self.price_history[symbol].append(tick.price)
        self.volume_history[symbol].append(tick.volume)
        
        # Keep only last 100 data points
        if len(self.price_history[symbol]) > 100:
            self.price_history[symbol] = self.price_history[symbol][-100:]
            self.volume_history[symbol] = self.volume_history[symbol][-100:]
    
    def analyze_market(self, symbol: str) -> Dict:
        """Perform technical analysis"""
        prices = self.price_history[symbol]
        
        if len(prices) < 5:
            return {}
        
        # Technical indicators
        ma_5 = self.simple_moving_average(prices, 5)
        ma_20 = self.simple_moving_average(prices, 20)
        rsi = self.calculate_rsi(prices)
        momentum = self.calculate_momentum(prices)
        
        # Current price
        current_price = prices[-1]
        
        return {
            'ma_5': ma_5,
            'ma_20': ma_20,
            'rsi': rsi,
            'momentum': momentum,
            'current_price': current_price,
            'ma_trend': 'BULLISH' if ma_5 > ma_20 else 'BEARISH'
        }
    
    def generate_trading_signal(self, tick: MarketTick) -> Optional[TradingSignal]:
        """Generate trading signal based on technical analysis"""
        self.add_market_data(tick)
        analysis = self.analyze_market(tick.symbol)
        
        if not analysis:
            return None
        
        signal_strength = 0.0
        strategy_components = []
        
        # Moving Average Signal
        if analysis['ma_trend'] == 'BULLISH' and tick.price > analysis['ma_5']:
            signal_strength += 0.3
            strategy_components.append("MA_BULLISH")
        elif analysis['ma_trend'] == 'BEARISH' and tick.price < analysis['ma_5']:
            signal_strength -= 0.3
            strategy_components.append("MA_BEARISH")
        
        # RSI Signal
        rsi = analysis['rsi']
        if rsi < 30:  # Oversold
            signal_strength += 0.4
            strategy_components.append("RSI_OVERSOLD")
        elif rsi > 70:  # Overbought
            signal_strength -= 0.4
            strategy_components.append("RSI_OVERBOUGHT")
        elif 30 <= rsi <= 40:
            signal_strength += 0.1
            strategy_components.append("RSI_WEAK_BUY")
        elif 60 <= rsi <= 70:
            signal_strength -= 0.1
            strategy_components.append("RSI_WEAK_SELL")
        
        # Momentum Signal
        momentum = analysis['momentum']
        if momentum > 3:  # Strong upward momentum
            signal_strength += 0.2
            strategy_components.append("MOMENTUM_STRONG_UP")
        elif momentum > 1:
            signal_strength += 0.1
            strategy_components.append("MOMENTUM_UP")
        elif momentum < -3:  # Strong downward momentum
            signal_strength -= 0.2
            strategy_components.append("MOMENTUM_STRONG_DOWN")
        elif momentum < -1:
            signal_strength -= 0.1
            strategy_components.append("MOMENTUM_DOWN")
        
        # Determine action
        action = "HOLD"
        if signal_strength >= 0.5:
            action = "BUY"
        elif signal_strength <= -0.5:
            action = "SELL"
        
        if action != "HOLD":
            # Risk management: position sizing
            confidence = abs(signal_strength)
            max_position_value = self.initial_balance * 0.1  # Max 10% per position
            position_value = max_position_value * confidence
            quantity = position_value / tick.price
            
            # Minimum order size
            if quantity * tick.price < 50:  # Minimum $50 order
                return None
            
            price = tick.ask if action == "BUY" else tick.bid
            
            signal = TradingSignal(
                symbol=tick.symbol,
                action=action,
                quantity=quantity,
                price=price,
                confidence=confidence,
                strategy=" + ".join(strategy_components)
            )
            
            self.signals.append(signal)
            return signal
        
        return None
    
    def execute_order(self, signal: TradingSignal) -> Order:
        """Execute trading order"""
        self.order_counter += 1
        order_id = f"ORD_{self.order_counter:06d}"
        
        status = "REJECTED"
        
        if signal.action == "BUY":
            cost = signal.quantity * signal.price
            if cost <= self.balance:
                self.balance -= cost
                if signal.symbol not in self.positions:
                    self.positions[signal.symbol] = 0.0
                self.positions[signal.symbol] += signal.quantity
                status = "FILLED"
            else:
                status = "REJECTED_INSUFFICIENT_FUNDS"
        
        elif signal.action == "SELL":
            current_position = self.positions.get(signal.symbol, 0.0)
            if current_position >= signal.quantity:
                self.positions[signal.symbol] -= signal.quantity
                self.balance += signal.quantity * signal.price
                status = "FILLED"
            else:
                status = "REJECTED_INSUFFICIENT_POSITION"
        
        order = Order(order_id, signal.symbol, signal.action, signal.quantity, signal.price, status)
        self.orders.append(order)
        return order
    
    def calculate_portfolio_value(self) -> float:
        """Calculate current portfolio value"""
        total_value = self.balance
        
        for symbol, quantity in self.positions.items():
            if quantity > 0:
                current_price = self.current_prices[symbol]
                position_value = quantity * current_price
                total_value += position_value
        
        return total_value
    
    def calculate_pnl(self) -> Dict:
        """Calculate profit and loss"""
        portfolio_value = self.calculate_portfolio_value()
        pnl = portfolio_value - self.initial_balance
        pnl_percent = (pnl / self.initial_balance) * 100
        
        return {
            'portfolio_value': portfolio_value,
            'pnl': pnl,
            'pnl_percent': pnl_percent
        }
    
    async def run_trading_simulation(self, duration_seconds: int = 60):
        """Run complete trading simulation"""
        print("=" * 100)
        print("🚀 PURE PYTHON LIVE TRADING SIMULATION")
        print("=" * 100)
        print(f"⏱️  Duration: {duration_seconds} seconds")
        print(f"💰 Initial Balance: ${self.initial_balance:,.2f}")
        print(f"📈 Trading Pairs: {', '.join(self.symbols)}")
        print(f"🎯 Strategy: MA Crossover + RSI + Momentum")
        print(f"⚡ Update Frequency: 2 ticks per second")
        print("-" * 100)
        
        self.running = True
        self.start_time = datetime.now()
        
        iteration = 0
        total_iterations = duration_seconds * 2  # 2 ticks per second
        
        while self.running and iteration < total_iterations:
            iteration += 1
            
            # Generate market data for all symbols
            for symbol in self.symbols:
                tick = self.generate_market_tick(symbol)
                
                # Show market data every 10 iterations (every 5 seconds)
                if iteration % 10 == 0:
                    print(f"📊 {tick.symbol}: ${tick.price:8.4f} | "
                          f"Bid: ${tick.bid:8.4f} | Ask: ${tick.ask:8.4f} | "
                          f"Vol: {tick.volume:6.0f}")
                
                # Generate trading signals
                signal = self.generate_trading_signal(tick)
                
                if signal and signal.confidence >= 0.6:  # Only high-confidence signals
                    order = self.execute_order(signal)
                    
                    print(f"⚡ SIGNAL: {signal.action} {signal.quantity:.3f} {signal.symbol} "
                          f"@ ${signal.price:.4f} | Conf: {signal.confidence:.2f} | {signal.strategy}")
                    
                    if order.status == "FILLED":
                        print(f"✅ FILLED: {order.side} {order.quantity:.3f} {order.symbol} | "
                              f"Cash: ${self.balance:.2f}")
                    else:
                        print(f"❌ REJECTED: {order.status}")
            
            # Calculate performance
            performance = self.calculate_pnl()
            performance['timestamp'] = datetime.now()
            self.performance.append(performance)
            
            # Show performance every 20 iterations (every 10 seconds)
            if iteration % 20 == 0:
                print(f"\n📊 PERFORMANCE UPDATE ({iteration}/{total_iterations}):")
                print(f"   Portfolio Value: ${performance['portfolio_value']:,.2f}")
                print(f"   P&L: ${performance['pnl']:+.2f} ({performance['pnl_percent']:+.2f}%)")
                print(f"   Active Positions: {sum(1 for q in self.positions.values() if q > 0)}")
                print(f"   Total Orders: {len(self.orders)}")
                print(f"   Success Rate: {len([o for o in self.orders if o.status == 'FILLED'])}/{len(self.orders)}")
                print("-" * 80)
            
            # Wait for next tick
            await asyncio.sleep(0.5)
        
        self.running = False
        await self.generate_final_report()
    
    async def generate_final_report(self):
        """Generate comprehensive final trading report"""
        print(f"\n" + "=" * 100)
        print("📈 FINAL TRADING REPORT")
        print("=" * 100)
        
        end_time = datetime.now()
        runtime = end_time - self.start_time
        final_performance = self.calculate_pnl()
        
        # Basic Performance
        print(f"⏱️  Runtime: {runtime}")
        print(f"💰 Initial Balance: ${self.initial_balance:,.2f}")
        print(f"📈 Final Portfolio Value: ${final_performance['portfolio_value']:,.2f}")
        print(f"💵 Net P&L: ${final_performance['pnl']:+,.2f} ({final_performance['pnl_percent']:+.2f}%)")
        
        # Order Analysis
        filled_orders = [o for o in self.orders if o.status == "FILLED"]
        buy_orders = [o for o in filled_orders if o.side == "BUY"]
        sell_orders = [o for o in filled_orders if o.side == "SELL"]
        
        print(f"\n📊 TRADING STATISTICS:")
        print(f"   Total Signals: {len(self.signals)}")
        print(f"   Total Orders: {len(self.orders)}")
        print(f"   Filled Orders: {len(filled_orders)} ({len(filled_orders)/len(self.orders)*100 if self.orders else 0:.1f}%)")
        print(f"   Buy Orders: {len(buy_orders)}")
        print(f"   Sell Orders: {len(sell_orders)}")
        
        if filled_orders:
            total_volume = sum(o.quantity * o.price for o in filled_orders)
            print(f"   Total Volume: ${total_volume:,.2f}")
        
        # Position Analysis
        print(f"\n💼 FINAL POSITIONS:")
        print(f"   Cash Balance: ${self.balance:,.2f}")
        
        total_position_value = 0
        for symbol, quantity in self.positions.items():
            if quantity > 0:
                current_price = self.current_prices[symbol]
                position_value = quantity * current_price
                total_position_value += position_value
                print(f"   {symbol}: {quantity:.6f} units @ ${current_price:.4f} = ${position_value:,.2f}")
        
        if total_position_value > 0:
            print(f"   Total Positions Value: ${total_position_value:,.2f}")
        
        # Market Performance
        print(f"\n📈 MARKET MOVEMENTS:")
        for symbol in self.symbols:
            start_price = self.base_prices[symbol]
            end_price = self.current_prices[symbol]
            price_change = ((end_price / start_price) - 1) * 100
            print(f"   {symbol}: ${start_price:.4f} → ${end_price:.4f} ({price_change:+.2f}%)")
        
        # Performance Analysis
        if len(self.performance) > 1:
            pnl_values = [p['pnl_percent'] for p in self.performance]
            max_gain = max(pnl_values)
            max_loss = min(pnl_values)
            
            # Calculate volatility
            mean_pnl = sum(pnl_values) / len(pnl_values)
            variance = sum((x - mean_pnl) ** 2 for x in pnl_values) / len(pnl_values)
            volatility = math.sqrt(variance)
            
            print(f"\n📊 PERFORMANCE METRICS:")
            print(f"   Maximum Gain: {max_gain:.2f}%")
            print(f"   Maximum Loss: {max_loss:.2f}%")
            print(f"   Volatility: {volatility:.2f}%")
            print(f"   Sharpe Ratio: {final_performance['pnl_percent'] / volatility if volatility > 0 else 0:.2f}")
        
        # Signal Analysis
        if self.signals:
            buy_signals = [s for s in self.signals if s.action == "BUY"]
            sell_signals = [s for s in self.signals if s.action == "SELL"]
            avg_confidence = sum(s.confidence for s in self.signals) / len(self.signals)
            
            print(f"\n⚡ SIGNAL ANALYSIS:")
            print(f"   Buy Signals: {len(buy_signals)}")
            print(f"   Sell Signals: {len(sell_signals)}")
            print(f"   Average Confidence: {avg_confidence:.2f}")
        
        # Performance Rating
        performance_rating = self.calculate_performance_rating(final_performance['pnl_percent'])
        print(f"\n🏆 PERFORMANCE RATING: {performance_rating}")
        
        print(f"\n✅ Trading simulation completed successfully!")
        print("=" * 100)
    
    def calculate_performance_rating(self, pnl_percent: float) -> str:
        """Calculate performance rating based on P&L"""
        if pnl_percent >= 5:
            return "🥇 EXCELLENT (≥5%)"
        elif pnl_percent >= 2:
            return "🥈 VERY GOOD (2-5%)"
        elif pnl_percent >= 0.5:
            return "🥉 GOOD (0.5-2%)"
        elif pnl_percent >= -0.5:
            return "⭐ NEUTRAL (±0.5%)"
        elif pnl_percent >= -2:
            return "⚠️ POOR (-0.5 to -2%)"
        else:
            return "❌ VERY POOR (<-2%)"

async def main():
    """Main function to run the trading demonstration"""
    print("🎯 Pure Python Live Trading Demo")
    print("\n📱 Features:")
    print("   ✅ Real-time market simulation (5 crypto pairs)")
    print("   ✅ Technical analysis (SMA, RSI, Momentum)")
    print("   ✅ Automated signal generation")
    print("   ✅ Order execution with risk management")
    print("   ✅ Performance tracking and reporting")
    print("   ✅ No external dependencies required")
    
    print(f"\n⚙️ Configuration:")
    print(f"   • Initial Balance: $10,000")
    print(f"   • Max Position Size: 10% of balance")
    print(f"   • Minimum Order: $50")
    print(f"   • Signal Confidence Threshold: 60%")
    
    demo = PurePythonTradingDemo()
    await demo.run_trading_simulation(duration_seconds=90)  # 90 second demo
    
    return demo

if __name__ == "__main__":
    asyncio.run(main())