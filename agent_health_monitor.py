#!/usr/bin/env python3
"""
🔍 AGENT HEALTH MONITOR & RECOVERY SYSTEM
=========================================

This module provides comprehensive health monitoring and automatic recovery
for the distributed AI agent architecture.

FEATURES:
🩺 Real-time Health Monitoring
🔄 Automatic Recovery Mechanisms
📊 Performance Metrics Collection
🚨 Proactive Alerting System
🔧 Self-Healing Capabilities
📈 Predictive Failure Detection
🛠️ Automated Remediation
📋 Comprehensive Reporting

Author: GitHub Copilot
Version: 1.0
Date: June 14, 2025
"""

import asyncio
import json
import logging
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import psutil
import aiohttp
import asyncio
import threading
from collections import deque, defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Health status levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"
    FAILED = "failed"

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class HealthMetric:
    """Individual health metric"""
    name: str
    value: float
    threshold_warning: float
    threshold_critical: float
    unit: str = ""
    timestamp: float = field(default_factory=time.time)
    
    @property
    def status(self) -> HealthStatus:
        if self.value >= self.threshold_critical:
            return HealthStatus.CRITICAL
        elif self.value >= self.threshold_warning:
            return HealthStatus.WARNING
        else:
            return HealthStatus.GOOD

@dataclass
class AgentHealthProfile:
    """Comprehensive health profile for an agent"""
    agent_id: str
    last_updated: float = field(default_factory=time.time)
    metrics: Dict[str, HealthMetric] = field(default_factory=dict)
    status_history: List[HealthStatus] = field(default_factory=list)
    performance_trends: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    recovery_attempts: int = 0
    last_recovery_time: float = 0
    
    @property
    def overall_status(self) -> HealthStatus:
        if not self.metrics:
            return HealthStatus.FAILED
            
        critical_count = sum(1 for m in self.metrics.values() if m.status == HealthStatus.CRITICAL)
        warning_count = sum(1 for m in self.metrics.values() if m.status == HealthStatus.WARNING)
        
        if critical_count > 0:
            return HealthStatus.CRITICAL
        elif warning_count > len(self.metrics) * 0.5:
            return HealthStatus.WARNING
        elif warning_count > 0:
            return HealthStatus.GOOD
        else:
            return HealthStatus.EXCELLENT

