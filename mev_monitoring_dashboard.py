#!/usr/bin/env python3
"""
MEV Protection Monitoring Dashboard
==================================

Real-time monitoring dashboard for MEV protection system:
- MEV attack detection metrics
- Transaction protection statistics
- Private mempool usage analytics
- Threat level monitoring
- Performance metrics

Usage:
    python mev_monitoring_dashboard.py --port 8080
    python mev_monitoring_dashboard.py --network mainnet --export-metrics
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import argparse

# Web dashboard dependencies
try:
    from flask import Flask, render_template_string, jsonify, request
    from flask_socketio import SocketIO, emit
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("⚠️ Flask not available. Install with: pip install flask flask-socketio")

# MEV protection imports
from mev_protection_critical_fixes import SecureMEVProtectionPatch
from web3 import Web3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MEV_MONITOR")

@dataclass
class MEVMetrics:
    """MEV protection metrics"""
    timestamp: str
    mev_attacks_detected: int
    mev_attacks_prevented: int
    private_mempool_usage: int
    public_mempool_usage: int
    average_threat_level: str
    total_transactions_protected: int
    failed_protections: int
    gas_savings_eth: float
    slippage_prevented_bps: float
    response_time_ms: float

@dataclass
class ThreatIntelligence:
    """Threat intelligence data"""
    known_mev_bots: int
    recent_sandwich_attacks: int
    current_threat_level: str
    high_risk_contracts: List[str]
    suspicious_addresses: List[str]
    network_congestion_level: str

class MEVProtectionMonitor:
    """Real-time MEV protection monitoring system"""
    
    def __init__(self, network: str = 'mainnet', web3_provider: Optional[Web3] = None):
        self.network = network
        self.web3 = web3_provider or self._setup_web3()
        self.secure_mev_patch = SecureMEVProtectionPatch(self.web3)
        
        # Metrics storage
        self.metrics_history: List[MEVMetrics] = []
        self.threat_intelligence = ThreatIntelligence(
            known_mev_bots=0,
            recent_sandwich_attacks=0,
            current_threat_level="UNKNOWN",
            high_risk_contracts=[],
            suspicious_addresses=[],
            network_congestion_level="NORMAL"
        )
        
        # Monitoring state
        self.monitoring_active = False
        self.last_scan_time = datetime.now()
        
        # Alerts
        self.alert_thresholds = {
            'high_threat_level': 'HIGH',
            'max_failed_protections': 5,
            'max_response_time_ms': 5000,
            'min_protection_rate': 0.95
        }
        
        self.active_alerts = []
    
    def _setup_web3(self) -> Web3:
        """Setup Web3 connection"""
        # This would normally use environment variables
        rpc_url = "https://mainnet.infura.io/v3/YOUR_INFURA_KEY"
        return Web3(Web3.HTTPProvider(rpc_url))
    
    async def start_monitoring(self):
        """Start real-time monitoring"""
        logger.info("🔍 Starting MEV protection monitoring...")
        self.monitoring_active = True
        
        while self.monitoring_active:
            try:
                await self._collect_metrics()
                await self._update_threat_intelligence()
                await self._check_alerts()
                
                # Wait before next scan
                await asyncio.sleep(30)  # Scan every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _collect_metrics(self):
        """Collect MEV protection metrics"""
        start_time = time.time()
        
        try:
            # Get mempool analysis
            mempool_analysis = await self.secure_mev_patch.secure_mempool_analysis()
            
            # Calculate metrics
            metrics = MEVMetrics(
                timestamp=datetime.now().isoformat(),
                mev_attacks_detected=mempool_analysis.get('mev_transactions_found', 0),
                mev_attacks_prevented=self._calculate_prevented_attacks(),
                private_mempool_usage=self._get_private_mempool_usage(),
                public_mempool_usage=self._get_public_mempool_usage(),
                average_threat_level=mempool_analysis.get('threat_level', 'UNKNOWN'),
                total_transactions_protected=self._get_protected_transactions(),
                failed_protections=self._get_failed_protections(),
                gas_savings_eth=self._calculate_gas_savings(),
                slippage_prevented_bps=self._calculate_slippage_prevented(),
                response_time_ms=(time.time() - start_time) * 1000
            )
            
            # Store metrics
            self.metrics_history.append(metrics)
            
            # Keep only last 24 hours of data
            cutoff_time = datetime.now() - timedelta(hours=24)
            self.metrics_history = [
                m for m in self.metrics_history 
                if datetime.fromisoformat(m.timestamp.replace('Z', '+00:00')) > cutoff_time
            ]
            
            logger.info(f"📊 Metrics collected - Threat level: {metrics.average_threat_level}")
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
    
    async def _update_threat_intelligence(self):
        """Update threat intelligence data"""
        try:
            # Get current threat data
            mempool_analysis = await self.secure_mev_patch.secure_mempool_analysis()
            
            self.threat_intelligence.known_mev_bots = len(self.secure_mev_patch.known_mev_bots)
            self.threat_intelligence.recent_sandwich_attacks = len([
                attack for attack in self.secure_mev_patch.recent_sandwich_attacks
                if datetime.now() - attack['timestamp'] < timedelta(hours=1)
            ])
            self.threat_intelligence.current_threat_level = mempool_analysis.get('threat_level', 'UNKNOWN')
            
            # Update network congestion
            latest_block = await self.web3.eth.get_block('latest')
            gas_used_ratio = latest_block.gasUsed / latest_block.gasLimit
            
            if gas_used_ratio > 0.9:
                self.threat_intelligence.network_congestion_level = "HIGH"
            elif gas_used_ratio > 0.7:
                self.threat_intelligence.network_congestion_level = "MEDIUM"
            else:
                self.threat_intelligence.network_congestion_level = "LOW"
            
        except Exception as e:
            logger.error(f"Error updating threat intelligence: {e}")
    
    async def _check_alerts(self):
        """Check for alert conditions"""
        current_metrics = self.metrics_history[-1] if self.metrics_history else None
        if not current_metrics:
            return
        
        new_alerts = []
        
        # Check threat level
        if current_metrics.average_threat_level in ['HIGH', 'CRITICAL']:
            new_alerts.append({
                'type': 'HIGH_THREAT',
                'message': f"High threat level detected: {current_metrics.average_threat_level}",
                'timestamp': datetime.now().isoformat(),
                'severity': 'HIGH'
            })
        
        # Check failed protections
        if current_metrics.failed_protections > self.alert_thresholds['max_failed_protections']:
            new_alerts.append({
                'type': 'PROTECTION_FAILURES',
                'message': f"High number of failed protections: {current_metrics.failed_protections}",
                'timestamp': datetime.now().isoformat(),
                'severity': 'MEDIUM'
            })
        
        # Check response time
        if current_metrics.response_time_ms > self.alert_thresholds['max_response_time_ms']:
            new_alerts.append({
                'type': 'SLOW_RESPONSE',
                'message': f"Slow response time: {current_metrics.response_time_ms:.1f}ms",
                'timestamp': datetime.now().isoformat(),
                'severity': 'LOW'
            })
        
        # Add new alerts
        self.active_alerts.extend(new_alerts)
        
        # Keep only recent alerts (last 4 hours)
        cutoff_time = datetime.now() - timedelta(hours=4)
        self.active_alerts = [
            alert for alert in self.active_alerts
            if datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00')) > cutoff_time
        ]
        
        # Log new alerts
        for alert in new_alerts:
            logger.warning(f"🚨 ALERT: {alert['message']}")
    
    def _calculate_prevented_attacks(self) -> int:
        """Calculate number of prevented MEV attacks"""
        # This would track actual prevented attacks
        # For now, return a simulation
        return max(0, len(self.secure_mev_patch.known_mev_bots) - 5)
    
    def _get_private_mempool_usage(self) -> int:
        """Get private mempool usage count"""
        # This would track actual private mempool usage
        return len([m for m in self.metrics_history[-10:] if m.average_threat_level in ['HIGH', 'CRITICAL']])
    
    def _get_public_mempool_usage(self) -> int:
        """Get public mempool usage count"""
        # This would track actual public mempool usage
        return len([m for m in self.metrics_history[-10:] if m.average_threat_level in ['LOW', 'MEDIUM']])
    
    def _get_protected_transactions(self) -> int:
        """Get total protected transactions count"""
        # This would track actual protected transactions
        return len(self.metrics_history) * 10  # Simulation
    
    def _get_failed_protections(self) -> int:
        """Get failed protections count"""
        # This would track actual failures
        return max(0, len(self.metrics_history) // 20)  # Simulation: 5% failure rate
    
    def _calculate_gas_savings(self) -> float:
        """Calculate gas savings in ETH"""
        # This would calculate actual gas savings from MEV protection
        return len(self.metrics_history) * 0.001  # Simulation: 0.001 ETH per scan
    
    def _calculate_slippage_prevented(self) -> float:
        """Calculate slippage prevented in basis points"""
        # This would calculate actual slippage prevention
        return len(self.metrics_history) * 2.5  # Simulation: 2.5 bps per scan
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for dashboard display"""
        latest_metrics = self.metrics_history[-1] if self.metrics_history else None
        
        return {
            'current_metrics': asdict(latest_metrics) if latest_metrics else None,
            'threat_intelligence': asdict(self.threat_intelligence),
            'active_alerts': self.active_alerts,
            'metrics_history': [asdict(m) for m in self.metrics_history[-100:]],  # Last 100 entries
            'protection_stats': {
                'total_protected': sum(m.total_transactions_protected for m in self.metrics_history),
                'total_prevented': sum(m.mev_attacks_prevented for m in self.metrics_history),
                'total_gas_saved': sum(m.gas_savings_eth for m in self.metrics_history),
                'average_response_time': sum(m.response_time_ms for m in self.metrics_history) / len(self.metrics_history) if self.metrics_history else 0
            },
            'monitoring_status': {
                'active': self.monitoring_active,
                'last_scan': self.last_scan_time.isoformat(),
                'network': self.network
            }
        }
    
    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics in specified format"""
        data = self.get_dashboard_data()
        
        if format.lower() == 'json':
            return json.dumps(data, indent=2)
        elif format.lower() == 'prometheus':
            return self._export_prometheus_metrics(data)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_prometheus_metrics(self, data: Dict[str, Any]) -> str:
        """Export metrics in Prometheus format"""
        prometheus_metrics = []
        
        if data['current_metrics']:
            metrics = data['current_metrics']
            prometheus_metrics.extend([
                f"mev_attacks_detected {metrics['mev_attacks_detected']}",
                f"mev_attacks_prevented {metrics['mev_attacks_prevented']}",
                f"private_mempool_usage {metrics['private_mempool_usage']}",
                f"public_mempool_usage {metrics['public_mempool_usage']}",
                f"total_transactions_protected {metrics['total_transactions_protected']}",
                f"failed_protections {metrics['failed_protections']}",
                f"gas_savings_eth {metrics['gas_savings_eth']}",
                f"slippage_prevented_bps {metrics['slippage_prevented_bps']}",
                f"response_time_ms {metrics['response_time_ms']}"
            ])
        
        prometheus_metrics.extend([
            f"known_mev_bots {data['threat_intelligence']['known_mev_bots']}",
            f"recent_sandwich_attacks {data['threat_intelligence']['recent_sandwich_attacks']}",
            f"active_alerts {len(data['active_alerts'])}"
        ])
        
        return '\n'.join(prometheus_metrics)

# Web Dashboard (if Flask is available)
if FLASK_AVAILABLE:
    app = Flask(__name__)
    socketio = SocketIO(app, cors_allowed_origins="*")
    monitor_instance = None
    
    DASHBOARD_HTML = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MEV Protection Dashboard</title>
        <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #ffffff; }
            .header { text-align: center; margin-bottom: 30px; }
            .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
            .metric-card { background: #2d2d2d; padding: 20px; border-radius: 8px; border-left: 4px solid #00ff88; }
            .metric-value { font-size: 2em; font-weight: bold; color: #00ff88; }
            .metric-label { color: #cccccc; }
            .threat-level { padding: 5px 15px; border-radius: 20px; font-weight: bold; }
            .threat-low { background: #28a745; }
            .threat-medium { background: #ffc107; color: #000; }
            .threat-high { background: #dc3545; }
            .threat-critical { background: #6f42c1; }
            .alerts { background: #2d2d2d; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .alert { padding: 10px; margin: 5px 0; border-radius: 4px; }
            .alert-high { background: #dc3545; }
            .alert-medium { background: #ffc107; color: #000; }
            .alert-low { background: #17a2b8; }
            .chart-container { background: #2d2d2d; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🛡️ MEV Protection Dashboard</h1>
            <div id="status">Connecting...</div>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">MEV Attacks Detected</div>
                <div class="metric-value" id="attacks-detected">-</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Attacks Prevented</div>
                <div class="metric-value" id="attacks-prevented">-</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Threat Level</div>
                <div class="metric-value" id="threat-level">-</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Response Time</div>
                <div class="metric-value" id="response-time">-</div>
            </div>
        </div>
        
        <div class="alerts">
            <h3>🚨 Active Alerts</h3>
            <div id="alerts-container">No active alerts</div>
        </div>
        
        <div class="chart-container">
            <h3>📊 MEV Protection Metrics</h3>
            <canvas id="metricsChart" width="400" height="200"></canvas>
        </div>
        
        <script>
            const socket = io();
            
            socket.on('connect', function() {
                document.getElementById('status').innerHTML = '🟢 Connected';
            });
            
            socket.on('dashboard_update', function(data) {
                updateDashboard(data);
            });
            
            function updateDashboard(data) {
                if (data.current_metrics) {
                    document.getElementById('attacks-detected').innerText = data.current_metrics.mev_attacks_detected;
                    document.getElementById('attacks-prevented').innerText = data.current_metrics.mev_attacks_prevented;
                    document.getElementById('response-time').innerText = data.current_metrics.response_time_ms.toFixed(1) + 'ms';
                    
                    const threatLevel = data.current_metrics.average_threat_level;
                    const threatElement = document.getElementById('threat-level');
                    threatElement.innerText = threatLevel;
                    threatElement.className = 'metric-value threat-level threat-' + threatLevel.toLowerCase();
                }
                
                // Update alerts
                const alertsContainer = document.getElementById('alerts-container');
                if (data.active_alerts.length > 0) {
                    alertsContainer.innerHTML = data.active_alerts.map(alert => 
                        `<div class="alert alert-${alert.severity.toLowerCase()}">${alert.message}</div>`
                    ).join('');
                } else {
                    alertsContainer.innerHTML = 'No active alerts';
                }
            }
            
            // Request initial data
            socket.emit('request_dashboard_data');
        </script>
    </body>
    </html>
    """
    
    @app.route('/')
    def dashboard():
        return DASHBOARD_HTML
    
    @app.route('/api/metrics')
    def api_metrics():
        if monitor_instance:
            return jsonify(monitor_instance.get_dashboard_data())
        return jsonify({'error': 'Monitor not initialized'})
    
    @app.route('/api/export/<format>')
    def api_export(format):
        if monitor_instance:
            try:
                return monitor_instance.export_metrics(format)
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
        return jsonify({'error': 'Monitor not initialized'}), 500
    
    @socketio.on('request_dashboard_data')
    def handle_dashboard_request():
        if monitor_instance:
            emit('dashboard_update', monitor_instance.get_dashboard_data())

