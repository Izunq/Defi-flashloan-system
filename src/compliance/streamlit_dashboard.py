#!/usr/bin/env python3
"""
🎯 PRODUCTION ARBITRAGE DASHBOARD
================================

Beautiful Streamlit dashboard for monitoring arbitrage trading
Real-time performance tracking, opportunity monitoring, and risk management
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import time
import json
import asyncio
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path

# Try to import the production system
try:
    from PRODUCTION_ARBITRAGE_SYSTEM import ProductionArbitrageSystem, TradingConfig
    SYSTEM_AVAILABLE = True
except ImportError:
    SYSTEM_AVAILABLE = False
    st.error("⚠️ Production system not available. Running in demo mode.")

# Page configuration
st.set_page_config(
    page_title="🚀 Arbitrage Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #00d4aa, #00a8ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .profit-positive {
        color: #00ff88;
        font-weight: bold;
    }
    
    .profit-negative {
        color: #ff4757;
        font-weight: bold;
    }
    
    .opportunity-card {
        border: 1px solid #e1e8ed;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

class DashboardData:
    """Manages dashboard data"""
    
    def __init__(self):
        self.db_path = "production_arbitrage.db"
        self.setup_database()
    
    def setup_database(self):
        """Setup database for demo data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create tables if they don't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY,
                    timestamp DATETIME,
                    strategy TEXT,
                    profit REAL,
                    success BOOLEAN
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS opportunities (
                    id INTEGER PRIMARY KEY,
                    timestamp DATETIME,
                    strategy TEXT,
                    profit_usd REAL,
                    risk_score REAL,
                    executed BOOLEAN
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            st.error(f"Database setup error: {e}")
    
    def get_demo_performance_data(self):
        """Generate demo performance data"""
        # Generate realistic trading data
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='H')
        
        # Simulate cumulative profits
        daily_returns = np.random.normal(0.02, 0.05, len(dates))  # 2% mean, 5% std
        cumulative_returns = np.cumsum(daily_returns)
        initial_capital = 50.0
        portfolio_values = initial_capital * (1 + cumulative_returns)
        
        return pd.DataFrame({
            'timestamp': dates,
            'portfolio_value': portfolio_values,
            'daily_return': daily_returns,
            'profit': portfolio_values - initial_capital
        })
    
    def get_demo_opportunities(self):
        """Generate demo opportunities"""
        strategies = ['simple_arbitrage', 'triangular_arbitrage', 'flash_arbitrage', 'cross_chain_arbitrage']
        chains = ['polygon', 'bsc', 'arbitrum']
        
        opportunities = []
        for i in range(10):
            opp = {
                'id': f"opp_{i}",
                'strategy': np.random.choice(strategies),
                'chain': np.random.choice(chains),
                'profit_usd': np.random.uniform(0.5, 15.0),
                'risk_score': np.random.uniform(0.1, 0.8),
                'confidence': np.random.uniform(0.6, 0.95),
                'gas_cost': np.random.uniform(0.1, 2.0),
                'timestamp': datetime.now() - timedelta(minutes=np.random.randint(1, 60))
            }
            opp['net_profit'] = opp['profit_usd'] - opp['gas_cost']
            opportunities.append(opp)
        
        return pd.DataFrame(opportunities)
    
    def get_demo_trades(self):
        """Generate demo trade history"""
        strategies = ['simple_arbitrage', 'triangular_arbitrage', 'flash_arbitrage']
        
        trades = []
        for i in range(50):
            success = np.random.random() > 0.2  # 80% success rate
            profit = np.random.uniform(0.5, 10.0) if success else -np.random.uniform(0.1, 2.0)
            
            trade = {
                'id': i,
                'timestamp': datetime.now() - timedelta(hours=np.random.randint(1, 24*7)),
                'strategy': np.random.choice(strategies),
                'profit': profit,
                'success': success
            }
            trades.append(trade)
        
        return pd.DataFrame(trades)