class HealthMonitor:
    """Health monitoring system for distributed agents"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.agent_profiles: Dict[str, AgentHealthProfile] = {}
        self.alert_handlers: List[Callable] = []
        self.recovery_strategies: Dict[str, Callable] = {}
        
        # Monitoring configuration
        self.monitoring_interval = config.get('monitoring_interval', 5)
        self.trend_window_size = config.get('trend_window_size', 50)
        self.alert_cooldown = config.get('alert_cooldown', 300)  # 5 minutes
        
        # Alert thresholds
        self.thresholds = config.get('alert_thresholds', {
            'cpu_usage': {'warning': 70, 'critical': 90},
            'memory_usage': {'warning': 80, 'critical': 95},
            'response_time': {'warning': 2000, 'critical': 5000},
            'error_rate': {'warning': 5, 'critical': 15},
            'heartbeat_delay': {'warning': 30, 'critical': 60}
        })
        
        # Predictive monitoring
        self.prediction_window = config.get('prediction_window', 10)
        self.enable_predictive_alerts = config.get('enable_predictive_alerts', True)
        
        self.running = False
        self.monitor_task = None
        
        logger.info("Health Monitor initialized")
    
    def register_agent(self, agent_id: str, initial_metrics: Optional[Dict[str, float]] = None):
        """Register a new agent for monitoring"""
        profile = AgentHealthProfile(agent_id=agent_id)
        
        # Initialize with default metrics if provided
        if initial_metrics:
            for name, value in initial_metrics.items():
                if name in self.thresholds:
                    threshold_config = self.thresholds[name]
                    metric = HealthMetric(
                        name=name,
                        value=value,
                        threshold_warning=threshold_config['warning'],
                        threshold_critical=threshold_config['critical'],
                        unit=self._get_metric_unit(name)
                    )
                    profile.metrics[name] = metric
        
        self.agent_profiles[agent_id] = profile
        logger.info(f"Registered agent {agent_id} for health monitoring")
    
    def unregister_agent(self, agent_id: str):
        """Unregister an agent from monitoring"""
        if agent_id in self.agent_profiles:
            del self.agent_profiles[agent_id]
            logger.info(f"Unregistered agent {agent_id} from health monitoring")
    
    async def update_agent_metrics(self, agent_id: str, metrics: Dict[str, float]):
        """Update health metrics for an agent"""
        if agent_id not in self.agent_profiles:
            logger.warning(f"Agent {agent_id} not registered for monitoring")
            return
            
        profile = self.agent_profiles[agent_id]
        profile.last_updated = time.time()
        
        # Update metrics
        for name, value in metrics.items():
            if name in self.thresholds:
                threshold_config = self.thresholds[name]
                metric = HealthMetric(
                    name=name,
                    value=value,
                    threshold_warning=threshold_config['warning'],
                    threshold_critical=threshold_config['critical'],
                    unit=self._get_metric_unit(name)
                )
                profile.metrics[name] = metric
                
                # Store for trend analysis
                profile.performance_trends[name].append(value)
                if len(profile.performance_trends[name]) > self.trend_window_size:
                    profile.performance_trends[name].pop(0)
        
        # Update status history
        current_status = profile.overall_status
        if not profile.status_history or profile.status_history[-1] != current_status:
            profile.status_history.append(current_status)
            if len(profile.status_history) > 100:  # Keep last 100 status changes
                profile.status_history.pop(0)
        
        # Check for alerts
        await self._check_alerts(agent_id, profile)
        
        # Predictive analysis
        if self.enable_predictive_alerts:
            await self._predictive_analysis(agent_id, profile)
    
    async def _check_alerts(self, agent_id: str, profile: AgentHealthProfile):
        """Check if any metrics trigger alerts"""
        current_time = time.time()
        
        for metric_name, metric in profile.metrics.items():
            if metric.status in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
                # Check alert cooldown
                recent_alerts = [
                    a for a in profile.alerts
                    if a['metric'] == metric_name and 
                       current_time - a['timestamp'] < self.alert_cooldown
                ]
                
                if not recent_alerts:
                    severity = AlertSeverity.WARNING if metric.status == HealthStatus.WARNING else AlertSeverity.CRITICAL
                    
                    alert = {
                        'agent_id': agent_id,
                        'metric': metric_name,
                        'value': metric.value,
                        'threshold': metric.threshold_critical if metric.status == HealthStatus.CRITICAL else metric.threshold_warning,
                        'severity': severity.value,
                        'timestamp': current_time,
                        'message': f"Agent {agent_id} {metric_name} is {metric.status.value}: {metric.value}{metric.unit}"
                    }
                    
                    profile.alerts.append(alert)
                    
                    # Trigger alert handlers
                    await self._trigger_alert(alert)
                    
                    # Trigger recovery if critical
                    if metric.status == HealthStatus.CRITICAL:
                        await self._trigger_recovery(agent_id, metric_name, metric)
    
    async def _predictive_analysis(self, agent_id: str, profile: AgentHealthProfile):
        """Perform predictive analysis on metrics trends"""
        for metric_name, values in profile.performance_trends.items():
            if len(values) >= self.prediction_window:
                # Simple linear regression for trend prediction
                predicted_value = self._predict_next_value(values)
                
                if metric_name in self.thresholds:
                    threshold_config = self.thresholds[metric_name]
                    
                    # Check if predicted value will exceed thresholds
                    if predicted_value >= threshold_config['critical']:
                        await self._trigger_predictive_alert(
                            agent_id, metric_name, predicted_value, 
                            threshold_config['critical'], AlertSeverity.CRITICAL
                        )
                    elif predicted_value >= threshold_config['warning']:
                        await self._trigger_predictive_alert(
                            agent_id, metric_name, predicted_value,
                            threshold_config['warning'], AlertSeverity.WARNING
                        )
    
    def _predict_next_value(self, values: List[float]) -> float:
        """Simple linear regression to predict next value"""
        if len(values) < 2:
            return values[-1] if values else 0
            
        # Calculate linear trend
        x = list(range(len(values)))
        y = values
        
        n = len(values)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(xi * xi for xi in x)
        
        # Calculate slope and intercept
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        intercept = (sum_y - slope * sum_x) / n
        
        # Predict next value
        next_x = n
        predicted_value = slope * next_x + intercept
        
        return max(0, predicted_value)  # Ensure non-negative
    
    async def _trigger_alert(self, alert: Dict[str, Any]):
        """Trigger alert handlers"""
        logger.warning(f"ALERT: {alert['message']}")
        
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")
    
    async def _trigger_predictive_alert(self, agent_id: str, metric_name: str, 
                                      predicted_value: float, threshold: float,
                                      severity: AlertSeverity):
        """Trigger predictive alert"""
        alert = {
            'agent_id': agent_id,
            'metric': metric_name,
            'predicted_value': predicted_value,
            'threshold': threshold,
            'severity': severity.value,
            'timestamp': time.time(),
            'type': 'predictive',
            'message': f"PREDICTIVE: Agent {agent_id} {metric_name} predicted to reach {predicted_value:.2f} (threshold: {threshold})"
        }
        
        await self._trigger_alert(alert)
    
    async def _trigger_recovery(self, agent_id: str, metric_name: str, metric: HealthMetric):
        """Trigger recovery procedure for critical metrics"""
        profile = self.agent_profiles[agent_id]
        current_time = time.time()
        
        # Check recovery cooldown
        if current_time - profile.last_recovery_time < 300:  # 5 minutes
            logger.info(f"Recovery cooldown active for agent {agent_id}")
            return
        
        profile.recovery_attempts += 1
        profile.last_recovery_time = current_time
        
        # Select recovery strategy
        recovery_strategy = self._select_recovery_strategy(metric_name, metric.value)
        
        if recovery_strategy and recovery_strategy in self.recovery_strategies:
            logger.info(f"Triggering recovery strategy '{recovery_strategy}' for agent {agent_id}")
            
            try:
                await self.recovery_strategies[recovery_strategy](agent_id, metric_name, metric)
                logger.info(f"Recovery strategy '{recovery_strategy}' completed for agent {agent_id}")
            except Exception as e:
                logger.error(f"Recovery strategy '{recovery_strategy}' failed for agent {agent_id}: {e}")
        else:
            logger.warning(f"No recovery strategy available for {metric_name} on agent {agent_id}")
    
    def _select_recovery_strategy(self, metric_name: str, value: float) -> str:
        """Select appropriate recovery strategy based on metric"""
        strategy_map = {
            'cpu_usage': 'reduce_load',
            'memory_usage': 'garbage_collection',
            'response_time': 'restart_service',
            'error_rate': 'circuit_breaker',
            'heartbeat_delay': 'restart_agent'
        }
        
        return strategy_map.get(metric_name, 'restart_agent')
    
    def add_alert_handler(self, handler: Callable):
        """Add an alert handler function"""
        self.alert_handlers.append(handler)
        logger.info("Added alert handler")
    
    def add_recovery_strategy(self, name: str, strategy: Callable):
        """Add a recovery strategy"""
        self.recovery_strategies[name] = strategy
        logger.info(f"Added recovery strategy: {name}")
    
    def _get_metric_unit(self, metric_name: str) -> str:
        """Get unit for a metric"""
        units = {
            'cpu_usage': '%',
            'memory_usage': '%',
            'response_time': 'ms',
            'error_rate': '%',
            'heartbeat_delay': 's'
        }
        return units.get(metric_name, '')
    
    async def get_agent_health_report(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive health report for an agent"""
        if agent_id not in self.agent_profiles:
            return None
            
        profile = self.agent_profiles[agent_id]
        
        # Calculate performance statistics
        performance_stats = {}
        for metric_name, values in profile.performance_trends.items():
            if values:
                performance_stats[metric_name] = {
                    'current': values[-1],
                    'average': statistics.mean(values),
                    'min': min(values),
                    'max': max(values),
                    'trend': 'increasing' if len(values) > 1 and values[-1] > values[0] else 'decreasing'
                }
        
        # Recent alerts
        recent_alerts = [
            a for a in profile.alerts
            if time.time() - a['timestamp'] < 3600  # Last hour
        ]
        
        return {
            'agent_id': agent_id,
            'overall_status': profile.overall_status.value,
            'last_updated': profile.last_updated,
            'metrics': {
                name: {
                    'value': metric.value,
                    'status': metric.status.value,
                    'unit': metric.unit,
                    'threshold_warning': metric.threshold_warning,
                    'threshold_critical': metric.threshold_critical
                }
                for name, metric in profile.metrics.items()
            },
            'performance_stats': performance_stats,
            'recent_alerts': recent_alerts,
            'recovery_attempts': profile.recovery_attempts,
            'status_history': [s.value for s in profile.status_history[-10:]]  # Last 10 status changes
        }
    
    async def get_cluster_health_summary(self) -> Dict[str, Any]:
        """Get summary of cluster health"""
        if not self.agent_profiles:
            return {'status': 'no_agents', 'agents': []}
        
        status_counts = defaultdict(int)
        total_agents = len(self.agent_profiles)
        unhealthy_agents = []
        
        for agent_id, profile in self.agent_profiles.items():
            status = profile.overall_status
            status_counts[status.value] += 1
            
            if status in [HealthStatus.WARNING, HealthStatus.CRITICAL, HealthStatus.FAILED]:
                unhealthy_agents.append({
                    'agent_id': agent_id,
                    'status': status.value,
                    'last_updated': profile.last_updated
                })
        
        # Determine overall cluster health
        if status_counts[HealthStatus.FAILED.value] > 0:
            cluster_status = 'critical'
        elif status_counts[HealthStatus.CRITICAL.value] > total_agents * 0.3:
            cluster_status = 'degraded'
        elif status_counts[HealthStatus.WARNING.value] > total_agents * 0.5:
            cluster_status = 'warning'
        else:
            cluster_status = 'healthy'
        
        return {
            'cluster_status': cluster_status,
            'total_agents': total_agents,
            'status_distribution': dict(status_counts),
            'unhealthy_agents': unhealthy_agents,
            'health_percentage': (status_counts[HealthStatus.EXCELLENT.value] + 
                                status_counts[HealthStatus.GOOD.value]) / total_agents * 100,
            'timestamp': time.time()
        }
    
    async def start_monitoring(self):
        """Start the health monitoring loop"""
        self.running = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Health monitoring started")
    
    async def stop_monitoring(self):
        """Stop the health monitoring loop"""
        self.running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Health monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Check for stale agents (no recent updates)
                current_time = time.time()
                stale_threshold = 60  # 1 minute
                
                for agent_id, profile in self.agent_profiles.items():
                    if current_time - profile.last_updated > stale_threshold:
                        # Simulate heartbeat failure
                        await self.update_agent_metrics(agent_id, {'heartbeat_delay': current_time - profile.last_updated})
                
                # Generate periodic health summary
                summary = await self.get_cluster_health_summary()
                if summary['cluster_status'] != 'healthy':
                    logger.warning(f"Cluster health: {summary['cluster_status']} "
                                 f"({summary['health_percentage']:.1f}% healthy)")
                
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)

