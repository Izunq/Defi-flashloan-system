#!/usr/bin/env python3
"""
Live Market Data and Trading Demo
Comprehensive demonstration of live data feeds and trading capabilities
"""

import asyncio
import json
import random
import time
import websockets
import aiohttp
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass
import threading
from queue import Queue
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class MarketData:
    """Market data structure"""
    symbol: str
    price: float
    volume: float
    bid: float
    ask: float
    timestamp: datetime
    exchange: str

@dataclass
class TradeSignal:
    """Trading signal structure"""
    symbol: str
    action: str  # BUY, SELL, HOLD
    quantity: float
    price: float
    confidence: float
    strategy: str
    timestamp: datetime

@dataclass
class OrderResult:
    """Order execution result"""
    order_id: str
    symbol: str
    side: str
    quantity: float
    price: float
    status: str
    timestamp: datetime

class MockMarketDataFeed:
    """Mock market data feed for demonstration"""
    
    def __init__(self):
        self.symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT']
        self.base_prices = {
            'BTC/USDT': 45000,
            'ETH/USDT': 3200,
            'BNB/USDT': 320,
            'ADA/USDT': 0.55,
            'SOL/USDT': 110
        }
        self.current_prices = self.base_prices.copy()
        self.running = False
        
    def generate_price_movement(self, current_price: float) -> float:
        """Generate realistic price movement"""
        # Random walk with slight upward bias
        change_percent = random.normalvariate(0.0001, 0.002)  # 0.01% mean, 0.2% std
        new_price = current_price * (1 + change_percent)
        return max(new_price, current_price * 0.95)  # Prevent extreme drops
    
    def generate_market_data(self, symbol: str) -> MarketData:
        """Generate realistic market data"""
        current_price = self.current_prices[symbol]
        new_price = self.generate_price_movement(current_price)
        self.current_prices[symbol] = new_price
        
        # Generate bid/ask spread (0.1-0.2%)
        spread = new_price * random.uniform(0.001, 0.002)
        bid = new_price - spread/2
        ask = new_price + spread/2
        
        # Generate volume
        volume = random.uniform(100, 10000)
        
        return MarketData(
            symbol=symbol,
            price=new_price,
            volume=volume,
            bid=bid,
            ask=ask,
            timestamp=datetime.now(),
            exchange='MockExchange'
        )

