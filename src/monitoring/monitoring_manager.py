#!/usr/bin/env python3
# =================================================================================================
# MONITORING MANAGER MODULE
# =================================================================================================

import os
import yaml
import json
import logging
import asyncio
import requests
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Import machine learning libraries
try:
    from sklearn.ensemble import IsolationForest
    from sklearn.neighbors import LocalOutlierFactor
    from sklearn.svm import OneClassSVM
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logging.warning("Scikit-learn not available. Install with: pip install scikit-learn")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("monitoring_manager.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("monitoring_manager")

@dataclass
class Alert:
    """Alert data"""
    name: str
    severity: str
    message: str
    description: str
    timestamp: datetime
    labels: Dict[str, str]
    value: float
    status: str = "firing"  # firing or resolved


class MonitoringManager:
    """
    Monitoring and alerting infrastructure manager
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize monitoring manager
        
        Args:
            config_path: Path to monitoring configuration file
        """
        # Load environment variables
        load_dotenv()
        
        self.config_path = config_path or os.getenv("MONITORING_CONFIG_PATH", "monitoring_config.yaml")
        self.config = self._load_config()
        
        # Initialize components
        self.prometheus_url = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
        self.elasticsearch_url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
        self.grafana_url = os.getenv("GRAFANA_URL", "http://localhost:3000")
        
        # Initialize behavioral analysis engine
        self.behavioral_analysis = BehavioralAnalysisEngine(self.config.get("behavioral_analysis", {}))
        
        # Initialize automated response system
        self.automated_response = AutomatedResponseSystem(self.config.get("automated_response", {}))
        
        # Initialize alert manager
        self.alert_manager = AlertManager(self.config.get("automated_response", {}).get("alerting", {}))
        
        logger.info("Monitoring Manager initialized")
    
    def _load_config(self) -> Dict:
        """
        Load configuration from YAML file
        
        Returns:
            Configuration dictionary
        """
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            logger.info(f"Loaded monitoring configuration from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load monitoring configuration: {e}")
            return {}
    
    async def query_prometheus(self, query: str, time: Optional[datetime] = None, timeout: Optional[float] = None) -> Dict:
        """
        Query Prometheus
        
        Args:
            query: PromQL query
            time: Query time (default: now)
            timeout: Query timeout in seconds
            
        Returns:
            Query result
        """
        params = {"query": query}
        
        if time:
            params["time"] = time.timestamp()
        
        if timeout:
            params["timeout"] = str(timeout)
        
        try:
            response = requests.get(f"{self.prometheus_url}/api/v1/query", params=params)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            logger.error(f"Failed to query Prometheus: {e}")
            return {"status": "error", "error": str(e)}
    
    async def query_prometheus_range(self, query: str, start: datetime, end: datetime, step: str = "15s") -> Dict:
        """
        Query Prometheus for a range of time
        
        Args:
            query: PromQL query
            start: Start time
            end: End time
            step: Query resolution step
            
        Returns:
            Query result
        """
        params = {
            "query": query,
            "start": start.timestamp(),
            "end": end.timestamp(),
            "step": step
        }
        
        try:
            response = requests.get(f"{self.prometheus_url}/api/v1/query_range", params=params)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            logger.error(f"Failed to query Prometheus range: {e}")
            return {"status": "error", "error": str(e)}
    
    async def query_elasticsearch(self, index: str, query: Dict, size: int = 100) -> Dict:
        """
        Query Elasticsearch
        
        Args:
            index: Elasticsearch index
            query: Elasticsearch query
            size: Maximum number of results
            
        Returns:
            Query result
        """
        url = f"{self.elasticsearch_url}/{index}/_search"
        
        params = {
            "size": size
        }
        
        try:
            response = requests.post(url, json=query, params=params)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            logger.error(f"Failed to query Elasticsearch: {e}")
            return {"error": str(e)}
    
    async def get_alerts(self) -> List[Alert]:
        """
        Get current alerts from Prometheus Alertmanager
        
        Returns:
            List of alerts
        """
        try:
            response = requests.get(f"{self.prometheus_url}/api/v1/alerts")
            response.raise_for_status()
            
            data = response.json()
            
            alerts = []
            for alert in data.get("data", {}).get("alerts", []):
                alerts.append(Alert(
                    name=alert.get("labels", {}).get("alertname", "Unknown"),
                    severity=alert.get("labels", {}).get("severity", "unknown"),
                    message=alert.get("annotations", {}).get("summary", ""),
                    description=alert.get("annotations", {}).get("description", ""),
                    timestamp=datetime.fromisoformat(alert.get("startsAt").replace("Z", "+00:00")),
                    labels=alert.get("labels", {}),
                    value=float(alert.get("value", 0)),
                    status=alert.get("state", "firing")
                ))
            
            return alerts
        except Exception as e:
            logger.error(f"Failed to get alerts: {e}")
            return []
    
    async def create_dashboard(self, dashboard: Dict) -> Dict:
        """
        Create a Grafana dashboard
        
        Args:
            dashboard: Dashboard configuration
            
        Returns:
            Creation result
        """
        url = f"{self.grafana_url}/api/dashboards/db"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv('GRAFANA_API_KEY')}"
        }
        
        try:
            response = requests.post(url, json=dashboard, headers=headers)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            logger.error(f"Failed to create dashboard: {e}")
            return {"error": str(e)}
    
    async def monitor_system_health(self) -> Dict:
        """
        Monitor system health
        
        Returns:
            System health metrics
        """
        # Query CPU usage
        cpu_result = await self.query_prometheus('100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)')
        
        # Query memory usage
        memory_result = await self.query_prometheus('(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100')
        
        # Query disk usage
        disk_result = await self.query_prometheus('100 - ((node_filesystem_avail_bytes{mountpoint="/"} * 100) / node_filesystem_size_bytes{mountpoint="/"})')
        
        # Extract values
        cpu_usage = 0
        memory_usage = 0
        disk_usage = 0
        
        if cpu_result.get("status") == "success":
            for result in cpu_result.get("data", {}).get("result", []):
                cpu_usage = float(result.get("value", [0, "0"])[1])
                break
        
        if memory_result.get("status") == "success":
            for result in memory_result.get("data", {}).get("result", []):
                memory_usage = float(result.get("value", [0, "0"])[1])
                break
        
        if disk_result.get("status") == "success":
            for result in disk_result.get("data", {}).get("result", []):
                disk_usage = float(result.get("value", [0, "0"])[1])
                break
        
        # Create health metrics
        health_metrics = {
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "disk_usage": disk_usage,
            "timestamp": datetime.now().isoformat()
        }
        
        # Check for critical conditions
        if cpu_usage > 90:
            await self.automated_response.trigger_action("high_cpu_usage", {"cpu_usage": cpu_usage})
        
        if disk_usage > 85:
            await self.automated_response.trigger_action("disk_space_low", {"disk_usage": disk_usage})
        
        return health_metrics
    
    async def monitor_database_health(self) -> Dict:
        """
        Monitor database health
        
        Returns:
            Database health metrics
        """
        # Query PostgreSQL connections
        connections_result = await self.query_prometheus('sum by (datname) (pg_stat_activity_count)')
        
        # Query PostgreSQL query duration
        duration_result = await self.query_prometheus('pg_stat_activity_max_tx_duration{datname!~"template.*|postgres"}')
        
        # Extract values
        connections = {}
        max_duration = 0
        
        if connections_result.get("status") == "success":
            for result in connections_result.get("data", {}).get("result", []):
                datname = result.get("metric", {}).get("datname", "unknown")
                connections[datname] = float(result.get("value", [0, "0"])[1])
        
        if duration_result.get("status") == "success":
            for result in duration_result.get("data", {}).get("result", []):
                duration = float(result.get("value", [0, "0"])[1])
                max_duration = max(max_duration, duration)
        
        # Create health metrics
        health_metrics = {
            "connections": connections,
            "max_query_duration": max_duration,
            "timestamp": datetime.now().isoformat()
        }
        
        # Check for critical conditions
        total_connections = sum(connections.values())
        if total_connections > 100:
            await self.automated_response.trigger_action("database_connection_spike", {"db_connections": total_connections})
        
        return health_metrics
    
    async def monitor_arbitrage_performance(self) -> Dict:
        """
        Monitor arbitrage performance
        
        Returns:
            Arbitrage performance metrics
        """
        # Query detected opportunities
        opportunities_result = await self.query_prometheus('arbitrage_opportunities_detected_total')
        
        # Query executed trades
        trades_result = await self.query_prometheus('arbitrage_trades_executed_total')
        
        # Query profit
        profit_result = await self.query_prometheus('arbitrage_profit_total')
        
        # Query gas costs
        gas_result = await self.query_prometheus('arbitrage_gas_cost_total')
        
        # Query execution failures
        failures_result = await self.query_prometheus('arbitrage_execution_failures_total')
        
        # Extract values
        opportunities = 0
        trades = 0
        profit = 0
        gas_cost = 0
        failures = 0
        
        if opportunities_result.get("status") == "success":
            for result in opportunities_result.get("data", {}).get("result", []):
                opportunities = float(result.get("value", [0, "0"])[1])
                break
        
        if trades_result.get("status") == "success":
            for result in trades_result.get("data", {}).get("result", []):
                trades = float(result.get("value", [0, "0"])[1])
                break
        
        if profit_result.get("status") == "success":
            for result in profit_result.get("data", {}).get("result", []):
                profit = float(result.get("value", [0, "0"])[1])
                break
        
        if gas_result.get("status") == "success":
            for result in gas_result.get("data", {}).get("result", []):
                gas_cost = float(result.get("value", [0, "0"])[1])
                break
        
        if failures_result.get("status") == "success":
            for result in failures_result.get("data", {}).get("result", []):
                failures = float(result.get("value", [0, "0"])[1])
                break
        
        # Create performance metrics
        performance_metrics = {
            "opportunities_detected": opportunities,
            "trades_executed": trades,
            "total_profit": profit,
            "total_gas_cost": gas_cost,
            "execution_failures": failures,
            "net_profit": profit - gas_cost,
            "execution_rate": trades / opportunities if opportunities > 0 else 0,
            "timestamp": datetime.now().isoformat()
        }
        
        # Check for critical conditions
        if failures > 0:
            await self.automated_response.trigger_action("arbitrage_execution_failure", {"arbitrage_execution_failures": failures})
        
        return performance_metrics
    
    async def analyze_logs(self, time_range: timedelta = timedelta(hours=1)) -> Dict:
        """
        Analyze logs for anomalies
        
        Args:
            time_range: Time range to analyze
            
        Returns:
            Log analysis results
        """
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - time_range
        
        # Create Elasticsearch query
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "timestamp": {
                                    "gte": start_time.isoformat(),
                                    "lte": end_time.isoformat()
                                }
                            }
                        }
                    ]
                }
            },
            "aggs": {
                "log_levels": {
                    "terms": {
                        "field": "level.keyword",
                        "size": 10
                    }
                },
                "services": {
                    "terms": {
                        "field": "service.keyword",
                        "size": 10
                    }
                },
                "error_count": {
                    "filter": {
                        "term": {
                            "level.keyword": "ERROR"
                        }
                    }
                },
                "avg_duration": {
                    "avg": {
                        "field": "duration_ms"
                    }
                }
            }
        }
        
        # Query Elasticsearch
        result = await self.query_elasticsearch("logs-*", query)
        
        # Extract aggregations
        aggregations = result.get("aggregations", {})
        
        log_levels = {}
        for bucket in aggregations.get("log_levels", {}).get("buckets", []):
            log_levels[bucket.get("key")] = bucket.get("doc_count", 0)
        
        services = {}
        for bucket in aggregations.get("services", {}).get("buckets", []):
            services[bucket.get("key")] = bucket.get("doc_count", 0)
        
        error_count = aggregations.get("error_count", {}).get("doc_count", 0)
        avg_duration = aggregations.get("avg_duration", {}).get("value", 0)
        
        # Create analysis results
        analysis_results = {
            "log_levels": log_levels,
            "services": services,
            "error_count": error_count,
            "avg_duration": avg_duration,
            "total_logs": result.get("hits", {}).get("total", {}).get("value", 0),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
        
        # Run behavioral analysis on logs
        if ML_AVAILABLE:
            # Extract log data for analysis
            logs = []
            for hit in result.get("hits", {}).get("hits", []):
                source = hit.get("_source", {})
                logs.append({
                    "timestamp": source.get("timestamp"),
                    "level": source.get("level"),
                    "service": source.get("service"),
                    "duration_ms": source.get("duration_ms", 0),
                    "status_code": source.get("status_code", 0),
                    "method": source.get("method"),
                    "path": source.get("path"),
                    "ip": source.get("ip")
                })
            
            # Convert to DataFrame
            if logs:
                df = pd.DataFrame(logs)
                
                # Run anomaly detection
                anomalies = await self.behavioral_analysis.detect_anomalies(df)
                
                # Add anomalies to results
                analysis_results["anomalies"] = anomalies
        
        return analysis_results
    
    async def run_monitoring_loop(self, interval: int = 60):
        """
        Run continuous monitoring loop
        
        Args:
            interval: Monitoring interval in seconds
        """
        logger.info(f"Starting monitoring loop with interval {interval} seconds")
        
        while True:
            try:
                # Monitor system health
                system_health = await self.monitor_system_health()
                logger.info(f"System health: CPU {system_health['cpu_usage']:.1f}%, Memory {system_health['memory_usage']:.1f}%, Disk {system_health['disk_usage']:.1f}%")
                
                # Monitor database health
                db_health = await self.monitor_database_health()
                logger.info(f"Database health: {sum(db_health['connections'].values())} connections, {db_health['max_query_duration']:.1f}s max query duration")
                
                # Monitor arbitrage performance
                arbitrage_performance = await self.monitor_arbitrage_performance()
                logger.info(f"Arbitrage performance: {arbitrage_performance['opportunities_detected']} opportunities, {arbitrage_performance['trades_executed']} trades, ${arbitrage_performance['net_profit']:.2f} net profit")
                
                # Get current alerts
                alerts = await self.get_alerts()
                if alerts:
                    logger.info(f"Current alerts: {len(alerts)}")
                    for alert in alerts:
                        logger.info(f"  {alert.severity.upper()}: {alert.name} - {alert.message}")
                
                # Run health checks
                await self.run_health_checks()
                
                # Wait for next interval
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(10)  # Wait a bit before retrying
    
    async def run_health_checks(self):
        """Run health checks for all services"""
        services = [
            {"name": "prometheus", "url": f"{self.prometheus_url}/-/healthy"},
            {"name": "elasticsearch", "url": f"{self.elasticsearch_url}/_cluster/health"},
            {"name": "grafana", "url": f"{self.grafana_url}/api/health"}
        ]
        
        for service in services:
            try:
                response = requests.get(service["url"], timeout=5)
                
                if response.status_code == 200:
                    logger.debug(f"Health check passed for {service['name']}")
                else:
                    logger.warning(f"Health check failed for {service['name']}: {response.status_code}")
                    
                    # Increment failure counter
                    await self.query_prometheus(f'health_check_failures{{service="{service["name"]}"}} + 1')
            except Exception as e:
                logger.error(f"Health check error for {service['name']}: {e}")
                
                # Increment failure counter
                await self.query_prometheus(f'health_check_failures{{service="{service["name"]}"}} + 1')


class BehavioralAnalysisEngine:
    """
    Behavioral analysis engine for anomaly detection
    """
    
    def __init__(self, config: Dict):
        """
        Initialize behavioral analysis engine
        
        Args:
            config: Behavioral analysis configuration
        """
        self.config = config
        self.anomaly_detection_config = config.get("anomaly_detection", {})
        self.user_behavior_config = config.get("user_behavior", {})
        self.threat_hunting_config = config.get("threat_hunting", {})
        
        # Initialize models
        self.models = {}
        
        # Initialize baselines
        self.baselines = {}
        
        logger.info("Behavioral Analysis Engine initialized")
    
    async def detect_anomalies(self, data: pd.DataFrame) -> Dict:
        """
        Detect anomalies in data
        
        Args:
            data: Data to analyze
            
        Returns:
            Anomaly detection results
        """
        if not ML_AVAILABLE:
            return {"error": "Machine learning libraries not available"}
        
        # Get algorithms from configuration
        algorithms = self.anomaly_detection_config.get("algorithms", [])
        
        # Initialize results
        results = {
            "anomalies": [],
            "anomaly_count": 0,
            "total_records": len(data)
        }
        
        # Run each algorithm
        for algorithm in algorithms:
            name = algorithm.get("name")
            params = algorithm.get("params", {})
            
            try:
                # Initialize model
                if name == "isolation_forest":
                    model = IsolationForest(**params)
                elif name == "local_outlier_factor":
                    model = LocalOutlierFactor(**params)
                elif name == "one_class_svm":
                    model = OneClassSVM(**params)
                else:
                    logger.warning(f"Unknown algorithm: {name}")
                    continue
                
                # Prepare features
                features = self._prepare_features(data)
                
                if features.empty:
                    logger.warning("No features available for anomaly detection")
                    continue
                
                # Fit and predict
                if name == "local_outlier_factor":
                    # LOF has fit_predict method
                    predictions = model.fit_predict(features)
                else:
                    # Other models have separate fit and predict methods
                    model.fit(features)
                    predictions = model.predict(features)
                
                # Convert predictions to anomaly flags (-1 for anomalies, 1 for normal)
                anomalies = predictions == -1
                
                # Get anomaly indices
                anomaly_indices = np.where(anomalies)[0]
                
                # Add anomalies to results
                for idx in anomaly_indices:
                    if idx < len(data):
                        results["anomalies"].append({
                            "algorithm": name,
                            "index": int(idx),
                            "timestamp": data.iloc[idx].get("timestamp") if "timestamp" in data.columns else None,
                            "features": {col: data.iloc[idx][col] for col in features.columns}
                        })
                
                # Update anomaly count
                results["anomaly_count"] += len(anomaly_indices)
                
                logger.info(f"Detected {len(anomaly_indices)} anomalies with {name}")
            except Exception as e:
                logger.error(f"Error detecting anomalies with {name}: {e}")
        
        return results
    
    def _prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare features for anomaly detection
        
        Args:
            data: Raw data
            
        Returns:
            Feature DataFrame
        """
        # Get feature configuration
        feature_config = self.anomaly_detection_config.get("features", [])
        
        # Initialize features DataFrame
        features = pd.DataFrame()
        
        # Extract numeric columns
        numeric_columns = data.select_dtypes(include=["number"]).columns.tolist()
        
        # Use numeric columns as features
        for col in numeric_columns:
            features[col] = data[col].fillna(0)
        
        # Add timestamp-based features if timestamp column exists
        if "timestamp" in data.columns:
            # Convert timestamp to datetime if it's not already
            if not pd.api.types.is_datetime64_any_dtype(data["timestamp"]):
                data["timestamp"] = pd.to_datetime(data["timestamp"])
            
            # Extract time components
            features["hour_of_day"] = data["timestamp"].dt.hour
            features["day_of_week"] = data["timestamp"].dt.dayofweek
            features["is_weekend"] = (data["timestamp"].dt.dayofweek >= 5).astype(int)
        
        # Add categorical features as one-hot encoding
        categorical_columns = data.select_dtypes(include=["object", "category"]).columns.tolist()
        
        for col in categorical_columns:
            # Skip timestamp column
            if col == "timestamp":
                continue
            
            # One-hot encode
            dummies = pd.get_dummies(data[col], prefix=col)
            features = pd.concat([features, dummies], axis=1)
        
        return features
    
    async def analyze_user_behavior(self, user_data: pd.DataFrame) -> Dict:
        """
        Analyze user behavior for anomalies
        
        Args:
            user_data: User behavior data
            
        Returns:
            User behavior analysis results
        """
        if not ML_AVAILABLE:
            return {"error": "Machine learning libraries not available"}
        
        # Get feature configuration
        feature_config = self.user_behavior_config.get("features", [])
        
        # Initialize results
        results = {
            "anomalies": [],
            "anomaly_count": 0,
            "total_users": len(user_data["user_id"].unique()) if "user_id" in user_data.columns else 0
        }
        
        # Group by user
        if "user_id" in user_data.columns:
            user_groups = user_data.groupby("user_id")
            
            for user_id, group in user_groups:
                # Detect anomalies for this user
                user_anomalies = await self.detect_anomalies(group)
                
                # Add user ID to anomalies
                for anomaly in user_anomalies.get("anomalies", []):
                    anomaly["user_id"] = user_id
                    results["anomalies"].append(anomaly)
                
                # Update anomaly count
                results["anomaly_count"] += user_anomalies.get("anomaly_count", 0)
        else:
            # No user ID column, treat all data as one user
            results = await self.detect_anomalies(user_data)
        
        return results
    
    async def hunt_threats(self, data: pd.DataFrame) -> Dict:
        """
        Hunt for threats using predefined rules
        
        Args:
            data: Data to analyze
            
        Returns:
            Threat hunting results
        """
        # Get rules from configuration
        rules = self.threat_hunting_config.get("rules", [])
        
        # Initialize results
        results = {
            "threats": [],
            "threat_count": 0,
            "total_records": len(data)
        }
        
        # Apply each rule
        for rule in rules:
            name = rule.get("name")
            condition = rule.get("condition")
            window = rule.get("window", "1h")
            severity = rule.get("severity", "medium")
            
            try:
                # Parse condition
                # This is a simplified parser for demonstration
                # In a real system, you would use a proper expression parser
                
                # Example condition: "failed_login_count > 5"
                parts = condition.split()
                if len(parts) == 3 and parts[1] in [">", "<", ">=", "<=", "==", "!="]:
                    field = parts[0]
                    operator = parts[1]
                    threshold = float(parts[2])
                    
                    # Check if field exists in data
                    if field in data.columns:
                        # Apply condition
                        if operator == ">":
                            matches = data[data[field] > threshold]
                        elif operator == "<":
                            matches = data[data[field] < threshold]
                        elif operator == ">=":
                            matches = data[data[field] >= threshold]
                        elif operator == "<=":
                            matches = data[data[field] <= threshold]
                        elif operator == "==":
                            matches = data[data[field] == threshold]
                        elif operator == "!=":
                            matches = data[data[field] != threshold]
                        else:
                            matches = pd.DataFrame()
                        
                        # Add matches to results
                        for idx, row in matches.iterrows():
                            results["threats"].append({
                                "rule": name,
                                "severity": severity,
                                "index": idx,
                                "timestamp": row.get("timestamp") if "timestamp" in row else None,
                                "details": {col: row[col] for col in row.index if col != "timestamp"}
                            })
                        
                        # Update threat count
                        results["threat_count"] += len(matches)
                        
                        logger.info(f"Detected {len(matches)} threats with rule '{name}'")
                else:
                    logger.warning(f"Invalid condition format: {condition}")
            except Exception as e:
                logger.error(f"Error applying rule '{name}': {e}")
        
        return results


class AutomatedResponseSystem:
    """
    Automated response system for incidents
    """
    
    def __init__(self, config: Dict):
        """
        Initialize automated response system
        
        Args:
            config: Automated response configuration
        """
        self.config = config
        self.incident_response_config = config.get("incident_response", {})
        self.self_healing_config = config.get("self_healing", {})
        
        # Initialize alert manager
        self.alert_manager = AlertManager(config.get("alerting", {}))
        
        logger.info("Automated Response System initialized")
    
    async def trigger_action(self, rule_name: str, context: Dict) -> bool:
        """
        Trigger actions for a rule
        
        Args:
            rule_name: Name of the rule
            context: Context data for the rule
            
        Returns:
            True if actions were triggered
        """
        # Find rule in incident response configuration
        rule = None
        
        for r in self.incident_response_config.get("rules", []):
            if r.get("name") == rule_name:
                rule = r
                break
        
        # If rule not found in incident response, check self-healing
        if rule is None:
            for r in self.self_healing_config.get("rules", []):
                if r.get("name") == rule_name:
                    rule = r
                    break
        
        # If rule not found, return False
        if rule is None:
            logger.warning(f"Rule '{rule_name}' not found")
            return False
        
        # Check if condition is met
        condition = rule.get("condition")
        if condition:
            # Parse condition
            # This is a simplified parser for demonstration
            # In a real system, you would use a proper expression parser
            
            # Example condition: "cpu_usage > 90"
            parts = condition.split()
            if len(parts) == 3 and parts[1] in [">", "<", ">=", "<=", "==", "!="]:
                field = parts[0]
                operator = parts[1]
                threshold = float(parts[2])
                
                # Check if field exists in context
                if field in context:
                    value = context[field]
                    
                    # Apply condition
                    condition_met = False
                    
                    if operator == ">":
                        condition_met = value > threshold
                    elif operator == "<":
                        condition_met = value < threshold
                    elif operator == ">=":
                        condition_met = value >= threshold
                    elif operator == "<=":
                        condition_met = value <= threshold
                    elif operator == "==":
                        condition_met = value == threshold
                    elif operator == "!=":
                        condition_met = value != threshold
                    
                    # If condition not met, return False
                    if not condition_met:
                        logger.debug(f"Condition not met for rule '{rule_name}': {field} {operator} {threshold}")
                        return False
                else:
                    logger.warning(f"Field '{field}' not found in context for rule '{rule_name}'")
                    return False
            else:
                logger.warning(f"Invalid condition format: {condition}")
                return False
        
        # Execute actions
        actions = rule.get("actions", [])
        
        for action in actions:
            action_type = action.get("type")
            params = action.get("params", {})
            
            # Replace template variables in params
            for key, value in params.items():
                if isinstance(value, str):
                    # Replace variables like {{ variable }}
                    for var_name, var_value in context.items():
                        placeholder = f"{{{{ {var_name} }}}}"
                        if placeholder in value:
                            params[key] = value.replace(placeholder, str(var_value))
            
            # Execute action
            if action_type == "alert":
                await self._execute_alert_action(params)
            elif action_type == "execute":
                await self._execute_command_action(params)
            elif action_type == "restart":
                await self._execute_restart_action(params)
            elif action_type == "scale":
                await self._execute_scale_action(params)
            else:
                logger.warning(f"Unknown action type: {action_type}")
        
        logger.info(f"Triggered {len(actions)} actions for rule '{rule_name}'")
        return True
    
    async def _execute_alert_action(self, params: Dict) -> bool:
        """
        Execute alert action
        
        Args:
            params: Action parameters
            
        Returns:
            True if successful
        """
        channels = params.get("channels", [])
        severity = params.get("severity", "info")
        message = params.get("message", "Automated alert")
        
        # Send alert to each channel
        for channel in channels:
            await self.alert_manager.send_alert(channel, severity, message)
        
        return True
    
    async def _execute_command_action(self, params: Dict) -> bool:
        """
        Execute command action
        
        Args:
            params: Action parameters
            
        Returns:
            True if successful
        """
        command = params.get("command")
        
        if not command:
            logger.warning("No command specified for execute action")
            return False
        
        try:
            # Execute command
            import subprocess
            
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Command executed successfully: {command}")
                logger.debug(f"Command output: {result.stdout}")
                return True
            else:
                logger.error(f"Command failed: {command}")
                logger.error(f"Error output: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return False
    
    async def _execute_restart_action(self, params: Dict) -> bool:
        """
        Execute restart action
        
        Args:
            params: Action parameters
            
        Returns:
            True if successful
        """
        service = params.get("service")
        
        if not service:
            logger.warning("No service specified for restart action")
            return False
        
        try:
            # Restart service
            import subprocess
            
            result = subprocess.run(f"systemctl restart {service}", shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Service restarted successfully: {service}")
                return True
            else:
                logger.error(f"Failed to restart service: {service}")
                logger.error(f"Error output: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error restarting service: {e}")
            return False
    
    async def _execute_scale_action(self, params: Dict) -> bool:
        """
        Execute scale action
        
        Args:
            params: Action parameters
            
        Returns:
            True if successful
        """
        service = params.get("service")
        replicas = params.get("replicas")
        
        if not service or not replicas:
            logger.warning("Service or replicas not specified for scale action")
            return False
        
        try:
            # Scale service
            import subprocess
            
            # Handle relative scaling (e.g., "+2")
            if isinstance(replicas, str) and (replicas.startswith("+") or replicas.startswith("-")):
                # Get current replicas
                result = subprocess.run(f"docker service ls --filter name={service} --format '{{{{.Replicas}}}}'", shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    current = result.stdout.strip()
                    
                    # Parse current replicas (format: "3/3")
                    current_replicas = int(current.split("/")[0])
                    
                    # Calculate new replicas
                    delta = int(replicas)
                    new_replicas = current_replicas + delta
                    
                    # Ensure at least 1 replica
                    new_replicas = max(1, new_replicas)
                    
                    # Update replicas
                    replicas = new_replicas
                else:
                    logger.error(f"Failed to get current replicas for service: {service}")
                    return False
            
            # Scale service
            result = subprocess.run(f"docker service scale {service}={replicas}", shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Service scaled successfully: {service} to {replicas} replicas")
                return True
            else:
                logger.error(f"Failed to scale service: {service}")
                logger.error(f"Error output: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error scaling service: {e}")
            return False


class AlertManager:
    """
    Alert manager for sending alerts to various channels
    """
    
    def __init__(self, config: Dict):
        """
        Initialize alert manager
        
        Args:
            config: Alert manager configuration
        """
        self.config = config
        self.channels = {}
        
        # Initialize channels
        for channel in config.get("channels", []):
            name = channel.get("name")
            channel_type = channel.get("type")
            params = channel.get("params", {})
            
            if name and channel_type:
                self.channels[name] = {
                    "type": channel_type,
                    "params": params
                }
        
        logger.info(f"Alert Manager initialized with {len(self.channels)} channels")
    
    async def send_alert(self, channel_name: str, severity: str, message: str, details: Optional[Dict] = None) -> bool:
        """
        Send alert to a channel
        
        Args:
            channel_name: Name of the channel
            severity: Alert severity
            message: Alert message
            details: Additional details
            
        Returns:
            True if alert was sent
        """
        # Get channel configuration
        channel = self.channels.get(channel_name)
        
        if not channel:
            logger.warning(f"Channel '{channel_name}' not found")
            return False
        
        channel_type = channel.get("type")
        params = channel.get("params", {})
        
        # Send alert based on channel type
        if channel_type == "slack":
            return await self._send_slack_alert(params, severity, message, details)
        elif channel_type == "email":
            return await self._send_email_alert(params, severity, message, details)
        elif channel_type == "pagerduty":
            return await self._send_pagerduty_alert(params, severity, message, details)
        else:
            logger.warning(f"Unknown channel type: {channel_type}")
            return False
    
    async def _send_slack_alert(self, params: Dict, severity: str, message: str, details: Optional[Dict] = None) -> bool:
        """
        Send alert to Slack
        
        Args:
            params: Channel parameters
            severity: Alert severity
            message: Alert message
            details: Additional details
            
        Returns:
            True if alert was sent
        """
        webhook_url = params.get("webhook_url")
        channel = params.get("channel")
        
        if not webhook_url:
            logger.warning("No webhook URL specified for Slack alert")
            return False
        
        try:
            # Create Slack message
            slack_message = {
                "text": message,
                "attachments": [
                    {
                        "color": self._get_severity_color(severity),
                        "title": f"Alert: {severity.upper()}",
                        "text": message,
                        "fields": []
                    }
                ]
            }
            
            # Add channel if specified
            if channel:
                slack_message["channel"] = channel
            
            # Add details if provided
            if details:
                for key, value in details.items():
                    slack_message["attachments"][0]["fields"].append({
                        "title": key,
                        "value": str(value),
                        "short": True
                    })
            
            # Send message
            response = requests.post(webhook_url, json=slack_message)
            response.raise_for_status()
            
            logger.info(f"Sent Slack alert: {message}")
            return True
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")
            return False
    
    async def _send_email_alert(self, params: Dict, severity: str, message: str, details: Optional[Dict] = None) -> bool:
        """
        Send alert via email
        
        Args:
            params: Channel parameters
            severity: Alert severity
            message: Alert message
            details: Additional details
            
        Returns:
            True if alert was sent
        """
        smtp_server = params.get("smtp_server")
        smtp_port = params.get("smtp_port", 587)
        smtp_user = params.get("smtp_user")
        smtp_password = params.get("smtp_password")
        from_email = params.get("from_email")
        to_emails = params.get("to_emails", [])
        
        if not smtp_server or not from_email or not to_emails:
            logger.warning("Missing required parameters for email alert")
            return False
        
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Create email message
            msg = MIMEMultipart()
            msg["From"] = from_email
            msg["To"] = ", ".join(to_emails)
            msg["Subject"] = f"[{severity.upper()}] {message}"
            
            # Create email body
            body = f"Alert: {message}\n\nSeverity: {severity.upper()}\n\n"
            
            # Add details if provided
            if details:
                body += "Details:\n"
                for key, value in details.items():
                    body += f"- {key}: {value}\n"
            
            msg.attach(MIMEText(body, "plain"))
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                
                server.send_message(msg)
            
            logger.info(f"Sent email alert to {len(to_emails)} recipients: {message}")
            return True
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
            return False
    
    async def _send_pagerduty_alert(self, params: Dict, severity: str, message: str, details: Optional[Dict] = None) -> bool:
        """
        Send alert to PagerDuty
        
        Args:
            params: Channel parameters
            severity: Alert severity
            message: Alert message
            details: Additional details
            
        Returns:
            True if alert was sent
        """
        integration_key = params.get("integration_key")
        severity_mapping = params.get("severity_mapping", {})
        
        if not integration_key:
            logger.warning("No integration key specified for PagerDuty alert")
            return False
        
        try:
            # Map severity
            pd_severity = severity_mapping.get(severity, "warning")
            
            # Create PagerDuty event
            event = {
                "routing_key": integration_key,
                "event_action": "trigger",
                "payload": {
                    "summary": message,
                    "severity": pd_severity,
                    "source": "monitoring_manager",
                    "custom_details": details or {}
                }
            }
            
            # Send event
            response = requests.post("https://events.pagerduty.com/v2/enqueue", json=event)
            response.raise_for_status()
            
            logger.info(f"Sent PagerDuty alert: {message}")
            return True
        except Exception as e:
            logger.error(f"Error sending PagerDuty alert: {e}")
            return False
    
    def _get_severity_color(self, severity: str) -> str:
        """
        Get color for severity level
        
        Args:
            severity: Severity level
            
        Returns:
            Color code
        """
        severity = severity.lower()
        
        if severity == "critical":
            return "#FF0000"  # Red
        elif severity == "warning":
            return "#FFA500"  # Orange
        elif severity == "info":
            return "#0000FF"  # Blue
        else:
            return "#808080"  # Gray


# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize monitoring manager
        monitoring_manager = MonitoringManager()
        
        # Run monitoring loop
        await monitoring_manager.run_monitoring_loop()
    
    # Run main function
    asyncio.run(main())