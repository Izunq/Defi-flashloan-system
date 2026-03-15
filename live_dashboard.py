#!/usr/bin/env python3
"""
Real-Time Trading Dashboard
Web-based dashboard for live market data and trading visualization
"""

import asyncio
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.utils
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealTimeDashboard:
    """Real-time trading dashboard with web interface"""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'trading_dashboard_secret'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Data storage
        self.market_data = {}
        self.signals = []
        self.orders = []
        self.performance = []
        
        # Setup routes
        self.setup_routes()
        self.setup_socketio_events()
        
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            return render_template('dashboard.html')
        
        @self.app.route('/api/market-data')
        def get_market_data():
            return jsonify(self.market_data)
        
        @self.app.route('/api/signals')
        def get_signals():
            return jsonify([
                {
                    'symbol': s.symbol,
                    'action': s.action,
                    'price': s.price,
                    'confidence': s.confidence,
                    'timestamp': s.timestamp.isoformat()
                } for s in self.signals[-50:]  # Last 50 signals
            ])
        
        @self.app.route('/api/orders')
        def get_orders():
            return jsonify([
                {
                    'order_id': o.order_id,
                    'symbol': o.symbol,
                    'side': o.side,
                    'quantity': o.quantity,
                    'price': o.price,
                    'status': o.status,
                    'timestamp': o.timestamp.isoformat()
                } for o in self.orders[-50:]  # Last 50 orders
            ])
        
        @self.app.route('/api/charts/<symbol>')
        def get_chart_data(symbol):
            if symbol not in self.market_data:
                return jsonify({'error': 'Symbol not found'})
            
            data = self.market_data[symbol][-100:]  # Last 100 points
            
            fig = go.Figure()
            
            # Add price line
            fig.add_trace(go.Scatter(
                x=[d['timestamp'] for d in data],
                y=[d['price'] for d in data],
                mode='lines',
                name='Price',
                line=dict(color='#00ff88', width=2)
            ))
            
            # Add volume bars
            fig.add_trace(go.Bar(
                x=[d['timestamp'] for d in data],
                y=[d['volume'] for d in data],
                name='Volume',
                yaxis='y2',
                opacity=0.3
            ))
            
            fig.update_layout(
                title=f'{symbol} Live Price & Volume',
                xaxis_title='Time',
                yaxis_title='Price (USD)',
                yaxis2=dict(
                    title='Volume',
                    overlaying='y',
                    side='right'
                ),
                template='plotly_dark',
                height=400
            )
            
            return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    def setup_socketio_events(self):
        """Setup SocketIO events"""
        
        @self.socketio.on('connect')
        def handle_connect():
            logger.info('Client connected to dashboard')
            emit('status', {'msg': 'Connected to live trading dashboard'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            logger.info('Client disconnected from dashboard')
    
    def update_market_data(self, data):
        """Update market data and broadcast to clients"""
        symbol = data.symbol
        
        if symbol not in self.market_data:
            self.market_data[symbol] = []
        
        data_point = {
            'price': data.price,
            'volume': data.volume,
            'bid': data.bid,
            'ask': data.ask,
            'timestamp': data.timestamp.isoformat(),
            'exchange': data.exchange
        }
        
        self.market_data[symbol].append(data_point)
        
        # Keep only last 1000 points per symbol
        if len(self.market_data[symbol]) > 1000:
            self.market_data[symbol] = self.market_data[symbol][-1000:]
        
        # Broadcast to clients
        self.socketio.emit('market_data', {
            'symbol': symbol,
            'data': data_point
        })
    
    def update_signal(self, signal):
        """Update trading signal and broadcast"""
        self.signals.append(signal)
        
        signal_data = {
            'symbol': signal.symbol,
            'action': signal.action,
            'quantity': signal.quantity,
            'price': signal.price,
            'confidence': signal.confidence,
            'strategy': signal.strategy,
            'timestamp': signal.timestamp.isoformat()
        }
        
        self.socketio.emit('new_signal', signal_data)
    
    def update_order(self, order):
        """Update order and broadcast"""
        self.orders.append(order)
        
        order_data = {
            'order_id': order.order_id,
            'symbol': order.symbol,
            'side': order.side,
            'quantity': order.quantity,
            'price': order.price,
            'status': order.status,
            'timestamp': order.timestamp.isoformat()
        }
        
        self.socketio.emit('new_order', order_data)
    
    def update_performance(self, performance_data):
        """Update performance metrics"""
        self.performance.append(performance_data)
        
        perf_data = {
            'portfolio_value': performance_data['portfolio_value'],
            'pnl': performance_data['pnl'],
            'pnl_percent': performance_data['pnl_percent'],
            'timestamp': performance_data['timestamp'].isoformat()
        }
        
        self.socketio.emit('performance_update', perf_data)
    
    def run(self, host='localhost', port=5000, debug=False):
        """Run the dashboard server"""
        logger.info(f"Starting dashboard server on http://{host}:{port}")
        self.socketio.run(self.app, host=host, port=port, debug=debug)

# Create HTML template for the dashboard
dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Live Trading Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #0e1117;
            color: #fafafa;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        .panel {
            background-color: #1e1e1e;
            border-radius: 10px;
            padding: 20px;
            border: 1px solid #333;
        }
        .full-width {
            grid-column: 1 / -1;
        }
        .metric {
            display: inline-block;
            margin: 10px;
            padding: 10px 15px;
            background-color: #2a2a2a;
            border-radius: 5px;
            border-left: 4px solid #00ff88;
        }
        .signal {
            margin: 5px 0;
            padding: 8px;
            border-radius: 5px;
            font-size: 12px;
        }
        .signal.BUY {
            background-color: #0f4f3c;
            border-left: 4px solid #00ff88;
        }
        .signal.SELL {
            background-color: #4f0f0f;
            border-left: 4px solid #ff4444;
        }
        .order {
            margin: 5px 0;
            padding: 8px;
            border-radius: 5px;
            font-size: 12px;
            background-color: #2a2a2a;
        }
        .order.FILLED {
            border-left: 4px solid #00ff88;
        }
        .order.REJECTED {
            border-left: 4px solid #ff4444;
        }
        .status {
            position: fixed;
            top: 10px;
            right: 10px;
            padding: 10px;
            border-radius: 5px;
            background-color: #00ff88;
            color: #000;
            font-weight: bold;
        }
        .market-data {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
        }
        .ticker {
            flex: 1;
            min-width: 200px;
            padding: 15px;
            background-color: #2a2a2a;
            border-radius: 8px;
            border-left: 4px solid #00ff88;
        }
        .ticker-symbol {
            font-weight: bold;
            font-size: 16px;
            margin-bottom: 5px;
        }
        .ticker-price {
            font-size: 20px;
            color: #00ff88;
        }
        .ticker-change {
            font-size: 14px;
            margin-top: 5px;
        }
        h2 {
            color: #00ff88;
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="status" id="status">Connecting...</div>
    
    <div class="header">
        <h1>🚀 Live Trading Dashboard</h1>
        <div id="performance-metrics">
            <div class="metric">
                <div>Portfolio Value</div>
                <div id="portfolio-value">$10,000.00</div>
            </div>
            <div class="metric">
                <div>P&L</div>
                <div id="pnl">$0.00</div>
            </div>
            <div class="metric">
                <div>P&L %</div>
                <div id="pnl-percent">0.00%</div>
            </div>
        </div>
    </div>

    <div class="grid">
        <div class="panel">
            <h2>📈 Live Market Data</h2>
            <div class="market-data" id="market-data">
                <!-- Market data will be populated here -->
            </div>
        </div>

        <div class="panel">
            <h2>⚡ Recent Signals</h2>
            <div id="signals" style="max-height: 300px; overflow-y: auto;">
                <!-- Signals will be populated here -->
            </div>
        </div>

        <div class="panel">
            <h2>💼 Recent Orders</h2>
            <div id="orders" style="max-height: 300px; overflow-y: auto;">
                <!-- Orders will be populated here -->
            </div>
        </div>

        <div class="panel">
            <h2>📊 Performance Chart</h2>
            <div id="performance-chart" style="height: 300px;"></div>
        </div>
    </div>

    <script>
        // Initialize Socket.IO
        const socket = io();
        
        // Performance data for charting
        let performanceData = [];
        
        // Socket event handlers
        socket.on('connect', function() {
            document.getElementById('status').textContent = 'Connected';
            document.getElementById('status').style.backgroundColor = '#00ff88';
        });
        
        socket.on('disconnect', function() {
            document.getElementById('status').textContent = 'Disconnected';
            document.getElementById('status').style.backgroundColor = '#ff4444';
        });
        
        socket.on('market_data', function(data) {
            updateMarketData(data);
        });
        
        socket.on('new_signal', function(signal) {
            addSignal(signal);
        });
        
        socket.on('new_order', function(order) {
            addOrder(order);
        });
        
        socket.on('performance_update', function(performance) {
            updatePerformance(performance);
        });
        
        // Update functions
        function updateMarketData(data) {
            const container = document.getElementById('market-data');
            let ticker = document.getElementById('ticker-' + data.symbol.replace('/', ''));
            
            if (!ticker) {
                ticker = document.createElement('div');
                ticker.className = 'ticker';
                ticker.id = 'ticker-' + data.symbol.replace('/', '');
                container.appendChild(ticker);
            }
            
            ticker.innerHTML = `
                <div class="ticker-symbol">${data.symbol}</div>
                <div class="ticker-price">$${parseFloat(data.data.price).toFixed(4)}</div>
                <div class="ticker-change">
                    Bid: $${parseFloat(data.data.bid).toFixed(4)} | 
                    Ask: $${parseFloat(data.data.ask).toFixed(4)}
                </div>
                <div class="ticker-change">Vol: ${Math.round(data.data.volume)}</div>
            `;
        }
        
        function addSignal(signal) {
            const container = document.getElementById('signals');
            const signalDiv = document.createElement('div');
            signalDiv.className = `signal ${signal.action}`;
            signalDiv.innerHTML = `
                <strong>${signal.action}</strong> ${signal.quantity.toFixed(2)} ${signal.symbol} 
                at $${signal.price.toFixed(4)} | 
                Confidence: ${(signal.confidence * 100).toFixed(0)}% | 
                ${signal.strategy}
                <br><small>${new Date(signal.timestamp).toLocaleTimeString()}</small>
            `;
            
            container.insertBefore(signalDiv, container.firstChild);
            
            // Keep only last 20 signals
            while (container.children.length > 20) {
                container.removeChild(container.lastChild);
            }
        }
        
        function addOrder(order) {
            const container = document.getElementById('orders');
            const orderDiv = document.createElement('div');
            orderDiv.className = `order ${order.status.split('_')[0]}`;
            orderDiv.innerHTML = `
                <strong>${order.side}</strong> ${order.quantity.toFixed(2)} ${order.symbol} 
                at $${order.price.toFixed(4)} | 
                Status: ${order.status}
                <br><small>${order.order_id} - ${new Date(order.timestamp).toLocaleTimeString()}</small>
            `;
            
            container.insertBefore(orderDiv, container.firstChild);
            
            // Keep only last 20 orders
            while (container.children.length > 20) {
                container.removeChild(container.lastChild);
            }
        }
        
        function updatePerformance(performance) {
            document.getElementById('portfolio-value').textContent = '$' + performance.portfolio_value.toFixed(2);
            document.getElementById('pnl').textContent = '$' + performance.pnl.toFixed(2);
            document.getElementById('pnl-percent').textContent = performance.pnl_percent.toFixed(2) + '%';
            
            // Update performance chart
            performanceData.push({
                x: new Date(performance.timestamp),
                y: performance.pnl_percent
            });
            
            // Keep only last 100 points
            if (performanceData.length > 100) {
                performanceData = performanceData.slice(-100);
            }
            
            updatePerformanceChart();
        }
        
        function updatePerformanceChart() {
            const trace = {
                x: performanceData.map(d => d.x),
                y: performanceData.map(d => d.y),
                type: 'scatter',
                mode: 'lines',
                name: 'P&L %',
                line: {color: '#00ff88', width: 2}
            };
            
            const layout = {
                title: 'Performance Over Time',
                xaxis: {title: 'Time'},
                yaxis: {title: 'P&L %'},
                paper_bgcolor: '#1e1e1e',
                plot_bgcolor: '#1e1e1e',
                font: {color: '#fafafa'}
            };
            
            Plotly.newPlot('performance-chart', [trace], layout);
        }
        
        // Initialize empty performance chart
        updatePerformanceChart();
    </script>
</body>
</html>
"""

# Save the HTML template
import os
templates_dir = "templates"
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)

with open(os.path.join(templates_dir, "dashboard.html"), "w") as f:
    f.write(dashboard_html)

if __name__ == "__main__":
    dashboard = RealTimeDashboard()
    print("🌐 Dashboard will be available at: http://localhost:5000")
    dashboard.run(debug=True)