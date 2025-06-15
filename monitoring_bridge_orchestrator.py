#!/usr/bin/env python3
"""
Monitoring Bridge Orchestrator
Connects sentinel agents with existing monitoring systems
"""

import os
import sys
import yaml
import json
import time
import logging
import asyncio
import importlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import sqlite3
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("monitoring_bridge.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MonitoringBridgeOrchestrator")

class DataSyncStatus(Enum):
    """Status of data synchronization operations"""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    PENDING = "pending"

class MonitoringBridgeOrchestrator:
    """
    Connects sentinel agents with existing monitoring systems
    Features:
    - Data sharing between monitoring systems
    - Alert correlation and deduplication
    - Unified monitoring dashboard data
    - System health aggregation
    - Performance metrics collection
    """
    
    def __init__(self, config_path: str = "sentinel_config.yaml"):
        """Initialize the Monitoring Bridge Orchestrator"""
        self.config = self._load_config(config_path)
        self.bridge_config = self.config.get("integration", {}).get("monitoring_bridge", {})
        
        # Check if monitoring bridge is enabled
        if not self.bridge_config.get("enabled", False):
            logger.warning("Monitoring Bridge is disabled in configuration")
            return
        
        # Initialize adapters
        self.adapters = {}
        self.legacy_systems = self.bridge_config.get("legacy_systems", {})
        
        # Sync state
        self.is_syncing = False
        self.sync_task = None
        self.last_sync = {}
        
        # Shared database for data integration
        self.shared_db_path = self.config.get("integration", {}).get("data_sharing", {}).get("shared_database", "sentinel_shared.db")
        self.shared_db = self._initialize_shared_db()
        
        logger.info("Monitoring Bridge Orchestrator initialized")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Config file {config_path} not found")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            sys.exit(1)
    
    def _initialize_shared_db(self) -> sqlite3.Connection:
        """Initialize the shared database for data integration"""
        try:
            conn = sqlite3.connect(self.shared_db_path)
            cursor = conn.cursor()
            
            # Create tables if they don't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                level TEXT NOT NULL,
                type TEXT NOT NULL,
                message TEXT NOT NULL,
                details TEXT,
                acknowledged INTEGER DEFAULT 0,
                resolved INTEGER DEFAULT 0,
                resolution_time INTEGER,
                resolution_message TEXT
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                category TEXT NOT NULL,
                name TEXT NOT NULL,
                value REAL,
                unit TEXT,
                metadata TEXT
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_health (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                component TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT,
                details TEXT
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_sync (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                target TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                status TEXT NOT NULL,
                records_synced INTEGER,
                error_message TEXT
            )
            ''')
            
            conn.commit()
            logger.info(f"Initialized shared database at {self.shared_db_path}")
            return conn
        except Exception as e:
            logger.error(f"Error initializing shared database: {e}")
            return None
    
    async def initialize_adapters(self):
        """Initialize all legacy system adapters"""
        for system_name, system_config in self.legacy_systems.items():
            if not system_config.get("enabled", False):
                logger.info(f"Legacy system {system_name} is disabled, skipping")
                continue
            
            adapter_name = system_config.get("adapter")
            if not adapter_name:
                logger.error(f"No adapter specified for legacy system {system_name}")
                continue
            
            try:
                # Import the adapter module dynamically
                adapter_module = importlib.import_module(adapter_name)
                adapter_class = getattr(adapter_module, f"{adapter_name.split('_')[-1].capitalize()}Adapter")
                
                # Initialize the adapter
                adapter = adapter_class(system_name, system_config)
                self.adapters[system_name] = adapter
                logger.info(f"Initialized adapter for {system_name}: {adapter_name}")
            except ImportError:
                logger.error(f"Could not import adapter module {adapter_name}")
            except AttributeError:
                logger.error(f"Could not find adapter class in module {adapter_name}")
            except Exception as e:
                logger.error(f"Error initializing adapter for {system_name}: {e}")
    
    async def start_syncing(self):
        """Start the data synchronization process"""
        if self.is_syncing:
            logger.warning("Monitoring Bridge is already syncing")
            return
        
        self.is_syncing = True
        logger.info("Starting Monitoring Bridge data synchronization")
        
        # Start the sync task
        self.sync_task = asyncio.create_task(self._sync_loop())
    
    async def stop_syncing(self):
        """Stop the data synchronization process"""
        if not self.is_syncing:
            logger.warning("Monitoring Bridge is not syncing")
            return
        
        self.is_syncing = False
        logger.info("Stopping Monitoring Bridge data synchronization")
        
        if self.sync_task:
            self.sync_task.cancel()
            try:
                await self.sync_task
            except asyncio.CancelledError:
                pass
            self.sync_task = None
    
    async def _sync_loop(self):
        """Main synchronization loop"""
        try:
            while self.is_syncing:
                logger.debug("Running monitoring bridge sync cycle")
                
                # Sync data from all legacy systems
                for system_name, adapter in self.adapters.items():
                    try:
                        await self._sync_legacy_system(system_name, adapter)
                    except Exception as e:
                        logger.error(f"Error syncing legacy system {system_name}: {e}")
                
                # Perform alert correlation and deduplication
                await self._correlate_alerts()
                
                # Clean up old data
                await self._cleanup_old_data()
                
                # Wait for the next sync cycle
                sync_interval = self.bridge_config.get("sync_interval", 30)
                await asyncio.sleep(sync_interval)
        except asyncio.CancelledError:
            logger.info("Monitoring bridge sync loop cancelled")
        except Exception as e:
            logger.error(f"Error in sync loop: {e}")
            self.is_syncing = False
    
    async def _sync_legacy_system(self, system_name: str, adapter) -> Dict[str, Any]:
        """Synchronize data from a legacy monitoring system"""
        logger.info(f"Syncing data from legacy system: {system_name}")
        system_config = self.legacy_systems.get(system_name, {})
        endpoints = system_config.get("endpoints", [])
        
        sync_results = {
            "system": system_name,
            "timestamp": int(time.time()),
            "endpoints": {},
            "overall_status": DataSyncStatus.PENDING.value
        }
        
        success_count = 0
        for endpoint in endpoints:
            try:
                # Get data from the legacy system through the adapter
                data = await adapter.get_data(endpoint)
                
                # Process and store the data
                if data:
                    records_synced = await self._store_legacy_data(system_name, endpoint, data)
                    sync_results["endpoints"][endpoint] = {
                        "status": DataSyncStatus.SUCCESS.value,
                        "records_synced": records_synced,
                        "timestamp": int(time.time())
                    }
                    success_count += 1
                else:
                    sync_results["endpoints"][endpoint] = {
                        "status": DataSyncStatus.FAILED.value,
                        "error": "No data returned from adapter",
                        "timestamp": int(time.time())
                    }
            except Exception as e:
                logger.error(f"Error syncing endpoint {endpoint} from {system_name}: {e}")
                sync_results["endpoints"][endpoint] = {
                    "status": DataSyncStatus.FAILED.value,
                    "error": str(e),
                    "timestamp": int(time.time())
                }
        
        # Determine overall sync status
        if success_count == len(endpoints):
            sync_results["overall_status"] = DataSyncStatus.SUCCESS.value
        elif success_count > 0:
            sync_results["overall_status"] = DataSyncStatus.PARTIAL.value
        else:
            sync_results["overall_status"] = DataSyncStatus.FAILED.value
        
        # Update last sync time
        self.last_sync[system_name] = {
            "timestamp": int(time.time()),
            "status": sync_results["overall_status"]
        }
        
        # Log sync results
        logger.info(f"Sync results for {system_name}: {sync_results['overall_status']}")
        
        # Store sync results in the database
        await self._store_sync_results(sync_results)
        
        return sync_results
    
    async def _store_legacy_data(self, system_name: str, endpoint: str, data: Any) -> int:
        """Store data from legacy system in the shared database"""
        if not self.shared_db:
            logger.error("Shared database not initialized")
            return 0
        
        records_synced = 0
        
        try:
            cursor = self.shared_db.cursor()
            
            # Determine data type and store accordingly
            if endpoint in ["alerts", "manipulation_alerts", "mev_alerts"]:
                # Process alerts
                for alert in data:
                    alert_id = alert.get("id", f"{system_name}_{int(time.time())}_{records_synced}")
                    cursor.execute('''
                    INSERT OR REPLACE INTO alerts 
                    (id, source, timestamp, level, type, message, details, acknowledged, resolved)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        alert_id,
                        system_name,
                        alert.get("timestamp", int(time.time())),
                        alert.get("level", "UNKNOWN"),
                        alert.get("type", endpoint),
                        alert.get("message", ""),
                        json.dumps(alert.get("details", {})),
                        alert.get("acknowledged", 0),
                        alert.get("resolved", 0)
                    ))
                    records_synced += 1
            
            elif endpoint in ["metrics", "health", "price_feeds", "protection_status", "transaction_analysis"]:
                # Process metrics
                for metric in data:
                    metric_id = metric.get("id", f"{system_name}_{endpoint}_{int(time.time())}_{records_synced}")
                    cursor.execute('''
                    INSERT OR REPLACE INTO metrics
                    (id, source, timestamp, category, name, value, unit, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        metric_id,
                        system_name,
                        metric.get("timestamp", int(time.time())),
                        endpoint,
                        metric.get("name", ""),
                        metric.get("value"),
                        metric.get("unit", ""),
                        json.dumps(metric.get("metadata", {}))
                    ))
                    records_synced += 1
            
            elif endpoint in ["oracle_health", "system_health"]:
                # Process system health
                for health in data:
                    health_id = health.get("id", f"{system_name}_{endpoint}_{int(time.time())}_{records_synced}")
                    cursor.execute('''
                    INSERT OR REPLACE INTO system_health
                    (id, source, timestamp, component, status, message, details)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        health_id,
                        system_name,
                        health.get("timestamp", int(time.time())),
                        health.get("component", ""),
                        health.get("status", "UNKNOWN"),
                        health.get("message", ""),
                        json.dumps(health.get("details", {}))
                    ))
                    records_synced += 1
            
            self.shared_db.commit()
            logger.info(f"Stored {records_synced} records from {system_name}/{endpoint}")
            
        except Exception as e:
            logger.error(f"Error storing data from {system_name}/{endpoint}: {e}")
            self.shared_db.rollback()
        
        return records_synced
    
    async def _store_sync_results(self, sync_results: Dict[str, Any]):
        """Store synchronization results in the database"""
        if not self.shared_db:
            logger.error("Shared database not initialized")
            return
        
        try:
            cursor = self.shared_db.cursor()
            
            # Store overall sync result
            sync_id = f"{sync_results['system']}_{sync_results['timestamp']}"
            
            cursor.execute('''
            INSERT INTO data_sync
            (id, source, target, timestamp, status, records_synced, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                sync_id,
                sync_results['system'],
                "sentinel_shared",
                sync_results['timestamp'],
                sync_results['overall_status'],
                sum(endpoint.get("records_synced", 0) for endpoint in sync_results["endpoints"].values() if "records_synced" in endpoint),
                json.dumps({endpoint: data.get("error", "") for endpoint, data in sync_results["endpoints"].items() if "error" in data})
            ))
            
            self.shared_db.commit()
            
        except Exception as e:
            logger.error(f"Error storing sync results: {e}")
            self.shared_db.rollback()
    
    async def _correlate_alerts(self):
        """Correlate and deduplicate alerts from different systems"""
        if not self.shared_db:
            logger.error("Shared database not initialized")
            return
        
        try:
            cursor = self.shared_db.cursor()
            
            # Get recent unresolved alerts
            cursor.execute('''
            SELECT id, source, timestamp, level, type, message, details
            FROM alerts
            WHERE resolved = 0
            AND timestamp > ?
            ORDER BY timestamp DESC
            ''', (int(time.time()) - 3600,))  # Last hour
            
            alerts = cursor.fetchall()
            
            # Group alerts by similarity
            alert_groups = {}
            for alert in alerts:
                alert_id, source, timestamp, level, alert_type, message, details = alert
                
                # Create a simple similarity key based on type and partial message
                # This is a basic approach - more sophisticated NLP could be used
                message_words = message.lower().split()
                similarity_key = f"{alert_type}_{' '.join(message_words[:3])}"
                
                if similarity_key not in alert_groups:
                    alert_groups[similarity_key] = []
                
                alert_groups[similarity_key].append(alert)
            
            # Process groups with multiple alerts (potential duplicates)
            for similarity_key, group in alert_groups.items():
                if len(group) > 1:
                    # Sort by timestamp (newest first)
                    group.sort(key=lambda x: x[2], reverse=True)
                    
                    # Keep the newest alert, mark others as duplicates
                    primary_alert = group[0]
                    primary_id = primary_alert[0]
                    
                    for duplicate in group[1:]:
                        duplicate_id = duplicate[0]
                        duplicate_details = json.loads(duplicate[6])
                        
                        # Update duplicate alert with reference to primary
                        duplicate_details["correlated_with"] = primary_id
                        duplicate_details["correlation_type"] = "duplicate"
                        
                        cursor.execute('''
                        UPDATE alerts
                        SET details = ?, resolved = 1, resolution_time = ?, resolution_message = ?
                        WHERE id = ?
                        ''', (
                            json.dumps(duplicate_details),
                            int(time.time()),
                            f"Correlated with alert {primary_id}",
                            duplicate_id
                        ))
                        
                        logger.info(f"Correlated duplicate alert {duplicate_id} with primary alert {primary_id}")
            
            self.shared_db.commit()
            
        except Exception as e:
            logger.error(f"Error correlating alerts: {e}")
            self.shared_db.rollback()
    
    async def _cleanup_old_data(self):
        """Clean up old data based on retention policy"""
        if not self.shared_db:
            logger.error("Shared database not initialized")
            return
        
        try:
            cursor = self.shared_db.cursor()
            
            # Get retention days from config
            retention_days = self.config.get("integration", {}).get("data_sharing", {}).get("retention_days", 30)
            cutoff_time = int(time.time()) - (retention_days * 24 * 60 * 60)
            
            # Delete old alerts
            cursor.execute('''
            DELETE FROM alerts
            WHERE timestamp < ?
            ''', (cutoff_time,))
            alerts_deleted = cursor.rowcount
            
            # Delete old metrics
            cursor.execute('''
            DELETE FROM metrics
            WHERE timestamp < ?
            ''', (cutoff_time,))
            metrics_deleted = cursor.rowcount
            
            # Delete old system health records
            cursor.execute('''
            DELETE FROM system_health
            WHERE timestamp < ?
            ''', (cutoff_time,))
            health_deleted = cursor.rowcount
            
            # Delete old sync records
            cursor.execute('''
            DELETE FROM data_sync
            WHERE timestamp < ?
            ''', (cutoff_time,))
            sync_deleted = cursor.rowcount
            
            self.shared_db.commit()
            
            logger.info(f"Cleaned up old data: {alerts_deleted} alerts, {metrics_deleted} metrics, "
                       f"{health_deleted} health records, {sync_deleted} sync records")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            self.shared_db.rollback()
    
    async def get_unified_dashboard_data(self) -> Dict[str, Any]:
        """Get unified dashboard data from all monitoring systems"""
        if not self.shared_db:
            logger.error("Shared database not initialized")
            return {}
        
        try:
            cursor = self.shared_db.cursor()
            
            dashboard_data = {
                "timestamp": int(time.time()),
                "alerts": {
                    "high_priority": [],
                    "medium_priority": [],
                    "low_priority": [],
                    "total_count": 0,
                    "unresolved_count": 0
                },
                "system_health": {},
                "metrics": {},
                "sync_status": {}
            }
            
            # Get recent high priority alerts
            cursor.execute('''
            SELECT id, source, timestamp, level, type, message, details
            FROM alerts
            WHERE level IN ('CRITICAL', 'EMERGENCY', 'HIGH')
            AND resolved = 0
            ORDER BY timestamp DESC
            LIMIT 10
            ''')
            
            for alert in cursor.fetchall():
                alert_id, source, timestamp, level, alert_type, message, details = alert
                dashboard_data["alerts"]["high_priority"].append({
                    "id": alert_id,
                    "source": source,
                    "timestamp": timestamp,
                    "level": level,
                    "type": alert_type,
                    "message": message,
                    "details": json.loads(details) if details else {}
                })
            
            # Get recent medium priority alerts
            cursor.execute('''
            SELECT id, source, timestamp, level, type, message, details
            FROM alerts
            WHERE level IN ('MEDIUM')
            AND resolved = 0
            ORDER BY timestamp DESC
            LIMIT 10
            ''')
            
            for alert in cursor.fetchall():
                alert_id, source, timestamp, level, alert_type, message, details = alert
                dashboard_data["alerts"]["medium_priority"].append({
                    "id": alert_id,
                    "source": source,
                    "timestamp": timestamp,
                    "level": level,
                    "type": alert_type,
                    "message": message,
                    "details": json.loads(details) if details else {}
                })
            
            # Get recent low priority alerts
            cursor.execute('''
            SELECT id, source, timestamp, level, type, message, details
            FROM alerts
            WHERE level IN ('LOW', 'INFO')
            AND resolved = 0
            ORDER BY timestamp DESC
            LIMIT 10
            ''')
            
            for alert in cursor.fetchall():
                alert_id, source, timestamp, level, alert_type, message, details = alert
                dashboard_data["alerts"]["low_priority"].append({
                    "id": alert_id,
                    "source": source,
                    "timestamp": timestamp,
                    "level": level,
                    "type": alert_type,
                    "message": message,
                    "details": json.loads(details) if details else {}
                })
            
            # Get alert counts
            cursor.execute('''
            SELECT COUNT(*) FROM alerts
            ''')
            dashboard_data["alerts"]["total_count"] = cursor.fetchone()[0]
            
            cursor.execute('''
            SELECT COUNT(*) FROM alerts
            WHERE resolved = 0
            ''')
            dashboard_data["alerts"]["unresolved_count"] = cursor.fetchone()[0]
            
            # Get system health
            cursor.execute('''
            SELECT source, component, status, message, details
            FROM system_health
            WHERE timestamp > ?
            ORDER BY timestamp DESC
            ''', (int(time.time()) - 3600,))  # Last hour
            
            for health in cursor.fetchall():
                source, component, status, message, details = health
                
                if source not in dashboard_data["system_health"]:
                    dashboard_data["system_health"][source] = {}
                
                dashboard_data["system_health"][source][component] = {
                    "status": status,
                    "message": message,
                    "details": json.loads(details) if details else {}
                }
            
            # Get key metrics
            cursor.execute('''
            SELECT source, category, name, value, unit
            FROM metrics
            WHERE timestamp > ?
            ORDER BY timestamp DESC
            ''', (int(time.time()) - 3600,))  # Last hour
            
            for metric in cursor.fetchall():
                source, category, name, value, unit = metric
                
                if source not in dashboard_data["metrics"]:
                    dashboard_data["metrics"][source] = {}
                
                if category not in dashboard_data["metrics"][source]:
                    dashboard_data["metrics"][source][category] = {}
                
                dashboard_data["metrics"][source][category][name] = {
                    "value": value,
                    "unit": unit
                }
            
            # Get sync status
            for system_name, sync_info in self.last_sync.items():
                dashboard_data["sync_status"][system_name] = sync_info
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error getting unified dashboard data: {e}")
            return {"error": str(e)}
    
    def close(self):
        """Close database connections and clean up resources"""
        if self.shared_db:
            self.shared_db.close()
            logger.info("Closed shared database connection")

async def main():
    """Main entry point for the Monitoring Bridge Orchestrator"""
    parser = argparse.ArgumentParser(description="Monitoring Bridge Orchestrator")
    parser.add_argument("--config", default="sentinel_config.yaml", help="Path to configuration file")
    args = parser.parse_args()
    
    # Initialize the orchestrator
    orchestrator = MonitoringBridgeOrchestrator(config_path=args.config)
    
    try:
        # Initialize adapters
        await orchestrator.initialize_adapters()
        
        # Start syncing
        await orchestrator.start_syncing()
        
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Monitoring Bridge Orchestrator interrupted")
    except Exception as e:
        logger.error(f"Error in Monitoring Bridge Orchestrator: {e}")
    finally:
        # Stop syncing
        await orchestrator.stop_syncing()
        
        # Close resources
        orchestrator.close()

if __name__ == "__main__":
    import argparse
    asyncio.run(main())