# Recovery Strategies
class RecoveryStrategies:
    """Collection of recovery strategies for common issues"""
    
    @staticmethod
    async def reduce_load(agent_id: str, metric_name: str, metric: HealthMetric):
        """Reduce load on an agent experiencing high CPU usage"""
        logger.info(f"Reducing load on agent {agent_id}")
        # Implementation would involve:
        # - Redistributing tasks to other agents
        # - Temporarily reducing processing rate
        # - Pausing non-critical operations
        
    @staticmethod
    async def garbage_collection(agent_id: str, metric_name: str, metric: HealthMetric):
        """Trigger garbage collection for high memory usage"""
        logger.info(f"Triggering garbage collection for agent {agent_id}")
        # Implementation would involve:
        # - Forcing garbage collection
        # - Clearing caches
        # - Releasing unused resources
        
    @staticmethod
    async def restart_service(agent_id: str, metric_name: str, metric: HealthMetric):
        """Restart specific service components"""
        logger.info(f"Restarting service components for agent {agent_id}")
        # Implementation would involve:
        # - Gracefully stopping affected services
        # - Restarting services
        # - Verifying service health
        
    @staticmethod
    async def circuit_breaker(agent_id: str, metric_name: str, metric: HealthMetric):
        """Activate circuit breaker for high error rates"""
        logger.info(f"Activating circuit breaker for agent {agent_id}")
        # Implementation would involve:
        # - Temporarily stopping request processing
        # - Switching to fallback mechanisms
        # - Gradual re-enablement
        
    @staticmethod
    async def restart_agent(agent_id: str, metric_name: str, metric: HealthMetric):
        """Restart the entire agent"""
        logger.info(f"Restarting agent {agent_id}")
        # Implementation would involve:
        # - Graceful shutdown of agent
        # - State preservation
        # - Agent restart
        # - State restoration