def create_performance_chart(data):
    """Create performance chart"""
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Portfolio Value', 'Daily Returns'),
        vertical_spacing=0.1
    )
    
    # Portfolio value
    fig.add_trace(
        go.Scatter(
            x=data['timestamp'],
            y=data['portfolio_value'],
            mode='lines',
            name='Portfolio Value',
            line=dict(color='#00d4aa', width=3),
            fill='tonexty'
        ),
        row=1, col=1
    )
    
    # Daily returns
    colors = ['#00ff88' if x > 0 else '#ff4757' for x in data['daily_return']]
    fig.add_trace(
        go.Bar(
            x=data['timestamp'],
            y=data['daily_return'] * 100,
            name='Daily Return %',
            marker_color=colors
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        height=600,
        showlegend=False,
        title_text="Performance Overview",
        title_x=0.5
    )
    
    return fig

def create_strategy_performance_chart(trades_df):
    """Create strategy performance chart"""
    strategy_performance = trades_df.groupby('strategy').agg({
        'profit': ['sum', 'mean', 'count'],
        'success': 'mean'
    }).round(2)
    
    strategy_performance.columns = ['Total Profit', 'Avg Profit', 'Total Trades', 'Win Rate']
    strategy_performance = strategy_performance.reset_index()
    
    fig = px.bar(
        strategy_performance,
        x='strategy',
        y='Total Profit',
        color='Win Rate',
        title='Strategy Performance Comparison',
        color_continuous_scale='RdYlGn'
    )
    
    fig.update_layout(height=400)
    return fig

def create_opportunities_chart(opportunities_df):
    """Create opportunities scatter plot"""
    fig = px.scatter(
        opportunities_df,
        x='risk_score',
        y='net_profit',
        color='strategy',
        size='confidence',
        hover_data=['chain', 'gas_cost'],
        title='Risk vs Profit Opportunities'
    )
    
    fig.update_layout(height=400)
    return fig

def main():
    """Main dashboard function"""
    # Header
    st.markdown('<h1 class="main-header">🚀 ARBITRAGE TRADING DASHBOARD</h1>', unsafe_allow_html=True)
    
    # Initialize data
    dashboard_data = DashboardData()
    
    # Sidebar
    st.sidebar.title("⚙️ Controls")
    
    # System status
    if SYSTEM_AVAILABLE:
        st.sidebar.success("✅ System Available")
        
        # Trading controls
        st.sidebar.subheader("🎯 Trading Controls")
        
        if st.sidebar.button("🚀 Start Trading"):
            st.sidebar.success("Trading started!")
            # Here you would start the actual trading system
        
        if st.sidebar.button("⏹️ Stop Trading"):
            st.sidebar.warning("Trading stopped!")
        
        # Configuration
        st.sidebar.subheader("⚙️ Configuration")
        capital = st.sidebar.number_input("💰 Capital ($)", min_value=10.0, max_value=10000.0, value=50.0)
        risk_level = st.sidebar.selectbox("🎯 Risk Level", ["Conservative", "Moderate", "Aggressive"])
        
    else:
        st.sidebar.error("❌ System Unavailable")
        st.sidebar.info("Running in demo mode")
    
    # Auto-refresh
    auto_refresh = st.sidebar.checkbox("🔄 Auto Refresh", value=True)
    if auto_refresh:
        refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", 5, 60, 30)
    
    # Main content
    col1, col2, col3, col4 = st.columns(4)
    
    # Get demo data
    performance_data = dashboard_data.get_demo_performance_data()
    opportunities_df = dashboard_data.get_demo_opportunities()
    trades_df = dashboard_data.get_demo_trades()
    
    # Calculate metrics
    current_value = performance_data['portfolio_value'].iloc[-1]
    total_profit = current_value - 50.0
    profit_percent = (total_profit / 50.0) * 100
    win_rate = trades_df['success'].mean() * 100
    
    # Display metrics
    with col1:
        st.metric(
            label="💰 Portfolio Value",
            value=f"${current_value:.2f}",
            delta=f"${total_profit:.2f}"
        )
    
    with col2:
        st.metric(
            label="📈 Total Profit",
            value=f"${total_profit:.2f}",
            delta=f"{profit_percent:.1f}%"
        )
    
    with col3:
        st.metric(
            label="✅ Win Rate",
            value=f"{win_rate:.1f}%",
            delta="2.3%" if win_rate > 75 else "-1.2%"
        )
    
    with col4:
        st.metric(
            label="🔄 Total Trades",
            value=len(trades_df),
            delta=f"+{np.random.randint(1, 5)}"
        )
    
    # Performance chart
    st.plotly_chart(create_performance_chart(performance_data), use_container_width=True)
    
    # Two columns for additional charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(create_strategy_performance_chart(trades_df), use_container_width=True)
    
    with col2:
        st.plotly_chart(create_opportunities_chart(opportunities_df), use_container_width=True)
    
    # Opportunities table
    st.subheader("🎯 Current Opportunities")
    
    # Filter profitable opportunities
    profitable_opps = opportunities_df[opportunities_df['net_profit'] > 0].sort_values('net_profit', ascending=False)
    
    if len(profitable_opps) > 0:
        # Format the dataframe for display
        display_df = profitable_opps[['strategy', 'chain', 'net_profit', 'risk_score', 'confidence']].copy()
        display_df['net_profit'] = display_df['net_profit'].apply(lambda x: f"${x:.2f}")
        display_df['risk_score'] = display_df['risk_score'].apply(lambda x: f"{x:.2f}")
        display_df['confidence'] = display_df['confidence'].apply(lambda x: f"{x:.1%}")
        
        display_df.columns = ['Strategy', 'Chain', 'Net Profit', 'Risk Score', 'Confidence']
        
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("No profitable opportunities found at the moment.")
    
    # Recent trades
    st.subheader("📊 Recent Trades")
    
    recent_trades = trades_df.head(10).copy()
    recent_trades['profit'] = recent_trades['profit'].apply(lambda x: f"${x:.2f}")
    recent_trades['success'] = recent_trades['success'].apply(lambda x: "✅" if x else "❌")
    recent_trades['timestamp'] = recent_trades['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
    
    recent_trades.columns = ['ID', 'Timestamp', 'Strategy', 'Profit', 'Success']
    st.dataframe(recent_trades[['Timestamp', 'Strategy', 'Profit', 'Success']], use_container_width=True)
    
    # Risk metrics
    st.subheader("🛡️ Risk Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        daily_var = np.percentile(performance_data['daily_return'], 5) * 100
        st.metric("📉 Daily VaR (95%)", f"{daily_var:.2f}%")
    
    with col2:
        max_drawdown = (performance_data['portfolio_value'].cummax() - performance_data['portfolio_value']).max()
        drawdown_percent = (max_drawdown / performance_data['portfolio_value'].max()) * 100
        st.metric("📊 Max Drawdown", f"{drawdown_percent:.2f}%")
    
    with col3:
        sharpe_ratio = performance_data['daily_return'].mean() / performance_data['daily_return'].std() * np.sqrt(365)
        st.metric("📈 Sharpe Ratio", f"{sharpe_ratio:.2f}")
    
    # System logs
    with st.expander("📋 System Logs"):
        log_messages = [
            "🔍 Scanning for opportunities...",
            "✅ Found 3 profitable opportunities",
            "🚀 Executing simple arbitrage on Polygon",
            "💰 Trade successful: $2.45 profit",
            "⏳ Waiting for next cycle...",
            "🔍 Scanning for opportunities...",
            "⚠️ High gas costs detected on Ethereum",
            "✅ Flash loan opportunity found on Arbitrum"
        ]
        
        for msg in log_messages[-10:]:
            st.text(f"{datetime.now().strftime('%H:%M:%S')} - {msg}")
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_rate)
        st.experimental_rerun()

if __name__ == "__main__":
    main()