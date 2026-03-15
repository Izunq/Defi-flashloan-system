#!/usr/bin/env python3
"""
MEV Monitoring Adapter
Adapts data from the MEV monitoring system for sentinel consumption
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
        logging.FileHandler("mev_adapter.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MEVMonitoringAdapter")

class MEVAdapter:
    """
    Adapter for the MEV Monitoring System
    Converts MEV monitoring data for sentinel consumption
    """
    
    def __init__(self, system_name: str, config: Dict[str, Any]):
        """Initialize the MEV Monitoring Adapter"""
        self.system_name = system_name
        self.config = config
        self.endpoints = config.get("endpoints", [])
        self.data_format = config.get("data_format", "json")
        
        # Import the MEV monitoring system
        try:
            from mev_monitoring_dashboard import MEVProtectionMonitor
            self.mev_system = MEVProtectionMonitor()
            logger.info("Successfully imported MEV Protection Monitor")
        except ImportError as e:
            logger.error(f"Failed to import MEV Protection Monitor: {e}")
            self.mev_system = None
        
        # Severity mapping for MEV alerts
        self.severity_mapping = {
            "critical": "CRITICAL",
            "high": "HIGH",
            "medium": "MEDIUM",
            "low": "LOW",
            "info": "INFO"
        }
        
        logger.info(f"MEV Monitoring Adapter initialized for {system_name}")
    
    async def get_data(self, endpoint: str) -> List[Dict[str, Any]]:
        """Get data from the MEV monitoring system"""
        if not self.mev_system:
            logger.error("MEV Monitoring System not available")
            return []
        
        try:
            if endpoint == "mev_alerts":
                return await self._get_mev_alerts_data()
            elif endpoint == "protection_status":
                return await self._get_protection_status_data()
            elif endpoint == "transaction_analysis":
                return await self._get_transaction_analysis_data()
            else:
                logger.warning(f"Unknown endpoint: {endpoint}")
                return []
        except Exception as e:
            logger.error(f"Error getting data from endpoint {endpoint}: {e}")
            return []
    
    async def _get_mev_alerts_data(self) -> List[Dict[str, Any]]:
        """Get MEV alerts data from the MEV monitoring system"""
        try:
            # Get dashboard data which includes alerts
            dashboard_data = self.mev_system.get_dashboard_data()
            
            alerts_data = []
            
            # Extract recent alerts
            recent_alerts = dashboard_data.get("recent_alerts", [])
            
            for alert in recent_alerts:
                # Map severity from MEV system to sentinel format
                severity = alert.get("severity", "medium").lower()
                mapped_severity = self.severity_mapping.get(severity, "MEDIUM")
                
                alerts_data.append({
                    "id": alert.get("id", f"mev_alert_{int(time.time())}_{len(alerts_data)}"),
                    "timestamp": alert.get("timestamp", int(time.time())),
                    "level": mapped_severity,
                    "type": alert.get("type", "UNKNOWN"),
                    "message": alert.get("message", ""),
                    "details": {
                        "source_system": "mev_monitoring",
                        "attack_vector": alert.get("attack_vector", ""),
                        "tx_hash": alert.get("tx_hash", ""),
                        "block_number": alert.get("block_number", 0),
                        "gas_price": alert.get("gas_price", 0),
                        "profit_estimate": alert.get("profit_estimate", 0),
                        "additional_info": alert.get("details", {})
                    },
                    "acknowledged": 1 if alert.get("acknowledged", False) else 0,
                    "resolved": 1 if alert.get("resolved", False) else 0
                })
            
            # Extract threat intelligence
            threat_intel = dashboard_data.get("threat_intelligence", {})
            
            # Add high-risk addresses as alerts
            high_risk_addresses = threat_intel.get("high_risk_addresses", [])
            for address_data in high_risk_addresses:
                alerts_data.append({
                    "id": f"mev_threat_address_{int(time.time())}_{len(alerts_data)}",
                    "timestamp": int(time.time()),
                    "level": "HIGH",
                    "type": "THREAT_INTELLIGENCE",
                    "message": f"High-risk MEV address detected: {address_data.get('address', 'unknown')}",
                    "details": {
                        "source_system": "mev_monitoring",
                        "address": address_data.get("address", ""),
                        "risk_score": address_data.get("risk_score", 0),
                        "attack_history": address_data.get("attack_history", []),
                        "last_seen": address_data.get("last_seen", 0)
                    },
                    "acknowledged": 0,
                    "resolved": 0
                })
            
            return alerts_data
            
        except Exception as e:
            logger.error(f"Error getting MEV alerts data: {e}")
            return []
    
    async def _get_protection_status_data(self) -> List[Dict[str, Any]]:
        """Get protection status data from the MEV monitoring system"""
        try:
            # Get dashboard data which includes protection status
            dashboard_data = self.mev_system.get_dashboard_data()
            
            protection_data = []
            
            # Extract protection metrics
            protection_metrics = dashboard_data.get("protection_metrics", {})
            
            # Add overall protection status
            protection_data.append({
                "id": f"mev_protection_overall_{int(time.time())}",
                "timestamp": int(time.time()),
                "category": "protection",
                "name": "overall_protection_status",
                "value": protection_metrics.get("protection_score", 0),
                "unit": "score",
                "metadata": {
                    "source_system": "mev_monitoring",
                    "protected_txs": protection_metrics.get("protected_transactions", 0),
                    "prevented_attacks": protection_metrics.get("prevented_attacks", 0)
                }
            })
            
            # Add private mempool usage
            protection_data.append({
                "id": f"mev_private_mempool_{int(time.time())}",
                "timestamp": int(time.time()),
                "category": "protection",
                "name": "private_mempool_usage",
                "value": protection_metrics.get("private_mempool_usage", 0),
                "unit": "count",
                "metadata": {
                    "source_system": "mev_monitoring"
                }
            })
            
            # Add public mempool usage
            protection_data.append({
                "id": f"mev_public_mempool_{int(time.time())}",
                "timestamp": int(time.time()),
                "category": "protection",
                "name": "public_mempool_usage",
                "value": protection_metrics.get("public_mempool_usage", 0),
                "unit": "count",
                "metadata": {
                    "source_system": "mev_monitoring"
                }
            })
            
            # Add gas savings
            protection_data.append({
                "id": f"mev_gas_savings_{int(time.time())}",
                "timestamp": int(time.time()),
                "category": "protection",
                "name": "gas_savings",
                "value": protection_metrics.get("gas_savings", 0),
                "unit": "ETH",
                "metadata": {
                    "source_system": "mev_monitoring"
                }
            })
            
            # Add slippage prevented
            protection_data.append({
                "id": f"mev_slippage_prevented_{int(time.time())}",
                "timestamp": int(time.time()),
                "category": "protection",
                "name": "slippage_prevented",
                "value": protection_metrics.get("slippage_prevented", 0),
                "unit": "percent",
                "metadata": {
                    "source_system": "mev_monitoring"
                }
            })
            
            # Add protection strategies status
            strategies = dashboard_data.get("protection_strategies", {})
            for strategy_name, strategy_data in strategies.items():
                protection_data.append({
                    "id": f"mev_strategy_{strategy_name}_{int(time.time())}",
                    "timestamp": int(time.time()),
                    "category": "protection_strategy",
                    "name": f"{strategy_name}_effectiveness",
                    "value": strategy_data.get("effectiveness", 0),
                    "unit": "percent",
                    "metadata": {
                        "source_system": "mev_monitoring",
                        "strategy": strategy_name,
                        "enabled": strategy_data.get("enabled", False),
                        "last_update": strategy_data.get("last_update", 0)
                    }
                })
            
            return protection_data
            
        except Exception as e:
            logger.error(f"Error getting protection status data: {e}")
            return []
    
    async def _get_transaction_analysis_data(self) -> List[Dict[str, Any]]:
        """Get transaction analysis data from the MEV monitoring system"""
        try:
            # Get dashboard data which includes transaction analysis
            dashboard_data = self.mev_system.get_dashboard_data()
            
            transaction_data = []
            
            # Extract transaction metrics
            tx_metrics = dashboard_data.get("transaction_metrics", {})
            
            # Add transaction success rate
            transaction_data.append({
                "id": f"mev_tx_success_rate_{int(time.time())}",
                "timestamp": int(time.time()),
                "category": "transaction",
                "name": "success_rate",
                "value": tx_metrics.get("success_rate", 0),
                "unit": "percent",
                "metadata": {
                    "source_system": "mev_monitoring",
                    "total_txs": tx_metrics.get("total_transactions", 0),
                    "successful_txs": tx_metrics.get("successful_transactions", 0)
                }
            })
            
            # Add average gas price
            transaction_data.append({
                "id": f"mev_avg_gas_price_{int(time.time())}",
                "timestamp": int(time.time()),
                "category": "transaction",
                "name": "average_gas_price",
                "value": tx_metrics.get("average_gas_price", 0),
                "unit": "gwei",
                "metadata": {
                    "source_system": "mev_monitoring"
                }
            })
            
            # Add average confirmation time
            transaction_data.append({
                "id": f"mev_avg_confirmation_time_{int(time.time())}",
                "timestamp": int(time.time()),
                "category": "transaction",
                "name": "average_confirmation_time",
                "value": tx_metrics.get("average_confirmation_time", 0),
                "unit": "seconds",
                "metadata": {
                    "source_system": "mev_monitoring"
                }
            })
            
            # Add recent transactions analysis
            recent_txs = dashboard_data.get("recent_transactions", [])
            for i, tx in enumerate(recent_txs[:10]):  # Limit to 10 most recent
                transaction_data.append({
                    "id": f"mev_tx_{tx.get('hash', i)}_{int(time.time())}",
                    "timestamp": tx.get("timestamp", int(time.time())),
                    "category": "transaction_detail",
                    "name": f"transaction_{i}",
                    "value": tx.get("value", 0),
                    "unit": "ETH",
                    "metadata": {
                        "source_system": "mev_monitoring",
                        "tx_hash": tx.get("hash", ""),
                        "block_number": tx.get("block_number", 0),
                        "gas_price": tx.get("gas_price", 0),
                        "gas_used": tx.get("gas_used", 0),
                        "status": tx.get("status", ""),
                        "protection_used": tx.get("protection_used", False),
                        "protection_type": tx.get("protection_type", "")
                    }
                })
            
            return transaction_data
            
        except Exception as e:
            logger.error(f"Error getting transaction analysis data: {e}")
            return []

# For testing the adapter directly
async def test_adapter():
    """Test the MEV Monitoring Adapter"""
    # Create a test configuration
    test_config = {
        "enabled": True,
        "adapter": "mev_monitoring_adapter",
        "endpoints": ["mev_alerts", "protection_status", "transaction_analysis"],
        "data_format": "json"
    }
    
    # Initialize the adapter
    adapter = MEVAdapter("mev_monitoring", test_config)
    
    # Test each endpoint
    for endpoint in ["mev_alerts", "protection_status", "transaction_analysis"]:
        print(f"\nTesting endpoint: {endpoint}")
        data = await adapter.get_data(endpoint)
        print(f"Retrieved {len(data)} records")
        if data:
            print(f"Sample data: {json.dumps(data[0], indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_adapter())