# Alert Handlers
class AlertHandlers:
    """Collection of alert handlers"""
    
    @staticmethod
    async def log_alert(alert: Dict[str, Any]):
        """Log alert to file"""
        logger.warning(f"ALERT: {alert['message']}")
    
    @staticmethod
    async def webhook_alert(alert: Dict[str, Any]):
        """Send alert via webhook"""
        # Implementation would send HTTP POST to alerting system
        logger.info(f"Sending webhook alert for {alert['agent_id']}")
    
    @staticmethod
    async def email_alert(alert: Dict[str, Any]):
        """Send alert via email"""
        # Implementation would send email notification
        logger.info(f"Sending email alert for {alert['agent_id']}")

# Example usage
async def setup_health_monitoring():
    """Setup health monitoring with recovery strategies"""
    config = {
        'monitoring_interval': 5,
        'trend_window_size': 50,
        'alert_cooldown': 300,
        'prediction_window': 10,
        'enable_predictive_alerts': True,
        'alert_thresholds': {
            'cpu_usage': {'warning': 70, 'critical': 90},
            'memory_usage': {'warning': 80, 'critical': 95},
            'response_time': {'warning': 2000, 'critical': 5000},
            'error_rate': {'warning': 5, 'critical': 15},
            'heartbeat_delay': {'warning': 30, 'critical': 60}
        }
    }
    
    monitor = HealthMonitor(config)
    
    # Add recovery strategies
    monitor.add_recovery_strategy('reduce_load', RecoveryStrategies.reduce_load)
    monitor.add_recovery_strategy('garbage_collection', RecoveryStrategies.garbage_collection)
    monitor.add_recovery_strategy('restart_service', RecoveryStrategies.restart_service)
    monitor.add_recovery_strategy('circuit_breaker', RecoveryStrategies.circuit_breaker)
    monitor.add_recovery_strategy('restart_agent', RecoveryStrategies.restart_agent)
    
    # Add alert handlers
    monitor.add_alert_handler(AlertHandlers.log_alert)
    monitor.add_alert_handler(AlertHandlers.webhook_alert)
    
    return monitor

if __name__ == "__main__":
    async def main():
        monitor = await setup_health_monitoring()
        
        # Register some test agents
        monitor.register_agent('agent-1', {'cpu_usage': 45, 'memory_usage': 60})
        monitor.register_agent('agent-2', {'cpu_usage': 85, 'memory_usage': 30})
        
        # Start monitoring
        await monitor.start_monitoring()
        
        # Simulate some metrics updates
        for i in range(10):
            await monitor.update_agent_metrics('agent-1', {
                'cpu_usage': 50 + i * 5,
                'memory_usage': 60 + i * 2,
                'response_time': 1000 + i * 100,
                'error_rate': i
            })
            
            await asyncio.sleep(2)
        
        # Get health reports
        report = await monitor.get_agent_health_report('agent-1')
        print(f"Agent 1 Health Report: {json.dumps(report, indent=2)}")
        
        summary = await monitor.get_cluster_health_summary()
        print(f"Cluster Health Summary: {json.dumps(summary, indent=2)}")
        
        # Stop monitoring
        await monitor.stop_monitoring()
    
    asyncio.run(main())
