#!/usr/bin/env python3
"""
Webhook Alert Manager
Handles sending alerts to external systems via webhooks
"""

import os
import sys
import time
import json
import yaml
import logging
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("webhook_alerts.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("webhook_alert_manager")

class WebhookAlertManager:
    """
    Manages sending alerts to external systems via webhooks
    - Formats alerts according to configuration
    - Handles HTTP requests with retries
    - Supports multiple webhook endpoints
    - Manages rate limiting and batching
    """
    
    def __init__(self, config_path="alert_routing_config.yaml"):
        """
        Initialize the Webhook Alert Manager
        
        Args:
            config_path: Path to the alert routing configuration file
        """
        self.config_path = config_path
        self.last_sent_time = 0
        self.pending_alerts = []
        
        # Load configuration
        self.load_config()
        
        logger.info("Webhook Alert Manager initialized")
    
    def load_config(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
                
            # Extract webhook-specific configuration
            self.config = config.get("channel_configs", {}).get("webhook", {})
            self.global_config = config.get("global_settings", {})
            
            # Set defaults if not specified
            if not self.config:
                self.config = {}
                
            logger.info(f"Loaded configuration from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self.config = {}
            self.global_config = {}
    
    def send_alert(self, alert: Dict[str, Any]) -> bool:
        """
        Send an alert via webhook
        
        Args:
            alert: Alert data dictionary
            
        Returns:
            bool: True if alert was sent successfully
        """
        # Check if webhook is enabled
        if not self.config.get("enabled", False):
            logger.info("Webhook alerts are disabled")
            return False
            
        # Get webhook configuration
        url = self.config.get("url", os.environ.get("WEBHOOK_URL", ""))
        method = self.config.get("method", "POST")
        headers = self.config.get("headers", {"Content-Type": "application/json"})
        timeout = self.config.get("timeout", 10)
        retry_attempts = self.config.get("retry_attempts", 3)
        retry_delay = self.config.get("retry_delay", 5)
        
        # Validate configuration
        if not url:
            logger.warning("Webhook URL not configured")
            return False
            
        # Check rate limiting
        if not self._check_rate_limit():
            logger.warning("Webhook rate limit exceeded, adding to pending alerts")
            self.pending_alerts.append(alert)
            return False
            
        # Format alert for webhook
        payload = self._format_alert(alert)
        
        # Send to webhook with retries
        for attempt in range(retry_attempts):
            try:
                if method.upper() == "POST":
                    response = requests.post(url, json=payload, headers=headers, timeout=timeout)
                elif method.upper() == "PUT":
                    response = requests.put(url, json=payload, headers=headers, timeout=timeout)
                else:
                    logger.error(f"Unsupported webhook method: {method}")
                    return False
                    
                if response.status_code in [200, 201, 202, 204]:
                    # Update last sent time
                    self.last_sent_time = time.time()
                    
                    logger.info(f"Alert sent to webhook: {alert.get('title')}")
                    return True
                else:
                    logger.warning(f"Webhook returned status {response.status_code}: {response.text}")
                    
                    # Retry if not last attempt
                    if attempt < retry_attempts - 1:
                        logger.info(f"Retrying in {retry_delay} seconds (attempt {attempt + 1}/{retry_attempts})")
                        time.sleep(retry_delay)
            except Exception as e:
                logger.error(f"Error sending alert to webhook: {e}")
                
                # Retry if not last attempt
                if attempt < retry_attempts - 1:
                    logger.info(f"Retrying in {retry_delay} seconds (attempt {attempt + 1}/{retry_attempts})")
                    time.sleep(retry_delay)
        
        return False
    
    def _check_rate_limit(self) -> bool:
        """
        Check if rate limit allows sending a webhook request
        
        Returns:
            bool: True if webhook request can be sent
        """
        # Get rate limit from config
        rate_limit = self.global_config.get("rate_limit", 10)  # alerts per minute
        
        # Calculate minimum interval between requests
        min_interval = 60.0 / rate_limit  # seconds
        
        # Check if enough time has passed since last request
        current_time = time.time()
        return (current_time - self.last_sent_time) >= min_interval
    
    def _format_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format an alert for webhook
        
        Args:
            alert: Alert data dictionary
            
        Returns:
            Dict[str, Any]: Formatted webhook payload
        """
        # Create a copy of the alert to avoid modifying the original
        payload = dict(alert)
        
        # Add additional context if configured
        if self.config.get("include_full_context", True):
            payload["_meta"] = {
                "sent_at": time.time(),
                "sender": "sentinel_alert_system",
                "format_version": "1.0"
            }
            
        return payload
    
    def send_pending_alerts(self):
        """Send any pending alerts if rate limit allows"""
        if not self.pending_alerts:
            return
            
        # Check if rate limit allows sending
        if not self._check_rate_limit():
            return
            
        # Get next alert
        alert = self.pending_alerts.pop(0)
        
        # Send alert
        self.send_alert(alert)
    
    def send_batch(self, alerts: List[Dict[str, Any]]) -> bool:
        """
        Send a batch of alerts in a single webhook request
        
        Args:
            alerts: List of alert data dictionaries
            
        Returns:
            bool: True if batch was sent successfully
        """
        if not alerts:
            return False
            
        # Check if webhook is enabled
        if not self.config.get("enabled", False):
            logger.info("Webhook alerts are disabled")
            return False
            
        # Get webhook configuration
        url = self.config.get("url", os.environ.get("WEBHOOK_URL", ""))
        method = self.config.get("method", "POST")
        headers = self.config.get("headers", {"Content-Type": "application/json"})
        timeout = self.config.get("timeout", 10)
        
        # Validate configuration
        if not url:
            logger.warning("Webhook URL not configured")
            return False
            
        # Check rate limiting
        if not self._check_rate_limit():
            logger.warning("Webhook rate limit exceeded, adding to pending alerts")
            self.pending_alerts.extend(alerts)
            return False
            
        # Create batch payload
        payload = {
            "type": "batch",
            "timestamp": time.time(),
            "count": len(alerts),
            "alerts": alerts,
            "_meta": {
                "sent_at": time.time(),
                "sender": "sentinel_alert_system",
                "format_version": "1.0",
                "batch": True
            }
        }
        
        # Send to webhook
        try:
            if method.upper() == "POST":
                response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            elif method.upper() == "PUT":
                response = requests.put(url, json=payload, headers=headers, timeout=timeout)
            else:
                logger.error(f"Unsupported webhook method: {method}")
                return False
                
            if response.status_code in [200, 201, 202, 204]:
                # Update last sent time
                self.last_sent_time = time.time()
                
                logger.info(f"Batch of {len(alerts)} alerts sent to webhook")
                return True
            else:
                logger.error(f"Failed to send batch alert to webhook: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending batch alert to webhook: {e}")
            return False
    
    def shutdown(self):
        """Shutdown the webhook alert manager"""
        logger.info("Shutting down Webhook Alert Manager")
        
        # Send any pending alerts
        pending_count = len(self.pending_alerts)
        if pending_count > 0:
            logger.info(f"Sending {pending_count} pending alerts")
            
            # Try to send as batch
            if pending_count > 1:
                self.send_batch(self.pending_alerts)
            else:
                self.send_alert(self.pending_alerts[0])
        
        logger.info("Webhook Alert Manager shutdown complete")

if __name__ == "__main__":
    # This block allows for standalone testing of the webhook alert manager
    
    # Initialize manager
    manager = WebhookAlertManager(config_path="alert_routing_config.yaml")
    
    # Test alert
    test_alert = {
        "sentinel": "oracle_sentinel",
        "timestamp": time.time(),
        "severity": "HIGH",
        "title": "Oracle Price Deviation",
        "description": "ETH/USD price deviation of 5% detected",
        "data": {
            "asset": "ETH/USD",
            "expected_price": 2000.00,
            "actual_price": 2100.00,
            "deviation_percent": 5.0
        }
    }
    
    # Send test alert
    manager.send_alert(test_alert)
    
    # Shutdown
    manager.shutdown()