#!/usr/bin/env python3
"""
Oracle Monitoring Adapter
Adapts data from the oracle monitoring system for sentinel consumption
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
        logging.FileHandler("oracle_adapter.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("OracleMonitoringAdapter")

class OracleAdapter:
    """
    Adapter for the Oracle Monitoring System
    Converts oracle monitoring data for sentinel consumption
    """
    
    def __init__(self, system_name: str, config: Dict[str, Any]):
        """Initialize the Oracle Monitoring Adapter"""
        self.system_name = system_name
        self.config = config
        self.endpoints = config.get("endpoints", [])
        self.data_format = config.get("data_format", "json")
        
        # Import the oracle monitoring system
        try:
            from advanced_oracle_security_monitor import AdvancedOracleSecurityMonitor, ThreatLevel, AttackType
            self.oracle_system = AdvancedOracleSecurityMonitor()
            self.ThreatLevel = ThreatLevel
            self.AttackType = AttackType
            logger.info("Successfully imported Advanced Oracle Security Monitor")
        except ImportError as e:
            logger.error(f"Failed to import Advanced Oracle Security Monitor: {e}")
            self.oracle_system = None
        
        # Threat level mapping from oracle system to sentinel
        self.threat_level_mapping = {
            "CRITICAL": "CRITICAL",
            "HIGH": "HIGH",
            "MEDIUM": "MEDIUM",
            "LOW": "LOW",
            "INFO": "INFO"
        }
        
        logger.info(f"Oracle Monitoring Adapter initialized for {system_name}")
    
    async def get_data(self, endpoint: str) -> List[Dict[str, Any]]:
        """Get data from the oracle monitoring system"""
        if not self.oracle_system:
            logger.error("Oracle Monitoring System not available")
            return []
        
        try:
            if endpoint == "price_feeds":
                return await self._get_price_feeds_data()
            elif endpoint == "oracle_health":
                return await self._get_oracle_health_data()
            elif endpoint == "manipulation_alerts":
                return await self._get_manipulation_alerts_data()
            else:
                logger.warning(f"Unknown endpoint: {endpoint}")
                return []
        except Exception as e:
            logger.error(f"Error getting data from endpoint {endpoint}: {e}")
            return []
    
    async def _get_price_feeds_data(self) -> List[Dict[str, Any]]:
        """Get price feeds data from the oracle monitoring system"""
        try:
            # Get security dashboard data which includes price feeds
            dashboard_data = await self.oracle_system.get_security_dashboard()
            
            price_feeds_data = []
            
            # Extract price feeds
            price_data = dashboard_data.get("price_data", {})
            
            for asset, asset_data in price_data.items():
                price_feeds_data.append({
                    "id": f"oracle_price_{asset}_{int(time.time())}",
                    "timestamp": int(time.time()),
                    "category": "price_feed",
                    "name": f"{asset}_price",
                    "value": asset_data.get("current_price", 0),
                    "unit": "USD",
                    "metadata": {
                        "source_system": "oracle_monitoring",
                        "asset": asset,
                        "change_24h": asset_data.get("change_24h", 0),
                        "volatility": asset_data.get("volatility", 0),
                        "last_update": asset_data.get("last_update", 0)
                    }
                })
                
                # Add deviation metrics if available
                if "deviation" in asset_data:
                    price_feeds_data.append({
                        "id": f"oracle_deviation_{asset}_{int(time.time())}",
                        "timestamp": int(time.time()),
                        "category": "price_feed",
                        "name": f"{asset}_deviation",
                        "value": asset_data.get("deviation", 0),
                        "unit": "percent",
                        "metadata": {
                            "source_system": "oracle_monitoring",
                            "asset": asset
                        }
                    })
            
            return price_feeds_data
            
        except Exception as e:
            logger.error(f"Error getting price feeds data: {e}")
            return []
    
    async def _get_oracle_health_data(self) -> List[Dict[str, Any]]:
        """Get oracle health data from the oracle monitoring system"""
        try:
            # Get system health data
            system_health = self.oracle_system.get_system_health()
            
            health_data = []
            
            # Add overall system health
            health_data.append({
                "id": f"oracle_overall_{int(time.time())}",
                "timestamp": int(time.time()),
                "component": "overall",
                "status": system_health.get("status", "UNKNOWN"),
                "message": "Oracle monitoring system overall status",
                "details": {
                    "uptime": system_health.get("uptime", 0),
                    "last_check": int(time.time())
                }
            })
            
            # Add memory usage health
            memory_usage = system_health.get("memory_usage", {})
            health_data.append({
                "id": f"oracle_memory_{int(time.time())}",
                "timestamp": int(time.time()),
                "component": "memory",
                "status": "NORMAL" if memory_usage.get("percent", 0) < 80 else "WARNING",
                "message": f"Memory usage: {memory_usage.get('percent', 0)}%",
                "details": memory_usage
            })
            
            # Add performance metrics health
            performance = system_health.get("performance", {})
            health_data.append({
                "id": f"oracle_performance_{int(time.time())}",
                "timestamp": int(time.time()),
                "component": "performance",
                "status": "NORMAL" if performance.get("response_time", 0) < 500 else "WARNING",
                "message": f"Response time: {performance.get('response_time', 0)}ms",
                "details": performance
            })
            
            # Get security dashboard for oracle sources health
            dashboard_data = await self.oracle_system.get_security_dashboard()
            oracle_sources = dashboard_data.get("oracle_sources", {})
            
            for source, source_data in oracle_sources.items():
                health_data.append({
                    "id": f"oracle_source_{source}_{int(time.time())}",
                    "timestamp": int(time.time()),
                    "component": f"source_{source}",
                    "status": source_data.get("status", "UNKNOWN"),
                    "message": f"Oracle source {source} status: {source_data.get('status', 'UNKNOWN')}",
                    "details": {
                        "latency": source_data.get("latency", 0),
                        "reliability": source_data.get("reliability", 0),
                        "last_update": source_data.get("last_update", 0)
                    }
                })
            
            return health_data
            
        except Exception as e:
            logger.error(f"Error getting oracle health data: {e}")
            return []
    
    async def _get_manipulation_alerts_data(self) -> List[Dict[str, Any]]:
        """Get manipulation alerts data from the oracle monitoring system"""
        try:
            # Get security dashboard data which includes alerts
            dashboard_data = await self.oracle_system.get_security_dashboard()
            
            alerts_data = []
            
            # Extract recent alerts
            recent_alerts = dashboard_data.get("recent_alerts", [])
            
            for alert in recent_alerts:
                # Map threat level from oracle system to sentinel format
                threat_level = alert.get("threat_level", "MEDIUM")
                mapped_level = self.threat_level_mapping.get(threat_level, "MEDIUM")
                
                alerts_data.append({
                    "id": alert.get("id", f"oracle_alert_{int(time.time())}_{len(alerts_data)}"),
                    "timestamp": alert.get("timestamp", int(time.time())),
                    "level": mapped_level,
                    "type": alert.get("attack_type", "UNKNOWN"),
                    "message": alert.get("message", ""),
                    "details": {
                        "source_system": "oracle_monitoring",
                        "asset": alert.get("asset", ""),
                        "confidence": alert.get("confidence", 0),
                        "impact": alert.get("impact", 0),
                        "additional_info": alert.get("details", {})
                    },
                    "acknowledged": 1 if alert.get("acknowledged", False) else 0,
                    "resolved": 1 if alert.get("resolved", False) else 0
                })
            
            # Extract anomaly detection results
            anomalies = dashboard_data.get("anomalies", [])
            
            for anomaly in anomalies:
                # Only include significant anomalies
                if anomaly.get("score", 0) > 0.7:
                    alerts_data.append({
                        "id": f"oracle_anomaly_{int(time.time())}_{len(alerts_data)}",
                        "timestamp": int(time.time()),
                        "level": "MEDIUM",
                        "type": "ANOMALY",
                        "message": f"Price anomaly detected for {anomaly.get('asset', 'unknown asset')}",
                        "details": {
                            "source_system": "oracle_monitoring",
                            "asset": anomaly.get("asset", ""),
                            "anomaly_score": anomaly.get("score", 0),
                            "expected_price": anomaly.get("expected", 0),
                            "actual_price": anomaly.get("actual", 0),
                            "deviation_percent": anomaly.get("deviation", 0)
                        },
                        "acknowledged": 0,
                        "resolved": 0
                    })
            
            return alerts_data
            
        except Exception as e:
            logger.error(f"Error getting manipulation alerts data: {e}")
            return []

# For testing the adapter directly
async def test_adapter():
    """Test the Oracle Monitoring Adapter"""
    # Create a test configuration
    test_config = {
        "enabled": True,
        "adapter": "oracle_monitoring_adapter",
        "endpoints": ["price_feeds", "oracle_health", "manipulation_alerts"],
        "data_format": "json"
    }
    
    # Initialize the adapter
    adapter = OracleAdapter("oracle_monitoring", test_config)
    
    # Test each endpoint
    for endpoint in ["price_feeds", "oracle_health", "manipulation_alerts"]:
        print(f"\nTesting endpoint: {endpoint}")
        data = await adapter.get_data(endpoint)
        print(f"Retrieved {len(data)} records")
        if data:
            print(f"Sample data: {json.dumps(data[0], indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_adapter())