#!/usr/bin/env python3
"""
Enhanced Cross-Chain Security Dashboard
=====================================

Real-time security monitoring dashboard with advanced analytics,
threat visualization, and automated response management.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import hashlib

# For web interface (would use FastAPI/Flask in production)
try:
    from flask import Flask, render_template, jsonify, request
    from flask_socketio import SocketIO, emit
    WEB_INTERFACE_AVAILABLE = True
except ImportError:
    WEB_INTERFACE_AVAILABLE = False
    print("Web interface dependencies not available. Dashboard will run in terminal mode.")

@dataclass
class DashboardMetrics:
    """Real-time dashboard metrics"""
    timestamp: datetime
    global_security_level: str
    total_operations_24h: int
    blocked_operations_24h: int
    threat_detections_24h: int
    average_threat_score: float
    active_alerts: int
    chain_health_average: float
    response_time_avg_ms: float
    false_positive_rate: float

@dataclass
class ChainHealthMetrics:
    """Chain-specific health metrics"""
    chain_id: int
    chain_name: str
    trust_score: float
    security_level: str
    operations_24h: int
    threats_24h: int
    avg_confirmation_time: float
    is_operational: bool
    last_incident: Optional[datetime]

@dataclass
class ThreatVisualization:
    """Threat visualization data"""
    threat_type: str
    count: int
    severity_distribution: Dict[str, int]
    trend_24h: List[int]
    affected_chains: List[int]
    response_actions: List[str]

class SecurityDashboard:
    """
    Enhanced cross-chain security monitoring dashboard
    """
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.metrics_history = deque(maxlen=1440)  # 24 hours of minute-by-minute data
        self.threat_data = defaultdict(list)
        self.chain_metrics = {}
        self.active_alerts = []
        self.response_log = []
        
        # Real-time data
        self.current_metrics = None
        self.websocket_clients = set()
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Initialize web interface if available
        if WEB_INTERFACE_AVAILABLE:
            self.app = Flask(__name__)
            self.socketio = SocketIO(self.app, cors_allowed_origins="*")
            self._setup_web_routes()
        
        # Initialize chain metrics
        self._initialize_chain_metrics()
    
    def _initialize_chain_metrics(self):
        """Initialize chain health metrics"""
        for chain in self.config.get('supported_chains', []):
            self.chain_metrics[chain['id']] = ChainHealthMetrics(
                chain_id=chain['id'],
                chain_name=chain['name'],
                trust_score=chain.get('trust_score', 1.0),
                security_level=chain.get('security_level', 'medium'),
                operations_24h=0,
                threats_24h=0,
                avg_confirmation_time=0.0,
                is_operational=True,
                last_incident=None
            )
    
    def _setup_web_routes(self):
        """Setup web interface routes"""
        if not WEB_INTERFACE_AVAILABLE:
            return
        
        @self.app.route('/')
        def dashboard():
            return render_template('security_dashboard.html')
        
        @self.app.route('/api/metrics')
        def get_metrics():
            return jsonify(self._get_dashboard_data())
        
        @self.app.route('/api/threats')
        def get_threats():
            return jsonify(self._get_threat_analytics())
        
        @self.app.route('/api/chains')
        def get_chain_health():
            return jsonify(self._get_chain_health_data())
        
        @self.app.route('/api/alerts')
        def get_alerts():
            return jsonify(self._get_active_alerts())
        
        @self.socketio.on('connect')
        def handle_connect():
            self.websocket_clients.add(request.sid)
            emit('connected', {'data': 'Connected to security dashboard'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            self.websocket_clients.discard(request.sid)
    
    async def update_metrics(self, metrics_data: Dict[str, Any]):
        """Update dashboard metrics with new data"""
        # Create metrics object
        metrics = DashboardMetrics(
            timestamp=datetime.now(),
            global_security_level=metrics_data.get('global_security_level', 'normal'),
            total_operations_24h=metrics_data.get('total_operations_24h', 0),
            blocked_operations_24h=metrics_data.get('blocked_operations_24h', 0),
            threat_detections_24h=metrics_data.get('threat_detections_24h', 0),
            average_threat_score=metrics_data.get('average_threat_score', 0.0),
            active_alerts=metrics_data.get('active_alerts', 0),
            chain_health_average=metrics_data.get('chain_health_average', 1.0),
            response_time_avg_ms=metrics_data.get('response_time_avg_ms', 0.0),
            false_positive_rate=metrics_data.get('false_positive_rate', 0.0)
        )
        
        # Store metrics
        self.current_metrics = metrics
        self.metrics_history.append(metrics)
        
        # Update chain-specific metrics
        chain_data = metrics_data.get('chain_metrics', {})
        for chain_id, data in chain_data.items():
            if int(chain_id) in self.chain_metrics:
                chain_metrics = self.chain_metrics[int(chain_id)]
                chain_metrics.trust_score = data.get('trust_score', chain_metrics.trust_score)
                chain_metrics.security_level = data.get('security_level', chain_metrics.security_level)
                chain_metrics.operations_24h = data.get('operations_24h', 0)
                chain_metrics.threats_24h = data.get('threats_24h', 0)
                chain_metrics.is_operational = data.get('is_operational', True)
        
        # Broadcast updates to connected clients
        if WEB_INTERFACE_AVAILABLE and self.websocket_clients:
            self.socketio.emit('metrics_update', asdict(metrics))
    
    async def add_threat_detection(self, threat_data: Dict[str, Any]):
        """Add new threat detection to dashboard"""
        threat_type = threat_data.get('type', 'unknown')
        severity = threat_data.get('severity', 'low')
        affected_chains = threat_data.get('affected_chains', [])
        
        # Store threat data
        threat_entry = {
            'timestamp': datetime.now(),
            'type': threat_type,
            'severity': severity,
            'affected_chains': affected_chains,
            'confidence': threat_data.get('confidence', 0.0),
            'description': threat_data.get('description', ''),
            'response_actions': threat_data.get('response_actions', [])
        }
        
        self.threat_data[threat_type].append(threat_entry)
        
        # Create alert if severity is high enough
        if severity in ['high', 'critical']:
            alert = {
                'id': self._generate_alert_id(),
                'timestamp': datetime.now(),
                'type': threat_type,
                'severity': severity,
                'message': threat_data.get('description', f'High severity {threat_type} detected'),
                'affected_chains': affected_chains,
                'status': 'active'
            }
            self.active_alerts.append(alert)
            
            # Broadcast alert to connected clients
            if WEB_INTERFACE_AVAILABLE and self.websocket_clients:
                self.socketio.emit('new_alert', alert)
    
    async def add_response_action(self, action_data: Dict[str, Any]):
        """Log response action taken by the system"""
        response_entry = {
            'timestamp': datetime.now(),
            'action_type': action_data.get('action_type', 'unknown'),
            'target_operation': action_data.get('target_operation', ''),
            'target_chains': action_data.get('target_chains', []),
            'success': action_data.get('success', True),
            'details': action_data.get('details', ''),
            'automated': action_data.get('automated', True)
        }
        
        self.response_log.append(response_entry)
        
        # Broadcast to connected clients
        if WEB_INTERFACE_AVAILABLE and self.websocket_clients:
            self.socketio.emit('response_action', response_entry)
    
    def _get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        if not self.current_metrics:
            return {'error': 'No metrics available'}
        
        # Get trend data (last 24 hours)
        trends = self._calculate_trends()
        
        # Get summary statistics
        summary = self._calculate_summary_stats()
        
        return {
            'current_metrics': asdict(self.current_metrics),
            'trends': trends,
            'summary': summary,
            'last_updated': datetime.now().isoformat()
        }
    
    def _get_threat_analytics(self) -> Dict[str, Any]:
        """Get threat analytics data"""
        analytics = {}
        
        # Threat type distribution
        threat_distribution = defaultdict(int)
        severity_distribution = defaultdict(int)
        hourly_threats = defaultdict(int)
        
        for threat_type, threats in self.threat_data.items():
            for threat in threats:
                if threat['timestamp'] > datetime.now() - timedelta(hours=24):
                    threat_distribution[threat_type] += 1
                    severity_distribution[threat['severity']] += 1
                    hour = threat['timestamp'].hour
                    hourly_threats[hour] += 1
        
        # Top affected chains
        chain_threat_count = defaultdict(int)
        for threats in self.threat_data.values():
            for threat in threats:
                if threat['timestamp'] > datetime.now() - timedelta(hours=24):
                    for chain_id in threat['affected_chains']:
                        chain_threat_count[chain_id] += 1
        
        analytics = {
            'threat_distribution': dict(threat_distribution),
            'severity_distribution': dict(severity_distribution),
            'hourly_threats': dict(hourly_threats),
            'top_affected_chains': dict(sorted(chain_threat_count.items(), 
                                             key=lambda x: x[1], reverse=True)[:5]),
            'total_threats_24h': sum(threat_distribution.values()),
            'critical_threats_24h': severity_distribution.get('critical', 0)
        }
        
        return analytics
    
    def _get_chain_health_data(self) -> Dict[str, Any]:
        """Get chain health dashboard data"""
        chain_data = {}
        
        for chain_id, metrics in self.chain_metrics.items():
            chain_data[chain_id] = {
                'name': metrics.chain_name,
                'trust_score': metrics.trust_score,
                'security_level': metrics.security_level,
                'operations_24h': metrics.operations_24h,
                'threats_24h': metrics.threats_24h,
                'threat_ratio': metrics.threats_24h / max(metrics.operations_24h, 1),
                'is_operational': metrics.is_operational,
                'last_incident': metrics.last_incident.isoformat() if metrics.last_incident else None,
                'health_score': self._calculate_chain_health_score(metrics)
            }
        
        return {
            'chains': chain_data,
            'summary': {
                'total_chains': len(chain_data),
                'operational_chains': len([c for c in chain_data.values() if c['is_operational']]),
                'average_trust_score': sum([c['trust_score'] for c in chain_data.values()]) / len(chain_data),
                'total_operations_24h': sum([c['operations_24h'] for c in chain_data.values()]),
                'total_threats_24h': sum([c['threats_24h'] for c in chain_data.values()])
            }
        }
    
    def _get_active_alerts(self) -> Dict[str, Any]:
        """Get active security alerts"""
        # Filter out resolved/expired alerts
        active_alerts = [
            alert for alert in self.active_alerts
            if alert['status'] == 'active' and 
               alert['timestamp'] > datetime.now() - timedelta(hours=24)
        ]
        
        # Sort by severity and timestamp
        severity_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        active_alerts.sort(
            key=lambda x: (severity_order.get(x['severity'], 0), x['timestamp']),
            reverse=True
        )
        
        return {
            'alerts': active_alerts,
            'count': len(active_alerts),
            'critical_count': len([a for a in active_alerts if a['severity'] == 'critical']),
            'high_count': len([a for a in active_alerts if a['severity'] == 'high'])
        }
    
    def _calculate_trends(self) -> Dict[str, List[float]]:
        """Calculate trend data for visualizations"""
        if len(self.metrics_history) < 2:
            return {}
        
        # Get last 24 hours of data (up to 1440 data points)
        recent_metrics = list(self.metrics_history)[-1440:]
        
        trends = {
            'threat_scores': [m.average_threat_score for m in recent_metrics],
            'operation_counts': [m.total_operations_24h for m in recent_metrics],
            'blocked_operations': [m.blocked_operations_24h for m in recent_metrics],
            'response_times': [m.response_time_avg_ms for m in recent_metrics],
            'false_positive_rates': [m.false_positive_rate for m in recent_metrics]
        }
        
        return trends
    
    def _calculate_summary_stats(self) -> Dict[str, Any]:
        """Calculate summary statistics"""
        if not self.metrics_history:
            return {}
        
        recent_metrics = list(self.metrics_history)[-60:]  # Last hour
        
        summary = {
            'operations_per_minute_avg': sum([m.total_operations_24h for m in recent_metrics]) / len(recent_metrics),
            'threat_detection_rate': sum([m.threat_detections_24h for m in recent_metrics]) / len(recent_metrics),
            'system_uptime': self._calculate_uptime(),
            'performance_score': self._calculate_performance_score(),
            'security_effectiveness': self._calculate_security_effectiveness()
        }
        
        return summary
    
    def _calculate_chain_health_score(self, metrics: ChainHealthMetrics) -> float:
        """Calculate overall health score for a chain"""
        # Base score from trust score
        health_score = metrics.trust_score * 0.4
        
        # Operational status factor
        if metrics.is_operational:
            health_score += 0.3
        
        # Threat ratio factor (lower is better)
        threat_ratio = metrics.threats_24h / max(metrics.operations_24h, 1)
        health_score += max(0, (1 - threat_ratio * 10)) * 0.3
        
        return min(1.0, max(0.0, health_score))
    
    def _calculate_uptime(self) -> float:
        """Calculate system uptime percentage"""
        # This would be calculated from actual system monitoring data
        # For now, return a mock value
        return 99.95
    
    def _calculate_performance_score(self) -> float:
        """Calculate overall performance score"""
        if not self.current_metrics:
            return 0.0
        
        # Factors: response time, false positive rate, successful operations
        response_factor = max(0, 1 - (self.current_metrics.response_time_avg_ms / 1000))
        fp_factor = max(0, 1 - self.current_metrics.false_positive_rate)
        
        blocked_ratio = (self.current_metrics.blocked_operations_24h / 
                        max(self.current_metrics.total_operations_24h, 1))
        operation_factor = max(0, 1 - blocked_ratio)
        
        return (response_factor + fp_factor + operation_factor) / 3
    
    def _calculate_security_effectiveness(self) -> float:
        """Calculate security system effectiveness"""
        if not self.current_metrics:
            return 0.0
        
        # Factors: threat detection, response success, false positives
        detection_factor = min(1.0, self.current_metrics.threat_detections_24h / 10)
        fp_factor = max(0, 1 - self.current_metrics.false_positive_rate)
        
        return (detection_factor + fp_factor) / 2
    
    def _generate_alert_id(self) -> str:
        """Generate unique alert ID"""
        timestamp = str(datetime.now().timestamp())
        return f"alert_{hashlib.md5(timestamp.encode()).hexdigest()[:8]}"
    
    def print_dashboard(self):
        """Print dashboard to terminal"""
        if not self.current_metrics:
            print("No metrics available")
            return
        
        print("\n" + "="*80)
        print("🔒 ENHANCED CROSS-CHAIN SECURITY DASHBOARD")
        print("="*80)
        print(f"Last Updated: {self.current_metrics.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Global Security Level: {self.current_metrics.global_security_level.upper()}")
        
        print(f"\n📊 SYSTEM METRICS (24h)")
        print(f"  Total Operations: {self.current_metrics.total_operations_24h:,}")
        print(f"  Blocked Operations: {self.current_metrics.blocked_operations_24h:,}")
        print(f"  Threat Detections: {self.current_metrics.threat_detections_24h:,}")
        print(f"  Average Threat Score: {self.current_metrics.average_threat_score:.3f}")
        print(f"  Active Alerts: {self.current_metrics.active_alerts}")
        print(f"  Response Time: {self.current_metrics.response_time_avg_ms:.1f}ms")
        print(f"  False Positive Rate: {self.current_metrics.false_positive_rate:.3f}")
        
        print(f"\n🔗 CHAIN HEALTH")
        for chain_id, metrics in self.chain_metrics.items():
            status = "🟢" if metrics.is_operational else "🔴"
            trust_color = "🟢" if metrics.trust_score > 0.8 else "🟡" if metrics.trust_score > 0.5 else "🔴"
            print(f"  {status} {metrics.chain_name} (ID: {chain_id})")
            print(f"    Trust Score: {trust_color} {metrics.trust_score:.3f}")
            print(f"    Security Level: {metrics.security_level.upper()}")
            print(f"    Operations: {metrics.operations_24h:,} | Threats: {metrics.threats_24h}")
        
        print(f"\n🚨 ACTIVE ALERTS")
        active_alerts = self._get_active_alerts()['alerts']
        if active_alerts:
            for alert in active_alerts[:5]:  # Show top 5 alerts
                severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(alert['severity'], "⚪")
                print(f"  {severity_icon} {alert['type'].upper()} - {alert['message']}")
        else:
            print("  ✅ No active alerts")
        
        print("\n" + "="*80)
    
    async def start_web_interface(self, host: str = '0.0.0.0', port: int = 5000):
        """Start web interface"""
        if not WEB_INTERFACE_AVAILABLE:
            print("Web interface not available. Install Flask and Flask-SocketIO.")
            return
        
        print(f"Starting security dashboard web interface on {host}:{port}")
        self.socketio.run(self.app, host=host, port=port, debug=False)

# Example usage and testing
async def main():
    """Main function for testing dashboard"""
    dashboard = SecurityDashboard("enhanced_cross_chain_security_config.json")
    
    # Simulate some metrics updates
    for i in range(5):
        metrics_data = {
            'global_security_level': 'normal' if i < 3 else 'elevated',
            'total_operations_24h': 1000 + i * 100,
            'blocked_operations_24h': i * 2,
            'threat_detections_24h': i * 3,
            'average_threat_score': 0.3 + (i * 0.1),
            'active_alerts': i,
            'chain_health_average': 0.9 - (i * 0.05),
            'response_time_avg_ms': 100 + (i * 20),
            'false_positive_rate': 0.05 + (i * 0.01),
            'chain_metrics': {
                '1': {'trust_score': 0.95, 'security_level': 'high', 'operations_24h': 500, 'threats_24h': i},
                '137': {'trust_score': 0.85, 'security_level': 'medium', 'operations_24h': 300, 'threats_24h': i*2}
            }
        }
        
        await dashboard.update_metrics(metrics_data)
        
        # Simulate threat detection
        if i > 2:
            threat_data = {
                'type': 'anomaly',
                'severity': 'high' if i > 3 else 'medium',
                'affected_chains': [1, 137],
                'confidence': 0.8,
                'description': f'Suspicious pattern detected in operation sequence #{i}',
                'response_actions': ['delay', 'monitor']
            }
            await dashboard.add_threat_detection(threat_data)
        
        # Print dashboard
        dashboard.print_dashboard()
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
