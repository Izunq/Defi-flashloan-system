#!/usr/bin/env python3
"""
Emergency Monitoring Adapter
Adapts data from the emergency monitoring system for sentinel consumption
"""

import os
import sys
import yaml
import json
import time
import logging
import asyncio
import sqlite3
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("emergency_adapter.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("EmergencyMonitoringAdapter")

class EmergencyAdapter:
    """
    Adapter for the Emergency Monitoring System
    Converts emergency monitoring data for sentinel consumption
    """
    
    def __init__(self, system_name: str, config: Dict[str, Any]):
        """Initialize the Emergency Monitoring Adapter"""
        self.system_name = system_name
        self.config = config
        self.endpoints = config.get("endpoints", [])
        self.data_format = config.get("data_format", "json")
        
        # Import the emergency monitoring system
        try:
            from emergency_monitoring_system import EmergencyMonitoringSystem, AlertSeverity, SystemStatus, MonitoringComponent
            self.emergency_system = EmergencyMonitoringSystem()
            self.AlertSeverity = AlertSeverity
            self.SystemStatus = SystemStatus
            self.MonitoringComponent = MonitoringComponent
            logger.info("Successfully imported Emergency Monitoring System")
        except ImportError as e:
            logger.error(f"Failed to import Emergency Monitoring System: {e}")
            self.emergency_system = None
        
        # Severity mapping from emergency system to sentinel
        self.severity_mapping = {
            "CRITICAL": "CRITICAL",
            "HIGH": "HIGH",
            "MEDIUM": "MEDIUM",
            "LOW": "LOW",
            "INFO": "INFO"
        }
        
        logger.info(f"Emergency Monitoring Adapter initialized for {system_name}")
    
    async def get_data(self, endpoint: str) -> List[Dict[str, Any]]:
        """Get data from the emergency monitoring system"""
        if not self.emergency_system:
            logger.error("Emergency Monitoring System not available")
            return []
        
        try:
            if endpoint == "health":
                return await self._get_health_data()
            elif endpoint == "alerts":
                return await self._get_alerts_data()
            elif endpoint == "metrics":
                return await self._get_metrics_data()
            else:
                logger.warning(f"Unknown endpoint: {endpoint}")
                return []
        except Exception as e:
            logger.error(f"Error getting data from endpoint {endpoint}: {e}")
            return []
    
    async def _get_health_data(self) -> List[Dict[str, Any]]:
        """Get health data from the emergency monitoring system"""
        try:
            # Get dashboard data which includes health information
            dashboard_data = await self.emergency_system.get_dashboard_data()
            
            health_data = []
            
            # Extract system status
            system_status = dashboard_data.get("system_status", {})
            overall_status = system_status.get("overall", "UNKNOWN")
            
            # Add overall system health
            health_data.append({
                "id": f"emergency_overall_{int(time.time())}",
                "timestamp": int(time.time()),
                "component": "overall",
                "status": overall_status,
                "message": f"Emergency monitoring system overall status: {overall_status}",
                "details": {
                    "uptime": system_status.get("uptime", 0),
                    "last_check": system_status.get("last_check", 0)
                }
            })
            
            # Extract component statuses
            components = dashboard_data.get("components", {})
            for component_name, component_data in components.items():
                health_data.append({
                    "id": f"emergency_{component_name}_{int(time.time())}",
                    "timestamp": int(time.time()),
                    "component": component_name,
                    "status": component_data.get("status", "UNKNOWN"),
                    "message": component_data.get("message", ""),
                    "details": {
                        "last_check": component_data.get("last_check", 0),
                        "error_rate": component_data.get("error_rate", 0),
                        "response_time": component_data.get("response_time", 0)
                    }
                })
            
            return health_data
            
        except Exception as e:
            logger.error(f"Error getting health data: {e}")
            return []
    
    async def _get_alerts_data(self) -> List[Dict[str, Any]]:
        """Get alerts data from the emergency monitoring system"""
        try:
            # Get dashboard data which includes active alerts
            dashboard_data = await self.emergency_system.get_dashboard_data()
            
            alerts_data = []
            
            # Extract active alerts
            active_alerts = dashboard_data.get("active_alerts", [])
            
            for alert in active_alerts:
                # Map severity from emergency system to sentinel format
                severity = alert.get("severity", "UNKNOWN")
                mapped_severity = self.severity_mapping.get(severity, "MEDIUM")
                
                alerts_data.append({
                    "id": alert.get("id", f"emergency_alert_{int(time.time())}_{len(alerts_data)}"),
                    "timestamp": alert.get("timestamp", int(time.time())),
                    "level": mapped_severity,
                    "type": alert.get("component", "UNKNOWN"),
                    "message": alert.get("message", ""),
                    "details": {
                        "source_system": "emergency_monitoring",
                        "original_severity": severity,
                        "component": alert.get("component", ""),
                        "additional_info": alert.get("details", {})
                    },
                    "acknowledged": 1 if alert.get("acknowledged", False) else 0,
                    "resolved": 1 if alert.get("resolved", False) else 0
                })
            
            return alerts_data
            
        except Exception as e:
            logger.error(f"Error getting alerts data: {e}")
            return []
    
    async def _get_metrics_data(self) -> List[Dict[str, Any]]:
        """Get metrics data from the emergency monitoring system"""
        try:
            # Get dashboard data which includes metrics
            dashboard_data = await self.emergency_system.get_dashboard_data()
            
            metrics_data = []
            
            # Extract system metrics
            system_metrics = dashboard_data.get("metrics", {})
            
            # Process network metrics
            network_metrics = system_metrics.get("network", {})
            for metric_name, metric_value in network_metrics.items():
                metrics_data.append({
                    "id": f"emergency_network_{metric_name}_{int(time.time())}",
                    "timestamp": int(time.time()),
                    "category": "network",
                    "name": metric_name,
                    "value": metric_value,
                    "unit": self._get_metric_unit(metric_name),
                    "metadata": {
                        "source_system": "emergency_monitoring"
                    }
                })
            
            # Process security metrics
            security_metrics = system_metrics.get("security", {})
            for metric_name, metric_value in security_metrics.items():
                metrics_data.append({
                    "id": f"emergency_security_{metric_name}_{int(time.time())}",
                    "timestamp": int(time.time()),
                    "category": "security",
                    "name": metric_name,
                    "value": metric_value,
                    "unit": self._get_metric_unit(metric_name),
                    "metadata": {
                        "source_system": "emergency_monitoring"
                    }
                })
            
            # Process performance metrics
            performance_metrics = system_metrics.get("performance", {})
            for metric_name, metric_value in performance_metrics.items():
                metrics_data.append({
                    "id": f"emergency_performance_{metric_name}_{int(time.time())}",
                    "timestamp": int(time.time()),
                    "category": "performance",
                    "name": metric_name,
                    "value": metric_value,
                    "unit": self._get_metric_unit(metric_name),
                    "metadata": {
                        "source_system": "emergency_monitoring"
                    }
                })
            
            return metrics_data
            
        except Exception as e:
            logger.error(f"Error getting metrics data: {e}")
            return []
    
    def _get_metric_unit(self, metric_name: str) -> str:
        """Get the appropriate unit for a metric based on its name"""
        if "latency" in metric_name or "time" in metric_name:
            return "ms"
        elif "rate" in metric_name:
            return "per_second"
        elif "percentage" in metric_name or metric_name.endswith("_pct"):
            return "percent"
        elif "count" in metric_name:
            return "count"
        elif "size" in metric_name or "memory" in metric_name:
            return "bytes"
        else:
            return ""

# For testing the adapter directly
async def test_adapter():
    """Test the Emergency Monitoring Adapter"""
    # Create a test configuration
    test_config = {
        "enabled": True,
        "adapter": "emergency_monitoring_adapter",
        "endpoints": ["health", "alerts", "metrics"],
        "data_format": "json"
    }
    
    # Initialize the adapter
    adapter = EmergencyAdapter("emergency_monitoring", test_config)
    
    # Test each endpoint
    for endpoint in ["health", "alerts", "metrics"]:
        print(f"\nTesting endpoint: {endpoint}")
        data = await adapter.get_data(endpoint)
        print(f"Retrieved {len(data)} records")
        if data:
            print(f"Sample data: {json.dumps(data[0], indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_adapter())