#!/usr/bin/env python3
"""
Integrated Live Trading Demo with Web Dashboard
Comprehensive demonstration combining live trading with real-time web visualization
"""

import asyncio
import threading
import time
from datetime import datetime
import logging
from live_trading_demo import LiveTradingDemo
from live_dashboard import RealTimeDashboard

logger = logging.getLogger(__name__)

class IntegratedTradingSystem:
    """Integrated system combining trading engine with web dashboard"""
    
    def __init__(self):
        self.trading_demo = LiveTradingDemo()
        self.dashboard = RealTimeDashboard()
        self.dashboard_thread = None
        self.running = False
        
    def start_dashboard_server(self):
        """Start the web dashboard server"""
        logger.info("🌐 Starting web dashboard server...")
        self.dashboard.run(host='localhost', port=5000, debug=False)
    
    def connect_trading_to_dashboard(self):
        """Connect trading data to dashboard"""
        logger.info("🔗 Connecting trading engine to dashboard...")
        
        # Override trading demo methods to send data to dashboard
        original_market_data_put = self.trading_demo.market_data_queue.put
        original_signals_put = self.trading_demo.signals_queue.put
        original_orders_put = self.trading_demo.orders_queue.put
        
        def enhanced_market_data_put(data):
            original_market_data_put(data)
            self.dashboard.update_market_data(data)
        
        def enhanced_signals_put(signal):
            original_signals_put(signal)
            self.dashboard.update_signal(signal)
        
        def enhanced_orders_put(order):
            original_orders_put(order)
            self.dashboard.update_order(order)
        
        # Override methods
        self.trading_demo.market_data_queue.put = enhanced_market_data_put
        self.trading_demo.signals_queue.put = enhanced_signals_put
        self.trading_demo.orders_queue.put = enhanced_orders_put
        
        # Override performance monitoring to send to dashboard
        original_monitor = self.trading_demo.monitor_performance
        
        def enhanced_monitor_performance():
            while self.trading_demo.running:
                try:
                    current_prices = {symbol: self.trading_demo.market_feed.current_prices[symbol] 
                                    for symbol in self.trading_demo.market_feed.symbols}
                    
                    portfolio_value = self.trading_demo.trading_engine.get_portfolio_value(current_prices)
                    pnl = self.trading_demo.trading_engine.get_pnl(current_prices)
                    pnl_percent = (pnl / self.trading_demo.trading_engine.initial_balance) * 100
                    
                    performance_data = {
                        'timestamp': datetime.now(),
                        'portfolio_value': portfolio_value,
                        'pnl': pnl,
                        'pnl_percent': pnl_percent
                    }
                    
                    self.trading_demo.performance_history.append(performance_data)
                    
                    # Send to dashboard
                    self.dashboard.update_performance(performance_data)
                    
                    # Print performance every 10 seconds
                    if len(self.trading_demo.performance_history) % 20 == 0:
                        print(f"\n📊 PERFORMANCE UPDATE:")
                        print(f"   Portfolio Value: ${portfolio_value:.2f}")
                        print(f"   P&L: ${pnl:.2f} ({pnl_percent:.2f}%)")
                        print(f"   Total Orders: {len(self.trading_demo.trading_engine.orders)}")
                        print(f"   Positions: {self.trading_demo.trading_engine.positions}")
                        print("-" * 80)
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    if self.trading_demo.running:
                        logger.error(f"Performance monitoring error: {e}")
                        time.sleep(1)
        
        self.trading_demo.monitor_performance = enhanced_monitor_performance
    
    async def run_integrated_demo(self, duration_seconds: int = 120):
        """Run integrated demo with both trading and dashboard"""
        print("="*100)
        print("🚀 STARTING INTEGRATED LIVE TRADING & DASHBOARD DEMO")
        print("="*100)
        print(f"Duration: {duration_seconds} seconds")
        print(f"Dashboard: http://localhost:5000")
        print(f"Symbols: {', '.join(self.trading_demo.market_feed.symbols)}")
        print(f"Initial Balance: ${self.trading_demo.trading_engine.initial_balance:.2f}")
        print("-" * 100)
        
        # Start dashboard server in separate thread
        self.dashboard_thread = threading.Thread(target=self.start_dashboard_server, daemon=True)
        self.dashboard_thread.start()
        
        # Wait for dashboard to start
        await asyncio.sleep(3)
        print("✅ Dashboard server started at http://localhost:5000")
        
        # Connect trading to dashboard
        self.connect_trading_to_dashboard()
        print("✅ Trading engine connected to dashboard")
        
        # Run trading demo
        self.running = True
        self.trading_demo.running = True
        self.trading_demo.start_time = datetime.now()
        
        # Start all trading components
        data_task = asyncio.create_task(self.trading_demo.start_market_data_feed())
        
        # Start threading components
        signal_thread = threading.Thread(target=self.trading_demo.process_trading_signals)
        trade_thread = threading.Thread(target=self.trading_demo.execute_trades)
        monitor_thread = threading.Thread(target=self.trading_demo.monitor_performance)
        
        signal_thread.start()
        trade_thread.start()
        monitor_thread.start()
        
        print(f"✅ All systems operational - trading for {duration_seconds} seconds")
        print(f"🌐 Open http://localhost:5000 in your browser to view live dashboard")
        
        # Run for specified duration
        await asyncio.sleep(duration_seconds)
        
        # Stop all components
        print(f"\n⏹️ Stopping integrated demo...")
        self.running = False
        self.trading_demo.running = False
        data_task.cancel()
        
        signal_thread.join(timeout=2)
        trade_thread.join(timeout=2)
        monitor_thread.join(timeout=2)
        
        # Generate final report
        self.trading_demo.generate_performance_report()
        
        print(f"\n✅ Integrated demo completed!")
        print(f"🌐 Dashboard remains available at http://localhost:5000")
        
        return self.trading_demo.performance_history, self.trading_demo.trading_engine.orders

async def main():
    """Main function for integrated demo"""
    print("🎯 Starting integrated live trading and dashboard demonstration...")
    print("\n📱 This demo includes:")
    print("   • Real-time market data simulation")
    print("   • Advanced technical analysis")
    print("   • Automated trading signals")
    print("   • Order execution and risk management")
    print("   • Live web dashboard with charts")
    print("   • Performance monitoring")
    
    print("\n🌐 Dashboard Features:")
    print("   • Live price feeds for 5 cryptocurrencies")
    print("   • Real-time trading signals visualization")
    print("   • Order execution tracking")
    print("   • Performance charts and metrics")
    print("   • Responsive web interface")
    
    integrated_system = IntegratedTradingSystem()
    await integrated_system.run_integrated_demo(duration_seconds=120)

if __name__ == "__main__":
    asyncio.run(main())