class TradingStrategy:
    """Advanced trading strategy with multiple signals"""
    
    def __init__(self):
        self.price_history = {}
        self.positions = {}
        self.signals_history = []
        
    def add_price_data(self, data: MarketData):
        """Add price data for analysis"""
        symbol = data.symbol
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        
        self.price_history[symbol].append({
            'price': data.price,
            'volume': data.volume,
            'timestamp': data.timestamp,
            'bid': data.bid,
            'ask': data.ask
        })
        
        # Keep only last 100 data points
        if len(self.price_history[symbol]) > 100:
            self.price_history[symbol] = self.price_history[symbol][-100:]
    
    def calculate_technical_indicators(self, symbol: str) -> Dict:
        """Calculate technical indicators"""
        if symbol not in self.price_history or len(self.price_history[symbol]) < 20:
            return {}
        
        prices = [d['price'] for d in self.price_history[symbol]]
        volumes = [d['volume'] for d in self.price_history[symbol]]
        
        df = pd.DataFrame({
            'price': prices,
            'volume': volumes
        })
        
        # Moving averages
        df['ma_5'] = df['price'].rolling(5).mean()
        df['ma_20'] = df['price'].rolling(20).mean()
        
        # RSI
        delta = df['price'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['price'].ewm(span=12).mean()
        exp2 = df['price'].ewm(span=26).mean()
        df['macd'] = exp1 - exp2
        df['signal'] = df['macd'].ewm(span=9).mean()
        
        # Bollinger Bands
        df['bb_middle'] = df['price'].rolling(20).mean()
        bb_std = df['price'].rolling(20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        
        return df.iloc[-1].to_dict()
    
    def generate_signal(self, data: MarketData) -> Optional[TradeSignal]:
        """Generate trading signals based on technical analysis"""
        self.add_price_data(data)
        
        indicators = self.calculate_technical_indicators(data.symbol)
        if not indicators:
            return None
        
        signal_strength = 0
        action = "HOLD"
        strategy_reasons = []
        
        # MA Crossover Strategy
        if 'ma_5' in indicators and 'ma_20' in indicators:
            ma_5 = indicators['ma_5']
            ma_20 = indicators['ma_20']
            
            if ma_5 > ma_20 and data.price > ma_5:
                signal_strength += 0.3
                strategy_reasons.append("MA_BULLISH")
            elif ma_5 < ma_20 and data.price < ma_5:
                signal_strength -= 0.3
                strategy_reasons.append("MA_BEARISH")
        
        # RSI Strategy
        if 'rsi' in indicators:
            rsi = indicators['rsi']
            if rsi < 30:  # Oversold
                signal_strength += 0.4
                strategy_reasons.append("RSI_OVERSOLD")
            elif rsi > 70:  # Overbought
                signal_strength -= 0.4
                strategy_reasons.append("RSI_OVERBOUGHT")
        
        # MACD Strategy
        if 'macd' in indicators and 'signal' in indicators:
            macd = indicators['macd']
            macd_signal = indicators['signal']
            
            if macd > macd_signal:
                signal_strength += 0.2
                strategy_reasons.append("MACD_BULLISH")
            else:
                signal_strength -= 0.2
                strategy_reasons.append("MACD_BEARISH")
        
        # Bollinger Bands Strategy
        if 'bb_upper' in indicators and 'bb_lower' in indicators:
            bb_upper = indicators['bb_upper']
            bb_lower = indicators['bb_lower']
            
            if data.price <= bb_lower:
                signal_strength += 0.3
                strategy_reasons.append("BB_OVERSOLD")
            elif data.price >= bb_upper:
                signal_strength -= 0.3
                strategy_reasons.append("BB_OVERBOUGHT")
        
        # Determine action
        if signal_strength >= 0.5:
            action = "BUY"
        elif signal_strength <= -0.5:
            action = "SELL"
        
        # Calculate position size (risk management)
        position_size = min(abs(signal_strength) * 1000, 500)  # Max 500 units
        
        if action != "HOLD":
            signal = TradeSignal(
                symbol=data.symbol,
                action=action,
                quantity=position_size,
                price=data.ask if action == "BUY" else data.bid,
                confidence=abs(signal_strength),
                strategy=" + ".join(strategy_reasons),
                timestamp=datetime.now()
            )
            
            self.signals_history.append(signal)
            return signal
        
        return None

class MockTradingEngine:
    """Mock trading engine for demonstration"""
    
    def __init__(self, initial_balance: float = 10000):
        self.balance = initial_balance
        self.initial_balance = initial_balance
        self.positions = {}
        self.orders = []
        self.order_counter = 0
        
    def execute_order(self, signal: TradeSignal) -> OrderResult:
        """Execute trading order"""
        self.order_counter += 1
        order_id = f"ORDER_{self.order_counter:06d}"
        
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
        
        result = OrderResult(
            order_id=order_id,
            symbol=signal.symbol,
            side=signal.action,
            quantity=signal.quantity,
            price=signal.price,
            status=status,
            timestamp=datetime.now()
        )
        
        self.orders.append(result)
        return result
    
    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate current portfolio value"""
        total_value = self.balance
        
        for symbol, quantity in self.positions.items():
            if quantity > 0:
                clean_symbol = symbol.replace('/USDT', '')
                price = current_prices.get(symbol, 0)
                total_value += quantity * price
        
        return total_value
    
    def get_pnl(self, current_prices: Dict[str, float]) -> float:
        """Calculate profit/loss"""
        current_value = self.get_portfolio_value(current_prices)
        return current_value - self.initial_balance

class LiveTradingDemo:
    """Comprehensive live trading demonstration"""
    
    def __init__(self):
        self.market_feed = MockMarketDataFeed()
        self.strategy = TradingStrategy()
        self.trading_engine = MockTradingEngine()
        self.market_data_queue = Queue()
        self.signals_queue = Queue()
        self.orders_queue = Queue()
        self.running = False
        
        # Performance tracking
        self.start_time = None
        self.performance_history = []
        
    async def start_market_data_feed(self):
        """Start simulated market data feed"""
        logger.info("🚀 Starting market data feed...")
        
        while self.running:
            for symbol in self.market_feed.symbols:
                data = self.market_feed.generate_market_data(symbol)
                self.market_data_queue.put(data)
                
                # Print live data
                print(f"📈 {data.symbol}: ${data.price:.4f} | "
                      f"Bid: ${data.bid:.4f} | Ask: ${data.ask:.4f} | "
                      f"Vol: {data.volume:.0f}")
            
            await asyncio.sleep(0.5)  # 2 updates per second
    
    def process_trading_signals(self):
        """Process market data and generate trading signals"""
        logger.info("🎯 Starting signal generation...")
        
        while self.running:
            try:
                if not self.market_data_queue.empty():
                    data = self.market_data_queue.get(timeout=1)
                    signal = self.strategy.generate_signal(data)
                    
                    if signal:
                        self.signals_queue.put(signal)
                        print(f"⚡ SIGNAL: {signal.action} {signal.quantity:.2f} {signal.symbol} "
                              f"at ${signal.price:.4f} | Confidence: {signal.confidence:.2f} | "
                              f"Strategy: {signal.strategy}")
                
                time.sleep(0.1)
                
            except Exception as e:
                if self.running:
                    logger.error(f"Signal processing error: {e}")
                    time.sleep(1)
    
    def execute_trades(self):
        """Execute trading orders"""
        logger.info("💼 Starting trade execution...")
        
        while self.running:
            try:
                if not self.signals_queue.empty():
                    signal = self.signals_queue.get(timeout=1)
                    
                    # Risk management: Only trade if confidence > 0.6
                    if signal.confidence >= 0.6:
                        result = self.trading_engine.execute_order(signal)
                        self.orders_queue.put(result)
                        
                        if result.status == "FILLED":
                            print(f"✅ ORDER FILLED: {result.side} {result.quantity:.2f} "
                                  f"{result.symbol} at ${result.price:.4f} | "
                                  f"Balance: ${self.trading_engine.balance:.2f}")
                        else:
                            print(f"❌ ORDER REJECTED: {result.status}")
                    else:
                        print(f"⏸️ Signal ignored (low confidence): {signal.confidence:.2f}")
                
                time.sleep(0.1)
                
            except Exception as e:
                if self.running:
                    logger.error(f"Trade execution error: {e}")
                    time.sleep(1)
    
    def monitor_performance(self):
        """Monitor trading performance"""
        logger.info("📊 Starting performance monitoring...")
        
        while self.running:
            try:
                current_prices = {symbol: self.market_feed.current_prices[symbol] 
                                for symbol in self.market_feed.symbols}
                
                portfolio_value = self.trading_engine.get_portfolio_value(current_prices)
                pnl = self.trading_engine.get_pnl(current_prices)
                pnl_percent = (pnl / self.trading_engine.initial_balance) * 100
                
                self.performance_history.append({
                    'timestamp': datetime.now(),
                    'portfolio_value': portfolio_value,
                    'pnl': pnl,
                    'pnl_percent': pnl_percent
                })
                
                # Print performance every 10 seconds
                if len(self.performance_history) % 20 == 0:
                    print(f"\n📊 PERFORMANCE UPDATE:")
                    print(f"   Portfolio Value: ${portfolio_value:.2f}")
                    print(f"   P&L: ${pnl:.2f} ({pnl_percent:.2f}%)")
                    print(f"   Total Orders: {len(self.trading_engine.orders)}")
                    print(f"   Positions: {self.trading_engine.positions}")
                    print("-" * 80)
                
                time.sleep(0.5)
                
            except Exception as e:
                if self.running:
                    logger.error(f"Performance monitoring error: {e}")
                    time.sleep(1)
    
    def generate_performance_report(self):
        """Generate comprehensive performance report"""
        print(f"\n" + "="*100)
        print("📊 LIVE TRADING DEMO PERFORMANCE REPORT")
        print("="*100)
        
        if not self.performance_history:
            print("No performance data available")
            return
        
        # Final metrics
        final_metrics = self.performance_history[-1]
        runtime = datetime.now() - self.start_time
        
        print(f"⏱️ Runtime: {runtime}")
        print(f"💰 Initial Balance: ${self.trading_engine.initial_balance:.2f}")
        print(f"📈 Final Portfolio Value: ${final_metrics['portfolio_value']:.2f}")
        print(f"💵 Total P&L: ${final_metrics['pnl']:.2f} ({final_metrics['pnl_percent']:.2f}%)")
        
        # Order statistics
        filled_orders = [o for o in self.trading_engine.orders if o.status == "FILLED"]
        buy_orders = [o for o in filled_orders if o.side == "BUY"]
        sell_orders = [o for o in filled_orders if o.side == "SELL"]
        
        print(f"\n📋 ORDER STATISTICS:")
        print(f"   Total Orders: {len(self.trading_engine.orders)}")
        print(f"   Filled Orders: {len(filled_orders)}")
        print(f"   Buy Orders: {len(buy_orders)}")
        print(f"   Sell Orders: {len(sell_orders)}")
        
        # Position summary
        print(f"\n💼 CURRENT POSITIONS:")
        for symbol, quantity in self.trading_engine.positions.items():
            if quantity > 0:
                current_price = self.market_feed.current_prices[symbol]
                position_value = quantity * current_price
                print(f"   {symbol}: {quantity:.4f} units (${position_value:.2f})")
        
        print(f"   Cash: ${self.trading_engine.balance:.2f}")
        
        # Signal statistics
        print(f"\n⚡ SIGNAL STATISTICS:")
        print(f"   Total Signals: {len(self.strategy.signals_history)}")
        
        if self.strategy.signals_history:
            buy_signals = [s for s in self.strategy.signals_history if s.action == "BUY"]
            sell_signals = [s for s in self.strategy.signals_history if s.action == "SELL"]
            avg_confidence = np.mean([s.confidence for s in self.strategy.signals_history])
            
            print(f"   Buy Signals: {len(buy_signals)}")
            print(f"   Sell Signals: {len(sell_signals)}")
            print(f"   Average Confidence: {avg_confidence:.2f}")
        
        # Performance metrics
        if len(self.performance_history) > 1:
            pnl_values = [p['pnl_percent'] for p in self.performance_history]
            max_drawdown = min(pnl_values)
            max_gain = max(pnl_values)
            volatility = np.std(pnl_values)
            
            print(f"\n📈 PERFORMANCE METRICS:")
            print(f"   Max Gain: {max_gain:.2f}%")
            print(f"   Max Drawdown: {max_drawdown:.2f}%")
            print(f"   Volatility: {volatility:.2f}%")
            
            if volatility > 0:
                sharpe_ratio = final_metrics['pnl_percent'] / volatility
                print(f"   Sharpe Ratio: {sharpe_ratio:.2f}")
    
    async def run_demo(self, duration_seconds: int = 60):
        """Run live trading demonstration"""
        print("="*100)
        print("🚀 STARTING LIVE MARKET DATA & TRADING DEMO")
        print("="*100)
        print(f"Duration: {duration_seconds} seconds")
        print(f"Symbols: {', '.join(self.market_feed.symbols)}")
        print(f"Initial Balance: ${self.trading_engine.initial_balance:.2f}")
        print("-" * 100)
        
        self.running = True
        self.start_time = datetime.now()
        
        # Start all components
        data_task = asyncio.create_task(self.start_market_data_feed())
        
        # Start threading components
        signal_thread = threading.Thread(target=self.process_trading_signals)
        trade_thread = threading.Thread(target=self.execute_trades)
        monitor_thread = threading.Thread(target=self.monitor_performance)
        
        signal_thread.start()
        trade_thread.start()
        monitor_thread.start()
        
        # Run for specified duration
        await asyncio.sleep(duration_seconds)
        
        # Stop all components
        print(f"\n⏹️ Stopping demo...")
        self.running = False
        data_task.cancel()
        
        signal_thread.join(timeout=2)
        trade_thread.join(timeout=2)
        monitor_thread.join(timeout=2)
        
        # Generate final report
        self.generate_performance_report()
        
        print(f"\n✅ Live trading demo completed successfully!")
        return self.performance_history, self.trading_engine.orders

async def main():
    """Main demonstration function"""
    demo = LiveTradingDemo()
    
    print("🎯 Starting 60-second live trading demonstration...")
    print("📈 This demo shows:")
    print("   • Live market data feeds")
    print("   • Real-time technical analysis")
    print("   • Automated signal generation")
    print("   • Order execution and risk management")
    print("   • Performance monitoring")
    
    await demo.run_demo(duration_seconds=60)

if __name__ == "__main__":
    asyncio.run(main())