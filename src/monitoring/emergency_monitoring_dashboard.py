#!/usr/bin/env python3
"""
🚨 EMERGENCY MONITORING DASHBOARD
=================================

Real-time web dashboard for emergency monitoring system.
Provides live system status, alerts, and control interface.

Features:
- Real-time system status
- Interactive alert management
- Component health monitoring
- Emergency response controls
- Historical metrics visualization
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from flask import Flask, render_template_string, jsonify, request
from flask_socketio import SocketIO, emit
import threading
import time

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'emergency_monitoring_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global monitoring system reference
monitoring_system = None

# Dashboard HTML template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚨 Emergency Monitoring Dashboard</title>
    <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            color: #ffffff;
            min-height: 100vh;
        }
        
        .header {
            background: linear-gradient(90deg, #ff4444 0%, #cc0000 100%);
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }
        
        .status-badge {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 1.2em;
            margin-top: 10px;
        }
        
        .status-healthy { background: #28a745; }
        .status-warning { background: #ffc107; color: #000; }
        .status-degraded { background: #fd7e14; }
        .status-critical { background: #dc3545; }
        .status-emergency { background: #6f42c1; animation: pulse 1s infinite; }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            padding: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .card {
            background: rgba(45, 45, 45, 0.9);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.3);
            border-left: 4px solid #007bff;
            transition: transform 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
        }
        
        .card h3 {
            margin-bottom: 15px;
            color: #ffffff;
            font-size: 1.3em;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }
        
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
        }
        
        .metric {
            text-align: center;
            padding: 15px;
            background: rgba(0,0,0,0.3);
            border-radius: 8px;
        }
        
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #00d4ff;
        }
        
        .metric-label {
            font-size: 0.9em;
            color: #ccc;
            margin-top: 5px;
        }
        
        .alerts-container {
            max-height: 400px;
            overflow-y: auto;
        }
        
        .alert {
            padding: 12px;
            margin: 8px 0;
            border-radius: 6px;
            border-left: 4px solid;
        }
        
        .alert-low { 
            background: rgba(23, 162, 184, 0.2); 
            border-color: #17a2b8; 
        }
        
        .alert-medium { 
            background: rgba(255, 193, 7, 0.2); 
            border-color: #ffc107; 
        }
        
        .alert-high { 
            background: rgba(220, 53, 69, 0.2); 
            border-color: #dc3545; 
        }
        
        .alert-critical { 
            background: rgba(111, 66, 193, 0.2); 
            border-color: #6f42c1; 
            animation: glow 2s infinite;
        }
        
        .alert-emergency { 
            background: rgba(255, 0, 0, 0.3); 
            border-color: #ff0000; 
            animation: emergency-glow 1s infinite;
        }
        
        @keyframes glow {
            0% { box-shadow: 0 0 5px rgba(111, 66, 193, 0.5); }
            50% { box-shadow: 0 0 20px rgba(111, 66, 193, 0.8); }
            100% { box-shadow: 0 0 5px rgba(111, 66, 193, 0.5); }
        }
        
        @keyframes emergency-glow {
            0% { box-shadow: 0 0 10px rgba(255, 0, 0, 0.5); }
            50% { box-shadow: 0 0 30px rgba(255, 0, 0, 1); }
            100% { box-shadow: 0 0 10px rgba(255, 0, 0, 0.5); }
        }
        
        .component-status {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            margin: 5px 0;
            background: rgba(0,0,0,0.3);
            border-radius: 6px;
        }
        
        .component-name {
            font-weight: bold;
        }
        
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-left: 10px;
        }
        
        .status-healthy-indicator { background: #28a745; }
        .status-warning-indicator { background: #ffc107; }
        .status-degraded-indicator { background: #fd7e14; }
        .status-critical-indicator { background: #dc3545; }
        .status-emergency-indicator { background: #6f42c1; animation: pulse 1s infinite; }
        .status-offline-indicator { background: #6c757d; }
        
        .emergency-controls {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }
        
        .emergency-btn {
            padding: 12px;
            border: none;
            border-radius: 6px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .emergency-btn:hover {
            transform: scale(1.05);
        }
        
        .btn-pause {
            background: #ffc107;
            color: #000;
        }
        
        .btn-shutdown {
            background: #dc3545;
            color: #fff;
        }
        
        .btn-restart {
            background: #28a745;
            color: #fff;
        }
        
        .btn-alert {
            background: #6f42c1;
            color: #fff;
        }
        
        .chart-container {
            height: 300px;
            margin-top: 20px;
        }
        
        .timestamp {
            text-align: center;
            color: #888;
            font-size: 0.9em;
            margin-top: 20px;
        }
        
        .connection-status {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            z-index: 1000;
        }
        
        .connected { background: #28a745; }
        .disconnected { background: #dc3545; animation: pulse 1s infinite; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚨 Emergency Monitoring Dashboard</h1>
        <div id="overall-status" class="status-badge status-healthy">HEALTHY</div>
    </div>
    
    <div id="connection-status" class="connection-status disconnected">
        🔴 Connecting...
    </div>
    
    <div class="dashboard-grid">
        <!-- System Health Card -->
        <div class="card">
            <h3>📊 System Health</h3>
            <div class="metric-grid">
                <div class="metric">
                    <div id="cpu-usage" class="metric-value">0%</div>
                    <div class="metric-label">CPU Usage</div>
                </div>
                <div class="metric">
                    <div id="memory-usage" class="metric-value">0%</div>
                    <div class="metric-label">Memory Usage</div>
                </div>
                <div class="metric">
                    <div id="disk-usage" class="metric-value">0%</div>
                    <div class="metric-label">Disk Usage</div>
                </div>
                <div class="metric">
                    <div id="error-rate" class="metric-value">0%</div>
                    <div class="metric-label">Error Rate</div>
                </div>
            </div>
        </div>
        
        <!-- Alert Summary Card -->
        <div class="card">
            <h3>🚨 Alert Summary</h3>
            <div class="metric-grid">
                <div class="metric">
                    <div id="total-alerts" class="metric-value">0</div>
                    <div class="metric-label">Active Alerts</div>
                </div>
                <div class="metric">
                    <div id="critical-alerts" class="metric-value">0</div>
                    <div class="metric-label">Critical Alerts</div>
                </div>
            </div>
        </div>
        
        <!-- Component Status Card -->
        <div class="card">
            <h3>🔧 Component Status</h3>
            <div id="component-status-list">
                <!-- Component statuses will be populated here -->
            </div>
        </div>
        
        <!-- Emergency Controls Card -->
        <div class="card">
            <h3>🛠️ Emergency Controls</h3>
            <div class="emergency-controls">
                <button class="emergency-btn btn-pause" onclick="pauseSystem()">⏸️ Pause Trading</button>
                <button class="emergency-btn btn-shutdown" onclick="emergencyShutdown()">🛑 Emergency Stop</button>
                <button class="emergency-btn btn-restart" onclick="restartSystem()">🔄 Restart System</button>
                <button class="emergency-btn btn-alert" onclick="testAlert()">📢 Test Alert</button>
            </div>
        </div>
        
        <!-- Recent Alerts Card -->
        <div class="card" style="grid-column: span 2;">
            <h3>📋 Recent Alerts</h3>
            <div id="alerts-container" class="alerts-container">
                <!-- Alerts will be populated here -->
            </div>
        </div>
        
        <!-- Metrics Chart Card -->
        <div class="card" style="grid-column: span 2;">
            <h3>📈 System Metrics (Last 24 Hours)</h3>
            <div class="chart-container">
                <canvas id="metricsChart"></canvas>
            </div>
        </div>
    </div>
    
    <div class="timestamp">
        Last updated: <span id="last-updated">Never</span>
    </div>

    <script>
        // Socket.IO connection
        const socket = io();
        
        // Chart configuration
        let metricsChart;
        
        socket.on('connect', function() {
            console.log('Connected to monitoring system');
            document.getElementById('connection-status').className = 'connection-status connected';
            document.getElementById('connection-status').innerHTML = '🟢 Connected';
        });
        
        socket.on('disconnect', function() {
            console.log('Disconnected from monitoring system');
            document.getElementById('connection-status').className = 'connection-status disconnected';
            document.getElementById('connection-status').innerHTML = '🔴 Disconnected';
        });
        
        socket.on('dashboard_update', function(data) {
            updateDashboard(data);
        });
        
        function updateDashboard(data) {
            // Update overall status
            const overallStatus = document.getElementById('overall-status');
            overallStatus.textContent = data.overall_status.toUpperCase();
            overallStatus.className = `status-badge status-${data.overall_status}`;
            
            // Update system metrics
            if (data.recent_metrics) {
                document.getElementById('cpu-usage').textContent = data.recent_metrics.cpu_usage.toFixed(1) + '%';
                document.getElementById('memory-usage').textContent = data.recent_metrics.memory_usage.toFixed(1) + '%';
                document.getElementById('disk-usage').textContent = data.recent_metrics.disk_usage.toFixed(1) + '%';
                document.getElementById('error-rate').textContent = (data.recent_metrics.error_rate * 100).toFixed(2) + '%';
            }
            
            // Update alert counts
            document.getElementById('total-alerts').textContent = data.active_alerts_count;
            document.getElementById('critical-alerts').textContent = data.critical_alerts_count;
            
            // Update component status
            updateComponentStatus(data.component_status);
            
            // Update recent alerts
            updateRecentAlerts(data.recent_alerts);
            
            // Update timestamp
            document.getElementById('last-updated').textContent = new Date().toLocaleString();
        }
        
        function updateComponentStatus(componentStatus) {
            const container = document.getElementById('component-status-list');
            container.innerHTML = '';
            
            for (const [component, status] of Object.entries(componentStatus)) {
                const div = document.createElement('div');
                div.className = 'component-status';
                div.innerHTML = `
                    <span class="component-name">${component.replace('_', ' ').toUpperCase()}</span>
                    <span class="status-indicator status-${status}-indicator"></span>
                `;
                container.appendChild(div);
            }
        }
        
        function updateRecentAlerts(alerts) {
            const container = document.getElementById('alerts-container');
            container.innerHTML = '';
            
            if (alerts.length === 0) {
                container.innerHTML = '<div style="text-align: center; color: #888; padding: 20px;">No recent alerts</div>';
                return;
            }
            
            alerts.forEach(alert => {
                const div = document.createElement('div');
                div.className = `alert alert-${alert.severity}`;
                div.innerHTML = `
                    <div style="font-weight: bold;">${alert.title}</div>
                    <div style="font-size: 0.9em; color: #ccc;">${alert.component} • ${new Date(alert.timestamp).toLocaleString()}</div>
                `;
                container.appendChild(div);
            });
        }
        
        function initializeChart() {
            const ctx = document.getElementById('metricsChart').getContext('2d');
            metricsChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'CPU Usage (%)',
                            data: [],
                            borderColor: '#ff6384',
                            backgroundColor: 'rgba(255, 99, 132, 0.1)',
                            tension: 0.4
                        },
                        {
                            label: 'Memory Usage (%)',
                            data: [],
                            borderColor: '#36a2eb',
                            backgroundColor: 'rgba(54, 162, 235, 0.1)',
                            tension: 0.4
                        },
                        {
                            label: 'Error Rate (%)',
                            data: [],
                            borderColor: '#ffce56',
                            backgroundColor: 'rgba(255, 206, 86, 0.1)',
                            tension: 0.4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: {
                                color: '#ffffff'
                            }
                        }
                    },
                    scales: {
                        x: {
                            ticks: {
                                color: '#ffffff'
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            }
                        },
                        y: {
                            ticks: {
                                color: '#ffffff'
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            }
                        }
                    }
                }
            });
        }
        
        // Emergency control functions
        function pauseSystem() {
            if (confirm('Are you sure you want to pause the trading system?')) {
                socket.emit('emergency_action', {action: 'pause_trading'});
                alert('Trading system paused');
            }
        }
        
        function emergencyShutdown() {
            if (confirm('⚠️ EMERGENCY SHUTDOWN - This will stop all operations. Are you sure?')) {
                socket.emit('emergency_action', {action: 'emergency_shutdown'});
                alert('Emergency shutdown initiated');
            }
        }
        
        function restartSystem() {
            if (confirm('Are you sure you want to restart the system?')) {
                socket.emit('emergency_action', {action: 'restart_system'});
                alert('System restart initiated');
            }
        }
        
        function testAlert() {
            socket.emit('emergency_action', {action: 'test_alert'});
            alert('Test alert sent');
        }
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            initializeChart();
            
            // Request initial data
            socket.emit('request_dashboard_data');
        });
        
        // Auto-refresh dashboard data every 5 seconds
        setInterval(() => {
            socket.emit('request_dashboard_data');
        }, 5000);
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """Serve the emergency monitoring dashboard"""
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/status')
def get_status():
    """Get current system status via API"""
    global monitoring_system
    if monitoring_system:
        return jsonify(asyncio.run(monitoring_system.get_dashboard_data()))
    else:
        return jsonify({'error': 'Monitoring system not available'})

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('connected', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

@socketio.on('request_dashboard_data')
def handle_dashboard_data_request():
    """Handle dashboard data request"""
    global monitoring_system
    if monitoring_system:
        data = asyncio.run(monitoring_system.get_dashboard_data())
        emit('dashboard_update', data)

@socketio.on('emergency_action')
def handle_emergency_action(data):
    """Handle emergency actions from dashboard"""
    action = data.get('action')
    print(f"Emergency action requested: {action}")
    
    # Here you would implement actual emergency actions
    if action == 'pause_trading':
        # Implement pause trading logic
        emit('action_response', {'status': 'success', 'message': 'Trading paused'})
    elif action == 'emergency_shutdown':
        # Implement emergency shutdown logic
        emit('action_response', {'status': 'success', 'message': 'Emergency shutdown initiated'})
    elif action == 'restart_system':
        # Implement restart logic
        emit('action_response', {'status': 'success', 'message': 'System restart initiated'})
    elif action == 'test_alert':
        # Implement test alert logic
        emit('action_response', {'status': 'success', 'message': 'Test alert sent'})

def run_dashboard(monitoring_system_instance, host='0.0.0.0', port=8080):
    """Run the dashboard server"""
    global monitoring_system
    monitoring_system = monitoring_system_instance
    
    print(f"🌐 Starting Emergency Monitoring Dashboard on http://{host}:{port}")
    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)

def start_dashboard_thread(monitoring_system_instance, host='0.0.0.0', port=8080):
    """Start dashboard in a separate thread"""
    dashboard_thread = threading.Thread(
        target=run_dashboard,
        args=(monitoring_system_instance, host, port),
        daemon=True
    )
    dashboard_thread.start()
    return dashboard_thread

if __name__ == '__main__':
    print("🚨 Emergency Monitoring Dashboard")
    print("Visit http://localhost:8080 to view the dashboard")
    run_dashboard(None)
