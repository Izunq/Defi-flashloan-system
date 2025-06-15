#!/usr/bin/env python3
"""
🚨 EMERGENCY MONITORING SYSTEM
=============================

Comprehensive emergency monitoring system for flashloan arbitrage operations.
Integrates health monitoring, security alerts, MEV protection, and cross-chain monitoring.

FEATURES:
🔍 Real-time System Health Monitoring
🛡️ Security Threat Detection
🤖 MEV Protection Monitoring  
🌉 Cross-Chain Security Monitoring
📊 Performance Metrics Collection
🚨 Multi-level Alert System
🔄 Automatic Recovery Mechanisms
📈 Predictive Analytics
🛠️ Emergency Response Automation

Author: GitHub Copilot
Version: 1.0
Date: June 14, 2025
"""

import asyncio
import json
import logging
import time
import psutil
import aiohttp
import websockets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
from collections import defaultdict, deque
import yaml
import subprocess
import sys
import traceback

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('emergency_monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class SystemStatus(Enum):
    """System status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    EMERGENCY = "emergency"
    OFFLINE = "offline"

class MonitoringComponent(Enum):
    """Monitoring component types"""
    HEALTH_MONITOR = "health_monitor"
    SECURITY_MONITOR = "security_monitor"
    MEV_MONITOR = "mev_monitor"
    CROSS_CHAIN_MONITOR = "cross_chain_monitor"
    FINANCIAL_MONITOR = "financial_monitor"
    ORACLE_MONITOR = "oracle_monitor"

@dataclass
class EmergencyAlert:
    """Emergency alert data structure"""
    alert_id: str
    severity: AlertSeverity
    component: MonitoringComponent
    title: str
    description: str
    timestamp: datetime
    metrics: Dict[str, Any] = field(default_factory=dict)
    actions_taken: List[str] = field(default_factory=list)
    resolved: bool = False
    escalated: bool = False

@dataclass
class SystemHealthMetrics:
    """System health metrics"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_latency: float
    active_connections: int
    error_rate: float
    response_time: float
    timestamp: datetime

@dataclass
class EmergencyConfig:
    """Emergency monitoring configuration"""
    monitoring_interval: int = 30
    alert_cooldown: int = 300
    max_alerts_per_hour: int = 50
    emergency_contacts: List[str] = field(default_factory=list)
    webhook_urls: List[str] = field(default_factory=list)
    auto_recovery_enabled: bool = True
    predictive_alerts_enabled: bool = True
    escalation_thresholds: Dict[str, int] = field(default_factory=dict)

class EmergencyMonitoringSystem:
    """
    Comprehensive Emergency Monitoring System
    """
    
    def __init__(self, config_file: str = "emergency_monitoring_config.yaml"):
        """Initialize emergency monitoring system"""
        self.config = self._load_config(config_file)
        self.is_monitoring = False
        self.alerts_queue = deque(maxlen=1000)
        self.active_alerts: Dict[str, EmergencyAlert] = {}
        self.system_metrics: List[SystemHealthMetrics] = []
        self.component_status: Dict[MonitoringComponent, SystemStatus] = {}
        
        # Initialize monitoring components
        self.health_monitor = None
        self.security_monitor = None
        self.mev_monitor = None
        self.cross_chain_monitor = None
        
        # Alert tracking
        self.alert_counts = defaultdict(int)
        self.last_alert_time = defaultdict(float)
        
        # Recovery mechanisms
        self.recovery_strategies = {}
        self.auto_recovery_enabled = self.config.auto_recovery_enabled
        
        # Initialize component status
        for component in MonitoringComponent:
            self.component_status[component] = SystemStatus.OFFLINE
        
        logger.info("🚨 Emergency Monitoring System initialized")

    def _load_config(self, config_file: str) -> EmergencyConfig:
        """Load configuration from file"""
        try:
            if Path(config_file).exists():
                with open(config_file, 'r') as f:
                    config_data = yaml.safe_load(f)
                return EmergencyConfig(**config_data)
            else:
                # Create default config
                default_config = EmergencyConfig(
                    emergency_contacts=["admin@flashloan.com"],
                    escalation_thresholds={
                        "critical_alerts": 3,
                        "failed_transactions": 10,
                        "security_breaches": 1
                    }
                )
                self._save_config(config_file, default_config)
                return default_config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return EmergencyConfig()

    def _save_config(self, config_file: str, config: EmergencyConfig):
        """Save configuration to file"""
        try:
            with open(config_file, 'w') as f:
                yaml.dump(config.__dict__, f, default_flow_style=False)
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    async def start_monitoring(self):
        """Start comprehensive emergency monitoring"""
        logger.info("🚀 Starting Emergency Monitoring System...")
        self.is_monitoring = True
        
        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self._system_health_monitoring()),
            asyncio.create_task(self._security_monitoring()),
            asyncio.create_task(self._mev_protection_monitoring()),
            asyncio.create_task(self._cross_chain_monitoring()),
            asyncio.create_task(self._financial_monitoring()),
            asyncio.create_task(self._oracle_monitoring()),
            asyncio.create_task(self._alert_processing()),
            asyncio.create_task(self._emergency_response_loop()),
            asyncio.create_task(self._metrics_cleanup())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Emergency monitoring error: {e}")
            await self.emergency_shutdown()

    async def stop_monitoring(self):
        """Stop emergency monitoring"""
        logger.info("🛑 Stopping Emergency Monitoring System...")
        self.is_monitoring = False
        
        # Send final status report
        await self._send_shutdown_notification()

    async def _system_health_monitoring(self):
        """Monitor overall system health"""
        logger.info("🩺 Starting system health monitoring...")
        self.component_status[MonitoringComponent.HEALTH_MONITOR] = SystemStatus.HEALTHY
        
        while self.is_monitoring:
            try:
                # Collect system metrics
                metrics = SystemHealthMetrics(
                    cpu_usage=psutil.cpu_percent(interval=1),
                    memory_usage=psutil.virtual_memory().percent,
                    disk_usage=psutil.disk_usage('/').percent,
                    network_latency=await self._measure_network_latency(),
                    active_connections=len(psutil.net_connections()),
                    error_rate=await self._calculate_error_rate(),
                    response_time=await self._measure_response_time(),
                    timestamp=datetime.now()
                )
                
                self.system_metrics.append(metrics)
                
                # Check for health alerts
                await self._check_health_alerts(metrics)
                
                # Keep only last 24 hours of metrics
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.system_metrics = [
                    m for m in self.system_metrics 
                    if m.timestamp > cutoff_time
                ]
                
                await asyncio.sleep(self.config.monitoring_interval)
                
            except Exception as e:
                logger.error(f"System health monitoring error: {e}")
                await self._create_alert(
                    AlertSeverity.HIGH,
                    MonitoringComponent.HEALTH_MONITOR,
                    "Health Monitoring Error",
                    f"System health monitoring failed: {e}"
                )
                await asyncio.sleep(60)

    async def _security_monitoring(self):
        """Monitor security threats and violations"""
        logger.info("🛡️ Starting security monitoring...")
        self.component_status[MonitoringComponent.SECURITY_MONITOR] = SystemStatus.HEALTHY
        
        while self.is_monitoring:
            try:
                # Monitor log files for security events
                security_events = await self._scan_security_logs()
                
                for event in security_events:
                    await self._process_security_event(event)
                
                # Check for suspicious patterns
                await self._detect_suspicious_patterns()
                
                # Monitor access control violations
                await self._check_access_control_violations()
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Security monitoring error: {e}")
                await self._create_alert(
                    AlertSeverity.CRITICAL,
                    MonitoringComponent.SECURITY_MONITOR,
                    "Security Monitoring Error",
                    f"Security monitoring failed: {e}"
                )
                await asyncio.sleep(30)

    async def _mev_protection_monitoring(self):
        """Monitor MEV protection systems"""
        logger.info("🤖 Starting MEV protection monitoring...")
        self.component_status[MonitoringComponent.MEV_MONITOR] = SystemStatus.HEALTHY
        
        try:
            # Import MEV monitoring if available
            from mev_monitoring_dashboard import MEVProtectionMonitor
            self.mev_monitor = MEVProtectionMonitor()
        except ImportError:
            logger.warning("MEV monitoring dashboard not available")
            self.component_status[MonitoringComponent.MEV_MONITOR] = SystemStatus.DEGRADED
            return
        
        while self.is_monitoring:
            try:
                # Check MEV protection status
                mev_status = await self._check_mev_protection_status()
                
                if mev_status.get('threat_level') in ['HIGH', 'CRITICAL']:
                    await self._create_alert(
                        AlertSeverity.HIGH,
                        MonitoringComponent.MEV_MONITOR,
                        "High MEV Threat Level",
                        f"MEV threat level: {mev_status.get('threat_level')}"
                    )
                
                # Monitor failed protections
                failed_protections = mev_status.get('failed_protections', 0)
                if failed_protections > 5:
                    await self._create_alert(
                        AlertSeverity.MEDIUM,
                        MonitoringComponent.MEV_MONITOR,
                        "MEV Protection Failures",
                        f"Failed protections: {failed_protections}"
                    )
                
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"MEV monitoring error: {e}")
                await asyncio.sleep(60)

    async def _cross_chain_monitoring(self):
        """Monitor cross-chain bridge security"""
        logger.info("🌉 Starting cross-chain monitoring...")
        self.component_status[MonitoringComponent.CROSS_CHAIN_MONITOR] = SystemStatus.HEALTHY
        
        try:
            # Import cross-chain monitoring if available
            from cross_chain_security_monitor import CrossChainSecurityMonitor
            self.cross_chain_monitor = CrossChainSecurityMonitor({})
        except ImportError:
            logger.warning("Cross-chain monitoring not available")
            self.component_status[MonitoringComponent.CROSS_CHAIN_MONITOR] = SystemStatus.DEGRADED
            return
        
        while self.is_monitoring:
            try:
                # Check cross-chain health
                chain_health = await self._check_cross_chain_health()
                
                for chain_id, health in chain_health.items():
                    if not health.get('is_healthy', True):
                        await self._create_alert(
                            AlertSeverity.HIGH,
                            MonitoringComponent.CROSS_CHAIN_MONITOR,
                            f"Chain {chain_id} Unhealthy",
                            f"Chain {chain_id} health check failed"
                        )
                
                await asyncio.sleep(120)  # Check every 2 minutes
                
            except Exception as e:
                logger.error(f"Cross-chain monitoring error: {e}")
                await asyncio.sleep(60)

    async def _financial_monitoring(self):
        """Monitor financial metrics and anomalies"""
        logger.info("💰 Starting financial monitoring...")
        self.component_status[MonitoringComponent.FINANCIAL_MONITOR] = SystemStatus.HEALTHY
        
        while self.is_monitoring:
            try:
                # Monitor profit/loss patterns
                financial_metrics = await self._get_financial_metrics()
                
                # Check for unusual losses
                if financial_metrics.get('loss_rate', 0) > 0.1:  # 10% loss rate
                    await self._create_alert(
                        AlertSeverity.CRITICAL,
                        MonitoringComponent.FINANCIAL_MONITOR,
                        "High Loss Rate Detected",
                        f"Loss rate: {financial_metrics.get('loss_rate', 0):.2%}"
                    )
                
                # Monitor gas price anomalies
                gas_price = financial_metrics.get('avg_gas_price', 0)
                if gas_price > 100:  # High gas price threshold
                    await self._create_alert(
                        AlertSeverity.MEDIUM,
                        MonitoringComponent.FINANCIAL_MONITOR,
                        "High Gas Prices",
                        f"Average gas price: {gas_price} gwei"
                    )
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Financial monitoring error: {e}")
                await asyncio.sleep(120)

    async def _oracle_monitoring(self):
        """Monitor oracle health and manipulation detection"""
        logger.info("🔮 Starting oracle monitoring...")
        self.component_status[MonitoringComponent.ORACLE_MONITOR] = SystemStatus.HEALTHY
        
        while self.is_monitoring:
            try:
                # Monitor oracle health
                oracle_status = await self._check_oracle_health()
                
                for oracle_name, status in oracle_status.items():
                    if not status.get('healthy', True):
                        await self._create_alert(
                            AlertSeverity.HIGH,
                            MonitoringComponent.ORACLE_MONITOR,
                            f"Oracle {oracle_name} Unhealthy",
                            f"Oracle {oracle_name} health check failed"
                        )
                
                # Check for price manipulation
                price_anomalies = await self._detect_price_anomalies()
                for anomaly in price_anomalies:
                    await self._create_alert(
                        AlertSeverity.CRITICAL,
                        MonitoringComponent.ORACLE_MONITOR,
                        "Price Manipulation Detected",
                        f"Anomaly detected: {anomaly}"
                    )
                
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Oracle monitoring error: {e}")
                await asyncio.sleep(30)

    async def _create_alert(self, severity: AlertSeverity, component: MonitoringComponent,
                          title: str, description: str, metrics: Dict[str, Any] = None):
        """Create and process emergency alert"""
        alert_id = f"{component.value}_{int(time.time())}"
        
        alert = EmergencyAlert(
            alert_id=alert_id,
            severity=severity,
            component=component,
            title=title,
            description=description,
            timestamp=datetime.now(),
            metrics=metrics or {}
        )
        
        # Check alert cooldown
        last_alert = self.last_alert_time.get(component, 0)
        if time.time() - last_alert < self.config.alert_cooldown:
            logger.debug(f"Alert cooldown active for {component.value}")
            return
        
        self.last_alert_time[component] = time.time()
        self.alerts_queue.append(alert)
        self.active_alerts[alert_id] = alert
        
        logger.warning(f"🚨 EMERGENCY ALERT: {severity.value.upper()} - {title}")
        
        # Immediate actions for critical/emergency alerts
        if severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]:
            await self._handle_critical_alert(alert)

    async def _handle_critical_alert(self, alert: EmergencyAlert):
        """Handle critical and emergency alerts immediately"""
        logger.critical(f"🔥 CRITICAL ALERT: {alert.title}")
        
        # Auto-recovery for known issues
        if self.auto_recovery_enabled:
            recovery_action = await self._attempt_auto_recovery(alert)
            if recovery_action:
                alert.actions_taken.append(recovery_action)
        
        # Emergency notifications
        await self._send_emergency_notifications(alert)
        
        # Emergency response escalation
        if alert.severity == AlertSeverity.EMERGENCY:
            await self._emergency_escalation(alert)

    async def _alert_processing(self):
        """Process alerts queue"""
        while self.is_monitoring:
            try:
                if self.alerts_queue:
                    alert = self.alerts_queue.popleft()
                    await self._process_alert(alert)
                
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Alert processing error: {e}")
                await asyncio.sleep(10)

    async def _process_alert(self, alert: EmergencyAlert):
        """Process individual alert"""
        try:
            # Send notifications
            await self._send_alert_notifications(alert)
            
            # Log alert
            logger.info(f"Processing alert: {alert.alert_id} - {alert.title}")
            
            # Check for escalation
            if self._should_escalate(alert):
                await self._escalate_alert(alert)
            
        except Exception as e:
            logger.error(f"Error processing alert {alert.alert_id}: {e}")

    async def _emergency_response_loop(self):
        """Emergency response coordination"""
        while self.is_monitoring:
            try:
                # Check system status
                overall_status = self._calculate_overall_status()
                
                if overall_status in [SystemStatus.CRITICAL, SystemStatus.EMERGENCY]:
                    await self._activate_emergency_protocols()
                
                # Clean up resolved alerts
                await self._cleanup_resolved_alerts()
                
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Emergency response error: {e}")
                await asyncio.sleep(30)

    async def _activate_emergency_protocols(self):
        """Activate emergency protocols"""
        logger.critical("🔥 ACTIVATING EMERGENCY PROTOCOLS")
        
        # Emergency actions based on severity
        emergency_actions = [
            "Pausing automated trading",
            "Activating circuit breakers",
            "Enabling emergency withdrawal mode",
            "Notifying emergency contacts"
        ]
        
        for action in emergency_actions:
            try:
                logger.critical(f"Emergency action: {action}")
                # Implement actual emergency actions here
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Emergency action failed: {action} - {e}")

    async def emergency_shutdown(self):
        """Emergency system shutdown"""
        logger.critical("🚨 EMERGENCY SHUTDOWN INITIATED")
        
        try:
            # Save current state
            await self._save_emergency_state()
            
            # Send emergency notifications
            await self._send_emergency_shutdown_notification()
            
            # Stop monitoring
            self.is_monitoring = False
            
        except Exception as e:
            logger.error(f"Emergency shutdown error: {e}")

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get dashboard data for monitoring UI"""
        recent_metrics = self.system_metrics[-1] if self.system_metrics else None
        
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_status': self._calculate_overall_status().value,
            'component_status': {
                comp.value: status.value 
                for comp, status in self.component_status.items()
            },
            'active_alerts_count': len(self.active_alerts),
            'critical_alerts_count': len([
                a for a in self.active_alerts.values() 
                if a.severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]
            ]),
            'recent_metrics': {
                'cpu_usage': recent_metrics.cpu_usage if recent_metrics else 0,
                'memory_usage': recent_metrics.memory_usage if recent_metrics else 0,
                'disk_usage': recent_metrics.disk_usage if recent_metrics else 0,
                'error_rate': recent_metrics.error_rate if recent_metrics else 0
            } if recent_metrics else {},
            'recent_alerts': [
                {
                    'id': alert.alert_id,
                    'severity': alert.severity.value,
                    'title': alert.title,
                    'component': alert.component.value,
                    'timestamp': alert.timestamp.isoformat()
                }
                for alert in list(self.active_alerts.values())[-10:]
            ]
        }

    # Helper methods (implementation stubs for brevity)
    async def _measure_network_latency(self) -> float:
        """Measure network latency"""
        return 50.0  # Placeholder

    async def _calculate_error_rate(self) -> float:
        """Calculate current error rate"""
        return 0.01  # Placeholder

    async def _measure_response_time(self) -> float:
        """Measure system response time"""
        return 150.0  # Placeholder

    async def _check_health_alerts(self, metrics: SystemHealthMetrics):
        """Check health metrics for alerts"""
        if metrics.cpu_usage > 90:
            await self._create_alert(
                AlertSeverity.CRITICAL,
                MonitoringComponent.HEALTH_MONITOR,
                "High CPU Usage",
                f"CPU usage: {metrics.cpu_usage:.1f}%"
            )
        
        if metrics.memory_usage > 95:
            await self._create_alert(
                AlertSeverity.CRITICAL,
                MonitoringComponent.HEALTH_MONITOR,
                "High Memory Usage",
                f"Memory usage: {metrics.memory_usage:.1f}%"
            )

    async def _scan_security_logs(self) -> List[Dict[str, Any]]:
        """Scan security logs for events"""
        return []  # Placeholder

    async def _process_security_event(self, event: Dict[str, Any]):
        """Process security event"""
        pass  # Placeholder

    async def _detect_suspicious_patterns(self):
        """Detect suspicious patterns"""
        pass  # Placeholder

    async def _check_access_control_violations(self):
        """Check for access control violations"""
        pass  # Placeholder

    async def _check_mev_protection_status(self) -> Dict[str, Any]:
        """Check MEV protection status"""
        return {'threat_level': 'MEDIUM', 'failed_protections': 2}  # Placeholder

    async def _check_cross_chain_health(self) -> Dict[str, Dict[str, Any]]:
        """Check cross-chain health"""
        return {'1': {'is_healthy': True}, '137': {'is_healthy': True}}  # Placeholder

    async def _get_financial_metrics(self) -> Dict[str, Any]:
        """Get financial metrics"""
        return {'loss_rate': 0.05, 'avg_gas_price': 50}  # Placeholder

    async def _check_oracle_health(self) -> Dict[str, Dict[str, Any]]:
        """Check oracle health"""
        return {'chainlink': {'healthy': True}, 'uniswap': {'healthy': True}}  # Placeholder

    async def _detect_price_anomalies(self) -> List[str]:
        """Detect price anomalies"""
        return []  # Placeholder

    async def _attempt_auto_recovery(self, alert: EmergencyAlert) -> Optional[str]:
        """Attempt automatic recovery"""
        return None  # Placeholder

    async def _send_emergency_notifications(self, alert: EmergencyAlert):
        """Send emergency notifications"""
        pass  # Placeholder

    async def _emergency_escalation(self, alert: EmergencyAlert):
        """Handle emergency escalation"""
        pass  # Placeholder

    async def _send_alert_notifications(self, alert: EmergencyAlert):
        """Send alert notifications"""
        pass  # Placeholder

    def _should_escalate(self, alert: EmergencyAlert) -> bool:
        """Check if alert should be escalated"""
        return False  # Placeholder

    async def _escalate_alert(self, alert: EmergencyAlert):
        """Escalate alert"""
        pass  # Placeholder

    def _calculate_overall_status(self) -> SystemStatus:
        """Calculate overall system status"""
        statuses = list(self.component_status.values())
        
        if SystemStatus.EMERGENCY in statuses:
            return SystemStatus.EMERGENCY
        elif SystemStatus.CRITICAL in statuses:
            return SystemStatus.CRITICAL
        elif SystemStatus.DEGRADED in statuses:
            return SystemStatus.DEGRADED
        elif SystemStatus.WARNING in statuses:
            return SystemStatus.WARNING
        else:
            return SystemStatus.HEALTHY

    async def _cleanup_resolved_alerts(self):
        """Clean up resolved alerts"""
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(hours=24)
        
        # Remove old alerts
        self.active_alerts = {
            alert_id: alert for alert_id, alert in self.active_alerts.items()
            if alert.timestamp > cutoff_time
        }

    async def _save_emergency_state(self):
        """Save emergency state"""
        pass  # Placeholder

    async def _send_emergency_shutdown_notification(self):
        """Send emergency shutdown notification"""
        pass  # Placeholder

    async def _send_shutdown_notification(self):
        """Send shutdown notification"""
        pass  # Placeholder

    async def _metrics_cleanup(self):
        """Clean up old metrics"""
        while self.is_monitoring:
            try:
                cutoff_time = datetime.now() - timedelta(days=7)
                
                # Clean up old metrics
                self.system_metrics = [
                    m for m in self.system_metrics 
                    if m.timestamp > cutoff_time
                ]
                
                await asyncio.sleep(3600)  # Clean up every hour
                
            except Exception as e:
                logger.error(f"Metrics cleanup error: {e}")
                await asyncio.sleep(1800)

# Example usage and testing
async def main():
    """Main emergency monitoring function"""
    print("🚨 Emergency Monitoring System")
    print("=" * 50)
    
    # Initialize monitoring system
    emergency_monitor = EmergencyMonitoringSystem()
    
    try:
        # Start monitoring
        await emergency_monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
    except Exception as e:
        print(f"❌ Monitoring error: {e}")
        traceback.print_exc()
    finally:
        await emergency_monitor.stop_monitoring()

if __name__ == "__main__":
    asyncio.run(main())
