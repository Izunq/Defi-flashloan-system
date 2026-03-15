#!/usr/bin/env python3
"""
Alert Correlation Engine
Correlates related alerts to reduce noise and provide better insights
"""

import os
import sys
import time
import json
import yaml
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from collections import defaultdict
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.ensemble import IsolationForest
from scipy.stats import pearsonr

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("alert_correlation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("alert_correlation_engine")

class AlertCorrelationEngine:
    """
    Correlates related alerts to reduce noise and provide better insights
    - Uses multiple correlation models (similarity, temporal, causal)
    - Groups related alerts together
    - Generates summary insights
    - Reduces alert fatigue
    """
    
    def __init__(self, config_path="sentinel_config.yaml"):
        """
        Initialize the Alert Correlation Engine
        
        Args:
            config_path: Path to the sentinel configuration file
        """
        self.config_path = config_path
        self.alert_history = []
        self.correlation_groups = []
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.models = {}
        
        # Load configuration
        self.load_config()
        
        # Initialize correlation models
        self._init_correlation_models()
        
        logger.info("Alert Correlation Engine initialized")
    
    def load_config(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
                
            # Extract correlation-specific configuration
            self.config = config.get("advanced_features", {}).get("alert_correlation", {})
            
            # Set defaults if not specified
            if not self.config:
                self.config = {
                    "enabled": True,
                    "models": [
                        {
                            "name": "similarity_model",
                            "type": "cosine_similarity",
                            "threshold": 0.8
                        },
                        {
                            "name": "temporal_model",
                            "type": "time_window",
                            "window_seconds": 300
                        }
                    ],
                    "correlation_rules": [],
                    "noise_reduction": {
                        "enabled": True,
                        "duplicate_threshold": 0.9,
                        "max_alerts_per_group": 3,
                        "summary_generation": True
                    }
                }
                
            logger.info(f"Loaded configuration from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self.config = {}
    
    def _init_correlation_models(self):
        """Initialize correlation models based on configuration"""
        for model_config in self.config.get("models", []):
            model_name = model_config.get("name")
            model_type = model_config.get("type")
            
            if model_type == "cosine_similarity":
                self.models[model_name] = {
                    "type": model_type,
                    "threshold": model_config.get("threshold", 0.8),
                    "vectorizer": TfidfVectorizer(stop_words='english')
                }
                logger.info(f"Initialized similarity model: {model_name}")
                
            elif model_type == "time_window":
                self.models[model_name] = {
                    "type": model_type,
                    "window_seconds": model_config.get("window_seconds", 300)
                }
                logger.info(f"Initialized temporal model: {model_name}")
                
            elif model_type == "bayesian_network":
                self.models[model_name] = {
                    "type": model_type,
                    "confidence_threshold": model_config.get("confidence_threshold", 0.7),
                    "causal_relationships": {}  # Will be populated as alerts are processed
                }
                logger.info(f"Initialized causal model: {model_name}")
                
            elif model_type == "isolation_forest":
                self.models[model_name] = {
                    "type": model_type,
                    "model": IsolationForest(
                        contamination=model_config.get("contamination", 0.05),
                        n_estimators=model_config.get("n_estimators", 100),
                        random_state=42
                    ),
                    "features": []  # Will be populated as alerts are processed
                }
                logger.info(f"Initialized anomaly detection model: {model_name}")
                
            else:
                logger.warning(f"Unknown model type: {model_type}")
    
    def process_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an alert through correlation engine
        
        Args:
            alert: Alert data dictionary
            
        Returns:
            Dict[str, Any]: Processed alert with correlation information
        """
        # Check if correlation is enabled
        if not self.config.get("enabled", True):
            return alert
            
        # Add timestamp if not present
        if "timestamp" not in alert:
            alert["timestamp"] = time.time()
            
        # Add to alert history
        self.alert_history.append(alert)
        
        # Trim alert history if needed
        max_history = 1000
        if len(self.alert_history) > max_history:
            self.alert_history = self.alert_history[-max_history:]
            
        # Apply correlation rules
        correlated_alerts = self._find_correlated_alerts(alert)
        
        # Create or update correlation group
        if correlated_alerts:
            group = self._create_or_update_correlation_group(alert, correlated_alerts)
            
            # Add correlation information to alert
            alert["correlation"] = {
                "group_id": group["group_id"],
                "related_count": len(group["alerts"]) - 1,
                "is_primary": group["primary_alert"]["alert_id"] == alert.get("alert_id")
            }
            
            # If this is the primary alert and summary generation is enabled, add summary
            if alert.get("alert_id") == group["primary_alert"].get("alert_id") and \
               self.config.get("noise_reduction", {}).get("summary_generation", True):
                alert["correlation"]["summary"] = group["summary"]
                
            logger.info(f"Alert correlated with {len(correlated_alerts)} other alerts")
        else:
            # No correlations found
            alert["correlation"] = {
                "group_id": None,
                "related_count": 0,
                "is_primary": True
            }
            
            logger.info("No correlations found for alert")
            
        return alert
    
    def _find_correlated_alerts(self, alert: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find alerts that correlate with the given alert
        
        Args:
            alert: Alert data dictionary
            
        Returns:
            List[Dict[str, Any]]: List of correlated alerts
        """
        correlated_alerts = []
        
        # Apply each correlation model
        for model_name, model in self.models.items():
            model_type = model.get("type")
            
            if model_type == "cosine_similarity":
                similar_alerts = self._find_similar_alerts(alert, model)
                correlated_alerts.extend(similar_alerts)
                
            elif model_type == "time_window":
                temporal_alerts = self._find_temporal_alerts(alert, model)
                correlated_alerts.extend(temporal_alerts)
                
            elif model_type == "bayesian_network":
                causal_alerts = self._find_causal_alerts(alert, model)
                correlated_alerts.extend(causal_alerts)
                
            elif model_type == "isolation_forest":
                anomaly_alerts = self._find_anomaly_alerts(alert, model)
                correlated_alerts.extend(anomaly_alerts)
        
        # Apply correlation rules
        rule_based_alerts = self._apply_correlation_rules(alert)
        correlated_alerts.extend(rule_based_alerts)
        
        # Remove duplicates
        unique_alerts = []
        alert_ids = set()
        
        for a in correlated_alerts:
            if a.get("alert_id") not in alert_ids and a.get("alert_id") != alert.get("alert_id"):
                alert_ids.add(a.get("alert_id"))
                unique_alerts.append(a)
                
        return unique_alerts
    
    def _find_similar_alerts(self, alert: Dict[str, Any], model: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find alerts that are similar to the given alert using text similarity
        
        Args:
            alert: Alert data dictionary
            model: Similarity model configuration
            
        Returns:
            List[Dict[str, Any]]: List of similar alerts
        """
        # Extract text from alert
        alert_text = f"{alert.get('title', '')} {alert.get('message', '')} {alert.get('description', '')}"
        
        # If alert has no text, return empty list
        if not alert_text.strip():
            return []
            
        # Get threshold from model
        threshold = model.get("threshold", 0.8)
        
        # Get vectorizer from model
        vectorizer = model.get("vectorizer", self.vectorizer)
        
        # Create corpus of alert texts
        corpus = [f"{a.get('title', '')} {a.get('message', '')} {a.get('description', '')}" for a in self.alert_history]
        
        # If corpus is empty, return empty list
        if not corpus:
            return []
            
        # Fit vectorizer on corpus
        try:
            tfidf_matrix = vectorizer.fit_transform(corpus)
            
            # Get index of current alert in history
            current_index = self.alert_history.index(alert) if alert in self.alert_history else -1
            
            # If alert is not in history, add it to the end
            if current_index == -1:
                corpus.append(alert_text)
                tfidf_matrix = vectorizer.fit_transform(corpus)
                current_index = len(corpus) - 1
                
            # Calculate similarity between current alert and all others
            alert_vector = tfidf_matrix[current_index:current_index+1]
            similarities = cosine_similarity(alert_vector, tfidf_matrix).flatten()
            
            # Find indices of similar alerts
            similar_indices = [i for i, sim in enumerate(similarities) if sim >= threshold and i != current_index]
            
            # Get similar alerts
            similar_alerts = [self.alert_history[i] for i in similar_indices]
            
            return similar_alerts
        except Exception as e:
            logger.error(f"Error finding similar alerts: {e}")
            return []
    
    def _find_temporal_alerts(self, alert: Dict[str, Any], model: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find alerts that occurred within a time window of the given alert
        
        Args:
            alert: Alert data dictionary
            model: Temporal model configuration
            
        Returns:
            List[Dict[str, Any]]: List of temporal alerts
        """
        # Get time window from model
        window_seconds = model.get("window_seconds", 300)
        
        # Get alert timestamp
        timestamp = alert.get("timestamp", time.time())
        
        # Find alerts within time window
        temporal_alerts = []
        
        for a in self.alert_history:
            if a.get("alert_id") == alert.get("alert_id"):
                continue
                
            a_timestamp = a.get("timestamp", 0)
            
            if abs(timestamp - a_timestamp) <= window_seconds:
                # Check if alerts are from the same sentinel
                if a.get("sentinel") == alert.get("sentinel"):
                    temporal_alerts.append(a)
                    
        return temporal_alerts
    
    def _find_causal_alerts(self, alert: Dict[str, Any], model: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find alerts that may have a causal relationship with the given alert
        
        Args:
            alert: Alert data dictionary
            model: Causal model configuration
            
        Returns:
            List[Dict[str, Any]]: List of causally related alerts
        """
        # Get confidence threshold from model
        confidence_threshold = model.get("confidence_threshold", 0.7)
        
        # Get causal relationships from model
        causal_relationships = model.get("causal_relationships", {})
        
        # Get alert type and sentinel
        alert_type = alert.get("type", "").lower()
        sentinel = alert.get("sentinel", "").lower()
        
        # Create key for this alert type
        key = f"{sentinel}:{alert_type}"
        
        # Find causally related alerts
        causal_alerts = []
        
        # Check for known causal relationships
        if key in causal_relationships:
            for related_key, confidence in causal_relationships[key].items():
                if confidence >= confidence_threshold:
                    related_sentinel, related_type = related_key.split(":")
                    
                    # Find alerts of the related type
                    for a in self.alert_history:
                        if a.get("alert_id") == alert.get("alert_id"):
                            continue
                            
                        if a.get("sentinel", "").lower() == related_sentinel and \
                           a.get("type", "").lower() == related_type:
                            causal_alerts.append(a)
        
        # Update causal relationships based on this alert
        self._update_causal_relationships(alert, model)
        
        return causal_alerts
    
    def _update_causal_relationships(self, alert: Dict[str, Any], model: Dict[str, Any]):
        """
        Update causal relationships based on observed alerts
        
        Args:
            alert: Alert data dictionary
            model: Causal model configuration
        """
        # Get causal relationships from model
        causal_relationships = model.get("causal_relationships", {})
        
        # Get alert type and sentinel
        alert_type = alert.get("type", "").lower()
        sentinel = alert.get("sentinel", "").lower()
        
        # Create key for this alert type
        key = f"{sentinel}:{alert_type}"
        
        # Initialize if not exists
        if key not in causal_relationships:
            causal_relationships[key] = {}
            
        # Get timestamp
        timestamp = alert.get("timestamp", time.time())
        
        # Look for alerts that occurred shortly before this one
        window_seconds = 60  # 1 minute
        
        for a in self.alert_history:
            if a.get("alert_id") == alert.get("alert_id"):
                continue
                
            a_timestamp = a.get("timestamp", 0)
            
            # Only consider alerts that occurred before this one
            if 0 < (timestamp - a_timestamp) <= window_seconds:
                a_type = a.get("type", "").lower()
                a_sentinel = a.get("sentinel", "").lower()
                
                # Create key for the other alert type
                a_key = f"{a_sentinel}:{a_type}"
                
                # Update confidence
                if a_key in causal_relationships[key]:
                    # Increase confidence
                    causal_relationships[key][a_key] = min(1.0, causal_relationships[key][a_key] + 0.1)
                else:
                    # Initialize confidence
                    causal_relationships[key][a_key] = 0.5
        
        # Update model
        model["causal_relationships"] = causal_relationships
    
    def _find_anomaly_alerts(self, alert: Dict[str, Any], model: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find anomalous alerts using isolation forest
        
        Args:
            alert: Alert data dictionary
            model: Anomaly detection model configuration
            
        Returns:
            List[Dict[str, Any]]: List of anomalous alerts
        """
        # Not enough data yet
        if len(self.alert_history) < 10:
            return []
            
        # Get model
        isolation_forest = model.get("model")
        
        # Get features
        features = model.get("features", [])
        
        # If no features defined yet, try to extract numeric features
        if not features:
            # Try to extract features from alert data
            if "data" in alert and isinstance(alert["data"], dict):
                for key, value in alert["data"].items():
                    if isinstance(value, (int, float)):
                        features.append(key)
                        
            # Update model
            model["features"] = features
            
        # If still no features, return empty list
        if not features:
            return []
            
        # Extract feature values from alerts
        feature_values = []
        
        for a in self.alert_history:
            if "data" not in a or not isinstance(a["data"], dict):
                continue
                
            values = []
            
            for feature in features:
                if feature in a["data"] and isinstance(a["data"][feature], (int, float)):
                    values.append(a["data"][feature])
                else:
                    values.append(0)
                    
            if values:
                feature_values.append(values)
                
        # If not enough feature values, return empty list
        if len(feature_values) < 10:
            return []
            
        # Fit model
        try:
            isolation_forest.fit(feature_values)
            
            # Predict anomalies
            anomaly_scores = isolation_forest.decision_function(feature_values)
            
            # Find anomalous alerts
            anomalous_indices = [i for i, score in enumerate(anomaly_scores) if score < 0]
            
            # Get anomalous alerts
            anomalous_alerts = []
            
            for i, a in enumerate(self.alert_history):
                if i < len(anomaly_scores) and anomaly_scores[i] < 0:
                    if a.get("alert_id") != alert.get("alert_id"):
                        anomalous_alerts.append(a)
                        
            return anomalous_alerts
        except Exception as e:
            logger.error(f"Error finding anomalous alerts: {e}")
            return []
    
    def _apply_correlation_rules(self, alert: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Apply correlation rules to find related alerts
        
        Args:
            alert: Alert data dictionary
            
        Returns:
            List[Dict[str, Any]]: List of related alerts
        """
        rule_based_alerts = []
        
        # Get correlation rules
        correlation_rules = self.config.get("correlation_rules", [])
        
        # Apply each rule
        for rule in correlation_rules:
            # Check if rule applies to this alert
            sentinel = rule.get("sentinel")
            alert_type = rule.get("alert_type")
            alert_types = rule.get("alert_types", [])
            
            if sentinel and sentinel != alert.get("sentinel", "").lower():
                continue
                
            if alert_type and alert_type != alert.get("type", "").lower():
                continue
                
            if alert_types and alert.get("type", "").lower() not in alert_types:
                continue
                
            # Rule applies, find related alerts
            time_window = rule.get("time_window", 300)
            group_by = rule.get("group_by", [])
            
            # Get alert timestamp
            timestamp = alert.get("timestamp", time.time())
            
            for a in self.alert_history:
                if a.get("alert_id") == alert.get("alert_id"):
                    continue
                    
                # Check sentinel
                if sentinel and sentinel != a.get("sentinel", "").lower():
                    continue
                    
                # Check alert type
                if alert_type and alert_type != a.get("type", "").lower():
                    continue
                    
                # Check alert types
                if alert_types and a.get("type", "").lower() not in alert_types:
                    continue
                    
                # Check time window
                a_timestamp = a.get("timestamp", 0)
                
                if abs(timestamp - a_timestamp) > time_window:
                    continue
                    
                # Check group by fields
                if group_by:
                    match = True
                    
                    for field in group_by:
                        if field in alert.get("data", {}) and field in a.get("data", {}):
                            if alert["data"][field] != a["data"][field]:
                                match = False
                                break
                        else:
                            match = False
                            break
                            
                    if not match:
                        continue
                        
                # All checks passed, add to rule-based alerts
                rule_based_alerts.append(a)
                
        return rule_based_alerts
    
    def _create_or_update_correlation_group(self, alert: Dict[str, Any], correlated_alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create or update a correlation group
        
        Args:
            alert: Alert data dictionary
            correlated_alerts: List of correlated alerts
            
        Returns:
            Dict[str, Any]: Correlation group
        """
        # Check if alert is already in a group
        for group in self.correlation_groups:
            if any(a.get("alert_id") == alert.get("alert_id") for a in group["alerts"]):
                # Update existing group
                for correlated_alert in correlated_alerts:
                    if not any(a.get("alert_id") == correlated_alert.get("alert_id") for a in group["alerts"]):
                        group["alerts"].append(correlated_alert)
                        
                # Update summary
                group["summary"] = self._generate_group_summary(group["alerts"])
                
                return group
                
        # Check if any correlated alerts are in a group
        for group in self.correlation_groups:
            for correlated_alert in correlated_alerts:
                if any(a.get("alert_id") == correlated_alert.get("alert_id") for a in group["alerts"]):
                    # Add alert to existing group
                    group["alerts"].append(alert)
                    
                    # Add any remaining correlated alerts
                    for ca in correlated_alerts:
                        if not any(a.get("alert_id") == ca.get("alert_id") for a in group["alerts"]):
                            group["alerts"].append(ca)
                            
                    # Update summary
                    group["summary"] = self._generate_group_summary(group["alerts"])
                    
                    return group
        
        # Create new group
        group_id = f"group_{int(time.time())}_{len(self.correlation_groups)}"
        
        # Determine primary alert (highest severity)
        all_alerts = [alert] + correlated_alerts
        primary_alert = self._determine_primary_alert(all_alerts)
        
        # Create group
        group = {
            "group_id": group_id,
            "alerts": all_alerts,
            "primary_alert": primary_alert,
            "created_at": time.time(),
            "updated_at": time.time(),
            "summary": self._generate_group_summary(all_alerts)
        }
        
        # Add to groups
        self.correlation_groups.append(group)
        
        # Limit number of groups
        max_groups = 100
        if len(self.correlation_groups) > max_groups:
            self.correlation_groups = self.correlation_groups[-max_groups:]
            
        return group
    
    def _determine_primary_alert(self, alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Determine the primary alert in a group based on severity
        
        Args:
            alerts: List of alerts
            
        Returns:
            Dict[str, Any]: Primary alert
        """
        # Define severity levels
        severity_levels = {
            "emergency": 5,
            "critical": 4,
            "high": 3,
            "medium": 2,
            "low": 1,
            "info": 0
        }
        
        # Find alert with highest severity
        primary_alert = alerts[0]
        max_severity = severity_levels.get(primary_alert.get("severity", "").lower(), 0)
        
        for alert in alerts[1:]:
            severity = severity_levels.get(alert.get("severity", "").lower(), 0)
            
            if severity > max_severity:
                primary_alert = alert
                max_severity = severity
                
        return primary_alert
    
    def _generate_group_summary(self, alerts: List[Dict[str, Any]]) -> str:
        """
        Generate a summary for a group of alerts
        
        Args:
            alerts: List of alerts
            
        Returns:
            str: Summary text
        """
        if not alerts:
            return "No alerts in group"
            
        # Count alerts by sentinel
        sentinel_counts = defaultdict(int)
        
        for alert in alerts:
            sentinel_counts[alert.get("sentinel", "unknown")] += 1
            
        # Count alerts by severity
        severity_counts = defaultdict(int)
        
        for alert in alerts:
            severity_counts[alert.get("severity", "unknown").lower()] += 1
            
        # Count alerts by type
        type_counts = defaultdict(int)
        
        for alert in alerts:
            type_counts[alert.get("type", "unknown").lower()] += 1
            
        # Generate summary
        summary_parts = []
        
        # Add sentinel counts
        sentinel_part = ", ".join([f"{count} {sentinel}" for sentinel, count in sentinel_counts.items()])
        summary_parts.append(f"Sources: {sentinel_part}")
        
        # Add severity counts
        severity_part = ", ".join([f"{count} {severity}" for severity, count in severity_counts.items()])
        summary_parts.append(f"Severities: {severity_part}")
        
        # Add type counts
        type_part = ", ".join([f"{count} {alert_type}" for alert_type, count in type_counts.items()])
        summary_parts.append(f"Types: {type_part}")
        
        # Add time range
        timestamps = [alert.get("timestamp", 0) for alert in alerts]
        min_time = min(timestamps)
        max_time = max(timestamps)
        
        time_range = f"{datetime.fromtimestamp(min_time).strftime('%H:%M:%S')} to {datetime.fromtimestamp(max_time).strftime('%H:%M:%S')}"
        summary_parts.append(f"Time range: {time_range}")
        
        # Join parts
        summary = " | ".join(summary_parts)
        
        return summary
    
    def get_correlation_groups(self) -> List[Dict[str, Any]]:
        """
        Get all correlation groups
        
        Returns:
            List[Dict[str, Any]]: List of correlation groups
        """
        return self.correlation_groups
    
    def get_group_by_id(self, group_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a correlation group by ID
        
        Args:
            group_id: Group ID
            
        Returns:
            Optional[Dict[str, Any]]: Correlation group or None if not found
        """
        for group in self.correlation_groups:
            if group["group_id"] == group_id:
                return group
                
        return None
    
    def get_alert_group(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the correlation group for an alert
        
        Args:
            alert_id: Alert ID
            
        Returns:
            Optional[Dict[str, Any]]: Correlation group or None if not found
        """
        for group in self.correlation_groups:
            if any(a.get("alert_id") == alert_id for a in group["alerts"]):
                return group
                
        return None
    
    def cleanup_old_groups(self, max_age_seconds: int = 3600):
        """
        Clean up old correlation groups
        
        Args:
            max_age_seconds: Maximum age of groups to keep
        """
        current_time = time.time()
        self.correlation_groups = [
            group for group in self.correlation_groups
            if (current_time - group.get("updated_at", 0)) <= max_age_seconds
        ]
        
        logger.info(f"Cleaned up correlation groups, {len(self.correlation_groups)} remaining")
    
    def shutdown(self):
        """Shutdown the alert correlation engine"""
        logger.info("Shutting down Alert Correlation Engine")
        
        # Clean up resources
        self.alert_history = []
        self.correlation_groups = []
        self.models = {}
        
        logger.info("Alert Correlation Engine shutdown complete")

if __name__ == "__main__":
    # This block allows for standalone testing of the alert correlation engine
    
    # Initialize engine
    engine = AlertCorrelationEngine(config_path="sentinel_config.yaml")
    
    # Test alerts
    test_alerts = [
        {
            "alert_id": "oracle-1",
            "sentinel": "oracle_sentinel",
            "severity": "high",
            "type": "price_deviation",
            "title": "Oracle Alert: PRICE_DEVIATION",
            "message": "Oracle anomaly detected for ETH with 5.75% deviation",
            "timestamp": time.time(),
            "data": {
                "asset": "ETH",
                "price": 2850.25,
                "expected_price": 3020.50,
                "deviation": 5.75,
                "source": "chainlink"
            }
        },
        {
            "alert_id": "oracle-2",
            "sentinel": "oracle_sentinel",
            "severity": "high",
            "type": "price_deviation",
            "title": "Oracle Alert: PRICE_DEVIATION",
            "message": "Oracle anomaly detected for ETH with 6.25% deviation",
            "timestamp": time.time() + 30,
            "data": {
                "asset": "ETH",
                "price": 2830.25,
                "expected_price": 3020.50,
                "deviation": 6.25,
                "source": "uniswap"
            }
        },
        {
            "alert_id": "mev-1",
            "sentinel": "mev_sentinel",
            "severity": "critical",
            "type": "sandwich_attack",
            "title": "MEV Alert: SANDWICH_ATTACK",
            "message": "MEV attack detected: SANDWICH_ATTACK",
            "timestamp": time.time() + 60,
            "data": {
                "attack_type": "SANDWICH_ATTACK",
                "profit": 0.35,
                "gas_used": 250000,
                "asset": "ETH"
            }
        }
    ]
    
    # Process test alerts
    for alert in test_alerts:
        processed_alert = engine.process_alert(alert)
        print(f"Processed alert: {processed_alert.get('title')}")
        print(f"Correlation: {processed_alert.get('correlation')}")
        print()
    
    # Get correlation groups
    groups = engine.get_correlation_groups()
    print(f"Correlation groups: {len(groups)}")
    
    for group in groups:
        print(f"Group ID: {group['group_id']}")
        print(f"Alerts: {len(group['alerts'])}")
        print(f"Primary alert: {group['primary_alert'].get('title')}")
        print(f"Summary: {group['summary']}")
        print()
    
    # Shutdown
    engine.shutdown()