async def run_monitoring_with_dashboard(monitor: MEVProtectionMonitor, port: int = 8080):
    """Run monitoring with web dashboard"""
    global monitor_instance
    monitor_instance = monitor
    
    # Start monitoring in background
    monitoring_task = asyncio.create_task(monitor.start_monitoring())
    
    # Start web dashboard
    logger.info(f"🌐 Starting web dashboard on http://localhost:{port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='MEV Protection Monitoring Dashboard')
    parser.add_argument('--network', choices=['mainnet', 'testnet'], default='mainnet',
                        help='Network to monitor')
    parser.add_argument('--port', type=int, default=8080,
                        help='Web dashboard port')
    parser.add_argument('--export-metrics', action='store_true',
                        help='Export metrics and exit')
    parser.add_argument('--export-format', choices=['json', 'prometheus'], default='json',
                        help='Export format')
    parser.add_argument('--no-dashboard', action='store_true',
                        help='Run monitoring without web dashboard')
    
    args = parser.parse_args()
    
    # Initialize monitor
    monitor = MEVProtectionMonitor(network=args.network)
    
    if args.export_metrics:
        # Collect metrics once and export
        await monitor._collect_metrics()
        await monitor._update_threat_intelligence()
        print(monitor.export_metrics(args.export_format))
        return
    
    if args.no_dashboard or not FLASK_AVAILABLE:
        # Run monitoring only
        logger.info("🔍 Starting MEV protection monitoring (no dashboard)")
        await monitor.start_monitoring()
    else:
        # Run with dashboard
        await run_monitoring_with_dashboard(monitor, args.port)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
